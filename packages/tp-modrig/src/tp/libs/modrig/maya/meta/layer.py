from __future__ import annotations

from collections.abc import Generator

from maya.api import OpenMaya

from tp.libs.maya import factory
from tp.libs.maya.wrapper import DagNode
from tp.libs.maya.om import attributetypes
from tp.libs.maya.meta.base import MetaBase

from .nodes import SettingsNode
from ..base import constants
from ..descriptors.attributes import AttributeDescriptor


class MetaLayer(MetaBase):
    """MetaClass implementation for a layer in the Maya scene."""

    ID = constants.BASE_LAYER_TYPE

    # region === Overrides === #

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

    # endregion

    # region === Settings === #

    def iterate_settings_nodes(self) -> Generator[SettingsNode]:
        """Iterate over the settings nodes and yields them one by one.

        Yields:
            Yields `SettingsNode` instances one by one.
        """

        for element in self.attribute(constants.LAYER_SETTING_NODES_ATTR):
            source_node = element.child(0).sourceNode()
            if source_node is None:
                continue
            yield SettingsNode(mobj=source_node.object())

    def settings_nodes(self) -> list[SettingsNode]:
        """Return the list of settings nodes associated with the current
        metanode.

        Returns:
            List of `SettingsNode` instances.
        """

        return list(self.iterate_settings_nodes())

    def settings_node(self, settings_id: str) -> SettingsNode | None:
        """Return the settings node with the given ID.

        Args:
            settings_id: The ID of the settings node to retrieve.

        Returns:
            The `SettingsNode` instance with the given ID, or `None` if not
                found.
        """

        found_settings_node: SettingsNode | None = None
        for setting_node in self.iterate_settings_nodes():
            if setting_node.id() == settings_id:
                found_settings_node = setting_node
                break

        return found_settings_node

    def create_settings_node(self, settings_id: str, attr_name: str) -> SettingsNode:
        """Create a new settings node with the given ID and attribute name or
        return the existing one if it already exists.

        Args:
            settings_id: The ID of the settings node to create or retrieve.
            attr_name: The attribute name to associate with the settings node.

        Returns:
            The newly created or existing `SettingsNode` instance.
        """

        settings_node = self.settings_node(settings_id)
        if settings_node is not None:
            return settings_node

        settings_node = SettingsNode()
        settings_node.create(settings_id, id=attr_name)
        new_element = self.attribute(constants.LAYER_SETTING_NODES_ATTR).nextAvailableDestElementPlug()
        self.connect_to_by_plug(new_element.child(0), settings_node)
        new_element.child(1).set(attr_name)
        settings_node.lock(True)

        return settings_node


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

    # endregion

    # region === Root Transform === #

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

    # endregion

    # region === Visibility === #

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

    # endregion
