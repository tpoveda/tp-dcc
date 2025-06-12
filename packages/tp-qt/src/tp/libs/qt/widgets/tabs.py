from __future__ import annotations

from Qt.QtCore import Qt, Property, Signal
from Qt.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from Qt.QtGui import QIcon

from .dividers import Divider
from .groups import BaseButtonGroup
from .buttons import BaseToolButton
from .stacks import SlidingOpacityStackedWidget
from ..style import theme


class UnderlineButton(BaseToolButton):
    """Underline button class that creates a button with an underline effect.

    Inherits from BaseToolButton and sets the button to be checkable by default.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self.setCheckable(True)


class UnderlineButtonGroup(BaseButtonGroup):
    """Underline button group class that creates a group of buttons with an underline effect.

    Inherits from BaseButtonGroup and manages a group of UnderlineButton instances
    that can be toggled with an underline visual effect.
    """

    tabChecked = Signal(int)

    def __init__(self, tab: LineTabWidget, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._line_tab = tab
        self._button_group.setExclusive(True)
        self._button_group.buttonClicked.connect(self._on_button_group_button_clicked)

        self.set_spacing(1)

    def create_button(self, button_data: dict) -> UnderlineButton:
        """Overrides the base class method to create an underline button.

        Args:
            button_data: Data dictionary used to configure the button.

        Returns:
            UnderlineButton: The created underline button instance.
        """

        button = UnderlineButton(parent=self)
        if button_data.get("image"):
            button.image(button_data.get("image"))
        if button_data.get("text"):
            if button_data.get("image") or button_data.get("icon"):
                button.text_beside_icon()
            else:
                button.text_only()
        else:
            button.icon_only()

        button.button_size = self._line_tab.line_tab_size

        return button

    def update_size(self, size: str):
        """Update the size of the buttons in the group.

        Args:
            size: Size value to set on all buttons in the group.
        """

        for button in self._button_group.buttons():
            button.button_size = size

    def _get_checked(self) -> int:
        """Gets the current checked button's id value from the button group.

        Returns:
            int: Current checked button's id.
        """

        return self._button_group.checkedId()

    def _set_checked(self, value: int):
        """Sets the checked button by its id value.

        Args:
            value: ID value of the button to check.
        """

        button = self._button_group.button(value)
        button.setChecked(True)
        self.tabChecked.emit(value)

    def _on_button_group_button_clicked(self, button: UnderlineButton):
        """Callback function that is called each time a button is clicked.

        Args:
            button: Button instance that was clicked.
        """

        self.tabChecked.emit(self._button_group.id(button))

    checked = Property(int, _get_checked, _set_checked, notify=tabChecked)


class LineTabWidget(QWidget):
    """Line tab widget class that creates a widget with tabs that can be checked.

    This widget creates a tab bar with selectable tabs that show different content
    when selected. It uses an underline effect to indicate the selected tab.
    """

    def __init__(
        self,
        alignment: Qt.AlignmentFlag = Qt.AlignCenter,
        parent: QWidget | None = None,
    ):
        super().__init__(parent=parent)

        current_theme = theme.instance()
        self.tool_button_group = UnderlineButtonGroup(tab=self)
        self._bar_layout = QHBoxLayout()
        self._bar_layout.setContentsMargins(0, 0, 0, 0)
        if alignment == Qt.AlignCenter:
            # self._bar_layout.addStretch()
            self._bar_layout.addWidget(self.tool_button_group)
            # self._bar_layout.addStretch()
        elif alignment == Qt.AlignLeft:
            self._bar_layout.addWidget(self.tool_button_group)
            self._bar_layout.addStretch()
        elif alignment == Qt.AlignRight:
            self._bar_layout.addStretch()
            self._bar_layout.addWidget(self.tool_button_group)
        self._stack_widget = SlidingOpacityStackedWidget(parent=self)
        self.tool_button_group.tabChecked.connect(self._on_tab_checked)
        main_lay = QVBoxLayout()
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)
        main_lay.addLayout(self._bar_layout)
        main_lay.addWidget(Divider(parent=self))
        main_lay.addSpacing(5)
        main_lay.addWidget(self._stack_widget)
        self.setLayout(main_lay)
        self._line_tab_size: str = current_theme.Sizes.Default.value

    def append_widget(self, widget: QWidget):
        """Append the widget to line tab's right position.

        Args:
            widget: Widget to add to the tab bar's right side.
        """

        self._bar_layout.addWidget(widget)

    def insert_widget(self, widget: QWidget):
        """Insert a widget to line tab's left position.

        Args:
            widget: Widget to insert at the tab bar's left side.
        """

        self._bar_layout.insertWidget(0, widget)

    def add_tab(self, widget: QWidget, data_dict: str | QIcon | dict):
        """Adds a tab to the line tab widget.

        Args:
            widget: tab widget to add.
            data_dict: tab properties.
        """

        self._stack_widget.addWidget(widget)
        self.tool_button_group.add_button(data_dict, self._stack_widget.count() - 1)
        self.tool_button_group.checked = (
            len(self.tool_button_group.button_group.buttons()) - 1
        )

    def _get_line_tab_size(self) -> str:
        """Get the current line tab size.

        Returns:
            str: Current line tab size as a string value.
        """

        return self._line_tab_size

    def _set_line_tab_size(self, value: str):
        """Set the line tab size.

        Args:
            value: Size value to set for the line tabs.
        """

        self._line_tab_size = value
        self.tool_button_group.update_size(self._line_tab_size)
        # self.style().polish(self)

    def _on_tab_checked(self, index: int):
        """Callback function that is called when a tab is checked.

        Args:
            index: Index of the tab that was checked.
        """

        self._stack_widget.setCurrentIndex(index)

    line_tab_size = Property(str, _get_line_tab_size, _set_line_tab_size)
