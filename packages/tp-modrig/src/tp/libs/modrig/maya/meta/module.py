from __future__ import annotations

from maya.api import OpenMaya

from tp.libs.maya import factory
from tp.libs.maya.om import attributetypes
from tp.libs.maya.wrapper import DagNode
from tp.libs.maya.meta.base import MetaBase

from ..base import constants


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
                    name=constants.IS_COMPONENT_ATTR,
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
