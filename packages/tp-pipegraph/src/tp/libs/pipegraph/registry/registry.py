"""Node registry for managing registered node types.

Provides a singleton registry for node type discovery,
lookup, and instantiation.
"""

from __future__ import annotations

import threading


class NodeRegistry:
    """Singleton registry for node type definitions.

    The registry manages:
        - Node type registration and lookup.
        - Deprecated type mappings.
        - Category organization.
        - Search functionality.
        - Change notifications.
    """

    _instance: NodeRegistry | None = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> NodeRegistry:
        """Get or create the singleton instance."""

        if cls._instance is None:
            with cls._lock:
                # Double-check pattern.
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance

        return cls._instance

    def __init__(self) -> None:
        """Initialize the registry."""

        if getattr(self, "_initialized", False):
            return
