"""Server-Sent Events plumbing shared by the streaming endpoints.

Every SSE endpoint here has the same shape: a background producer coroutine
pushes ``data: ...`` frames onto a queue while the response generator drains
it. The dangerous part is the disconnect path — when the client goes away the
response generator is closed, and a producer that nobody owns keeps running
with its own DB session open. ``sse_stream`` owns that task so it cannot
outlive the response.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

logger = logging.getLogger(__name__)

# Headers every SSE response needs. ``X-Accel-Buffering`` tells nginx not to
# buffer the response; without it frames arrive in batches behind a proxy.
SSE_HEADERS: dict[str, str] = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}

# How long to wait for a cancelled producer to unwind (i.e. close its DB
# session) before giving up and letting the event loop finish the job.
PRODUCER_SHUTDOWN_TIMEOUT = 5.0

# Queue sentinel meaning "no more frames".
END_OF_STREAM = None


def sse_frame(payload: dict[str, Any]) -> str:
    """Serialise an SSE data frame.

    ``json.dumps`` escapes the quotes and newlines that would otherwise break
    the frame apart.
    """
    return f"data: {json.dumps(payload)}\n\n"


async def sse_stream(
    producer: Callable[[asyncio.Queue], Coroutine[Any, Any, None]],
    *,
    label: str = "sse",
) -> AsyncIterator[str]:
    """Drain frames from ``producer`` and guarantee it dies with the response.

    ``producer`` receives the queue it should push frames onto, and must push
    :data:`END_OF_STREAM` exactly once when it is finished (put it in a
    ``finally`` so an exception path still terminates the stream).

    The task is created *inside* the generator so its lifetime is the response's
    lifetime. When the client disconnects, Starlette closes this generator,
    ``finally`` runs, and the producer is cancelled and awaited — which runs its
    own ``finally`` and closes its DB session. Without this the producer and its
    session leak for as long as the pipeline keeps running.
    """
    queue: asyncio.Queue = asyncio.Queue()
    task = asyncio.create_task(producer(queue))
    try:
        while True:
            event = await queue.get()
            if event is END_OF_STREAM:
                break
            yield event
        # Normal completion: surface a producer crash instead of hiding it.
        await task
    finally:
        await _shutdown_producer(task, label=label)


async def _shutdown_producer(task: asyncio.Task, *, label: str) -> None:
    """Cancel ``task`` and wait for it to unwind, without masking cancellation.

    Only the producer's own ``CancelledError`` is swallowed. If *this* coroutine
    was the one being cancelled, that propagates — hiding it would break
    Starlette's disconnect handling and leave the response half-open.
    """
    if task.done():
        # Consume any exception so asyncio does not log "never retrieved".
        if not task.cancelled() and task.exception() is not None:
            logger.error("%s producer failed: %s", label, task.exception())
        return

    logger.info("%s client disconnected — cancelling background producer", label)
    task.cancel()
    try:
        await asyncio.wait_for(asyncio.shield(task), PRODUCER_SHUTDOWN_TIMEOUT)
    except asyncio.CancelledError:
        # The producer acknowledged the cancel. Re-raise only if the
        # cancellation was aimed at us rather than at the producer.
        if not task.cancelled():
            raise
    except asyncio.TimeoutError:
        logger.warning(
            "%s producer did not unwind within %.0fs; its DB session may close late",
            label,
            PRODUCER_SHUTDOWN_TIMEOUT,
        )
    except Exception:
        logger.exception("%s producer raised while shutting down", label)
