from __future__ import annotations

from functools import partial

from Qt import QtCompat
from Qt.QtCore import (
    Qt,
    Signal,
    QObject,
    QPoint,
    QRectF,
    QSize,
    QModelIndex,
    QAbstractItemModel,
)
from Qt.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLineEdit,
    QAbstractItemDelegate,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)
from Qt.QtGui import (
    QFontMetrics,
    QIcon,
    QColor,
    QPainter,
    QBrush,
    QPen,
    QPolygon,
    QTextOption,
    QTextDocument,
    QTextCursor,
    QMouseEvent,
    QFocusEvent,
)

from ....python import paths
from ... import dpi, uiconsts, contexts
from ..layouts import HorizontalLayout
from . import roles
from .roles import TEXT_MARGIN_ROLE


def paint_rect(painter, option, color):
    """
    Paints a rectangle with the given color using the given painter.

    :param painter: painter to use to paint the rectangle.
    :param option: style option for the rectangle.
    :param color: color to use to paint the rectangle.
    """

    points = (
        QPoint(option.rect.x() + 5, option.rect.y()),
        QPoint(option.rect.x(), option.rect.y()),
        QPoint(option.rect.x(), option.rect.y() + 5),
    )
    polygon_triangle = QPolygon.fromList(points)
    painter.save()
    try:
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color))
        painter.drawPolygon(polygon_triangle)
    finally:
        painter.restore()


def paint_html(
    delegate: QStyledItemDelegate,
    painter: QPainter,
    option: QStyleOptionViewItem,
    index: QModelIndex,
) -> bool:
    """
    Paints the HTML text in the given index using the given painter.

    :param delegate: QStyledItemDelegate that is painting the HTML text.
    :param painter: QPainter to use to paint the HTML text.
    :param option: QStyleOptionViewItem to use to paint the HTML text.
    :param index: QModelIndex that contains the HTML text to paint.
    :return bool: Whether the HTML text was painted successfully or not.
    """

    delegate.initStyleOption(option, index)
    if not option.text:
        return False

    model = index.model()
    text_color = model.data(index, Qt.ForegroundRole)
    text_margin = model.data(index, roles.TEXT_MARGIN_ROLE)
    style = option.widget.style() if option.widget else QApplication.style()
    text_option = QTextOption()
    text_option.setWrapMode(
        QTextOption.WordWrap
        if QStyleOptionViewItem.WrapText
        else QTextOption.ManualWrap
    )
    text_option.setTextDirection(option.direction)

    doc = QTextDocument()
    doc.setDefaultTextOption(text_option)
    doc.setHtml(
        '<font color="{}">{}</font>'.format(text_color.name(QColor.HexRgb), option.text)
    )
    doc.setDefaultFont(option.font)
    doc.setDocumentMargin(text_margin)
    doc.setTextWidth(option.rect.width())
    doc.adjustSize()

    # Elide text if necessary.
    if doc.size().width() > option.rect.width():
        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.End)
        elided_postfix = "..."
        metric = QFontMetrics(option.font)
        postfix_width = metric.horizontalAdvance(elided_postfix)
        while doc.size().width() > option.rect.width() - postfix_width:
            cursor.deletePreviousChar()
            doc.adjustSize()
        cursor.insertText(elided_postfix)

    # Painting item without text (this takes care of painting e.g. the highlighted
    # for selected or hovered over items in an ItemView)
    option.text = ""
    style.drawControl(QStyle.CE_ItemViewItem, option, painter, option.widget)

    # Figure out where to render the text in order to follow the requested alignment.
    text_rect = style.subElementRect(QStyle.SE_ItemViewItemText, option)
    document_size = QSize(int(doc.size().width()), int(doc.size().height()))
    layout_rect = QStyle.alignedRect(
        Qt.LayoutDirectionAuto, option.displayAlignment, document_size, text_rect
    )
    painter.save()
    try:
        # Translate the painter to the origin of the layout rectangle in order for the
        # text to be rendered at the correct position
        painter.translate(layout_rect.topLeft())
        doc.drawContents(painter, QRectF(text_rect.translated(-text_rect.topLeft())))
    finally:
        painter.restore()

    return True


