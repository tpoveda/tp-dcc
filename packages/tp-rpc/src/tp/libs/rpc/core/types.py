from __future__ import annotations

from typing import (
    Dict,
    List,
    Any,
    Callable,
    TypeVar,
    Union,
    Protocol,
    Optional,
    TypedDict,
)

# Type aliases for common types
DCCType = str
InstanceName = str
URI = str
FunctionName = str

# Function types
RPCFunction = Callable[..., Any]
RPCFunctionRegistry = Dict[str, RPCFunction]

# Result types
T = TypeVar("T")
RPCResult = Union[T, Exception]


# Instance registry types
class InstanceData(TypedDict):
    """Represents a single DCC instance with its URI and last heartbeat
    time.
    """

    uri: str
    last_heartbeat: str


InstanceRegistry = Dict[DCCType, Dict[InstanceName, InstanceData]]


# Protocol for RPC clients
class RPCClientProtocol(Protocol):
    """A Pyro5-exposed client class for handling remote procedure calls."""

    def call(self, function_name: str, *args: Any, **kwargs: Any) -> Any: ...
    def list_methods(self) -> List[str]: ...
    def close(self) -> None: ...


# Protocol for RPC services.
class RPCServiceProtocol(Protocol):
    """A Pyro5-exposed service class for handling remote procedure calls."""

    def call(self, function_name: str, *args: Any, **kwargs: Any) -> Any: ...
    def list_methods(self) -> List[str]: ...
    def batch_call(self, calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]: ...


# Task types
class TaskStatus:
    """Enum-like container for task status values."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELED = "canceled"


class TaskData(TypedDict):
    """Represents a single remote task with execution metadata and result"""

    id: str
    status: str
    function: str
    result: Optional[Any]
    error: Optional[str]
