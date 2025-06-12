from __future__ import annotations

import re
import typing

if typing.TYPE_CHECKING:
    from .stack import Stack
    from .attributes import Attribute

ADDRESS_REGEX = re.compile(r"(\[.*\].\[(option|requirement|output)].\[.*\])")


def get_label(address: str) -> str | None:
    """
    Returns the label part of the address string.

    :param address: address string to get the label from.
    :return: label part of the address string.
    """

    try:
        return address.split(".")[0][1:-1]
    except IndexError:
        return None


def get_category(address: str) -> str | None:
    """
    Returns the category (or type) part of the address string.

    :param address: address string to get the category from.
    :return: category part of the address string.
    """

    try:
        return address.split(".")[1][1:-1]
    except IndexError:
        return None


def get_attribute_name(address: str) -> str | None:
    """
    Returns the attribute name from the address string.

    :param address: address string to get the attribute name from.
    :return: attribute name.
    """

    try:
        return address.split(".")[2][1:-1]
    except IndexError:
        return None


def get_parts(address: str) -> tuple[str, str, str]:
    """
    Returns the label, category, and attribute name from the address string.

    :param address: address string to get the parts from.
    :return: label, category, and attribute name.
    """

    return get_label(address), get_category(address), get_attribute_name(address)


def is_address(address: str) -> bool:
    """
    Returns whether the given string is a valid address or not.

    :param address: address string to check.
    :return: whether the string is a valid address or not.
    """

    return True if isinstance(address, str) and ADDRESS_REGEX.search(address) else False


def form_address(attribute: Attribute, category: str) -> str:
    """
    Returns the address string for the given attribute and category.

    :param attribute: attribute to form the address for.
    :param category: category of the attribute.
    """

    return f"[{attribute.component.label}].[{category}].[{attribute.name}]"


def get_attribute(address: str, stack: Stack) -> Attribute:
    """
    Converts the given address to an actual attribute within the given stack.

    :param address: address to convert to an attribute.
    :param stack: stack to search for the attribute.
    :return: attribute object.
    """

    component_label, category, attribute_name = get_parts(address)

    component = _get_component_with_label(component_label, stack)

    if category == "option":
        return component.option(attribute_name)
    if category == "requirement":
        return component.requirement(attribute_name)
    if category == "output":
        return component.output(attribute_name)

    return None


def _get_component_with_label(label: str, stack: Stack) -> str | None:
    """
    Internal function that loop through the components of a stack looking for the
    first component with a matching label.

    :param label: label to search for.
    :param stack: stack to search in.
    :return: component with the matching label.
    """

    found_component: str | None = None
    for component in stack.components():
        if component.label() == label:
            found_component = component
            break

    return found_component
