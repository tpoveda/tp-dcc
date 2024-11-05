from __future__ import annotations

import typing
from typing import Sequence

import unreal

from . import pins
from . import nodes
from . import consts
from . import helpers
from .hierarchy import variable, factory

if typing.TYPE_CHECKING:
    from .controllers import ControlRig
    from .hierarchy.control import Control


def create_single_bone(
    control: Control, joint: str, child_maintain_bone: str | None = None
):
    function_name = "noddle_singleCtrl"
    control_rig = control.control_rig

    if child_maintain_bone:
        function_name = f"{function_name}_maintainChild"
        extra_inputs = [nodes.NodePinInputOutput("ChildMaintain", "FName", False)]
    else:
        extra_inputs = []

    function = nodes.get_function(control_rig, function_name)
    if not function:
        nodes.start_function(
            control_rig,
            function_name,
            inputs=[
                nodes.NodePinInputOutput("Bone", "FName", False),
                nodes.NodePinInputOutput("Control", "FName", False),
                nodes.NodePinInputOutput("Passer", "FName", False),
                nodes.NodePinInputOutput("ATTACHER_root_r", "FConstraintParent", True),
                nodes.NodePinInputOutput("ATTACHER_root_t", "FConstraintParent", True),
                nodes.NodePinInputOutput("ATTACHER_main_r", "FConstraintParent", True),
                nodes.NodePinInputOutput("ATTACHER_main_t", "FConstraintParent", True),
            ]
            + extra_inputs,
        )
        if child_maintain_bone:
            control_rig.open_comment_box("Get Bone to Maintain")
            child_before = variable.new_variable(
                control_rig, "ChildBefore", "FTransform", local=True
            )
            entry_child_maintain = helpers.get_element_key(
                nodes.create_get_entry_variable(control_rig, "ChildMaintain"), "Bone"
            )
            child_transform = nodes.create_get_transform_node(
                control_rig, entry_child_maintain
            )
            nodes.create_set_variable_execute_node(
                control_rig, child_before, child_transform
            )
            control_rig.set_new_column()
            control_rig.close_comment_box("Get Bone to Maintain")

        control_rig.open_comment_box("Attachers")
        control_rig.set_new_column()
        passer = helpers.get_element_key(
            nodes.create_get_entry_variable(control_rig, "Passer"), "Null"
        )
        nodes.create_parent_constraint_execute_node(
            control_rig,
            "Entry.ATTACHER_root_t",
            passer,
            maintain_offset=True,
            skip_rotate=["x", "y", "z"],
        )
        nodes.create_parent_constraint_execute_node(
            control_rig,
            "Entry.ATTACHER_root_r",
            passer,
            maintain_offset=True,
            skip_translate=["x", "y", "z"],
        )
        nodes.create_parent_constraint_execute_node(
            control_rig,
            "Entry.ATTACHER_main_t",
            passer,
            maintain_offset=True,
            skip_rotate=["x", "y", "z"],
        )
        nodes.create_parent_constraint_execute_node(
            control_rig,
            "Entry.ATTACHER_main_r",
            passer,
            maintain_offset=True,
            skip_translate=["x", "y", "z"],
        )
        control_rig.close_comment_box("Attachers")

        control_rig.open_comment_box("Constraint Bone")
        control_rig.set_new_column()
        entry_bone = helpers.get_element_key(
            nodes.create_get_entry_variable(control_rig, "Bone"), "Bone"
        )
        entry_control = helpers.get_element_key(
            nodes.create_get_entry_variable(control_rig, "Control"), "Control"
        )
        control_rig.set_new_column()
        nodes.create_parent_constraint_execute_node(
            control_rig, [(entry_control, 1.0)], entry_bone, maintain_offset=True
        )
        control_rig.close_comment_box("Constraint Bone")

        if child_maintain_bone:
            control_rig.set_new_column()
            control_rig.open_comment_box("Fix Child Bone to Maintain")
            entry_child_maintain = helpers.get_element_key(
                nodes.create_get_entry_variable(control_rig, "ChildMaintain"), "Bone"
            )
            # noinspection PyUnboundLocalVariable
            child_transform = nodes.create_get_variable_node(control_rig, child_before)
            nodes.create_set_transform_execute_node(
                control_rig, entry_child_maintain, child_transform
            )
            control_rig.close_comment_box("Fix Child Bone to Maintain")

        nodes.end_current_function(control_rig, add_to_execute=False)

    single_bone_node = nodes.add_function_node(
        control_rig, function_name, node_size=[300, 400]
    )
    if joint:
        pins.set_string(control_rig, joint, f"{single_bone_node}.Bone")
    pins.set_string(control_rig, control.passer.name, f"{single_bone_node}.Passer")
    pins.set_string(control_rig, control.control.name, f"{single_bone_node}.Control")
    if child_maintain_bone:
        pins.set_string(
            control_rig, child_maintain_bone, f"{single_bone_node}.ChildMaintain"
        )

    return single_bone_node


