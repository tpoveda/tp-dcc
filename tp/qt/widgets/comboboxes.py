from __future__ import annotations

from typing import Sequence, Any

from ...externals.Qt.QtCore import Qt, Signal
from ...externals.Qt.QtWidgets import QSizePolicy, QWidget, QLabel, QComboBox
from ...externals.Qt.QtGui import QIcon, QKeyEvent, QWheelEvent
from .. import uiconsts, dpi
from . import layouts, labels


class BaseComboBox(QComboBox):
    """
    A base class for ComboBox widgets.

    Signals:
    itemSelected (str): Emitted when an item is selected in the ComboBox.
    checkStateChanged (int, int): Emitted when the check state of an item changes.
    """

    itemSelected = Signal(str)
    checkStateChanged = Signal(int, int)

    def __init__(self, items: list[str] | None = None, parent: QWidget | None = None):
        """
        Initializes the BaseComboBox.

        :param items: A list of items to populate the ComboBox with. Defaults to None.
        :param parent: The parent widget. Defaults to None.
        """

        super().__init__(parent)

        if items:
            self.addItems(items)

        self._is_checkable = False

        self.setEditable(True)

    def keyPressEvent(self, event: QKeyEvent):
        """
        Handles key press events.

        This method handles key press events.

        :param event: The key event.
        """

        super().keyPressEvent(event)

        if event.key() == Qt.Key_Escape:
            self.close()
            self.parent().setFocus()
        elif event.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.itemSelected.emit(self.currentText())
            self.parent().setFocus()

    def addItem(self, icon: QIcon | str | None, text: str = '', user_data: Any = ..., is_checkable: bool = False):
        """
        Adds an item to the ComboBox.

        This method adds an item to the ComboBox.

        :param icon: The icon associated with the item. Can be a QIcon object, a string representing the icon file path,
                     or None if no icon is desired. Defaults to None.
        :param text: The text of the item. Defaults to an empty string.
        :param user_data: Additional data associated with the item. Defaults to Ellipsis.
        :param is_checkable: True if the item is checkable, False otherwise. Defaults to False.
        """

        if not icon:
            super().addItem(text, userData=user_data)
        elif isinstance(icon, str):
            super().addItem(icon, userData=user_data)
        else:
            super().addItem(icon, text, user_data)

        model = self.model()
        # noinspection PyUnresolvedReferences
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

    def wheelEvent(self, e: QWheelEvent) -> None:
        e.ignore()


