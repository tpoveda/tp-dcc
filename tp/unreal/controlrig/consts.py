from __future__ import annotations

import unreal

IDENTITY_MATRIX = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]

CPP_TYPE_TO_OBJECT_PATH = {
    "FVector": "/Script/CoreUObject.Vector",
    "FQuat": "/Script/CoreUObject.Quat",
    "FTransform": "/Script/CoreUObject.Transform",
    "FControlRigSpline": "/Script/ControlRigSpline.ControlRigSpline",
    "FRigElementKey": "/Script/ControlRig.RigElementKey",
    "FConstraintParent": "/Script/ControlRig.ConstraintParent",
}

CONTROL_TYPES = {
    "transform": unreal.RigControlType.EULER_TRANSFORM,
    "rotation": unreal.RigControlType.ROTATOR,
    "translation": unreal.RigControlType.POSITION,
    "scale": unreal.RigControlType.SCALE,
}

# noinspection PyTypeChecker
CONTROL_DEFAULTS = {
    "transform": unreal.RigHierarchy.make_control_value_from_euler_transform(
        unreal.EulerTransform(
            location=[0.0, 0.0, 0.0], rotation=[0.0, 0.0, 0.0], scale=[1.0, 1.0, 1.0]
        )
    ),
    "translation": unreal.RigHierarchy.make_control_value_from_vector(
        unreal.Vector(0.000000, 0.000000, 0.000000)
    ),
    "rotation": unreal.RigHierarchy.make_control_value_from_rotator(
        unreal.Rotator(pitch=0.000000, roll=-0.000000, yaw=0.000000)
    ),
    "scale": unreal.RigHierarchy.make_control_value_from_vector(
        unreal.Vector(1.000000, 1.000000, 1.000000)
    ),
}

SIDE_COLORS = {
    "m": [1, 1, 0],
    "l": [0, 0, 1],
    "r": [1, 0, 0],
}


ELEMENT_TYPES = {
    "Control": unreal.RigElementType.CONTROL,
    "Bone": unreal.RigElementType.BONE,
    "Null": unreal.RigElementType.NULL,
}

ELEMENT_TYPE_STRINGS = {
    unreal.RigElementType.CONTROL: "Control",
    unreal.RigElementType.BONE: "Bone",
    unreal.RigElementType.NULL: "Null",
}

FILTERED_CHANNELS = {
    "TRANSLATION_X": unreal.RigControlTransformChannel.TRANSLATION_X,
    "TRANSLATION_Y": unreal.RigControlTransformChannel.TRANSLATION_Y,
    "TRANSLATION_Z": unreal.RigControlTransformChannel.TRANSLATION_Z,
    "PITCH": unreal.RigControlTransformChannel.PITCH,
    "ROLL": unreal.RigControlTransformChannel.ROLL,
    "YAW": unreal.RigControlTransformChannel.YAW,
    "SCALE_X": unreal.RigControlTransformChannel.SCALE_X,
    "SCALE_Y": unreal.RigControlTransformChannel.SCALE_Y,
    "SCALE_Z": unreal.RigControlTransformChannel.SCALE_Z,
}

TOP_NODE_DEFAULTS = [0, -3000, 0]
COMMENT_BOX_BORDER_SIZE = 50
NEXT_COLUMN_GAP_FACTOR = 1.0
BLOCK_BRANCH_TRUE = True
BLOCK_BRANCH_FALSE = True
BLOCK_FOREACH = True
