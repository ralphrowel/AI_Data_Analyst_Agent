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
        user_id: str = "user_default",
        created_at: Optional[str] = None,
    ):
        self.session_id = session_id
        self.title = title
        self.dataset_name = dataset_name
        self.user_id = user_id
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.history: List[Dict[str, Any]] = []
        self.widgets: List[Dict[str, Any]] = []
        self.token_usage: Dict[str, int] = {
            "prompt_tokens": 0,
            "response_tokens": 0,
            "total_tokens": 0,
            "gemini_tokens": 0,
            "groq_tokens": 0,
        }

    @property
    def df(self) -> pd.DataFrame:
        """Dynamically fetch the session's dataset (scoped to user uploads)."""
        return default_dataset_manager.get_dataset(self.dataset_name, user_id=self.user_id)

    @property
    def data_description(self) -> str:
        """Fetch the schema and description of the session's dataset."""
        return default_dataset_manager.get_dataset_description(self.dataset_name, user_id=self.user_id)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session metadata."""
        last_preview = ""
        if self.history:
            for turn in reversed(self.history):
                if turn.get("role") == "user":
                    last_preview = str(turn.get("content", ""))[:90]
                    break
            if not last_preview and self.history:
                last_preview = str(self.history[-1].get("content", ""))[:90]

        return {
            "session_id": self.session_id,
            "title": self.title,
            "dataset_name": self.dataset_name,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "message_count": len(self.history),
            "widget_count": len(self.widgets),
            "token_usage": self.token_usage,
            "last_message": last_preview,
        }



from backend.app import storage
from backend.app.auth.context import request_user_id

def restore_session(row):
    session = ChatSession(row['session_id'], row['title'], row['dataset_name'], row['user_id'], row['created_at'])
    session.history, session.widgets, session.token_usage = row['history'], row['widgets'], row['token_usage']
    return session

class SessionStore:
    """Durable session snapshots; mutations lock and reload records in PostgreSQL."""

    def ensure_default_session(self, user_id='user_default'):
        key = f'default_session_{user_id}'
        with storage.transaction('sessions', user_id, key) as conn:
            row = storage.get('sessions', user_id, key, conn)
            if row is None:
                session = ChatSession(key, 'Default Workspace', DEFAULT_DATASET_PATH.name, user_id)
                row = vars(session)
                storage.put('sessions', user_id, key, row, conn)
            return restore_session(row)

    def create_session(self, dataset_name=None, title=None, user_id='user_default'):
        name = dataset_name or DEFAULT_DATASET_PATH.name
        session = ChatSession(str(uuid.uuid4()), title or f'Analysis of {name}', name, user_id)
        storage.put('sessions', user_id, session.session_id, vars(session))
        return session

    def get_session(self, session_id, user_id=None):
        if not session_id: return None
        owner = request_user_id.get() or user_id
        row = storage.find('sessions', session_id, owner)
        return restore_session(row) if row else None

    def list_sessions(self, user_id=None):
        owner = request_user_id.get() or user_id
        return [restore_session(r).to_dict() for r in storage.list_records('sessions', owner)]

    def delete_session(self, session_id, user_id=None):
        session = self.get_session(session_id, user_id)
        if not session: return False
        storage.delete('sessions', session.user_id, session_id)
        return True

    def _mutate(self, session_id, change):
        session = self.get_session(session_id)
        if not session: return None
        with storage.transaction('sessions', session.user_id, session_id) as conn:
            row = storage.get('sessions', session.user_id, session_id, conn)
            if row is None: return None
            current = restore_session(row)
            result = change(current)
            storage.put('sessions', current.user_id, session_id, vars(current), conn)
            return result

    def add_turn(self, session_id, role, content, metadata=None):
        def change(session):
            session.history.append(dict(role=role, content=content, metadata=metadata or {}))
            if role == 'user' and (session.title.startswith('Analysis of') or session.title == 'New Chat'):
                session.title = content[:30] + ('...' if len(content) > 30 else '')
        self._mutate(session_id, change)

    def get_history(self, session_id):
        session = self.get_session(session_id)
        return session.history if session else []

    def clear_session(self, session_id):
        def change(session):
            session.history = []
            session.token_usage = {key: 0 for key in session.token_usage}
        self._mutate(session_id, change)

    def update_tokens(self, session_id, usage, model_used):
        def change(session):
            for key in ('prompt_tokens','response_tokens','total_tokens'):
                session.token_usage[key] += usage.get(key, 0) or 0
            session.token_usage['groq_tokens' if model_used == 'groq' else 'gemini_tokens'] += usage.get('total_tokens',0) or 0
        if usage: self._mutate(session_id, change)

    def get_widgets(self, session_id):
        session = self.get_session(session_id)
        return session.widgets if session else []

    def add_widget(self, session_id, widget):
        def change(session):
            session.widgets.append(widget)
            return widget
        return self._mutate(session_id, change)

    def delete_widget(self, session_id, widget_id):
        def change(session):
            before = len(session.widgets)
            session.widgets = [w for w in session.widgets if w.get('id') != widget_id]
            return len(session.widgets) < before
        return bool(self._mutate(session_id, change))

    def set_widgets(self, session_id, widgets):
        def change(session):
            # Recompute updates existing IDs without resurrecting deleted widgets
            # or discarding a widget concurrently added in another request.
            replacements = {w['id']: w for w in widgets}
            session.widgets = [replacements.get(w['id'], w) for w in session.widgets]
            return True
        return bool(self._mutate(session_id, change))

default_session_store = SessionStore()
SessionMemory = SessionStore
