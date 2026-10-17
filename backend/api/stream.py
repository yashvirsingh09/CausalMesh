"""
api/stream.py — Server-Sent Events (SSE) broadcaster with persistent event history buffer.
Streams real-time agent reasoning and live graph events to the frontend.
"""
import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

router = APIRouter()

# Active subscriber queues
_subscribers: list[asyncio.Queue] = []
# Persistent event buffer (last 100 events) for page refresh replay
_event_history: list[str] = []
MAX_HISTORY = 100


async def broadcast_event(event_type: str, data: dict | str) -> None:
    """
    Broadcasts an event to all connected SSE clients and stores it in the history buffer.
    """
    payload = json.dumps({"type": event_type, "data": data})

    # Keep in buffer (excluding pings, heartbeats, and resets)
    if event_type not in ("ping", "connected", "graph_reset"):
        _event_history.append(payload)
        if len(_event_history) > MAX_HISTORY:
            _event_history.pop(0)

    disconnected = []
    for q in _subscribers:
        try:
            await q.put(payload)
        except Exception:
            disconnected.append(q)
    for q in disconnected:
        if q in _subscribers:
            _subscribers.remove(q)


def clear_history() -> None:
    """Clears the event history buffer (called on graph reset)."""
    global _event_history
    _event_history.clear()


async def event_generator(request: Request) -> AsyncGenerator[str, None]:
    """Generates SSE messages for a connected client, replaying recent history first."""
    queue = asyncio.Queue()
    _subscribers.append(queue)
    try:
        # Initial heartbeat
        yield json.dumps({"type": "connected", "data": {"message": "CausalMesh Event Stream Connected"}})

        # Replay buffered history on connection so state isn't lost on refresh
        for historical_payload in list(_event_history):
            yield historical_payload

        while True:
            if await request.is_disconnected():
                break
            try:
                payload = await asyncio.wait_for(queue.get(), timeout=20.0)
                yield payload
            except asyncio.TimeoutError:
                yield json.dumps({"type": "ping", "data": {}})
    finally:
        if queue in _subscribers:
            _subscribers.remove(queue)


@router.get("/stream")
async def sse_stream(request: Request):
    """SSE endpoint for streaming agent activity and live graph updates."""
    return EventSourceResponse(
        event_generator(request),
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream",
        },
    )
