from __future__ import annotations

import enum
import typing
from typing import Sequence

import unreal

from . import consts

if typing.TYPE_CHECKING:
    from .controllers import ControlRig


class PinType(enum.Enum):
    """
    Enum class defining the different types of pins.
    """

    Integer = 0
    Double = 1
    Vector = 2
    Bool = 3
    Spline = 4
    Item = 5
    Transform = 6


PIN_TYPES = {
    PinType.Integer.value: "int32",
    PinType.Double.value: "double",
    PinType.Vector.value: "FVector",
    PinType.Bool.value: "bool",
    PinType.Item.value: "FRigElementKey",
    PinType.Transform.value: "FTransform",
}


def get_parent_pin(pin_path: str) -> str:
    """
    Returns the parent pin of the given pin path.

    :param pin_path: pin path to get parent pin from.
    :return: parent pin path of the given pin path.
    """

    return pin_path[: pin_path.rfind(".")]


def expand_pin(control_rig: ControlRig, pin_path: str, expand: bool = True):
    """
    Expands or collapses the given pin path.

    :param control_rig: control rig to expand or collapse pin.
    :param pin_path: pin path to expand or collapse.
    :param expand: whether to expand or collapse the pin path.
    """

    control_rig.latest_function_stack().vm_model.set_pin_expansion(
        pin_path, expand, setup_undo_redo=False
    )


def expand_parent_pins(control_rig: ControlRig, pin_path: str, expand: bool = True):
    """
    Expands the parent pins of the given pin path.

    :param control_rig: control rig to expand parent pins.
    :param pin_path: pin path to expand parent pins.
    :param expand: whether to expand or collapse the parent pins.
    """

    if pin_path.count(".") < 2:
        return

    parent_pin = get_parent_pin(pin_path)
    expand_pin(control_rig, parent_pin, expand=expand)
    if parent_pin.count(".") >= 2:
        parent_pin = get_parent_pin(parent_pin)
        expand_pin(control_rig, parent_pin, expand=expand)


def connect_to_pin_1d(
    control_rig: ControlRig,
    from_element: str | bool | float | int,
    target_pin_path: str,
):
    """
    Connects a 1D element to a target pin path.

    :param control_rig: control rig to connect element to pin.
    :param from_element: element to connect to pin.
    :param target_pin_path: target pin path to connect element to.
    """

    if from_element is None:
        return

    if isinstance(from_element, str):
        if from_element.upper() == "NONE":
            control_rig.latest_function_stack().vm_model.set_pin_default_value(
                target_pin_path, from_element, setup_undo_redo=False
            )
        else:
            control_rig.latest_function_stack().vm_model.add_link(
                from_element, target_pin_path, setup_undo_redo=False
            )
    elif isinstance(from_element, bool):
        control_rig.latest_function_stack().vm_model.set_pin_default_value(
            target_pin_path,
            "true" if from_element else "false",
            False,
            setup_undo_redo=False,
        )
    elif isinstance(from_element, float):
        control_rig.latest_function_stack().vm_model.set_pin_default_value(
            target_pin_path, "%0.6f" % from_element, True, setup_undo_redo=False
        )
    elif isinstance(from_element, int):
        control_rig.latest_function_stack().vm_model.set_pin_default_value(
            target_pin_path, "%d" % from_element, True, setup_undo_redo=False
        )
    else:
        raise Exception(
            f"Invalid type for from_element: {from_element} ({type(from_element)})"
        )

    if isinstance(from_element, str):
        expand_parent_pins(control_rig, from_element)


def connect_to_pin_vector(
    control_rig: ControlRig,
    element: str | int | unreal.RigElementKey | tuple[unreal.RigElementKey, float],
    vector_pin: str,
    attrs: Sequence[str] | None = None,
    auto_expand: bool = True,
):
    """
    Connects an element to a vector pin.

    :param control_rig: control rig to connect element to pin.
    :param element: element to connect to pin.
    :param vector_pin: target vector pin to connect element to.
    :param attrs: optional list of vector attributes to connect element to.
    :param auto_expand: whether to auto expand the parent pins.
    """
    if element is None:
        return

    if isinstance(element, str):
        connect_to_pin_1d(control_rig, element, vector_pin)
        expand_parent_pins(control_rig, element)
    elif isinstance(element, (list, tuple)):
        for sub_element, attr in zip(element, attrs):
            connect_to_pin_1d(control_rig, sub_element, f"{vector_pin}.{attr}")
        if auto_expand:
            expand_pin(control_rig, vector_pin)
    else:
        # noinspection PyTypeChecker
        control_rig.latest_function_stack().vm_model.add_link(
            element, vector_pin, setup_undo_redo=False
        )


