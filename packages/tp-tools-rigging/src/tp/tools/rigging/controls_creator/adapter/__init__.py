from __future__ import annotations

from tp import dcc

from .abstract import AbstractControlCreatorAdapter

_ADAPTER_INSTANCE: AbstractControlCreatorAdapter | None = None

__all__ = [
    "get",
]


def get() -> AbstractControlCreatorAdapter:
    """Returns the current DCC's control creator adapter.

    Returns:
        The current DCC's control creator adapter.

    Raises:
        NotImplementedError: If no adapter is available for the current DCC.
    """

    global _ADAPTER_INSTANCE

    if _ADAPTER_INSTANCE is not None:
        return _ADAPTER_INSTANCE

    if dcc.is_maya():
        from .maya import MayaControlCreatorAdapter as ControlCreatorAdapter

        _ADAPTER_INSTANCE = ControlCreatorAdapter()
    else:
        raise NotImplementedError(
            f"No controls creator adapter available for current DCC: {dcc.current_dcc()}"
        )

    return _ADAPTER_INSTANCE
