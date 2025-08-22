from __future__ import annotations

from typing import Any
from enum import IntEnum
from collections import defaultdict
from dataclasses import dataclass

from Qt.QtCore import Qt
from Qt.QtGui import QKeySequence

from tp.libs.python.decorators import Singleton


class InputActionType(IntEnum):
    """Enum to define the type of input action."""

    Mouse = 1
    Keyboard = 2


@dataclass
class InputActionData:
    """Data class to hold input action data."""

    mouse: Qt.MouseButton
    key: Qt.Key | None
    modifiers: Qt.KeyboardModifier | Qt.KeyboardModifiers


class InputAction:
    """Class to represent an input action, which can be a mouse or keyboard
    action.
    """

    def __init__(
        self,
        name: str = "defaultName",
        action_type: InputActionType = InputActionType.Keyboard,
        group: str = "default",
        mouse: Qt.MouseButton = Qt.NoButton,
        key: Qt.Key | None = None,
        modifiers: Qt.KeyboardModifier | Qt.KeyboardModifiers = Qt.NoModifier,
    ):
        super().__init__()

        self._action_type = action_type
        self._name = name
        self._group = group
        self._data = InputActionData(
            mouse=mouse,
            key=key,
            modifiers=modifiers,
        )

    def __str__(self) -> str:
        """Return a string representation of the action."""

        parts: list[str] = []

        # Modifiers.
        if self.modifiers and int(self.modifiers) != int(Qt.NoModifier):
            parts.append(QKeySequence(int(self.modifiers)).toString())

        # Mouse or Keyboard specifics.
        if self.action_type == InputActionType.Mouse:
            parts.append(self.mouse_button.name)
        elif self.action_type == InputActionType.Keyboard and self.key is not None:
            parts.append(QKeySequence(int(self.key)).toString())

        return " ".join([p for p in parts if p])

    def __eq__(self, other: object) -> bool:
        """Check the equality of two `InputAction` instances."""

        if not isinstance(other, InputAction):
            return False

        return all(
            [
                self.mouse_button == other.mouse_button,
                self.key == other.key,
                self.modifiers == other.modifiers,
            ]
        )

    def __ne__(self, other: object) -> bool:
        """Check the inequality of two `InputAction` instances."""

        return not self.__eq__(other)

    @property
    def name(self) -> str:
        """The name of the action."""

        return self._name

    @property
    def group(self) -> str:
        """The group this action belongs to."""

        return self._group

    @property
    def action_type(self) -> InputActionType:
        """The type of action (mouse or keyboard)."""

        return self._action_type

    @property
    def data(self) -> InputActionData:
        """The data associated with the action."""

        return self._data

    @property
    def mouse_button(self) -> Qt.MouseButton:
        """The mouse button associated with the action."""

        return self._data.mouse

    @mouse_button.setter
    def mouse_button(self, value: Qt.MouseButton):
        """Set the mouse button for the action."""

        self._data.mouse = value

    @property
    def key(self) -> Qt.Key | None:
        """The key associated with the action."""

        return self._data.key

    @key.setter
    def key(self, value: Qt.Key | None):
        """Set the key for the action."""

        self._data.key = value

    @property
    def modifiers(self) -> Qt.KeyboardModifier | Qt.KeyboardModifiers:
        """The keyboard modifiers associated with the action."""

        return self._data.modifiers

    @modifiers.setter
    def modifiers(self, value: Qt.KeyboardModifier | Qt.KeyboardModifiers):
        """Set the keyboard modifiers for the action."""

        self._data.modifiers = value

    # === Serialization ===

    @classmethod
    def from_json_data(cls, data: dict[str, Any]) -> InputAction:
        """Create an InputAction from a JSON data dictionary.

        Args:
            data: The JSON data dictionary containing action properties.

        Returns:
            InputAction: An instance of InputAction created from the data.
        """

        try:
            modifiers = Qt.NoModifier
            for mod in data.get("modifiers", []):
                modifiers = modifiers | Qt.KeyboardModifier(int(mod))

            return cls(
                name=data["name"],
                action_type=InputActionType(data["action_type"]),
                group=data["group"],
                mouse=Qt.MouseButton(int(data["mouse"])),
                key=Qt.Key(int(data["key"])) if data.get("key") is not None else None,
                modifiers=modifiers,
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Invalid data for InputAction: {data}") from e

    def to_json(self) -> dict[str, Any]:
        """Convert the InputAction to a JSON serializable dictionary.

        Returns:
            A dictionary representation of the InputAction.
        """

        modifiers: list[int] = []
        mods = self.modifiers
        if mods & Qt.ShiftModifier:
            modifiers.append(int(Qt.ShiftModifier))
        if mods & Qt.ControlModifier:
            modifiers.append(int(Qt.ControlModifier))
        if mods & Qt.AltModifier:
            modifiers.append(int(Qt.AltModifier))
        if mods & Qt.MetaModifier:
            modifiers.append(int(Qt.MetaModifier))
        if mods & Qt.KeypadModifier:
            modifiers.append(int(Qt.KeypadModifier))
        if mods & Qt.GroupSwitchModifier:
            modifiers.append(int(Qt.GroupSwitchModifier))

        return {
            "name": self.name,
            "action_type": self.action_type.value,
            "group": self.group,
            "mouse": int(self.mouse_button),
            "key": int(self.key) if self.key is not None else None,
            "modifiers": modifiers,
        }


class InputManager(metaclass=Singleton):
    """Singleton class to manage input actions."""

    def __init__(self):
        super().__init__()

        self._actions: defaultdict[str, list[InputAction]] = defaultdict(list)

    @property
    def actions(self) -> dict[str, list[InputAction]]:
        """All registered input actions."""

        return self._actions

    def __getitem__(self, key: str) -> list[InputAction]:
        """Get the input actions by name.

        Args:
            key: The name of the input action.

        Returns:
            list[InputAction]: A list of input actions associated with the name.
        """

        return self._actions[key] if key in self._actions else []

    def __contains__(self, item: str | InputAction) -> bool:
        """Check if an input action exists by name.

        Args:
            item: The name of the input action.

        Returns:
            bool: True if the action exists, False otherwise.
        """

        if isinstance(item, str):
            return item in self._actions
        if isinstance(item, InputAction):
            return any(
                existing == item for existing in self._actions.get(item.name, [])
            )

        return False

    def register_action(self, action: InputAction) -> None:
        """Register a new input action.

        Args:
            action: The input action to register.

        Raises:
            ValueError: If the action is already registered.
        """

        if action in self._actions[action.name]:
            raise ValueError(f"Action '{action.name}' is already registered.")

        self._actions[action.name].append(action)

    # === Serialization ===

    def serialize(self) -> dict[str, list[dict[str, Any]]]:
        """Serialize the input actions to a JSON serializable dictionary.

        Returns:
            A dictionary where keys are action names and values are lists of
                action variant data.
        """

        result: dict[str, list[dict[str, Any]]] = {}

        for action_name, action_list in self._actions.items():
            result[action_name] = [
                input_action.to_json() for input_action in action_list
            ]

        return result

    def load_from_data(self, data: dict[str, list[dict[str, Any]]]) -> None:
        """Load input actions from a data dictionary.

        Args:
            data: A dictionary where keys are action names and values are
                lists of action variant data.
        """

        for input_actions in data.values():
            for input_action_data in input_actions:
                action = InputAction.from_json_data(input_action_data)
                self.register_action(action)


manager: InputManager = InputManager()
