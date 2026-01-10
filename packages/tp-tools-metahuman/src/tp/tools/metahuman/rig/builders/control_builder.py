"""Control shape builder for MetaHuman rig.

This module provides classes for building various control shapes used in the rig.
Uses tp.libs.maya.wrapper for OpenMaya operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import maya.cmds as cmds

from ..data.skeleton_config import (
    CONTROL_CONFIGS,
    Color,
    ControlShapeConfig,
    RigColors,
    Side,
)
from ..utils.attribute_utils import (
    ATTR_CONFIG_ALL_UNLOCKED,
    ATTR_CONFIG_FK_LIMB,
    ATTR_CONFIG_IK_LIMB,
    TransformAttributeConfig,
    cleanup_attributes,
)
from ..utils.maya_utils import (
    create_control_shape,
    create_nurbs_circle,
    create_offset_group,
    delete_history,
    freeze_transforms,
    get_parent,
    match_transform,
    object_exists,
    reparent_node,
    set_color_override,
)


@dataclass
class ControlResult:
    """Result of control creation."""

    control: str
    offset: str
    shape: str


class ControlBuilder:
    """Builder class for creating rig control curves.

    This class provides methods for creating various types of control curves
    with proper naming, coloring, and attribute setup.
    """

    def __init__(self, parent_group: str = "rig_ctrls"):
        """Initialize the control builder.

        Args:
            parent_group: Default parent group for controls.
        """
        self.parent_group = parent_group

    def create_circle_control(
        self,
        name: str,
        config: Optional[ControlShapeConfig] = None,
        match_to: Optional[str] = None,
        side: Optional[Side] = None,
        color: Optional[Color] = None,
        rotate_shape: bool = True,
        parent: Optional[str] = None,
        create_offset: bool = True,
        attr_config: Optional[TransformAttributeConfig] = None,
        match_position_only: bool = False,
    ) -> ControlResult:
        """Create a control curve based on configuration.

        Args:
            name: Name for the control (without _ctrl suffix).
            config: Control shape configuration.
            match_to: Optional object to match transform to.
            side: Optional side for automatic coloring.
            color: Optional explicit color (overrides side-based color).
            rotate_shape: If True, rotate shape 90 degrees on Y.
            parent: Optional parent for the control.
            create_offset: If True, create an offset group.
            attr_config: Optional attribute configuration.
            match_position_only: If True, only match position (keep world orientation).

        Returns:
            ControlResult with control, offset, and shape names.
        """
        config = config or ControlShapeConfig()
        ctrl_name = f"{name}_ctrl"

        # Create the control using the appropriate shape type
        ctrl = create_control_shape(ctrl_name, config)

        # Get the shape(s)
        shapes = cmds.listRelatives(ctrl, shapes=True, type="nurbsCurve") or []
        shape = shapes[0] if shapes else f"{ctrl}Shape"

        # Rotate shape if needed
        if rotate_shape and "root" not in name:
            cmds.setAttr(f"{ctrl}.ry", 90)

        # Freeze transforms
        freeze_transforms(ctrl)

        # Match to target if specified
        if match_to and object_exists(match_to):
            if match_position_only:
                # Only match position, keep world orientation
                match_transform(ctrl, match_to, translate=True, rotate=False)
            else:
                match_transform(ctrl, match_to)

        # Determine color
        ctrl_color = color
        if ctrl_color is None:
            ctrl_color = self._get_side_color(name, side)

        # Apply color to all shapes
        for shp in shapes:
            if object_exists(shp):
                set_color_override(shp, ctrl_color)

        # Create offset group
        offset_name = None
        if create_offset:
            offset_name = f"{name}_offset"
            create_offset_group(ctrl, offset_name)

        # Parent to group (use OpenMaya 2.0 utilities)
        parent_node = parent or self.parent_group
        if parent_node and object_exists(parent_node):
            node_to_parent = offset_name if offset_name else ctrl
            if object_exists(node_to_parent):
                current_parent = get_parent(node_to_parent)
                if current_parent != parent_node:
                    reparent_node(node_to_parent, parent_node)

        # Apply attribute configuration
        if attr_config:
            cleanup_attributes(ctrl, attr_config)

        return ControlResult(
            control=ctrl, offset=offset_name or "", shape=shape
        )

    def create_text_control(
        self,
        name: str,
        text: str = "+",
        match_to: Optional[str] = None,
        side: Optional[Side] = None,
        scale: float = 10.0,
        parent: Optional[str] = None,
    ) -> ControlResult:
        """Create a text-based control curve (for switches).

        Args:
            name: Name for the control.
            text: Text to display.
            match_to: Optional object to match transform to.
            side: Optional side for positioning.
            scale: Scale of the text.
            parent: Optional parent.

        Returns:
            ControlResult with control info.
        """
        # Create empty group first
        if not cmds.objExists(name):
            cmds.group(name=name, empty=True)

        # Create text curves
        text_curves = cmds.textCurves(text=text, name=name, object=True)
        text_shape = f"{name}Shape"

        # Get all nurbs curve shapes and parent them to the main node
        if cmds.objExists(text_shape):
            shapes = cmds.listRelatives(
                text_shape, allDescendents=True, type="nurbsCurve"
            )
            if shapes:
                for shape in shapes:
                    cmds.parent(shape, name, shape=True, relative=True)
            cmds.delete(text_shape)

        # Match transform if specified
        if match_to and cmds.objExists(match_to):
            match_transform(name, match_to)

        # Set rotation and scale
        cmds.setAttr(f"{name}.rx", 90)
        cmds.setAttr(f"{name}.sx", scale)
        cmds.setAttr(f"{name}.sy", scale)
        cmds.setAttr(f"{name}.sz", scale)

        # Position offset based onside.
        if side == Side.LEFT:
            cmds.setAttr(f"{name}.tx", 30)
        elif side == Side.RIGHT:
            cmds.setAttr(f"{name}.tx", -30)

        # Freeze transforms
        freeze_transforms(name)

        # Parent to group
        parent_node = parent or self.parent_group
        if parent_node and cmds.objExists(parent_node):
            cmds.parent(name, parent_node)

        return ControlResult(
            control=name,
            offset="",
            shape=f"{name}Shape" if cmds.objExists(f"{name}Shape") else "",
        )

    def create_global_control(self) -> ControlResult:
        """Create the global control.

        Returns:
            ControlResult for the global control.
        """
        config = CONTROL_CONFIGS["global"]
        result = self.create_circle_control(
            name="global",
            config=config,
            color=RigColors.GLOBAL,
            rotate_shape=False,
            attr_config=ATTR_CONFIG_ALL_UNLOCKED,
        )
        return result

    def create_body_offset_control(self) -> ControlResult:
        """Create the body offset control.

        Returns:
            ControlResult for the body offset control.
        """
        config = CONTROL_CONFIGS["body_offset"]
        result = self.create_circle_control(
            name="body_offset",
            config=config,
            color=RigColors.GLOBAL,
            rotate_shape=False,
            attr_config=ATTR_CONFIG_ALL_UNLOCKED,
        )
        return result

    def create_body_control(
        self, match_to: str = "hips_ctrl"
    ) -> ControlResult:
        """Create the body control.

        Args:
            match_to: Object to match position to.

        Returns:
            ControlResult for the body control.
        """
        config = CONTROL_CONFIGS["body"]
        result = self.create_circle_control(
            name="body",
            config=config,
            match_to=match_to,
            color=RigColors.BODY,
            rotate_shape=False,
            attr_config=ATTR_CONFIG_ALL_UNLOCKED,
            match_position_only=True,
        )
        return result

    def create_fk_limb_control(
        self,
        name: str,
        side: Side,
        match_to: str,
        parent: Optional[str] = None,
        is_thigh: bool = False,
    ) -> ControlResult:
        """Create an FK limb control.

        Args:
            name: Base name for the control.
            side: Body side.
            match_to: Joint to match position to.
            parent: Optional parent control.
            is_thigh: If True, use larger radius for thigh.

        Returns:
            ControlResult for the FK control.
        """
        config_key = "limb_fk_thigh" if is_thigh else "limb_fk"
        config = CONTROL_CONFIGS.get(config_key, CONTROL_CONFIGS["limb_fk"])

        ctrl_base = f"{name}_{side.value}_fk"
        color = (
            RigColors.LEFT_BRIGHT
            if side == Side.LEFT
            else RigColors.RIGHT_BRIGHT
        )

        result = self.create_circle_control(
            name=ctrl_base,
            config=config,
            match_to=match_to,
            color=color,
            parent=parent,
            attr_config=ATTR_CONFIG_FK_LIMB,
        )

        # Delete history
        delete_history(result.control)

        return result

    def create_ik_limb_control(
        self, name: str, side: Side, match_to: Optional[str] = None
    ) -> ControlResult:
        """Create an IK limb control.

        Args:
            name: Base name for the control (hand/foot).
            side: Body side.
            match_to: Joint to match position to (optional).

        Returns:
            ControlResult for the IK control.
        """
        # Use larger config for leg IK controls
        if name == "foot":
            config = CONTROL_CONFIGS["limb_ik_leg"]
        else:
            config = CONTROL_CONFIGS["limb_ik"]

        ctrl_base = f"{name}_{side.value}_ik"
        color = (
            RigColors.LEFT_BRIGHT
            if side == Side.LEFT
            else RigColors.RIGHT_BRIGHT
        )

        result = self.create_circle_control(
            name=ctrl_base,
            config=config,
            match_to=match_to,
            color=color,
            attr_config=ATTR_CONFIG_IK_LIMB,
        )

        # Delete history
        delete_history(result.control)

        return result

    def create_pole_vector_control(
        self,
        limb_type: str,
        side: Side,
        position: Tuple[float, float, float],
    ) -> ControlResult:
        """Create a pole vector control.

        Args:
            limb_type: Type of limb ("arm" or "leg").
            side: Body side.
            position: World position for the control (already in limb plane).

        Returns:
            ControlResult for the pole vector control.
        """
        config = CONTROL_CONFIGS["pole_vector"]
        ctrl_base = f"{limb_type}_pole_vector_{side.value}"
        color = (
            RigColors.LEFT_BRIGHT
            if side == Side.LEFT
            else RigColors.RIGHT_BRIGHT
        )

        # Create the control using the configured shape type
        ctrl_name = f"{ctrl_base}_ctrl"
        ctrl = create_control_shape(ctrl_name, config)

        # Position control at the calculated pole vector position.
        cmds.xform(ctrl, worldSpace=True, translation=position)

        # Freeze transforms
        freeze_transforms(ctrl)

        # Color all shapes
        shapes = cmds.listRelatives(ctrl, shapes=True, type="nurbsCurve") or []
        for shape in shapes:
            if cmds.objExists(shape):
                set_color_override(shape, color)

        # Create offset
        offset_name = f"{ctrl_base}_offset"
        create_offset_group(ctrl, offset_name)

        # Parent to rig_ctrls
        if cmds.objExists(self.parent_group):
            cmds.parent(offset_name, self.parent_group)

        shape = shapes[0] if shapes else f"{ctrl}Shape"
        return ControlResult(control=ctrl, offset=offset_name, shape=shape)

    def create_pole_vector_match(
        self, limb_type: str, side: Side, source_ctrl: str
    ) -> str:
        """Create a pole vector match locator (for FK/IK snapping).

        Args:
            limb_type: Type of limb.
            side: Body side.
            source_ctrl: Source control to duplicate from.

        Returns:
            Name of the match control.
        """
        match_name = f"{limb_type}_pole_vector_{side.value}_match"
        cmds.duplicate(source_ctrl, name=match_name)
        cmds.scale(0.3, 0.3, 0.3, match_name, relative=True)

        # Create offset
        offset_name = f"{match_name}_offset"
        create_offset_group(match_name, offset_name)

        if cmds.objExists(self.parent_group):
            cmds.parent(offset_name, self.parent_group)

        # Hide by default
        cmds.setAttr(f"{offset_name}.visibility", 0)

        return match_name

    def _get_side_color(self, name: str, side: Optional[Side] = None) -> Color:
        """Determine the color based on name or side.

        Args:
            name: Control name.
            side: Optional explicit side.

        Returns:
            Appropriate color for the control.
        """
        if side == Side.LEFT or "_l_" in name or name.endswith("_l"):
            return RigColors.LEFT
        elif side == Side.RIGHT or "_r_" in name or name.endswith("_r"):
            return RigColors.RIGHT
        else:
            return RigColors.CENTER
