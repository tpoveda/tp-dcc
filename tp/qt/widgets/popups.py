from __future__ import annotations

import uuid

from Qt.QtCore import Qt, QSize
from Qt.QtWidgets import QApplication, QSizePolicy, QWidget, QLabel, QToolButton
from Qt.QtGui import QIcon, QKeyEvent

from tp.python import strings
from tp.python.paths import canonical_path

from .. import dpi, utils as qtutils
from ..icon import colorize_icon
from .frameless import FramelessWindowThin
from .layouts import VerticalLayout, HorizontalLayout
from .buttons import BaseButton


class MessageBoxBase(FramelessWindowThin):
    """Class that defines a base message box."""

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
        key_presses: tuple[Qt.Key, ...] = (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Space),
    ):
        self._args = locals()
        self._default = default
        parent = parent.window() if parent else None
        name = self._generate_name(icon) if icon else self._generate_name("MessageBox")

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
        """
        Getter function that returns whether the message box is closed or not.

        :return: whether the message box is closed or not.
        """

        return self._msg_closed

    @property
    def result(self) -> str:
        """
        Getter function that returns the result of the message box.

        :return: result of the message box.
        """

        return self._result

    def keyPressEvent(self, event: QKeyEvent):
        """
        Overrides `keyPressEvent` function to handle key press events.

        :param event: Qt key event.
        """

        if self._default > 0:
            keys = self._args["key_presses"]
            if any(map(lambda y: event.key() == y, keys)):
                self._buttons[self._default].leftClicked.emit()

    def close(self, result: str | None = None):
        """
        Overrides `close` function to close the message box.

        :param result: result of the message box.
        """

        self._msg_closed = True
        self._result = result
        super().close()

    def _generate_name(self, name: str):
        """
        Internal function used to generate a unique name.

        :param str  name: original name.
        :return: unique name.
        :rtype: str
        """

        return f"{name}_{str(uuid.uuid4())[:4]}"

    # noinspection PyMethodMayBeStatic
    def _calculate_label_height(self, text: str, label: QLabel):
        """
        Internal function that returns the height of a label based on its text.

        :param str text: label text.
        :param QLabel label: label instance.
        :return: label height.
        :rtype: int
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
        """
        Internal function that initializes message box contents.
        """

        self.set_maximize_button_visible(False)
        self.set_minimize_button_visible(False)
        self.title_bar.set_title_align(Qt.AlignCenter)

        icon_size = 32

        image = QToolButton(parent=self)
        button_icon = self._args["icon"] or None

        if button_icon and isinstance(button_icon, str):
            if button_icon == self.WARNING:
                button_icon = colorize_icon(
                    QIcon(
                        canonical_path(f"../../resources/icons/{self.WARNING_ICON}.png")
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
                        canonical_path(f"../../resources/icons/{self.INFO_ICON}.png")
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
                self._label.fontMetrics().boundingRect(self._label.text()).width() + 20,
                400,
            )
        )
        self._label.setFixedHeight(
            min(self._calculate_label_height(self._label.text(), self._label), 800)
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
            qtutils.set_horizontal_size_policy(button, QSizePolicy.MinimumExpanding)
            self._buttons_layout.addWidget(button)
            button.leftClicked.connect(lambda x=res[i]: self.close(x))
            self._buttons.append(button)
        self._buttons_layout.addStretch(1)

        self.main_layout().addLayout(self._image_layout)
        self.main_layout().addLayout(self._buttons_layout)


class CustomDialog(MessageBoxBase):
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
        """
        Function that shows a dialog with a custom widget.

        :param custom_widget: Custom widget to show in the dialog.
        :param title: Title of the dialog.
        :param message: Message to show in the dialog.
        :param icon: Icon to show in the dialog.
        :param default: Default button index.
        :param button_a: Text of the first button.
        :param button_b: Text of the second button.
        :param button_c: Text of the third button.
        :param parent: Parent widget of the dialog.
        :return: tuple with the result of the dialog and the custom widget.
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
        while dialog.msg_closed is False:
            QApplication.processEvents()

        return dialog.result, custom_widget

    def _init(self):
        """
        Overrides internal `_init` function to initialize message box contents.
        """

        super()._init()

        self._message_layout.addSpacing(dpi.dpi_scale(5))
        self._message_layout.addWidget(self._custom_widget)
