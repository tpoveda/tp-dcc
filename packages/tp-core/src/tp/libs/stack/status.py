from __future__ import annotations

import enum


class Status(enum.Enum):
    """
    Enum that defines the status of a validation result.
    """

    Invalid = "invalid"
    Success = "success"
    Failed = "failed"
    NotExecuted = "not_executed"
    Disabled = "disabled"
