from __future__ import annotations

from typing import Sequence, Any

from ..externals.Qt.QtCore import Qt
from ..externals.Qt.QtWidgets import QWidget, QComboBox, QLineEdit, QTextBrowser
from ..externals.Qt.QtGui import QIcon

from .widgets.labels import BaseLabel, ClippedLabel, IconLabel
from .widgets.comboboxes import BaseComboBox, NoWheelComboBox
from .widgets.lineedits import BaseLineEdit
from .widgets.search import SearchFindWidget


def label(
        text: str = '', tooltip: str = '', status_tip: str | None = None, upper: bool = False, bold: bool = False,
        alignment: Qt.AlignmentFlag | None = None, elide_mode: Qt.TextElideMode = Qt.ElideNone,
        min_width: int | None = None, max_width: int | None = None, properties: list[tuple[str, Any]] | None = None,
        parent: QWidget | None = None) -> BaseLabel:
    """
    Creates a new label widget.

    :param text: label text.
    :param tooltip: optional label tooltip.
    :param tooltip: optional label status tip.
    :param upper: whether label text is forced to be uppercase.
    :param bold: whether label font is bold.
    :param alignment: optional alignment flag for the label.
    :param elide_mode: whether label text should elide.
    :param min_width: optional minimum width for the label.
    :param max_width: optional maximum width for the label.
    :param properties: optional dynamic properties to add to the label.
    :param tooltip: optional label tooltip.
    :param status_tip: optional status tip.
    :param parent: parent widget.
    :return: new label widget instance.
    """

    new_label = BaseLabel(
        text=text, tooltip=tooltip, status_tip=status_tip, bold=bold, upper=upper, elide_mode=elide_mode, parent=parent)
    if min_width is not None:
        new_label.setMinimumWidth(min_width)
    if max_width is not None:
        new_label.setMaximumWidth(max_width)

    if alignment:
        new_label.setAlignment(alignment)

    if properties:
        for name, value in properties:
            new_label.setProperty(name, value)

    return new_label


def h1_label(
        text: str = '', tooltip: str = '', upper: bool = False, bold: bool = False,
        elide_mode: Qt.TextElideMode = Qt.ElideNone, min_width: int | None = None, max_width: int | None = None,
        parent: QWidget | None = False) -> BaseLabel:
    """
    Creates a new H1 label widget.

    :param text: label text.
    :param tooltip: label tooltip.
    :param upper: whether label text is forced to be uppercase.
    :param bold: whether label font is bold.
    :param elide_mode: whether label text should elide.
    :param min_width: optional minimum width for the label.
    :param max_width: optional maximum width for the label.
    :param parent: parent widget.
    :return: new label widget instance.
    """

    return label(
        text=text, tooltip=tooltip, upper=upper, bold=bold, elide_mode=elide_mode, min_width=min_width,
        max_width=max_width, parent=parent).h1()


def h2_label(
        text: str = '', tooltip: str = '', upper: bool = False, bold: bool = False,
        elide_mode: Qt.TextElideMode = Qt.ElideNone, min_width: int | None = None, max_width: int | None = None,
        parent: QWidget | None = False) -> BaseLabel:
    """
    Creates a new H2 label widget.

    :param text: label text.
    :param tooltip: label tooltip.
    :param upper: whether label text is forced to be uppercase.
    :param bold: whether label font is bold.
    :param elide_mode: whether label text should elide.
    :param min_width: optional minimum width for the label.
    :param max_width: optional maximum width for the label.
    :param parent: parent widget.
    :return: new label widget instance.
    """

    return label(
        text=text, tooltip=tooltip, upper=upper, bold=bold, elide_mode=elide_mode, min_width=min_width,
        max_width=max_width, parent=parent).h2()


def h3_label(
        text: str = '', tooltip: str = '', upper: bool = False, bold: bool = False,
        elide_mode: Qt.TextElideMode = Qt.ElideNone, min_width: int | None = None, max_width: int | None = None,
        parent: QWidget | None = False) -> BaseLabel:
    """
    Creates a new H3 label widget.

    :param text: label text.
    :param tooltip: label tooltip.
    :param upper: whether label text is forced to be uppercase.
    :param bold: whether label font is bold.
    :param elide_mode: whether label text should elide.
    :param min_width: optional minimum width for the label.
    :param max_width: optional maximum width for the label.
    :param parent: parent widget.
    :return: new label widget instance.
    """

    return label(
        text=text, tooltip=tooltip, upper=upper, bold=bold, elide_mode=elide_mode, min_width=min_width,
        max_width=max_width, parent=parent).h3()


def h4_label(
        text: str = '', tooltip: str = '', upper: bool = False, bold: bool = False,
        elide_mode: Qt.TextElideMode = Qt.ElideNone, min_width: int | None = None, max_width: int | None = None,
        parent: QWidget | None = False) -> BaseLabel:
    """
    Creates a new H4 label widget.

    :param text: label text.
    :param tooltip: label tooltip.
    :param upper: whether label text is forced to be uppercase.
    :param bold: whether label font is bold.
    :param elide_mode: whether label text should elide.
    :param min_width: optional minimum width for the label.
    :param max_width: optional maximum width for the label.
    :param parent: parent widget.
    :return: new label widget instance.
    """

    return label(
        text=text, tooltip=tooltip, upper=upper, bold=bold, elide_mode=elide_mode, min_width=min_width,
        max_width=max_width, parent=parent).h4()


