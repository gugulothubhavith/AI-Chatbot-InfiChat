"""Per-user concurrency caps — semantics and streaming-response lifetime.

The load-bearing claim in `app.core.concurrency` is that a dependency with
`yield` holds its slot for the whole `StreamingResponse`, not just until the
handler returns. Deep research depends on that: its pipeline runs inside the
SSE stream, after the handler has already returned. These tests pin that
behaviour so a FastAPI upgrade that changes the dependency exit-stack scope
fails here instead of silently uncapping the expensive endpoints.
"""

import asyncio

import pytest
from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse

import app.core.concurrency as concurrency_module
from app.core.concurrency import (
    ConcurrencyLimitExceeded,
    UserConcurrencyLimiter,
    code_agent_limiter,
    deep_research_limiter,
    limit_concurrency,
)


# ── Limiter semantics ─────────────────────────────────────────

async def test_cap_is_enforced_per_user():
    limiter = UserConcurrencyLimiter("test", limit=2)

    async with limiter.slot("u1"):
        async with limiter.slot("u1"):
            assert limiter.active_for("u1") == 2
            with pytest.raises(ConcurrencyLimitExceeded):
                async with limiter.slot("u1"):
                    pytest.fail("third slot should not be granted")

            # One user at their cap must not block anybody else.
            async with limiter.slot("u2"):
                assert limiter.active_for("u2") == 1


async def test_slot_released_when_body_raises():
    limiter = UserConcurrencyLimiter("test", limit=1)

    with pytest.raises(RuntimeError):
        async with limiter.slot("u1"):
            raise RuntimeError("boom")

    assert limiter.active_for("u1") == 0


async def test_slot_released_on_cancellation():
    """The client-disconnect path: the task is cancelled mid-run."""
    limiter = UserConcurrencyLimiter("test", limit=1)
    started = asyncio.Event()

    async def long_run():
        async with limiter.slot("u1"):
            started.set()
            await asyncio.sleep(60)

    task = asyncio.create_task(long_run())
    await started.wait()
    assert limiter.active_for("u1") == 1

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert limiter.active_for("u1") == 0


async def test_no_leak_under_concurrent_burst():
    """Exactly `limit` runs proceed, and the map empties afterwards."""
    limiter = UserConcurrencyLimiter("test", limit=3)

    async def worker():
        try:
            async with limiter.slot("u1"):
                await asyncio.sleep(0.01)
            return "ran"
        except ConcurrencyLimitExceeded:
            return "capped"

    results = await asyncio.gather(*(worker() for _ in range(20)))

    assert results.count("ran") == 3
    assert results.count("capped") == 17
    # The map is keyed by users with work in flight, not users ever seen.
    assert limiter._active == {}


async def test_limit_below_one_is_rejected():
    with pytest.raises(ValueError):
        UserConcurrencyLimiter("test", limit=0)


def test_shipped_limiters_are_configured():
    assert deep_research_limiter.limit == 1
    assert code_agent_limiter.limit == 2


# ── HTTP behaviour ────────────────────────────────────────────

class _FakeUser:
    id = "user-1"


@pytest.fixture
def stream_app(monkeypatch):
    """A minimal app whose one route streams until told to stop.

    `get_current_user` is stubbed so this exercises the slot mechanics rather
    than the auth stack.
    """

    async def fake_user():
        return _FakeUser()

    monkeypatch.setattr(concurrency_module, "get_current_user", fake_user)

    limiter = UserConcurrencyLimiter("stream test", limit=1)
    release = asyncio.Event()
    api = FastAPI()

    @api.post("/stream", dependencies=[Depends(limit_concurrency(limiter))])
    async def stream():
        async def gen():
            yield "data: start\n\n"
            await release.wait()
            yield "data: end\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    return api, limiter, release


