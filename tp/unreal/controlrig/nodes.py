from __future__ import annotations

import string
import typing
import logging
from typing import Sequence
from dataclasses import dataclass

import unreal

from . import consts, pins
from .helpers import string_between_quotes

if typing.TYPE_CHECKING:
    from .controllers import ControlRig
    from .hierarchy.variable import Variable

logger = logging.getLogger(__name__)


@dataclass
class NodePinInputOutput:
    """
    Data class that defines a node pin input or output.
    """

    name: str
    type: str
    is_array: any


def node_name_from_node(
    node: unreal.RigVMLibraryNode
    | unreal.RigVMNode
    | unreal.RigVMUnitNode
    | unreal.RigVMVariableNode
    | unreal.RigVMTemplateNode,
) -> str:
    """
    Returns the name of the given node.

    :param node: node to get name from.
    :return: node name.
    """

    return string_between_quotes(str(node))


def new_node_position(
    control_rig: ControlRig,
    node_size: tuple[int, int] | None = None,
    execute_node: bool = False,
) -> unreal.Vector2D:
    """
    Returns a new node position based on the given node size.

    :param control_rig: control rig object.
    :param node_size: size of the node to place.
    :param execute_node: whether the node is an execute node.
    :return: new node position.
    """

    node_size = node_size or [350, 200]

    function_stack = control_rig.function_stack()[-1]
    if function_stack.next_is_new_column:
        function_stack.current_node_position[0] += (
            function_stack.last_node_size[0]
            + function_stack.gap * consts.NEXT_COLUMN_GAP_FACTOR
        )
        function_stack.current_node_position[1] = (
            function_stack.top_node_position
            if execute_node
            else (function_stack.top_node_position + 100)
        )
        function_stack.next_is_new_column = False
    else:
        function_stack.current_node_position[1] += (
            function_stack.last_node_size[1] + function_stack.gap
        )

    function_stack.maximum_height = max(
        function_stack.maximum_height,
        function_stack.current_node_position[1] + node_size[1],
    )

    function_stack.last_node_size = node_size

    return unreal.Vector2D(
        function_stack.current_node_position[0], function_stack.current_node_position[1]
    )


def create_node_from_path(
    control_rig: ControlRig,
    path: str,
    force_node_position: Sequence[int | float] | None = None,
    node_size: Sequence[int | float] | None = None,
    execute_node: bool = False,
) -> str:
    """
    Creates a new node from the given path.

    :param control_rig: control rig object.
    :param path: path to the node to create.
    :param force_node_position: optional list of x and y position to force the node to be placed at.
    :param node_size: optional list of x and y size for the node.
    :param execute_node: whether the node is an execute node.
    :return: name of the created node.
    """

    node_size = node_size or [300.0, 200.0]

    if force_node_position is None:
        node_position = new_node_position(
            control_rig, node_size=node_size, execute_node=execute_node
        )
    else:
        node_position = unreal.Vector2D(force_node_position[0], force_node_position[1])

    # noinspection PyTypeChecker
    vm_unit_node = control_rig.function_stack()[
        -1
    ].vm_model.add_unit_node_from_struct_path(
        path, "Execute", node_position, path.split(".")[-1], setup_undo_redo=False
    )
    control_rig.record_node_for_comment_box(vm_unit_node, node_size)

    return node_name_from_node(vm_unit_node)


def add_to_execute(
    control_rig: ControlRig,
    node_name: str,
    following_execute_pin: str = "ExecuteContext",
    error_if_last_execute_no_exists: bool = True,
):
    """
    Adds the given node to the execute node.

    :param control_rig: control rig object.
    :param node_name: name of the node to connect.
    :param following_execute_pin: name of the pin to connect the node to.
    :param error_if_last_execute_no_exists: whether to raise an error if the last execute node does not exist.
    """

    new_execute = f"{node_name}.{following_execute_pin}"
    function_stack = control_rig.function_stack()[-1]
    try:
        function_stack.vm_model.add_link(
            function_stack.last_executes[-1], new_execute, setup_undo_redo=False
        )
    except Exception as err:
        if error_if_last_execute_no_exists:
            raise
        else:
            logger.warning(f"Skipping execute ...: {err}")
            return
    function_stack.last_executes[-1] = new_execute


def add_to_execute_embedded(
    control_rig: ControlRig,
    node_name: str,
    parent_execute_pin: str = "Completed",
    following_execute_pin: str = "ExecuteContext",
):
    """
    Adds the given node to the execute node.

    :param control_rig: control rig object.
    :param node_name: name of the node to connect.
    :param parent_execute_pin: name of the pin to connect the node to.
    :param following_execute_pin: name of the pin to connect the node to.
    """

    new_execute = f"{node_name}.{following_execute_pin}"
    function_stack = control_rig.latest_function_stack()
    control_rig.latest_function_stack().vm_model.add_link(
        function_stack.last_executes[-1], new_execute, setup_undo_redo=False
    )
    function_stack.last_executes.append(new_execute)
    function_stack.last_executes[-2] = f"{node_name}.{parent_execute_pin}"


