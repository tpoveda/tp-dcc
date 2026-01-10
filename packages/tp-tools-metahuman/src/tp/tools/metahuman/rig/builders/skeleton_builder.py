"""Skeleton builder for MetaHuman rig.

This module provides classes for building and managing skeleton structures
including motion skeletons, FK/IK chains, and constraint systems.
Uses tp.libs.maya.wrapper for OpenMaya operations.
"""

from __future__ import annotations

import maya.cmds as cmds
from loguru import logger

from ..data.skeleton_config import (
    ARM_LIMB,
    FULL_METAHUMAN_SKELETON,
    LEG_LIMB,
    LimbConfig,
    RigType,
    Side,
)
from ..utils.attribute_utils import connect_attribute
from ..utils.maya_utils import get_parent, object_exists, select_hierarchy


class SkeletonBuilder:
    """Builder class for creating and managing skeleton structures.

    This class handles the creation of motion skeletons, FK/IK joint chains,
    and their connections to the driver skeleton.
    """

    def __init__(self, root_suffix: str = "_drv"):
        """Initialize the skeleton builder.

        Args:
            root_suffix: Suffix used for driver joints (e.g., "_drv").
        """
        self.root_suffix = root_suffix
        self.motion_suffix = "_motion"
        self.rig_setup_group = "rig_setup"

    @property
    def root_joint(self) -> str | None:
        """Get the root joint name."""

        if object_exists("root_drv"):
            return "root_drv"
        elif object_exists("root"):
            return "root"

        return None

    @property
    def is_driver_skeleton(self) -> bool:
        """Check if using driver skeleton with _drv suffix."""

        return self.root_suffix == "_drv"

    @staticmethod
    def detect_skeleton_type() -> tuple[str | None, str]:
        """Detect the skeleton type and return root joint and suffix.

        Returns:
            Tuple of (root_joint_name, suffix).
        """

        if object_exists("root_drv"):
            return "root_drv", "_drv"
        elif object_exists("root"):
            return "root", ""

        return None, ""

    def create_motion_skeleton(self) -> str | None:
        """Create a motion skeleton by duplicating the driver skeleton.

        The motion skeleton is used to receive animation data and drive
        the driver skeleton through constraints.

        Returns:
            Name of the root motion joint, or `None` if failed.
        """

        root_joint = self.root_joint
        if not root_joint:
            logger.error("No valid skeleton found.")
            return None

        # Select hierarchy.
        source_joints = select_hierarchy(root_joint)

        # Duplicate skeleton.
        cmds.duplicate(root_joint, name="root_motion", renameChildren=True)

        # Rename motion joints.
        motion_joints = select_hierarchy("root_motion")

        for idx, obj in enumerate(motion_joints):
            if obj == "root_motion":
                continue

            src_obj = source_joints[idx] if idx < len(source_joints) else None
            if not src_obj:
                continue

            if self.is_driver_skeleton:
                # Replace the last suffix with _motion.
                new_name = obj.rsplit("_", 1)[0] + self.motion_suffix
            else:
                new_name = src_obj + self.motion_suffix

            if obj != new_name and object_exists(obj):
                try:
                    cmds.rename(obj, new_name)
                except RuntimeError:
                    pass

        # Clean up non-skeleton joints.
        self._cleanup_motion_skeleton()

        # Connect motion skeleton to driver skeleton.
        self._connect_motion_to_driver()

        return "root_motion"

    def _cleanup_motion_skeleton(self) -> None:
        """Remove helper bones from the motion skeleton."""

        if not object_exists("root_motion"):
            return

        motion_joints = select_hierarchy("root_motion")

        for obj in motion_joints:
            # Check if this joint is part of the valid skeleton.
            base_name = obj.replace(self.motion_suffix, "")
            if base_name not in FULL_METAHUMAN_SKELETON:
                if object_exists(obj):
                    try:
                        cmds.delete(obj)
                    except RuntimeError:
                        pass

    def _connect_motion_to_driver(self) -> None:
        """Connect motion skeleton transforms to driver skeleton."""

        if not object_exists("root_motion"):
            return

        motion_joints = select_hierarchy("root_motion")

        for motion_joint in motion_joints:
            driver_joint = motion_joint.replace(
                self.motion_suffix, self.root_suffix
            )
            if object_exists(driver_joint):
                connect_attribute(
                    f"{motion_joint}.translate",
                    f"{driver_joint}.translate",
                    force=True,
                )
                connect_attribute(
                    f"{motion_joint}.rotate",
                    f"{driver_joint}.rotate",
                    force=True,
                )

    def create_ikfk_limb_chains(
        self, side: Side, limb_config: LimbConfig, skel_type: str = "_motion"
    ) -> dict[RigType, list[str]]:
        """Create IK and FK joint chains for a limb.

        Args:
            side: Body side.
            limb_config: Configuration for the limb.
            skel_type: Skeleton type suffix.

        Returns:
            Dictionary mapping `RigType` to a list of joint names.
        """
        chains: dict[RigType, list[str]] = {RigType.FK: [], RigType.IK: []}

        for rig_type in [RigType.FK, RigType.IK]:
            for idx, part in enumerate(limb_config.parts):
                source_joint = f"{part}_{side.value}{skel_type}"
                new_joint = f"{part}_{side.value}_{rig_type.value}{skel_type}"

                if not object_exists(source_joint):
                    logger.warning(f"Source joint not found: {source_joint}")
                    continue

                # Duplicate joint.
                cmds.duplicate(source_joint, name=new_joint, parentOnly=True)

                # Parent to the previous joint in the chain or to rig_setup.
                if idx > 0 and part != "thigh":  # thigh starts a new chain.
                    prev_part = limb_config.parts[idx - 1]
                    parent_joint = (
                        f"{prev_part}_{side.value}_{rig_type.value}{skel_type}"
                    )

                    current_parent = get_parent(new_joint)
                    if current_parent != parent_joint and object_exists(
                        parent_joint
                    ):
                        cmds.parent(new_joint, parent_joint)
                else:
                    # Parent limb root to its anatomical parent.
                    if part == "upperarm":
                        parent_joint = f"clavicle_{side.value}{skel_type}"
                    elif part == "thigh":
                        parent_joint = f"pelvis{skel_type}"
                    else:
                        parent_joint = self.rig_setup_group

                    if object_exists(parent_joint):
                        cmds.parent(new_joint, parent_joint)

                chains[rig_type].append(new_joint)

        return chains

    def set_ik_preferred_angles(
        self, side: Side, limb_config: LimbConfig, skel_type: str = "_motion"
    ) -> None:
        """Set preferred angles for IK mid-joints based on their current rotation.

        This ensures the IK solver bends the joint in the correct direction.

        Args:
            side: Body side.
            limb_config: Configuration for the limb.
            skel_type: Skeleton type suffix.
        """
        # The mid-joint is typically the second joint in the chain (index 1).
        if len(limb_config.parts) < 2:
            return

        mid_part = limb_config.parts[1]  # lowerarm or calf
        ik_mid_joint = f"{mid_part}_{side.value}_ik{skel_type}"

        if not object_exists(ik_mid_joint):
            return

        # Get current rotation and set as preferred angle.
        rot_x = cmds.getAttr(f"{ik_mid_joint}.rotateX")
        rot_y = cmds.getAttr(f"{ik_mid_joint}.rotateY")
        rot_z = cmds.getAttr(f"{ik_mid_joint}.rotateZ")

        cmds.setAttr(f"{ik_mid_joint}.preferredAngleX", rot_x)
        cmds.setAttr(f"{ik_mid_joint}.preferredAngleY", rot_y)
        cmds.setAttr(f"{ik_mid_joint}.preferredAngleZ", rot_z)

    def create_ikfk_constraints(
        self, side: Side, limb_config: LimbConfig, skel_type: str = "_motion"
    ) -> list[str]:
        """Create FK/IK blend constraints for a limb.

        Args:
            side: Body side.
            limb_config: Configuration for the limb.
            skel_type: Skeleton type suffix.

        Returns:
            List of created constraint names.
        """

        constraints = []

        for part in limb_config.parts:
            base_joint = f"{part}_{side.value}{skel_type}"
            ik_joint = f"{part}_{side.value}_{RigType.IK.value}{skel_type}"
            fk_joint = f"{part}_{side.value}_{RigType.FK.value}{skel_type}"

            if not all(
                object_exists(j) for j in [base_joint, ik_joint, fk_joint]
            ):
                continue

            constraint_name = f"{part}_{side.value}_ikfk{skel_type}_orient_con"

            # Create orient constraint (maintainOffset=False like original).
            cmds.orientConstraint(
                ik_joint,
                fk_joint,
                base_joint,
                name=constraint_name,
                maintainOffset=False,
            )

            # Set default weights (FK active).
            cmds.setAttr(f"{constraint_name}.{ik_joint}W0", 0)
            cmds.setAttr(f"{constraint_name}.{fk_joint}W1", 1)

            constraints.append(constraint_name)

        return constraints

    def create_ik_handle(
        self,
        start_joint: str,
        end_joint: str,
        name: str,
        parent: str | None = None,
    ) -> str:
        """Create an IK handle.

        Args:
            start_joint: Start joint of the IK chain.
            end_joint: End joint of the IK chain.
            name: Name for the IK handle.
            parent: Optional parent for the IK handle.

        Returns:
            Name of the created IK handle.
        """

        handle = cmds.ikHandle(
            startJoint=start_joint,
            endEffector=end_joint,
            sticky="sticky",
            name=name,
        )[0]

        if parent and object_exists(parent):
            cmds.parent(handle, parent)

        return handle

    def create_arm_ik_handle(
        self,
        side: Side,
        skel_type: str = "_motion",
        parent: str | None = None,
    ) -> str:
        """Create an IK handle for the arm.

        Args:
            side: Body side.
            skel_type: Skeleton type suffix.
            parent: Optional parent.

        Returns:
            Name of the IK handle.
        """

        return self.create_ik_handle(
            start_joint=f"upperarm_{side.value}_ik{skel_type}",
            end_joint=f"hand_{side.value}_ik{skel_type}",
            name=f"hand_{side.value}_ikHandle",
            parent=parent,
        )

    def create_leg_ik_handle(
        self,
        side: Side,
        skel_type: str = "_motion",
        parent: str | None = None,
    ) -> str:
        """Create an IK handle for the leg.

        Args:
            side: Body side.
            skel_type: Skeleton type suffix.
            parent: Optional parent.

        Returns:
            Name of the IK handle.
        """

        return self.create_ik_handle(
            start_joint=f"thigh_{side.value}_ik{skel_type}",
            end_joint=f"foot_{side.value}_ik{skel_type}",
            name=f"foot_{side.value}_ikHandle",
            parent=parent,
        )

    def setup_all_limbs(self, skel_type: str = "_motion") -> dict[str, dict]:
        """Set up IK/FK for all limbs.

        Args:
            skel_type: Skeleton type suffix.

        Returns:
            Dictionary with limb setup information.
        """

        result: dict[str, dict] = {}

        for side in [Side.LEFT, Side.RIGHT]:
            s = side.value

            # Arms
            arm_chains = self.create_ikfk_limb_chains(
                side, ARM_LIMB, skel_type
            )
            # # Set preferred angles for IK mid-joints before creating IK handles.
            # self.set_ik_preferred_angles(side, ARM_LIMB, skel_type)

            arm_constraints = self.create_ikfk_constraints(
                side, ARM_LIMB, skel_type
            )
            arm_ik = self.create_arm_ik_handle(
                side, skel_type, self.rig_setup_group
            )

            result[f"arm_{side.value}"] = {
                "chains": arm_chains,
                "constraints": arm_constraints,
                "ik_handle": arm_ik,
            }

            # Legs
            leg_chains = self.create_ikfk_limb_chains(
                side, LEG_LIMB, skel_type
            )
            # Set preferred angles for IK mid-joints before creating IK handles.
            # self.set_ik_preferred_angles(side, LEG_LIMB, skel_type)

            leg_constraints = self.create_ikfk_constraints(
                side, LEG_LIMB, skel_type
            )
            leg_ik = self.create_leg_ik_handle(
                side, skel_type, self.rig_setup_group
            )

            result[f"leg_{side.value}"] = {
                "chains": leg_chains,
                "constraints": leg_constraints,
                "ik_handle": leg_ik,
            }

        return result