class ComboBoxAbstractWidget(QWidget):
    """
    A base class for ComboBox widgets.

    This class serves as a base for ComboBox widgets.
    """

    class ComboItemChangedEvent:
        """
        A class representing a ComboItemChanged event.

        This class represents an event that occurs when a combo box item is changed.
        """

        def __init__(self, previous_index: int, current_index: int, parent: ComboBoxAbstractWidget):

            self._previous_index = previous_index
            self._index = current_index
            self._parent = parent

        @property
        def text(self) -> str:
            """
            Gets the text associated with the event.

            This property returns the text associated with the ComboItemChanged event.

            :return: The text associated with the event.
            """

            return self._parent.item_text(self._index)

        @property
        def prev_text(self) -> str:
            """
            Gets the previous text associated with the event.

            This property returns the previous text associated with the ComboItemChanged event.

            :return: The previous text associated with the event.
            """

            return self._parent.item_text(self._previous_index)

        @property
        def data(self) -> Any:
            """
            Gets the data associated with the event.

            This property returns the data associated with the ComboItemChanged event.

            :return: The data associated with the event.
            """

            return self._parent.item_data(self._index)

        @property
        def prev_data(self) -> Any:
            """
            Gets the previous data associated with the event.

            This property returns the previous data associated with the ComboItemChanged event.

            :return: The previous data associated with the event.
            """

            return self._parent.item_data(self._previous_index)

        @property
        def index(self) -> int:
            """
            Gets the index associated with the event.

            This property returns the index associated with the ComboItemChanged event.

            :return: The index associated with the event.
            """

            return self._index

    itemChanged = Signal(ComboItemChangedEvent)

    PREV_INDEX = None

    def __init__(self, parent: QWidget | None = None):
        """
        Initializes the ComboBoxAbstractWidget.

        :param parent: parent widget. Defaults to None.
        """
        super().__init__(parent)

        self._label: QLabel | None = None
        self._box: QComboBox | None = None

    def __getattr__(self, item):
        if hasattr(self._box, item):
            return getattr(self._box, item)

    def blockSignals(self, flag: bool):
        self._box.blockSignals(flag)
        if self._label:
            self._label.blockSignals(flag)
        super().blockSignals(flag)

    def add_item(self, item: str, sort_alphabetically: bool = False, user_data: Any = None):
        """
        Adds an item to the combobox with the given text and containing the given user data.

        :param item: name to add to the combo box.
        :param sort_alphabetically: whether to sort the full combo box alphabetically after adding the item.
        :param user_data: optional user data to set.
        """

        self._box.addItem(item, userData=user_data)
        if sort_alphabetically:
            self._box.model().sort(0)

    def add_items(self, items: list[str], sort_alphabetically: bool = False):
        """
        Adds given items to the combobox.

        :param items: names to add to the combo box.
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
        """

        return int(self._box.currentIndex())

    def set_index(self, index: int, quiet: bool = False):
        """
        Sets current combo box index.

        :param index: index to set.
        :param quiet: whether combo box should emit signals.
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
        """

        return self._box.itemText(index)

    def set_item_text(self, index: int, text: str):
        """
        Sets the text of the item at given index.

        :param index: index of the item we want to set text of.
        :param text: item text.
        """

        self._box.setItemText(index, text)

    def current_text(self) -> str:
        """
        Returns the current selected item text.

        :return: current item text.
        """

        return self._box.currentText()

    def set_to_text(self, text: str, flags: Qt.MatchFlags = Qt.MatchFixedString):
        """
        Sets the index based on given text.

        :param text: text to search and switch the combo box to.
        :param Qt.MatchFlags flags: optional match flags.
        """

        index = self._box.findText(text, flags)
        if index >= 0:
            self.setCurrentIndex(index)

    def item_data(self, index: int, role: Qt.ItemDataRole = Qt.UserRole) -> Any:
        """
        Returns the data of the combo box item located at given index and with given data role.

        :param index: combo box item index to get data for.
        :param role: role of the data to get.
        :return: item data.
        """

        return self._box.itemData(index, role)

    def current_data(self, role: Qt.ItemDataRole = Qt.UserRole) -> Any:
        """
        Returns the data of the current selected combo box item.

        :param role: role of the data to get.
        :return: item data.
        """

        return self._box.currentData(role)

    def set_item_data(self, index: int, value: Any):
        """
        Sets the data of the item at given index.

        :param index: index to assign data to.
        :param value: data to assign.
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
            self, label: str = '', items: Sequence[str] | None = None, label_ratio: int | None = None,
            box_ratio: int | None = None, tooltip: str = '', set_index: int = 0, sort_alphabetically: bool = False,
            margins: tuple[int, int, int, int] = (0, 0, 0, 0), spacing: int = uiconsts.SMALL_SPACING,
            box_min_width: int | None = None, item_data: Sequence[Any] | None = None,
            support_middle_mouse_scroll: bool = True, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._box = BaseComboBox(items=items)

        if not support_middle_mouse_scroll:
            self._box = NoWheelComboBox(parent)
        else:
            self._box = BaseComboBox(parent)

        if sort_alphabetically:
            self._box.setInsertPolicy(QComboBox.InsertAlphabetically)
            if items:
                items = [str(x) for x in list(items)]
                items.sort(key=lambda x: x.lower())
        if item_data:
            for i, item in enumerate(items):
                self._box.addItem(item, item_data[i])
        else:
            self._box.addItems(items)
        self._box.setToolTip(tooltip)
        if set_index:
            self._box.setCurrentIndex(set_index)

        layout = layouts.horizontal_layout(margins=margins, spacing=spacing, parent=self)
        if label:
            self._label = labels.BaseLabel(label, tooltip=tooltip, parent=parent)
            layout.addWidget(self._label, label_ratio) if label_ratio else layout.addWidget(self._label)
            self._box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self._box, box_ratio) if box_ratio else layout.addWidget(self._box)
        if box_min_width:
            self._box.setMinimumWidth(dpi.dpi_scale(box_min_width))
        self._box.currentIndexChanged.connect(self.on_item_changed)

    @property
    def label(self) -> labels.BaseLabel:
        """
        Getter method that returns label associated the combobox.

        :return: combobox label.
        """

        return self._label