def create_blend_attributes(
    control_rig: ControlRig,
    attribute_parent: unreal.RigElementKey,
    attribute_names: list[str] | None = None,
) -> str:
    """
    Creates a blend attributes function.

    :param control_rig: control rig to create the function in.
    :param attribute_parent: attribute parent pin path.
    :param attribute_names: attribute names pin paths.
    :return: blend attributes node path.
    """

    attribute_names = attribute_names or ["space_local", "space_head"]

    function_name = f"noddle_blendAttributes_{len(attribute_names)}Inputs"
    function = nodes.get_function(control_rig, function_name)
    if not function:
        nodes.start_function(
            control_rig,
            function_name,
            inputs=[nodes.NodePinInputOutput("CtrlName", "FName", False)]
            + [
                nodes.NodePinInputOutput(f"Attr_{o}", "FName", False)
                for o in range(1, len(attribute_names), 1)
            ],
            outputs=[
                nodes.NodePinInputOutput(f"OutAttr_{o}", "float", True)
                for o in range(0, len(attribute_names), 1)
            ],
            mutable=False,
        )

        user_attributes = [1]
        for i in range(1, len(attribute_names), 1):
            user_attributes.append(
                nodes.create_get_channel_node(
                    control_rig, "Entry.CtrlName", f"Entry.Attr_{i}"
                )
            )
        for i in range(len(user_attributes)):
            if i < len(user_attributes) - 1:
                minus = user_attributes[i + 1 :]
                minus_calculated = (
                    minus[0]
                    if len(minus) == 1
                    else nodes.create_basic_calculate_node(
                        control_rig, minus, operation="Add"
                    )
                )
                difference = nodes.create_basic_calculate_node(
                    control_rig,
                    [user_attributes[i], minus_calculated],
                    operation="Subtract",
                )
                pins.connect_to_pin_1d(
                    control_rig,
                    nodes.create_clamp_node(control_rig, difference, 0, 1),
                    f"Return.OutAttr_{i}",
                )
            else:
                print("asdasdf", user_attributes[i])
                pins.connect_to_pin_1d(
                    control_rig, user_attributes[i], f"Return.OutAttr_{i}"
                )
        nodes.end_current_function(control_rig, add_to_execute=False)

    blend_node = nodes.add_function_node(
        control_rig, function_name, function_is_mutable=False
    )
    pins.set_string(control_rig, attribute_parent.name, f"{blend_node}.CtrlName")
    for i in range(len(attribute_names)):
        if i > 0:
            pins.set_string(control_rig, attribute_names[i], f"{blend_node}.Attr_{i}")

    return blend_node


