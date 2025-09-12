from __future__ import annotations

from typing import Unpack, Any

from tp.libs.maya.wrapper import DGNode
from tp.libs.maya.om import attributetypes

from .control import ControlNode, CreateControlParams
from ...base import constants


class CreateGuideParams(CreateControlParams):
    pass


class GuideNode(ControlNode):
    """Class that defines a guide node in the rigging system."""

    @staticmethod
    def is_guide(node: DGNode) -> bool:
        """Whether the specified node is a guide node.

        Args:
            node: The node to check.

        Returns:
            `True` if the specified node is a guide node; `False` otherwise.
        """

        return node.hasAttribute(constants.IS_GUIDE_ATTR)

    # region === Creation === #

    # noinspection PyMethodOverriding
    def create(self, **params: Unpack[CreateGuideParams]) -> GuideNode:
        attributes = params.get("attributes", [])

        params["attributes"] = self._merge_user_guide_attributes(params, attributes)

        super().create(**params)
        return self

    # noinspection PyTypedDict
    @staticmethod
    def _merge_user_guide_attributes(
        params: CreateGuideParams,
        user_attributes: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Merges the default guide attributes with the ones provided by the
        user.

        Args:
            params: Parameters for the guide creation.
            user_attributes: List of user-provided attributes to merge with
                the default ones.

        Returns:
            Merged list of guide attributes.
        """

        user_attributes = user_attributes or []
        guide_attributes = GUIDE_ATTRIBUTES.copy()
        guide_attributes[constants.ID_ATTR]["value"] = params.get("id", "GUIDE_RENAME")
        guide_attributes[constants.GUIDE_DISPLAY_AXIS_SHAPE_ATTR]["value"] = params.get(
            constants.GUIDE_DISPLAY_AXIS_SHAPE_ATTR, False
        )
        guide_attributes[constants.GUIDE_AUTO_ALIGN_ATTR]["value"] = params.get(
            constants.GUIDE_AUTO_ALIGN_ATTR, True
        )
        guide_attributes[constants.GUIDE_MIRROR_ATTR]["value"] = params.get(
            constants.GUIDE_MIRROR_ATTR, True
        )
        guide_attributes[constants.GUIDE_MIRROR_BEHAVIOR_ATTR]["value"] = params.get(
            constants.GUIDE_MIRROR_BEHAVIOR_ATTR, 0
        )
        guide_attributes[constants.GUIDE_AUTO_ALIGN_UP_VECTOR_ATTR]["value"] = (
            params.get(
                constants.GUIDE_AUTO_ALIGN_UP_VECTOR_ATTR, constants.DEFAULT_UP_VECTOR
            )
        )
        guide_attributes[constants.GUIDE_AUTO_ALIGN_AIM_VECTOR_ATTR]["value"] = (
            params.get(
                constants.GUIDE_AUTO_ALIGN_AIM_VECTOR_ATTR, constants.DEFAULT_AIM_VECTOR
            )
        )
        guide_attributes[constants.GUIDE_PIVOT_SHAPE_ATTR]["value"] = params.get(
            constants.GUIDE_PIVOT_SHAPE_ATTR, ""
        )
        guide_attributes[constants.GUIDE_PIVOT_COLOR_ATTR]["value"] = params.get(
            constants.GUIDE_PIVOT_COLOR_ATTR, (0, 0, 0)
        )
        guide_attributes[constants.GUIDE_PIVOT_SHAPE_TYPE_ATTR]["value"] = params.get(
            constants.GUIDE_PIVOT_SHAPE_TYPE_ATTR, 0
        )

        for user_attr in user_attributes:
            name = user_attr["name"]
            if name in guide_attributes:
                guide_attributes[name]["value"] = user_attr.get("value")
            else:
                guide_attributes[name] = user_attr

        return list(guide_attributes.values())

    # endregion

    # region === Shape === #

    def shape_node(self) -> ControlNode | None:
        """Return the shape node connected to this guide, if any.

        Returns:
            The connected shape node or `None` if no shape is connected.
        """

        found_shape_node: ControlNode | None = None
        for destination_plug in self.attribute(
            constants.GUIDE_SHAPE_ATTR
        ).destinations():
            found_shape_node = ControlNode(destination_plug.node().object())
            break

        return found_shape_node

    # endregion


GUIDE_ATTRIBUTES: dict[str, Any] = {
    constants.ID_ATTR: {
        "type": attributetypes.kMFnDataString,
        "name": constants.ID_ATTR,
        "default": "",
        "channelBox": False,
        "keyable": False,
        "locked": True,
    },
    constants.IS_GUIDE_ATTR: {
        "type": attributetypes.kMFnNumericBoolean,
        "name": constants.IS_GUIDE_ATTR,
        "default": True,
        "value": True,
        "channelBox": False,
        "keyable": False,
        "locked": True,
    },
    constants.GUIDE_DISPLAY_AXIS_SHAPE_ATTR: {
        "type": attributetypes.kMFnNumericBoolean,
        "name": constants.GUIDE_DISPLAY_AXIS_SHAPE_ATTR,
        "default": False,
        "channelBox": True,
        "keyable": False,
        "locked": False,
    },
    constants.GUIDE_AUTO_ALIGN_ATTR: {
        "type": attributetypes.kMFnNumericBoolean,
        "name": constants.GUIDE_AUTO_ALIGN_ATTR,
        "default": True,
        "channelBox": True,
        "keyable": False,
        "locked": False,
    },
    constants.GUIDE_AUTO_ALIGN_UP_VECTOR_ATTR: {
        "type": attributetypes.kMFnNumeric3Float,
        "name": constants.GUIDE_AUTO_ALIGN_UP_VECTOR_ATTR,
        "default": constants.DEFAULT_UP_VECTOR,
        "channelBox": True,
        "keyable": False,
        "locked": False,
    },
    constants.GUIDE_AUTO_ALIGN_AIM_VECTOR_ATTR: {
        "type": attributetypes.kMFnNumeric3Float,
        "name": constants.GUIDE_AUTO_ALIGN_AIM_VECTOR_ATTR,
        "default": constants.DEFAULT_AIM_VECTOR,
        "channelBox": True,
        "keyable": False,
        "locked": False,
    },
    constants.GUIDE_MIRROR_ATTR: {
        "type": attributetypes.kMFnNumericBoolean,
        "name": constants.GUIDE_MIRROR_ATTR,
        "channelBox": True,
        "keyable": False,
        "locked": False,
    },
    constants.GUIDE_MIRROR_BEHAVIOR_ATTR: {
        "type": attributetypes.kMFnkEnumAttribute,
        "name": constants.GUIDE_MIRROR_BEHAVIOR_ATTR,
        "enums": constants.GUIDE_MIRROR_BEHAVIOR_TYPES,
        "default": 0,
        "value": 0,
        "channelBox": True,
        "keyable": False,
        "locked": False,
    },
    constants.GUIDE_MIRROR_PLANE_ATTR: {
        "type": attributetypes.kMFnkEnumAttribute,
        "name": constants.GUIDE_MIRROR_PLANE_ATTR,
        "enums": ["xy", "yz", "xz"],
        "default": 1,
        "value": 1,
        "channelBox": True,
        "keyable": False,
        "locked": False,
    },
    constants.GUIDE_MIRROR_SCALED_ATTR: {
        "type": attributetypes.kMFnNumericBoolean,
        "name": constants.GUIDE_MIRROR_SCALED_ATTR,
        "default": False,
        "value": False,
        "channelBox": False,
        "keyable": False,
        "locked": False,
    },
    constants.GUIDE_PIVOT_SHAPE_ATTR: {
        "type": attributetypes.kMFnDataString,
        "name": constants.GUIDE_PIVOT_SHAPE_ATTR,
        "channelBox": False,
        "keyable": False,
        "locked": False,
    },
    constants.GUIDE_PIVOT_COLOR_ATTR: {
        "type": attributetypes.kMFnNumeric3Float,
        "name": constants.GUIDE_PIVOT_COLOR_ATTR,
        "channelBox": False,
        "keyable": False,
        "locked": False,
    },
    constants.GUIDE_PIVOT_SHAPE_TYPE_ATTR: {
        "type": attributetypes.kMFnkEnumAttribute,
        "name": constants.GUIDE_PIVOT_SHAPE_TYPE_ATTR,
        "enums": ["Curve", "Surface"],
    },
    constants.GUIDE_SHAPE_ATTR: {
        "type": attributetypes.kMFnMessageAttribute,
        "name": constants.GUIDE_SHAPE_ATTR,
    },
    constants.GUIDE_SNAP_PIVOT_ATTR: {
        "type": attributetypes.kMFnMessageAttribute,
        "name": constants.GUIDE_SNAP_PIVOT_ATTR,
    },
    constants.GUIDE_SHAPE_PRIMARY_ATTR: {
        "type": attributetypes.kMFnMessageAttribute,
        "name": constants.GUIDE_SHAPE_PRIMARY_ATTR,
    },
}
