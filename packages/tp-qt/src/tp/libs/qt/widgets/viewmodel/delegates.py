from __future__ import annotations

from functools import partial

from Qt import QtCompat
from Qt.QtCore import (
    Qt,
    Signal,
    QObject,
    QPoint,
    QRect,
    QRectF,
    QSize,
    QModelIndex,
    QAbstractItemModel,
    QEvent,
)
from Qt.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLineEdit,
    QAbstractItemDelegate,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionButton,
    QStyleOptionViewItem,
    QSpinBox,
    QDoubleSpinBox,
    QDateEdit,
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
    QEnterEvent,
)

from tp.libs.python import paths

from . import roles
from ..layouts import HorizontalLayout
from ..comboboxes import BaseComboBox
from ... import icons
from ... import dpi, uiconsts, contexts


def paint_rect(painter: QPainter, option: QStyleOptionViewItem, color: QColor):
    """Draw a triangle-shaped polygon on a given painter object with the
    specified color, using the geometry defined by the input option.

    Args:
        painter: A QPainter object used to render the triangle shape.
        option: Provides the geometry and state information that the function
            uses to determine the triangle's position.
        color: The color used to paint the triangle's brush and pen.
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
    """Render HTML content in a styled item delegate's paint method.

    This function customizes the painting of an item in a view, allowing
    the display of formatted HTML content rendered with the specified style
    options. It computes the layout, adjusts for text wrapping or ellipsis,
    and paints the content on the provided `QPainter` object.

    Notes:
        The function ensures adjusted rendering to account for alignment,
        font, and layout constraints.

    Args:
        delegate: The item delegate responsible for painting the view's item.
        painter: The painter object used to perform the rendering.
        option: Style information about the item to be painted, including
            font, state, and alignment.
        index: The index of the current item in the model.

    Returns:
        `True` if the painting process was completed successfully, `False` if
            the item contains no text and painting is skipped.
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
    """Custom delegate to render HTML content in item views."""

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """Calculate the size hint for a specific item in a view, considering
        custom text formatting and margin properties.

        Args:
            option: The item style options, which include attributes such as
                font and text alignment.
            index: The model index representing the item for which the size
                hint is being calculated.

        Returns:
            The size hint for the given item, adjusted for custom text and
                margin properties.
        """

        self.initStyleOption(option, index)
        if not option.text:
            return super(HtmlDelegate, self).sizeHint(option, index)
        model = index.model()
        text_margin = model.data(index, roles.TEXT_MARGIN_ROLE)
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
        """Paint the given index of a model using the provided painter and
        style option. This  method attempts to render HTML-formatted content
        if present.

        Notes:
            If rendering as HTML is unsuccessful, it falls back to the
                default painting behavior.

        Args:
            painter: `QPainter` instance used to perform the actual painting
                on the widget.
            option: `QStyleOptionViewItem` object containing style options
                for rendering.
            index: `QModelIndex` object representing the model index to be
                painted.
        """

        if not paint_html(self, painter, option, index):
            return super().paint(painter, option, index)

        return None