def create_points_from_items(
    control_rig: ControlRig,
    items: str | list[unreal.RigElementKey | str],
    initial: bool = False,
    local: bool = False,
) -> str:
    """
    Creates a points from items function.

    :param control_rig: control rig to create the function in.
    :param items: items pin paths.
    :param initial: whether it is the initial point or not.
    :param local: whether the points are local or global.
    :return: points pin path.
    """

    function_name = f"noddle_pointsFromItems_{'local' if local else 'global'}"

    function = nodes.get_function(control_rig, function_name)
    if not function:
        nodes.start_function(
            control_rig,
            function_name,
            inputs=[
                nodes.NodePinInputOutput("Items", "FRigElementKey", True),
                nodes.NodePinInputOutput("Initial", "bool", False),
            ],
            outputs=[nodes.NodePinInputOutput("Points", "FVector", True)],
        )
        control_rig.set_new_column()
        points_variable = variable.new_variable(
            control_rig, "OutPoints", "FVector", True, local=True
        )
        points_variable_node = nodes.create_get_variable_node(
            control_rig, points_variable
        )
        nodes.create_reset_array_node(control_rig, points_variable_node)
        control_rig.set_new_column()
        for_each_node = nodes.create_for_each_execute_node(control_rig, "Entry.Items")
        control_rig.set_new_column()
        transform_node = nodes.create_get_transform_node(
            control_rig,
            f"{for_each_node}.Element",
            initial="Entry.Initial",
            local=local,
        )
        nodes.create_aray_add_node(
            control_rig, points_variable_node, f"{transform_node}.Translation"
        )
        control_rig.go_to_parent_execute()

        control_rig.set_new_column()
        pins.connect_to_pin_vector(control_rig, points_variable_node, "Return.Points")
        nodes.end_current_function(control_rig, add_to_execute=False)

    points_node = nodes.add_function_node(
        control_rig, function_name, function_is_mutable=True, node_size=[300.0, 400.0]
    )
    pins.set_item_array(control_rig, items, f"{points_node}.Items")
    pins.connect_to_pin_1d(control_rig, initial, f"{points_node}.Initial")

    return f"{points_node}.Points"