def set_string(
    control_rig: ControlRig,
    string_value: str | unreal.Name,
    pin_path: str,
    connect_if_plug: bool = True,
):
    """
    Sets a string value to a pin path.

    :param control_rig: control rig to set string value to pin path.
    :param string_value: value to set to pin path.
    :param pin_path: pin path to set value to.
    :param connect_if_plug: whether to connect to pin if it is a plug.
    """

    string_value = str(string_value)
    if connect_if_plug and "." in string_value:
        connect_to_pin_1d(control_rig, string_value, pin_path)
    else:
        control_rig.latest_function_stack().vm_model.set_pin_default_value(
            pin_path, string_value, setup_undo_redo=False
        )


def set_string_array(
    control_rig: ControlRig, strings: str | Sequence[str], pin_path: str
):
    """
    Sets a string array to a pin path.

    :param control_rig: control rig to set string array to pin path.
    :param strings: value to set to pin path.
    :param pin_path: pin path to set value to.
    """

    if isinstance(strings, str):
        connect_to_pin_1d(control_rig, strings, pin_path)
    else:
        _set_string = "(%s)" % ",".join(
            ['"%s"' % str(fV).replace(".", "") for fV in strings]
        )
        control_rig.latest_function_stack().vm_model.set_pin_default_value(
            pin_path, _set_string, setup_undo_redo=False
        )
        for i, string in enumerate(strings):
            if "." in str(string):
                connect_to_pin_1d(control_rig, string, f"{pin_path}.{i}")
        expand_pin(control_rig, pin_path)


def set_vector_array(
    control_rig: ControlRig, vectors: str | Sequence[str], vector_pin_path: str
):
    """
    Sets a vector array to a pin path.

    :param control_rig: control rig to set vector array to pin path.
    :param vectors: value to set to pin path.
    :param vector_pin_path: pin path to set value to.
    """

    if isinstance(vectors, str):
        connect_to_pin_1d(control_rig, vectors, vector_pin_path)
    elif isinstance(vectors, (list, tuple)):
        # noinspection PyStringFormat
        vectors_str = "(%s)" % ",".join(
            [
                "(X=%0.10f,Y=%0.10f,Z=%0.10f)"
                % ((0, 0, 0) if isinstance(fV, str) else (fV[0], fV[1], fV[2]))
                for fV in vectors
            ]
        )
        control_rig.latest_function_stack().vm_model.set_pin_default_value(
            vector_pin_path, vectors_str, setup_undo_redo=False
        )  # '(5,4,3,2)'
        for i, fV in enumerate(vectors):
            if isinstance(fV, str):
                connect_to_pin_vector(control_rig, fV, f"{vector_pin_path}.{i}")


def set_item_array(
    control_rig: ControlRig, elements: str | Sequence[str], items_pin_path: str
):
    """
    Sets an item array to a pin path.

    :param control_rig: control rig to set item array to pin path.
    :param elements: elements to set to pin path.
    :param items_pin_path: pin path to set value to.
    """

    if isinstance(elements, str):
        connect_to_pin_1d(control_rig, elements, items_pin_path)
    else:
        strings_str = []
        for element in elements:
            if isinstance(element, unreal.RigElementKey):
                strings_str.append(
                    '(Type=%s,Name="%s")'
                    % (
                        consts.ELEMENT_TYPE_STRINGS[element.type],
                        "None" if "." in str(element.name) else element.name,
                    )
                )
            else:
                strings_str.append('(Type="Bone",Name="None")')

        strings_str = "(%s)" % ",".join(strings_str)
        set_string(control_rig, strings_str, items_pin_path)

        for i, element in enumerate(elements):
            if isinstance(element, unreal.RigElementKey):
                if "." in str(element.name):
                    connect_to_pin_1d(
                        control_rig, str(element.name), f"{items_pin_path}.{i}.Name"
                    )
            else:
                connect_to_pin_1d(control_rig, element, f"{items_pin_path}.{i}")


def connect_item(
    control_rig: ControlRig, element_or_string: unreal.RigElementKey | str, item_pin
):
    """
    Connects a rig element or string to an item pin.

    :param control_rig: Control rig to connect element to pin.
    :param element_or_string: Rig element or string to connect.
    :param item_pin: Item pin to connect to.
    """

    if isinstance(element_or_string, str):
        connect_to_pin_1d(control_rig, element_or_string, item_pin)
    else:
        set_string(
            control_rig,
            consts.ELEMENT_TYPE_STRINGS[element_or_string.type],
            f"{item_pin}.Type",
        )
        if "." in str(element_or_string.name):
            connect_to_pin_1d(
                control_rig, str(element_or_string.name), f"{item_pin}.Name"
            )
        else:
            set_string(control_rig, str(element_or_string.name), f"{item_pin}.Name")

        expand_pin(control_rig, item_pin)


