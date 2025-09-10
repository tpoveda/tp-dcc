from __future__ import annotations

from tp import dcc
from tp.libs.commands import execute

from tp.libs.maya import triggers
from tp.libs.maya.qt import nodeeditor
from tp.libs.modrig.maya.api import Rig


@triggers.block_selection_callback_decorator
def create_rig(name: str | None = None, namespace: str | None = None) -> Rig:
    """Creates a new rig instance.

    Args:
        name: The name of the rig to create. If `None`, a default name will
            be assigned.
        namespace: Optional namespace to create the rig in.

    Returns:
        The created rig instance.
    """

    if dcc.is_maya():
        with nodeeditor.disable_node_editor_add_node_context():
            return execute("modrig.rig.create", name=name, namespace=namespace)

    return execute("modrig.rig.create", name=name, namespace=namespace)


@triggers.block_selection_callback_decorator
def delete_rig(rig: Rig) -> bool:
    """Deletes the specified rig instance from the scene.

    Args:
        rig: The rig instance to delete.
    """

    return execute("modrig.rig.delete", rig=rig)
