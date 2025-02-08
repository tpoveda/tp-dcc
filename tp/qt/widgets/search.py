from __future__ import annotations

from Qt.QtCore import Qt, QObject, Signal, QSize, QEvent
from Qt.QtWidgets import QWidget, QLineEdit, QToolButton, QStyle
from Qt.QtGui import QPixmap, QIcon, QResizeEvent, QKeyEvent

from .. import dpi
from ..widgets import layouts, buttons
from ...python import paths


class SearchFindWidget(QWidget, dpi.DPIScaling):
    """
    A widget for searching and finding text.

    Inherits from QWidget and dpi.DPIScaling.

    Signals:
        textChanged (str): Emitted when the text is changed.
        editingFinished (str): Emitted when editing is finished.
        returnPressed (): Emitted when the return key is pressed.
    """

    textChanged = Signal(str)
    editingFinished = Signal(str)
    returnPressed = Signal()

    def __init__(
        self, search_line: QLineEdit | None = None, parent: QWidget | None = None
    ):
        """
        Initializes the SearchFindWidget.

        :param search_line: The QLineEdit for searching. Defaults to None.
        :param parent: The parent widget. Defaults to None.
        """

        super().__init__(parent=parent)

        main_layout = layouts.HorizontalLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(main_layout)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self._search_line = search_line or QLineEdit(parent=self)
        self._search_line.setParent(self)
        self._search_line.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self._search_line.installEventFilter(self)

        try:
            icon_size = self.style().pixelMetric(QStyle.PM_SmallIconSize)
        except RuntimeError:
            icon_size = 62

        self._clear_button = buttons.IconMenuButton(parent=self)
        self._clear_button.setIcon(
            QIcon(paths.canonical_path("../../resources/icons/close.png"))
        )
        self._clear_button.setIconSize(QSize(icon_size - 6, icon_size - 6))
        self._clear_button.setFixedSize(QSize(icon_size, icon_size))
        self._clear_button.setFocusPolicy(Qt.NoFocus)
        self._clear_button.hide()
        self._search_button = buttons.IconMenuButton(parent=self)
        self._search_button.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._search_button.setIcon(
            QIcon(paths.canonical_path("../../resources/icons/search.png"))
        )
        self._search_button.setIconSize(QSize(4, 4))
        self._search_button.setFixedSize(QSize(4, 4))
        self._search_button.setEnabled(True)
        self._search_button.setFocusPolicy(Qt.NoFocus)

        self._search_line.setStyleSheet(
            """
            QLineEdit { padding-left: %spx; padding-right: %spx; border-radius:10px; }
            """
            % (self._search_button_padded_width(), self._clear_button_padded_width())
        )

        self.update_minimum_size()

        self.layout().addWidget(self._search_line)

    def setup_signals(self):
        """
        Function that connects signals for all widget UI widgets.
        """

        self._search_line.textChanged.connect(self.textChanged.emit)
        self._search_line.textChanged.connect(self.set_text)
        self._clear_button.clicked.connect(self.clear)

    @property
    def search_line(self):
        return self._search_line

    def changeEvent(self, event: QEvent):
        """
        Function that overrides base changeEvent function to make sure line edit is properly updated.

        :param event: Qt event.
        """

        try:
            if event.type() == QEvent.EnabledChange:
                enabled = self.isEnabled()
                self._search_button.setEnabled(enabled)
                self._search_line.setEnabled(enabled)
                self._clear_button.setEnabled(enabled)
        except AttributeError:
            pass

    # 	super().changeEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Function that overrides base resizeEvent function to make sure that search icons are properly placed.

        :param event: Qt resize event.
        """

        if not self._clear_button and self._search_line:
            return

        super().resizeEvent(event)

        x = self.width() - self._clear_button_padded_width() * 0.85
        y = (self.height() - self._clear_button.height()) * 0.5
        self._clear_button.move(int(x - 6), int(y))
        self._search_button.move(
            self._search_line_frame_width() * 3,
            int((self.height() - self._search_button.height()) * 0.5),
        )

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Function that overrides base keyPressEvent function to make sure that line is cleared too.

        :param event: Qt key event.
        """

        if event.key() == Qt.Key_Escape:
            self.clear()
            self._search_line.clearFocus()
        super().keyPressEvent(event)

    # noinspection PyTypeChecker
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """
        Overrides base eventFilter function
        :param watched: watched object.
        :param event: event.
        :return:
        """

        try:
            if watched is self._search_line:
                if event.type() == QEvent.FocusIn:
                    self.focusInEvent(event)
                elif event.type() == QEvent.FocusOut:
                    self.focusOutEvent(event)
        except AttributeError:
            pass
        return super().eventFilter(watched, event)

    def get_text(self) -> str:
        """
        Returns current search text.

        :return: search text.
        """

        if not self._search_line:
            return ""
        return self._search_line.text()

    def set_text(self, text: str):
        """
        Sets current search text.

        :param text: search text.
        """

        if not (self._clear_button and self._search_line):
            return

        self._clear_button.setVisible(not (len(text) == 0))
        if text != self.get_text():
            self._search_line.setText(text)

    def get_placeholder_text(self) -> str:
        """
        Returns current search line edit placeholder text.

        :return: placeholder text.
        """

        if not self._search_line:
            return ""

        return self._search_line.text()

    def set_placeholder_text(self, text: str):
        """
        Sets search line edit placeholder text.

        :param text: placeholder text.
        """

        if not self._search_line:
            return
        self._search_line.setPlaceholderText(text)

    def set_focus(self, reason: Qt.FocusReason = Qt.OtherFocusReason):
        """
        Sets the focus reason for the search line edit.

        :param reason: focus reason flag.
        """

        if self._search_line:
            self._search_line.setFocus(reason)
        else:
            self.setFocus(Qt.OtherFocusReason)

    def clear(self, focus: bool = True):
        """
        Clear search line edit text.

        :param focus: whether to focus line edit widget after clearing it.
        """

        if not self._search_line:
            return
        self._search_line.clear()
        if focus:
            self.set_focus()

    def select_all(self):
        """
        Selects all search line edit text.
        """

        if not self._search_line:
            return
        self._search_line.selectAll()

    def update_minimum_size(self):
        """
        Updates the minimum size of the search line edit widget.
        """

        self._search_line.setMinimumSize(
            max(
                self._search_line.minimumSizeHint().width(),
                self._clear_button_padded_width() + self._search_button_padded_width(),
            ),
            max(
                self._search_line.minimumSizeHint().height(),
                max(
                    self._clear_button_padded_width(),
                    self._search_button_padded_width(),
                ),
            ),
        )

    def _search_line_frame_width(self) -> int:
        """
        Internal function that returns the search line widget frame width.

        :return: search line edit frame width.
        """

        try:
            return self._search_line.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        except RuntimeError:
            return 2

    def _clear_button_padded_width(self) -> int:
        """
        Internal function that returns clear button padded width.

        :return: clear button padded width.
        """

        return self._clear_button.width() + self._search_line_frame_width() * 2

    def _clear_button_padded_height(self) -> int:
        """
        Internal function that returns clear button padded height.

        :return: clear button padded height.
        """

        return self._clear_button.height() + self._search_line_frame_width() * 2

    def _search_button_padded_width(self) -> int:
        """
        Internal function that returns search button padded width.

        :return: search button padded width.
        """

        return self._search_button.width() + 2 + self._search_line_frame_width() * 3

    def _search_button_padded_height(self) -> int:
        """
        Internal function that returns search button padded width.

        :return: search button padded width.
        """

        return self._search_button.height() + self._search_line_frame_width() * 2


