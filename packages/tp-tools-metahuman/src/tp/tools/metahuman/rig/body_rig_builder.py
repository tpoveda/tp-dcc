"""MetaHuman Body Rig Builder.

This module provides the main class for building MetaHuman body rig controls.
It orchestrates all the individual builders to create a complete animation rig.
Uses tp.libs.maya.wrapper for OpenMaya operations.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import maya.cmds as cmds

from .builders import (
    ControlBuilder,
    FingerControlBuilder,
    FKIKSwitchBuilder,
    ReverseFootBuilder,
    SkeletonBuilder,
    SpaceSwitchBuilder,
)
from .data.skeleton_config import (
    CONTROL_CONFIGS,
    ControlShapeConfig,
    RigColors,
    Side,
    get_skeleton_joints_with_radius,
    is_constrainable_joint,
)
from .meta import constants as meta_constants
from .meta.layers import (
    MetaHumanControlsLayer,
    MetaHumanFKIKLayer,
    MetaHumanReverseFootLayer,
    MetaHumanSkeletonLayer,
    MetaHumanSpaceSwitchLayer,
)
from .meta.rig import MetaMetaHumanRig
from .utils.attribute_utils import add_string_attribute, connect_attribute
from .utils.maya_utils import (
    create_group,
    create_pole_vector_locator,
    current_up_axis,
    delete_if_exists,
    ensure_plugin_loaded,
    get_parent,
    object_exists,
    set_color_override,
    show_confirm_dialog,
)

if TYPE_CHECKING:
    from tp.libs.maya.wrapper import DagNode

logger = logging.getLogger(__name__)


@dataclass
class RigBuildResult:
    """Result of the rig build process."""

    success: bool
    message: str
    root_joint: str | None = None
    motion_skeleton: str | None = None
    controls_created: list[str] = field(default_factory=list)
    meta_rig: MetaMetaHumanRig | None = None


class MetaHumanBodyRigBuilder:
    """Main class for building MetaHuman body rig controls.

    This class orchestrates all the individual builders to create a complete
    animation rig for MetaHuman characters in Maya.

    Example:
        >>> builder = MetaHumanBodyRigBuilder(motion=True)
        >>> result = builder.build()
        >>> if result.success:
        ...     print("Rig built successfully!")
    """

    # Group names
    RIG_SETUP_GROUP = "rig_setup"
    RIG_CTRLS_GROUP = "rig_ctrls"

    def __init__(self, motion: bool = True, show_dialogs: bool = True):
        """Initialize the rig builder.

        Args:
            motion: If True, create a motion skeleton for animation.
                   If False, create controls for the existing skeleton.
            show_dialogs: If True, show confirmation dialogs during build.
                         If False, skip dialogs and proceed with default actions.
        """

        self._motion = motion
        self._show_dialogs = show_dialogs
        self._root_joint: str | None = None
        self._root_suffix: str = ""
        self._skel_type: str = "_motion" if motion else ""
        self._restore_up_axis: bool = False

        # Metanode for rig tracking
        self._meta_rig: MetaMetaHumanRig | None = None

        # Layer references
        self._controls_layer: MetaHumanControlsLayer | None = None
        self._fkik_layer: MetaHumanFKIKLayer | None = None

        # Initialize builders.
        self._control_builder = ControlBuilder(self.RIG_CTRLS_GROUP)
        self._skeleton_builder = SkeletonBuilder()
        self._reverse_foot_builder = ReverseFootBuilder(
            self.RIG_SETUP_GROUP, self.RIG_CTRLS_GROUP
        )
        self._space_switch_builder = SpaceSwitchBuilder(self.RIG_CTRLS_GROUP)
        self._finger_builder = FingerControlBuilder(self.RIG_CTRLS_GROUP)
        self._fkik_switch_builder = FKIKSwitchBuilder(self.RIG_CTRLS_GROUP)

    def build(self) -> RigBuildResult:
        """Build the complete MetaHuman body rig.

        Returns:
            `RigBuildResult` with build status and information.
        """

        up_axis = current_up_axis()

        # Detect skeleton.
        if not self._detect_skeleton():
            return RigBuildResult(
                success=False, message="No valid MetaHuman skeleton found."
            )

        self._restore_up_axis = True

        # Check for existing rig.
        if self._motion and not self._handle_existing_rig():
            return RigBuildResult(
                success=False, message="User cancelled rig rebuild."
            )

        # Load required plugins.
        ensure_plugin_loaded("lookdevKit")

        # Register and create metanode system
        self._create_meta_rig()

        # Create rig groups.
        self._create_rig_groups()

        # Create the motion skeleton if needed.
        if self._motion:
            self._create_motion_skeleton()

        # Build FK/IK systems for limbs
        self._build_limb_systems()

        # Create controls layer
        self._create_controls_layer()

        # Create skeleton controls
        self._create_skeleton_controls()

        # Create additional controls
        self._create_additional_controls()

        # Create FK/IK layer
        self._create_fkik_layer()

        # Create FK/IK limb controls
        self._create_fkik_limb_controls()

        # Create reverse foot setup
        self._create_reverse_foot_systems()

        # Create finger controls (motion mode only).
        if self._motion:
            self._create_finger_controls()

        # Create space switches.
        self._create_space_switches()

        # Final setup.
        self._finalize_rig(up_axis)

        # Tag MetaHuman.
        if self._motion:
            self._tag_metahuman()

        cmds.select(clear=True)

        return RigBuildResult(
            success=True,
            message="MetaHuman Body Rig created successfully.",
            root_joint=self._root_joint,
            motion_skeleton="root_motion" if self._motion else None,
            meta_rig=self._meta_rig,
        )

    def _detect_skeleton(self) -> bool:
        """Detect and validate the MetaHuman skeleton.

        Returns:
            `True` if valid skeleton found; `False` otherwise.
        """

        root, suffix = self._skeleton_builder.detect_skeleton_type()

        if not root:
            logger.error("No valid MetaHuman skeleton found.")
            return False

        self._root_joint = root
        self._root_suffix = suffix
        self._skeleton_builder.root_suffix = suffix

        return True

    def _handle_existing_rig(self) -> bool:
        """Handle existing rig - prompt user for rebuild.

        Returns:
            `True` if it should continue with build; `False` otherwise.
        """

        existing_nodes = [
            "root_motion",
            "rig_setup",
            "rig_ctrls",
            "DHIbody:root_loc",
            "metahuman_body_rig_meta",
        ]

        has_existing = any(object_exists(node) for node in existing_nodes)

        if has_existing:
            if self._show_dialogs:
                result = show_confirm_dialog(
                    title="Confirm",
                    message="MetaHuman Body Controls found in scene. Delete and rebuild?",
                    buttons=["Yes", "No"],
                    default_button="Yes",
                    cancel_button="No",
                )
                if result == "Yes":
                    self._delete_existing_rig()
                    return True
                else:
                    return False
            else:
                # No dialog mode (automatically delete existing rig).
                self._delete_existing_rig()
                return True

        return True

    def _delete_existing_rig(self) -> None:
        """Delete existing rig components including metanode."""

        # Delete existing metanode if present
        delete_if_exists("metahuman_body_rig_meta")

        nodes_to_delete = [
            "root_motion",
            "rig_setup",
            "rig_ctrls",
            "face_gui_custom_labels_sceneConfigurationScriptNode",
            "face_gui_custom_labels_uiConfigurationScriptNode",
        ]

        for node in nodes_to_delete:
            delete_if_exists(node)

        # Reset root rotation.
        if self._root_joint and object_exists(self._root_joint):
            cmds.setAttr(f"{self._root_joint}.rotateX", 0)

        if object_exists("headRig_grp"):
            cmds.setAttr("headRig_grp.rotateX", 0)

        # Reset leg joints.
        for side in [Side.LEFT, Side.RIGHT]:
            for part in ["thigh", "calf", "foot", "ball"]:
                joint = f"{part}_{side.value}{self._root_suffix}"
                if object_exists(joint):
                    for axis in ["X", "Y", "Z"]:
                        cmds.setAttr(f"{joint}.rotate{axis}", 0)

    def _create_meta_rig(self) -> None:
        """Create and configure the metanode for the rig.

        This registers the metanode classes and creates the root rig metanode
        which tracks all rig components, groups, and layers.
        """

        from tp.libs.maya.meta.base import MetaRegistry

        # Register metanode classes
        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanControlsLayer)
        MetaRegistry.register_meta_class(MetaHumanSkeletonLayer)
        MetaRegistry.register_meta_class(MetaHumanFKIKLayer)
        MetaRegistry.register_meta_class(MetaHumanSpaceSwitchLayer)
        MetaRegistry.register_meta_class(MetaHumanReverseFootLayer)

        # Create the rig metanode
        self._meta_rig = MetaMetaHumanRig(name="metahuman_body_rig_meta")
        self._meta_rig.attribute(meta_constants.NAME_ATTR).set(
            meta_constants.DEFAULT_RIG_NAME
        )
        self._meta_rig.attribute(meta_constants.RIG_IS_MOTION_MODE_ATTR).set(
            self._motion
        )

        logger.info(
            "MetaHuman rig metanode created: %s", self._meta_rig.name()
        )

    def _create_rig_groups(self) -> None:
        """Create rig hierarchy groups and connect to metanode."""

        # Rig setup group.
        if not object_exists(self.RIG_SETUP_GROUP):
            if self._meta_rig is not None:
                self._meta_rig.create_setup_group(self.RIG_SETUP_GROUP)
            else:
                create_group(self.RIG_SETUP_GROUP, empty=True)

        # Rig controls group.
        delete_if_exists(self.RIG_CTRLS_GROUP)
        if self._meta_rig is not None:
            self._meta_rig.create_controls_group(self.RIG_CTRLS_GROUP)
        else:
            create_group(self.RIG_CTRLS_GROUP, empty=True)

    def _create_motion_skeleton(self) -> None:
        """Create motion skeleton for animation and connect to metanode."""

        self._skeleton_builder.create_motion_skeleton()

        # Connect motion skeleton root to metanode and create skeleton layer
        if self._meta_rig is not None and object_exists("root_motion"):
            from tp.libs.maya.wrapper import node_by_name

            motion_root = node_by_name("root_motion")
            if motion_root is not None:
                self._meta_rig.connect_motion_skeleton(motion_root)

                # Create skeleton layer
                self._create_skeleton_layer(motion_root)

    def _create_skeleton_layer(self, motion_root: "DagNode") -> None:
        """Create the skeleton layer and register all joints.

        Args:
            motion_root: The root joint of the motion skeleton.
        """

        from typing import cast

        from tp.libs.maya.wrapper import node_by_name

        if self._meta_rig is None:
            return

        # Create skeleton layer
        layer = self._meta_rig.create_layer(
            meta_constants.METAHUMAN_SKELETON_LAYER_TYPE,
            "skeleton_layer",
            "skeleton_layer_meta",
        )

        if layer is None:
            logger.warning("Failed to create skeleton layer")
            return

        # Cast to MetaHumanSkeletonLayer for proper type hints
        skeleton_layer = cast(MetaHumanSkeletonLayer, layer)

        # Connect root joint
        skeleton_layer.connect_root_joint(motion_root)
        skeleton_layer.set_is_motion_skeleton(True)

        # Register all motion skeleton joints
        self._register_skeleton_joints(skeleton_layer, motion_root.name())

        # Also connect bind skeleton root if it exists
        if self._root_joint and object_exists(self._root_joint):
            bind_root = node_by_name(self._root_joint)
            if bind_root is not None:
                skeleton_layer.connect_bind_root(bind_root)

        logger.info("Skeleton layer created with joints registered")

    def _register_skeleton_joints(
        self, skeleton_layer: "MetaHumanSkeletonLayer", root_name: str
    ) -> None:
        """Register all joints under the root to the skeleton layer.

        Args:
            skeleton_layer: The skeleton layer to register joints with.
            root_name: Name of the root joint.
        """

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name

        # Get all joints under the root
        all_joints = (
            cmds.listRelatives(root_name, allDescendents=True, type="joint")
            or []
        )

        # Add root joint itself
        all_joints.insert(0, root_name)

        for joint_name in all_joints:
            joint_node = node_by_name(joint_name)
            if joint_node is not None:
                skeleton_layer.add_joint(joint_node)

    def _create_controls_layer(self) -> None:
        """Create the controls layer for tracking all rig controls."""

        from typing import cast

        if self._meta_rig is None:
            return

        # Create controls layer
        layer = self._meta_rig.create_layer(
            meta_constants.METAHUMAN_CONTROLS_LAYER_TYPE,
            "controls_layer",
            "controls_layer_meta",
        )

        if layer is None:
            logger.warning("Failed to create controls layer")
            return

        # Cast to MetaHumanControlsLayer for proper type hints
        self._controls_layer = cast(MetaHumanControlsLayer, layer)

        logger.info("Controls layer created: %s", self._controls_layer.name())

    def _register_control(self, control_name: str) -> None:
        """Register a control with the controls layer.

        Args:
            control_name: Name of the control node to register.
        """

        from tp.libs.maya.wrapper import node_by_name

        if self._controls_layer is None:
            return

        if not object_exists(control_name):
            return

        control_node = node_by_name(control_name)
        if control_node is not None:
            self._controls_layer.add_control(control_node)

    def _create_fkik_layer(self) -> None:
        """Create the FK/IK layer for tracking FK/IK controls and systems."""

        from typing import cast

        if self._meta_rig is None:
            return

        # Create FK/IK layer
        layer = self._meta_rig.create_layer(
            meta_constants.METAHUMAN_FKIK_LAYER_TYPE,
            "fkik_layer",
            "fkik_layer_meta",
        )

        if layer is None:
            logger.warning("Failed to create FK/IK layer")
            return

        # Cast to MetaHumanFKIKLayer for proper type hints
        self._fkik_layer = cast(MetaHumanFKIKLayer, layer)

        logger.info("FK/IK layer created: %s", self._fkik_layer.name())

    def _register_fk_control(self, control_name: str) -> None:
        """Register an FK control with the FK/IK layer.

        Args:
            control_name: Name of the FK control node to register.
        """

        from tp.libs.maya.wrapper import node_by_name

        if self._fkik_layer is None:
            return

        if not object_exists(control_name):
            return

        control_node = node_by_name(control_name)
        if control_node is not None:
            self._fkik_layer.add_fk_control(control_node)

    def _register_ik_control(self, control_name: str) -> None:
        """Register an IK control with the FK/IK layer.

        Args:
            control_name: Name of the IK control node to register.
        """

        from tp.libs.maya.wrapper import node_by_name

        if self._fkik_layer is None:
            return

        if not object_exists(control_name):
            return

        control_node = node_by_name(control_name)
        if control_node is not None:
            self._fkik_layer.add_ik_control(control_node)

    def _register_pole_vector(self, control_name: str) -> None:
        """Register a pole vector control with the FK/IK layer.

        Args:
            control_name: Name of the pole vector control node to register.
        """

        from tp.libs.maya.wrapper import node_by_name

        if self._fkik_layer is None:
            return

        if not object_exists(control_name):
            return

        control_node = node_by_name(control_name)
        if control_node is not None:
            self._fkik_layer.add_pole_vector(control_node)

    def _build_limb_systems(self) -> None:
        """Build FK/IK systems for all limbs."""

        self._skeleton_builder.setup_all_limbs(self._skel_type)

    def _create_skeleton_controls(self) -> None:
        """Create controls for skeleton joints."""

        skeleton_data = get_skeleton_joints_with_radius()

        for joint_name, radius in skeleton_data:
            motion_joint = f"{joint_name}{self._skel_type}"
            ctrl_name = joint_name

            # Handle pelvis -> hips rename.
            if "pelvis" in ctrl_name:
                ctrl_name = ctrl_name.replace("pelvis", "hips")

            if not object_exists(motion_joint):
                continue

            # Use special config for root control, otherwise default.
            if joint_name == "root":
                config = CONTROL_CONFIGS.get(
                    "root", ControlShapeConfig(radius=radius)
                )
                # Root control should be world-oriented
                result = self._control_builder.create_circle_control(
                    name=ctrl_name,
                    config=config,
                    match_to=motion_joint,
                    rotate_shape=False,
                    match_position_only=True,
                )
            else:
                config = ControlShapeConfig(radius=radius)
                result = self._control_builder.create_circle_control(
                    name=ctrl_name,
                    config=config,
                    match_to=motion_joint,
                    rotate_shape=True,
                )

            # Connect control to joint.
            if is_constrainable_joint(joint_name):
                cmds.pointConstraint(
                    result.control,
                    motion_joint,
                    maintainOffset=True,
                    name=f"{result.control}_point_con",
                )
                cmds.orientConstraint(
                    result.control,
                    motion_joint,
                    maintainOffset=True,
                    name=f"{result.control}_orient_con",
                )
            else:
                connect_attribute(
                    f"{result.control}.translate", f"{motion_joint}.translate"
                )
                connect_attribute(
                    f"{result.control}.rotate", f"{motion_joint}.rotate"
                )

            # Register control with controls layer
            self._register_control(result.control)

        # Parent controls their hierarchy.
        self._parent_skeleton_controls()

    def _parent_skeleton_controls(self) -> None:
        """Parent skeleton controls according to joint hierarchy."""

        skeleton_data = get_skeleton_joints_with_radius()

        for joint_name, _ in skeleton_data:
            motion_joint = f"{joint_name}{self._skel_type}"
            ctrl_name = joint_name

            # Handle pelvis -> hips rename.
            if "pelvis" in ctrl_name:
                ctrl_name = ctrl_name.replace("pelvis", "hips")

            # Offset name should use the renamed ctrl_name.
            offset_name = f"{ctrl_name}_offset"

            if not object_exists(offset_name):
                continue

            # Get parent
            parent_joint = get_parent(motion_joint)
            if parent_joint:
                # Remove the skeleton type suffix and add _ctrl suffix.
                if self._skel_type and parent_joint.endswith(self._skel_type):
                    parent_base = parent_joint[: -len(self._skel_type)]
                else:
                    parent_base = parent_joint
                parent_ctrl = f"{parent_base}_ctrl"

                if "pelvis" in parent_ctrl:
                    parent_ctrl = parent_ctrl.replace("pelvis", "hips")

                if object_exists(parent_ctrl):
                    cmds.parent(offset_name, parent_ctrl)
                else:
                    # Handle special cases.
                    self._handle_special_parenting(ctrl_name, offset_name)

            # Apply control styling.
            self._style_skeleton_control(f"{ctrl_name}_ctrl", joint_name)

    def _handle_special_parenting(
        self, ctrl_name: str, offset_name: str
    ) -> None:
        """Handle special control parenting cases.

        Args:
            ctrl_name: Name of control.
            offset_name: Name of control offset.
        """

        # Determine side from control name.
        is_right = "_r_" in ctrl_name or ctrl_name.endswith("_r")
        is_left = "_l_" in ctrl_name or ctrl_name.endswith("_l")
        side_suffix = "r" if is_right else "l" if is_left else ""

        if not side_suffix:
            return

        # Handle metacarpal and thumb_01 - parent constrain to hand.
        if "metacarpal" in ctrl_name or "thumb_01_" in ctrl_name:
            cmds.parentConstraint(
                f"hand_{side_suffix}{self._skel_type}",
                offset_name,
                maintainOffset=True,
            )

        # Handle finger base joints (index_01, middle_01, ring_01, pinky_01).
        # These should be parented to their metacarpal control.
        elif any(
            finger in ctrl_name
            for finger in ["index_01_", "middle_01_", "ring_01_", "pinky_01_"]
        ):
            # Extract finger name (index, middle, ring, pinky).
            finger_name = ctrl_name.split("_01_")[0]
            metacarpal_ctrl = f"{finger_name}_metacarpal_{side_suffix}_ctrl"
            if object_exists(metacarpal_ctrl):
                cmds.parent(offset_name, metacarpal_ctrl)
            else:
                # Fallback to parent constraint to metacarpal joint.
                metacarpal_joint = (
                    f"{finger_name}_metacarpal_{side_suffix}{self._skel_type}"
                )
                if object_exists(metacarpal_joint):
                    cmds.parentConstraint(
                        metacarpal_joint,
                        offset_name,
                        maintainOffset=True,
                    )

        # Handle toe joints - parent constrain to ball.
        elif "toe" in ctrl_name:
            cmds.parentConstraint(
                f"ball_{side_suffix}{self._skel_type}",
                offset_name,
                maintainOffset=True,
            )

    def _style_skeleton_control(self, ctrl_name: str, joint_name: str) -> None:
        """Apply styling to skeleton control."""
        if not object_exists(ctrl_name):
            return

        shape = f"{ctrl_name}Shape"
        if not object_exists(shape):
            return

        # Determine color
        if "_r_" in ctrl_name or ctrl_name.endswith("_r"):
            color = RigColors.RIGHT
        elif "_l_" in ctrl_name or ctrl_name.endswith("_l"):
            color = RigColors.LEFT
        else:
            color = RigColors.CENTER

        set_color_override(shape, color)

        # Apply polygon shape for specific controls
        if any(part in ctrl_name for part in ["head", "spine", "clavicle"]):
            from .utils.maya_utils import find_make_node

            make_node = find_make_node(ctrl_name, "makeNurbCircle")
            if make_node:
                cmds.setAttr(f"{make_node}.degree", 1)
                cmds.setAttr(f"{make_node}.sections", 6)

    def _create_additional_controls(self) -> None:
        """Create additional rig controls (global, body, etc.)."""

        # Global control.
        self._control_builder.create_global_control()
        self._register_control("global_ctrl")

        # Body offset control.
        self._control_builder.create_body_offset_control()
        self._register_control("body_offset_ctrl")

        # Body control.
        self._control_builder.create_body_control()
        self._register_control("body_ctrl")

        # Parent hierarchy.
        cmds.parent("body_offset_offset", "global_ctrl")
        cmds.parent("root_offset", "body_offset_ctrl")
        cmds.parent("body_offset", "root_ctrl")
        cmds.parent("hips_offset", "body_ctrl")
        cmds.parent("spine_01_offset", "body_ctrl")

    def _create_fkik_limb_controls(self) -> None:
        """Create FK and IK controls for limbs."""

        for side in [Side.LEFT, Side.RIGHT]:
            # Create FK limb controls.
            self._create_fk_limb_controls_for_side(side)

            # Create IK limb controls.
            self._create_ik_limb_controls_for_side(side)

            # Create pole vectors.
            self._create_pole_vectors_for_side(side)

            # Create FK/IK switches.
            self._create_fkik_switches_for_side(side)

    def _create_fk_limb_controls_for_side(self, side: Side) -> None:
        """Create FK controls for a side.

        Args:
            side: Side to create controls for.
        """

        s = side.value
        arm_parts = ["upperarm", "lowerarm", "hand"]
        leg_parts = ["thigh", "calf", "foot", "ball"]

        # Arm FK controls.
        for idx, part in enumerate(arm_parts):
            is_thigh = False
            parent = None

            if part == "upperarm":
                parent = f"clavicle_{s}_ctrl"
            elif idx > 0:
                parent = f"{arm_parts[idx - 1]}_{s}_fk_ctrl"

            self._create_fk_control(part, side, parent, is_thigh)

        # Leg FK controls.
        for idx, part in enumerate(leg_parts):
            is_thigh = part == "thigh"
            parent = None

            if part == "thigh":
                parent = "hips_ctrl"
            elif idx > 0:
                parent = f"{leg_parts[idx - 1]}_{s}_fk_ctrl"

            self._create_fk_control(part, side, parent, is_thigh)

    def _create_fk_control(
        self, part: str, side: Side, parent: str | None, is_thigh: bool
    ) -> None:
        """Create a single FK control.

        Args:
            part: Name of part to create control for.
            side: Side to create control for.
            parent: Parent control to connect to.
            is_thigh: Whether the part is a thigh.
        """

        s = side.value
        match_to = f"{part}_{s}_fk{self._skel_type}"

        result = self._control_builder.create_fk_limb_control(
            name=part,
            side=side,
            match_to=match_to,
            parent=parent,
            is_thigh=is_thigh,
        )

        # Connect to FK joint
        cmds.orientConstraint(
            result.control,
            f"{part}_{s}_fk{self._skel_type}",
            maintainOffset=False,
            name=f"{result.control}_parentCon",
        )

        # Register control with controls layer
        self._register_control(result.control)

        # Register FK control with FK/IK layer
        self._register_fk_control(result.control)

    def _create_ik_limb_controls_for_side(self, side: Side) -> None:
        """Create IK controls for a side."""
        s = side.value

        # Hand IK.
        hand_match = f"hand_{s}_ik{self._skel_type}"
        hand_result = self._control_builder.create_ik_limb_control(
            name="hand", side=side, match_to=hand_match
        )

        # Connect IK control to IK handle only.
        # The IK solver handles joint orientation - no orient constraint needed.
        cmds.parentConstraint(
            hand_result.control,
            f"hand_{s}_ikHandle",
            maintainOffset=True,
            name=f"hand_{s}_ik_ctrl_parentCon",
        )

        # Foot IK.
        foot_match = f"foot_{s}_ik{self._skel_type}"
        foot_result = self._control_builder.create_ik_limb_control(
            name="foot", side=side, match_to=foot_match
        )

        # Register IK controls
        self._register_control(hand_result.control)
        self._register_control(foot_result.control)

        # Register IK controls with FK/IK layer
        self._register_ik_control(hand_result.control)
        self._register_ik_control(foot_result.control)

        # Parent IK controls to root.
        cmds.parentConstraint(
            "root_ctrl", f"hand_{s}_ik_offset", maintainOffset=True
        )
        cmds.parentConstraint(
            "root_ctrl", f"foot_{s}_ik_offset", maintainOffset=True
        )

    def _create_pole_vectors_for_side(self, side: Side) -> None:
        """Create pole vector controls for a side.

        Args:
            side: Side to create pole vectors for.
        """

        s = side.value

        # Arm pole vector
        arm_pv_loc = create_pole_vector_locator(
            f"upperarm_{s}_ik{self._skel_type}",
            f"lowerarm_{s}_ik{self._skel_type}",
            f"hand_{s}_ik{self._skel_type}",
            flip=False,
        )

        arm_pv_pos: tuple[float, float, float] = cmds.xform(
            arm_pv_loc, query=True, worldSpace=True, translation=True
        )
        cmds.delete(arm_pv_loc)

        arm_result = self._control_builder.create_pole_vector_control(
            limb_type="arm",
            side=side,
            position=tuple(arm_pv_pos),
        )

        cmds.poleVectorConstraint(arm_result.control, f"hand_{s}_ikHandle")

        # Create an arm pole vector match.
        self._control_builder.create_pole_vector_match(
            "arm", side, arm_result.control
        )
        cmds.parentConstraint(
            f"lowerarm_{s}_fk{self._skel_type}",
            f"arm_pole_vector_{s}_match_offset",
            maintainOffset=True,
        )

        # Leg pole vector
        leg_pv_loc = create_pole_vector_locator(
            f"thigh_{s}_ik{self._skel_type}",
            f"calf_{s}_ik{self._skel_type}",
            f"foot_{s}_ik{self._skel_type}",
        )

        leg_pv_pos: tuple[float, float, float] = cmds.xform(
            leg_pv_loc, query=True, worldSpace=True, translation=True
        )
        cmds.delete(leg_pv_loc)

        leg_result = self._control_builder.create_pole_vector_control(
            limb_type="leg",
            side=side,
            position=tuple(leg_pv_pos),
        )

        cmds.poleVectorConstraint(
            leg_result.control,
            f"foot_{s}_ikHandle",
            name=f"foot_{s}_poleVector_con",
        )

        # Create the leg pole vector match.
        self._control_builder.create_pole_vector_match(
            "leg", side, leg_result.control
        )
        cmds.parentConstraint(
            f"calf_{s}_fk{self._skel_type}",
            f"leg_pole_vector_{s}_match_offset",
            maintainOffset=True,
        )

        # Parent pole vectors to root
        cmds.parentConstraint(
            "root_ctrl", f"arm_pole_vector_{s}_offset", maintainOffset=True
        )
        cmds.parentConstraint(
            "root_ctrl", f"leg_pole_vector_{s}_offset", maintainOffset=True
        )

        # Register pole vector controls
        self._register_control(arm_result.control)
        self._register_control(leg_result.control)

        # Register pole vectors with FK/IK layer
        self._register_pole_vector(arm_result.control)
        self._register_pole_vector(leg_result.control)

    def _create_fkik_switches_for_side(self, side: Side) -> None:
        """Create FK/IK switches for a side.

        Args:
            side: Side to create switches for.
        """

        # Create switch controls.
        self._fkik_switch_builder.create_arm_switch(side, self._skel_type)
        self._fkik_switch_builder.create_leg_switch(side, self._skel_type)

        # Connect FK/IK blends.
        self._fkik_switch_builder.connect_all_fkik_blends(
            side, self._skel_type
        )

        # Connect pole vector visibility.
        self._fkik_switch_builder.connect_pole_vector_visibility(side)

        # Set default states.
        self._fkik_switch_builder.set_default_fkik_states(side)

    def _create_reverse_foot_systems(self) -> None:
        """Create reverse foot setups for both sides."""

        for side in [Side.LEFT, Side.RIGHT]:
            # Build reverse foot.
            self._reverse_foot_builder.build_reverse_foot(
                side, self._skel_type
            )

            # Create toe twist control.
            self._reverse_foot_builder.create_toe_twist_control(side)

            # Create ball lift control.
            self._reverse_foot_builder.create_ball_lift_control(
                side, self._skel_type
            )

            # Connect toe twist visibility to FK/IK switch.
            s = side.value
            if object_exists(f"leg_pole_vector_{s}_ctrl"):
                connect_attribute(
                    f"foot_fkik_{s}_switch.limb_fkik_switch",
                    f"toe_twist_{s}_ik_offset.visibility",
                )

    def _create_finger_controls(self) -> None:
        """Create finger controls for both hands."""

        for side in [Side.LEFT, Side.RIGHT]:
            self._finger_builder.build_finger_controls(side, self._skel_type)

    def _create_space_switches(self) -> None:
        """Create space switch systems."""

        for side in [Side.LEFT, Side.RIGHT]:
            # Hand space switch.
            self._space_switch_builder.create_hand_space_switch(side)

            # Pole vector space switches.
            self._space_switch_builder.create_pole_vector_space_switch(
                side, "arm", f"hand_{side.value}_ik_ctrl"
            )
            self._space_switch_builder.create_pole_vector_space_switch(
                side, "leg", f"foot_{side.value}_ik_ctrl"
            )

    def _finalize_rig(self, up_axis: str = "y") -> None:
        """Finalize rig setup - visibility, etc."""

        # Import face GUI labels if applicable.
        if self._motion and object_exists("headGui_grp"):
            self._import_face_gui_labels()

        # Make custom attributes keyable.
        self._make_custom_attrs_keyable()

    def _import_face_gui_labels(self) -> None:
        """Import face GUI custom labels if available."""

        script_path = os.path.dirname(__file__)
        face_gui_file = os.path.join(script_path, "face_gui_custom_labels.ma")

        if not object_exists("facial_gui_custom_labels_offset"):
            if os.path.exists(face_gui_file):
                try:
                    cmds.file(face_gui_file, i=True)
                except Exception as e:
                    logger.warning(f"Could not import face GUI labels: {e}")

        if object_exists("facial_gui_custom_labels_offset") and object_exists(
            "FRM_faceGUI"
        ):
            cmds.parent(
                "facial_gui_custom_labels_offset", self.RIG_SETUP_GROUP
            )
            cmds.parentConstraint(
                "FRM_faceGUI",
                "facial_gui_custom_labels_offset",
                maintainOffset=False,
                name="facial_gui_custom_labels_parentCon",
            )
            cmds.setAttr("facial_gui_custom_labels.translateY", -3)

    def _make_custom_attrs_keyable(self) -> None:
        """Make custom attributes keyable."""

        for side in [Side.LEFT, Side.RIGHT]:
            s = side.value

            # FK/IK switch attributes.
            for attr_path in [
                f"hand_fkik_{s}_switch.limb_fk_ik",
                f"foot_fkik_{s}_switch.limb_fk_ik",
                f"foot_{s}_ik_ctrl.Roll",
                f"foot_{s}_ik_ctrl.Bend_Limit_Angle",
                f"foot_{s}_ik_ctrl.Toe_Straight",
            ]:
                if object_exists(attr_path.split(".")[0]):
                    try:
                        cmds.setAttr(attr_path, keyable=True)
                    except RuntimeError:
                        pass

            # Finger attributes (motion mode only).
            if self._motion:
                for finger in [
                    "thumb_curl",
                    "index_curl",
                    "middle_curl",
                    "ring_curl",
                    "pinky_curl",
                    "spread_fingers",
                ]:
                    attr_path = f"fingers_{s}_ctrl.{finger}"
                    if object_exists(f"fingers_{s}_ctrl"):
                        try:
                            cmds.setAttr(attr_path, keyable=True)
                        except RuntimeError:
                            pass

    @staticmethod
    def _tag_metahuman() -> None:
        """Tag MetaHuman objects for identification."""

        # Tag body
        body_roots = cmds.ls("*DHIbody:root")
        for body_root in body_roots:
            add_string_attribute(body_root, "ue_tag", "metahuman_body")
            add_string_attribute(body_root, "variant_override", "")

        # Tag face
        face_controls = cmds.ls("*FacialControls")
        for face_ctrl in face_controls:
            add_string_attribute(face_ctrl, "ue_tag", "metahuman_face")

        logger.info("MetaHuman objects tagged successfully.")


def build_metahuman_body_rig(
    motion: bool = True, show_dialogs: bool = True
) -> RigBuildResult:
    """Build MetaHuman body rig controls.

    This is the main entry point for building the rig.

    Args:
        motion: If True, create a motion skeleton for animation.
        show_dialogs: If True, show confirmation dialogs during the build.
                     If False, skip dialogs and proceed with default actions.

    Returns:
        `RigBuildResult` with build status.
    """

    builder = MetaHumanBodyRigBuilder(motion=motion, show_dialogs=show_dialogs)
    return builder.build()
