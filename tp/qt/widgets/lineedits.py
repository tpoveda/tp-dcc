from __future__ import annotations

import os
import enum
from typing import Any
from functools import partial

from Qt.QtCore import Qt, Signal, QObject, QPoint, QRegularExpression
from Qt.QtWidgets import (
    QWidget,
    QLineEdit,
    QPushButton,
    QAction,
    QFileDialog,
    QHBoxLayout,
    QVBoxLayout,
)
from Qt.QtGui import (
    QIcon,
    QColor,
    QValidator,
    QIntValidator,
    QDoubleValidator,
    QMouseEvent,
    QFocusEvent,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QRegularExpressionValidator,
)

from .. import uiconsts, dpi, contexts, utils as qtutils
from . import labels, menus
from ... import dcc
from ...python import paths


@menus.mixin
class BaseLineEdit(QLineEdit):
    # noinspection GrazieInspection
    """
    A base class for LineEdit widgets.

    Signals:
    textModified: Emitted when the text is modified.
    textChanged: Emitted when the text is changed.
    mousePressed: Emitted when the mouse button is pressed.
    mouseMoved: Emitted when the mouse is moved.
    mouseReleased: Emitted when the mouse button is released.
    """

    textModified = Signal(str)
    textChanged = Signal(str)
    mousePressed = Signal(QMouseEvent)
    mouseMoved = Signal(QMouseEvent)
    mouseReleased = Signal(QMouseEvent)
    leftClicked = Signal()
    middleClicked = Signal()
    rightClicked = Signal()

    def __init__(
        self,
        text: str = "",
        placeholder: str = "",
        tooltip: str = "",
        edit_width: int | None = None,
        fixed_width: int | None = None,
        enable_menu: bool = False,
        parent: QWidget | None = None,
    ):
        """
        Initializes the BaseLineEdit.

        :param text: The initial text.
        :param placeholder: The placeholder.
        :param tooltip: The tooltip.
        :param edit_width: The width of the LineEdit for editing. Defaults to None.
        :param fixed_width: The fixed width of the LineEdit. Defaults to None.
        :param enable_menu: Whether to enable the context menu. Defaults to False.
        :param parent: The parent widget.
        """

        super().__init__(parent)

        self._value: str | None = None
        self._text_changed_before: str | None = None
        self._enter_pressed: bool = False

        self._setup_validator()

        if edit_width:
            self.setFixedWidth(dpi.dpi_scale(edit_width))
        if fixed_width:
            self.setFixedWidth(dpi.dpi_scale(fixed_width))
        self.setPlaceholderText(str(placeholder))
        self.setToolTip(tooltip)

        self.set_value(text)

        self.textEdited.connect(self._on_text_edited)
        self.textModified.connect(self._on_text_modified)
        self.editingFinished.connect(self._on_editing_finished)
        super().textChanged.connect(self._on_text_changed)
        self.returnPressed.connect(self._on_return_pressed)

        self._before_finished = self.value()

        if enable_menu:
            # noinspection PyUnresolvedReferences
            self._setup_menu_class()
            # noinspection PyUnresolvedReferences
            self.leftClicked.connect(partial(self.show_context_menu, Qt.LeftButton))
            # noinspection PyUnresolvedReferences
            self.middleClicked.connect(partial(self.show_context_menu, Qt.MidButton))
            # noinspection PyUnresolvedReferences
            self.rightClicked.connect(partial(self.show_context_menu, Qt.RightButton))
        else:
            # noinspection PyStatementEffect
            self._click_menu = None

    def focusInEvent(self, event: QFocusEvent):
        self._before_finished = self.value()
        super().focusInEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        self.mousePressed.emit(event)
        if not self._click_menu:
            super().mousePressEvent(event)
            return

        for mouse_button, menu in self._click_menu.items():
            if menu and event.button() == mouse_button:
                if mouse_button == Qt.LeftButton:
                    self.leftClicked.emit()
                    return
                elif mouse_button == Qt.MidButton:
                    self.middleClicked.emit()
                    return
                elif mouse_button == Qt.RightButton:
                    self.rightClicked.emit()
                    return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        self.mouseMoved.emit(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.mouseReleased.emit(event)
        super().mouseReleaseEvent(event)

    def value(self) -> Any:
        """
        Returns line edit internal value.

        :return: line edit value.
        """

        return self._value

    def set_value(self, value: Any, update_text: bool = True):
        """
        Updates value of the line edit.

        :param value: line edit value.
        :param update_text: whether to update UI text or only internal text value.
        """

        self._value = value

        if update_text:
            with contexts.block_signals(self):
                self.setText(str(value))

    def set_alphanumeric_validator(self):
        """
        Sets validator that only accepts numbers and letters.
        """

        validator = QRegularExpressionValidator(
            QRegularExpression("[a-zA-Z0-9]+", self)
        )
        self.setValidator(validator)

    def _setup_validator(self):
        """
        Internal function that setup line edit validator.
        It should be overridden by subclasses.
        """

        pass

    def _before_after_state(self) -> tuple[Any, Any]:
        """
        Internal function that returns the before and after state of the line edit.

        :return: before and after state.
        """

        return self._before_finished, self.value()

    def _on_text_edited(self, value: str):
        """
        Internal callback function that is called each time text is edited by the user.
        Updates internal value without updating UI (UI is already updated).

        :param value: new line edit text.
        """

        self.set_value(value, update_text=False)

    def _on_text_modified(self, value: str):
        """
        Internal callback function that is called each time text is modified by the user (on return or switching out of
        the text box).

        Updates internal value without updating UI (UI is already updated).

        :param value: text modified value.
        """

        self.set_value(value, update_text=False)

    def _on_editing_finished(self):
        """
        Internal callback function that is called when text edit if finished.
        """

        before, after = self._before_after_state()
        if before != after and not self._enter_pressed:
            self._before_finished = after
            self.textModified.emit(after)

        self._enter_pressed = False

    def _on_text_changed(self, text: str):
        """
        Internal callback function that is called each time text is changed by the user.

        :param text: new text.
        """

        self._text_changed_before = text

        if not self.hasFocus():
            self._before_finished = text

    def _on_return_pressed(self):
        """
        Internal callback function that is called when return is pressed by the user.
        """

        before, after = self._before_after_state()
        if before != after:
            self.textModified.emit(after)
            self._enter_pressed = True


class IntLineEdit(BaseLineEdit):
    """
    A LineEdit widget for integer input.

    Inherits from BaseLineEdit.
    """

    def __init__(
        self,
        text: str = "",
        placeholder: str = "",
        tooltip: str = "",
        edit_width: int | None = None,
        fixed_width: int | None = None,
        enable_menu: bool = False,
        slide_distance: float = 0.01,
        small_slide_distance: float = 0.001,
        large_slide_distance: float = 0.1,
        scroll_distance: float = 1.0,
        update_on_slide_tick: bool = True,
        parent: QWidget | None = None,
    ):
        """
        Initializes the IntLineEdit.

        :param text: The initial text.
        :param placeholder: The placeholder.
        :param tooltip: The tooltip.
        :param edit_width: The width of the LineEdit for editing. Defaults to None.
        :param fixed_width: The fixed width of the LineEdit. Defaults to None.
        :param enable_menu: Whether to enable the context menu. Defaults to False.
        :param slide_distance: The distance to slide on normal drag. Defaults to 1.0.
        :param small_slide_distance: The distance to slide on small drag. Defaults to 0.1.
        :param large_slide_distance: The distance to slide on large drag. Defaults to 5.0.
        :param scroll_distance: The distance to scroll. Defaults to 1.0.
        :param update_on_slide_tick: If True, updates on tick events. Defaults to False.
        :param parent: The parent widget.
        """

        super().__init__(
            text=text,
            placeholder=placeholder,
            tooltip=tooltip,
            edit_width=edit_width,
            fixed_width=fixed_width,
            enable_menu=enable_menu,
            parent=parent,
        )

        self._mouse_slider = MouseSlider(
            self,
            slide_distance=slide_distance,
            small_slide_distance=small_slide_distance,
            large_slide_distance=large_slide_distance,
            scroll_distance=scroll_distance,
            update_on_tick=update_on_slide_tick,
        )

    @classmethod
    def convert_value(cls, value: Any) -> int:
        """
        Converts given value to a compatible integer line edit value.

        :param value: value to convert.
        :return: float line edit compatible value.
        """

        result = 0
        if value == "0.0" or value == "-":
            return result
        elif value != "":
            try:
                result = int(float(value))
            except ValueError:
                pass

        return result

    @property
    def mouse_slider(self) -> MouseSlider:
        """
        Getter method that returns the mouse slider.

        :return: mouse slider.
        """

        return self._mouse_slider

    def value(self) -> int:
        """
        Overrides `value` function to return the integer value of the line edit.

        :return: integer value of the line edit.
        """

        return super().value() or 0

    def set_value(self, value: int, update_text: bool = True):
        """
        Overrides `set_value` function to set the value of the line edit.

        :param value: value to set.
        :param update_text: whether to update the text. Default is True.
        """


        self._value = self.convert_value(value)
        if update_text:
            self.blockSignals(True)
            self.setText(str(self.value()))
            self.blockSignals(False)

    def _setup_validator(self):
        """
        Overrides `_setup_validator` function to set the line edit validator to an integer validator.
        """

        self.setValidator(QIntValidator())

    # noinspection PyMethodOverriding
    def _on_text_modified(self):
        """
        Overrides `_on_text_modified` function to update the text to the integer value.
        """

        value = self.convert_value(self.value())
        self.blockSignals(True)
        self.setText(str(int(float(value))))
        self.clearFocus()
        self.blockSignals(False)


class FloatLineEdit(BaseLineEdit):
    """
    A LineEdit widget for float input.

    Inherits from BaseLineEdit.
    """

    def __init__(
        self,
        text: str = "",
        placeholder: str = "",
        tooltip: str = "",
        edit_width: int | None = None,
        fixed_width: int | None = None,
        enable_menu: bool = False,
        rounding: int = 3,
        slide_distance: float = 0.01,
        small_slide_distance: float = 0.001,
        large_slide_distance: float = 0.1,
        scroll_distance: float = 1.0,
        update_on_slide_tick: bool = True,
        parent: QWidget | None = None,
    ):
        """
        Initializes the IntLineEdit.

        :param text: The initial text.
        :param placeholder: The placeholder.
        :param tooltip: The tooltip.
        :param edit_width: The width of the LineEdit for editing. Defaults to None.
        :param fixed_width: The fixed width of the LineEdit. Defaults to None.
        :param enable_menu: Whether to enable the context menu. Defaults to False.
        :param rounding: The number of decimal places to round to. Defaults to 3.
        :param slide_distance: The distance to slide on normal drag. Defaults to 1.0.
        :param small_slide_distance: The distance to slide on small drag. Defaults to 0.1.
        :param large_slide_distance: The distance to slide on large drag. Defaults to 5.0.
        :param scroll_distance: The distance to scroll. Defaults to 1.0.
        :param update_on_slide_tick: If True, updates on tick events. Defaults to False.
        :param parent: The parent widget.
        """

        self._rounding = rounding

        super().__init__(
            text=text,
            placeholder=placeholder,
            tooltip=tooltip,
            edit_width=edit_width,
            fixed_width=fixed_width,
            enable_menu=enable_menu,
            parent=parent,
        )

        self._mode: str | None = None
        if dcc.is_maya():
            self._mode = dcc.Maya
        elif dcc.is_blender():
            self._mode = dcc.Blender

        self._mouse_slider = MouseSlider(
            self,
            slide_distance=slide_distance,
            small_slide_distance=small_slide_distance,
            large_slide_distance=large_slide_distance,
            scroll_distance=scroll_distance,
            update_on_tick=update_on_slide_tick,
        )

    @classmethod
    def convert_value(cls, value: Any) -> float:
        """
        Converts given value to a compatible float line edit value.

        :param Any value: value to convert.
        :return: float line edit compatible value.
        :rtype: float
        """

        result = 0.0
        if value == ".":
            return result
        elif value != "":
            try:
                result = float(value)
            except ValueError:
                pass

        return result

    @property
    def mouse_slider(self) -> MouseSlider:
        """
        Getter method that returns the mouse slider.

        :return: mouse slider.
        """

        return self._mouse_slider

    @property
    def rounding(self) -> int:
        """
        Getter method that returns the rounding value.

        :return: rounding value.
        """

        return self._rounding

    @rounding.setter
    def rounding(self, value: int):
        """
        Setter method that sets the rounding value.

        :param value: rounding value.
        """

        self._rounding = value

    def focusInEvent(self, event: QFocusEvent):
        """
        Overrides `focusInEvent` function to select all text when the line edit is focused.

        :param event: Qt focus event.
        """

        if self._mode == dcc.Blender:
            self.blockSignals(True)
            self.setText(str(self.value()))
            self.setFocus()
            self.selectAll()
            self.blockSignals(False)
        super().focusInEvent(event)

    def focusOutEvent(self, event: QFocusEvent):
        """
        Overrides `focusOutEvent` function to update the text to the float value when the line edit loses focus.

        :param event: Qt focus event.
        """

        self._on_text_modified()
        super().focusOutEvent(event)

    def clearFocus(self):
        """
        Overrides `clearFocus` function to update the text to the float value when the line edit loses focus.
        """

        super().clearFocus()
        self.setText(str(round(self.value(), self._rounding)))

    def value(self) -> float:
        """
        Overrides `value` function to return the float value of the line edit.
        """

        return super().value() or 0.0

    def set_value(self, value: float, update_text: bool = True):
        """
        Overrides `set_value` function to set the value of the line edit.

        :param value: value to set.
        :param update_text: whether to update the text. Default is True.
        """

        self._value = self.convert_value(value)
        if update_text:
            self.blockSignals(True)
            self.setText(str(round(self.value(), self._rounding)))
            self.blockSignals(False)

    def _setup_validator(self):
        """
        Overrides `_setup_validator` function to set the line edit validator to a float validator.
        """

        self.setValidator(QDoubleValidator())

    # noinspection PyMethodOverriding
    def _on_text_modified(self):
        """
        Internal callback function that is called each time text is modified by the user (on return or switching out of
        """

        value = self.convert_value(self.value())
        self.blockSignals(True)
        self.setText(str(round(value, self._rounding)))
        self.clearFocus()
        self.blockSignals(False)

    def _before_after_state(self) -> tuple[Any, Any]:
        """
        Overrides `_before_after_state` function to return the before and after state of the line edit.

        :return: before and after state.
        """

        before_finished, value = super()._before_after_state()
        return float(before_finished), float(value)


class FolderLineEdit(BaseLineEdit):
    """
    Custom QLineEdit with drag and drop behaviour for files and folders
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self.setDragEnabled(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        Overrides base QLineEdit dragEnterEvent function.

        :param event: Qt drag enter event.
        """

        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == "file":
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent):
        """
        Overrides base QLineEdit dragMoveEvent function.

        :param event: Qt drag move event.
        """

        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == "file":
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """
        Overrides base QLineEdit dropEvent function.

        :param event: Qt drop event.
        """

        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == "file":
            self.setText(urls[0].toLocalFile())


