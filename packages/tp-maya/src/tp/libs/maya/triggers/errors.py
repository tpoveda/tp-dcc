from __future__ import annotations


class NodeHasExistingCommandError(Exception):
    """
    Exception raised when a node has an existing command.
    """

    pass


class NodeHasExistingTriggerError(Exception):
    """
    Exception raised when a node has an existing trigger.
    """

    pass


class MissingRegisteredCommandOnNodeError(Exception):
    """
    Exception raised when a node is missing a registered command.
    """

    pass
