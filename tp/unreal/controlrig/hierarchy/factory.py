from __future__ import annotations

import typing
from typing import Sequence

import unreal

from .. import consts, helpers

if typing.TYPE_CHECKING:
    from ..controllers import ControlRig


def create_float_control(
    control_rig: ControlRig,
    name: str,
    parent: unreal.RigElementKey | None = None,
    float_range: list[float] | None = None,
    default: float = 0.0,
    is_bool: bool = False,
) -> unreal.RigElementKey:
    """
    Creates a float control.

    :param control_rig: control rig object that will contain the new control.
    :param name: name of the control.
    :param parent: parent of the control.
    :param float_range: range of the float control.
    :param default: default value of the float control.
    :param is_bool: whether the control is a boolean or not.
    :return: created control element key.
    """

    float_range = float_range or [-100, 100]

    control_settings = unreal.RigControlSettings(group_with_parent_control=True)
    control_settings.animation_type = unreal.RigControlAnimationType.ANIMATION_CHANNEL
    control_settings.control_type = (
        unreal.RigControlType.BOOL if is_bool else unreal.RigControlType.FLOAT
    )
    control_settings.display_name = name
    control_settings.draw_limits = True
    control_settings.shape_color = unreal.LinearColor(1.0, 0.0, 0.0, 1.0)
    control_settings.shape_name = "Default"
    control_settings.shape_visible = True
    control_settings.is_transient_control = False
    control_settings.limit_enabled = [unreal.RigControlLimitEnabled(True, True)]
    control_settings.primary_axis = unreal.RigControlAxis.X
    control_settings.minimum_value = unreal.RigHierarchy.make_control_value_from_float(
        float_range[0]
    )
    control_settings.maximum_value = unreal.RigHierarchy.make_control_value_from_float(
        float_range[1]
    )
    parent_key = parent or ""
    # noinspection PyTypeChecker
    control_key = control_rig.hierarchy.add_control(
        name,
        parent_key,
        control_settings,
        unreal.RigHierarchy.make_control_value_from_euler_transform(
            unreal.EulerTransform(
                location=[0.0, 0.0, 0.0],
                rotation=[0.0, 0.0, 0.0],
                scale=[1.0, 1.0, 1.0],
            )
        ),
        setup_undo=False,
    )
    # noinspection PyTypeChecker
    control_rig.blueprint.hierarchy.set_local_transform(
        control_key,
        unreal.Transform(
            location=[float(default), 0.0, 0.0],
            rotation=[0.0, 0.0, 0.0],
            scale=[1.0, 1.0, 1.0],
        ),
        True,
        True,
        setup_undo=False,
    )

    return control_key


def create_bool_control(
    control_rig: ControlRig,
    name: str,
    parent: unreal.RigElementKey | None = None,
    default: bool = False,
) -> unreal.RigElementKey:
    """
    Creates a boolean control.

    :param control_rig: control rig object that will contain the new control.
    :param name: name of the control.
    :param parent: parent of the control.
    :param default: default value of the float control.
    :return: created control element key.
    """

    control_settings = unreal.RigControlSettings(group_with_parent_control=True)
    control_settings.animation_type = unreal.RigControlAnimationType.ANIMATION_CHANNEL
    control_settings.control_type = unreal.RigControlType.BOOL
    control_settings.display_name = name
    control_settings.draw_limits = True
    control_settings.shape_color = unreal.LinearColor(1.0, 0.0, 0.0, 1.0)
    control_settings.shape_name = "Default"
    control_settings.shape_visible = True
    control_settings.is_transient_control = False
    control_settings.limit_enabled = [unreal.RigControlLimitEnabled(True, True)]
    control_settings.primary_axis = unreal.RigControlAxis.X
    parent_key = parent or ""
    # noinspection PyTypeChecker
    control_key = control_rig.hierarchy.add_control(
        name,
        parent_key,
        control_settings,
        unreal.RigHierarchy.make_control_value_from_euler_transform(
            unreal.EulerTransform(
                location=[0.0, 0.0, 0.0],
                rotation=[0.0, 0.0, 0.0],
                scale=[1.0, 1.0, 1.0],
            )
        ),
        setup_undo=False,
    )
    # noinspection PyTypeChecker
    control_rig.blueprint.hierarchy.set_local_transform(
        control_key,
        unreal.Transform(
            location=[1.0 if default else 0.0, 0.0, 0.0],
            rotation=[0.0, 0.0, 0.0],
            scale=[1.0, 1.0, 1.0],
        ),
        True,
        True,
        setup_undo=False,
    )

    return control_key


