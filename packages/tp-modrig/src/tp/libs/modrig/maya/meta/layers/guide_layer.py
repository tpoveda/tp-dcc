from __future__ import annotations

from collections.abc import Generator

from tp.libs.maya.wrapper import Plug
from tp.libs.maya.om import attributetypes

from ..layer import MetaLayer
from ..nodes import GuideNode, SettingsNode
from ...base import constants


class MetaGuidesLayer(MetaLayer):
    ID = constants.GUIDE_LAYER_TYPE

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
                {
                    "name": constants.GUIDES_LAYER_GUIDES_ATTR,
                    "isArray": True,
                    "locked": False,
                    "children": [
                        {
                            "name": constants.GUIDES_LAYER_GUIDE_ID_ATTR,
                            "type": attributetypes.kMFnDataString,
                        },
                        {
                            "name": constants.GUIDES_LAYER_GUIDE_NODE_ATTR,
                            "type": attributetypes.kMFnMessageAttribute,
                        },
                        {
                            "name": constants.GUIDES_LAYER_SRTS_ATTR,
                            "type": attributetypes.kMFnMessageAttribute,
                            "isArray": True,
                        },
                        {
                            "name": constants.GUIDES_LAYER_SHAPE_NODE_ATTR,
                            "type": attributetypes.kMFnMessageAttribute,
                        },
                        {
                            "name": constants.GUIDES_LAYER_SOURCE_GUIDES_ATTR,
                            "type": attributetypes.kMFnCompoundAttribute,
                            "isArray": True,
                            "children": [
                                {
                                    "name": constants.GUIDES_LAYER_SOURCE_GUIDE_ATTR,
                                    "type": attributetypes.kMFnMessageAttribute,
                                },
                                {
                                    "name": constants.GUIDES_LAYER_CONSTRAINT_NODES_ATTR,
                                    "type": attributetypes.kMFnMessageAttribute,
                                    "isArray": True,
                                },
                            ],
                        },
                        {
                            "name": constants.GUIDES_LAYER_GUIDE_MIRROR_ROTATION_ATTR,
                            "type": attributetypes.kMFnNumericBoolean,
                        },
                        {
                            "name": constants.GUIDES_LAYER_GUIDE_AUTO_ALIGN_ATTR,
                            "type": attributetypes.kMFnNumericBoolean,
                        },
                        {
                            "name": constants.GUIDES_LAYER_GUIDE_AIM_VECTOR_ATTR,
                            "type": attributetypes.kMFnNumeric3Float,
                        },
                        {
                            "name": constants.GUIDES_LAYER_GUIDE_UP_VECTOR_ATTR,
                            "type": attributetypes.kMFnNumeric3Float,
                        },
                    ],
                },
                {
                    "name": constants.GUIDES_LAYER_GUIDE_VISIBILITY_ATTR,
                    "type": attributetypes.kMFnNumericBoolean,
                    "default": True,
                    "value": True,
                },
                {
                    "name": constants.GUIDES_LAYER_GUIDE_CONTROL_VISIBILITY_ATTR,
                    "type": attributetypes.kMFnNumericBoolean,
                    "default": False,
                    "value": False,
                },
                {
                    "name": constants.GUIDES_LAYER_PIN_SETTINGS_ATTR,
                    "children": [
                        {
                            "name": constants.GUIDES_LAYER_PINNED_ATTR,
                            "type": attributetypes.kMFnNumericBoolean,
                        },
                        {
                            "name": constants.GUIDES_LAYER_PINNED_CONSTRAINTS_ATTR,
                            "type": attributetypes.kMFnDataString,
                        },
                    ],
                },
                {
                    "name": constants.GUIDES_LAYER_LIVE_LINK_NODES_ATTR,
                    "type": attributetypes.kMFnMessageAttribute,
                    "isArray": True,
                },
                {
                    "name": constants.GUIDES_LAYER_LIVE_LINK_IS_ACTIVE_ATTR,
                    "type": attributetypes.kMFnNumericBoolean,
                    "value": False,
                    "default": False,
                },
                {
                    "name": constants.GUIDES_LAYER_CONNECTOR_GROUP_ATTR,
                    "type": attributetypes.kMFnMessageAttribute,
                },
                {
                    "name": constants.GUIDES_LAYER_DG_GRAPH_ATTR,
                    "isArray": True,
                    "children": [
                        {
                            "name": constants.GUIDES_LAYER_DG_GRAPH_ID_ATTR,
                            "type": attributetypes.kMFnDataString,
                        },
                        {
                            "name": constants.GUIDES_LAYER_DG_GRAPH_NODES_ATTR,
                            "type": attributetypes.kMFnCompoundAttribute,
                            "isArray": True,
                            "children": [
                                {
                                    "name": constants.GUIDES_LAYER_DG_GRAPH_NODE_ID_ATTR,
                                    "type": attributetypes.kMFnDataString,
                                },
                                {
                                    "name": constants.GUIDES_LAYER_DG_GRAPH_NODE_ATTR,
                                    "type": attributetypes.kMFnMessageAttribute,
                                },
                            ],
                        },
                        {
                            "name": constants.GUIDES_LAYER_DG_GRAPH_NAME_ATTR,
                            "type": attributetypes.kMFnDataString,
                        },
                        {
                            "name": constants.GUIDES_LAYER_DG_GRAPH_METADATA_ATTR,
                            "type": attributetypes.kMFnDataString,
                        },
                        {
                            "name": constants.GUIDES_LAYER_DG_GRAPH_INPUT_NODE_ATTR,
                            "type": attributetypes.kMFnMessageAttribute,
                        },
                        {
                            "name": constants.GUIDES_LAYER_DG_GRAPH_OUTPUT_NODE_ATTR,
                            "type": attributetypes.kMFnMessageAttribute,
                        },
                    ],
                },
            ]
        )

        return attrs

    # endregion

    # region === Settings === #

    def guide_settings(self) -> SettingsNode | None:
        """Returns the settings node for the guide layer.

        Returns:
            The settings node instance or None if not found.
        """

        return self.settings_node(constants.GUIDE_LAYER_TYPE)

    # endregion

    # region === Guides === #

    def iterate_guides_compound(self) -> Generator[Plug, None, None]:
        """Generator that iterates over all the guide compound plugs in the layer.

        Yields:
            The next guide compound plug.
        """

        guide_plug = self.attribute(constants.GUIDES_LAYER_GUIDES_ATTR)
        for i in range(guide_plug.evaluateNumElements()):
            yield guide_plug.elementByPhysicalIndex(i)

    def iterate_guides(
        self, include_root: bool = True
    ) -> Generator[GuideNode, None, None]:
        """Generator that iterates over all the guide nodes in the layer.

        Args:
            include_root: Whether to include the root guide node in the
                iteration.

        Yields:
            The next guide node instance.
        """

        if not self.exists():
            return

        for element in self.iterate_guides_compound():
            guide_plug = element.child(0)
            source = guide_plug.sourceNode()
            if source is None:
                continue
            if not include_root and element.child(1).asString() == "root":
                continue
            if not GuideNode.is_guide(source):
                continue
            yield GuideNode(source.object())

    def guides(self, include_root: bool = True) -> list[GuideNode]:
        """Return the list of all the guide nodes in the layer.

        Args:
            include_root: Whether to include the root guide node in the
                iteration.

        Returns:
            The list of guide node instances.
        """

        return list(self.iterate_guides(include_root=include_root))

    def guide(self, guide_id: str) -> GuideNode | None:
        """Return the guide node with the given ID.

        Args:
            guide_id: The ID of the guide node to retrieve.

        Returns:
            The guide node instance or None if not found.
        """

        if not self.exists():
            return None

        found_guide: GuideNode | None = None
        for guide in self.iterate_guides():
            if guide.id() == guide_id:
                found_guide = guide
                break

        return found_guide

    def guide_root(self) -> GuideNode | None:
        """Return the root guide node of the layer.

        Returns:
            The root guide node instance or None if not found.
        """

        if not self.exists():
            return None

        root_guide: GuideNode | None = None
        for element in self.iterate_guides_compound():
            is_root_flag = element.child(2)
            if not is_root_flag:
                continue
            source = element.child(0).sourceNode()
            if source is None:
                continue
            root_guide = GuideNode(source.object())
            break

        return root_guide

    def guide_count(self) -> int:
        """Return the number of guides in the layer.

        Returns:
            The number of guides in the layer.
        """

        return self.attribute(constants.GUIDES_LAYER_GUIDES_ATTR).evaluateNumElements()

    def guide_plug_by_id(self, guide_id: str) -> Plug | None:
        """Return the guide compound plug with the given ID.

        Args:
            guide_id: The ID of the guide node to retrieve.

        Returns:
            The guide compound plug or None if not found.
        """

        found_plug: Plug | None = None
        for element in self.iterate_guides_compound():
            id_plug = element.child(1)
            if id_plug.asString() == guide_id:
                found_plug = element
                break

        return found_plug

    def guide_node_plug_by_id(self, guide_id: str) -> Plug | None:
        """Return the guide node plug with the given ID.

        Args:
            guide_id: The ID of the guide node to retrieve.

        Returns:
            The guide node plug or None if not found.
        """

        guide_element_plug = self.guide_plug_by_id(guide_id)
        return guide_element_plug.child(0) if guide_element_plug else None

    def source_guide_plug_by_id(self, guide_id: str, source_index: int) -> Plug | None:
        """Return the source guide plug for the guide with the given ID.

        Args:
            guide_id: The ID of the guide node to retrieve.
            source_index: The index of the source guide to retrieve.

        Returns:
            The source guide plug or `None` if not found.
        """

        guide_element_plug = self.guide_plug_by_id(guide_id)
        if not guide_element_plug:
            return None

        return guide_element_plug.child(4)[source_index]

    def add_child_guide(self, guide: GuideNode):
        """Add the given guide node as a child of the layer.

        Args:
            guide: The guide node instance to add.
        """

        guides_plug = self.attribute(constants.GUIDES_LAYER_GUIDES_ATTR)
        guides_plug.isLocked = False
        element = guides_plug.nextAvailableDestElementPlug()
        guide.attribute("message").connect(element.child(0))
        shape_node = guide.shape_node()
        if shape_node is not None:
            shape_node.attribute("message").connect(element.child(3))
        element.child(1).setAsProxy(guide.attribute(constants.ID_ATTR))
        element.child(5).setAsProxy(guide.attribute(constants.GUIDE_MIRROR_ATTR))
        element.child(6).setAsProxy(guide.attribute(constants.GUIDE_AUTO_ALIGN_ATTR))
        element.child(7).setAsProxy(
            guide.attribute(constants.GUIDE_AUTO_ALIGN_AIM_VECTOR_ATTR)
        )
        element.child(8).setAsProxy(
            guide.attribute(constants.GUIDE_AUTO_ALIGN_UP_VECTOR_ATTR)
        )

    # noinspection PyShadowingBuiltins
    def create_guide(self, id: str = "", parent: str | None = None):
        parent = self.root_transform() if parent is None else self.guide(parent)

        guide = GuideNode()
        guide.create(parent=parent)
        self.add_child_guide(guide)

        guide_plug = self.guide_plug_by_id(id)
        if guide_plug is None:
            return guide

        return guide

    # endregion