def set_default_value(control_rig: ControlRig, value: str, pin_path: str):
    """
    Set default value to pin path.

    :param control_rig: control rig to set default value to pin path.
    :param value: value to set to pin path.
    :param pin_path: pin path to set value to.
    """

    control_rig.latest_function_stack().vm_model.set_pin_default_value(
        pin_path, value, setup_undo_redo=False
    )


def connect_to_pin_constraint_parent(
    control_rig: ControlRig,
    element: str | unreal.RigElementKey | tuple[unreal.RigElementKey, float],
    constraint_parents_pin: str,
):
    """
    Connects an element to a constraint parent array pin.

    :param control_rig: control rig to connect element to pin.
    :param element: element to connect to pin.
    :param constraint_parents_pin: constraint parents pin to connect element to.
    :raises Exception: If element is a list or tuple and does not have 2 elements.
    :raises Exception: If element is not a valid type.
    """

    if isinstance(element, str):
        connect_to_pin_1d(control_rig, element, constraint_parents_pin)
    elif isinstance(element, unreal.RigElementKey):
        connect_item(control_rig, element, f"{constraint_parents_pin}.Item")
        connect_to_pin_1d(control_rig, 1.0, f"{constraint_parents_pin}.Weight")
    elif isinstance(element, (list, tuple)):
        if len(element) != 2:
            raise Exception(f"{element} nees to be in the form of (Item, Weight)")
        connect_item(control_rig, element[0], f"{constraint_parents_pin}.Item")
        connect_to_pin_1d(control_rig, element[1], f"{constraint_parents_pin}.Weight")
    else:
        raise Exception(f"Invalid type for element: {element} ({type(element)})")


def connect_to_pin_constraint_parent_array(
    control_rig: ControlRig,
    element_array: str | Sequence[str | bool | float | int],
    constraint_parents_array_pin: str,
):
    """
    Connects an element to a constraint parent array pin.

    :param control_rig: control rig to connect element to pin.
    :param element_array: elements to connect to pin.
    :param constraint_parents_array_pin: constraint parents array pin to connect element to.
    """

    if isinstance(element_array, str):
        connect_to_pin_1d(control_rig, element_array, constraint_parents_array_pin)
    elif isinstance(element_array, (list, tuple)):
        if element_array:
            array_string = "(%s)" % ",".join(
                ['(Item=(Type=Bone,Name="None"),Weight=0.0)'] * len(element_array)
            )
            control_rig.latest_function_stack().vm_model.set_pin_default_value(
                constraint_parents_array_pin, array_string, setup_undo_redo=False
            )
            for i, element in enumerate(element_array):
                connect_to_pin_constraint_parent(
                    control_rig, element, f"{constraint_parents_array_pin}.{i}"
                )


def connect_to_pin_transform(
    control_rig: ControlRig,
    from_element: str | Sequence[str, bool | int | float],
    transform_pin_path: str,
    auto_expanded: bool = True,
):
    """
    Connects an element to a transform pin.

    :param control_rig: control rig to connect element to pin.
    :param from_element: elements to connect to transform pin.
    :param transform_pin_path: transform pin path to connect element to.
    :param auto_expanded: whether to auto expand the parent pins.
    """

    if not from_element:
        return

    if isinstance(from_element, (list, tuple)):
        connect_to_pin_vector(
            control_rig, from_element[0], f"{transform_pin_path}.Translation"
        )
        connect_to_pin_1d(
            control_rig, from_element[1], f"{transform_pin_path}.Rotation"
        )
        connect_to_pin_vector(
            control_rig, from_element[2], f"{transform_pin_path}.Scale3D"
        )
        if auto_expanded:
            expand_pin(control_rig, transform_pin_path)
    else:
        control_rig.latest_function_stack().vm_model.add_link(
            from_element, transform_pin_path, setup_undo_redo=False
        )


def resolve_wildcard_pin(control_rig: ControlRig, pin_path: str, pin_type: str):
    """
    Resolves a wildcard pin.

    :param control_rig: control rig to resolve wildcard pin.
    :param pin_path: pin path to resolve.
    :param pin_type: pin type to resolve.
    """

    if isinstance(pin_type, int):
        pin_type = PIN_TYPES[pin_type]

    cpp_type = consts.CPP_TYPE_TO_OBJECT_PATH.get(pin_type, "None")
    control_rig.latest_function_stack().vm_model.resolve_wild_card_pin(
        pin_path, pin_type, cpp_type, setup_undo_redo=False
    )
