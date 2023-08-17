from __future__ import annotations

from typing import Iterable, Any

from overrides import override
from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QSizePolicy, QWidget, QLabel, QComboBox
from Qt.QtGui import QIcon, QKeyEvent, QWheelEvent

from tp.common.python import helpers
from tp.common.qt import consts, dpi
from tp.common.qt.widgets import layouts, labels


def combobox(
        items: Iterable = (), item_data: Iterable[list[Any]] = (), placeholder_text: str = '',
        tooltip: str = '', set_index: int = 0, sort_alphabetically: bool = True,
        support_middle_mouse_scroll: bool = True, parent: QWidget | None = None) -> BaseComboBox:
    """
    Creates a basic QComboBox widget.

    :param Iterable[str] items: list of items to add into the combo box.
    :param Iterable[list[str]] items: list of items data to add into the combo box.
    :param str placeholder_text: placeholder_text optional placeholder text.
    :param str tooltip: combo box tooltip.
    :param int set_index: initial combo box index.
    :param QWidget or None parent: optional parent widget.
    :param bool sort_alphabetically: whether combo box items should be ordered alphabetically.
    :param bool support_middle_mouse_scroll: whether middle mouse scroll should be supported.
    :return: newly created combo box.
    :rtype: QComboBox
    """

    if not support_middle_mouse_scroll:
        combo_box = NoWheelComboBox(parent)
    else:
        combo_box = BaseComboBox(parent)

    if sort_alphabetically:
        combo_box.setInsertPolicy(QComboBox.InsertAlphabetically)
        if items:
            items = [str(x) for x in list(items)]
            items.sort(key=lambda x: x.lower())
    if item_data:
        for i, item in enumerate(items):
            combo_box.addItem(item, item_data[i])
    else:
        combo_box.addItems(items)
    combo_box.setToolTip(tooltip)
    if placeholder_text:
        combo_box.setPlaceholderText(str(placeholder_text))
    if set_index:
        combo_box.setCurrentIndex(set_index)

    return combo_box


class BaseComboBox(QComboBox):

    itemSelected = Signal(str)
    checkStateChanged = Signal(int, int)

    def __init__(self, items: list[str] | None = None, parent: QWidget | None = None):
        super().__init__(parent)

        self._is_checkable = False

        self.setEditable(True)

    @override
    def keyPressEvent(self, e: QKeyEvent) -> None:
        super().keyPressEvent(e)

        if e.key() == Qt.Key_Escape:
            self.close()
            self.parent().setFocus()
        elif e.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.itemSelected.emit(self.currentText())
            self.parent().setFocus()

    @override(check_signature=False)
    def addItem(self, icon: QIcon | str | None, text: str = '', userData: Any = ..., is_checkable: bool = False) -> None:

        if not icon:
            super().addItem(text, userData=userData)
        elif helpers.is_string(icon):
            super().addItem(icon, userData=userData)
        else:
            super().addItem(icon, text, userData)

        model = self.model()
        item = model.item(model.rowCount() - 1, 0)
        if item and is_checkable:
            self._is_checkable = is_checkable
            item.setCheckState(Qt.Checked)


