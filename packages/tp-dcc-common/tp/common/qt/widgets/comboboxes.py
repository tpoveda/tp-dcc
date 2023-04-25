#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for custom combo boxes
"""

from Qt.QtCore import Qt, Signal, Property, QPoint, QEvent, QSortFilterProxyModel
from Qt.QtWidgets import QSizePolicy, QWidget, QCompleter, QComboBox

from tp.common.python import helpers
from tp.common.qt import formatters, mixin, dpi
from tp.common.qt.widgets import layouts, labels
from tp.common.resources import theme


def combobox(items=None, placeholder_text=None, parent=None):
    """
    Creates a basic QComboBox widget.

    :param list(str) items: list of items to add into the combo box.
    :param str parent: placeholder_text optional placeholder text.
    :return: newly created combo box.
    :rtype: BaseComboBox
    """

    new_combobox = BaseComboBox(items=items, parent=parent)
    if placeholder_text:
        new_combobox.setPlaceholderText(str(placeholder_text))

    return new_combobox


def searchable_combobox(items=None, parent=None):
    """
    Creates a searchable QComboBox widget.

    :param list(str) items: list of items to add into the combo box.
    :param QWidget parent: parent widget.
    :return: newly created combo box.
    :rtype: SearchableComboBox
    """

    new_combobox = SearchableComboBox(items=items, parent=parent)
    return new_combobox


def combobox_widget(
        text='', items=None, label_ratio=None, box_ratio=None, tooltip='', set_index=0, sort_alphabetically=False,
        spacing=2, margins=(0, 0, 0, 0), box_min_width=None, item_data=None, parent=None):
    """
    Creates a basic combobox widget that contains a QComboBox and a QLabel.
    :param str text: text of the label.
    :param list(str) items: list of combo box it ems.
    :param int label_ratio: ratio of the label within the layout.
    :param int box_ratio: ratio of the combobox within the layout.
    :param str tooltip: label and combobox tooltip.
    :param int set_index: default initial index to set after the addition of the combo box items.
    :param bool sort_alphabetically: whether or not combo box items should be ordered alphabetically.
    :param int spacing: spacing used by the layout where the combobox and label widgets are located.
    :param tuple(float, float, float, float) margins: margins used by the layout where the combobox and label widgets
        are located.
    :param int box_min_width: optional combobox minimum width.
    :param list(object) item_data: custom data to add to each one of the items added into the combo box.
    :param QWidget parent: parent widget.
    :return: newly created base combobox widget.
    :rtype: BaseComboBoxWidget
    """

    new_combobox_widget = BaseComboBoxWidget(
        text=text, items=items, label_ratio=label_ratio, box_ratio=box_ratio, tooltip=tooltip, set_index=set_index,
        sort_alphabetically=sort_alphabetically, spacing=spacing, margins=margins, box_min_width=box_min_width,
        item_data=item_data, parent=parent)
    return new_combobox_widget


def searchable_combobox_widget(
        text='', items=None, label_ratio=None, box_ratio=None, tooltip='', set_index=0, sort_alphabetically=False,
        spacing=2, margins=(0, 0, 0, 0), box_min_width=None, item_data=None, parent=None):
    """
    Creates a searchable combobox widget that contains a QComboBox and a QLabel.

    :param str text: text of the label.
    :param list(str) items: list of combo box it ems.
    :param int label_ratio: ratio of the label within the layout.
    :param int box_ratio: ratio of the combobox within the layout.
    :param str tooltip: label and combobox tooltip.
    :param int set_index: default initial index to set after the addition of the combo box items.
    :param bool sort_alphabetically: whether or not combo box items should be ordered alphabetically.
    :param int spacing: spacing used by the layout where the combobox and label widgets are located.
    :param tuple(float, float, float, float) margins: margins used by the layout where the combobox and label widgets
        are located.
    :param int box_min_width: optional combobox minimum width.
    :param list(object) item_data: custom data to add to each one of the items added into the combo box.
    :param QWidget parent: parent widget.
    :return: newly created base combobox widget.
    :rtype: BaseComboBoxWidget
    """

    new_combobox_widget = SearchableComboBoxWidget(
        text=text, items=items, label_ratio=label_ratio, box_ratio=box_ratio, tooltip=tooltip, set_index=set_index,
        sort_alphabetically=sort_alphabetically, spacing=spacing, margins=margins, box_min_width=box_min_width,
        item_data=item_data, parent=parent)
    return new_combobox_widget


def bool_combobox(state=True, parent=None):
    """
    Creates a bool combobox.

    :param bool state: default boolean combo box state.
    :param QWidget parent: parent widget.
    :return: newly created bool combobox widget.
    :rtype: BoolComboBox
    """

    new_bool_combobox_widget = BoolComboBox(state=state, parent=parent)
    return new_bool_combobox_widget


@theme.mixin
@mixin.dynamic_property
class BaseComboBox(QComboBox, dpi.DPIScaling):

    valueChanged = Signal(list)
    itemSelected = Signal(str)
    checkStateChanged = Signal(str, int)

    def __init__(self, items=None, parent=None):
        super(BaseComboBox, self).__init__(parent)

        self._root_menu = None
        self._display_formatter = formatters.display_formatter
        self._has_custom_view = False
        self._size = self.theme_default_size()

        self.setEditable(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.set_value('')
        self.set_placeholder('Please Select...')

        line_edit = self.lineEdit()
        line_edit.setReadOnly(True)
        line_edit.setTextMargins(4, 0, 4, 0)
        line_edit.installEventFilter(self)

        if items:
            self.addItems(items)

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    def _get_size(self):
        """
        Returns the button height size
        :return: float
        """

        return self._size

    def _set_size(self, value):
        """
        Sets button height size
        :param value: float
        """

        self._size = value
        self.lineEdit().setProperty('theme_size', value)
        self.style().polish(self)

    theme_size = Property(int, _get_size, _set_size)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def eventFilter(self, widget, event):
        """
        Overrides base eventFilter function
        :param widget:
        :param event:
        :return:
        """

        if widget is self.lineEdit():
            if event.type() == QEvent.MouseButtonPress and self.isEnabled():
                self.showPopup()
        return super(BaseComboBox, self).eventFilter(widget, event)

    def showPopup(self):
        """
        Overrides base QComboBox showPopup function.
        If we have a custom menu, we make sure that we show it.
        """

        if self._has_custom_view or self._root_menu is None:
            super(BaseComboBox, self).showPopup()
        else:
            QComboBox.hidePopup(self)
            self._root_menu.popup(self.mapToGlobal(QPoint(0, self.height())))

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_formatter(self, fn):
        """
        Sets the formatter used by combobox.

        :param callable fn: display callable formatter.
        """

        self._display_formatter = fn

    def set_placeholder(self, text):
        """
        Sets the placeholder text that appears when no item is selected.

        :param str text: placeholder text.
        """

        self.lineEdit().setPlaceholderText(text)

    def set_value(self, value):
        """
        Sets combo box value.

        :param object value: combobox value.
        """

        self.setProperty('value', value)

    def set_menu(self, menu):
        """
        Sets combo box custom menu.

        :param QMenu menu: combobox menu.
        """

        self._root_menu = menu
        self._root_menu.valueChanged.connect(self.valueChanged)
        self._root_menu.valueChanged.connect(self.set_value)

    def tiny(self):
        """
        Sets spin box to tiny size.
        """

        widget_theme = self.theme_data()
        self.theme_size = widget_theme.TINY if widget_theme else theme.Theme.Sizes.TINY

        return self

    def small(self):
        """
        Sets spin box to small size.
        """

        widget_theme = self.theme_data()
        self.theme_size = widget_theme.SMALL if widget_theme else theme.Theme.Sizes.SMALL

        return self

    def medium(self):
        """
        Sets spin box to medium size.
        """

        widget_theme = self.theme_data()
        self.theme_size = widget_theme.MEDIUM if widget_theme else theme.Theme.Sizes.MEDIUM

        return self

    def large(self):
        """
        Sets spin box to large size.
        """

        widget_theme = self.theme_data()
        self.theme_size = widget_theme.LARGE if widget_theme else theme.Theme.Sizes.LARGE

        return self

    def huge(self):
        """
        Sets spin box to huge size.
        """

        widget_theme = self.theme_data()
        self.theme_size = widget_theme.HUGE if widget_theme else theme.Theme.Sizes.HUGE

        return self

    # =================================================================================================================
    # PROPERTY MIXIN SETTERS
    # =================================================================================================================

    def _set_value(self, value):
        """
        Internal property function used to set value.

        :param object value: combobox value.
        """

        self.lineEdit().setProperty('text', self._display_formatter(value))
        if self._root_menu:
            self._root_menu.set_value(value)


@theme.mixin
@mixin.dynamic_property
class SearchableComboBox(BaseComboBox):
    def __init__(self, items=None, parent=None):
        super(SearchableComboBox, self).__init__(items=items, parent=parent)

        self._is_checkable = False

        self._filter_model = QSortFilterProxyModel(self, filterCaseSensitivity=Qt.CaseSensitive)
        self._completer = QCompleter(self)
        self.setCompleter(self._completer)
        self._completer.setModel(self._filter_model)
        self.setCompleter(self._completer)
        self._filter_model.setSourceModel(self.model())

        line_edit = self.lineEdit()
        line_edit.setReadOnly(False)

        line_edit.textEdited.connect(self._filter_model.setFilterFixedString)
        self._completer.activated.connect(self._on_completer_activated)
        self.view().pressed.connect(self._on_handle_item_pressed)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def keyPressEvent(self, event):
        """
        Overrides base QComboBox keyPressEvent function.

        :param QEvent event: Qt key press event.
        """

        super(BaseComboBox, self).keyPressEvent(event)
        if event.key() == Qt.Key_Escape:
            self.close()
            self.parent().setFocus()
        elif event.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.itemSelected.emit(self.currentText())
            self.parent().setFocus()

    def addItem(self, text, is_checkable=False):
        """
        Overrides base QComboBox addItem function.

        :param str text: text item to add.
        :param bool is_checkable: whether or not new added item is checkable.
        """

        super(BaseComboBox, self).addItem(text)
        model = self.mode()
        item = model.item(model.rowCount() - 1, 0)
        if item and is_checkable:
            self._is_checkable = is_checkable
            item.setCheckState(Qt.Checked)

    def setModel(self, model):
        """
        Overrides base QComboBox setModel function.

        :param QAbstractItemModel model: combobox model.
        """

        super(BaseComboBox, self).setModel(model)
        self._filter_model.setSourceModel(model)
        self._completer.setModel(self._filter_model)

    def setModelColumn(self, column):
        """
        Overrides base QComboBox setModelColumn function.

        :param int column: column to set model of.
        """

        self._completer.setCompletionColumn(column)
        self._filter_model.setFilterKeyColumn(column)
        super(BaseComboBox, self).setModelColumn(column)

    def setView(self, *args, **kwargs):
        """
        Overrides base QComboBox setView function.

        :param args:
        :param kwargs:
        """

        self._has_custom_view = True
        super(BaseComboBox, self).setView(*args, **kwargs)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def get_checked_items(self):
        """
        Returns a list of checked items.

        :return: list of checked items.
        :rtype: list(str)
        """

        model = self.model()
        checked_items = list()
        for index in range(model.rowCount()):
            item = model.itemFromIndex(index)
            if item.isVisible():
                checked_items.append(item)

        return checked_items

    def get_valid_items(self):
        """
        Returns a list with the the items that are valid.

        :return: list of valid items.
        :rtype: list(str)
        """

        model = self.model()
        checked_items = list()
        for index in range(model.rowCount()):
            item = model.itemFromIndex(index)
            if item.isValid():
                checked_items.append(item)

        return checked_items

    # =================================================================================================================
    # CALLBACKS
    # =================================================================================================================

    def _on_completer_activated(self, text):
        """
        Internal callback function that is called when completer is activated.

        :param str text: completer text.
        """

        if text:
            index = self.findText(text)
            self.setCurrentIndex(index)
            self.activated.emit(str(self.itemText(index)))

    def _on_handle_item_pressed(self, index):
        """
        Internal callback function that is called when view is pressed by the user.

        :parm QModelIndex index: model index clicked by the user.
        """

        if not self._is_checkable:
            return
        item = self.model().itemFromIndex(index)
        state = Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
        item.setCheckState(state)
        self.checkStateChanged.emit(item.text(), state)


class AbstractComboBoxWidget(QWidget):
    """
    Custom widget that wraps a combo box with extra widgets.

    NOTE: Do not instantiate this abstract combo box widget implementation directly.
    """

    itemChanged = Signal(object)

    _PREV_INDEX = None

    class ComboItemChangedEvent(object):
        def __init__(self, prev_index, current_index, parent):
            self._parent = parent
            self._index = current_index
            self._prev_index = prev_index

        @property
        def text(self):
            return self._parent.item_text(self._index)

        @property
        def prev_text(self):
            return self._parent.item_text(self._prev_index)

    def __init__(self, parent=None):

        self._label = ''
        self._combo = None

        super(AbstractComboBoxWidget, self).__init__(parent=parent)

    def __getattr__(self, item):
        if hasattr(self._combo, item):
            return getattr(self._combo, item)

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    @property
    def activated(self):
        return self._combo.activated

    @property
    def currentIndexChanged(self):
        # we used camelcase to match Qt signal name
        return self._combo.currentIndexChanged

    @property
    def currentTextChanged(self):
        # we used camelcase to match Qt signal name
        return self._combo.currentTextChanged

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def blockSignals(self, flag):
        """
        Blocks the signals of the combo box and label widgets.
        """

        self._combo.blockSignals(flag)
        if self._label:
            self._label.blockSignals(flag)

        super(AbstractComboBoxWidget, self).blockSignals(flag)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def add_item(self, item, sort_alphabetically=False):
        """
        Adds an entry into the combo box widget.

        :param str item: the name to add to the combo box.
        :param bool sort_alphabetically: whether or not to sorts the full combo box alphabetically after adding.
        """

        self._combo.addItem(item)
        if sort_alphabetically:
            self._combo.model().sort(0)

    def add_items(self, items, sort_alphabetically=False):
        """
        Adds a list of entries into the combo box widget.

        :param list(str) items: the names to add to the combo box.
        :param bool sort_alphabetically: whether or not to sorts the full combo box alphabetically after adding.
        """

        self._combo.addItems(items)
        if sort_alphabetically:
            self._combo.model().sort(0)

    def current_index(self):
        """
        Returns the index value of the combo box for the current selected item.

        :return: current selected item index within combo box.
        :rtype: int
        """

        return int(self._combo.currentIndex())

    def set_current_index(self, index, quiet=False):
        """
        Sets the com box to the given index number.

        :param int index: index to set combo box to.
        :param bool quiet: whether to block signals before setting the index.
        """

        index = index or 0
        if quiet:
            self._combo.blockSignals(True)
        self._combo.setCurrentIndex(index)
        if quiet:
            self._combo.blockSignals(False)

    def current_text(self):
        """
        Returns the current text of the combo box.

        :return: combo box current text.
        :rtype: str
        """

        return self._combo.currentText()

    def set_current_text(self, text, quiet=False):
        """
        Sets the combo box to the given text.

        :param str text: text to set combo box to.
        :param bool quiet: whether to block signals before setting the index.
        """

        if quiet:
            self._combo.blockSignals(True)
        self._combo.setCurrentText(text)
        if quiet:
            self._combo.blockSignals(False)

    def item_text(self, index):
        """
        Returns the text of the item with given index.

        :param int index: combo box item index.
        :return: combo box item text.
        :rtype: str
        """

        return self._combo.itemText(index)

    def item_texts(self):
        """
        Generator function that returns all the item texts within the combo box widget.

        :return: all item texts.
        :rtype: generator(str)
        """

        for i in range(self.count()):
            yield self.item_Text(i)

    def set_item_text(self, index, text):
        """
        Sets the text of the item with given index with combo box widget.

        :param int index: index of the combo box item we want to set text of.
        :param str text: new text for the combo box item.
        """

        return self._combo.setItemText(index, text)

    def set_to_text(self, text, quiet=False):
        """
        Sets the index based on the text.

        :param str text: text to search and switch the combo box to.
        :param bool quiet: whether or not to block signals before setting the index.
        """

        index = self._combo.findText(text, Qt.MatchFixedString)
        if index >= 0:
            self.set_current_index(index, quiet=quiet)

    def remove_item_by_text(self, text):
        """
        Removes the index based on the text from the combo box.

        :param str text: text to search and delete its entire entry from the combo box.
        :return: True if the removal operation was successful; False otherwise.
        :rtype: bool
        """

        index = self._combo.findText(text, Qt.MatchFixedString)
        if index >= 0:
            self._combo.removeItem(index)

    def current_data(self, role=Qt.UserRole):
        """
        Returns the data of the current selected item.

        :param Qt.Role role: role ot the data we want to retrieve.
        :return: current item data.
        :rtype: object
        """

        return self._combo.currentData(role)

    def set_item_data(self, index, value):
        """
        Sets the data role for the item on the given index with the combo box to the given value.

        :param int index: item index to assign value to.
        :param object value: value to assign.
        """

        self._combo.setItemData(index, value)

    def item_data(self, index, role=Qt.UserRole):
        """
        Returns custom user data contained within the combo box item in the given index.

        :param int index: combo box item whose data we want to retrieve.
        :param Qt.Role role: role of the data.
        :return: combo box item data.
        :rtype: object
        """

        return self._combo.itemData(index, role)

    def iter_item_data(self):
        """
        Generator function that returns all the available combo box item data.

        :return: item data generator.
        :rtype: generator(object)
        """

        for i in range(self.count()):
            yield self.item_data(i)

    def value(self):
        """
        Returns the literal value of the combo box.

        :return: literal value of the combo box.
        :rtype: str
        """

        return str(self._combo.currentText())

    def count(self):
        """
        Returns the total amount of items.

        :return: total amount of items.
        :rtype: int
        """

        return self._combo.count()

    def clear(self):
        """
        Clears all the items within the widget combo box.
        """

        self._combo.clear()

    def set_label_fixed_width(self, width):
        """
        Sets the fixed width of the label.

        :param int width: fixed label width in pixels.
        """

        self._label.setFixedWidth(width)

    def set_box_fixed_width(self, width):
        """
        Sets the fixed width of the combo box.

        :param int width: fixed combo box width in pixels.
        """

        self._combo.setFixedWidth(width)

    # =================================================================================================================
    # CALLBACKS
    # =================================================================================================================

    def _on_current_index_chagend(self):
        """
        Internal callback function that is called when the combo items changes.

        :return: the combo box value as an int and the literal string (text).
        :rtype: tuple(int, str)
        """

        event = AbstractComboBoxWidget.ComboItemChangedEvent(
            int(self._PREV_INDEX if self._PREV_INDEX is not None else -1), int(self._combo.currentIndex()), parent=self)
        self.itemChanged.emit(event)
        self._PREV_INDEX = self._combo.currentIndex()


@theme.mixin
class BaseComboBoxWidget(AbstractComboBoxWidget):
    """
    Creates a basic combo box widget width a label.
    """

    def __init__(self, text='', items=None, label_ratio=None, box_ratio=None, tooltip='', set_index=0,
                 sort_alphabetically=False, spacing=2, margins=(0, 0, 0, 0), box_min_width=None, item_data=None,
                 parent=None):
        super(BaseComboBoxWidget, self).__init__(parent=parent)

        self._combo = self.setup_combo(
            items=items, item_data=item_data, tooltip=tooltip, set_index=set_index,
            sort_alphabetically=sort_alphabetically, parent=parent)

        combo_layout = layouts.HorizontalLayout(spacing=spacing, margins=margins)
        self.setLayout(combo_layout)

        if text:
            self._label = labels.BaseLabel(text, tooltip=tooltip, parent=parent)
            combo_layout.addWidget(self._label, label_ratio) if label_ratio else combo_layout.addWidget(self._label)

        combo_layout.addWidget(self._combo, box_ratio) if box_ratio else combo_layout.addWidget(self._combo)

        if box_min_width:
            self._combo.setMinimumWidth(box_min_width)

        self._combo.currentIndexChanged.connect(self._on_current_index_chagend)

    # =================================================================================================================
    # CLASS METHODS
    # =================================================================================================================

    @classmethod
    def setup_combo(cls, items=None, item_data=None, tooltip='', set_index=0, sort_alphabetically=False, parent=None):
        """
        Class methods that creates the combo box widget contained within this widget.

        :param list(str) items: list of combo box it ems.
        :param list(object) item_data: custom data that should be stored within each one of the items.
        :param str tooltip: combo box tooltip.
        :param int set_index: default initial index to set after the addition of the combo box items.
        :param bool sort_alphabetically: whether or not combo box items should be ordered alphabetically.
        :param QWidget parent: combo box parent.
        :return: newly created combo box widget.
        :rtype: BaseComboBox
        """

        items = helpers.force_list(items)
        combo = BaseComboBox(parent=parent)
        if sort_alphabetically and items:
            # sort alphabetically case insensitive
            items = [x.encode('UTF8') for x in items]
            items.sort(key=str.lower)

        if item_data:
            for i, item in enumerate(items):
                combo.addItem(item, item_data[i])
        else:
            combo.addItems(items)

        combo.setToolTip(tooltip)

        if set_index:
            combo.setCurrentIndex(set_index)

        return combo


@theme.mixin
class SearchableComboBoxWidget(AbstractComboBoxWidget):
    """
    Searchable combo box with a label.
    """

    def __init__(self, text='', items=None, label_ratio=None, box_ratio=None, tooltip='', set_index=0,
                 sort_alphabetically=False, spacing=2, margins=(0, 0, 0, 0), box_min_width=None, item_data=None,
                 parent=None):
        super(SearchableComboBoxWidget, self).__init__(parent=parent)

        self._combo = self.setup_combo(
            items=items, item_data=item_data, tooltip=tooltip, set_index=set_index,
            sort_alphabetically=sort_alphabetically, parent=parent)

        combo_layout = layouts.HorizontalLayout(spacing=spacing, margins=margins)
        self.setLayout(combo_layout)

        if text:
            self._label = labels.BaseLabel(text, tooltip=tooltip, parent=parent)
            combo_layout.addWidget(self._label, label_ratio) if label_ratio else combo_layout.addWidget(self._label)

        combo_layout.addWidget(self._combo, box_ratio) if box_ratio else combo_layout.addWidget(self._combo)

        if box_min_width:
            self._combo.setMinimumWidth(box_min_width)

        self._combo.currentIndexChanged.connect(self._on_current_index_chagend)

    # =================================================================================================================
    # CLASS METHODS
    # =================================================================================================================

    @classmethod
    def setup_combo(cls, items=None, item_data=None, tooltip='', set_index=0, sort_alphabetically=False, parent=None):
        """
        Class methods that creates the combo box widget contained within this widget.

        :param list(str) items: list of combo box it ems.
        :param list(object) item_data: custom data that should be stored within each one of the items.
        :param str tooltip: combo box tooltip.
        :param int set_index: default initial index to set after the addition of the combo box items.
        :param bool sort_alphabetically: whether or not combo box items should be ordered alphabetically.
        :param QWidget parent: combo box parent.
        :return: newly created combo box widget.
        :rtype: BaseComboBox
        """

        items = helpers.force_list(items)
        combo = SearchableComboBox(parent=parent)
        if sort_alphabetically and items:
            # sort alphabetically case insensitive
            items = [x.encode('UTF8') for x in items]
            items.sort(key=str.lower)

        if item_data:
            for i, item in enumerate(items):
                combo.addItem(item, item_data[i])
        else:
            combo.addItems(items)

        combo.setToolTip(tooltip)

        if set_index:
            combo.setCurrentIndex(set_index)

        return combo


class BoolComboBox(BaseComboBox):

    valueSet = Signal(bool)

    def __init__(self, state=True, parent=None):
        super(BoolComboBox, self).__init__(parent=parent)

        self.addItem('True')
        self.addItem('False')
        self.setCurrentText(str(state))

        self.currentIndexChanged.connect(self._on_current_index_changed)

    def get_state(self):
        """
        Returns current bool combo state.

        :return: combo state.
        :rtype: bool
        """

        return self.currentText().lower() == 'true'

    def _on_current_index_changed(self):
        """
        Internal callback function that is called when index is changed by the user.
        """

        self.valueSet.emit(self.get_state())