def new_sequence_node_plug(
    control_rig: ControlRig, padding: int = 300, force: bool = False
):
    """
    Creates a new sequencer plug.

    :param control_rig: control rig object.
    :param padding: extra padding to add to the top node position.
    :param force: whether to force the creation of a new sequencer plug.
    """

    function_stack = control_rig.function_stack()[-1]
    if (
        not force
        and function_stack.last_sequencer_plug
        and not function_stack.last_sequencer_plug.get_target_links()
    ):
        logger.info(
            "Skipping creating new sequencer plug as last one has no target links."
        )
        return

    current_sequencer = function_stack.sequence_node
    if not current_sequencer:
        msg = (
            f"FunctionStack.FunctionName: {function_stack.function_name} | "
            f"Current function stack does not have a sequencer."
        )
        logger.exception(msg)
        raise Exception(msg)

    if function_stack.current_sequence_plug_count < 2:
        pin_name = f"{current_sequencer}.{string.ascii_uppercase[function_stack.current_sequence_plug_count]}"
    else:
        pin_name = function_stack.vm_model.add_aggregate_pin(
            current_sequencer, "", "", setup_undo_redo=False
        )

    function_stack.last_executes[-1] = pin_name
    function_stack.last_sequencer_plug = function_stack.vm_model.get_graph().find_pin(
        pin_name
    )
    function_stack.top_node_position = function_stack.maximum_height + padding
    function_stack.current_node_position[0] = 0
    function_stack.current_node_position[1] = function_stack.top_node_position
    function_stack.maximum_height = function_stack.top_node_position
    function_stack.current_sequence_plug_count += 1
    function_stack.last_node_size = (0, 0)


def create_sequence(control_rig: ControlRig):
    """
    Creates a new sequencer node.

    :param control_rig: control rig object.
    """

    function_stack = control_rig.function_stack()[-1]
    function_stack.sequence_node = create_node_from_path(
        control_rig,
        "/Script/ControlRig.RigUnit_SequenceAggregate",
        force_node_position=[-200, 0],
    )
    add_to_execute(
        control_rig, function_stack.sequence_node, error_if_last_execute_no_exists=False
    )
    new_sequence_node_plug(control_rig, force=False)


def create_get_variable_node(
    control_rig: ControlRig,
    variable: Variable,
    force_node_position: Sequence[int | float] | None = None,
    node_size: Sequence[int | float] | None = None,
) -> str:
    """
    Creates a new get variable node.

    :param control_rig: control rig object.
    :param variable: variable to get.
    :param force_node_position: optional list of x and y position to force the node to be placed at.
    :param node_size: optional list of x and y size for the node.
    :return: name of the created node.
    """

    node_size = node_size or [300.0, 30.0]
    if force_node_position is None:
        node_position = new_node_position(
            control_rig, node_size=node_size, execute_node=False
        )
    else:
        node_position = unreal.Vector2D(force_node_position[0], force_node_position[1])

    function_stack = control_rig.latest_function_stack()

    if variable.local:
        # noinspection PyTypeChecker
        variable_node = function_stack.vm_model.add_variable_node_from_object_path(
            variable.name,
            variable.type,
            variable.cpp_type,
            is_getter=True,
            default_value="",
            position=node_position,
            setup_undo_redo=False,
        )
    else:
        if variable.cpp_type:
            # noinspection PyTypeChecker
            variable_node = function_stack.vm_model.add_variable_node_from_object_path(
                variable.name,
                variable.type,
                variable.cpp_type,
                is_getter=True,
                default_value="",
                position=node_position,
                setup_undo_redo=False,
            )
        else:
            # noinspection PyTypeChecker
            variable_node = function_stack.vm_model.add_variable_node(
                variable.name,
                variable.type,
                None,
                is_getter=False,
                default_value="",
                position=node_position,
                setup_undo_redo=False,
            )
    control_rig.record_node_for_comment_box(variable_node, node_size)

    variable_node_name = node_name_from_node(variable_node)

    return f"{variable_node_name}.Value"


