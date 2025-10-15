from __future__ import annotations

from Qt.QtCore import Qt

from tp.libs.python.decorators import Singleton

from .input import InputAction, InputActionType, manager as input_manager


class ConfigManager(metaclass=Singleton):
    """Singleton manager for registering configuration files."""

    def __init__(self):
        super().__init__()

        self.create_default_input()

    # noinspection PyMethodMayBeStatic
    def create_default_input(self) -> None:
        """Create default input actions for the node graph."""

        input_manager.register_action(
            InputAction(
                name="Canvas.Pan",
                action_type=InputActionType.Mouse,
                group="Navigation",
                mouse=Qt.MouseButton.MiddleButton,
            )
        )
        input_manager.register_action(
            InputAction(
                name="Canvas.Pan",
                action_type=InputActionType.Mouse,
                group="Navigation",
                mouse=Qt.MouseButton.LeftButton,
                modifiers=Qt.AltModifier,
            )
        )
        input_manager.register_action(
            InputAction(
                name="Canvas.Zoom",
                action_type=InputActionType.Mouse,
                group="Navigation",
                mouse=Qt.MouseButton.RightButton,
                modifiers=Qt.AltModifier,
            )
        )


# noinspection PyTypeChecker
manager: ConfigManager = ConfigManager()
