from __future__ import annotations

import uuid

from Qt.QtCore import QSize, Qt
from Qt.QtGui import QIcon, QKeyEvent
from Qt.QtWidgets import (
    QApplication,
    QLabel,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from tp.libs.python import strings
from tp.libs.python.paths import canonical_path

from .. import dpi
from .. import utils as qtutils
from ..icon import colorize_icon
from .buttons import BaseButton
from .layouts import HorizontalLayout, VerticalLayout
from .window import Window


class MessageBoxBase(Window):
    """Base message box implementation.

    A frameless window that provides standardized message box functionality
    with customizable buttons, icons, and behavior.
    """

    INFO = "Info"
    QUESTION = "Question"
    WARNING = "Warning"
    CRITICAL = "Critical"

    INFO_ICON = "information"
    QUESTION_ICON = "question"
    WARNING_ICON = "warning"
    CRITICAL_ICON = "critical"
    OK_ICON = "checkmark"
    CANCEL_ICON = "close"

    def __init__(
        self,
        parent: QWidget,
        title: str = "",
        message: str = "",
        icon: str | QIcon = QUESTION,
        button_a: str | None = "OK",
        button_b: str | None = None,
        button_c: str | None = None,
        button_icon_a: str | QIcon | None = OK_ICON,
        button_icon_b: str | QIcon | None = CANCEL_ICON,
        button_icon_c: str | QIcon | None = None,
        default: int = 0,
        on_top: bool = True,
        key_presses: tuple[Qt.Key, ...] = (
            Qt.Key_Enter,
            Qt.Key_Return,
            Qt.Key_Space,
        ),
    ):
        self._args = locals()
        self._default = default
        parent = parent.window() if parent else None
        name = (
            self._generate_name(icon)
            if icon
            else self._generate_name("MessageBox")
        )

        super().__init__(
            parent=parent,
            title=title,
            name=name,
            resizable=False,
            width=100,
            height=100,
            modal=False,
            minimize_enabled=False,
            on_top=on_top,
        )

        self._msg_closed = False
        self._result: str | None = None
        self._buttons: list[BaseButton] = []

        self._init()

    @property
    def msg_closed(self) -> bool:
        """Whether the message box is closed or not.

        Returns:
            bool: True if the message box is closed, False otherwise.
        """

        return self._msg_closed

    @property
    def result(self) -> str:
        """The result of the message box interaction.

        Returns:
            str: The result code from user interaction with the message box.
        """

        return self._result

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events.

        Override of Qt's keyPressEvent to trigger default button actions when
        specified keys are pressed.

        Args:
            event (QKeyEvent): The key event from Qt.
        """

        if self._default > 0:
            keys = self._args["key_presses"]
            if any(map(lambda y: event.key() == y, keys)):
                self._buttons[self._default].leftClicked.emit()

    def close(self, result: str | None = None):
        """Close the message box with a result.

        Args:
            result (str, optional): The result code to set before closing. Defaults to None.
        """

        self._msg_closed = True
        self._result = result
        super().close()

    # noinspection PyMethodMayBeStatic
    def _generate_name(self, name: str) -> str:
        """Generate a unique name by appending a UUID fragment.

        Args:
            name: The base name to make unique.

        Returns:
            A unique name with UUID suffix.
        """

        return f"{name}_{str(uuid.uuid4())[:4]}"

    # noinspection PyMethodMayBeStatic
    def _calculate_label_height(self, text: str, label: QLabel) -> int:
        """Calculate the appropriate height for a label based on its text
        content.

        Determines the height needed to display the text by calculating the
        number of lines required and multiplying by line height.

        Args:
            text: The text content to calculate height for.
            label: The label widget to use for font metrics.

        Returns:
            int: The calculated height in pixels.
        """

        font_metrics = label.fontMetrics()
        width = label.size().width()
        height = font_metrics.height()
        lines = 1
        total_width = 0

        for char in text:
            char_width = font_metrics.horizontalAdvance(char)
            total_width += char_width + 1.1
            if total_width > width:
                total_width = width
                lines = +1

        new_lines = strings.new_lines(text)
        lines += new_lines

        return height * lines

    def _init(self):
        """Initialize message box UI components.

        Sets up the button layout, icons, and overall UI structure of the
        message box.
        """

        icon_size = 32

        image = QToolButton(parent=self)
        button_icon = self._args["icon"] or None

        if button_icon and isinstance(button_icon, str):
            if button_icon == self.WARNING:
                button_icon = colorize_icon(
                    QIcon(
                        canonical_path(
                            f"../../resources/icons/{self.WARNING_ICON}.png"
                        )
                    ),
                    size=icon_size,
                    color=(220, 210, 0),
                )
            elif button_icon == self.QUESTION:
                button_icon = colorize_icon(
                    QIcon(
                        canonical_path(
                            f"../../resources/icons/{self.QUESTION_ICON}.png"
                        )
                    ),
                    size=icon_size,
                    color=(0, 192, 32),
                )
            elif button_icon == self.INFO:
                button_icon = colorize_icon(
                    QIcon(
                        canonical_path(
                            f"../../resources/icons/{self.INFO_ICON}.png"
                        )
                    ),
                    size=icon_size,
                    color=(220, 220, 220),
                )
            elif button_icon == self.CRITICAL:
                button_icon = colorize_icon(
                    QIcon(
                        canonical_path(
                            f"../../resources/icons/{self.CRITICAL_ICON}.png"
                        )
                    ),
                    size=icon_size,
                    color=(220, 90, 90),
                )

        if button_icon and isinstance(button_icon, QIcon):
            image.setIcon(button_icon)
        else:
            image.hide()
        if button_icon:
            image.setIconSize(dpi.size_by_dpi(QSize(icon_size, icon_size)))
            image.setFixedSize(dpi.size_by_dpi(QSize(icon_size, icon_size)))

        self._label = QLabel(self._args["message"], parent=self)
        self._label.setFixedWidth(
            min(
                self._label.fontMetrics()
                .boundingRect(self._label.text())
                .width()
                + 20,
                400,
            )
        )
        self._label.setFixedHeight(
            min(
                self._calculate_label_height(self._label.text(), self._label),
                800,
            )
        )
        self._label.setWordWrap(True)
        self._label.setAlignment(Qt.AlignTop)
        self._image_layout = HorizontalLayout()
        self._image_layout.setSpacing(15)
        self._image_layout.setContentsMargins(15, 15, 15, 15)
        self._message_layout = VerticalLayout()
        self._image_layout.addWidget(image)
        self._image_layout.addLayout(self._message_layout)
        self._message_layout.addWidget(self._label)
        self._buttons_layout = HorizontalLayout()
        self._buttons_layout.setContentsMargins(10, 0, 10, 10)
        self._buttons_layout.addStretch(1)

        msg_buttons = [
            self._args["button_a"],
            self._args["button_b"],
            self._args["button_c"],
        ]
        button_icons = [
            self._args["button_icon_a"],
            self._args["button_icon_b"],
            self._args["button_icon_c"],
        ]
        res = ["A", "B", "C"]
        for i, msg_button in enumerate(msg_buttons):
            if not msg_button:
                continue
            _button_icon = button_icons[i]
            if isinstance(_button_icon, str):
                _button_icon = QIcon(
                    canonical_path(f"../../resources/icons/{_button_icon}.png")
                )
            button = BaseButton(
                text=f" {msg_button}",
                button_icon=_button_icon,
                parent=self.parentWidget(),
            )
            button.setMinimumWidth(80)
            button.setMinimumHeight(24)
            qtutils.set_horizontal_size_policy(
                button, QSizePolicy.MinimumExpanding
            )
            self._buttons_layout.addWidget(button)
            button.leftClicked.connect(lambda x=res[i]: self.close(x))
            self._buttons.append(button)
        self._buttons_layout.addStretch(1)

        self.main_layout().addLayout(self._image_layout)
        self.main_layout().addLayout(self._buttons_layout)


class CustomDialog(MessageBoxBase):
    """Custom dialog that extends the base message box to include a custom
    widget.
    """

    def __init__(
        self,
        parent: QWidget,
        custom_widget: QWidget,
        title: str = "",
        message: str = "",
        icon: str | QIcon = MessageBoxBase.QUESTION,
        button_a: str | None = "OK",
        button_b: str | None = None,
        button_c: str | None = None,
        button_icon_a: str | QIcon | None = MessageBoxBase.OK_ICON,
        button_icon_b: str | QIcon | None = MessageBoxBase.CANCEL_ICON,
        button_icon_c: str | QIcon | None = None,
        default: int = 0,
        on_top: bool = True,
    ):
        """Initialize a custom dialog with a custom widget.

        Args:
            parent: Parent widget for the dialog.
            custom_widget: Custom widget to embed in the dialog.
            title: Title of the dialog.
            message: Message to display in the dialog.
            icon: Icon to display in the dialog. Can be a string or QIcon.
            button_a: Text for the first button. Defaults to "OK".
            button_b: Text for the second button. Defaults to None.
            button_c: Text for the third button. Defaults to None.
            button_icon_a: Icon for the first button. Defaults to OK_ICON.
            button_icon_b: Icon for the second button. Defaults to CANCEL_ICON.
            button_icon_c: Icon for the third button. Defaults to None.
            default: int: Index of the default button. Defaults to 0.
            on_top: bool: Whether the dialog should stay on top of other
                windows.
        """

        self._custom_widget = custom_widget

        super().__init__(
            parent=parent,
            title=title,
            message=message,
            icon=icon,
            button_a=button_a,
            button_b=button_b,
            button_c=button_c,
            button_icon_a=button_icon_a,
            button_icon_b=button_icon_b,
            button_icon_c=button_icon_c,
            default=default,
            on_top=on_top,
        )

    @classmethod
    def show_dialog(
        cls,
        custom_widget: QWidget,
        title: str = "Confirm",
        message: str = "Proceed",
        icon: str | QIcon = MessageBoxBase.QUESTION,
        default: int = 0,
        button_a: str | None = "OK",
        button_b: str | None = "Cancel",
        button_c: str | None = None,
        parent: QWidget | None = None,
    ) -> tuple[str, QWidget]:
        """Show a dialog with a custom widget and wait for user interaction.

        Creates and displays a message box dialog that includes a custom
        widget and processes events until the dialog is closed.

        Args:
            custom_widget: Custom widget to embed in the dialog.
            title: Title of the dialog. Defaults to "Confirm".
            message: Message to display. Defaults to "Proceed".
            icon: Icon to display. Defaults to QUESTION.
            default: Index of the default button. Defaults to 0.
            button_a: Text for first button. Defaults to "OK".
            button_b: Text for second button. Defaults to "Cancel".
            button_c: Text for third button. Defaults to None.
            parent: Parent widget for the dialog. Defaults to None.

        Returns:
            A tuple containing the result code and the custom widget.
        """

        dialog = cls(
            parent,
            custom_widget,
            title=title,
            message=message,
            icon=icon,
            default=default,
            button_a=button_a,
            button_b=button_b,
            button_c=button_c,
        )
        dialog.show()
        while not dialog.msg_closed:
            QApplication.processEvents()

        return dialog.result, custom_widget

    def _init(self):
        """Initialize custom dialog UI components.

        Extends the base message box initialization to include the
        custom widget.
        """

        super()._init()

        self._message_layout.addSpacing(dpi.dpi_scale(5))
        self._message_layout.addWidget(self._custom_widget)