class FileSystemPathLineEdit(QLineEdit):
    """
    Custom QLineEdit that provides a file system path line edit with browse and clear actions.
    """

    class DialogType(enum.Enum):
        """Enumerator that defines available path dialog types."""

        Load = "load"
        Save = "save"

    class Type(enum.Enum):
        """Enumerator that defines available file system path types."""

        File = "file"
        Directory = "directory"

    def __init__(
        self,
        path_type: Type,
        dialog_type: DialogType | None = None,
        path_filter: str = "",
        validate_path: bool = False,
        path_description: str | None = None,
        parent: QWidget | None = None,
    ):
        """Constructor.

        :param path_type: type of path.
        :param dialog_type: optional enumerator that specifies which type of dialog to construct.
        :param path_filter: QFileDialog supported file type filter.
        :param validate_path: whether to validate directory. If True, and path is not valid, an error message will be
            triggerd on the widget.
        :param path_description: optional path description.
        :param parent: optional parent widget.
        """

        super().__init__(parent=parent)

        all_path_types = (
            FileSystemPathLineEdit.Type.File,
            FileSystemPathLineEdit.Type.Directory,
        )
        if path_type not in all_path_types:
            raise ValueError(
                f'Invalid path type {path_type}. Supported path types are {", ".join(map(str, all_path_types))}'
            )

        self._path_type = path_type
        self._dialog_type = dialog_type or FileSystemPathLineEdit.DialogType.Load
        self._path_filter = path_filter
        self._validate_path = validate_path
        self._path_description = path_description or self._path_type.value.title()
        self._error_message: str | None = None

        if self._path_type == FileSystemPathLineEdit.Type.File:
            browse_icon_key = (
                "save"
                if self._dialog_type == FileSystemPathLineEdit.DialogType.Save
                else "file"
            )
        else:
            browse_icon_key = "folder"
        self._browse_action = QAction(parent=self)
        self._browse_action.setIcon(
            QIcon(paths.canonical_path(f"../../resources/icons/{browse_icon_key}.svg"))
        )
        self._clear_action = QAction()
        self._clear_action.setIcon(
            QIcon(paths.canonical_path("../../resources/icons/close.png"))
        )
        self.addAction(self._clear_action, QLineEdit.TrailingPosition)
        self.addAction(self._browse_action, QLineEdit.TrailingPosition)
        self._clear_action.setVisible(False)

        self._browse_action.triggered.connect(self._on_browse_action_triggered)
        self._clear_action.triggered.connect(self._on_clear_action_triggered)
        self.textChanged.connect(self._on_text_changed)

        self.setMouseTracking(True)
        self.setPlaceholderText(self._path_description or "")

    @property
    def path_type(self) -> Type:
        """
        Getter method that returns the path type.

        :return: path type.
        """

        return self._path_type

    @property
    def path_filter(self) -> str:
        """
        Getter method that returns the path filter.

        :return: path filter.
        """

        return self._path_filter

    @path_filter.setter
    def path_filter(self, value: str):
        """
        Setter method that sets the path filter.

        :param value: path filter.
        """

        self._path_filter = value

    @property
    def path_description(self) -> str:
        """
        Getter method that returns the path description.

        :return: path description.
        """

        return self._path_description

    @path_description.setter
    def path_description(self, value: str):
        """
        Setter method that sets the path description.

        :param value: path description.
        :return:
        """

        self._path_description = value
        if self._path_description is not None:
            self.setPlaceholderText(self._path_description)

    @property
    def validate_path(self) -> bool:
        """
        Getter method that returns whether to validate directory.

        :return: whether to validate directory.
        """

        return self._validate_path

    @validate_path.setter
    def validate_path(self, flag: bool):
        """
        Setter method that sets whether to validate directory.

        :param flag: whether to validate directory.
        :return:
        """

        self._validate_path = flag
        self._do_validate_path()

    @property
    def error_message(self) -> str:
        """
        Getter method that returns the error message.

        :return: error message.
        """

        return self._error_message or ""

    def setText(self, text: str) -> None:
        """
        Overrides base QLineEdit setText function.

        :param text: new text
        """

        self._clear_action.setVisible(True if text else False)
        super().setText(text)

    def has_error(self) -> bool:
        """
        Returns whether current path is valid.

        :return: whether current path is valid.
        """

        return self._error_message is not None

    def _do_validate_path(self, path: str | None = None):
        """
        Internal function that validates given path.

        :param path: path to validate. If not given, current line edit text will be used.
        """

        path = path or self.text()
        self._error_message = None
        if path and self._validate_path:
            if not os.path.exists(path):
                self._error_message = f'Path "{path}" does not exist.'
            elif (
                self._path_type == FileSystemPathLineEdit.Type.File
                and not os.path.isfile(path)
                or self._path_type == FileSystemPathLineEdit.Type.Directory
                and not os.path.isdir(path)
            ):
                self._error_message = (
                    f'Path "{path}" is not a valid {self._path_type.value}'
                )

        if self._error_message is not None:
            self.setStyleSheet(
                "QLineEdit { color: " + QColor(Qt.red).lighter(125).name() + "}"
            )
            self.setToolTip(self._error_message)
        else:
            self.setStyleSheet("")
            self.setToolTip(self._path_description)

    def _on_browse_action_triggered(self):
        """
        Internal callback function that is called when Browse action is triggered by the user.
        """

        current_path = self.text()
        caption = f"Choose {self._path_description}"
        if self._path_type == FileSystemPathLineEdit.Type.File:
            if self._dialog_type == FileSystemPathLineEdit.DialogType.Save:
                new_path, _ = QFileDialog.getSaveFileName(
                    self, caption, os.path.dirname(current_path), self._path_filter
                )
            else:
                default_path = (
                    current_path
                    if self._validate_path
                    else os.path.dirname(current_path)
                )
                new_path, _ = QFileDialog.getOpenFileName(
                    self, caption, default_path, self._path_filter
                )
        else:
            new_path = QFileDialog.getExistingDirectory(self, caption, current_path)

        if new_path and new_path != current_path:
            self.setText(new_path)

    def _on_clear_action_triggered(self):
        """
        Internal callback function that is called when Clear action is triggered by the user.
        """

        self.setText("")

    def _on_text_changed(self, path: str):
        """
        Internal callback function that is called each timeline edit text changes.
        Validates path during edit.

        :param path: line edit text.
        """

        self._do_validate_path(path)


