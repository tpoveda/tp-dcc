from __future__ import annotations

import typing
from abc import ABC
from typing import Any

from .signals import Signal
from .address import is_address, form_address, get_attribute

if typing.TYPE_CHECKING:
    from .component import Component


class Attribute(ABC):
    """
    Abstract class that represents an exposed attribute to a component.
    An option allows a component to change its behaviour based on the value of the
    attribute.
    """

    def __init__(
        self,
        name: str,
        value: Any,
        description: str = "",
        group: str = "",
        should_inherit: bool = False,
        should_pre_expose: bool = False,
        hidden: bool = False,
        component: Component | None = None,
    ):
        """
        :param name: name of the attribute.
        :param value: value of the attribute.
        :param description: description of the attribute.
        :param group: group name of the attribute.
        :param should_inherit: whether the attribute should be inherited by children.
        :param should_pre_expose: whether the attribute should be exposed before
            the component is built.
        :param hidden: whether the attribute should be hidden in the UI.
        :param component: component this attribute is attached to.
        """

        self._name = name
        self._value = value
        self._description = description
        self._group = group
        self._should_inherit = should_inherit
        self._should_pre_expose = should_pre_expose
        self._hidden = hidden
        self._component = component

        self._value_changed = Signal()

    @property
    def value_changed(self) -> Signal:
        """
        Getter that returns the value changed signal.

        :return: value changed signal.
        """

        return self._value_changed

    @property
    def name(self) -> str:
        """
        Getter that returns the name of the attribute.

        :return: name of the attribute.
        """

        return self._name

    @property
    def description(self) -> str:
        """
        Getter that returns the description of the attribute.

        :return: description of the attribute.
        """

        return self._description

    @property
    def group(self) -> str:
        """
        Getter that returns the group of the attribute.

        :return: group of the attribute.
        """

        return self._group

    @property
    def should_inherit(self) -> bool:
        """
        Getter that returns whether the attribute should be inherited by children.

        :return: whether the attribute should be inherited by children.
        """

        return self._should_inherit

    @property
    def should_pre_expose(self) -> bool:
        """
        Getter that returns whether the attribute should be exposed before the component
        is built.

        :return: whether the attribute should be exposed before the component is built.
        """

        return self._should_pre_expose

    @property
    def hidden(self) -> bool:
        """
        Getter that returns whether the attribute should be hidden in the UI.

        :return: whether the attribute should be hidden in the UI.
        """

        return self._hidden

    @property
    def component(self) -> Component:
        """
        Returns the component this attribute is attached to.

        :return: component this attribute is attached to.
        """

        return self._component

    def is_address(self) -> bool:
        """
        Returns whether the value of the option is an address.

        :return: True if the value is an address; False otherwise.
        """

        return is_address(self._value)

    def get(self, resolved: bool = True) -> Any:
        """
        Returns the resolved value of the option.

        :return: value of the option.
        """

        if resolved and self.is_address():
            return get_attribute(self._value, self.component.stack).get()

        return self._value

    def set(self, value: Any):
        """
        Sets the value of the attribute and emits the value changed signal.

        :param value: value to set.
        """

        self._value = value
        self.value_changed.emit()

    def serialize(self) -> dict:
        """
        Serializes the attribute.

        :return: serialized attribute.
        """

        return {
            "name": self.name,
            "value": self.get(),
            "description": self.description,
            "group": self.group,
            "should_inherit": self.should_inherit,
            "should_pre_expose": self.should_pre_expose,
            "hidden": self.hidden,
        }


class Option(Attribute):
    """
    Class that represents an exposed option to a component.
    An option allows a component to change its behaviour based on the value of the
    option.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def address(self) -> str:
        """
        Returns the address of the option.

        :return: address of the option.
        """

        return form_address(self, "option")


class Input(Attribute):
    """
    Class that represents an exposed input to a component.
    An input allows a component to receive data from other components.
    """

    def __init__(self, validate, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._validate = validate

    def requires_validation(self) -> bool:
        """
        Returns whether the input requires validation.

        :return: True if the input requires validation; False otherwise.
        """

        return self._validate

    def validate(self) -> bool:
        """
        Validates the input.

        :return: True if the input is valid; False otherwise.
        """

        return True if self.get(resolved=False) else False

    def address(self) -> str:
        """
        Returns the address of the input.

        :return: address of the input.
        """

        return form_address(self, "requirement")


class Output(Attribute):
    """
    Class that represents an exposed output to a component.
    An output allows a component to send data to other components.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def address(self) -> str:
        """
        Returns the address of the output.

        :return: address of the output.
        """

        return form_address(self, "output")