class HtmlDelegate(QStyledItemDelegate):
    """
    Custom delegate that displays HTML text in the view.
    """

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """
        Overrides `sizeHint` method to return the size hint for the HTML text.

        :param option: style option for the HTML text.
        :param index: model index to get the size hint for.
        :return: size hint for the HTML text.
        """

        self.initStyleOption(option, index)
        if not option.text:
            return super(HtmlDelegate, self).sizeHint(option, index)
        model = index.model()
        text_margin = model.data(index, TEXT_MARGIN_ROLE)
        if not text_margin:
            return super(HtmlDelegate, self).sizeHint(option, index)
        doc = QTextDocument()
        doc.setHtml(option.text)
        doc.setDefaultFont(option.font)
        doc.setDocumentMargin(text_margin)

        return QSize(int(doc.idealWidth()), int(doc.size().height()))

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """
        Overrides `paint` method to paint the HTML text.

        :param painter: painter to use to paint the HTML text.
        :param option: style option for the HTML text.
        :param index: model index to paint the HTML text for.
        """

        if not paint_html(self, painter, option, index):
            return super().paint(painter, option, index)


class LineEditButtonDelegate(QStyledItemDelegate):
    """
    Custom delegate that displays a combobox and a button.
    Designed to be persistent on the view.
    Combo box will be visible when the users mouse enters the cell only.
    """

    def __ini__(self, parent: QObject | None = None):
        super().__init__(parent=parent)

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """
        Overrides `createEditor` method to create the editor widget.

        :param parent: parent widget to create the editor for.
        :param option: style option for the editor.
        :param index: model index to create the editor for.
        :return: editor widget to use.
        """

        self.initStyleOption(option, index)
        model = index.model()
        text = model.data(index, Qt.DisplayRole)
        rect = option.rect
        widget = LineEditButtonWidget(text, rect.size(), parent)
        widget.setEnabled(bool(model.flags(index) & Qt.ItemIsEditable))
        # widget.button.setStyleSheet("background-color: #{};".format(self.btnColorStr))
        widget.buttonClicked.connect(
            partial(self._on_button_clicked, model, widget, index)
        )
        widget.line_edit.editingFinished.connect(
            partial(self._on_commit_and_close_editor, widget)
        )
        return widget

    def setEditorData(self, editor: LineEditButtonWidget, index: QModelIndex):
        """
        Overrides `setEditorData` method to set the data for the given editor.

        :param editor: editor widget to set the data for.
        :param index: model index to set the data for.
        """

        text = index.model().data(index, Qt.DisplayRole)
        editor.line_edit.setText(text)

    def setModelData(
        self,
        editor: LineEditButtonWidget,
        model: QAbstractItemModel,
        index: QModelIndex,
    ):
        """
        Overrides `setModelData` method to set the data for the given model index.

        :param editor: editor widget to set the data for.
        :param model: model to set the data for.
        :param index: model index to set the data for.
        """

        model.setData(index, editor.line_edit.text(), role=Qt.EditRole)

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """
        Overrides `paint` method to paint the combobox and button.

        :param painter: painter to use to paint the combobox and button.
        :param option: style option for the combobox and button.
        :param index: model index to paint the combobox and button for.
        """

        if not paint_html(self, painter, option, index):
            return super().paint(painter, option, index)

        model = index.model()
        color = model.data(index, roles.EDIT_CHANGED_ROLE)
        if color is None:
            return
        paint_rect(painter, option, color)

    def _on_button_clicked(
        self, model, widget: LineEditButtonWidget, index: QModelIndex
    ):
        """
        Internal callback function that is called when the button is clicked.

        :param model: model to set the data for.
        :param widget: widget to set the data for.
        :param index: model index to set the data for.
        """

        data_changed = model.data(index, roles.BUTTON_CLICKED_ROLE)
        if not data_changed:
            return
        # noinspection PyUnresolvedReferences
        QtCompat.dataChanged(model, index, index)
        with contexts.block_signals(widget.line_edit):
            widget.line_edit.setText(model.data(index, Qt.DisplayRole))
        self.setEditorData(widget, index)

    def _on_commit_and_close_editor(self, widget: LineEditButtonWidget):
        """
        Internal callback function that is called when the editor is committed and closed.

        :param widget: widget to set the data for.
        """

        self.commitData.emit(widget)
        self.closeEditor.emit(widget, QAbstractItemDelegate.NoHint)


