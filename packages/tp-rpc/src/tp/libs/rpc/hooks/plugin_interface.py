from __future__ import annotations

import abc
from typing import ClassVar, Any


class DCCPluginInterface(abc.ABC):
    """Abstract base class that defines the interface for all DCC plugins.

    All DCC plugins must implement this interface to ensure consistent
    behavior across different DCCs.

    Attributes:
        DCC_TYPE: Class variable defining the DCC type identifier.
        SUPPORTS_THREADING: Whether the DCC supports initialization in a
            background thread.
    """

    DCC_TYPE: ClassVar[str] = ""
    SUPPORTS_THREADING: ClassVar[bool] = True

    @abc.abstractmethod
    def initialize(
        self,
        host: str = "localhost",
        port: int = 0,
        instance_name: str | None = None,
    ) -> str:
        """Initialize the DCC plugin and start the RPC server.

        Args:
            host: Host address to bind the server to.
            port: Port to bind the server to.
            instance_name: Optional instance name for registry.

        Returns:
            The registered instance name.
        """

        pass

    @abc.abstractmethod
    def shutdown(self) -> None:
        """Shutdown the RPC server and clean up resources."""

        pass

    @abc.abstractmethod
    def setup_main_thread_execution(self) -> None:
        """Set up the mechanism for executing code in the DCC's main thread."""

        pass

    @abc.abstractmethod
    def register_shutdown_hook(self) -> None:
        """Register a hook to be called when the DCC application is shutting
        down.
        """

        pass

    def get_dcc_globals(self) -> dict[str, Any]:
        """Get DCC-specific globals to inject into the RPC server.

        Returns:
            Dictionary of global variables to inject.
        """

        return {}
