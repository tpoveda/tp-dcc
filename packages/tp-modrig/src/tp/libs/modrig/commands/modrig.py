from __future__ import annotations

from typing import Any

from tp import dcc
from tp.libs.commands import execute

from tp.libs.maya import triggers
from tp.libs.maya.qt import nodeeditor
from tp.libs.modrig.maya.api import Rig, Module


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


@triggers.block_selection_callback_decorator
def create_modules(
    rig: Rig,
    modules: list[dict[str, Any]],
    build_guides: bool = False,
    build_rigs: bool = False,
) -> list[Module]:
    """Create modules in the specified rig instance.

    Args:
        rig: The rig instance to create the modules in.
        modules: List of dictionaries containing module creation parameters.
        build_guides: Whether to build guides after creating the modules.
        build_rigs: Whether to build rigs after creating the modules.

    Returns:
        List of created module instances.
    """

    if dcc.is_maya():
        with nodeeditor.disable_node_editor_add_node_context():
            return execute(
                "modrig.rig.create.modules",
                rig=rig,
                modules=modules,
                build_guides=build_guides,
                build_rigs=build_rigs,
            )

    return execute(
        "modrig.rig.create.modules",
        rig=rig,
        modules=modules,
        build_guides=build_guides,
        build_rigs=build_rigs,
    )
