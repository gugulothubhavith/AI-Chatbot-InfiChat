"""Middleware must not stall the event loop, and must not buffer SSE.

Two separate claims are pinned here, because the original plan for this work
assumed the wrong one:

1. `BaseHTTPMiddleware` forwards streamed chunks incrementally. It does *not*
   buffer the response. Measured on Starlette 0.50.0 through a 7-layer stack —
   the same depth the real app registers. If a future upgrade regresses to
   buffering, `test_stack_does_not_buffer_streams` fails and the conversion to
   pure ASGI middleware becomes justified. Until then it isn't.

2. Synchronous database work inside `dispatch` is what actually broke
   streaming. The loop is single-threaded, so a blocking query in middleware
   freezes every concurrent request for its duration — measurably delaying
   frames of an SSE stream that was already mid-flight. The metering and audit
   middlewares now hand that work to a thread; the tests below fail if either
   one goes back to running it inline.
"""

import asyncio
import time

import pytest
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse, StreamingResponse
from starlette.routing import Route

FRAME_GAP = 0.05
FRAME_COUNT = 5
BLOCKING_WORK = 0.35


class _Call:
    """Drives one request through an ASGI app, timestamping each frame.

    `httpx.ASGITransport` buffers the whole body before returning, which would
    hide the very behaviour these tests measure.
    """

    def __init__(self, app, path):
        self._app = app
        self._path = path
        self.status: int | None = None
        self.frames: list[tuple[float, bytes]] = []
        self._done = asyncio.Event()
        self._body_sent = False

    async def _receive(self):
        # One body message, then park until the response completes. Repeating
        # `http.request` makes BaseHTTPMiddleware raise, and returning
        # `http.disconnect` early cancels the stream under test.
        if not self._body_sent:
            self._body_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await self._done.wait()
        return {"type": "http.disconnect"}

    async def _send(self, message):
        if message["type"] == "http.response.start":
            self.status = message["status"]
        elif message["type"] == "http.response.body":
            if message.get("body"):
                self.frames.append((time.perf_counter(), message["body"]))
            if not message.get("more_body", False):
                self._done.set()

    async def run(self) -> "_Call":
        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": self._path,
            "raw_path": self._path.encode(),
            "query_string": b"",
            "root_path": "",
            "headers": [(b"host", b"testserver")],
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }
        await self._app(scope, self._receive, self._send)
        return self

    @property
    def gaps(self) -> list[float]:
        stamps = [t for t, _ in self.frames]
        return [b - a for a, b in zip(stamps, stamps[1:])]


async def _ticking_stream(request):
    async def gen():
        for i in range(FRAME_COUNT):
            yield f"data: {i}\n\n".encode()
            await asyncio.sleep(FRAME_GAP)

    return StreamingResponse(gen(), media_type="text/event-stream")


async def test_stack_does_not_buffer_streams():
    """Frames must arrive spread over time, not all at once at the end."""
    app = Starlette(routes=[Route("/s", _ticking_stream)])

    class Passthrough(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            return await call_next(request)

    for _ in range(7):  # matches the real app's stack depth
        app.add_middleware(Passthrough)

    call = await _Call(app, "/s").run()

    assert call.status == 200
    assert len(call.frames) == FRAME_COUNT, "chunks were coalesced — response buffered"
    assert min(call.gaps) >= FRAME_GAP * 0.5, (
        f"frames arrived together (gaps={call.gaps}); the stack is buffering"
    )


async def test_sync_work_in_dispatch_stalls_the_loop():
    """The failure mode being defended against, demonstrated deliberately.

    This is the control for the next test: it shows the measurement is capable
    of detecting a stall, so a passing result there means something.
    """
    app = Starlette(
        routes=[
            Route("/s", _ticking_stream),
            Route("/blocking", lambda r: PlainTextResponse("ok")),
        ]
    )

    class BlocksInline(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            if request.url.path == "/blocking":
                time.sleep(BLOCKING_WORK)  # what a sync query costs the loop
            return await call_next(request)

    app.add_middleware(BlocksInline)

    stream = asyncio.create_task(_Call(app, "/s").run())
    await asyncio.sleep(FRAME_GAP)
    await _Call(app, "/blocking").run()
    call = await stream

    assert max(call.gaps) > BLOCKING_WORK, (
        "expected the inline sleep to delay a stream frame"
    )


async def test_offloaded_work_does_not_stall_the_loop():
    """The fix: identical work, moved to a thread, leaves the stream alone."""
    app = Starlette(
        routes=[
            Route("/s", _ticking_stream),
            Route("/blocking", lambda r: PlainTextResponse("ok")),
        ]
    )

    class OffloadsWork(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            if request.url.path == "/blocking":
                await asyncio.to_thread(time.sleep, BLOCKING_WORK)
            return await call_next(request)

    app.add_middleware(OffloadsWork)

    stream = asyncio.create_task(_Call(app, "/s").run())
    await asyncio.sleep(FRAME_GAP)
    await _Call(app, "/blocking").run()
    call = await stream

    assert max(call.gaps) < BLOCKING_WORK, (
        f"stream was delayed despite offloading (gaps={call.gaps})"
    )


# ── The shipped middlewares ───────────────────────────────────

def test_metering_middleware_offloads_its_queries():
    """Guards against a revert to inline `SessionLocal()` in dispatch."""
    import inspect

    from app.middleware.usage_tracker import UsageTrackingMiddleware

    src = inspect.getsource(UsageTrackingMiddleware.dispatch)
    assert "SessionLocal()" not in src, "metering opens a sync session on the loop"
    assert "to_thread" in src, "metering no longer offloads its DB work"


def test_audit_middleware_offloads_its_write():
    import inspect

    from app.middleware.audit_logging import AdminAuditMiddleware

    src = inspect.getsource(AdminAuditMiddleware.dispatch)
    assert "SessionLocal()" not in src, "audit opens a sync session on the loop"
    assert "to_thread" in src, "audit no longer offloads its DB write"


def test_offloaded_helpers_take_no_request_objects():
    """A function running off-loop must not touch Request/Response.

    Both helpers deliberately accept plain values (the auth header, a status
    code) instead of the objects they came from, so nothing loop-bound is
    reachable from the worker thread.
    """
    import inspect

    from app.middleware.audit_logging import _write_audit_log
    from app.middleware.usage_tracker import _check_entitlements, _resolve_user_id

    for fn in (_check_entitlements, _resolve_user_id, _write_audit_log):
        annotations = inspect.signature(fn).parameters
        for name, param in annotations.items():
            assert "Request" not in str(param.annotation), (
                f"{fn.__name__} takes a Request ({name}); it runs off the loop"
            )
            assert "Response" not in str(param.annotation), (
                f"{fn.__name__} takes a Response ({name}); it runs off the loop"
            )
