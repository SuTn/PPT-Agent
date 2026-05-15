"""Per-session progress queues for slide generation streaming."""
import asyncio
from typing import Optional

_queues: dict[str, asyncio.Queue] = {}


def create_queue(session_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _queues[session_id] = q
    return q


def get_queue(session_id: str) -> Optional[asyncio.Queue]:
    return _queues.get(session_id)


def has_queue(session_id: str) -> bool:
    return session_id in _queues


def remove_queue(session_id: str):
    _queues.pop(session_id, None)