class UpperCaseValidator(QValidator):
    """
    Custom Qt validator that keeps the text upper case.
    """

    # noinspection PyTypeChecker
    def validate(self, arg__1: str, arg__2: int) -> QValidator.State:
        return QValidator.Acceptable, arg__1.upper(), arg__2


class EditableLineEditOnClick(QLineEdit):
    """
    Custom QLineEdit that becomes editable on click or double click.
    """

    def __init__(
        self,
        text: str,
        single: bool = False,
        double: bool = True,
        pass_through_clicks: bool = True,
        upper: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(text, parent=parent)

        self._upper = upper
        self._validator = UpperCaseValidator()

        if upper:
            self.setValidator(self._validator)
            self.setText(text)

        self.setReadOnly(True)
        self._editing_style = self.styleSheet()
        self._default_style = "QLineEdit {border: 0;}"
        self.setStyleSheet(self._default_style)
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.setProperty("clearFocus", True)

        if single:
            self.mousePressEvent = self.edit_event
        else:
            if pass_through_clicks:
                self.mousePressEvent = self.mouse_click_pass_through
        if double:
            self.mouseDoubleClickEvent = self.edit_event
        else:
            if pass_through_clicks:
                self.mouseDoubleClickEvent = self.mouse_click_pass_through

        self.editingFinished.connect(self._on_editing_finished)

    def setText(self, text: str):
        if self._upper:
            text = text.upper()

        super().setText(text)

    def focusOutEvent(self, event: QFocusEvent):
        super().focusOutEvent(event)
        self._edit_finished()

    def mousePressEvent(self, event: QMouseEvent):
        event.ignore()

    def mouseReleaseEvent(self, event: QMouseEvent):
        event.ignore()

    def edit_event(self, event: QMouseEvent):
        """
        Internal function that overrides mouse press/release event behaviour.

        :param event: Qt mouse event.
        """

        self.setStyleSheet(self._editing_style)
        self.selectAll()
        self.setReadOnly(False)
        self.setFocus()
        event.accept()

    @staticmethod
    def mouse_click_pass_through(event: QMouseEvent):
        """
        Internal function that overrides mouse press/release event behaviour to pass through the click.

        :param event: Qt mouse event.
        """

        event.ignore()

    def _edit_finished(self):
        """
        Internal function that exits from the edit mode.
        """

        self.setReadOnly(True)
        self.setStyleSheet(self._default_style)
        self.deselect()

    def _on_editing_finished(self):
        """
        Internal callback function that is called when line edit text is changed.
        """

        self._edit_finished()


class StringLineEditWidget(QWidget):
    """
    Base class that creates a label, a text box to edit and an optional button.
    """

    textChanged = Signal(str)
    textModified = Signal(str)
    editingFinished = Signal()
    returnPressed = Signal()
    mousePressed = Signal(QMouseEvent)
    mouseMoved = Signal(QMouseEvent)
    mouseReleased = Signal(QMouseEvent)
    buttonClicked = Signal()

    def __init__(
        self,
        label: str = "",
        text: str = "",
        placeholder_text: str = "",
        button_text: str | None = None,
        edit_width: int | None = None,
        tooltip: str = "",
        orientation: Qt.AlignmentFlag = Qt.Horizontal,
        label_ratio: int = 1,
        edit_ratio: int = 5,
        button_ratio: int = 1,
        parent: QWidget | None = None,
    ):
        super().__init__(parent=parent)

        self._label: str | None = None
        self._label: labels.BaseLabel | None = None
        self._button: QPushButton | None = None

        self._layout = QHBoxLayout() if orientation == Qt.Horizontal else QVBoxLayout()
        self._layout.setSpacing(uiconsts.SPACING)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        self._line_edit = self._setup_line_edit(
            text, placeholder_text, tooltip, edit_width, parent
        )

        if label:
            self._label = labels.BaseLabel(text=label, tooltip=tooltip, parent=parent)
            self._layout.addWidget(self._label, label_ratio)

        self._layout.addWidget(self._line_edit, edit_ratio)

        if button_text:
            self._button = QPushButton(button_text, parent=parent)
            self._layout.addWidget(self._button, button_ratio)

        self._setup_signals()

    def setDisabled(self, flag: bool):
        self._line_edit.setDisabled(flag)
        if self._label:
            self._label.setDisabled(flag)

    def setEnabled(self, flag: bool):
        self._line_edit.setEnabled(flag)
        if self._label:
            self._label.setEnabled(flag)

    # noinspection PyMethodOverriding
    def setFocus(self):
        self._line_edit.setFocus()

    def clearFocus(self):
        self._line_edit.clearFocus()

    def blockSignals(self, b: bool) -> bool:
        result = super().blockSignals(b)
        [child.blockSignals(b) for child in qtutils.iterate_children(self)]
        return result

    def update(self, *args, **kwargs) -> None:
        self._line_edit.update(*args, **kwargs)
        super().update(*args, **kwargs)

    def value(self) -> Any:
        """
        Returns line edit value.

        :return: line edit value.
        """

        return self._line_edit.value()

    def set_value(self, value: Any):
        """
        Sets line edit value.

        :param value: line edit value.
        """

        self._line_edit.set_value(value)

    def set_label(self, label_text: str):
        """
        Sets label text.

        :param label_text: label text.
        """

        if self._label is not None:
            self._label.setText(label_text)

    def set_label_fixed_width(self, width: int):
        """
        Sets fixed with of the label.

        :param width: label fixed with.
        """

        self._label.setFixedWidth(dpi.dpi_scale(width))

    def text(self) -> str:
        """Returns line edit text.

        :return: line edit text.
        """

        return self._line_edit.text()

    def set_text(self, value: str):
        """
        Sets line edit text.

        :param value: line edit text.
        """

        self._line_edit.setText(str(value))

    def set_text_fixed_width(self, width: int):
        """
        Sets fixed with of the line edit.

        :param width: line edit fixed with.
        """

        self._line_edit.setFixedWidth(dpi.dpi_scale(width))

    def set_placeholder_text(self, placeholder_text: str):
        """
        Sets line edit placeholder text.

        :param placeholder_text: line edit placeholder text.
        """

        self._line_edit.setPlaceholderText(placeholder_text)

    def select_all(self):
        """
        Selects all the text within line edit.
        """

        self._line_edit.selectAll()

    def set_validator(self, validator: QValidator):
        """
        Sets line edit validator.

        :param validator: line edit validator.
        """

        self._line_edit.setValidator(validator)

    def _setup_line_edit(
        self,
        text: str,
        placeholder: str,
        tooltip: str,
        edit_width: int | None,
        parent: QWidget | None,
    ) -> BaseLineEdit:
        """
        Internal function that creates the line edit used to edit text.

        :param text: initial line edit text.
        :param placeholder: placeholder text.
        :param tooltip: tooltip text.
        :param edit_width: width of the line edit.
        :param parent: line edit parent widget.
        :return: line edit instance.
        """

        return BaseLineEdit(
            text=text,
            placeholder=placeholder,
            tooltip=tooltip,
            edit_width=edit_width,
            parent=parent,
        )

    def _setup_signals(self):
        """
        Internal function that connect widgets signals.
        """

        self._line_edit.textChanged.connect(self.textChanged.emit)
        self._line_edit.textModified.connect(self.textModified.emit)
        self._line_edit.editingFinished.connect(self.editingFinished.emit)
        self._line_edit.returnPressed.connect(self.returnPressed.emit)
        self._line_edit.mousePressed.connect(self.mousePressed.emit)
        self._line_edit.mouseMoved.connect(self.mouseMoved.emit)
        self._line_edit.mouseReleased.connect(self.mouseReleased.emit)

        if self._button is not None:
            self._button.clicked.connect(self.buttonClicked.emit)


class IntLineEditWidget(StringLineEditWidget):
    """
    Line edit that can display integer attributes.
    """

    def __init__(
        self,
        label: str = "",
        text: str = "",
        placeholder_text: str = "",
        button_text: str | None = None,
        edit_width: int | None = None,
        tooltip: str = "",
        orientation: Qt.AlignmentFlag = Qt.Horizontal,
        label_ratio: int = 1,
        edit_ratio: int = 5,
        button_ratio: int = 1,
        parent: QWidget | None = None,
    ):
        super().__init__(
            label=label,
            text=text,
            placeholder_text=placeholder_text,
            button_text=button_text,
            edit_width=edit_width,
            tooltip=tooltip,
            orientation=orientation,
            label_ratio=label_ratio,
            edit_ratio=edit_ratio,
            button_ratio=button_ratio,
            parent=parent,
        )

    def _setup_line_edit(
        self,
        text: str,
        placeholder: str,
        tooltip: str,
        edit_width: int | None,
        parent: QWidget | None,
    ) -> BaseLineEdit:
        return IntLineEdit(
            text=text,
            placeholder=placeholder,
            tooltip=tooltip,
            edit_width=edit_width,
            parent=parent,
        )

    def set_min_value(self, value: int):
        """
        Sets line edit minimum value.

        :param value: minimum value.
        """

        # noinspection PyTypeChecker
        validator: QIntValidator = self._line_edit.validator()
        validator.setBottom(value)

    def set_max_value(self, value: int):
        """
        Sets line edit maximum value.

        :param value: maximum value.
        """

        # noinspection PyTypeChecker
        validator: QIntValidator = self._line_edit.validator()
        validator.setTop(value)


class FloatLineEditWidget(StringLineEditWidget):
    """
    Line edit that can display float attributes.
    """

    def __init__(
        self,
        label: str = "",
        text: str = "",
        placeholder_text: str = "",
        button_text: str | None = None,
        edit_width: int | None = None,
        tooltip: str = "",
        orientation: Qt.AlignmentFlag = Qt.Horizontal,
        label_ratio: int = 1,
        edit_ratio: int = 5,
        button_ratio: int = 1,
        rounding: int = 3,
        parent: QWidget | None = None,
    ):
        self._rounding = rounding

        super().__init__(
            label=label,
            text=text,
            placeholder_text=placeholder_text,
            button_text=button_text,
            edit_width=edit_width,
            tooltip=tooltip,
            orientation=orientation,
            label_ratio=label_ratio,
            edit_ratio=edit_ratio,
            button_ratio=button_ratio,
            parent=parent,
        )

    def _setup_line_edit(
        self,
        text: str,
        placeholder: str,
        tooltip: str,
        edit_width: int | None,
        parent: QWidget | None,
    ) -> BaseLineEdit:
        return FloatLineEdit(
            text=text,
            placeholder=placeholder,
            tooltip=tooltip,
            edit_width=edit_width,
            rounding=self._rounding,
            parent=parent,
        )

    def set_min_value(self, value: float):
        """
        Sets line edit minimum value.

        :param value: minimum value.
        """

        # noinspection PyTypeChecker
        validator: QDoubleValidator = self._line_edit.validator()
        validator.setBottom(value)

    def set_max_value(self, value: float):
        """
        Sets line edit maximum value.

        :param value: maximum value.
        """

        # noinspection PyTypeChecker
        validator: QDoubleValidator = self._line_edit.validator()
        validator.setTop(value)


class MouseSlider(QObject):
    """
    Signals:
        tickEvent (Signal): Emitted when a tick event occurs.
        deltaChanged (Signal): Emitted when the delta value changes.
        sliderStarted (Signal): Emitted when the slider starts moving.
        sliderChanged (Signal): Emitted when the slider value changes.
        sliderFinished (Signal): Emitted when the slider stops moving.
    """

    tickEvent = Signal(object)
    deltaChanged = Signal(object)
    sliderStarted = Signal()
    sliderChanged = Signal(object)
    sliderFinished = Signal(object)

    def __init__(
        self,
        parent_edit: BaseLineEdit,
        slide_distance: float = 1.0,
        small_slide_distance: float = 0.1,
        large_slide_distance: float = 5.0,
        scroll_distance: float = 1.0,
        update_on_tick: bool = False,
    ):
        """
        Initializes the MouseSlider.

        :param parent_edit: The parent line edit widget.
        :param slide_distance: The distance to slide on normal drag. Defaults to 1.0.
        :param small_slide_distance: The distance to slide on small drag. Defaults to 0.1.
        :param large_slide_distance: The distance to slide on large drag. Defaults to 5.0.
        :param scroll_distance: The distance to scroll. Defaults to 1.0.
        :param update_on_tick: If True, updates on tick events. Defaults to False.
        """

        super().__init__()

        self._edit = parent_edit
        self._update_on_tick = update_on_tick
        self._slide_distance = slide_distance
        self._small_slide_distance = small_slide_distance
        self._large_slide_distance = large_slide_distance
        self._scroll_distance = scroll_distance
        self._press_pos: QPoint | None = None
        self._start_value = 0
        self._mouse_delta = 0
        self._delta_x = 0
        self._prev_delta_x = 0
        self._enabled = True

        self._setup_signals()

    @property
    def update_on_tick(self) -> bool:
        """
        Getter method that returns whether to update on tick events.

        :return: True if updates on tick events; False otherwise.
        """

        return self._update_on_tick

    @update_on_tick.setter
    def update_on_tick(self, flag: bool):
        """
        Setter method that sets whether to update on tick events.

        :param flag: True to update on tick events; False otherwise.
        """

        self._update_on_tick = flag

    @property
    def slide_distance(self) -> float:
        """
        Getter method that returns the distance to slide on normal drag.

        :return: distance to slide on normal drag.
        """

        return self._slide_distance

    @slide_distance.setter
    def slide_distance(self, value: float):
        """
        Setter method that sets the distance to slide on normal drag.

        :param value: distance to slide on normal drag.
        """

        self._slide_distance = value

    @property
    def small_slide_distance(self) -> float:
        """
        Getter method that returns the distance to slide on small drag.

        :return: distance to slide on small drag.
        """

        return self._small_slide_distance

    @small_slide_distance.setter
    def small_slide_distance(self, value: float):
        """
        Setter method that sets the distance to slide on small drag.

        :param value: distance to slide on small drag.
        """

        self._small_slide_distance = value

    @property
    def large_slide_distance(self) -> float:
        """
        Getter method that returns the distance to slide on large drag.

        :return: distance to slide on large drag.
        """

        return self._large_slide_distance

    @large_slide_distance.setter
    def large_slide_distance(self, value: float):
        """
        Setter method that sets the distance to slide on large drag.

        :param value: distance to slide on large drag.
        """

        self._large_slide_distance = value

    @property
    def scroll_distance(self) -> float:
        """
        Getter method that returns the distance to scroll.

        :return: distance to scroll.
        """

        return self._scroll_distance

    @scroll_distance.setter
    def scroll_distance(self, value: float):
        """
        Setter method that sets the distance to scroll.

        :param value: distance to scroll.
        """

        self._scroll_distance = value

    def set_enabled(self, flag: bool):
        """
        Sets whether slider is enabled.

        :param flag: True to enable the slider; False to disable it.
        """

        self._enabled = flag

    def tick(self, delta: float):
        """
        Runs slider tick.

        :param delta: delta value.
        """

        if not self._enabled:
            return

        value = self._start_value + float(delta)
        self._edit.set_value(value)
        self._edit.update()

        if self._update_on_tick:
            self._edit.textChanged.emit(self._edit.text())
            self._edit.textModified.emit(self._edit.text())
            self.sliderChanged.emit(self._edit.text())

    def _setup_signals(self):
        """
        Internal function that handles the connection of the signals for this object.
        """

        self._edit.mouseMoved.connect(self._on_mouse_moved)
        self._edit.mousePressed.connect(self._on_mouse_pressed)
        self._edit.mouseReleased.connect(self._on_mouse_released)

    def _on_mouse_moved(self, event: QMouseEvent):
        """
        Internal callback function that is called each time mouseMoved event signal from QLineEdit is emitted.

        :param event: Qt mouse event.
        """

        if not self._enabled:
            return

        if self._press_pos:
            self._mouse_delta = event.pos().x() - self._press_pos.x()
            if self._mouse_delta % self._scroll_distance == 0:
                self._delta_x = self._mouse_delta / self._scroll_distance
                if self._delta_x != self._prev_delta_x:
                    self.deltaChanged.emit(self._delta_x - self._prev_delta_x)
                    ctrl_pressed = int(
                        event.modifiers() == Qt.KeyboardModifier.ControlModifier
                    )
                    shift_pressed = int(
                        event.modifiers() == Qt.KeyboardModifier.ShiftModifier
                    )
                    if ctrl_pressed:
                        self.tickEvent.emit(self._delta_x * self._small_slide_distance)
                    elif shift_pressed:
                        self.tickEvent.emit(self._delta_x * self._large_slide_distance)
                    else:
                        self.tickEvent.emit(self._delta_x * self._slide_distance)
                self._prev_delta_x = self._delta_x

    def _on_mouse_pressed(self, event: QMouseEvent):
        """
        Internal callback function that is called each time mousePressed event signal from QLineEdit is emitted.

        :param event: Qt mouse event.
        """

        if not self._enabled:
            return

        if event.button() == Qt.MiddleButton:
            self._press_pos = event.pos()
            self._start_value = self._edit.value()
            self.sliderStarted.emit()

    def _on_mouse_released(self, event: QMouseEvent):
        """
        Internal callback function that is called each time mouseReleased event signal from QLineEdit is emitted.

        :param event: Qt mouse event.
        """

        if not self._enabled:
            return

        if event.button() == Qt.MiddleButton:
            self._press_pos = None
            self._edit.set_value(self._edit.value())
            self._edit.textChanged.emit(self._edit.text())
            self._edit.textModified.emit(self._edit.text())
            self.sliderFinished.emit()
