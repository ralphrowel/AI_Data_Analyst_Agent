"""Session-level conversation memory and isolated workspace state."""
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import pandas as pd
from backend.app.data_engine.dataset_manager import default_dataset_manager
from backend.app.config import DEFAULT_DATASET_PATH


class ChatSession:
    """An isolated chat workspace with its own dataset, memory, and token usage."""

    def __init__(
        self,
        session_id: str,
        title: str,
        dataset_name: str,
        created_at: Optional[str] = None,
    ):
        self.session_id = session_id
        self.title = title
        self.dataset_name = dataset_name
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.history: List[Dict[str, Any]] = []
        self.token_usage: Dict[str, int] = {
            "prompt_tokens": 0,
            "response_tokens": 0,
            "total_tokens": 0,
            "gemini_tokens": 0,
            "groq_tokens": 0,
        }

    @property
    def df(self) -> pd.DataFrame:
        """Dynamically fetch the session's dataset."""
        return default_dataset_manager.get_dataset(self.dataset_name)

    @property
    def data_description(self) -> str:
        """Fetch the schema and description of the session's dataset."""
        return default_dataset_manager.get_dataset_description(self.dataset_name)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session metadata."""
        return {
            "session_id": self.session_id,
            "title": self.title,
            "dataset_name": self.dataset_name,
            "created_at": self.created_at,
            "message_count": len(self.history),
            "token_usage": self.token_usage,
        }


class SessionStore:
    """Manages multiple isolated ChatSession workspaces."""

    def __init__(self):
        self._sessions: Dict[str, ChatSession] = {}
        # Ensure a default session is available immediately
        self.ensure_default_session()

    def ensure_default_session(self) -> ChatSession:
        """Create or return the default initial session."""
        default_id = "default_session"
        if default_id not in self._sessions:
            session = ChatSession(
                session_id=default_id,
                title="Netflix Analysis",
                dataset_name=DEFAULT_DATASET_PATH.name,
            )
            self._sessions[default_id] = session
        return self._sessions[default_id]

    def create_session(
        self,
        dataset_name: Optional[str] = None,
        title: Optional[str] = None,
    ) -> ChatSession:
        """Create a new isolated session attached to a dataset."""
        session_id = str(uuid.uuid4())
        chosen_dataset = dataset_name or DEFAULT_DATASET_PATH.name
        chosen_title = title or f"Analysis of {chosen_dataset.replace('.csv', '').replace('_', ' ').title()}"

        session = ChatSession(
            session_id=session_id,
            title=chosen_title,
            dataset_name=chosen_dataset,
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: Optional[str]) -> Optional[ChatSession]:
        """Fetch a session by ID, defaulting to the initial session if missing."""
        if not session_id or session_id not in self._sessions:
            return self.ensure_default_session()
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active chat sessions."""
        return [session.to_dict() for session in self._sessions.values()]

    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            # If no sessions remain, regenerate default
            if not self._sessions:
                self.ensure_default_session()
            return True
        return False

    def add_turn(self, session_id: str, role: str, content: Any, metadata: dict | None = None):
        """Append a message turn to a session's history."""
        session = self.get_session(session_id)
        if session:
            session.history.append({
                "role": role,
                "content": content,
                "metadata": metadata or {},
            })
            # Auto-title the session on first user question if it still has generic title
            if role == "user" and (session.title.startswith("Analysis of") or session.title == "New Chat"):
                truncated = content[:30] + "..." if len(content) > 30 else content
                session.title = truncated

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get history for a session (SessionMemory compatibility)."""
        session = self.get_session(session_id)
        return session.history if session else []

    def clear_session(self, session_id: str):
        """Clear session history (SessionMemory compatibility)."""
        session = self.get_session(session_id)
        if session:
            session.history.clear()
            session.token_usage = {
                "prompt_tokens": 0,
                "response_tokens": 0,
                "total_tokens": 0,
                "gemini_tokens": 0,
                "groq_tokens": 0,
            }

    def update_tokens(self, session_id: str, usage: dict, model_used: str):
        """Update token accumulation for a session."""
        session = self.get_session(session_id)
        if not session or not usage:
            return

        call_total = usage.get("total_tokens", 0)
        session.token_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
        session.token_usage["response_tokens"] += usage.get("response_tokens", 0)
        session.token_usage["total_tokens"] += call_total

        if model_used == "groq":
            session.token_usage["groq_tokens"] += call_total
        else:
            session.token_usage["gemini_tokens"] += call_total


# Global singleton instance
default_session_store = SessionStore()

# Backward compatibility alias
SessionMemory = SessionStore