def create_get_entry_variable(
    control_rig: ControlRig,
    name: str,
    force_node_position: Sequence[int | float] | None = None,
    node_size: Sequence[int | float] | None = None,
) -> str:
    """
    Creates a new get entry variable node.

    :param control_rig: control rig object.
    :param name: name of the variable to get.
    :param force_node_position: optional list of x and y position to force the node to be placed at.
    :param node_size: optional list of x and y size for the node.
    :return: name of the created node.
    """

    node_size = node_size or [300.0, 30.0]
    if force_node_position is None:
        node_position = new_node_position(
            control_rig, node_size=node_size, execute_node=False
        )
    else:
        node_position = unreal.Vector2D(force_node_position[0], force_node_position[1])

    function_stack = control_rig.latest_function_stack()

    pin_type, pin_is_array = function_stack.inputs[name]

    cpp_type = consts.CPP_TYPE_TO_OBJECT_PATH.get(pin_type, None)
    type_to_pass = f"TArray<{pin_type}>" if pin_is_array else pin_type

    if cpp_type:
        # noinspection PyTypeChecker
        variable_node = function_stack.vm_model.add_variable_node_from_object_path(
            name,
            type_to_pass,
            cpp_type,
            is_getter=True,
            default_value="",
            position=node_position,
            setup_undo_redo=False,
        )
    else:
        # noinspection PyTypeChecker
        variable_node = function_stack.vm_model.add_variable_node(
            name,
            type_to_pass,
            None,
            is_getter=True,
            default_value="",
            position=node_position,
            setup_undo_redo=False,
        )
    control_rig.record_node_for_comment_box(variable_node, node_size)

    variable_node_name = node_name_from_node(variable_node)
    return f"{variable_node_name}.Value"


def create_set_variable_execute_node(
    control_rig: ControlRig,
    variable: Variable,
    x_value,
    force_node_position: tuple[int | float] | None = None,
    node_size: list[int | float] | None = None,
) -> str:
    """
    Creates a new set variable execute node.

    :param control_rig: control rig object.
    :param variable: variable to set.
    :param x_value: value to set the variable to.
    :param force_node_position: optional list of x and y position to force the node to be placed at.
    :param node_size: optional list of x and y size for the node.
    :return: name of the created node.
    """

    node_size = node_size or [300.0, 200.0]
    if force_node_position is None:
        node_position = new_node_position(
            control_rig, node_size=node_size, execute_node=False
        )
    else:
        node_position = unreal.Vector2D(force_node_position[0], force_node_position[1])

    function_stack = control_rig.latest_function_stack()

    if variable.local:
        # noinspection PyTypeChecker
        variable_node = function_stack.vm_model.add_variable_node_from_object_path(
            variable.name,
            variable.type,
            variable.cpp_type,
            is_getter=False,
            default_value="",
            position=node_position,
            setup_undo_redo=False,
        )
    else:
        # noinspection PyTypeChecker
        variable_node = function_stack.vm_model.add_variable_node(
            variable.name,
            variable.type,
            None,
            is_getter=False,
            default_value="",
            position=node_position,
            setup_undo_redo=False,
        )
    control_rig.record_node_for_comment_box(variable_node, node_size)

    variable_node_name = node_name_from_node(variable_node)
    if variable.type == "FVector":
        pins.connect_to_pin_vector(control_rig, x_value, f"{variable_node_name}.Value")
    else:
        pins.connect_to_pin_1d(control_rig, x_value, f"{variable_node}.Value")

    add_to_execute(control_rig, variable_node_name)

    return variable_node_name


def create_parent_constraint_execute_node(
    control_rig: ControlRig,
    x_parents: str | Sequence[tuple[unreal.RigElementKey, float]],
    bone: unreal.RigElementKey | str,
    maintain_offset: bool = False,
    skip_translate: Sequence[str] | None = None,
    skip_rotate: Sequence[str] | None = None,
    skip_scale: Sequence[str] | None = None,
    weight: float = 1.0,
) -> str:
    """
    Creates a new parent constraint execute node.

    :param control_rig:
    :param x_parents:
    :param bone:
    :param maintain_offset:
    :param skip_translate:
    :param skip_rotate:
    :param skip_scale:
    :param weight:
    :return:
    """

    parent_constraint_node = create_node_from_path(
        control_rig,
        "/Script/ControlRig.RigUnit_ParentConstraint",
        node_size=[300, 400],
        execute_node=True,
    )

    for axis in skip_translate or []:
        control_rig.latest_function_stack().vm_model.set_pin_default_value(
            f"{parent_constraint_node}.Filter.TranslationFilter.b{axis.upper()}",
            "false",
            False,
            setup_undo_redo=False,
        )
    for axis in skip_rotate or []:
        control_rig.latest_function_stack().vm_model.set_pin_default_value(
            f"{parent_constraint_node}.Filter.RotationFilter.b{axis.upper()}",
            "false",
            False,
            setup_undo_redo=False,
        )
    for axis in skip_scale or []:
        control_rig.latest_function_stack().vm_model.set_pin_default_value(
            f"{parent_constraint_node}.Filter.ScaleFilter.b{axis.upper()}",
            "false",
            False,
            setup_undo_redo=False,
        )

    pins.connect_item(control_rig, bone, f"{parent_constraint_node}.Child")

    pins.connect_to_pin_constraint_parent_array(
        control_rig, x_parents, f"{parent_constraint_node}.Parents"
    )
    pins.connect_to_pin_1d(
        control_rig, maintain_offset, f"{parent_constraint_node}.bMaintainOffset"
    )
    pins.connect_to_pin_1d(control_rig, weight, f"{parent_constraint_node}.Weight")

    add_to_execute(control_rig, parent_constraint_node)

    return parent_constraint_node