class LineEditButtonDelegate(QStyledItemDelegate):
    """A delegate for managing a custom editor widget that combines a line edit
    and a button within item views such as `QTableView` or `QTreeView`.
    """

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """Create and return an editor widget for use within item views, such
        as `QTreeView` or `QTableView`. This editor is customized to include a
        LineEdit and Button within the same widget.

        The editor adapts to the size and content of the item being edited
        and executes specified actions through signal connections to manage
        user interactions.

        Args:
            parent: The parent widget for the created editor.
            option: Contains options detailing how the editor should be
                rendered.
            index: The index of the data item for which the editor is being
                created.

        Returns:
            A custom editor widget consisting of a line edit and button,
                with behavior dynamically defined by the item's properties
                and signals.
        """

        self.initStyleOption(option, index)
        model = index.model()
        text = model.data(index, Qt.DisplayRole)
        rect = option.rect
        widget = LineEditButtonWidget(text, rect.size(), parent)
        widget.setEnabled(bool(model.flags(index) & Qt.ItemIsEditable))
        widget.buttonClicked.connect(
            partial(self._on_button_clicked, model, widget, index)
        )
        widget.line_edit.editingFinished.connect(
            partial(self._on_commit_and_close_editor, widget)
        )
        return widget

    def setEditorData(self, editor: LineEditButtonWidget, index: QModelIndex):
        """Set the data from the model index into the provided editor widget.

        Args:
            editor: The `LineEditButtonWidget` instance where the data will be
                set.
            index: The `QModelIndex` instance containing the model data to be
                set in the editor.
        """

        text = index.model().data(index, Qt.DisplayRole)
        editor.line_edit.setText(text)

    def setModelData(
        self,
        editor: LineEditButtonWidget,
        model: QAbstractItemModel,
        index: QModelIndex,
    ):
        """Set the data for a specified index in the given model using the text
        from the provided LineEditButtonWidget editor.

        Args:
            editor: A custom editor widget with a line edit whose text will
                be set as data for the model.
            model: The data model where the data will be set at the specified
                index.
            index: The `QModelIndex` indicating the position in the data model
                where the data will be set.
        """

        model.setData(index, editor.line_edit.text(), role=Qt.EditRole)

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """Paint the content of a view item in a QTableView or similar widget.
        This function checks whether an HTML-based painting is required;
        if not, it falls back to the base implementation.

        Additionally, it supports custom rendering by using a color provided
        through a custom data role.

        Args:
            painter: A QPainter instance used to render the item.
            option: The style and display options for the item.
            index: The QModelIndex identifying the item to be painted.
        """

        if not paint_html(self, painter, option, index):
            return super().paint(painter, option, index)

        model = index.model()
        color = model.data(index, roles.EDIT_CHANGED_ROLE)
        if color is None:
            return None

        return paint_rect(painter, option, color)

    def _on_button_clicked(
        self, model, widget: LineEditButtonWidget, index: QModelIndex
    ):
        """Handles button click events within a custom widget editor.
        The method is invoked when a button in the widget is clicked, and it
        proceeds to update the widget's state and synchronize its data with
        the model.

        The function checks whether the button click action has triggered a
        change in the data. If it has, updates are made to the model and
        the widget's line edit is synchronized with the model's data for the
        corresponding index.

        Notes:
            Any signals emitted by the widget's line edit while updating are
            temporarily blocked to prevent undesired side effects. Additionally,
            editor data is set with updated widget state after the data
            synchronization process.

        Args:
            model: The data model that interfaces with the widget. Expected to
                have a custom data role to handle button click events and
                update its state accordingly.
            widget: The custom widget containing a button and a line edit field.
                The widget is updated based on the new model data.
            index: The index in the data model that is associated with the
                widget. Represents the specific location in the data structure
                for interaction.
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
        """Execute commit and close editor operations on the given widget.

        Args:
            widget: The widget that is undergoing the commit and close editor
                operations.
        """

        self.commitData.emit(widget)
        self.closeEditor.emit(widget, QAbstractItemDelegate.NoHint)


class LineEditButtonWidget(QWidget):
    """Custom widget that contains a line edit and a button."""

    buttonClicked = Signal()

    def __init__(self, text: str, size: QSize, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._setup_widgets(text, size)
        self._setup_layouts()
        self._setup_signals()

    @property
    def button(self) -> QPushButton:
        """The button widget."""

        return self._button

    @property
    def line_edit(self) -> QLineEdit:
        """The line edit widget."""

        return self._line_edit

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle the double-click event on the mouse to enable and manage the
        appearance of a `QLineEdit` widget.

        This method overrides the default behavior for mouse double-click
        events. It makes the `QLineEdit` widget visible, focuses on it, and
        selects all its content to allow quick editing.

        Notes:
            The parent class's implementation is also called to ensure the
            base functionality is preserved.

        Args:
            event: The mouse event object containing information about the
                double-click interaction.
        """

        self._line_edit.show()
        self._line_edit.setFocus()
        self._line_edit.selectAll()
        super().mouseDoubleClickEvent(event)

    def _setup_widgets(self, text: str, size: QSize):
        """Set up the widgets.

        Args:
            text: text to set in the line edit.
            size: size to set to the widget.
        """

        self._button = QPushButton(parent=self)
        self._button.setIconSize(
            QSize(
                dpi.dpi_scale(uiconsts.BUTTON_WIDTH_ICON_SMALL),
                dpi.dpi_scale(uiconsts.BUTTON_WIDTH_ICON_SMALL),
            )
        )
        self._button.setIcon(
            QIcon(
                paths.canonical_path("../../../resources/icons/arrow_backward_64.png")
            )
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
        """Set up the layouts."""

        main_layout = HorizontalLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        main_layout.addWidget(self._line_edit)
        main_layout.addWidget(self._button)

    def _setup_signals(self):
        """Set up the signals."""

        self._button.clicked.connect(self._on_button_clicked)
        self._line_edit.editingFinished.connect(self._on_line_edit_editing_finished)

    def _focus_out_event_line_edit(self, event: QFocusEvent):
        """Handles the focus out event for a line edit widget.

        This method overrides the default focus out event to perform
        additional checks and actions when the line edit widget loses focus.

        If the input of the line edit is valid, the line edit is hidden,
        and the `editingFinished` signal is emitted.

        Args:
            event: The focus event that triggered this method.
        """

        super().focusOutEvent(event)

        if not self._line_edit.hasAcceptableInput():
            return

        self._line_edit.hide()
        self._line_edit.editingFinished.emit()

    def _on_button_clicked(self):
        """Handle the event triggered when the button is clicked."""

        self.buttonClicked.emit()

    def _on_line_edit_editing_finished(self):
        """Handle the event triggered when the editing of the line edit widget
        is finished.
        """

        self._line_edit.hide()


class CheckBoxDelegate(QStyledItemDelegate):
    """A delegate that places a fully functioning QCheckBox in every
    cell of the column to which it's applied
    """

    def __init__(self, parent):
        super(CheckBoxDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        """Create an editor widget for editing item data in a model-view
        framework.

        Notes:
            In this case, we do not create an editor widget because the
            checkbox is painted directly in the cell.

            Is the developer's responsibility to make sure to set up the model
            so the delegate is automatically opened when the view is
            instantiated.

        Args:
            parent : The parent widget of the editor.
            option: Contains style options for the item being edited.
            index: Refers to the specific item in the model for which the
                editor is being created.

        Returns:
            A configured instance of `QCheckBox` based on the model's
                data roles.
        """

        return None

    def setModelData(self, editor: None, model: QAbstractItemModel, index: QModelIndex):
        """Update the model data with the value from the widget at a given
        index.

        Args:
            editor: The widget containing the data to be set in the model.
            model: The model where data will be updated.
            index: The index in the model where the data will be set.
        """

        new_value = not index.data()
        model.setData(index, new_value, Qt.EditRole)

    def editorEvent(self, event: QEvent, model, option, index):
        """Handle the editor events for QWidget-based items.

        Args:
            event: The event being processed, typically related to user actions
                like mouse or keyboard interactions.
            model: The model containing item data corresponding to the editor
                event.
            option: The `QStyleOptionViewItem` that describes parameters for
                drawing.
            index: The index representing the item's position in the model.

        Returns:
            True if the event should proceed with further processing; False
                otherwise.
        """

        if index.flags() & Qt.ItemIsEditable < 1:
            return False

        # Do not change the checkbox-state.
        if (
            event.type() == QEvent.MouseButtonPress
            or event.type() == QEvent.MouseMove
            or event.type() == QEvent.KeyPress
        ):
            return False
        elif (
            event.type() == QEvent.MouseButtonRelease
            or event.type() == QEvent.MouseButtonDblClick
        ):
            # noinspection PyUnresolvedReferences
            if event.button() != Qt.LeftButton or not self._get_check_box_rect(
                option
            ).contains(event.pos()):
                return False
            if event.type() == QEvent.MouseButtonDblClick:
                return True

        # Change the checkbox-state.
        self.setModelData(None, model, index)

        return True

    def paint(self, painter, option, index):
        """Paint the cell with a custom appearance for a checkbox delegate.

        Args:
            painter: `QPainter` instance used for rendering purposes.
            option: `QStyleOptionViewItem` object that specifies options for
                the rendering of the cell.
            index: `QModelIndex` object that represents the model index
                corresponding to the cell to be painted.
        """

        checked = bool(index.data())
        check_box_style_option = QStyleOptionButton()
        is_enabled = (index.flags() & Qt.ItemIsEditable) > 0 and (
            index.flags() & Qt.ItemIsEnabled
        ) > 0
        if is_enabled:
            check_box_style_option.state |= QStyle.State_Enabled
        else:
            check_box_style_option.state |= QStyle.State_ReadOnly

        if checked:
            check_box_style_option.state |= QStyle.State_On
        else:
            check_box_style_option.state |= QStyle.State_Off
        check_box_style_option.rect = self._get_check_box_rect(option)
        check_box_style_option.state |= QStyle.State_Enabled

        QApplication.style().drawControl(
            QStyle.CE_CheckBox, check_box_style_option, painter
        )
        model = index.model()
        color = model.data(index, roles.EDIT_CHANGED_ROLE)
        if color is None:
            return None

        return paint_rect(painter, option, color)

    # noinspection PyMethodMayBeStatic
    def _get_check_box_rect(self, option: QStyleOptionViewItem) -> QRect:
        check_box_style_option = QStyleOptionButton()
        check_box_rect = QApplication.style().subElementRect(
            QStyle.SE_CheckBoxIndicator, check_box_style_option, None
        )
        check_box_point = QPoint(
            option.rect.x() + option.rect.width() * 0.5 - check_box_rect.width() * 0.5,
            option.rect.y()
            + option.rect.height() * 0.5
            - check_box_rect.height() * 0.5,
        )
        return QRect(check_box_point, check_box_rect.size())


class NumericIntDelegate(QStyledItemDelegate):
    """A delegate class for providing and handling double numeric input in a
    model-view framework using a `QSpinBox` editor.
    """

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """Create an editor widget for editing item data in a model-view
        framework.

        Args:
            parent : The parent widget of the editor.
            option: Contains style options for the item being edited.
            index: Refers to the specific item in the model for which the
                editor is being created.

        Returns:
            A configured instance of `QSpinBox` based on the model's
                data roles.
        """

        model = index.model()
        widget = QSpinBox(parent=parent)
        widget.setMinimum(model.data(index, roles.MIN_VALUE_ROLE))
        widget.setMaximum(model.data(index, roles.MAX_VALUE_ROLE))

        return widget

    def setEditorData(self, widget: QSpinBox, index: QModelIndex):
        """Set the data from the model to the widget before the widget is
        presented to the user for editing.

        Args:
            widget: The editor widget that will be used for data input.
            index: The index in the model that contains the data to be edited.
        """

        with contexts.block_signals(widget):
            value = index.model().data(index, Qt.EditRole)
            widget.setValue(value)

    def setModelData(
        self, widget: QSpinBox, model: QAbstractItemModel, index: QModelIndex
    ):
        """Update the model data with the value from the widget at a given
        index.

        Args:
            widget: The widget containing the data to be set in the model.
            model: The model where data will be updated.
            index: The index in the model where the data will be set.
        """

        value = widget.value()
        model.setData(index, int(value), Qt.EditRole)

    def updateEditorGeometry(
        self, editor: QSpinBox, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """Update the geometry of the editor widget to match the rectangle
        specified by the option. This function adjusts the position and size
        of the editor based on the given geometry data.

        Args:
            editor: The editor widget whose geometry needs to be updated.
            option: An object containing the rectangle (rect) and state
                information, used for configuring the editor's display.
            index: The model index that provides context for the editor,
                typically relating to where it is being displayed within a
                data model.
        """

        editor.setGeometry(option.rect)

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """Paint the cell with a custom appearance for a numeric delegate.

        Render the cell's background with a specific color associated with the
        data in a given model index, provided custom painting conditions are
        met.

        Notes:
            If the custom condition fails, it falls back to the parent class's
            painting mechanism.

        Args:
            painter: `QPainter` instance used for rendering purposes.
            option: `QStyleOptionViewItem` object that specifies options for
                the rendering of the cell.
            index: `QModelIndex` object that represents the model index
                corresponding to the cell to be painted.
        """

        if not paint_html(self, painter, option, index):
            return super().paint(painter, option, index)

        model = index.model()
        color = model.data(index, roles.EDIT_CHANGED_ROLE)
        if color is None:
            return None

        return paint_rect(painter, option, color)


class NumericDoubleDelegate(QStyledItemDelegate):
    """A delegate class for providing and handling double numeric input in a
    model-view framework using a `QDoubleSpinBox` editor.
    """

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """Create an editor widget for editing item data in a model-view
        framework.

        Args:
            parent : The parent widget of the editor.
            option: Contains style options for the item being edited.
            index: Refers to the specific item in the model for which the
                editor is being created.

        Returns:
            A configured instance of `QDoubleSpinBox` based on the model's
                data roles.
        """

        model = index.model()
        widget = QDoubleSpinBox(parent=parent)
        widget.setMinimum(model.data(index, roles.MIN_VALUE_ROLE))
        widget.setMaximum(model.data(index, roles.MAX_VALUE_ROLE))

        return widget

    def setEditorData(self, widget: QDoubleSpinBox, index: QModelIndex):
        """Set the data from the model to the widget before the widget is
        presented to the user for editing.

        Args:
            widget: The editor widget that will be used for data input.
            index: The index in the model that contains the data to be edited.
        """

        with contexts.block_signals(widget):
            value = index.model().data(index, Qt.EditRole)
            widget.setValue(value)

    def setModelData(
        self, widget: QDoubleSpinBox, model: QAbstractItemModel, index: QModelIndex
    ):
        """Update the model data with the value from the widget at a given
        index.

        Args:
            widget: The widget containing the data to be set in the model.
            model: The model where data will be updated.
            index: The index in the model where the data will be set.
        """

        value = widget.value()
        model.setData(index, float(value), Qt.EditRole)

    def updateEditorGeometry(
        self, editor: QDoubleSpinBox, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """Update the geometry of the editor widget to match the rectangle
        specified by the option. This function adjusts the position and size
        of the editor based on the given geometry data.

        Args:
            editor: The editor widget whose geometry needs to be updated.
            option: An object containing the rectangle (rect) and state
                information, used for configuring the editor's display.
            index: The model index that provides context for the editor,
                typically relating to where it is being displayed within a
                data model.
        """

        editor.setGeometry(option.rect)

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """Paint the cell with a custom appearance for a numeric double
        delegate.

        Render the cell's background with a specific color associated with the
        data in a given model index, provided custom painting conditions are
        met.

        Notes:
            If the custom condition fails, it falls back to the parent class's
            painting mechanism.

        Args:
            painter: `QPainter` instance used for rendering purposes.
            option: `QStyleOptionViewItem` object that specifies options for
                the rendering of the cell.
            index: `QModelIndex` object that represents the model index
                corresponding to the cell to be painted.
        """

        if not paint_html(self, painter, option, index):
            return super().paint(painter, option, index)

        model = index.model()
        color = model.data(index, roles.EDIT_CHANGED_ROLE)
        if color is None:
            return None

        return paint_rect(painter, option, color)


class EnumerationDelegate(QStyledItemDelegate):
    """Provides a custom delegate for handling enumeration data in a model-view
    architecture.

    Attributes:
        _requires_popup: Tracks if the editor requires the popup to be
            displayed. Used to ensure popups are shown correctly after certain
            interactions.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._requires_popup = False

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> BaseComboBox:
        """Create an editor widget for editing item data in a model-view
        framework.

        Args:
            parent : The parent widget of the editor.
            option: Contains style options for the item being edited.
            index: Refers to the specific item in the model for which the
                editor is being created.

        Returns:
            A configured instance of `BaseComboBox` based on the model's
                data roles.
        """

        model = index.model()
        combo = BaseComboBox(model.data(index, roles.ENUMS_ROLE), parent=parent)
        return combo

    def editorEvent(
        self,
        event: QEvent,
        model: QAbstractItemModel,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> bool:
        """Handle the editor events for QWidget-based items.

        Args:
            event: The event being processed, typically related to user actions
                like mouse or keyboard interactions.
            model: The model containing item data corresponding to the editor
                event.
            option: The `QStyleOptionViewItem` that describes parameters for
                drawing.
            index: The index representing the item's position in the model.

        Returns:
            True if the event should proceed with further processing; False
                otherwise.
        """

        # noinspection PyUnresolvedReferences
        if (
            event.type() == QEvent.MouseButtonRelease
            and event.button() == Qt.LeftButton
            and (model.flags(index) & Qt.ItemIsEditable)
        ):
            view = option.widget
            if view is None:
                return True
            view.setCurrentIndex(index)
            view.edit(index)
            self._requires_popup = True

        return super().editorEvent(event, model, option, index)

    def setEditorData(self, editor: BaseComboBox, index: QModelIndex):
        """Set the data from the model to the widget before the widget is
        presented to the user for editing.

        Args:
            editor: The editor widget that will be used for data input.
            index: The index in the model that contains the data to be edited.
        """

        with contexts.block_signals(editor):
            text = index.model().data(index, Qt.DisplayRole)
            enums = index.model().data(index, roles.ENUMS_ROLE)
            index = editor.findText(text, Qt.MatchFixedString)
            if index >= 0:
                editor.clear()
                editor.addItems(enums)
                editor.setCurrentIndex(index)
            if self._requires_popup:
                self._requires_popup = False
                editor.showPopup()

    def setModelData(
        self, editor: BaseComboBox, model: QAbstractItemModel, index: QModelIndex
    ):
        """Update the model data with the value from the widget at a given
        index.

        Args:
            editor: The widget containing the data to be set in the model.
            model: The model where data will be updated.
            index: The index in the model where the data will be set.
        """

        model.setData(index, editor.currentIndex(), role=Qt.EditRole)

    def paint(self, painter, option, index):
        """Paint the cell with a custom appearance for a enumerator delegate.

        Args:
            painter: `QPainter` instance used for rendering purposes.
            option: `QStyleOptionViewItem` object that specifies options for
                the rendering of the cell.
            index: `QModelIndex` object that represents the model index
                corresponding to the cell to be painted.
        """

        if not paint_html(self, painter, option, index):
            return super(EnumerationDelegate, self).paint(painter, option, index)

        model = index.model()
        color = model.data(index, roles.EDIT_CHANGED_ROLE)
        if color is None:
            return None

        return paint_rect(painter, option, color)


class ButtonDelegate(QStyledItemDelegate):
    """A delegate for handling customizable `QPushButton` editors."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """Create an editor widget for editing item data in a model-view
        framework.

        Args:
            parent : The parent widget of the editor.
            option: Contains style options for the item being edited.
            index: Refers to the specific item in the model for which the
                editor is being created.

        Returns:
            A configured instance of `QPushButton` based on the model's
                data roles.
        """

        model = index.model()
        widget = QPushButton(text=str(model.data(index, Qt.DisplayRole)), parent=parent)
        widget.clicked.connect(partial(self.setModelData, widget, model, index))

        return widget

    def setEditorData(self, widget: QPushButton, index: QModelIndex):
        """Set the data from the model to the widget before the widget is
        presented to the user for editing.

        Args:
            widget: The editor widget that will be used for data input.
            index: The index in the model that contains the data to be edited.
        """

        text = index.model().data(index, Qt.DisplayRole)
        widget.setText(str(text))

    def setModelData(
        self, widget: QPushButton, model: QAbstractItemModel, index: QModelIndex
    ):
        """Update the model data with the value from the widget at a given
        index.

        Args:
            widget: The widget containing the data to be set in the model.
            model: The model where data will be updated.
            index: The index in the model where the data will be set.
        """

        model.setData(index, None, Qt.EditRole)

    def updateEditorGeometry(
        self, editor: QPushButton, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """Update the geometry of the editor widget to match the rectangle
        specified by the option. This function adjusts the position and size
        of the editor based on the given geometry data.

        Args:
            editor: The editor widget whose geometry needs to be updated.
            option: An object containing the rectangle (rect) and state
                information, used for configuring the editor's display.
            index: The model index that provides context for the editor,
                typically relating to where it is being displayed within a
                data model.
        """

        editor.setGeometry(option.rect)

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """Paint the cell with a custom appearance for a numeric delegate.

        Render the cell's background with a specific color associated with the
        data in a given model index, provided custom painting conditions are
        met.

        Notes:
            If the custom condition fails, it falls back to the parent class's
            painting mechanism.

        Args:
            painter: `QPainter` instance used for rendering purposes.
            option: `QStyleOptionViewItem` object that specifies options for
                the rendering of the cell.
            index: `QModelIndex` object that represents the model index
                corresponding to the cell to be painted.
        """

        if not paint_html(self, painter, option, index):
            return super().paint(painter, option, index)

        model = index.model()
        color = model.data(index, roles.EDIT_CHANGED_ROLE)
        if color is None:
            return None

        return paint_rect(painter, option, color)


class ButtonEnumerationDelegate(QStyledItemDelegate):
    """Delegate which displays a combobox and button."""

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> ButtonEnumerationWidget:
        """Creates and sets up a custom editor widget for use in an item model delegate.

        This method is called to create an editor widget which is used to edit
        data from the model. The created widget is highly customized and specific
        to enumeration data, providing a dropdown list and a color-configurable
        button.

        Args:
            parent: The parent widget for the editor.
            option: Contains parameters for rendering and editing behavior,
                including style and positioning information.
            index: The index of the model's item associated with the editor.

        Returns:
            The custom editor widget tailored for enumeration data.
        """

        self.initStyleOption(option, index)
        model = index.model()
        enums = model.data(index, roles.ENUMS_ROLE)
        rect: QRect = option.rect
        widget = ButtonEnumerationWidget(enums, rect.size(), parent)
        widget.setEnabled(bool(model.flags(index) & Qt.ItemIsEditable))
        widget._enable_enter_leave_popup = bool(model.flags(index) & Qt.ItemIsEditable)
        widget.buttonClicked.connect(
            partial(self._on_button_clicked, model, widget, index)
        )
        widget.combobox.currentIndexChanged.connect(
            partial(self._commit_and_close_editor, widget)
        )

        return widget

    def setEditorData(self, editor: ButtonEnumerationWidget, index: QModelIndex):
        """Set the editor's data based on the provided model index.

        Retrieves display text and enumeration options from the model using
        the index.

        Updates the editor's combo box by clearing its items, adding the
        retrieved enumeration options, and setting the current index to match
        the retrieved text.

        Args:
            editor: The editor instance containing a combo box to be updated.
            index: The model index from which data is retrieved to set in the editor.
        """

        model = index.model()
        text = model.data(index, Qt.DisplayRole)
        enums = model.data(index, roles.ENUMS_ROLE)
        match_index = editor.combobox.findText(text, Qt.MatchFixedString)
        if match_index >= 0:
            with contexts.block_signals(editor.combobox):
                editor.combobox.clear()
                editor.combobox.addItems(enums)
                editor.combobox.setCurrentIndex(match_index)

    def setModelData(
        self,
        editor: ButtonEnumerationWidget,
        model: QAbstractItemModel,
        index: QModelIndex,
    ):
        """Set the model data using the information from the editor widget
        and the specific index.

        This method updates the data in the model for the provided index with
        the current value selected in the editor's combo box.

        The data is set with the specified role indicating it should be edited.

        Args:
            editor: QComboBox-like widget used as an editor.
            model: QAbstractItemModel or its subclass where the data will be updated.
            index: QModelIndex that specifies the location in the model where the data will be set.
        """

        model.setData(index, int(editor.combobox.currentIndex()), role=Qt.EditRole)

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """Paint the delegate for the specified `QModelIndex`.

        Args:
            painter: The painter object used for rendering the delegate.
            option: The style option, providing styling parameters for the delegate.
            index: The QModelIndex that specifies where the delegate should be painted.
        """

        if not paint_html(self, painter, option, index):
            return super().paint(painter, option, index)

        model = index.model()
        color = model.data(index, roles.EDIT_CHANGED_ROLE)
        if color is None:
            return None

        return paint_rect(painter, option, color)

    # noinspection PyUnusedLocal
    def _commit_and_close_editor(
        self, widget: ButtonEnumerationWidget, index: QModelIndex
    ):
        """Commits data and closes the editor associated with the specified
        widget and index.

        Args:
            widget: The editor widget whose data
                needs to be committed and closed.
            index: The index in the model that is being edited.
        """

        self.commitData.emit(widget)
        self.closeEditor.emit(widget, QAbstractItemDelegate.NoHint)

    def _on_button_clicked(
        self,
        model: QAbstractItemModel,
        widget: ButtonEnumerationWidget,
        index: QModelIndex,
    ):
        """Handle the button clicked event for a widget.

        This method manages actions triggered when a button within the widget
        is clicked. It updates the corresponding data in the model, modifies
        the widget's state, and ensures the editor reflects the new data.

        Args:
            model: The data model associated with the widget.
            widget: The widget that contains the button triggering the event.
            index: The QModelIndex pointing to the item related to the event.
        """

        data_changed = model.data(index, roles.BUTTON_CLICKED_ROLE)
        if not data_changed:
            return

        # noinspection PyUnresolvedReferences
        QtCompat.dataChanged(model, index, index)

        with contexts.block_signals(widget.combobox):
            widget.combobox.clear()
            widget.combobox.addItems(model.data(index, roles.ENUMS_ROLE))

        self.setEditorData(widget, index)


class ButtonEnumerationWidget(QWidget):
    """A widget that combines a button and a combobox for enumeration
    selection.

    This widget allows users to interact with a custom button and dropdown
    (combobox) together. The combobox is populated dynamically with the
    provided enumeration items and maintains interactive behavior influenced
    by mouse enter and leave events.

    Attributes:
        buttonClicked: Signal emitted when the button in the widget is clicked.
        _combobox: The combobox associated with this widget.
        _button: The button associated with this widget.
    """

    buttonClicked = Signal()

    def __init__(self, enums, size, parent):
        super(ButtonEnumerationWidget, self).__init__(parent=parent)

        self._enable_enter_leave_popup = True
        self._current_combo_is_focused = False

        layout = HorizontalLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self._button = QPushButton(parent=self)
        button_size = int(dpi.dpi_scale(uiconsts.BUTTON_WIDTH_ICON_SMALL))
        self._button.setIconSize(QSize(button_size, button_size))
        self._button.setMaximumWidth(dpi.dpi_scale(uiconsts.BUTTON_WIDTH_ICON_REGULAR))
        self._button.setMaximumHeight(size.height())
        self._button.setIcon(icons.icon("arrow-left-white"))

        self._combobox = BaseComboBox(items=enums, parent=self)
        self._combobox.setMinimumHeight(size.height())
        policy = self._combobox.sizePolicy()
        policy.setRetainSizeWhenHidden(True)
        self._combobox.setSizePolicy(policy)
        self._combobox.setHidden(True)
        layout.addWidget(self._combobox)
        layout.addWidget(self._button)

        self._button.clicked.connect(self.buttonClicked.emit)

        def _show_combo_popup():
            """Handle the display of the combo popup while ensuring necessary
            focus settings. This method overrides default focus behavior to
            prevent the combobox from hiding due to leave events on associated
            widgets.
            """

            self._current_combo_is_focused = True
            super(BaseComboBox, self._combobox).showPopup()

        def _hide_combo_popup():
            """Hide the combo box popup.

            This method ensures that the popup menu of the combo box is hidden
            and updates the state to reflect that the combo box is no longer
            focused. It also ensures that additional required cleanup
            operations are performed using the superclass and other elements
            associated with the combo box.
            """

            self._current_combo_is_focused = False
            super(BaseComboBox, self._combobox).hidePopup()
            self._combobox.hide()

        self._combobox.hidePopup = _hide_combo_popup
        self._combobox.showPopup = _show_combo_popup

    @property
    def combobox(self) -> BaseComboBox:
        """The combobox associated with this widget."""

        return self._combobox

    def enterEvent(self, event: QEnterEvent):
        """Handle the event triggered when the mouse enters the widget area.

        Args:
            event: The event object containing details of the mouse entering
                the widget.
        """

        super().enterEvent(event)

        if self._enable_enter_leave_popup:
            self._combobox.show()

    def leaveEvent(self, event):
        """Handle the leave event for the widget.

        Args:
            event: The event object containing details of the leave event.
        """

        super().leaveEvent(event)

        if not self._enable_enter_leave_popup:
            return

        if not self._current_combo_is_focused:
            self._combobox.hide()


class PixmapDelegate(QStyledItemDelegate):
    """A delegate for rendering custom pixmap-based visuals in a view."""

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """Paint the cell with a custom appearance for a numeric delegate.

        Render the cell's background with a specific color associated with the
        data in a given model index, provided custom painting conditions are
        met.

        Notes:
            If the custom condition fails, it falls back to the parent class's
            painting mechanism.

        Args:
            painter: `QPainter` instance used for rendering purposes.
            option: `QStyleOptionViewItem` object that specifies options for
                the rendering of the cell.
            index: `QModelIndex` object that represents the model index
                corresponding to the cell to be painted.
        """

        model = index.model()
        icon = model.data(index, role=Qt.DecorationRole)
        if not icon:
            return super().paint(painter, option, index)

        pixmap = icon.pixmap(model.data(index, role=roles.ICON_SIZE_ROLE))
        painter.drawPixmap(option.rect.topLeft(), pixmap)

        color = model.data(index, roles.EDIT_CHANGED_ROLE)
        if color is None:
            return None

        paint_rect(painter, option, color)

        return super().paint(painter, option, index)


class DateColumnDelegate(QStyledItemDelegate):
    def __init__(self, date_format: str = "dd-MM-yyyy", parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._format = date_format

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QDateEdit:
        """Create an editor widget for editing item data in a model-view
        framework.

        Args:
            parent : The parent widget of the editor.
            option: Contains style options for the item being edited.
            index: Refers to the specific item in the model for which the
                editor is being created.

        Returns:
            A configured instance of `QSpinBox` based on the model's
                data roles.
        """

        model = index.model()
        date_edit = QDateEdit(parent=parent)
        date_edit.setDateRange(
            model.data(index, roles.MIN_VALUE_ROLE),
            model.data(index, roles.MAX_VALUE_ROLE),
        )
        date_edit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        date_edit.setDisplayFormat(self._format)
        date_edit.setCalendarPopup(True)

        return date_edit

    def setEditorData(self, editor: QDateEdit, index: QModelIndex):
        """Set the data from the model to the widget before the widget is
        presented to the user for editing.

        Args:
            editor: The editor widget that will be used for data input.
            index: The index in the model that contains the data to be edited.
        """

        value = index.model().data(index, Qt.DisplayRole)
        editor.setDate(value)

    def setModelData(
        self, editor: QDateEdit, model: QAbstractItemModel, index: QModelIndex
    ):
        """Update the model data with the value from the widget at a given
        index.

        Args:
            editor: The widget containing the data to be set in the model.
            model: The model where data will be updated.
            index: The index in the model where the data will be set.
        """

        model.setData(index, editor.date())

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """Paint the cell with a custom appearance for a numeric delegate.

        Render the cell's background with a specific color associated with the
        data in a given model index, provided custom painting conditions are
        met.

        Notes:
            If the custom condition fails, it falls back to the parent class's
            painting mechanism.

        Args:
            painter: `QPainter` instance used for rendering purposes.
            option: `QStyleOptionViewItem` object that specifies options for
                the rendering of the cell.
            index: `QModelIndex` object that represents the model index
                corresponding to the cell to be painted.
        """

        super().paint(painter, option, index)

        model = index.model()
        color = model.data(index, roles.EDIT_CHANGED_ROLE)
        if color is None:
            return None

        return paint_rect(painter, option, color)
