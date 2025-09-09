from __future__ import annotations

from maya.api import OpenMaya

from tp.libs.maya import factory
from tp.libs.maya.wrapper import DagNode
from tp.libs.maya.om import attributetypes
from tp.libs.maya.meta.base import MetaBase

from ..base import constants
from ..descriptors.attributes import AttributeDescriptor


class MetaLayer(MetaBase):
    """MetaClass implementation for a layer in the Maya scene."""

    ID = constants.BASE_LAYER_TYPE

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
                    name=constants.LAYER_EXTRA_NODES_ATTR,
                    isArray=True,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.LAYER_ROOT_TRANSFORM_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.LAYER_CONNECTORS_ATTR,
                    isArray=True,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.LAYER_SETTING_NODES_ATTR,
                    type=attributetypes.kMFnCompoundAttribute,
                    isArray=True,
                    children=[
                        dict(
                            name=constants.LAYER_SETTING_NODE_ATTR,
                            type=attributetypes.kMFnMessageAttribute,
                        ),
                        dict(
                            name=constants.LAYER_SETTING_NAME_ATTR,
                            type=attributetypes.kMFnDataString,
                        ),
                    ],
                ),
                dict(
                    name=constants.LAYER_TAGGED_NODE_ATTR,
                    type=attributetypes.kMFnCompoundAttribute,
                    isArray=True,
                    children=[
                        dict(
                            name=constants.LAYER_TAGGED_NODE_SOURCE_ATTR,
                            type=attributetypes.kMFnMessageAttribute,
                        ),
                        dict(
                            name=constants.LAYER_TAGGED_NODE_ID_ATTR,
                            type=attributetypes.kMFnDataString,
                        ),
                    ],
                ),
            ]
        )

        return attrs

    def update_metadata(self, metadata: list[AttributeDescriptor]) -> None:
        """Update the metanode attributes based on the provided metadata.

        Args:
            metadata: List of AttributeDescriptor instances containing the
                metadata to update the metanode attributes.
        """

        for meta_attr in metadata:
            if not meta_attr:
                continue
            attribute = self.attribute(meta_attr.name)
            if attribute is None:
                self.addAttribute(**meta_attr.to_dict())
            else:
                attribute.setFromDict(**meta_attr.to_dict())

    def root_transform(self) -> DagNode:
        """Retrieve the root transform node associated with the current object.

        Returns:
            The root transform node.
        """

        return self.sourceNodeByName(constants.LAYER_ROOT_TRANSFORM_ATTR)

    def create_transform(
        self, name: str, parent: OpenMaya.MObject | DagNode | None = None
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

        layer_transform = factory.create_dag_node(
            name=name, node_type="transform", parent=parent
        )
        layer_transform.setLockStateOnAttributes(constants.TRANSFORM_ATTRS)
        layer_transform.showHideAttributes(constants.TRANSFORM_ATTRS)
        self.connect_to(constants.LAYER_ROOT_TRANSFORM_ATTR, layer_transform)
        layer_transform.lock(True)

        return layer_transform

    def show(self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True):
        """Show the root transform if it exists.

        Args:
            mod: An optional MDGModifier object used to apply modifications.
                If `None`, no modifier is used.
            apply: A flag indicating whether to apply the modification
                immediately. If set to True, the changes will be applied.
        """

        root = self.root_transform()
        if root is not None:
            root.show(mod=mod, apply=apply)

    def hide(self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True):
        """Hides the root transform node of the object, if it exists.

        Args:
            mod: An optional MDGModifier object used to apply modifications.
                If `None`, no modifier is used.
            apply: A flag indicating whether to apply the modification
                immediately. If set to True, the changes will be applied.
        """

        root = self.root_transform()
        if root is not None:
            root.hide(mod=mod, apply=apply)