def get_function(
    control_rig: ControlRig, function_name: str
) -> unreal.RigVMLibraryNode:
    """
    Returns the function with the given name.

    :param control_rig: control rig object.
    :param function_name: name of the function to get.
    :return: found function.
    """

    # noinspection PyTypeChecker
    return control_rig.function_library.find_function(function_name)


def start_function(
    control_rig: ControlRig,
    function_name: str,
    inputs: Sequence[NodePinInputOutput] | None = None,
    outputs: Sequence[NodePinInputOutput] | None = None,
    mutable: bool = True,
    create_sequence_node: bool = False,
) -> str:
    """
    Creates a new function.

    :param control_rig: control rig object.
    :param function_name: name of the function to create.
    :param inputs: optional list of input pins to add to the function.
    :param outputs: optional list of output pins to add to the function.
    :param mutable: whether the function is mutable.
    :param create_sequence_node: whether to create a sequence node.
    :return: name of the created function node.
    """

    control_rig.add_function_to_stack(
        function_name,
        mutable=mutable,
        x_inputs=inputs,
        x_outputs=outputs,
    )

    # noinspection PyTypeChecker,SpellCheckingInspection
    ufunction = control_rig.library.add_function_to_library(
        function_name, mutable=mutable, setup_undo_redo=False
    )
    function_node_name = node_name_from_node(ufunction)

    function_library: unreal.RigVMController = (
        control_rig.blueprint.get_controller_by_name(function_node_name)
    )
    for input_pin in inputs or []:
        # noinspection PyTypeChecker
        function_library.add_exposed_pin(
            input_pin.name,
            unreal.RigVMPinDirection.INPUT,
            f"TArray<{input_pin.type}>" if input_pin.is_array else input_pin.type,
            consts.CPP_TYPE_TO_OBJECT_PATH.get(input_pin.type, ""),
            "",
            setup_undo_redo=False,
        )
    for output_pin in outputs or []:
        # noinspection PyTypeChecker
        function_library.add_exposed_pin(
            output_pin.name,
            unreal.RigVMPinDirection.OUTPUT,
            f"TArray<{output_pin.type}>" if output_pin.is_array else output_pin.type,
            consts.CPP_TYPE_TO_OBJECT_PATH.get(output_pin.type, ""),
            "",
            setup_undo_redo=False,
        )

    control_rig.function_stack()[
        -1
    ].vm_model = control_rig.blueprint.get_controller_by_name(function_node_name)

    if mutable and create_sequence_node:
        create_sequence(control_rig)

    return function_node_name


def add_function_node(
    control_rig: ControlRig,
    function_name: str,
    function_is_mutable: bool = True,
    node_size: Sequence[int | float] | None = None,
) -> str:
    """
    Adds a function node to the current control rig.

    :param control_rig: control rig object.
    :param function_name: name of the function to add.
    :param function_is_mutable: whether the function is mutable.
    :param node_size: size of the node to add.
    :return: name of the added function node.
    """

    node_size = node_size or [300.0, 200.0]
    node_position = new_node_position(
        control_rig, node_size=node_size, execute_node=function_is_mutable
    )
    # noinspection PyTypeChecker
    node = control_rig.function_stack()[-1].vm_model.add_function_reference_node(
        control_rig.blueprint.get_local_function_library().find_function(function_name),
        node_position,
        function_name,
        setup_undo_redo=False,
    )
    control_rig.record_node_for_comment_box(node)
    function_node = node_name_from_node(node)
    if function_is_mutable:
        add_to_execute(control_rig, function_node)

    return function_node


# noinspection PyShadowingNames
def end_current_function(
    control_rig: ControlRig,
    add_to_execute: bool = True,
    return_in_new_sequence_plug: bool = False,
):
    """
    Ends the current function.

    :param control_rig: control rig object.
    :param add_to_execute: whether to add the function to the execute node.
    :param return_in_new_sequence_plug: whether to return in a new sequence plug.
    """

    function_stack = control_rig.latest_function_stack()
    if function_stack.mutable:
        if function_stack.sequence_node and return_in_new_sequence_plug:
            new_sequence_node_plug(control_rig)
        control_rig.latest_function_stack().vm_model.add_link(
            control_rig.latest_function_stack().last_executes[-1],
            "Return.ExecuteContext",
            setup_undo_redo=False,
        )
    # noinspection PyTypeChecker
    control_rig.function_stack()[-1].vm_model.set_node_position_by_name(
        "Return",
        unreal.Vector2D(
            function_stack.current_node_position[0] + 600,
            function_stack.current_node_position[1],
        ),
        setup_undo_redo=False,
    )
    function_name = function_stack.function_name
    del control_rig.function_stack()[-1]

    if add_to_execute:
        return add_function_node(control_rig, function_name)


