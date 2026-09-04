"""Session-level conversation memory for multi-turn analytical dialogues."""
from typing import Dict, List, Any


class SessionMemory:
    """Manages session-level state storing queries, tool calls, and results."""

    def __init__(self):
        self._sessions: Dict[str, List[Dict[str, Any]]] = {}

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        return self._sessions.get(session_id, [])

    def add_turn(self, session_id: str, role: str, content: Any, metadata: dict | None = None):
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append({
            "role": role,
            "content": content,
            "metadata": metadata or {},
        })

    def clear_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]
