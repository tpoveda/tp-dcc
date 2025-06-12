from __future__ import annotations

import enum


class CommandReturnStatus(enum.IntEnum):
    """Enumerator that defines the different return statuses for a command."""

    Success = enum.auto()
    Error = enum.auto()
