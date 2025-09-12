from __future__ import annotations

from typing import TypedDict, Unpack, Any

from loguru import logger
from maya.api import OpenMaya

from tp.libs.maya.curves import ShapeType
from tp.libs.maya.om import apitypes, attributetypes, nodes
from tp.libs.maya.wrapper import DagNode, lock_state_attr_context, LOCAL_TRANSFORM_ATTRS

from ...base import constants


class CreateControlParams(TypedDict, total=False):
    id: str
    name: str
    type: str
    modRigType: str
    translate: tuple[float, float, float] | list[float]
    rotate: tuple[float, float, float, float] | list[float]
    scale: tuple[float, float, float] | list[float]
    rotationOrder: int
    worldMatrix: (
        tuple[
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
        ]
        | list[float]
        | None
    )
    parent: str | None
    shapeType: ShapeType
    shape: str | dict[str, Any]
    shapeSpace: int
    color: tuple[float, float, float] | list[float]
    attributes: list[dict[str, Any]]
    selectionChildHighlighting: bool


class ControlNode(DagNode):
    def id(self) -> str:
        """Return the ID of this settings node.

        The ID is a UUID (Unique Universal Identifier) assigned to the node
        when it is created. Used to uniquely identify the node within the
        scene.

        Returns:
            The node ID as a string.
        """

        id_attr = self.attribute(constants.ID_ATTR)
        return id_attr.value() if id_attr is not None else ""

    # region === Creation === #

    # noinspection PyMethodOverriding
    def create(self, **params: Unpack[CreateControlParams]) -> ControlNode:
        world_matrix = params.get("worldMatrix")
        translate = params.get("translate", (0.0, 0.0, 0.0))
        rotate = params.get("rotate", (0.0, 0.0, 0.0, 1.0))
        scale = params.get("scale", (1.0, 1.0, 1.0))
        parent: DagNode | None = params.get("parent")
        shape = params.get("shape")
        shape_type = params.get("shapeType", ShapeType.Curve)
        shape_space = params.get("shapeSpace", OpenMaya.MSpace.kWorld)
        color = params.get("color")

        params["type"] = "transform"
        params["name"] = params.get("name", "Control")
        params["parent"] = None
        params["rotationOrder"] = params.get("rotationOrder", apitypes.kRotateOrder_XYZ)

        try:
            node = nodes.deserialize_node(params)[0]
        except Exception:
            logger.error(
                f"Failed to deserialize node: {params['name']} from structure",
                exc_info=True,
                extra={"data": params["name"]},
            )
            raise
        self.setObject(node)

        with lock_state_attr_context(
            self,
            ["rotateOrder"] + LOCAL_TRANSFORM_ATTRS + ["translate", "rotate", "scale"],
            state=False,
        ):
            # Set the rotation order of the control.
            self.setRotationOrder(params["rotationOrder"])

            # Set the transform of the control.
            if world_matrix is None:
                self.setTranslation(
                    OpenMaya.MVector(translate), space=OpenMaya.MSpace.kWorld
                )
                # noinspection PyTypeChecker
                self.setRotation(rotate, space=OpenMaya.MSpace.kWorld)
                self.setScale(scale)
            else:
                self.setWorldMatrix(OpenMaya.MMatrix(world_matrix))

            # If a parent is provided, set it now that the world matrix has
            # been set.
            if parent is not None:
                self.setParent(parent, maintain_offset=True)

            # Make sure the ` shear ` attribute is zeroed out to avoid any
            # unexpected transformations.
            self.attribute("shear").set(OpenMaya.MVector(0, 0, 0))

        # Load the control shape from the library or from a dictionary
        # containing the serialized shape data.
        if shape:
            if isinstance(shape, str):
                self.add_shape_from_library(shape, replace=True, shape_type=shape_type)
                if color:
                    self.set_shape_color(color, shape_index=-1)
            else:
                self.add_shape_from_data(
                    shape, replace=True, shape_type=shape_type, space=shape_space
                )

        # Add the ID attribute to the control node.
        self.addAttribute(
            constants.ID_ATTR,
            type=attributetypes.kMFnDataString,
            value=params.get("id", params["name"]),
            default="",
            locked=True,
        )

        # If child highlighting is specified, set it on the control node.
        child_highlighting = params.get("selectionChildHighlighting", True)
        if child_highlighting is not None:
            self.attribute("selectionChildHighlighting").set(child_highlighting)

        # Make sure the `rotateOrder` attribute is visible and keyable.
        rotate_order = self.attribute("rotateOrder")
        rotate_order.show()
        rotate_order.setKeyable(True)

        return self

    # endregion

    # region === Shape === #

    def add_shape_from_library(
        self,
        shape_name: str,
        replace: bool = False,
        maintain_colors: bool = False,
        shape_type: int = ShapeType,
    ):
        pass
