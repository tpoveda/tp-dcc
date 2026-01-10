"""MetaHuman FK/IK Layer metanode class.

This module provides the FK/IK layer class for MetaHuman body rigs.
The FK/IK layer manages FK/IK switching systems for limbs (arms, legs).
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


class MetaHumanFKIKLayer(MetaHumanLayer):
    """Layer class for MetaHuman FK/IK limb systems.

    This layer manages FK/IK switching controls and blend nodes for
    arm and leg systems. It tracks FK controls, IK controls, pole vectors,
    and the blend settings.

    Example:
        >>> # FK/IK layers are typically created via the rig
        >>> layer = meta_rig.create_layer(
        ...     METAHUMAN_FKIK_LAYER_TYPE,
        ...     "fkik_layer",
        ...     "fkik_meta"
        ... )
        >>> layer.add_fk_control(fk_shoulder_ctrl)
        >>> layer.add_ik_control(ik_hand_ctrl)
        >>> layer.add_pole_vector(arm_pv)
    """

    ID = constants.METAHUMAN_FKIK_LAYER_TYPE
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
                    name=constants.FKIK_LAYER_FK_CONTROLS_ATTR,
                    isArray=True,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.FKIK_LAYER_IK_CONTROLS_ATTR,
                    isArray=True,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.FKIK_LAYER_POLE_VECTORS_ATTR,
                    isArray=True,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.FKIK_LAYER_BLEND_NODES_ATTR,
                    isArray=True,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.FKIK_LAYER_SETTINGS_NODE_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
            ]
        )

        return attrs

    # =========================================================================
    # FK Controls
    # =========================================================================

    def add_fk_control(self, control: DagNode) -> None:
        """Add an FK control to this layer.

        Args:
            control: The FK control node to add.
        """

        plug = self.attribute(constants.FKIK_LAYER_FK_CONTROLS_ATTR)
        next_plug = plug.nextAvailableDestElementPlug()
        self.connect_to_by_plug(next_plug, control)

    def iterate_fk_controls(self) -> Generator[DagNode, None, None]:
        """Iterate over all FK controls.

        Yields:
            FK control nodes.
        """

        plug = self.attribute(constants.FKIK_LAYER_FK_CONTROLS_ATTR)
        for element in plug:
            source = element.sourceNode()
            if source is not None:
                yield source

    def fk_controls(self) -> list[DagNode]:
        """Return all FK controls.

        Returns:
            List of FK control nodes.
        """

        return list(self.iterate_fk_controls())

    def fk_control_count(self) -> int:
        """Return the number of FK controls.

        Returns:
            Number of FK controls.
        """

        return len(self.fk_controls())

    # =========================================================================
    # IK Controls
    # =========================================================================

    def add_ik_control(self, control: DagNode) -> None:
        """Add an IK control to this layer.

        Args:
            control: The IK control node to add.
        """

        plug = self.attribute(constants.FKIK_LAYER_IK_CONTROLS_ATTR)
        next_plug = plug.nextAvailableDestElementPlug()
        self.connect_to_by_plug(next_plug, control)

    def iterate_ik_controls(self) -> Generator[DagNode, None, None]:
        """Iterate over all IK controls.

        Yields:
            IK control nodes.
        """

        plug = self.attribute(constants.FKIK_LAYER_IK_CONTROLS_ATTR)
        for element in plug:
            source = element.sourceNode()
            if source is not None:
                yield source

    def ik_controls(self) -> list[DagNode]:
        """Return all IK controls.

        Returns:
            List of IK control nodes.
        """

        return list(self.iterate_ik_controls())

    def ik_control_count(self) -> int:
        """Return the number of IK controls.

        Returns:
            Number of IK controls.
        """

        return len(self.ik_controls())

    # =========================================================================
    # Pole Vectors
    # =========================================================================

    def add_pole_vector(self, pole_vector: DagNode) -> None:
        """Add a pole vector control to this layer.

        Args:
            pole_vector: The pole vector control node to add.
        """

        plug = self.attribute(constants.FKIK_LAYER_POLE_VECTORS_ATTR)
        next_plug = plug.nextAvailableDestElementPlug()
        self.connect_to_by_plug(next_plug, pole_vector)

    def iterate_pole_vectors(self) -> Generator[DagNode, None, None]:
        """Iterate over all pole vector controls.

        Yields:
            Pole vector control nodes.
        """

        plug = self.attribute(constants.FKIK_LAYER_POLE_VECTORS_ATTR)
        for element in plug:
            source = element.sourceNode()
            if source is not None:
                yield source

    def pole_vectors(self) -> list[DagNode]:
        """Return all pole vector controls.

        Returns:
            List of pole vector control nodes.
        """

        return list(self.iterate_pole_vectors())

    # =========================================================================
    # Blend Nodes
    # =========================================================================

    def add_blend_node(self, blend_node: DagNode) -> None:
        """Add a blend node to this layer.

        Args:
            blend_node: The blend node to add.
        """

        plug = self.attribute(constants.FKIK_LAYER_BLEND_NODES_ATTR)
        next_plug = plug.nextAvailableDestElementPlug()
        self.connect_to_by_plug(next_plug, blend_node)

    def iterate_blend_nodes(self) -> Generator[DagNode, None, None]:
        """Iterate over all blend nodes.

        Yields:
            Blend nodes.
        """

        plug = self.attribute(constants.FKIK_LAYER_BLEND_NODES_ATTR)
        for element in plug:
            source = element.sourceNode()
            if source is not None:
                yield source

    def blend_nodes(self) -> list[DagNode]:
        """Return all blend nodes.

        Returns:
            List of blend nodes.
        """

        return list(self.iterate_blend_nodes())

    # =========================================================================
    # Settings Node
    # =========================================================================

    def settings_node(self) -> DagNode | None:
        """Return the FK/IK settings node.

        Returns:
            The settings node, or None if not connected.
        """

        return self.sourceNodeByName(constants.FKIK_LAYER_SETTINGS_NODE_ATTR)

    def connect_settings_node(self, node: DagNode) -> None:
        """Connect the FK/IK settings node.

        Args:
            node: The settings node to connect.
        """

        self.connect_to(constants.FKIK_LAYER_SETTINGS_NODE_ATTR, node)

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def delete(
        self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> bool:
        """Delete the FK/IK layer and its settings node.

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

        # Delete blend nodes
        for blend_node in self.blend_nodes():
            try:
                blend_node.lock(False)
                blend_node.delete()
            except Exception:
                pass

        return super().delete(mod=mod, apply=apply)
