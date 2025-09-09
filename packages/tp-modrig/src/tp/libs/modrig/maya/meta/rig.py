from __future__ import annotations

import json
import enum
import typing
from typing import cast, Any

from loguru import logger
from maya.api import OpenMaya

from tp.libs.maya import factory
from tp.libs.maya.om import attributetypes
from tp.libs.maya.meta.base import MetaBase, create_meta_node_by_type
from tp.libs.maya.wrapper import DGNode, DagNode, DisplayLayer, ObjectSet

from .layer import MetaLayer
from ..base import constants

if typing.TYPE_CHECKING:
    from tp.libs.naming.manager import NameManager
    from .layers import MetaModulesLayer, MetaGeometryLayer


class SelectionSetType(str, enum.Enum):
    """Enumeration of the different selection sets available for a rig."""

    Root = "root"
    Controls = "ctrls"
    Skeleton = "skeleton"
    Geometry = "geometry"
    Blendshape = "blendshape"


class MetaRig(MetaBase):
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
                    name=constants.RIG_BUILD_SCRIPT_CONFIG_ATTR,
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

    # === Display Layer === #

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

    # === Selection Sets === #

    def selection_sets(self) -> dict[str, ObjectSet]:
        """Return a list of all the selection sets for this rig within the
        current Maya scene.

        Returns:
            List of selection sets instances.
        """

        return {
            SelectionSetType.Root: self.sourceNodeByName(
                constants.RIG_ROOT_SELECTION_SET_ATTR
            ),
            SelectionSetType.Controls: self.sourceNodeByName(
                constants.RIG_CONTROL_SELECTION_SET_ATTR
            ),
            SelectionSetType.Skeleton: self.sourceNodeByName(
                constants.RIG_SKELETON_SELECTION_SET_ATTR
            ),
            SelectionSetType.Geometry: self.sourceNodeByName(
                constants.RIG_GEOMETRY_SELECTION_SET_ATTR
            ),
            SelectionSetType.Blendshape: self.sourceNodeByName(
                constants.RIG_BLENDSHAPE_SELECTION_SET_ATTR
            ),
        }

    def selection_set(self, selection_set_type: SelectionSetType) -> ObjectSet | None:
        """Return a specific selection set by its name ID.

        Args:
            selection_set_type: The type of selection set to retrieve.

        Returns:
            The selection set instance if found; `None` otherwise.
        """

        valid_types = {
            SelectionSetType.Root: constants.RIG_ROOT_SELECTION_SET_ATTR,
            SelectionSetType.Controls: constants.RIG_CONTROL_SELECTION_SET_ATTR,
            SelectionSetType.Skeleton: constants.RIG_SKELETON_SELECTION_SET_ATTR,
            SelectionSetType.Geometry: constants.RIG_GEOMETRY_SELECTION_SET_ATTR,
            SelectionSetType.Blendshape: constants.RIG_BLENDSHAPE_SELECTION_SET_ATTR,
        }
        if selection_set_type not in valid_types:
            logger.warning(
                f"Invalid selection set type: {selection_set_type}. "
                f"Valid options are: {list(valid_types.keys())}"
            )
            return None

        return self.sourceNodeByName(valid_types[selection_set_type])

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

        root = existing_selection_sets[SelectionSetType.Root]
        if root is None:
            name = name_manager.resolve(
                "rootSelectionSet", {"rigName": rig_name, "type": "objectSet"}
            )
            root: ObjectSet = factory.create_dg_node(name, "objectSet")
            self.connect_to(constants.RIG_ROOT_SELECTION_SET_ATTR, root)
            existing_selection_sets[SelectionSetType.Root] = root

        if existing_selection_sets.get(SelectionSetType.Controls, None) is None:
            name = name_manager.resolve(
                "selectionSet",
                {"rigName": rig_name, "selectionSet": "ctrls", "type": "objectSet"},
            )
            object_set = factory.create_dg_node(name, "objectSet")
            root.addMember(object_set)
            self.connect_to(constants.RIG_CONTROL_SELECTION_SET_ATTR, object_set)
            existing_selection_sets[SelectionSetType.Controls] = object_set

        if existing_selection_sets.get(SelectionSetType.Skeleton, None) is None:
            name = name_manager.resolve(
                "selectionSet",
                {"rigName": rig_name, "selectionSet": "skeleton", "type": "objectSet"},
            )
            object_set = factory.create_dg_node(name, "objectSet")
            root.addMember(object_set)
            self.connect_to(constants.RIG_SKELETON_SELECTION_SET_ATTR, object_set)
            existing_selection_sets[SelectionSetType.Skeleton] = object_set

        if existing_selection_sets.get(SelectionSetType.Geometry, None) is None:
            name = name_manager.resolve(
                "selectionSet",
                {"rigName": rig_name, "selectionSet": "geometry", "type": "objectSet"},
            )
            object_set = factory.create_dg_node(name, "objectSet")
            root.addMember(object_set)
            self.connect_to(constants.RIG_GEOMETRY_SELECTION_SET_ATTR, object_set)
            existing_selection_sets[SelectionSetType.Geometry] = object_set

        if existing_selection_sets.get(SelectionSetType.Blendshape, None) is None:
            name = name_manager.resolve(
                "selectionSet",
                {
                    "rigName": rig_name,
                    "selectionSet": "blendshape",
                    "type": "objectSet",
                },
            )
            object_set = factory.create_dg_node(name, "objectSet")
            root.addMember(object_set)
            self.connect_to(constants.RIG_BLENDSHAPE_SELECTION_SET_ATTR, object_set)
            existing_selection_sets[SelectionSetType.Blendshape] = object_set

        return existing_selection_sets

    # === Layers === #

    def create_layer(
        self,
        layer_type: str,
        hierarchy_name: str,
        meta_name: str,
        parent: OpenMaya.MObject | DagNode | None = None,
    ) -> MetaLayer:
        """Create a new layer or return an existing layer of the specified type.

        This function checks if a layer of the given `layer_type` already
        exists. If such a layer exists, it returns that layer. Otherwise, it
        creates a new layer using the provided parameters and returns the
        newly created layer.

        Args:
            layer_type: The type of the layer to create or retrieve.
            hierarchy_name: The name of the hierarchy associated with the layer.
            meta_name: The metadata name to be applied to the layer.
            parent: The parent object for the layer. Can be an instance of
                `OpenMaya.MObject`, `DagNode`, or `None` if no parent is
                provided.

        Returns:
            The existing layer if it exists, or the newly created layer.
        """

        existing_layer = self.layer(layer_type)
        if existing_layer:
            return existing_layer

        return self._create_layer(layer_type, hierarchy_name, meta_name, parent)

    def layer(self, layer_type_name: str) -> MetaLayer | None:
        """Get the first `MetaLayer` object of a specific type within a given
        depth.

        This function searches for child layers of the specified layer type
        within a depth limit of 1. If such a layer is found, it returns the
        first matching `MetaLayer` object.

        Args:
            layer_type_name: The name of the layer type to search for.

        Returns:
            The first `MetaLayer` object of the specified type if found,
                otherwise `None`.
        """

        meta = self.find_children_by_class_type(layer_type_name, depth_limit=1)
        if not meta:
            return None

        # noinspection PyTypeChecker
        root: MetaLayer = meta[0]
        if root is None:
            logger.warning(f"Missing layer connection: {layer_type_name}")
            return None

        return root

    def geometry_layer(self) -> MetaGeometryLayer | None:
        """Retrieve the layer that gives access to the geometry of the rig.

        Returns:
            The geometry layer instance, or `None` if it doesn't exist.
        """

        return self.layer(constants.GEOMETRY_LAYER_TYPE)

    def modules_layer(self) -> MetaModulesLayer | None:
        """Retrieve the layer that gives access to the modules of the rig.

        Returns:
            The module layer instance, or `None` if it doesn't exist.
        """

        return self.layer(constants.MODULES_LAYER_TYPE)

    def _create_layer(
        self,
        layer_type: str,
        hierarchy_name: str,
        meta_name: str,
        parent: OpenMaya.MObject | DagNode | None,
    ) -> MetaLayer | None:
        """Create a new meta-layer instance and its associated transform,
        adding it as a child to the current object.

        Args:
            layer_type: The type of the layer to be created.
            hierarchy_name: The name of the hierarchy associated with the
                layer.
            meta_name: The name to assign to the meta-layer node.
            parent: An optional parent object for the new layer transform.

        Returns:
            The newly created meta-layer instance if successful, or `None` if
                the layer could not be created.
        """

        new_layer_meta: MetaLayer = cast(
            MetaLayer, create_meta_node_by_type(layer_type, name=meta_name, parent=self)
        )
        if not new_layer_meta:
            logger.warning(
                f"Was not possible to create new layer meta node instance: {layer_type}"
            )
            return None

        new_layer_meta.create_transform(hierarchy_name, parent=parent)
        self.add_meta_child(new_layer_meta)

        return new_layer_meta

    # === Build Scripts === #

    def build_script_config(self) -> dict[str, Any]:
        """Return the build script configuration for this rig.

        Returns:
            The build script configuration as a dictionary.
        """

        config_str = self.attribute(constants.RIG_BUILD_SCRIPT_CONFIG_ATTR).value()
        if not config_str:
            return {}

        try:
            data = json.loads(config_str)
        except Exception as err:
            logger.error(f"Error evaluating rig config: {err}")
            return {}

        return data
