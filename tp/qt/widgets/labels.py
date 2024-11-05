from __future__ import annotations

import enum

from Qt.QtCore import Qt, Signal, Property
from Qt.QtWidgets import QSizePolicy, QWidget, QLabel, QStyleOption
from Qt.QtGui import QIcon, QPainter, QMouseEvent, QResizeEvent, QPaintEvent

from . import layouts
from .. import dpi


class BaseLabel(QLabel, dpi.DPIScaling):
    """
    Custom QLabel implementation that extends standard Qt QLabel class
    """

    clicked = Signal()
    textChanged = Signal(str)

    class Levels(enum.Enum):
        """
        Class that defines different label header levels
        """

        H1 = 1  # header 1
        H2 = 2  # header 2
        H3 = 3  # header 3
        H4 = 4  # header 4
        H5 = 5  # header 5

    class Types(enum.Enum):
        """
        Class that defines different label types
        """

        SECONDARY = "secondary"
        WARNING = "warning"
        DANGER = "danger"

    def __init__(
        self,
        text: str = "",
        tooltip: str = "",
        status_tip: str = "",
        upper: bool = False,
        bold: bool = False,
        enable_menu: bool = True,
        parent: QWidget | None = None,
        elide_mode: Qt.TextElideMode = Qt.ElideNone,
    ):
        """
        Initializes the widget with the specified properties.

        :param text: The text content of the widget. Defaults to an empty string.
        :param tooltip: The tooltip text displayed when hovering over the widget. Defaults to an empty string.
        :param status_tip: The status tip text displayed in the status bar when the widget is hovered. Defaults to an
            empty string.
        :param upper: Whether to display the text in uppercase. Defaults to False.
        :param bold: Whether to display the text in bold font. Defaults to False.
        :param enable_menu: Whether to enable the context menu for the widget. Defaults to True.
        :param parent: The parent widget. Defaults to None.
        :param elide_mode: The text elide mode used for text truncation. Defaults to Qt.ElideNone.
        """

        text = text.upper() if upper else text
        self._enable_menu = enable_menu
        self._actual_text = text

        super().__init__(text, parent)

        self._type = ""
        self._level = 0
        self._underline = False
        self._mark = False
        self._delete = False
        self._strong = False
        self._code = False
        self._elide_mode = elide_mode

        if tooltip:
            self.setToolTip(tooltip)
        if status_tip:
            self.setStatusTip(status_tip)
        self.setTextInteractionFlags(
            Qt.TextBrowserInteraction | Qt.LinksAccessibleByMouse
        )
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.strong(bold)

    def _get_type(self) -> str:
        """
        Internal Qt property function that returns label type.

        :return: label type.
        """

        return self._type

    def _set_type(self, value: BaseLabel.Types):
        """
        Internal Qt property function that sets label type.

        :param value: label type.
        """

        self._type = value
        self.style().polish(self)

    def _get_level(self) -> int:
        """
        Internal Qt property function that returns label level.

        :return: label level.
        """

        return self._level

    def _set_level(self, value: int):
        """
        Internal Qt property function that sets label level.

        :param value: label level.
        """

        self._level = value
        self.style().polish(self)

    def _get_underline(self) -> bool:
        """
        Internal Qt property function that returns whether label is using an underline style.

        :return: True if label has underline style; False otherwise.
        """

        return self._underline

    def _set_underline(self, flag: bool):
        """
        Internal Qt property function that sets label to use an underline style.

        :param flag: underline flag.
        """

        self._underline = flag
        self.style().polish(self)

    def _get_delete(self) -> bool:
        """
        Internal Qt property function that returns whether label is using delete style.

        :return: True if the label is using delete style; False otherwise.
        """

        return self._delete

    def _set_delete(self, flag: bool):
        """
        Internal Qt property function that sets label to use delete style.

        :param flag: delete flag
        """

        self._delete = flag
        self.style().polish(self)

    def _get_strong(self) -> bool:
        """
        Internal Qt property function that returns whether label is using a strong style.

        :return: True if the label has a strong style; False otherwise.
        """

        return self._strong

    def _set_strong(self, flag: bool):
        """
        Internal Qt property function that sets label to use a strong style.

        :param flag: strong flag.
        """

        self._strong = flag
        self.style().polish(self)

    def _get_mark(self) -> bool:
        """
        Internal Qt property function that returns whether label is using a mark style.

        :return: True if the label has a mark style; False otherwise.
        """

        return self._mark

    def _set_mark(self, flag: bool):
        """
        Internal Qt property function that sets label to use a mark style.

        :param flag: mark flag.
        """

        self._mark = flag
        self.style().polish(self)

    def _get_code(self) -> bool:
        """
        Internal Qt property function that returns whether label is using a code style.

        :return: True if the label has a code style; False otherwise.
        """

        return self._code

    def _set_code(self, flag: bool):
        """
        Internal Qt property function that sets label to use a code style.

        :param flag: code flag.
        """

        self._code = flag
        self.style().polish(self)

    def _get_elide_mode(self) -> Qt.TextElideMode:
        """
        Internal Qt property function that returns which elide mode label is using.

        :return: label elide mode.
        """

        return self._elide_mode

    def _set_elide_mode(self, value: Qt.TextElideMode):
        """
        Internal Qt property function that sets elide mode used by the label.

        :param Qt.TextElideMode value: elide mode.
        """

        self._elide_mode = value
        self._update_elided_text()

    theme_type = Property(str, _get_type, _set_type)
    theme_level = Property(int, _get_level, _set_level)
    theme_underline = Property(bool, _get_underline, _set_underline)
    theme_delete = Property(bool, _get_delete, _set_delete)
    theme_mark = Property(bool, _get_mark, _set_mark)
    theme_strong = Property(bool, _get_strong, _set_strong)
    theme_code = Property(bool, _get_code, _set_code)
    theme_elide_mode = Property(bool, _get_elide_mode, _set_elide_mode)

    def mousePressEvent(self, ev: QMouseEvent):
        """
        Overrides mousePressEvent function to emit clicked signal each time user clicks on the label.

        :param ev: Qt mouse event.
        """

        self.clicked.emit()
        super().mousePressEvent(ev)

    def resizeEvent(self, event: QResizeEvent):
        """
        Overrides base QObject resizeEvent function.

        :param event: Qt resize event.
        """

        self._update_elided_text()

    def text(self) -> str:
        """
        Overrides base QLabel text function.
        """

        return self._actual_text

    def setText(self, text: str):
        """
        Overrides base QLabel setText function.

        :param text: label text tos set.
        """

        self._actual_text = text
        self._update_elided_text()
        self.setToolTip(text)
        self.textChanged.emit(text)

    def h1(self) -> BaseLabel:
        """
        Sets label with h1 type.

        :return: current label instance.
        """

        self.theme_level = self.Levels.H1

        return self

    def h2(self) -> BaseLabel:
        """
        Sets label with h2 type.

        :return: current label instance.
        """

        self.theme_level = self.Levels.H2

        return self

    def h3(self) -> BaseLabel:
        """
        Sets label with h3 type.

        :return: current label instance.
        """

        self.theme_level = self.Levels.H3

        return self

    def h4(self) -> BaseLabel:
        """
        Sets label with h4 type.

        :return: current label instance.
        """

        self.theme_level = self.Levels.H4

        return self

    def h5(self) -> BaseLabel:
        """
        Sets label with h4 type.

        :return: current label instance.
        """

        self.theme_level = self.Levels.H5

        return self

    def secondary(self) -> BaseLabel:
        """
        Sets label with secondary type.

        :return: current label instance.
        """

        self.theme_type = self.Types.SECONDARY

        return self

    def warning(self) -> BaseLabel:
        """
        Sets label with warning type.

        :return: current label instance.
        """

        self.theme_type = self.Types.WARNING

        return self

    def danger(self) -> BaseLabel:
        """
        Sets label with danger type.

        :return: current label instance.
        """

        self.theme_type = self.Types.DANGER

        return self

    def strong(self, flag: bool = True) -> BaseLabel:
        """
        Sets label with strong type.

        :param flag: whether enable strong mode.
        :return: current label instance.
        """

        self.theme_strong = flag

        return self

    def mark(self, flag: bool = True) -> BaseLabel:
        """
        Sets label with mark type.

        :param flag: whether to enable mark mode.
        :return: current label instance.
        """

        self.theme_mark = flag

        return self

    def code(self, flag: bool = True) -> BaseLabel:
        """
        Sets label with code type.

        :param flag: whether or not enable code mode.
        :return: current label instance.
        """

        self.theme_code = flag

        return self

    def delete(self, flag: bool = True) -> BaseLabel:
        """
        Sets label with delete type.

        :param flag: whether or not enable delete mode.
        :return: current label instance.
        """

        self.theme_delete = flag

        return self

    def underline(self, flag: bool = True) -> BaseLabel:
        """
        Sets label with underline type.

        :param flag: whether or not enable underline mode.
        :return: current label instance.
        """

        self.theme_underline = flag

        return self

    def _update_elided_text(self):
        """
        Internal function that updates the elided text on the label
        """

        font_metrics = self.fontMetrics()
        elided_text = font_metrics.elidedText(
            self._actual_text, self._elide_mode, self.width() - 2 * 2
        )
        super().setText(elided_text)


