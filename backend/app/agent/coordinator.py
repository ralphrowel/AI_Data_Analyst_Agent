"""Agent Coordinator: Coordinates tool calls, multi-turn state, and Gemini reasoning."""
from typing import Any, Dict, Optional
from backend.app.agent.router import QueryRouter
from backend.app.memory.session_store import SessionMemory


class AgentCoordinator:
    """Orchestrates query resolution across Router, Tools, and Memory."""

    def __init__(self, router: QueryRouter, memory: SessionMemory):
        self.router = router
        self.memory = memory

    def process_query(self, session_id: str, question: str) -> Dict[str, Any]:
        """Process a question for a given session.

        Skeleton implementation ready for tool loop execution.
        """
        history = self.memory.get_history(session_id)
        route = self.router.route(question, history)
        
        # Skeleton result
        return {
            "route": route,
            "session_id": session_id,
            "status": "pending_execution",
        }
