from __future__ import annotations

import typing
from typing import cast

from tp.libs.maya import factory
from tp.libs.maya.om import attributetypes
from tp.libs.maya.meta.base import MetaBase
from tp.libs.maya.wrapper import DGNode, DagNode, DisplayLayer, ObjectSet

from ..base import constants

if typing.TYPE_CHECKING:
    from tp.libs.naming.manager import NameManager


class ModRig(MetaBase):
    """Metaclass for a ModRig rig in Maya."""

    ID = constants.RIG_TYPE

    def meta_attributes(self) -> list[dict]:
        """Return the list of default metanode attributes that should be added
        into the metanode instance during creation.

        Returns:
            List of dictionaries with attribute data.
        """

        attrs = super().meta_attributes()

        attrs.extend(
            [
                dict(
                    name=constants.RIG_VERSION_INFO_ATTR,
                    type=attributetypes.kMFnDataString,
                ),
                dict(
                    name=constants.NAME_ATTR,
                    type=attributetypes.kMFnDataString,
                ),
                dict(name=constants.ID_ATTR, type=attributetypes.kMFnDataString),
                dict(
                    name=constants.IS_MOD_RIG_ATTR,
                    value=True,
                    type=attributetypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.IS_ROOT_ATTR,
                    value=True,
                    type=attributetypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.RIG_CONFIG_ATTR,
                    type=attributetypes.kMFnDataString,
                ),
                dict(
                    name=constants.RIG_ROOT_TRANSFORM_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.RIG_CONTROL_DISPLAY_LAYER_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.RIG_ROOT_SELECTION_SET_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.RIG_CONTROL_SELECTION_SET_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.RIG_SKELETON_SELECTION_SET_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
            ]
        )

        return attrs

    def rig_name(self) -> str:
        """Return the name for the rig.

        Returns:
            The name of the rig.
        """

        return self.attribute(constants.NAME_ATTR).asString()

    def root_transform(self) -> DagNode:
        """Return the root transform node for this rig instance.

        Returns:
            The root transform node as a `DagNode` instance.
        """

        return self.sourceNodeByName(constants.RIG_ROOT_TRANSFORM_ATTR)

    def create_transform(self, name: str, parent: DagNode | None = None) -> DagNode:
        """Create the transform node within the current Maya scene and link
        it to this metanode instance.

        Args:
            name: Name of the transform node.
            parent: Optional parent node to attach the transform to.

        Returns:
            The newly created transform node.
        """

        transform_node = factory.create_dag_node(
            name=name, node_type="transform", parent=parent
        )
        transform_node.setLockStateOnAttributes(constants.TRANSFORM_ATTRS)
        transform_node.showHideAttributes(constants.TRANSFORM_ATTRS)
        self.connect_to(constants.RIG_ROOT_TRANSFORM_ATTR, transform_node)

        return transform_node

    def display_layer(self) -> DisplayLayer:
        """Return the display layer instance attached to this rig.

        Returns:
            The display layer instance as a `DisplayLayer` object.
        """

        return cast(
            DisplayLayer,
            self.attribute(constants.RIG_CONTROL_DISPLAY_LAYER_ATTR).sourceNode(),
        )

    def create_display_layer(self, name: str) -> DisplayLayer:
        """Create a new display layer for this rig instance.

        Args:
            name: Name for the new display layer.

        Returns:
            The newly created display layer instance.
        """

        display_layer_plug = self.attribute(constants.RIG_CONTROL_DISPLAY_LAYER_ATTR)
        layer = cast(DisplayLayer, display_layer_plug.sourceNode())
        if layer is not None:
            return layer

        layer = cast(DisplayLayer, factory.create_display_layer(name))
        layer.hideOnPlayback.set(True)
        layer.message.connect(display_layer_plug)

        return layer

    def delete_display_layer(self) -> bool:
        """Delete the display layer attached to this rig instance.

        Returns:
            True if the display layer was successfully deleted; False otherwise.
        """

        layer = self.display_layer()
        return layer.delete() if layer else False

    def selection_sets(self) -> dict[str, ObjectSet]:
        """Return a list of all the selection sets for this rig within the
        current Maya scene.

        Returns:
            List of selection sets instances.
        """

        return {
            "root": self.sourceNodeByName(constants.RIG_ROOT_SELECTION_SET_ATTR),
            "ctrls": self.sourceNodeByName(constants.RIG_CONTROL_SELECTION_SET_ATTR),
            "skeleton": self.sourceNodeByName(
                constants.RIG_SKELETON_SELECTION_SET_ATTR
            ),
        }

    def create_selection_sets(self, name_manager: NameManager) -> dict[str, DGNode]:
        """Create the selection sets for this rig instance.

        Args:
            name_manager: Name manager instance used to resolve valid
                selection set names.

        Notes:
            If the selection sets already exist within the scene, they will
                not be created.

        Returns:
            List of created selection sets.
        """

        existing_selection_sets = self.selection_sets()
        rig_name = self.name()

        root = existing_selection_sets["root"]
        if root is None:
            name = name_manager.resolve(
                "rootSelectionSet", {"rigName": rig_name, "type": "objectSet"}
            )
            root: ObjectSet = factory.create_dg_node(name, "objectSet")
            self.connect_to(constants.RIG_ROOT_SELECTION_SET_ATTR, root)
            existing_selection_sets["root"] = root

        if existing_selection_sets.get("ctrls", None) is None:
            name = name_manager.resolve(
                "selectionSet",
                {"rigName": rig_name, "selectionSet": "ctrls", "type": "objectSet"},
            )
            object_set = factory.create_dg_node(name, "objectSet")
            root.addMember(object_set)
            self.connect_to(constants.RIG_CONTROL_SELECTION_SET_ATTR, object_set)
            existing_selection_sets["ctrls"] = object_set
        if existing_selection_sets.get("skeleton", None) is None:
            name = name_manager.resolve(
                "selectionSet",
                {"rigName": rig_name, "selectionSet": "skeleton", "type": "objectSet"},
            )
            object_set = factory.create_dg_node(name, "objectSet")
            root.addMember(object_set)
            self.connect_to(constants.RIG_SKELETON_SELECTION_SET_ATTR, object_set)
            existing_selection_sets["skeleton"] = object_set

        return existing_selection_sets
