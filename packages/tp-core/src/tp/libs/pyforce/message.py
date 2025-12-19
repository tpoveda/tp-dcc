from __future__ import annotations

from enum import IntEnum


class MessageSeverity(IntEnum):
    """Enumeration representing the severity level of a message.

    Attributes:
        EMPTY: Represents no error or an empty state.
        INFO: Represents an informational message indicating a positive event or operation.
        WARNING: Represents a warning message indicating a potential issue or concern.
        FAILED: Represents a failed operation often resulting from incorrect user actions.
        FATAL: Represents a severe error indicating a critical system failure.
    """


    EMPTY = 0
    INFO = 1
    WARNING = 2
    FAILED = 3
    FATAL = 4

class MessageLevel(IntEnum):
    """Represent different levels of message severity or types of errors.

    This enumeration classifies various message levels or error types to identify
    their nature and purpose. It is typically used to categorize errors or messages
    that might occur during program execution, aiding in error handling, debugging,
    and logging.

    Attributes:
        NONE: Miscellaneous.
        USAGE: Request is not consistent with expected documentation (dox).
        UNKNOWN: Using unknown entity.
        CONTEXT: Using entity in the wrong context.
        ILLEGAL: Lack of permission to perform the action.
        NOTYET: An issue needs resolution before the action can be performed.
        PROTECT: Protections prevented the operation.
        EMPTY: Action returned empty results.
        FAULT: Inexplicable program fault.
        CLIENT: Client-side program errors.
        ADMIN: Server administrative action required.
        CONFIG: Client configuration is inadequate.
        UPGRADE: Client or server is too old to interact.
        COMM: Communications error.
        TOOBIG: Data size or request is too large to be handled.
    """

    NONE = 0
    USAGE = 0x01
    UNKNOWN = 0x02
    CONTEXT = 0x03
    ILLEGAL = 0x04
    NOTYET = 0x05
    PROTECT = 0x06
    EMPTY = 0x11
    FAULT = 0x21
    CLIENT = 0x22
    ADMIN = 0x23
    CONFIG = 0x24
    UPGRADE = 0x25
    COMM = 0x26
    TOOBIG = 0x27
