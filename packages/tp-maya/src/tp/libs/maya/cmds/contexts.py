from __future__ import annotations

from typing import Sequence
from contextlib import contextmanager

from maya import cmds


@contextmanager
def undo_context(name: str | None = None):
    """Context manager that wraps the given block of code in an undo chunk.

    Args:
        name: Optional name for the undo chunk. If not provided, the chunk
            will be unnamed.
    """

    cmds.undoInfo(openChunk=True, chunkName=name or "")
    try:
        yield
    finally:
        cmds.undoInfo(closeChunk=True)


@contextmanager
def isolated_nodes(node_paths: Sequence[str], panel: str):
    """Context manager that isolates the given nodes in the given panel.

    Args:
        node_paths: A sequence of node paths to isolate.
        panel: The panel in which to isolate the nodes.
    """

    cmds.isolateSelect(panel, state=True)
    try:
        for node_path in node_paths:
            cmds.isolateSelect(panel, addDagObject=node_path)
        yield
    finally:
        cmds.isolateSelect(panel, state=False)


@contextmanager
def maintain_selection_context():
    """Context manager that maintains the current selection."""

    current_selection = cmds.ls(selection=True, long=True) or []
    try:
        yield
    finally:
        if current_selection:
            # noinspection PyTypeChecker
            cmds.select([i for i in current_selection if cmds.objExists(i)])
