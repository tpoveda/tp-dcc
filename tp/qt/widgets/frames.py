from __future__ import annotations

from Qt.QtCore import Signal, QSize
from Qt.QtWidgets import (
    QApplication,
    QSizePolicy,
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QSpacerItem,
    QCheckBox,
)
from Qt.QtGui import QFont, QIcon, QMouseEvent

from .dividers import LabelDivider
from .. import uiconsts, dpi, utils as qtutils
from ...python import paths


class BaseFrame(QFrame):
    mouseReleased = Signal(QMouseEvent)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.mouseReleased.emit(event)
        return super().mouseReleaseEvent(event)


class CollapsibleFrame(QWidget):
    """
    Widget for collapsible frame.
    """

    _COLLAPSED_ICON: QIcon | None = None
    _EXPAND_ICON: QIcon | None = None

    openRequested = Signal()
    closeRequested = Signal()
    toggled = Signal()

    def __init__(
        self,
        title: str,
        tooltip: str | None = None,
        collapsed: bool = False,
        collapsable: bool = True,
        checkable: bool = False,
        checked: bool = True,
        content_margins: tuple[int, int, int, int] = uiconsts.MARGINS,
        content_spacing: int = uiconsts.SPACING,
        parent: QWidget | None = None,
    ):
        """
        Initializes CollapsibleFrame

        :param title: The title of the frame.
        :param tooltip: The tooltip of the frame.
        :param collapsed: Whether the frame is initially collapsed.
        :param collapsable: Whether the frame is collapsible.
        :param checkable: Whether the frame is checkable.
        :param checked: Whether the frame is checked.
        :param content_margins: The content margins.
        :param content_spacing: The content spacing.
        :param parent: The parent widget.
        """

        super().__init__(parent=parent)

        self._title = title
        self._tooltip = tooltip
        self._collapsed = collapsed if collapsable else False
        self._collapsable = collapsable
        self._checkable = checkable
        self._checked = checked
        self._content_margins = content_margins
        self._content_spacing = content_spacing

        self._title_frame: BaseFrame | None = None
        self._horizontal_layout: QHBoxLayout | None = None
        self._icon_button: QPushButton | None = None
        self._title_label: QLabel | None = None
        self._spacer_item: QSpacerItem | None = None
        self._hider_widget: QFrame | None = None
        self._hider_layout: QVBoxLayout | None = None
        self._checkbox: QCheckBox | None = None

        if CollapsibleFrame._COLLAPSED_ICON is None:
            CollapsibleFrame._COLLAPSED_ICON = QIcon(
                paths.canonical_path("../../resources/icons/arrow_forward.png")
            )
        if CollapsibleFrame._EXPAND_ICON is None:
            CollapsibleFrame._EXPAND_ICON = QIcon(
                paths.canonical_path("../../resources/icons/arrow_expand.png")
            )

        self._main_layout = QVBoxLayout()
        self._main_layout.setSpacing(0)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._main_layout)

        self._setup_ui()
        self._setup_signals()

    @property
    def hider_layout(self) -> QVBoxLayout:
        """
        Getter method that returns hider layout instance.

        :returns: hider layout.
        """

        return self._hider_layout

    def add_widget(self, widget: QWidget):
        """
        Adds given widget into the content layout.

        :param widget: widget to add.
        """

        self._hider_layout.addWidget(widget)

    def add_layout(self, layout: QVBoxLayout | QHBoxLayout | QGridLayout):
        """
        Adds given widget into the content layout.

        :param layout: layout to add.
        """

        self._hider_layout.addLayout(layout)

    def expand(self):
        """
        Expands/Shows contents.
        """

        self.setUpdatesEnabled(False)
        self._hider_widget.show()
        self._icon_button.setIcon(self._EXPAND_ICON)
        self.setUpdatesEnabled(True)
        self.openRequested.emit()
        self._collapsed = False

    def collapse(self):
        """
        Collapses/Hides contents.
        """

        self.setUpdatesEnabled(False)
        self._hider_widget.hide()
        self._icon_button.setIcon(self._COLLAPSED_ICON)
        QApplication.processEvents()
        self.setUpdatesEnabled(True)
        QApplication.processEvents()
        self.closeRequested.emit()
        self._collapsed = True

    def _setup_ui(self):
        """
        Internal function that setup widgets.
        """

        self._build_title_frame()
        self._build_hider_widget()
        self._main_layout.addWidget(self._title_frame)
        self._main_layout.addWidget(self._hider_widget)

        qtutils.set_stylesheet_object_name(self._title_frame, "collapsed")

    def _setup_signals(self):
        """
        Internal function that setup signal connections.
        """

        self.openRequested.connect(self.toggled.emit)
        self.closeRequested.connect(self.toggled.emit)
        self._checkbox.toggled.connect(self._on_checkbox_toggled)
        self._icon_button.clicked.connect(self._on_icon_button_clicked)
        self._title_frame.mouseReleased.connect(self._on_title_frame_mouse_released)

    def _build_title_frame(self):
        """
        Internal function that builds the title part of the layout with a QFrame widget.
        """

        self._title_frame = BaseFrame(parent=self)
        self._title_frame.setContentsMargins(0, 0, 0, 0)
        self._horizontal_layout = QHBoxLayout()
        self._horizontal_layout.setSpacing(2)
        self._horizontal_layout.setContentsMargins(0, 0, 0, 0)
        self._title_frame.setLayout(self._horizontal_layout)
        self._checkbox = QCheckBox(parent=self)
        self._checkbox.setChecked(self._checked)
        self._checkbox.setVisible(self._checkable)
        self._checkbox.setFixedSize(dpi.size_by_dpi(QSize(18, 18)))
        self._icon_button = QPushButton(parent=self)
        self._icon_button.setFixedSize(dpi.size_by_dpi(QSize(15, 15)))
        self._icon_button.setFlat(True)
        self._icon_button.setContentsMargins(0, 0, 0, 0)
        self._icon_button.setIcon(
            self._COLLAPSED_ICON if self._collapsed else self._EXPAND_ICON
        )
        self._title_label = QLabel(self._title, parent=self)
        font: QFont = self._title_label.font()
        font.setBold(True)
        self._title_label.setFont(font)
        self._title_label.setContentsMargins(0, 0, 0, 0)
        if self._tooltip:
            self._title_label.setToolTip(self._tooltip)
        self._spacer_item = QSpacerItem(
            10, 0, QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        self._horizontal_layout.addSpacing(5)
        self._horizontal_layout.addWidget(self._checkbox)
        self._horizontal_layout.addWidget(self._icon_button)
        self._horizontal_layout.addWidget(self._title_label)
        self._horizontal_layout.addItem(self._spacer_item)

    def _build_hider_widget(self):
        """
        Internal function that builds the collapsable widget.
        """

        self._hider_widget = QFrame(parent=self)
        self._hider_widget.setContentsMargins(0, 0, 0, 0)
        self._hider_layout = QVBoxLayout()
        self._hider_layout.setSpacing(self._content_spacing)
        self._hider_layout.setContentsMargins(*self._content_margins)
        self._hider_widget.setLayout(self._hider_layout)
        self._hider_widget.setHidden(self._collapsed)
        self._hider_widget.setEnabled(True if not self._checkable else self._checked)

    def _show_hide_widget(self):
        """
        Internal function that shows/hides the hider widget which contains the contents specified by the user.
        """

        if not self._collapsable:
            return

        if self._collapsed:
            self.expand()
            return

        self.collapse()

    def _on_checkbox_toggled(self, flag: bool):
        """
        Internal callback function that is called each time checkbox is toggled by the user.

        :param flag: whether checkbox was checked or unchecked.
        """

        self._hider_widget.setEnabled(flag)

    # noinspection PyUnusedLocal
    def _on_icon_button_clicked(self, *args):
        """
        Internal callback function that is called each time icon button is clicked by the user.
        """

        self._show_hide_widget()

    # noinspection PyUnusedLocal
    def _on_title_frame_mouse_released(self, *args):
        """
        Internal callback function that is called each time mouse is released over title frame.
        """

        self._show_hide_widget()


class CollapsibleFrameThin(CollapsibleFrame):
    def _build_title_frame(self):
        super()._build_title_frame()

        title_divider = LabelDivider(parent=self)
        self._spacer_item.changeSize(dpi.dpi_scale(3), 0)
        title_divider.setToolTip(self.toolTip())
        self._horizontal_layout.addWidget(title_divider, 1)