def create_get_transform_node(
    control_rig: ControlRig,
    element: unreal.RigElementKey | str,
    local: bool = False,
    initial: bool | str = False,
) -> str:
    """
    Returns the transform pin path for the given element.

    :param control_rig: control rig object.
    :param element: element to get the transform node for.
    :param local: whether to get the local transform node.
    :param initial: whether to get the initial transform node.
    :return: name of the transform node.
    """

    node = create_node_from_path(
        control_rig, "/Script/ControlRig.RigUnit_GetTransform", node_size=[300, 200]
    )
    pins.connect_item(control_rig, element, f"{node}.Item")
    control_rig.latest_function_stack().vm_model.set_pin_default_value(
        f"{node}.Space",
        "LocalSpace" if local else "GlobalSpace",
        False,
        setup_undo_redo=False,
    )
    pins.connect_to_pin_1d(control_rig, initial, f"{node}.bInitial")

    return f"{node}.Transform"


def add_template_node(
    control_rig: ControlRig,
    node_type_path: str,
    estimated_node_size: Sequence[int | float] | None = None,
):
    """
    Adds a template node to the current control rig.

    :param control_rig: control rig object.
    :param node_type_path: path to the node type to add.
    :param estimated_node_size: optional list of x and y size for the node.
    :return: name of the added node.
    """

    estimated_node_size = estimated_node_size or [300, 200]
    # noinspection PyTypeChecker
    node = control_rig.latest_function_stack().vm_model.add_template_node(
        node_type_path,
        new_node_position(control_rig, node_size=estimated_node_size),
        node_type_path.split("::")[0],
        setup_undo_redo=False,
    )
    control_rig.record_node_for_comment_box(node, estimated_node_size)
    return node_name_from_node(node)


def create_set_transform_execute_node(
    control_rig: ControlRig,
    element: str | unreal.RigElementKey,
    from_element: str,
    propagate_to_children: bool = True,
    local: bool = False,
    initial: bool = False,
    weight: float = 1.0,
) -> str:
    """
    Creates a new set transform execute node.

    :param control_rig: control rig object.
    :param element: element to set the transform to.
    :param from_element: element to get the transform from.
    :param propagate_to_children: whether to propagate the transform to children.
    :param local: whether to set the transform in local space.
    :param initial: whether to set the initial transform.
    :param weight: weight of the transform.
    :return: name of the created node.
    """

    node = add_template_node(
        control_rig,
        "Set Transform::Execute(in Item,in Space,in bInitial,in Value,in Weight,in bPropagateToChildren,io ExecuteContext)",
    )
    pins.connect_item(control_rig, element, f"{node}.Item")
    pins.connect_to_pin_1d(
        control_rig, propagate_to_children, f"{node}.bPropagateToChildren"
    )
    pins.resolve_wildcard_pin(control_rig, f"{node}.Value", "FTransform")
    pins.connect_to_pin_transform(control_rig, from_element, f"{node}.Value")
    pins.set_default_value(
        control_rig, "LocalSpace" if local else "GlobalSpace", f"{node}.Space"
    )

    if initial:
        pins.connect_to_pin_1d(control_rig, initial, f"{node}.bInitial")

    pins.connect_to_pin_1d(control_rig, weight, f"{node}.Weight")

    add_to_execute(control_rig, node)

    return node


def create_get_channel_node(
    control_rig: ControlRig, parent_ctrl_name: str, attribute_name: str
) -> str:
    """
    Creates a new get channel node.

    :param control_rig: control rig object.
    :param parent_ctrl_name: parent control name.
    :param attribute_name: attribute name.
    :return:
    """

    node = add_template_node(
        control_rig,
        "GetAnimationChannel::Execute(out Value,in Control,in Channel,in bInitial)",
    )
    if "." in parent_ctrl_name:
        pins.connect_to_pin_1d(control_rig, parent_ctrl_name, f"{node}.Control")
    else:
        pins.set_string(control_rig, parent_ctrl_name, f"{node}.Control")
    if "." in attribute_name:
        pins.connect_to_pin_1d(control_rig, attribute_name, f"{node}.Channel")
    else:
        pins.set_string(control_rig, attribute_name, f"{node}.Channel")

    return f"{node}.Value"


def create_branch_execute_node(control_rig: ControlRig, off_on: bool | str) -> str:
    """
    Creates a new branch execute node.

    :param control_rig: control rig object.
    :param off_on: condition to branch on.
    :return: name of the created node.
    """

    node = control_rig.latest_function_stack().vm_model.add_branch_node(
        new_node_position(control_rig, execute_node=True)
    )
    control_rig.record_node_for_comment_box(node, estimated_size=[300, 300])
    node_name = node_name_from_node(node)
    pins.connect_to_pin_1d(control_rig, off_on, f"{node_name}.Condition")
    new_execute = f"{node_name}.ExecuteContext"
    function_stack = control_rig.latest_function_stack()
    function_stack.vm_model.add_link(
        function_stack.last_executes[-1], new_execute, setup_undo_redo=False
    )
    function_stack.last_executes[-1] = f"{node_name}.Completed"
    function_stack.last_executes.append(f"{node_name}.False")
    function_stack.last_executes.append(f"{node_name}.True")

    return node_name


