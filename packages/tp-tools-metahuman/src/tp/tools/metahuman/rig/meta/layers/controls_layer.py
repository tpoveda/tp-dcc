"""MetaHuman Controls Layer metanode class.

This module provides the controls layer class for MetaHuman body rigs.
The controls layer manages FK controls for the spine, head, and other
body parts.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING

from maya.api import OpenMaya

from tp.libs.maya.om import attributetypes
from tp.libs.maya.wrapper import DagNode

from .. import constants
from ..layer import MetaHumanLayer

if TYPE_CHECKING:
    pass


class MetaHumanControlsLayer(MetaHumanLayer):
    """Layer class for MetaHuman FK controls.

    This layer manages FK controls for the body rig, including spine,
    neck, and head controls. It provides methods to add, query, and
    iterate over controls.

    Example:
        >>> # Controls layers are typically created via the rig
        >>> layer = meta_rig.create_layer(
        ...     METAHUMAN_CONTROLS_LAYER_TYPE,
        ...     "controls_layer",
        ...     "controls_meta"
        ... )
        >>> layer.add_control(spine_ctrl)
        >>> layer.add_control(head_ctrl)
    """

    ID = constants.METAHUMAN_CONTROLS_LAYER_TYPE
    VERSION = "1.0.0"

    def meta_attributes(self) -> list[dict]:
        """Return the list of default metanode attributes.

        Returns:
            List of dictionaries with attribute definitions.
        """

        attrs = super().meta_attributes()

        attrs.extend(
            [
                dict(
                    name=constants.CONTROLS_LAYER_SETTINGS_NODE_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.CONTROLS_LAYER_VISIBILITY_ATTR,
                    type=attributetypes.kMFnNumericBoolean,
                    value=True,
                ),
            ]
        )

        return attrs

    # =========================================================================
    # Settings Management
    # =========================================================================

    def settings_node(self) -> DagNode | None:
        """Return the settings node for controls visibility.

        Returns:
            The settings node, or None if not connected.
        """

        return self.sourceNodeByName(
            constants.CONTROLS_LAYER_SETTINGS_NODE_ATTR
        )

    def connect_settings_node(self, node: DagNode) -> None:
        """Connect a settings node for controls visibility.

        Args:
            node: The settings node to connect.
        """

        self.connect_to(constants.CONTROLS_LAYER_SETTINGS_NODE_ATTR, node)

    # =========================================================================
    # Visibility Management
    # =========================================================================

    def controls_visibility(self) -> bool:
        """Return the controls visibility state.

        Returns:
            True if controls are visible.
        """

        return self.attribute(constants.CONTROLS_LAYER_VISIBILITY_ATTR).value()

    def set_controls_visibility(self, visible: bool) -> None:
        """Set the controls visibility state.

        Args:
            visible: True to make controls visible.
        """

        self.attribute(constants.CONTROLS_LAYER_VISIBILITY_ATTR).set(visible)

    # =========================================================================
    # Control Query Methods
    # =========================================================================

    def iterate_controls_by_side(
        self, side: str
    ) -> Generator[DagNode, None, None]:
        """Iterate over controls filtered by side.

        Args:
            side: Side indicator ('l', 'r', 'c' for left/right/center).

        Yields:
            Control nodes matching the specified side.
        """

        for ctrl in self.iterate_controls():
            if ctrl.hasAttribute(constants.CONTROL_SIDE_ATTR):
                ctrl_side = ctrl.attribute(
                    constants.CONTROL_SIDE_ATTR
                ).asString()
                if ctrl_side == side:
                    yield ctrl

    def left_controls(self) -> list[DagNode]:
        """Return all left-side controls.

        Returns:
            List of left-side control nodes.
        """

        return list(self.iterate_controls_by_side("l"))

    def right_controls(self) -> list[DagNode]:
        """Return all right-side controls.

        Returns:
            List of right-side control nodes.
        """

        return list(self.iterate_controls_by_side("r"))

    def center_controls(self) -> list[DagNode]:
        """Return all center controls.

        Returns:
            List of center control nodes.
        """

        return list(self.iterate_controls_by_side("c"))

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def delete(
        self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> bool:
        """Delete the controls layer and optionally its settings node.

        Args:
            mod: Optional modifier for batched operations.
            apply: Whether to apply the modifier.

        Returns:
            True if deletion was successful.
        """

        settings = self.settings_node()
        if settings is not None:
            try:
                settings.lock(False)
                settings.delete()
            except Exception:
                pass

        return super().delete(mod=mod, apply=apply)