class ClippedLabel(BaseLabel):
    """ """

    _width = _text = _elided = None

    def __init__(
        self, text="", width=0, elide=True, always_show_all=False, parent=None
    ):
        """
        Custom QLabel that clips itself if the widget width is smaller than the text.

        :param text: label text.
        :param width: minimum width.
        :param elide: whether label will have ellipsis.
        :param always_show_all: force the label to show the complete text or hide the complete text.
        :param parent: parent widget.
        """

        super(ClippedLabel, self).__init__(text, parent=parent)

        self._always_show_all = always_show_all
        self._elide = elide

        self.setMinimumWidth(width if width > 0 else 1)

    def paintEvent(self, arg__1: QPaintEvent) -> None:
        painter = QPainter(self)
        self.drawFrame(painter)
        margin = self.margin()
        rect = self.contentsRect()
        rect.adjust(margin, margin, -margin, -margin)
        text = self.text()
        width = rect.width()
        if text != self._text or width != self._width:
            self._text = text
            self._width = width
            self._elided = self.fontMetrics().elidedText(text, Qt.ElideRight, width)

        option = QStyleOption()
        option.initFrom(self)

        if self._always_show_all:
            # show all text or show nothing
            if self._width >= self.sizeHint().width():
                self.style().drawItemText(
                    painter,
                    rect,
                    self.alignment(),
                    option.palette,
                    self.isEnabled(),
                    self.text(),
                    self.foregroundRole(),
                )

        else:  # if alwaysShowAll is false though, draw the ellipsis as normal
            if self._elide:
                self.style().drawItemText(
                    painter,
                    rect,
                    self.alignment(),
                    option.palette,
                    self.isEnabled(),
                    self._elided,
                    self.foregroundRole(),
                )
            else:
                self.style().drawItemText(
                    painter,
                    rect,
                    self.alignment(),
                    option.palette,
                    self.isEnabled(),
                    self.text(),
                    self.foregroundRole(),
                )