class LineEditButtonWidget(QWidget):
    """
    Custom widget that contains a line edit and a button.
    """

    buttonClicked = Signal()

    def __init__(self, text: str, size: QSize, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._setup_widgets(text, size)
        self._setup_layouts()
        self._setup_signals()

    @property
    def button(self) -> QPushButton:
        """
        Getter for the button widget.

        :return: push button instance.
        """

        return self._button

    @property
    def line_edit(self) -> QLineEdit:
        """
        Getter for the line edit widget.

        :return: line edit instance.
        """

        return self._line_edit

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """
        Overrides `mouseDoubleClickEvent` method to show the line edit when the widget is double-clicked.

        :param event: QMouseEvent that triggered the function.
        """

        self._line_edit.show()
        self._line_edit.setFocus()
        self._line_edit.selectAll()
        super().mouseDoubleClickEvent(event)

    def _setup_widgets(self, text: str, size: QSize):
        """
        Internal function that sets up the widget's widgets.

        :param text: text to set in the line edit.
        :param size: size to set to the widget.
        """

        self._button = QPushButton(parent=self)
        self._button.setIconSize(
            QSize(
                dpi.dpi_scale(uiconsts.BUTTON_WIDTH_ICON_SMALL),
                dpi.dpi_scale(uiconsts.BUTTON_WIDTH_ICON_SMALL),
            )
        )
        self._button.setIcon(
            QIcon(paths.canonical_path("../../../resources/icons/arrow_backward.png"))
        )
        self._button.setMaximumWidth(dpi.dpi_scale(uiconsts.BUTTON_WIDTH_ICON_REGULAR))
        self._button.setMaximumHeight(size.height())

        self._line_edit = QLineEdit(text, parent=self)
        self._line_edit.setMinimumHeight(size.height())
        size_policy = self._line_edit.sizePolicy()
        size_policy.setRetainSizeWhenHidden(True)
        self._line_edit.setSizePolicy(size_policy)
        self._line_edit.focusOutEvent = self._focus_out_event_line_edit
        self._line_edit.setHidden(True)

    def _setup_layouts(self):
        """
        Internal function that sets up the widget's layouts.
        """

        main_layout = HorizontalLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        main_layout.addWidget(self._line_edit)
        main_layout.addWidget(self._button)

    def _setup_signals(self):
        """
        Internal function that sets up the widget's signals.
        """

        self._button.clicked.connect(self._on_button_clicked)
        self._line_edit.editingFinished.connect(self._on_line_edit_editing_finished)

    def _focus_out_event_line_edit(self, event: QFocusEvent):
        """
        Internal function that is called when the line edit loses focus.

        :param event: QFocusEvent that triggered the function.
        """

        super().focusOutEvent(event)
        if not self._line_edit.hasAcceptableInput():
            return
        self._line_edit.hide()
        self._line_edit.editingFinished.emit()

    def _on_button_clicked(self):
        """
        Internal callback function that is called when the button is clicked.
        """

        self.buttonClicked.emit()

    def _on_line_edit_editing_finished(self):
        """
        Internal callback function that is called when the line edit editing is finished.
        """

        self._line_edit.hide()
