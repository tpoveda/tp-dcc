from __future__ import annotations

from typing import cast

from loguru import logger
from maya.api import OpenMaya

from tp.libs.maya import factory
from tp.libs.maya.om import attributetypes
from tp.libs.maya.wrapper import DagNode
from tp.libs.maya.meta.base import MetaBase, create_meta_node_by_type

from .layers import MetaLayerType, MetaGuidesLayer, MetaGeometryLayer
from ..base import constants


MODULE_LAYER_TYPE_IDS: list[str] = [
    MetaGuidesLayer.ID,
    MetaGeometryLayer.ID,
]


class MetaModule(MetaBase):
    """Metaclass for a ModRig module in Maya."""

    ID = constants.MODULE_TYPE

    def meta_attributes(self) -> list[dict]:
        """Return the list of default metanode attributes that should be added
        into the metanode instance during creation.

        Returns:
            List of dictionaries with attribute data.
        """

        attrs = super().meta_attributes()

        descriptor_attrs = [
            {
                "name": i.split(".")[-1],
                "type": attributetypes.kMFnDataString,
                "channelBox": False,
            }
            for i in constants.DESCRIPTOR_CACHE_ATTR_NAMES
        ]

        attrs.extend(
            (
                dict(
                    name=constants.IS_ROOT_ATTR,
                    value=False,
                    type=attributetypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.IS_MODULE_ATTR,
                    value=True,
                    type=attributetypes.kMFnNumericBoolean,
                ),
                dict(name=constants.ID_ATTR, type=attributetypes.kMFnDataString),
                dict(
                    name=constants.NAME_ATTR,
                    type=attributetypes.kMFnDataString,
                ),
                dict(
                    name=constants.MODULE_SIDE_ATTR,
                    type=attributetypes.kMFnDataString,
                ),
                dict(
                    name=constants.MODULE_VERSION_ATTR,
                    type=attributetypes.kMFnDataString,
                ),
                dict(
                    name=constants.MODULE_TYPE_ATTR,
                    type=attributetypes.kMFnDataString,
                ),
                dict(
                    name=constants.MODULE_IS_ENABLED_ATTR,
                    value=True,
                    type=attributetypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.MODULE_CONTAINER_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.MODULE_HAS_GUIDE_ATTR,
                    value=False,
                    type=attributetypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.MODULE_HAS_GUIDE_CONTROLS_ATTR,
                    value=False,
                    type=attributetypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.MODULE_HAS_SKELETON_ATTR,
                    value=False,
                    type=attributetypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.MODULE_HAS_RIG_ATTR,
                    value=False,
                    type=attributetypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.MODULE_HAS_POLISHED_ATTR,
                    value=False,
                    type=attributetypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.MODULE_GROUP_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.MODULE_ROOT_TRANSFORM_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.MODULE_DESCRIPTOR_ATTR,
                    type=attributetypes.kMFnCompoundAttribute,
                    children=descriptor_attrs,
                ),
            )
        )

        return attrs

    # region === Root Transform === #

    def root_transform(self) -> DagNode | None:
        """Retrieve the root transform node associated with the current object.

        Returns:
            The root transform node.
        """

        return self.sourceNodeByName(constants.MODULE_ROOT_TRANSFORM_ATTR)

    def create_transform(
        self, name: str, parent: OpenMaya.MObject | DagNode | None
    ) -> DagNode:
        """Create a transform node with specified attributes locked and
        connected as per the requirements.

        The node is attached to the given parent if provided. If no parent is
        specified, the node is added to the root level of the scene hierarchy.

        Args:
            name: A string representing the name of the transform node to be
                created.
            parent: The parent node under which the transform node will be
                created. If `None` is provided, the node will be created
                without a parent.

        Returns:
            The newly created transform node.
        """

        component_transform = factory.create_dag_node(
            name=name, node_type="transform", parent=parent
        )
        component_transform.setLockStateOnAttributes(constants.TRANSFORM_ATTRS)
        component_transform.showHideAttributes(constants.TRANSFORM_ATTRS)
        self.connect_to(constants.MODULE_ROOT_TRANSFORM_ATTR, component_transform)
        component_transform.lock(True)

        return component_transform

    # endregion

    # region === Layers === #

    def layers_by_id(self, layer_ids: list[str]) -> dict[str, MetaLayerType | None]:
        """Retrieve layers by their IDs.

        Args:
            layer_ids: List of layer IDs to retrieve.

        Returns:
            A dictionary mapping layer IDs to their corresponding MetaLayer
                instances.
        """

        layers_map: dict[str, MetaLayerType | None] = {
            layer_id: None for layer_id in layer_ids
        }
        for meta_node in self.find_children_by_class_types(layer_ids, depth_limit=1):
            layers_map[meta_node.id] = meta_node  # type: ignore

        return layers_map

    def layers(self) -> list[MetaLayerType]:
        """Retrieve all layers associated with the module.

        Returns:
            A list of MetaLayer instances representing the layers of the module.
        """

        return cast(
            list[MetaLayerType],
            self.find_children_by_class_types(MODULE_LAYER_TYPE_IDS, depth_limit=1),
        )

    def layer_id_mapping(self) -> dict[str, MetaLayerType]:
        """Retrieve a mapping of layer types to their corresponding IDs.

        Returns:
            A dictionary mapping layer types to their IDs.
        """

        return self.layers_by_id(MODULE_LAYER_TYPE_IDS)

    def layer(self, layer_type: str) -> MetaLayerType | None:
        """Retrieve a specific layer by its type.

        Args:
            layer_type: The type of the layer to retrieve.

        Returns:
            The MetaLayer instance corresponding to the specified type, or
                `None` if not found.
        """

        meta_nodes = self.find_children_by_class_type(layer_type, depth_limit=1)
        if not meta_nodes:
            return None

        root = cast(MetaLayerType, meta_nodes[0])
        if root is None:
            logger.warning(f"Missing layer connection: {layer_type}")
            return None

        return root

    def geometry_layer(self) -> MetaGeometryLayer | None:
        """Retrieve the geometry layer associated with the module.

        Returns:
            The `MetaGeometryLayer` instance if found; `None` otherwise.
        """

        return cast(MetaGeometryLayer | None, self.layer(constants.GEOMETRY_LAYER_TYPE))

    def create_layer(
        self,
        layer_type: str,
        hierarchy_name: str,
        meta_name: str,
        parent: DagNode | None = None,
    ) -> MetaLayerType | None:
        """Create a new layer of the specified type.

        Args:
            layer_type: The type of the layer to create.
            hierarchy_name: The name of the layer root transform node to create.
            meta_name: The name of the metanode to create.
            parent: The parent node under which the layer will be created. If
                `None`, the layer will be created at the root level.

        Notes:
            If a layer of the specified type already exists, it will be
                returned instead of creating a new one.

        Returns:
            The newly created `MetaLayer` instance.
        """

        existing_layer = self.layer(layer_type)
        if existing_layer:
            return existing_layer

        new_layer = cast(
            MetaLayerType, create_meta_node_by_type(layer_type, name=meta_name)
        )
        if not new_layer:
            return None

        new_layer.create_transform(name=hierarchy_name, parent=parent)
        self.add_meta_child(new_layer)

        return new_layer

    # endregion
