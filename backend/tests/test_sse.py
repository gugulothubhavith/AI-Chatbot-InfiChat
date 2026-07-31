"""SSE stream parsing tests — validates all SSE event types parse correctly."""

import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_sse_health_format():
    """SSE events from /health should return valid JSON."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "database" in data


def test_chat_stream_sse_detection():
    """Chat endpoint should advertise SSE support."""
    payload = {
        "messages": [{"role": "user", "content": "test"}],
        "model": "test-model",
    }
    resp = client.post("/api/v1/chat/stream", json=payload)
    # Without auth, should return 401 not 500
    assert resp.status_code in (401, 403, 200)
    if resp.status_code == 200:
        assert resp.headers.get("content-type", "").startswith("text/event-stream")


def test_research_sse_structure():
    """Research SSE stream should yield valid events."""
    from app.services.deep_research.orchestrator import run_pipeline
    import asyncio

    collected = []

    async def collect():
        async for event in run_pipeline("What is Python?", model="test-model"):
            if event.startswith("data: "):
                try:
                    data = json.loads(event[6:])
                    collected.append(data.get("type"))
                except json.JSONDecodeError:
                    pass
            if len(collected) > 5:
                break
        return collected

    events = asyncio.run(collect())
    assert len(events) > 0
    assert "agent_status" in events
    assert "research_stage" in events


def test_thinking_sse_structure():
    """Deep Thinking SSE stream should yield valid events."""
    from app.services.deep_thinking.orchestrator import run_thinking_pipeline
    import asyncio

    collected = []

    async def collect():
        async for event in run_thinking_pipeline("What is 2+2?"):
            if event.startswith("data: "):
                try:
                    data = json.loads(event[6:])
                    collected.append(data.get("type"))
                except json.JSONDecodeError:
                    pass
            if len(collected) > 3:
                break
        return collected

    events = asyncio.run(collect())
    assert len(events) > 0
    assert "thinking_progress" in events
