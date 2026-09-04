"""Base tool definitions and tool registry for the AI Data Analyst Agent.

Provides base structures for registering deterministic Python functions as
callable Gemini tools with explicit schemas.
"""
from typing import Any, Callable, Dict


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable[..., Any]] = {}
        self._schemas: Dict[str, dict] = {}

    def register(self, name: str, func: Callable[..., Any], schema: dict | None = None):
        """Register a tool with its implementation and optional schema."""
        self._tools[name] = func
        if schema:
            self._schemas[name] = schema

    def get(self, name: str) -> Callable[..., Any] | None:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def get_schemas(self) -> list[dict]:
        return list(self._schemas.values())


# Global default registry
default_registry = ToolRegistry()