def create_for_each_execute_node(
    control_rig: ControlRig,
    array: str | None = None,
    array_is_string_list: bool = False,
) -> str:
    """
    Creates a new for each execute node.

    :param control_rig: control rig object.
    :param array: array to iterate over.
    :param array_is_string_list: whether the array is a string list.
    :return: name of the created node.
    """

    node = control_rig.latest_function_stack().vm_model.add_array_node_from_object_path(
        unreal.RigVMOpCode.ARRAY_ITERATOR,
        "FRigVMUnknownType",
        "/Script/RigVM.RigVMUnknownType",
        new_node_position(control_rig, execute_node=True),
        "ArrayIterator",
    )
    control_rig.record_node_for_comment_box(node, estimated_size=[200, 300])
    for_each_node_name = node_name_from_node(node)
    if array is not None:
        if array_is_string_list:
            pins.resolve_wildcard_pin(
                control_rig, f"{for_each_node_name}.Array", "TArray<FName>"
            )
            pins.set_string_array(control_rig, array, f"{for_each_node_name}.Array")
        else:
            pins.connect_to_pin_1d(control_rig, array, f"{for_each_node_name}.Array")
    add_to_execute_embedded(control_rig, for_each_node_name)

    return for_each_node_name


def create_basic_calculate_node(
    control_rig: ControlRig,
    items: str | Sequence[str],
    operation: str = "Multiply",
    pin_type: pins.PinType = pins.PinType.Double,
):
    """
    Creates a new basic calculate node.

    :param control_rig: control rig object.
    :param items: items to calculate.
    :param operation: operation to perform.
    :param pin_type: pin type of the items.
    :return: name of the result pin.
    """

    if operation not in ["Add", "Subtract", "Multiply", "Divide", "Power"]:
        raise Exception(f"Invalid operation: {operation}")

    estimated_height = 50 + len(items) * 25
    node = add_template_node(
        control_rig,
        f"{operation}::Execute(in A,in B,out Result)",
        estimated_node_size=[300, estimated_height],
    )
    pins.resolve_wildcard_pin(control_rig, f"{node}.A", pin_type.value)

    if len(items) > 2:
        for _ in range(len(items) - 2):
            control_rig.latest_function_stack().vm_model.add_aggregate_pin(
                node, "", "", setup_undo_redo=False
            )

    for i, item in enumerate(items):
        letter = string.ascii_uppercase[i]
        attr = f"{node}.{letter}"
        if pin_type == pins.PinType.Vector:
            pins.connect_to_pin_vector(control_rig, item, attr)
        elif pin_type == pins.PinType.Transform:
            pins.connect_to_pin_transform(control_rig, item, attr)
        else:
            pins.connect_to_pin_1d(control_rig, item, attr)

    return f"{node}.Result"


def create_negate_node(control_rig: ControlRig, value: str) -> str:
    """
    Creates a new negate node.

    :param control_rig: control rig object.
    :param value: value to negate.
    :return: name of the result pin.
    """

    negate_node = add_template_node(control_rig, "Negate::Execute(in Value,out Result)")
    pins.connect_to_pin_1d(control_rig, value, f"{negate_node}.Value")
    return f"{negate_node}.Result"


def create_clamp_node(
    control_rig: ControlRig,
    value: int | str,
    min_value: int,
    max_value: int,
    vector: bool = False,
):
    """
    Creates a new clamp node.

    :param control_rig: control rig object.
    :param value: clamp value.
    :param min_value: minimum clamp value.
    :param max_value: maximum clamp value.
    :param vector: whether the clamp is a vector.
    :return: name of the result pin.
    """

    clamp_node = add_template_node(
        control_rig, "Clamp::Execute(in Value,in Minimum,in Maximum,out Result)"
    )
    if vector:
        # noinspection PyTypeChecker
        control_rig.latest_function_stack().vm_model.resolve_wild_card_pin(
            f"{clamp_node}.Value",
            "FVector",
            "/Script/CoreUObject.Vector",
            setup_undo_redo=False,
        )
        pins.connect_to_pin_vector(control_rig, value, f"{clamp_node}.Value")
        pins.connect_to_pin_vector(control_rig, min_value, f"{clamp_node}.Minimum")
        pins.connect_to_pin_vector(control_rig, max_value, f"{clamp_node}.Maximum")
    else:
        # noinspection PyTypeChecker
        control_rig.latest_function_stack().vm_model.resolve_wild_card_pin(
            f"{clamp_node}.Value", "double", "None", setup_undo_redo=False
        )
        pins.connect_to_pin_1d(control_rig, value, f"{clamp_node}.Value")
        pins.connect_to_pin_1d(control_rig, min_value, f"{clamp_node}.Minimum")
        pins.connect_to_pin_1d(control_rig, max_value, f"{clamp_node}.Maximum")

    return f"{clamp_node}.Result"