def create_null(
    control_rig: ControlRig,
    name: str,
    match: unreal.RigElementKey | None = None,
    matrix: list[list[float]] | None = None,
    slider_scale: list[int | float] | None = None,
    parent: unreal.RigElementKey | None = None,
    transform_in_global: bool = True,
):
    matrix = matrix or consts.IDENTITY_MATRIX.copy()
    slider_scale = slider_scale or [1, 1, 1]

    translation, rotation, scale = helpers.trs_from_list_matrix(matrix)
    scale.x *= slider_scale[0]
    scale.y *= slider_scale[1]
    scale.z *= slider_scale[2]

    # noinspection PyTypeChecker
    new_null = control_rig.hierarchy.add_null(
        name,
        match if match else "",
        unreal.Transform(location=translation, rotation=rotation, scale=scale),
        transform_in_global=transform_in_global,
        setup_undo=False,
    )

    if parent:
        control_rig.hierarchy.set_parent(
            new_null, parent, maintain_global_transform=True, setup_undo=False
        )
    elif match:
        control_rig.hierarchy.remove_all_parents(
            match, maintain_global_transform=True, setup_undo=False
        )

    return new_null


def create_control(
    control_rig: ControlRig,
    name: str,
    parent: unreal.RigElementKey,
    shape: str = "Default",
    shape_matrix: list[list[float, float, float, float]] | None = None,
    shape_force_rotation: list[float, float, float] | None = None,
    side: str = "l",
    no_select: bool = False,
    proxy: bool = False,
    overwrite_color: Sequence[float, float, float] | None = None,
    min_translation: list[float, float, float] | None = None,
    max_translation: list[float, float, float] | None = None,
    min_rotation: list[float, float, float] | None = None,
    max_rotation: list[float, float, float] | None = None,
    draw_limits: bool = False,
    add_spaces: list[unreal.RigElementKey] | None = None,
    control_type: str = "transform",
    filtered_channels: list[unreal.RigControlTransformChannel] | None = None,
    driven_controls: list[unreal.RigElementKey] | None = None,
) -> unreal.RigElementKey:
    """
    Creates a new control node within the control rig hierarchy.

    :param control_rig: control rig to create the control in.
    :param name: name of the control.
    :param parent: parent of the control.
    :param shape: shape of the control.
    :param shape_matrix: matrix of the shape.
    :param shape_force_rotation: force rotation of the shape.
    :param side: side of the control.
    :param no_select: whether the control is selectable.
    :param proxy: whether the control is a proxy.
    :param overwrite_color: color of the control.
    :param min_translation: minimum translation values.
    :param max_translation: maximum translation values.
    :param min_rotation: minimum rotation values.
    :param max_rotation: maximum rotation values.
    :param draw_limits: whether to draw limits.
    :param add_spaces: spaces to add to the control.
    :param control_type: type of the control.
    :param filtered_channels: channels to filter.
    :param driven_controls: controls to drive.
    :return: new control node key.
    """

    min_translation = min_translation or [None, None, None]
    max_translation = max_translation or [None, None, None]
    min_rotation = min_rotation or [None, None, None]
    max_rotation = max_rotation or [None, None, None]
    add_spaces = add_spaces or []
    filtered_channels = filtered_channels or [
        unreal.RigControlTransformChannel.TRANSLATION_X,
        unreal.RigControlTransformChannel.TRANSLATION_Y,
        unreal.RigControlTransformChannel.TRANSLATION_Z,
    ]
    driven_controls = driven_controls or []

    # noinspection PyTypeChecker
    customization = unreal.RigControlElementCustomization(
        [space for space in add_spaces]
    )

    # noinspection PyTypeChecker
    global_control_settings = unreal.RigControlSettings(
        customization=customization,
        filtered_channels=filtered_channels,
        driven_controls=driven_controls,
    )

    if no_select:
        global_control_settings.animation_type = (
            unreal.RigControlAnimationType.VISUAL_CUE
        )
    elif proxy:
        global_control_settings.animation_type = (
            unreal.RigControlAnimationType.PROXY_CONTROL
        )
    else:
        global_control_settings.animation_type = (
            unreal.RigControlAnimationType.ANIMATION_CONTROL
        )

    global_control_settings.control_type = consts.CONTROL_TYPES[control_type]
    global_control_settings.display_name = "None"
    global_control_settings.draw_limits = draw_limits
    color = consts.SIDE_COLORS[side] if overwrite_color is None else overwrite_color
    global_control_settings.shape_color = unreal.LinearColor(
        color[0], color[1], color[2], 1.0
    )
    global_control_settings.shape_name = shape
    global_control_settings.shape_visible = True
    global_control_settings.is_transient_control = False

    for i, channel in enumerate(
        [
            unreal.RigControlTransformChannel.PITCH,
            unreal.RigControlTransformChannel.YAW,
            unreal.RigControlTransformChannel.ROLL,
        ]
    ):
        if channel not in filtered_channels:
            # noinspection PyTypeChecker
            min_rotation[i] = 0.0
            # noinspection PyTypeChecker
            max_rotation[i] = 0.0
    for i, channel in enumerate(
        [
            unreal.RigControlTransformChannel.TRANSLATION_X,
            unreal.RigControlTransformChannel.TRANSLATION_Y,
            unreal.RigControlTransformChannel.TRANSLATION_Z,
        ]
    ):
        if channel not in filtered_channels:
            # noinspection PyTypeChecker
            min_translation[i] = 0.0
            # noinspection PyTypeChecker
            max_translation[i] = 0.0
    global_control_settings.primary_axis = unreal.RigControlAxis.X

    if control_type == "transform":
        global_control_settings.limit_enabled = [
            unreal.RigControlLimitEnabled(
                min_translation[0] is not None, max_translation[0] is not None
            ),
            unreal.RigControlLimitEnabled(
                min_translation[1] is not None, max_translation[1] is None
            ),
            unreal.RigControlLimitEnabled(
                min_translation[2] is not None, max_translation[2] is not None
            ),
            unreal.RigControlLimitEnabled(
                min_rotation[0] is not None, max_rotation[0] is not None
            ),
            unreal.RigControlLimitEnabled(
                min_rotation[1] is not None, max_rotation[1] is not None
            ),
            unreal.RigControlLimitEnabled(
                min_rotation[2] is not None, max_rotation[2] is not None
            ),
            unreal.RigControlLimitEnabled(False, False),
            unreal.RigControlLimitEnabled(False, False),
            unreal.RigControlLimitEnabled(False, False),
        ]
        min_translation = [0.0 if fV is None else fV for fV in min_translation]
        max_translation = [0.0 if fV is None else fV for fV in max_translation]
        min_rotation = [0.0 if fV is None else fV for fV in min_rotation]
        max_rotation = [0.0 if fV is None else fV for fV in max_rotation]
        # noinspection PyTypeChecker
        global_control_settings.minimum_value = (
            unreal.RigHierarchy.make_control_value_from_euler_transform(
                unreal.EulerTransform(
                    location=min_translation,
                    rotation=min_rotation,
                    scale=[1.0, 1.0, 1.0],
                )
            )
        )
        # noinspection PyTypeChecker
        global_control_settings.maximum_value = (
            unreal.RigHierarchy.make_control_value_from_euler_transform(
                unreal.EulerTransform(
                    location=max_translation,
                    rotation=max_rotation,
                    scale=[1.0, 1.0, 1.0],
                )
            )
        )
    elif control_type == "translation":
        global_control_settings.limit_enabled = [
            unreal.RigControlLimitEnabled(
                min_translation[0] is not None,
                max_translation[0] is not None,
            ),
            unreal.RigControlLimitEnabled(
                min_translation[1] is not None,
                max_translation[1] is not None,
            ),
            unreal.RigControlLimitEnabled(
                min_translation[2] is not None,
                max_translation[2] is not None,
            ),
        ]
        min_translation = [0.0 if fV is None else fV for fV in min_translation]
        max_translation = [0.0 if fV is None else fV for fV in max_translation]
        global_control_settings.minimum_value = (
            unreal.RigHierarchy.make_control_value_from_vector(
                unreal.Vector(
                    min_translation[0], min_translation[1], min_translation[2]
                )
            )
        )
        global_control_settings.maximum_value = (
            unreal.RigHierarchy.make_control_value_from_vector(
                unreal.Vector(
                    max_translation[0], max_translation[1], max_translation[2]
                )
            )
        )
    elif control_type == "rotation":
        global_control_settings.limit_enabled = [
            unreal.RigControlLimitEnabled(
                min_rotation[0] is not None, max_rotation[0] is not None
            ),
            unreal.RigControlLimitEnabled(
                min_rotation[1] is not None, max_rotation[1] is not None
            ),
            unreal.RigControlLimitEnabled(
                min_rotation[2] is not None, max_rotation[2] is not None
            ),
        ]
        min_rotation = [0.0 if fV is None else fV for fV in min_rotation]
        max_rotation = [0.0 if fV is None else fV for fV in max_rotation]
        global_control_settings.minimum_value = (
            unreal.RigHierarchy.make_control_value_from_rotator(
                unreal.Rotator(
                    pitch=min_rotation[0], roll=min_rotation[1], yaw=min_rotation[2]
                )
            )
        )
        global_control_settings.maximum_value = (
            unreal.RigHierarchy.make_control_value_from_rotator(
                unreal.Rotator(
                    pitch=max_rotation[0], roll=max_rotation[1], yaw=max_rotation[2]
                )
            )
        )
    elif control_type == "scale":
        pass
    else:
        raise Exception(f"Invalid control type: {control_type}")

    # noinspection PyTypeChecker
    new_element_key = control_rig.hierarchy.add_control(
        name,
        parent,
        global_control_settings,
        consts.CONTROL_DEFAULTS[control_type],
        setup_undo=False,
    )
    control_rig.blueprint.hierarchy.set_control_settings(
        new_element_key, global_control_settings, setup_undo=False
    )

    if shape_matrix is None:
        shape_translation, shape_rotation, shape_scale = (
            [0, 0, 0],
            [0, 0, 0, 1],
            [1, 1, 1],
        )
    else:
        shape_translation, shape_rotation, shape_scale = helpers.trs_from_list_matrix(
            shape_matrix
        )
    if shape_force_rotation:
        shape_rotation = shape_force_rotation

    control_rig.blueprint.hierarchy.set_control_shape_transform(
        new_element_key,
        unreal.Transform(
            location=shape_translation, rotation=shape_rotation, scale=shape_scale
        ),
        True,
        setup_undo=False,
    )

    control_settings = control_rig.blueprint.hierarchy.find_control(
        new_element_key
    ).settings
    control_rig.hierarchy.set_control_settings(
        new_element_key, control_settings, setup_undo=False
    )

    return new_element_key