def h5_label(
        text: str = '', tooltip: str = '', upper: bool = False, bold: bool = False,
        elide_mode: Qt.TextElideMode = Qt.ElideNone, min_width: int | None = None, max_width: int | None = None,
        parent: QWidget | None = False) -> BaseLabel:
    """
    Creates a new H5 label widget.

    :param text: label text.
    :param tooltip: label tooltip.
    :param upper: whether label text is forced to be uppercase.
    :param bold: whether label font is bold.
    :param elide_mode: whether label text should elide.
    :param min_width: optional minimum width for the label.
    :param max_width: optional maximum width for the label.
    :param parent: parent widget.
    :return: new label widget instance.
    """

    return label(
        text=text, tooltip=tooltip, upper=upper, bold=bold, elide_mode=elide_mode, min_width=min_width,
        max_width=max_width, parent=parent).h5()


def clipped_label(
        text: str = '', width: int = 0, elide: bool = True, always_show_all: bool = False,
        parent: QWidget | None = None) -> ClippedLabel:
    """
    Custom QLabel that clips itself if the widget width is smaller than the text.

    :param text: label text.
    :param width: minimum width.
    :param elide: whether to elide label.
    :param always_show_all: force the label to show the complete text or hide the complete text.
    :param parent: parent widget.
    :return: new clipped label widget instance.
    """

    return ClippedLabel(text=text, width=width, elide=elide, always_show_all=always_show_all, parent=parent)


def icon_label(
        icon: QIcon, text: str = '', tooltip: str = '', upper: bool = False, bold: bool = False,
        enable_menu: bool = True, parent: QWidget | None = None) -> IconLabel:
    """
    Creates a new widget with a horizontal layout with an icon and a label.

    :param icon: label icon.
    :param text: label text.
    :param tooltip: label tooltip.
    :param upper: whether label text is forced to be uppercase.
    :param bold: whether label font is bold.
    :param enable_menu: whether enable label menu.
    :param parent: parent widget.
    :return: new label widget instance.
    """

    return IconLabel(icon, text=text, tooltip=tooltip, upper=upper, bold=bold, enable_menu=enable_menu, parent=parent)


def combobox(
        items: Sequence[str] | None = None, item_data: Sequence[Any] | None = None, placeholder_text: str = '',
        tooltip: str = '', set_index: int = 0, sort_alphabetically: bool = True,
        support_middle_mouse_scroll: bool = True, parent: QWidget | None = None) -> BaseComboBox:
    """
    Creates a ComboBox widget with the specified parameters.

    :param items: An optional sequence of items to populate the ComboBox with. Defaults to None.
    :param item_data: An optional sequence of item data corresponding to the items. Defaults to None.
    :param placeholder_text: The placeholder text to display in the ComboBox when no item is selected.
        Defaults to an empty string.
    :param tooltip: The tooltip text to display for the ComboBox. Defaults to an empty string.
    :param set_index: The index of the item to set as selected initially. Defaults to 0.
    :param sort_alphabetically: Whether to sort items alphabetically. Defaults to True.
    :param support_middle_mouse_scroll: Whether to support middle mouse scroll. Defaults to True.
    :param parent: The parent widget. Defaults to None.

    :return: The created ComboBox widget.
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


def line_edit(
        text: str = '', read_only: bool = False, placeholder_text: str = '', tooltip: str = '',
        parent: QWidget | None = None) -> BaseLineEdit:
    """
    Creates a basic line edit widget.

    :param str text: default line edit text.
    :param bool read_only: whether line edit is read only.
    :param str placeholder_text: line edit placeholder text.
    :param str tooltip: line edit tooltip text.
    :param QWidget parent: parent widget.
    :return: newly created combo box.
    :rtype: BaseLineEdit
    """

    new_line_edit = BaseLineEdit(text=text, parent=parent)
    new_line_edit.setReadOnly(read_only)
    new_line_edit.setPlaceholderText(str(placeholder_text))
    if tooltip:
        new_line_edit.setToolTip(tooltip)

    return new_line_edit


def text_browser(parent=None):
    """
    Creates a text browser widget.

    :param QWidget parent: parent widget.
    :return: newly created text browser.
    :rtype: QTextBrowser
    """

    new_text_browser = QTextBrowser(parent=parent)

    return new_text_browser


def search_widget(
        placeholder_text: str = '', search_line: QLineEdit | None = None,
        parent: QWidget | None = None) -> SearchFindWidget:
    """
    Returns widget that allows to do searches within widgets.

    :param str placeholder_text: search placeholder text.
    :param QLineEdit search_line: custom line edit widget to use.
    :param QWidget parent: parent widget.
    :return: search find widget instance.
    :rtype: SearchFindWidget
    """

    new_widget = SearchFindWidget(search_line=search_line, parent=parent)
    new_widget.set_placeholder_text(str(placeholder_text))

    return new_widget