def create_bool_and_node(control_rig: ControlRig, a: bool | str, b: bool | str) -> str:
    """
    Creates a new boolean and node.

    :param control_rig: control rig object.
    :param a: first condition.
    :param b: second condition.
    :return: condition result.
    """

    bool_node = create_node_from_path(
        control_rig, "/Script/RigVM.RigVMFunction_MathBoolAnd", execute_node=True
    )
    pins.connect_to_pin_1d(control_rig, a, f"{bool_node}.A")
    pins.connect_to_pin_1d(control_rig, b, f"{bool_node}.B")

    return f"{bool_node}.Result"


def create_bool_not_node(control_rig: ControlRig, value: bool | str) -> str:
    """
    Creates a new boolean not node.

    :param control_rig: control rig object.
    :param value: condition to negate.
    :return: negated condition.
    """

    bool_node = create_node_from_path(
        control_rig, "/Script/RigVM.RigVMFunction_MathBoolNot", execute_node=True
    )
    pins.connect_to_pin_1d(control_rig, value, f"{bool_node}.Value")

    return f"{bool_node}.Result"


def create_has_metadata_node(
    control_rig: ControlRig,
    item: unreal.RigElementKey | str,
    name: str,
    pin_type: pins.PinType = pins.PinType.Double,
) -> str:
    """
    Creates a new has metadata node.

    :param control_rig: control rig object.
    :param item: item to retrieve metadata from.
    :param name: name of the metadata to check existence for.
    :param pin_type: type of the metadata pin.
    :return: found metadata pin path.
    """

    metadata_node = create_node_from_path(
        control_rig, "/Script/ControlRig.RigUnit_HasMetadata"
    )
    pins.connect_item(control_rig, item, "%s.Item" % metadata_node)
    pins.set_string(control_rig, name, "%s.Name" % metadata_node, connect_if_plug=True)
    pins.set_default_value(
        control_rig, pins.PIN_TYPES[pin_type.value], f"{metadata_node}.Type"
    )

    return f"{metadata_node}.Found"


def create_get_metadata_node(
    control_rig: ControlRig,
    item: str,
    name: str,
    default: str | None = None,
    pin_type: pins.PinType | None = None,
):
    """
    Creates a new get metadata node.

    :param control_rig: control rig object.
    :param item: item to get the metadata from.
    :param name: name of the metadata to get.
    :param default: default value to return if metadata is not found.
    :param pin_type: type of the metadata pin.
    :return: found metadata pin path.
    """

    node = add_template_node(
        control_rig,
        "DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)",
    )
    pins.connect_item(control_rig, item, f"{node}.Item")
    pins.set_string(control_rig, name, "{metadata_node}.Name", connect_if_plug=True)
    if pin_type is not None:
        pins.resolve_wildcard_pin(control_rig, f"{node}.Default", pin_type.value)
    pins.connect_to_pin_1d(control_rig, default, "{metadata_node}.Default")

    return f"{node}.Value"


def create_set_metadata_execute_node(
    control_rig: ControlRig,
    item: str,
    name: str,
    value: str | None = None,
    pin_type: pins.PinType = pins.PinType.Double,
):
    """
    Creates a new set metadata execute node.

    :param control_rig: control rig object.
    :param item: item to set the metadata for.
    :param name: name of the metadata to set.
    :param value: value to set the metadata to.
    :param pin_type: type of the metadata pin.
    :return:
    """

    node = add_template_node(
        control_rig,
        "DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)",
    )
    pins.connect_item(control_rig, item, f"{node}.Item")
    pins.set_string(control_rig, name, f"{node}.Name", connect_if_plug=True)
    pins.resolve_wildcard_pin(control_rig, f"{node}.Value", pin_type.value)
    pins.connect_to_pin_1d(control_rig, value, f"{node}.Value")
    add_to_execute(control_rig, node)

    return node


def create_array_at_node(
    control_rig: ControlRig,
    array: str,
    index: int,
    node_size: tuple[int | float] | None = None,
) -> str:
    """
    Creates a new array at node.

    :param control_rig: control rig object.
    :param array: array to get the item from.
    :param index: index of the item to get.
    :param node_size: size of the node to create.
    :return: name of the created node.
    """

    node_size = node_size or [300, 100]

    node = control_rig.latest_function_stack().vm_model.add_array_node_from_object_path(
        unreal.RigVMOpCode.ARRAY_GET_AT_INDEX,
        "FRigVMUnknownType",
        "/Script/RigVM.RigVMUnknownType",
        new_node_position(control_rig, node_size=node_size),
        "ArrayGetAtIndex",
        setup_undo_redo=False,
    )
    control_rig.record_node_for_comment_box(node, estimated_size=node_size)
    node_name = node_name_from_node(node)
    pins.connect_to_pin_1d(control_rig, array, f"{node_name}.Array")
    pins.connect_to_pin_1d(control_rig, index, f"{node_name}.Index")

    return f"{node_name}.Element"


