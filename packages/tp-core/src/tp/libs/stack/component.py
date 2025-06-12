from __future__ import annotations

import uuid
import json
import typing
import traceback
from typing import Any
from abc import ABC, abstractmethod

from .status import Status
from .signals import Signal

if typing.TYPE_CHECKING:
    from .stack import Stack
    from Qt.QtWidgets import QWidget
    from .attributes import Option, Input, Output


class Component(ABC):
    """
    Class that represents a single item within the stack. A component is composed by:
        - Options
        - Inputs

    All components must define:
        - Unique identifier (id) in order to avoid conflicts with different components.
        - Version number (version) to keep track of the component's version. If multiple
            components with the same ID are found, the one with the highest version
            will be used.
    """

    # Unique identifier of the component.
    id: str = ""

    # Version number of the component.
    # This allows to have multiple versions of the same component.
    # The one with the highest version is the one that will be used.
    version: int = 1

    # Optional absolute path to the icon file to use for this component.
    icon: str = ""

    def __init__(self, label: str, stack: Stack, unique_id: str | None = None):
        """
        :param label: Label of the component.
        :param stack: Stack that owns this component.
        :param unique_id: Unique identifier of the component.
        """

        super().__init__()

        self._label = label
        self._stack = stack
        self._unique_id = unique_id or str(uuid.uuid4())
        self._options: list[Option] = []
        self._inputs: list[Input] = []
        self._outputs: list[Output] = []
        self._status: Status = Status.NotExecuted
        self._forced_version: int | None = None
        self._enabled: bool = True

        self._build_started = Signal()
        self._build_completed = Signal()
        self._changed = Signal()

    @abstractmethod
    def run(self) -> bool:
        """
        Implements all the logic that should run during the execution process.

        This function must be implemented by subclasses.

        :return: True if the component was executed successfully; False otherwise.
        """

        raise NotImplementedError("run function must be implemented!")

    # noinspection PyMethodMayBeStatic
    def is_valid(self) -> bool:
        """
        Returns whether the component is valid or not.

        :return: True if the component is valid; False otherwise.
        """

        return True

    # noinspection PyMethodMayBeStatic
    def option_widget(self, option_name: str) -> QWidget:
        """
        Returns a specific (or custom) widget to represent the given option in the UI.

        :param option_name: Name of the option to return the widget for.
        :return: QWidget that represents the option in the UI.
        """

        return None

    # noinspection PyMethodMayBeStatic
    def input_widget(self, input_name: str) -> QWidget:
        """
        Returns a specific (or custom) widget to represent the given input in the UI.

        :param input_name: Name of the input to return the widget for.
        :return: QWidget that represents the input in the UI.
        """

        return None

    def on_enter_stack(self):
        """
        Function that is called when the component enters the stack.
        """

        pass

    def removed_from_stack(self):
        """
        Function that is called when the component is removed from the stack.
        """

        pass

    def help(self):
        """
        Help function that should display a help dialog with the component
        documentation or to open a webpage showing the component documentation.
        """

        pass

    @property
    def build_started(self) -> Signal:
        """
        Getter that returns the signal that is emitted when the build process starts.

        :return: Signal that is emitted when the build process starts.
        """

        return self._build_started

    @property
    def build_completed(self) -> Signal:
        """
        Getter that returns the signal that is emitted when the build process completes.

        :return: Signal that is emitted when the build process completes.
        """

        return self._build_completed

    @property
    def changed(self) -> Signal:
        """
        Getter that returns the signal that is emitted when the component changes.

        :return: Signal that is emitted when the component changes.
        """

        return self._changed

    @property
    def label(self) -> str:
        """
        Getter that returns the label of the component.
        The label is the name of the component that is displayed usually in the UI and
        is more human-readable.

        :return: Label of the component.
        """

        return self._label

    @label.setter
    def label(self, value: str):
        """
        Setter that sets the label of the component.
        The label is the name of the component that is displayed usually in the UI and
        is more human-readable.

        :param value: Label of the component.
        """

        self._label = value
        self.changed.emit()

    @property
    def suggested_label(self) -> str:
        """
        Getter that returns the suggested label of the component.
        The suggested label is the label that is used when the component is created
        and is the same as the component's ID.

        :return: Suggested Label of the component.
        """

        return self.id

    @property
    def stack(self) -> Stack:
        """
        Getter that returns the stack that owns this component.

        :return: Stack that owns this component.
        """

        return self._stack

    @property
    def unique_id(self) -> str:
        """
        Getter that returns the unique identifier of the component.
        All component instances have a unique identifier that allows the build process
        and the stack to keep track of all the components instances.

        :return: Unique identifier of the component.
        """

        return self._unique_id

    @property
    def forced_version(self) -> int | None:
        """
        Getter that returns the version of the component that is expected to be used.

        :return: Forced version of the component.
        """

        return self._forced_version

    @forced_version.setter
    def forced_version(self, value: int | None):
        """
        Setter that sets the version of the component that is expected to be used.
        This allows to specify that this component should always use a specific version.

        Setting this to None will ensure this component will always use the latest
        available version.

        :param value: Forced version of the component.
        """

        self._forced_version = value

    @property
    def is_enabled(self) -> bool:
        """
        Getter that returns whether the component is enabled or not.
        Any component that is not enabled will not be executed.

        :return: True if the component is enabled; False otherwise.
        """

        return self._enabled

    @is_enabled.setter
    def is_enabled(self, value: bool):
        """
        Setter that sets whether the component is enabled or not.
        Any component that is not enabled will not be executed.

        :param value: True if the component is enabled; False otherwise.
        """

        self._enabled = value
        self.changed.emit()

    @property
    def status(self) -> Status:
        """
        Getter that returns the current status of the component.

        :return: Current status of the component.
        """

        return Status.Disabled if not self.is_enabled else self._status

    @status.setter
    def status(self, value: Status):
        """
        Setter that sets the current status of the component.

        :param value: Current status of the component.
        """

        self._status = value

    @property
    def parent(self) -> Component | None:
        """
        Returns the parent of the component.

        :return: Parent of the component.
        """

        return self.stack.get_parent(self)

    def declare_option(
        self,
        name: str,
        value: Any,
        description: str = "",
        group: str | None = None,
        should_inherit: bool = False,
        should_pre_expose: bool = False,
        hidden: bool = False,
    ):
        """
        Adds a new option to the component.

        An option is a value that can be set by the user and is used as a configuration
        for the component that can be accessed during the execution process.

        :param name: Name of the option.
        :param value: Value of the option.
        :param description: Description of the option to be presented to the user.
        :param group: Group of the option. If given, this option will be grouped together
            with other options that have the same group within the UI.
        :param should_inherit: Whether the option should inherit the value from the parent
            when it's initialized.
        :param should_pre_expose: Whether the option should be exposed.
        :param hidden: Whether the option should be hidden or not.
        """

        option = Option(
            name=name,
            value=value,
            description=description,
            group=group,
            should_inherit=should_inherit,
            should_pre_expose=should_pre_expose,
            hidden=hidden,
            component=self,
        )
        self._options.append(option)
        option.value_changed.connect(self.changed.emit)

    def declare_input(
        self,
        name: str,
        value: Any = None,
        description: str = "",
        validate: bool = True,
        group: str | None = None,
        should_inherit: bool = False,
        should_pre_expose: bool = False,
        hidden: bool = False,
    ):
        """
        Adds a new requirement input to the component.

        A requirement can be set by the user and is used as an input for the component
        that can be accessed during the execution process.

        :param name: Name of the requirement.
        :param value: Value of the requirement.
        :param description: Description of the requirement to be presented to the user.
        :param validate: Whether the requirement should be validated prior its
            component  being executed.
        :param group: Group of the requirement. If given, this requirement will be
            grouped together with other requirements that have the same group within
            the UI.
        :param should_inherit: Whether the requirement should inherit the value from
            the parent when it's initialized.
        :param should_pre_expose: Whether the requirement should be exposed.
        :param hidden: Whether the requirement should be hidden or not.
        :return:
        """

        input_ = Input(
            name=name,
            value=value,
            validate=validate,
            description=description,
            group=group,
            should_inherit=should_inherit,
            should_pre_expose=should_pre_expose,
            hidden=hidden,
            component=self,
        )
        self._inputs.append(input_)
        input_.value_changed.connect(self.changed.emit)

    def declare_output(self, name: str, description: str):
        """
        Adds a new output to the component.

        An output is a value that is guaranteed to be set by the component during the
        execution process and can be accessed by other components.

        This allows components to dynamically resolve values from other components
        rather than have them explicitly set.

        :param name: Name of the output.
        :param description: Description of the output to be presented to the user.
        """

        output = Output(
            name=name,
            description=description,
            component=self,
        )
        self._outputs.append(output)

    def options(self) -> list[Option]:
        """
        Returns all the options of the component.

        :return: List of all the options of the component.
        """

        return self._options

    def inputs(self) -> list[Input]:
        """
        Returns all the inputs of the component.

        :return: List of all the inputs of the component.
        """

        return self._inputs

    def outputs(self) -> list[Output]:
        """
        Returns all the outputs of the component.

        :return: List of all the outputs of the component.
        """

        return self._outputs

    def option(self, name: str) -> Option | None:
        """
        Returns the option with the given name.

        :param name: Name of the option to return.
        :return: Option with the given name or None if no option with that name is found.
        """

        found_option: Option | None = None
        for option in self._options:
            if option.name == name:
                found_option = option
                break

        return found_option

    def input(self, name: str) -> Input | None:
        """
        Returns the input with the given name.

        :param name: Name of the input to return.
        :return: Input with the given name or None if no input with that name is found.
        """

        found_input: Input | None = None
        for input_ in self._inputs:
            if input_.name == name:
                found_input = input_
                break

        return found_input

    def output(self, name: str) -> Output | None:
        """
        Returns the output with the given name.

        :param name: Name of the output to return.
        :return: Output with the given name or None if no output with that name is found.
        """

        found_output: Output | None = None
        for output in self._outputs:
            if output.name == name:
                found_output = output
                break

        return found_output

    def copy(self, other_component: Component):
        """
        Copies the data from the given component to this component.

        :param other_component: Component to copy the data from.
        """

        for input_ in self.inputs():
            input_to_copy = other_component.input(input_.name)
            if input_to_copy:
                self.input(input_.name).set(
                    input_to_copy.get(resolved=False),
                )

        for option in self.options():
            option_to_copy = other_component.option(option.name)
            if option_to_copy:
                self.option(option.name).set(
                    option_to_copy.get(resolved=False),
                )

        self.label = other_component.label
        self.is_enabled = other_component.is_enabled

    def duplicate(self):
        """
        Creates a duplicate of the component in the stack.
        Children components are not duplicated.
        """

        new_component = self.stack.add_component(
            component_type=self.id,
            label=self.label,
        )
        new_component.copy(self)

        self.stack.set_build_position(new_component, parent=self.parent)

        new_component.changed.emit()

    def serialize(self) -> dict:
        """
        Serializes the component to a dictionary.

        :return: Dictionary that represents the serialized component.
        """

        return {
            "component_type": self.id,
            "forced_version": self.forced_version,
            "uuid": self.unique_id,
            "label": self.label,
            "enabled": self.is_enabled,
            "inputs": [input_.serialize() for input_ in self.inputs()],
            "options": [option.serialize() for option in self.options()],
        }

    def save(self, file_path: str):
        """
        Saves the component settings to the given file path.

        :param file_path: File path to save the component settings to.
        """

        data = self.serialize()
        with open(file_path, "w") as f:
            json.dump(
                data,
                f,
                indent=4,
                sort_keys=True,
            )

    def load(self, file_path: str):
        """
        Loads the component settings from the given file path.

        :param file_path: File path to load the component settings from.
        """

        with open(file_path, "r") as f:
            data = json.load(f)

        for input_data in data.get("inputs", []):
            input_name = input_data["name"]
            input_ = self.input(input_name)
            if input_:
                input_.set(input_data["value"])

        for option_data in data.get("options", []):
            option_name = option_data["name"]
            option = self.option(option_name)
            if option:
                option.set(option_data["value"])

        self.changed.emit()

    def documentation(self) -> str:
        """
        Returns the documentation of the component.

        :return: Documentation of the component.
        """

        if not self.__doc__:
            return ""

        lines: list[str] = []
        for line in self.__doc__.split("\n"):
            line = line.strip()
            if not line:
                line = "\n"
            lines.append(line)
        return " ".join(lines)

    def format_print(self):
        """
        Prints a nicely formatted string representation of the component.
        """

        print(f"Component Type : {self.id} (Version : {self.version})")
        print(f"    Identifier : {self.unique_id}")
        print("    Options    :")
        option_len = max([len(option.name) for option in self.options()] or [0])
        for option in self.options():
            print(
                f"        {option.name.ljust(option_len + 2, ' ')} : {self.option(option.name).get()}"
            )
        print("    Inputs :")
        inputs_len = max([len(input_.name) for input_ in self.inputs()] or [0])
        for input_ in self.inputs():
            print(
                f"        {input_.name.ljust(inputs_len + 2, ' ')} : {self.input(input_.name).get()}"
            )

    def print_outputs(self):
        """
        Prints a nicely formatted string representation of the component outputs.
        """

        print("    Outputs :")
        output_len = max([len(output.name) for output in self.outputs()] or [0])
        for output in self.outputs():
            print(
                f"        {output.name.ljust(output_len + 2, ' ')} : {self.output(output.name).get()}"
            )

    def _run(self) -> bool:
        """
        Function used specifically by the Stack class to instigate your implement
        function whilst wrapped in the signal and logging mechanisms.
        """

        self.build_started.emit()

        result = True

        try:
            self.run()
            self.status = Status.Success
        except Exception as err:
            self.status = Status.Failed
            print(traceback.print_exc(), err)
            result = False

        self.build_completed.emit()

        return result