class ClearToolButton(QToolButton):
    """
    For CSS purposes only
    """

    pass


class SearchToolButton(QToolButton):
    """
    For CSS purposes only
    """

    pass


class SearchLineEdit(QLineEdit, dpi.DPIScaling):
    """Custom line edit similar to a standard search widget."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        clear_pixmap = QPixmap(paths.canonical_path("../../resources/icons/close.png"))
        search_pixmap = QPixmap(
            paths.canonical_path("../../resources/icons/search.png")
        )

        self._clear_action = self.addAction(
            QIcon(clear_pixmap), QLineEdit.TrailingPosition
        )
        self._clear_action.setVisible(False)
        self._search_action = self.addAction(
            QIcon(search_pixmap), QLineEdit.LeadingPosition
        )

        self.setStyleSheet(f"border-radius: {dpi.dpi_scale(9)}px;")

        self._clear_action.triggered.connect(self.clear)
        self.textChanged.connect(self._on_text_changed)

    def keyPressEvent(self, arg__1: QKeyEvent) -> None:
        """
        Function that overrides base keyPressEvent function to make sure that line is cleared too.

        :param QKeyEvent arg__1: Qt key event.
        """

        if arg__1.key() == Qt.Key_Escape:
            self.clear()
            self.setFocus(Qt.OtherFocusReason)
        super().keyPressEvent(arg__1)

    def _on_text_changed(self, text: str) -> None:
        """
        Internal callback function that is called each time the line edit text changes.
        Shows/Hides clear action.
        """

        self._clear_action.setVisible(not len(text) == 0)
