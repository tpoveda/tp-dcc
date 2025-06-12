import logging

logger = logging.getLogger(__name__)


class NodeException(Exception):
    """Base exception class."""

    def __init__(self, message: str):
        super().__init__(message)
        logger.error(message)


class DataTypeAlreadyRegisteredError(NodeException):
    """Exception raised when attempting to register a data type that is already registered."""

    def __init__(self, data_type: str):
        super().__init__(f'Data type "{data_type}" is already registered.')


class NodeAlreadyRegisteredError(NodeException):
    """Exception raised when attempting to register a node that is already registered."""

    def __init__(self, node_id: str):
        super().__init__(f'Node with ID "{node_id}" is already registered.')


class NodeAliasAlreadyRegisteredError(NodeException):
    """Exception raised when attempting to register a node alias that is already registered."""

    def __init__(self, alias: str):
        super().__init__(f'Node with alias "{alias}" is already registered.')


class NodeNotFoundError(NodeException):
    """Exception raised when a node is not found."""

    def __init__(self, node_id: str):
        self.node_id = node_id
        super().__init__(f'Node with ID "{node_id}" not found.')


class NodeCreationError(NodeException):
    """Exception raised when a node cannot be created."""

    def __init__(self, node_id: str):
        super().__init__(f'Node with ID "{node_id}" cannot be created.')


class NodeLockedError(NodeException):
    """Exception raised when a node is locked."""

    def __init__(self, node_id: str):
        super().__init__(f'Node with ID "{node_id}" is locked.')


class NodePropertyAlreadyExistsError(NodeException):
    """Exception raised when a property is invalid."""

    def __init__(self, node_id: str, property_name: str):
        super().__init__(
            f'Property "{property_name}" already exists in node "{node_id}".'
        )


class NodePropertyNotFoundError(NodeException):
    """Exception raised when a property is not found."""

    def __init__(self, node_id: str, property_name: str):
        super().__init__(f'Property "{property_name}" not found in node "{node_id}".')


class NodePropertyReservedError(NodeException):
    """Exception raised when a property is reserved."""

    def __init__(self, property_name: str):
        super().__init__(f'Property "{property_name}" is reserved and cannot be set.')


class NodePropertyWidgetErrror(NodeException):
    """Exception raised when a property widget is invalid."""

    def __init__(self, widget_name: str):
        super().__init__(f'Property widget "{widget_name}" is invalid.')


class NodeInputPortAlreadyExistsError(NodeException):
    """Exception raised when a port already exists."""

    def __init__(self, port_name: str, node_id: str):
        super().__init__(f'Port "{port_name}" already exists in node "{node_id}".')


class NodeOutputPortAlreadyExistsError(NodeException):
    """Exception raised when a port already exists."""

    def __init__(self, port_name: str, node_id: str):
        super().__init__(f'Port "{port_name}" already exists in node "{node_id}".')


class NodePortNotFoundError(NodeException):
    """Exception raised when a port is not found."""

    def __init__(self, port_name: str, node_id: str):
        super().__init__(f'Port "{port_name}" not found in node "{node_id}".')


class NodePortLockedError(NodeException):
    """Exception raised when a port is locked."""

    def __init__(self, port_name: str, node_id: str):
        super().__init__(f'Port "{port_name}" in node "{node_id}" is locked.')


class NodeGraphMenuError(NodeException):
    """Base exception class for node graph menus."""

    def __init__(self, menu_name: str):
        super().__init__(f'Menu with name "{menu_name}" already exists!.')


class NodePortNotRemovableError(NodeException):
    """Exception raised when a port is not removable."""

    def __init__(self, port_name: str, node_id: str):
        super().__init__(f'Port "{port_name}" in node "{node_id}" is not removable.')


class NodeWidgetAlreadyInitializedError(NodeException):
    """Exception raised when a node widget is already initialized."""

    def __init__(self, node_id: str):
        super().__init__(f'Widget for node "{node_id}" is already initialized.')