def create_aray_add_node(
    control_rig: ControlRig,
    array: str,
    other_array: str,
    node_size: Sequence[int | float] | None = None,
) -> str:
    """
    Creates a new array add node.

    :param control_rig: control rig object.
    :param array: array pin path to connect.
    :param other_array: other array pin path to connect.
    :param node_size: size of the node to create.
    :return: name of the created node.
    """

    node_size = node_size or [300, 100]
    function_stack = control_rig.latest_function_stack()

    # noinspection PyTypeChecker
    node = function_stack.vm_model.add_template_node(
        "DISPATCH_RigVMDispatch_ArrayAppend(io Array,in Other)",
        new_node_position(control_rig, node_size=node_size),
        setup_undo_redo=False,
    )
    control_rig.record_node_for_comment_box(node, estimated_size=node_size)
    append_node_name = node_name_from_node(node)
    pins.connect_to_pin_1d(control_rig, array, f"{append_node_name}.Array")
    pins.connect_to_pin_1d(control_rig, other_array, f"{append_node_name}.Other")
    add_to_execute(control_rig, append_node_name)

    return append_node_name


def create_reset_array_node(
    control_rig: ControlRig, array: str, node_size: Sequence[int | float | None] = None
) -> str:
    """
    Creates a new reset array node.

    :param control_rig: control rig object.
    :param array: array pin path to connect.
    :param node_size: size of the node to create.
    :return: name of the created node.
    """

    node_size = node_size or [300, 100]
    function_stack = control_rig.latest_function_stack()
    # noinspection PyTypeChecker
    node = function_stack.vm_model.add_template_node(
        "DISPATCH_RigVMDispatch_ArrayReset(io Array)",
        new_node_position(control_rig, node_size=node_size),
        "DISPATCH_RigVMDispatch_ArrayReset",
        setup_undo_redo=False,
    )
    control_rig.record_node_for_comment_box(node, estimated_size=node_size)
    reset_node_name = node_name_from_node(node)
    pins.connect_to_pin_1d(control_rig, array, f"{reset_node_name}.Array")
    add_to_execute(control_rig, reset_node_name)

    return reset_node_name


def create_spline_from_positions_node(
    control_rig: ControlRig,
    positions: str,
    spline: bool = False,
    samples_per_segment: int | str = 16,
) -> str:
    """
    Creates a new spline from positions node.

    :param control_rig: control rig object.
    :param positions: positions to create the spline from.
    :param spline: whether to create a spline.
    :param samples_per_segment: samples per segment.
    :return: spline pin path.
    """

    node = create_node_from_path(
        control_rig,
        "/Script/ControlRigSpline.RigUnit_ControlRigSplineFromPoints",
        node_size=[300, 300],
    )
    pins.set_vector_array(control_rig, positions, f"{node}.Points")
    pins.connect_to_pin_1d(
        control_rig, samples_per_segment, f"{node}.SamplesPerSegment"
    )
    if spline:
        pins.set_default_value(control_rig, "BSpline", f"{node}.SplineMode")

    return f"{node}.Spline"


def create_fit_chain_to_spline_curve(
    control_rig: ControlRig, spline: str, items: str, stretched: bool | str = True
) -> str:
    """
    Creates a new fit chain to spline curve node.

    :param control_rig: control rig object.
    :param spline: spline pin path to connect.
    :param items: items pin path to connect.
    :param stretched: whether to stretch the chain.
    :return: name of the created node.
    """

    node = create_node_from_path(
        control_rig,
        "/Script/ControlRigSpline.RigUnit_FitChainToSplineCurveItemArray",
        node_size=[300, 600],
    )
    pins.set_item_array(control_rig, items, f"{node}.Items")
    pins.connect_to_pin_1d(control_rig, spline, "node.Spline")
    if stretched:
        pins.set_default_value(control_rig, "Stretched", f"{node}.Alignment")
    else:
        pins.set_default_value(control_rig, "Front", f"{node}.Alignment")
    add_to_execute(control_rig, node)

    return node


def create_draw_spline_node(
    control_rig: ControlRig,
    spline: str,
    thickness: float | str = 1.0,
    detail: int | str = 16,
    color: Sequence[int | float] | str | None = None,
):
    """
    Creates a new draw spline node.

    :param control_rig: control rig object.
    :param spline: spline pin path to connect.
    :param thickness: thickness of the spline.
    :param detail: detail of the spline.
    :param color: color of the spline.
    :return: name of the created node.
    """

    color = color or [1.0, 0.0, 0.0]

    node = create_node_from_path(
        control_rig,
        "/Script/ControlRigSpline.RigUnit_DrawControlRigSpline",
        node_size=[300, 300],
    )
    pins.connect_to_pin_1d(control_rig, spline, f"{node}.Spline")
    pins.connect_to_pin_1d(control_rig, thickness, f"{node}.Thickness")
    pins.connect_to_pin_vector(
        control_rig, color, f"{node}.Color", attrs=["R", "G", "B"]
    )
    pins.connect_to_pin_1d(control_rig, detail, "{node}.Detail")
    add_to_execute(control_rig, node)

    return node
