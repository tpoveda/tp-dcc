from __future__ import annotations

import typing
from typing import Generator, Any

if typing.TYPE_CHECKING:
    from ..module import Module

from contextlib import contextmanager


@contextmanager
def disconnect_module_context(modules: list[Module]) -> Generator[None, Any, None]:
    """Context manager to temporarily disconnect modules.

    Args:
        modules: List of modules to disconnect.
    """

    visited: set[Module] = set()
    for module in modules:
        if module not in visited:
            module.pin()
            visited.add(module)

        for child in module.children(depth_limit=1):
            if child in visited:
                continue
            visited.add(child)
            child.pin()

    yield

    for i in visited:
        i.unpin()