def create_spine_spline(
    control_rig: ControlRig,
    transform_array,
    bones_array,
    negative: str,
    first_controls: str,
    second_controls: str,
    control_weights: str,
    up_vector: Sequence[int | float] | str | None = None,
    stretched: bool | str = False,
) -> str:
    """
    Creates a spine spline control rig function.

    :param control_rig: control rig to create the function in.
    :param transform_array: transform array pin path.
    :param bones_array: bones array pin path.
    :param negative: negative pin path.
    :param first_controls: first controls pin path.
    :param second_controls: second controls pin path.
    :param control_weights: control weights pin path.
    :param up_vector: up vector or up vector pin path.
    :param stretched: whether the spline is stretched or not.
    :return: spine spline control rig function node path.
    """

    function_name = "noddle_spineSpline"

    function = nodes.get_function(control_rig, function_name)
    if not function:
        nodes.start_function(
            control_rig,
            function_name,
            inputs=[
                nodes.NodePinInputOutput("Transforms", "FRigElementKey", True),
                nodes.NodePinInputOutput("Bones", "FRigElementKey", True),
                nodes.NodePinInputOutput("CtrlWeights", "float", True),
                nodes.NodePinInputOutput("FirstCtrls", "int32", True),
                nodes.NodePinInputOutput("SecondCtrls", "int32", True),
                nodes.NodePinInputOutput("Negative", "bool", False),
                nodes.NodePinInputOutput("UpVector", "FVector", False),
                nodes.NodePinInputOutput("Stretched", "bool", False),
            ],
            create_sequence_node=True,
        )
        control_rig.open_comment_box("Check if it is the first time")
        has_metadata = nodes.create_has_metadata_node(
            control_rig,
            nodes.create_array_at_node(control_rig, "Entry.Bones", 0),
            "OffsetTransform",
            pin_type=pins.PinType.Transform,
        )
        does_not_have_metadata = nodes.create_bool_not_node(control_rig, has_metadata)
        nodes.create_branch_execute_node(control_rig, does_not_have_metadata)
        control_rig.close_comment_box("Check if it is the first time")

        current_bone = variable.new_variable(
            control_rig, "CurrentBone", "FRigElementKey"
        )
        for initial in [True, False]:
            control_rig.open_comment_box("Create Splines")
            control_rig.set_new_column()
            current_points = create_points_from_items(
                control_rig, "Entry.Transforms", initial=initial
            )
            spline = nodes.create_spline_from_positions_node(
                control_rig, current_points
            )
            control_rig.close_comment_box("Create Splines")

            control_rig.open_comment_box("Put Joints on Splines and store Positions")
            control_rig.set_new_column()
            entry_bones = nodes.create_get_entry_variable(control_rig, "Bones")
            control_rig.set_new_column()
            stretched_entry = nodes.create_get_entry_variable(control_rig, "Stretched")
            control_rig.set_new_column()
            nodes.create_branch_execute_node(control_rig, stretched_entry)
            control_rig.set_new_column()
            if consts.BLOCK_BRANCH_TRUE:
                nodes.create_fit_chain_to_spline_curve(
                    control_rig, spline, entry_bones, stretched=True
                )
                control_rig.go_to_parent_execute()
            if consts.BLOCK_BRANCH_FALSE:
                nodes.create_fit_chain_to_spline_curve(
                    control_rig, spline, entry_bones, stretched=False
                )
                control_rig.go_to_parent_execute()
            control_rig.set_new_column()
            control_rig.set_new_column()
            for_each = nodes.create_for_each_execute_node(control_rig, "Entry.Bones")
            control_rig.set_new_column()
            spline_metadata_key = f"Splined{('Initial' if initial else '')}"
            if consts.BLOCK_FOREACH:
                position = f"{nodes.create_get_transform_node(control_rig, f'{for_each}.Element')}.Translation"
                nodes.create_set_metadata_execute_node(
                    control_rig,
                    f"{for_each}.Element",
                    spline_metadata_key,
                    position,
                    pin_type=pins.PinType.Vector,
                )
                control_rig.go_to_parent_execute()
            control_rig.close_comment_box("Put Joints on Splines and store Positions")

            # controllers.setNewColumn()
            # sForEach = nodes.createForEachExecuteNode("Entry.Bones")
            # nodes.createSetVariableExecuteNode(vCurrentBone, "%s.Element" % sForEach)
            #
            # controllers.setNewColumn()
            # if controllers.BLOCK_FOREACH:
            #     controllers.openCommentBox("Check if Joint still has a Child")
            #     controllers.setNewColumn()
            #     sMinusOne = nodes.createBasicCalculateNode(
            #         ["%s.Count" % sForEach, 1],
            #         sOperation="Subtract",
            #         iPinType=pins.PinType.integer,
            #     )
            #     sDoJoint = nodes.createConditionNodes(
            #         "%s.Index" % sForEach,
            #         "<",
            #         sMinusOne,
            #         True,
            #         False,
            #         iTermsPinType=pins.PinType.integer,
            #     )
            #     controllers.closeCommentBox("Check if Joint still has a Child")
            #
            #     controllers.setNewColumn()
            #     nodes.createBranchExecuteNode(sDoJoint)
            #     if controllers.BLOCK_BRANCH_TRUE:  # NOT last bone
            #         controllers.setNewColumn()
            #         controllers.openCommentBox("Get Control Weightings")
            #
            #         controllers.setNewColumn()
            #         if bInitial:
            #             sEntryFirstCtrls = nodes.createGetEntryVariable("FirstCtrls")
            #             sStartCtrlIndex = nodes.createArrayAtNode(
            #                 sEntryFirstCtrls, "%s.Index" % sForEach
            #             )
            #             sEntry_Transforms = nodes.createGetEntryVariable("Transforms")
            #             sStartItem = nodes.createArrayAtNode(
            #                 sEntry_Transforms, sStartCtrlIndex
            #             )
            #             sCurrentBone = nodes.createGetVariableNode(vCurrentBone)
            #             nodes.createSetMetaDataExecuteNode(
            #                 sCurrentBone,
            #                 "StartItem",
            #                 sStartItem,
            #                 iType=pins.PinType.item,
            #             )
            #         else:
            #             sCurrentBone = nodes.createGetVariableNode(vCurrentBone)
            #             sStartItem = nodes.createGetMetaData(
            #                 sCurrentBone, "StartItem", iType=pins.PinType.item
            #             )
            #         sStartCtrlTransform = nodes.getTransformNode(
            #             sStartItem, bInitial=bInitial
            #         )
            #
            #         controllers.setNewColumn()
            #         if bInitial:
            #             sEntrySecondCtrls = nodes.createGetEntryVariable("SecondCtrls")
            #             sEndCtrlIndex = nodes.createArrayAtNode(
            #                 sEntrySecondCtrls, "%s.Index" % sForEach
            #             )
            #             sEntry_Transforms = nodes.createGetEntryVariable("Transforms")
            #             sEndItem = nodes.createArrayAtNode(
            #                 sEntry_Transforms, sEndCtrlIndex
            #             )
            #             sCurrentBone = nodes.createGetVariableNode(vCurrentBone)
            #             nodes.createSetMetaDataExecuteNode(
            #                 sCurrentBone, "EndItem", sEndItem, iType=pins.PinType.item
            #             )
            #         else:
            #             sCurrentBone = nodes.createGetVariableNode(vCurrentBone)
            #
            #             sEndItem = nodes.createGetMetaData(
            #                 sCurrentBone, "EndItem", iType=pins.PinType.item
            #             )
            #         sEndCtrlTransform = nodes.getTransformNode(
            #             sEndItem, bInitial=bInitial
            #         )
            #
            #         controllers.setNewColumn()
            #         sEntryCtrlWeights = nodes.createGetEntryVariable("CtrlWeights")
            #         sBlend = nodes.createArrayAtNode(
            #             sEntryCtrlWeights, "%s.Index" % sForEach
            #         )
            #
            #         controllers.closeCommentBox("Get Control Weightings")
            #
            #         controllers.setNewColumn()
            #         controllers.openCommentBox("Aim Targets")
            #         sNextIndex = nodes.createBasicCalculateNode(
            #             ["%s.Index" % sForEach, 1],
            #             sOperation="Add",
            #             iPinType=pins.PinType.integer,
            #         )
            #         sEntry_Bones = nodes.createGetEntryVariable("Bones")
            #         sNextBone = nodes.createArrayAtNode(sEntry_Bones, sNextIndex)
            #
            #         sCurrentBone = nodes.createGetVariableNode(vCurrentBone)
            #         sSourcePosition = nodes.createGetMetaData(
            #             sCurrentBone, sSplinedMetaDataKey, iType=pins.PinType.vector
            #         )
            #         sAimPosition = nodes.createGetMetaData(
            #             sNextBone, sSplinedMetaDataKey, iType=pins.PinType.vector
            #         )
            #         controllers.closeCommentBox("Aim Targets")
            #
            #         controllers.setNewColumn()
            #         controllers.openCommentBox("Aim Secondary Targets")
            #
            #         sEntryUpVector = nodes.createGetEntryVariable("UpVector")
            #         controllers.setNewColumn()
            #
            #         sStartUp = nodes.createRotateVectorNode(
            #             sEntryUpVector, "%s.Rotation" % sStartCtrlTransform
            #         )
            #         sEndUp = nodes.createRotateVectorNode(
            #             sEntryUpVector, "%s.Rotation" % sEndCtrlTransform
            #         )
            #         sInterpUp = nodes.createVectorInterpolateNode(
            #             sBlend, sStartUp, sEndUp
            #         )
            #         controllers.closeCommentBox("Aim Secondary Targets")
            #
            #         controllers.setNewColumn()
            #         controllers.openCommentBox("Aim Nodes")
            #         sEntry_bNegative = nodes.createGetEntryVariable("bNegative")
            #         sNegSideMultipl = nodes.createIfNode(sEntry_bNegative, 1.0, -1.0)
            #         sAimTransform = nodes.createAimNode(
            #             [sSourcePosition, None, None],
            #             sAimPosition,
            #             fWorldUpVector=sInterpUp,
            #             fUpVector=[0, sNegSideMultipl, 0],
            #             bUpIsDirection=True,
            #         )
            #         controllers.closeCommentBox("Aim Nodes")
            #
            #         if bInitial:
            #             controllers.setNewColumn()
            #             controllers.openCommentBox("Calculate Offset")
            #             sCurrentBone = nodes.createGetVariableNode(vCurrentBone)
            #             sInitialTransform = nodes.getTransformNode(
            #                 sCurrentBone, bInitial=True
            #             )
            #             controllers.setNewColumn()
            #             sOffsetTransform = nodes.createMakeRelativeNode(
            #                 sInitialTransform, sAimTransform
            #             )
            #             nodes.createSetMetaDataExecuteNode(
            #                 sCurrentBone,
            #                 "OffsetTransform",
            #                 sOffsetTransform,
            #                 iType=pins.PinType.transform,
            #             )
            #             controllers.closeCommentBox("Calculate Offset")
            #         else:
            #             controllers.setNewColumn()
            #             controllers.openCommentBox("Apply")
            #             sCurrentBone = nodes.createGetVariableNode(vCurrentBone)
            #             sOffsetTransform = nodes.createGetMetaData(
            #                 sCurrentBone,
            #                 "OffsetTransform",
            #                 iType=pins.PinType.transform,
            #             )
            #             sAbsoluteTransform = nodes.createMakeAbsoluteNode(
            #                 sOffsetTransform, sAimTransform
            #             )
            #             nodes.createSetTransformExecuteNode(
            #                 sCurrentBone, sAbsoluteTransform
            #             )
            #             controllers.closeCommentBox("Apply")
            #         controllers.goToParentExecute()

        nodes.end_current_function(control_rig, add_to_execute=False)


