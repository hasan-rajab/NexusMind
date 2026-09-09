"""Session-scoped bounded memory for agent workflows."""
from collections import defaultdict, deque
from threading import Lock
from typing import Deque

from config import MEMORY_MAX_TURNS

_store: dict[str, Deque[dict]] = defaultdict(lambda: deque(maxlen=MEMORY_MAX_TURNS * 2))
_lock = Lock()


def append_message(session_id: str, role: str, content: str) -> None:
    if not session_id or not content:
        return
    with _lock:
        _store[session_id].append({"role": role, "content": content})


def get_memory(session_id: str) -> list[dict]:
    if not session_id:
        return []
    with _lock:
        return list(_store.get(session_id, ()))


def clear_memory(session_id: str) -> None:
    with _lock:
        _store.pop(session_id, None)


def stats() -> dict:
    with _lock:
        return {"active_sessions": len(_store), "stored_messages": sum(len(v) for v in _store.values()), "max_turns_per_session": MEMORY_MAX_TURNS}