class IconLabel(QWidget):
    """
    Custom widget that contains a horizontal layout with an icon and a label.
    """

    def __init__(
        self,
        icon: QIcon,
        text: str = "",
        tooltip: str = "",
        upper: bool = False,
        bold: bool = False,
        enable_menu: bool = True,
        parent: QWidget | None = None,
    ):
        """
        Initializes the IconLabel widget.

        :param icon: The icon to display.
        :param text: The text to display.
        :param tooltip: The tooltip.
        :param upper: Whether to display the text in uppercase.
        :param bold: Whether to display the text in bold.
        :param enable_menu: Whether to enable the context menu.
        :param parent: The parent widget.
        """

        super().__init__(parent)

        main_layout = layouts.horizontal_layout(
            margins=(0, 0, 0, 0),
            spacing=dpi.dpi_scale(4),
            alignment=Qt.AlignLeft,
            parent=self,
        )
        self.setLayout(main_layout)

        self._label = BaseLabel(
            text=text,
            tooltip=tooltip,
            upper=upper,
            bold=bold,
            enable_menu=enable_menu,
            parent=parent,
        )
        icon_size = self._label.sizeHint().height()
        self._icon_pixmap = icon.pixmap(icon_size, icon_size)
        self._icon_label = QLabel(parent=self)
        self._icon_label.setPixmap(self._icon_pixmap)

        main_layout.addWidget(self._icon_label)
        main_layout.addWidget(self._label)
        main_layout.addStretch()

    @property
    def label(self) -> BaseLabel:
        """
        Getter method that returns label instance.

        :return: label instance.
        """

        return self._label