class _Call:
    """Drives one request through the ASGI app, exposing frames as they arrive.

    `httpx.ASGITransport` buffers the whole response before returning, which
    deadlocks against a stream that is deliberately held open. Calling the app
    directly is both non-blocking and a closer match to what uvicorn does.
    """

    def __init__(self, api, path="/stream"):
        self._api = api
        self._path = path
        self.status: int | None = None
        self.headers: dict[str, str] = {}
        self.frames: list[str] = []
        self._first_frame = asyncio.Event()
        self._body_sent = False
        self._disconnect = asyncio.Event()
        self._task: asyncio.Task | None = None

    async def _receive(self):
        # The body goes out once; every later call must block until the client
        # actually disconnects. Returning `http.request` on repeat would spin
        # Starlette's `listen_for_disconnect` loop at 100% CPU forever.
        if not self._body_sent:
            self._body_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await self._disconnect.wait()
        return {"type": "http.disconnect"}

    async def _send(self, message):
        if message["type"] == "http.response.start":
            self.status = message["status"]
            self.headers = {
                k.decode().lower(): v.decode() for k, v in message["headers"]
            }
        elif message["type"] == "http.response.body":
            body = message.get("body", b"")
            if body:
                self.frames.append(body.decode())
                self._first_frame.set()

    def start(self) -> "_Call":
        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": self._path,
            "raw_path": self._path.encode(),
            "query_string": b"",
            "root_path": "",
            "headers": [(b"host", b"testserver")],
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }
        self._task = asyncio.create_task(self._api(scope, self._receive, self._send))
        return self

    async def wait_first_frame(self) -> str:
        await asyncio.wait_for(self._first_frame.wait(), timeout=5)
        return self.frames[0]

    async def finish(self) -> None:
        assert self._task is not None
        try:
            await asyncio.wait_for(self._task, timeout=5)
        finally:
            # Release any receive() still parked on the disconnect event.
            self._disconnect.set()

    async def disconnect(self) -> None:
        """Simulate the client going away mid-stream."""
        assert self._task is not None
        self._disconnect.set()
        try:
            await asyncio.wait_for(self._task, timeout=5)
        except asyncio.CancelledError:
            pass

    @property
    def body(self) -> str:
        return "".join(self.frames)


async def test_slot_spans_the_whole_stream(stream_app):
    """The point of the whole design: the handler returns, the slot does not."""
    api, limiter, release = stream_app

    live = _Call(api).start()
    assert "start" in await live.wait_first_frame()
    assert live.status == 200

    # The handler has already returned — the pipeline now runs inside the
    # stream. A second run must still be refused.
    capped = _Call(api).start()
    await capped.finish()

    assert capped.status == 429
    assert capped.headers["retry-after"] == "30"
    assert limiter.active_for("user-1") == 1

    release.set()
    await live.finish()

    # Stream closed: the slot came back, exactly once.
    assert limiter._active == {}


async def test_slot_reusable_after_stream_completes(stream_app):
    api, limiter, release = stream_app
    release.set()  # let each stream finish immediately

    for _ in range(3):
        call = _Call(api).start()
        await call.finish()
        assert call.status == 200
        assert "end" in call.body
        assert limiter._active == {}


async def test_slot_released_when_client_disconnects_mid_stream(stream_app):
    """Closing the tab during a long run must not burn the slot permanently.

    This is the failure that would hurt most: a leaked slot means that user is
    refused their own pipeline forever, with nothing to release it.
    """
    api, limiter, release = stream_app

    live = _Call(api).start()
    await live.wait_first_frame()
    assert limiter.active_for("user-1") == 1

    await live.disconnect()

    assert limiter._active == {}

    # And the user can immediately start a new run.
    release.set()
    again = _Call(api).start()
    await again.finish()
    assert again.status == 200


async def test_capped_request_never_opens_a_stream(stream_app):
    """The 429 is a plain JSON error, not a half-open event stream."""
    api, limiter, release = stream_app

    live = _Call(api).start()
    await live.wait_first_frame()

    capped = _Call(api).start()
    await capped.finish()

    assert capped.status == 429
    assert capped.headers["content-type"].startswith("application/json")
    assert "detail" in capped.body
    assert "text/event-stream" not in capped.headers.get("content-type", "")

    release.set()
    await live.finish()
