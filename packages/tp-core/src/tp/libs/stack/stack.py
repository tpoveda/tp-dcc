from __future__ import annotations

from typing import Type

from .signals import Signal
from .component import Component


class Stack:
    """
    Class that represents an stack object which interacts and is composed by components.
    """

    def __init__(
        self,
        label: str = "",
        component_paths: list[str] | None = None,
        component_base_class: Type[Component] = Component,
    ):
        """
        Class constructor.

        :param label: human-readable label for the stack.
        :param component_paths: list of paths to components that should be added to
            the components library when the stack is instanced.
        :param component_base_class: base class for components that allows for any
            subclassing of the Stack object to specify their own base class for
            components.
        """

        super().__init__()

        self._label = label
        self._component_paths = component_paths or []
        self._component_base_class = component_base_class
        self._components: dict = {}
        self._build_order: list = []

        self._component_added = Signal()
        self._component_removed = Signal()
        self._build_order_changed = Signal()
        self._changed = Signal()
        self._build_started = Signal()
        self._build_completed = Signal()

    @property
    def component_added(self) -> Signal:
        """
        Returns the signal that is emitted when a component is added to the stack.

        :return: Signal
        """

        return self._component_added

    @property
    def component_removed(self) -> Signal:
        """
        Returns the signal that is emitted when a component is removed from the stack.

        :return: Signal
        """

        return self._component_removed

    @property
    def build_order_changed(self) -> Signal:
        """
        Returns the signal that is emitted when the build order of the stack changes.

        :return: Signal
        """

        return self._build_order_changed

    @property
    def changed(self) -> Signal:
        """
        Returns the signal that is emitted when the stack changes.

        :return: Signal
        """

        return self._changed

    @property
    def build_started(self) -> Signal:
        """
        Returns the signal that is emitted when the stack build starts.

        :return: Signal
        """

        return self._build_started