class NoWheelComboBox(QComboBox):
    """
    Extended QComboBox class that ignores wheelEvent functionality.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFocusPolicy(Qt.StrongFocus)

    @override
    def wheelEvent(self, e: QWheelEvent) -> None:
        e.ignore()


class ComboBoxAbstractWidget(QWidget):

    class ComboItemChangedEvent:
        def __init__(self, previous_index: int, current_index: int, parent: ComboBoxAbstractWidget):

            self._previous_index = previous_index
            self._index = current_index
            self._parent = parent

        @property
        def text(self) -> str:
            return self._parent.item_text(self._index)

        @property
        def prev_text(self) -> str:
            return self._parent.item_text(self._previous_index)

        @property
        def data(self) -> Any:
            return self._parent.item_data(self._index)

        @property
        def prev_data(self) -> Any:
            return self._parent.item_data(self._previous_index)

        @property
        def index(self) -> int:
            return self._index

    itemChanged = Signal(ComboItemChangedEvent)

    PREV_INDEX = None

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._label = None          # type: QLabel
        self._box = None            # type: QComboBox

    def __getattr__(self, item):
        if hasattr(self._box, item):
            return getattr(self._box, item)

    @override
    def blockSignals(self, b: bool) -> bool:
        self._box.blockSignals(b)
        if self._label:
            self._label.blockSignals(b)
        super().blockSignals(b)

    def add_item(self, item: str, sort_alphabetically: bool = False, user_data: Any = None):
        """
        Adds an item to the combobox with the given text and containing the given user data.

        :param str item: name to add to the combo box.
        :param bool sort_alphabetically: whether to sort the full combo box alphabetically after adding the item.
        :param Any user_data: optional user data to set.
        """

        self._box.addItem(item, userData=user_data)
        if sort_alphabetically:
            self._box.model().sort(0)

    def add_items(self, items: list[str], sort_alphabetically: bool = False):
        """
        Adds given items to the combobox.

        :param list[str] items: names to add to the combo box.
        :param sort_alphabetically: whether to sort the full combo box alphabetically after adding the items.
        """

        self._box.addItems(items)
        if sort_alphabetically:
            self._box.model().sort(0)

    def clear(self):
        """
        Clears all combobox items.
        """

        self._box.clear()

    def current_index(self) -> int:
        """
        Returns the current item index.

        :return: item index.
        :rtype: int
        """

        return int(self._box.currentIndex())

    def set_index(self, index: int, quiet: bool = False):
        """
        Sets current combo box index.

        :param int index: index to set.
        :param bool quiet: whether combo box should emit signals.
        """

        index = index or 0
        if quiet:
            self._box.blockSignals(True)
        self._box.setCurrentIndex(index)
        if quiet:
            self._box.blockSignals(False)

    def item_text(self, index: int) -> str:
        """
        Returns the text of the combo box item located at given index.

        :param index: combo box item index to get text for.
        :return: item text.
        :rtype: str
        """

        return self._box.itemText(index)

    def set_item_text(self, index: int, text: str):
        """
        Sets the text of the item at given index.

        :param int index: index of the item we want to set text of.
        :param str text: item text.
        """

        self._box.setItemText(index, text)

    def current_text(self) -> str:
        """
        Returns the current selected item text.

        :return: current item text.
        :rtype: str
        """

        return self._box.currentText()

    def set_to_text(self, text: str, flags: Qt.MatchFlags = Qt.MatchFixedString):
        """
        Sets the index based on given text.

        :param str text: text to search and switch the combo box to.
        :param Qt.MatchFlags flags: optional match flags.
        """

        index = self._box.findText(text, flags)
        if index >= 0:
            self.setCurrentIndex(index)

    def item_data(self, index: int, role: Qt.ItemDataRole = Qt.UserRole) -> Any:
        """
        Returns the data of the combo box item located at given index and with given data role.

        :param int index: combo box item index to get data for.
        :param Qt.ItemDataRole role: role of the data to get.
        :return: item data.
        :rtype: Any
        """

        return self._box.itemData(index, role)

    def current_data(self, role: Qt.ItemDataRole = Qt.UserRole) -> Any:
        """
        Returns the data of the current selected combo box item.

        :param Qt.ItemDataRole role: role of the data to get.
        :return: item data.
        :rtype: Any
        """

        return self._box.currentData(role)

    def set_item_data(self, index: int, value: Any):
        """
        Sets the data of the item at given index.

        :param int index: index to assign data to.
        :param Any value: data to assign.
        """

        self._box.setItemData(index, value)

    def on_item_changed(self):
        """
        Callback function that is called by internal combo box when current its index changes.
        """

        event = ComboBoxAbstractWidget.ComboItemChangedEvent(
            int(self.PREV_INDEX if self.PREV_INDEX is not None else -1), int(self._box.currentIndex()), parent=self)
        self.itemChanged.emit(event)
        self.PREV_INDEX = self._box.currentIndex()


class ComboBoxRegularWidget(ComboBoxAbstractWidget):
    """
    Standard widget that contains a regular (not searchable) combo box with a label.
    """

    def __init__(
            self, label: str = '', items: Iterable = (), label_ratio: int | None = None, box_ratio: int | None = None,
            tooltip: str = '', set_index: int = 0, sort_alphabetically: bool = False,
            margins: set[int, int, int, int] = (0, 0, 0, 0), spacing: int = consts.SMALL_SPACING,
            box_min_width: int | None = None, item_data: set = (), support_middle_mouse_scroll: bool = True,
            parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._box = combobox(
            items=items, item_data=item_data, set_index=set_index, sort_alphabetically=sort_alphabetically,
            support_middle_mouse_scroll=support_middle_mouse_scroll, tooltip=tooltip, parent=parent)

        layout = layouts.horizontal_layout(margins=margins, spacing=spacing, parent=self)
        if label:
            self._label = labels.label(label, tooltip=tooltip, parent=parent)
            layout.addWidget(self._label, label_ratio) if label_ratio else layout.addWidget(self._label)
            self._box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self._box, box_ratio) if box_ratio else layout.addWidget(self._box)
        if box_min_width:
            self._box.setMinimumWidth(dpi.dpi_scale(box_min_width))
        self._box.currentIndexChanged.connect(self.on_item_changed)

    @property
    def label(self) -> labels.BaseLabel:
        return self._label