def create_fk_spline(
    control_rig: ControlRig,
    root: unreal.RigElementKey,
    controls: list[Control],
    joints: list[str],
    side: str,
    control_weightings: Sequence[list[int | float]],
    end_null: unreal.RigElementKey,
    up_vector: list[float],
):
    """
    Creates a FK spline control rig.

    :param control_rig:
    :param root:
    :param controls:
    :param joints:
    :param side:
    :param control_weightings:
    :param end_null:
    :param up_vector:
    :return:
    """

    attributes_control = controls[-1].control
    factory.create_float_control(
        control_rig, "Stretched", parent=attributes_control, is_bool=True, default=False
    )

    controls_length = len(controls)
    function_name = f"noodle_fkSpline_{controls_length}Transforms"
    function = nodes.get_function(control_rig, function_name)
    if not function:
        procedural_inputs: list[nodes.NodePinInputOutput] = []
        for i in range(controls_length):
            procedural_inputs.append(
                nodes.NodePinInputOutput(f"Passer_{i}", "FRigElementKey", False)
            )
            if i > 0:
                procedural_inputs.append(
                    nodes.NodePinInputOutput(
                        f"ATTACHER_fkSpline_{helpers.get_letter(i - 1)}_t",
                        "FConstraintParent",
                        True,
                    )
                )
                procedural_inputs.append(
                    nodes.NodePinInputOutput(
                        f"ATTACHER_fkSpline_{helpers.get_letter(i - 1)}_r",
                        "FConstraintParent",
                        True,
                    )
                )

        nodes.start_function(
            control_rig,
            function_name,
            inputs=[
                nodes.NodePinInputOutput("Root", "FRigElementKey", False),
                nodes.NodePinInputOutput("Transforms", "FRigElementKey", True),
                nodes.NodePinInputOutput("Bones", "FRigElementKey", True),
                nodes.NodePinInputOutput("CtrlWeights", "float", True),
                nodes.NodePinInputOutput("FirstCtrls", "int32", True),
                nodes.NodePinInputOutput("SecondCtrls", "int32", True),
                nodes.NodePinInputOutput("Negative", "bool", False),
                nodes.NodePinInputOutput("UpVector", "FVector", False),
                nodes.NodePinInputOutput("AttributesControl", "FName", False),
                nodes.NodePinInputOutput("ATTACHER_root_t", "FConstraintParent", True),
                nodes.NodePinInputOutput("ATTACHER_root_r", "FConstraintParent", True),
            ]
            + procedural_inputs,
        )
        control_rig.set_new_column()
        for i in range(controls_length):
            control_rig.set_new_column()
            if i == 0:
                nodes.create_parent_constraint_execute_node(
                    control_rig,
                    "Entry.ATTACHER_root_t",
                    "Entry.Root",
                    maintain_offset=True,
                    skip_rotate=["x", "y", "z"],
                )
                nodes.create_parent_constraint_execute_node(
                    control_rig,
                    "Entry.ATTACHER_root_r",
                    "Entry.Root",
                    maintain_offset=True,
                    skip_translate=["x", "y", "z"],
                )
            else:
                nodes.create_parent_constraint_execute_node(
                    control_rig,
                    f"Entry.ATTACHER_fkSpline_{helpers.get_letter(i - 1)}_t",
                    f"Entry.Passer_{i}",
                    maintain_offset=True,
                    skip_rotate=["x", "y", "z"],
                )
                nodes.create_parent_constraint_execute_node(
                    control_rig,
                    f"Entry.ATTACHER_fkSpline_{helpers.get_letter(i - 1)}_r",
                    f"Entry.Passer_{i}",
                    maintain_offset=True,
                    skip_translate=["x", "y", "z"],
                )

        control_rig.open_comment_box("Bones")
        control_rig.set_new_column()
        entry_negative = nodes.create_get_entry_variable(control_rig, "Negative")
        entry_first_controls = nodes.create_get_entry_variable(
            control_rig, "FirstCtrls"
        )
        entry_second_controls = nodes.create_get_entry_variable(
            control_rig, "SecondCtrls"
        )
        entry_control_weights = nodes.create_get_entry_variable(
            control_rig, "CtrlWeights"
        )
        entry_up_vector = nodes.create_get_entry_variable(control_rig, "UpVector")
        entry_transforms = nodes.create_get_entry_variable(control_rig, "Transforms")
        entry_bones = nodes.create_get_entry_variable(control_rig, "Bones")
        entry_attributes_control = nodes.create_get_entry_variable(
            control_rig, "AttributesControl"
        )
        stretched = nodes.create_get_channel_node(
            control_rig, entry_attributes_control, "Stretched"
        )
        control_rig.set_new_column()

        print(
            "gogogog",
            list(control_rig.latest_function_stack()._comment_boxes_node_points.keys()),
        )

        create_spine_spline(
            control_rig,
            entry_transforms,
            entry_bones,
            entry_negative,
            entry_first_controls,
            entry_second_controls,
            entry_control_weights,
            entry_up_vector,
            stretched=stretched,
        )

        print(
            "adsfasdfasfasdfs",
            list(control_rig.latest_function_stack()._comment_boxes_node_points.keys()),
        )

        control_rig.close_comment_box("Bones")
        nodes.end_current_function(control_rig, add_to_execute=False)
