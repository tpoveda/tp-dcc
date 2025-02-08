from __future__ import annotations

import logging
from typing import Sequence, Any

from Qt.QtCore import Qt, QSize
from Qt.QtWidgets import (
    QWidget,
    QComboBox,
    QLineEdit,
    QTextBrowser,
    QPushButton,
    QCheckBox,
)
from Qt.QtGui import QIcon

from . import uiconsts, dpi, icon
from .uiconsts import ButtonStyles  # noqa: F401
from .widgets.layouts import VerticalLayout, HorizontalLayout, GridLayout
from .widgets.labels import BaseLabel, ClippedLabel, IconLabel
from .widgets.comboboxes import (
    BaseComboBox,
    NoWheelComboBox,
    ComboBoxRegularWidget,
    ComboBoxSearchableWidget,
)
from .widgets.lineedits import BaseLineEdit, IntLineEdit, FileSystemPathLineEdit
from .widgets.search import SearchFindWidget, SearchLineEdit
from .widgets.buttons import (
    BaseButton,
    BasePushButton,
    BaseToolButton,
    RoundButton,
    ShadowedButton,
    LeftAlignedButton,
    LabelSmallButton,
    OkCancelButtons,
)
from .widgets.checkboxes import BaseCheckBoxWidget
from .widgets.stringedit import StringEdit, IntEdit, FloatEdit
from .widgets.frames import CollapsibleFrame, CollapsibleFrameThin
from .widgets.dividers import Divider, LabelDivider, HorizontalLine, VerticalLine
from .widgets.groups import RadioButtonGroup
from .widgets.popups import MessageBoxBase, CustomDialog
from .widgets.tabs import LineTabWidget
from .widgets.stacks import SlidingOpacityStackedWidget
from .widgets.accordion import Accordion
from .widgets.overlay import OverlayLoadingWidget

logger = logging.getLogger(__name__)


def vertical_layout(
    spacing: int = uiconsts.DEFAULT_SPACING,
    margins: tuple[int, int, int, int] = (2, 2, 2, 2),
    alignment: Qt.AlignmentFlag | None = None,
    parent: QWidget | None = None,
) -> VerticalLayout:
    """
    Returns a new vertical layout that automatically handles DPI stuff.

    :param spacing: layout spacing
    :param margins: layout margins.
    :param alignment: optional layout alignment.
    :param parent: optional layout parent.
    :return: new vertical layout instance.
    """

    new_layout = VerticalLayout(parent=parent)
    new_layout.setContentsMargins(*margins)
    new_layout.setSpacing(spacing)
    if alignment is not None:
        new_layout.setAlignment(alignment)

    return new_layout


def vertical_main_layout() -> VerticalLayout:
    """
    Returns a new main vertical layout that automatically handles DPI stuff.
    This layout is usually used for the main widget layout of the parent widget.

    :return: new vertical layout instance.
    """

    return vertical_layout(
        margins=(
            uiconsts.WINDOW_SIDE_PADDING,
            uiconsts.WINDOW_BOTTOM_PADDING,
            uiconsts.WINDOW_SIDE_PADDING,
            uiconsts.WINDOW_BOTTOM_PADDING,
        ),
        spacing=uiconsts.SPACING,
    )


def horizontal_layout(
    spacing: int = uiconsts.DEFAULT_SPACING,
    margins: tuple[int, int, int, int] = (0, 0, 0, 0),
    alignment: Qt.AlignmentFlag | None = None,
    parent: QWidget | None = None,
) -> HorizontalLayout:
    """
    Returns a new horizontal layout that automatically handles DPI stuff.

    :param spacing: layout spacing
    :param margins: layout margins.
    :param alignment: optional layout alignment.
    :param parent: optional layout parent.
    :return: new horizontal layout instance.
    """

    new_layout = HorizontalLayout(parent)
    new_layout.setContentsMargins(*margins)
    new_layout.setSpacing(spacing)
    if alignment is not None:
        new_layout.setAlignment(alignment)

    return new_layout


def horizontal_main_layout(parent: QWidget | None = None) -> HorizontalLayout:
    """
    Returns a new main horizontal layout that automatically handles DPI stuff.
    This layout is usually used for the main widget layout of the parent widget.

    :param parent: optional layout parent.
    :return: new horizontal layout instance.
    """

    return horizontal_layout(
        margins=(
            uiconsts.WINDOW_SIDE_PADDING,
            uiconsts.WINDOW_BOTTOM_PADDING,
            uiconsts.WINDOW_SIDE_PADDING,
            uiconsts.WINDOW_BOTTOM_PADDING,
        ),
        spacing=uiconsts.SPACING,
    )


def grid_layout(
    spacing: int = uiconsts.DEFAULT_SPACING,
    margins: tuple[int, int, int, int] = (0, 0, 0, 0),
    column_min_width: list[int, int] | None = None,
    column_min_width_b: list[int, int] | None = None,
    vertical_spacing: int | None = None,
    horizontal_spacing: int | None = None,
    parent: QWidget | None = None,
) -> GridLayout:
    """
    Returns a new grid layout that automatically handles DPI stuff.

    :param spacing: layout spacing
    :param margins: layout margins.
    :param column_min_width: optional colum minimum width.
    :param column_min_width_b: optional colum secondary minimum width.
    :param vertical_spacing: optional vertical spacing.
    :param horizontal_spacing: optional horizontal spacing.
    :param parent: optional layout parent.
    :return: new grid layout instance.
    """

    new_layout = GridLayout(parent)
    new_layout.setContentsMargins(*margins)
    if not vertical_spacing and not horizontal_spacing:
        new_layout.setHorizontalSpacing(spacing)
        new_layout.setVerticalSpacing(spacing)
    elif vertical_spacing and not horizontal_spacing:
        new_layout.setHorizontalSpacing(horizontal_spacing)
        new_layout.setVerticalSpacing(vertical_spacing)
    elif horizontal_spacing and not vertical_spacing:
        new_layout.setHorizontalSpacing(horizontal_spacing)
        new_layout.setVerticalSpacing(spacing)
    else:
        new_layout.setHorizontalSpacing(horizontal_spacing)
        new_layout.setVerticalSpacing(vertical_spacing)

    if column_min_width:
        new_layout.setColumnMinimumWidth(
            column_min_width[0], dpi.dpi_scale(column_min_width[1])
        )
    if column_min_width_b:
        new_layout.setColumnMinimumWidth(
            column_min_width_b[0], dpi.dpi_scale(column_min_width_b[1])
        )

    return new_layout


def grid_main_layout(parent: QWidget | None = None) -> GridLayout:
    """
    Returns a new main grid layout that automatically handles DPI stuff.
    This layout is usually used for the main widget layout of the parent widget.

    :param parent: optional layout parent.
    :return: new grid layout instance.
    """

    return grid_layout(
        margins=(
            uiconsts.WINDOW_SIDE_PADDING,
            uiconsts.WINDOW_BOTTOM_PADDING,
            uiconsts.WINDOW_SIDE_PADDING,
            uiconsts.WINDOW_BOTTOM_PADDING,
        ),
        spacing=uiconsts.SPACING,
    )


def label(
    text: str = "",
    tooltip: str = "",
    status_tip: str | None = None,
    upper: bool = False,
    bold: bool = False,
    alignment: Qt.AlignmentFlag | None = None,
    elide_mode: Qt.TextElideMode = Qt.ElideNone,
    min_width: int | None = None,
    max_width: int | None = None,
    properties: list[tuple[str, Any]] | None = None,
    parent: QWidget | None = None,
) -> BaseLabel:
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
        text=text,
        tooltip=tooltip,
        status_tip=status_tip,
        bold=bold,
        upper=upper,
        elide_mode=elide_mode,
        parent=parent,
    )
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
    text: str = "",
    tooltip: str = "",
    upper: bool = False,
    bold: bool = False,
    elide_mode: Qt.TextElideMode = Qt.ElideNone,
    min_width: int | None = None,
    max_width: int | None = None,
    parent: QWidget | None = False,
) -> BaseLabel:
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
        text=text,
        tooltip=tooltip,
        upper=upper,
        bold=bold,
        elide_mode=elide_mode,
        min_width=min_width,
        max_width=max_width,
        parent=parent,
    ).h1()


def h2_label(
    text: str = "",
    tooltip: str = "",
    upper: bool = False,
    bold: bool = False,
    elide_mode: Qt.TextElideMode = Qt.ElideNone,
    min_width: int | None = None,
    max_width: int | None = None,
    parent: QWidget | None = False,
) -> BaseLabel:
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
        text=text,
        tooltip=tooltip,
        upper=upper,
        bold=bold,
        elide_mode=elide_mode,
        min_width=min_width,
        max_width=max_width,
        parent=parent,
    ).h2()


def h3_label(
    text: str = "",
    tooltip: str = "",
    upper: bool = False,
    bold: bool = False,
    elide_mode: Qt.TextElideMode = Qt.ElideNone,
    min_width: int | None = None,
    max_width: int | None = None,
    parent: QWidget | None = False,
) -> BaseLabel:
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
        text=text,
        tooltip=tooltip,
        upper=upper,
        bold=bold,
        elide_mode=elide_mode,
        min_width=min_width,
        max_width=max_width,
        parent=parent,
    ).h3()


def h4_label(
    text: str = "",
    tooltip: str = "",
    upper: bool = False,
    bold: bool = False,
    elide_mode: Qt.TextElideMode = Qt.ElideNone,
    min_width: int | None = None,
    max_width: int | None = None,
    parent: QWidget | None = False,
) -> BaseLabel:
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
        text=text,
        tooltip=tooltip,
        upper=upper,
        bold=bold,
        elide_mode=elide_mode,
        min_width=min_width,
        max_width=max_width,
        parent=parent,
    ).h4()


def h5_label(
    text: str = "",
    tooltip: str = "",
    upper: bool = False,
    bold: bool = False,
    elide_mode: Qt.TextElideMode = Qt.ElideNone,
    min_width: int | None = None,
    max_width: int | None = None,
    parent: QWidget | None = False,
) -> BaseLabel:
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
        text=text,
        tooltip=tooltip,
        upper=upper,
        bold=bold,
        elide_mode=elide_mode,
        min_width=min_width,
        max_width=max_width,
        parent=parent,
    ).h5()


def clipped_label(
    text: str = "",
    width: int = 0,
    elide: bool = True,
    always_show_all: bool = False,
    parent: QWidget | None = None,
) -> ClippedLabel:
    """
    Custom QLabel that clips itself if the widget width is smaller than the text.

    :param text: label text.
    :param width: minimum width.
    :param elide: whether to elide label.
    :param always_show_all: force the label to show the complete text or hide the complete text.
    :param parent: parent widget.
    :return: new clipped label widget instance.
    """

    return ClippedLabel(
        text=text,
        width=width,
        elide=elide,
        always_show_all=always_show_all,
        parent=parent,
    )


def icon_label(
    label_icon: QIcon,
    text: str = "",
    tooltip: str = "",
    upper: bool = False,
    bold: bool = False,
    enable_menu: bool = True,
    parent: QWidget | None = None,
) -> IconLabel:
    """
    Creates a new widget with a horizontal layout with an icon and a label.

    :param label_icon: label icon.
    :param text: label text.
    :param tooltip: label tooltip.
    :param upper: whether label text is forced to be uppercase.
    :param bold: whether label font is bold.
    :param enable_menu: whether enable label menu.
    :param parent: parent widget.
    :return: new label widget instance.
    """

    return IconLabel(
        label_icon,
        text=text,
        tooltip=tooltip,
        upper=upper,
        bold=bold,
        enable_menu=enable_menu,
        parent=parent,
    )


def combobox(
    items: Sequence[str] | None = None,
    item_data: Sequence[Any] | None = None,
    sort_items: bool = False,
    placeholder_text: str = "",
    tooltip: str = "",
    set_index: int = 0,
    sort_alphabetically: bool = True,
    support_middle_mouse_scroll: bool = True,
    parent: QWidget | None = None,
) -> BaseComboBox:
    """
    Creates a ComboBox widget with the specified parameters.

    :param items: An optional sequence of items to populate the ComboBox with. Defaults to None.
    :param item_data: An optional sequence of item data corresponding to the items. Defaults to None.
    :param sort_items: Whether to sort items. Defaults to False.
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
        combo_box = NoWheelComboBox(parent=parent)
    else:
        combo_box = BaseComboBox(parent=parent)

    if sort_alphabetically:
        combo_box.setInsertPolicy(QComboBox.InsertAlphabetically)
        if items:
            items = [str(x) for x in list(items)]
            if sort_items:
                items.sort(key=lambda x: x.lower())
    if item_data:
        for i, item in enumerate(items):
            combo_box.addItem(item, item_data[i])
    else:
        if items:
            combo_box.addItems(items)
    combo_box.setToolTip(tooltip)
    if placeholder_text:
        combo_box.setPlaceholderText(str(placeholder_text))
    if set_index:
        combo_box.setCurrentIndex(set_index)

    return combo_box


def combobox_widget(
    label_text: str = "",
    items: Sequence[str] | None = None,
    label_ratio: int | None = None,
    box_ratio: int | None = None,
    tooltip: str = "",
    set_index: int = 0,
    sort_alphabetically: bool = False,
    margins: tuple[int, int, int, int] = (0, 0, 0, 0),
    spacing: int = uiconsts.SMALL_SPACING,
    box_min_width: int | None = None,
    item_data: Sequence[Any] | None = None,
    support_middle_mouse_scroll: bool = True,
    searchable: bool = False,
    parent: QWidget | None = None,
) -> ComboBoxRegularWidget | ComboBoxSearchableWidget:
    """
    Creates a ComboBox widget with the specified parameters.

    :param label_text: The text for the label. Defaults to an empty string.
    :param items: An optional sequence of items to populate the ComboBox with. Defaults to None.
    :param label_ratio: The ratio of the label width. Defaults to None.
    :param box_ratio: The ratio of the box width. Defaults to None.
    :param tooltip: The tooltip text for the combo box. Defaults to an empty string.
    :param set_index: The index to be set as selected. Defaults to 0.
    :param sort_alphabetically: Whether to sort items alphabetically. Defaults to True.
    :param margins: The margins around the widget. Defaults to (0, 0, 0, 0).
    :param spacing: The spacing between the label and the combo box. Defaults to uiconsts.SMALL_SPACING.
    :param box_min_width: The minimum width for the combo box. Defaults to None.
    :param item_data: Additional data associated with the combo box items. Defaults to None.
    :param support_middle_mouse_scroll: If True, supports scrolling with the middle mouse button. Defaults to True.
    :param searchable: Whether to enable search functionality. Defaults to False.
    :param parent: The parent widget. Defaults to None.

    :return: The created ComboBox widget.
    """

    if not searchable:
        combo_box = ComboBoxRegularWidget(
            label=label_text,
            items=items,
            label_ratio=label_ratio,
            box_ratio=box_ratio,
            tooltip=tooltip,
            set_index=set_index,
            sort_alphabetically=sort_alphabetically,
            margins=margins,
            spacing=spacing,
            box_min_width=box_min_width,
            item_data=item_data,
            support_middle_mouse_scroll=support_middle_mouse_scroll,
            parent=parent,
        )
    else:
        combo_box = ComboBoxSearchableWidget(
            label=label_text,
            items=items,
            label_ratio=label_ratio,
            box_ratio=box_ratio,
            tooltip=tooltip,
            set_index=set_index,
            sort_alphabetically=sort_alphabetically,
            parent=parent,
        )

    return combo_box


def line_edit(
    text: str = "",
    read_only: bool = False,
    placeholder_text: str = "",
    tooltip: str = "",
    edit_width: int | None = None,
    fixed_width: int | None = None,
    enable_menu: bool = False,
    parent: QWidget | None = None,
) -> BaseLineEdit:
    """
    Creates a basic line edit widget.

    :param text: default line edit text.
    :param read_only: whether line edit is read only.
    :param placeholder_text: line edit placeholder text.
    :param tooltip: line edit tooltip text.
    :param edit_width: The width of the LineEdit for editing. Defaults to None.
    :param fixed_width: The fixed width of the LineEdit. Defaults to None.
    :param enable_menu: Whether to enable the context menu. Defaults to False.
    :param parent: parent widget.
    :return: newly created combo box.
    """

    new_line_edit = BaseLineEdit(
        text=text,
        placeholder=placeholder_text,
        tooltip=tooltip,
        edit_width=edit_width,
        fixed_width=fixed_width,
        enable_menu=enable_menu,
        parent=parent,
    )
    new_line_edit.setReadOnly(read_only)

    return new_line_edit


def int_line_edit(
    text: str = "",
    read_only: bool = False,
    placeholder_text: str = "",
    tooltip: str = "",
    parent: QWidget | None = None,
    edit_width: int | None = None,
    fixed_width: int | None = None,
    enable_menu: bool = False,
    slide_distance: float = 0.01,
    small_slide_distance: float = 0.001,
    large_slide_distance: float = 0.1,
    scroll_distance: float = 1.0,
    update_on_slide_tick: bool = True,
) -> IntLineEdit:
    """
    Creates an integer line edit widget.

    :param text: default line edit text.
    :param read_only: whether line edit is read only.
    :param placeholder_text: line edit placeholder text.
    :param tooltip: line edit tooltip text.
    :param edit_width: The width of the LineEdit for editing. Defaults to None.
    :param fixed_width: The fixed width of the LineEdit. Defaults to None.
    :param enable_menu: Whether to enable the context menu. Defaults to False.
    :param slide_distance: The distance to slide on normal drag. Defaults to 1.0.
    :param small_slide_distance: The distance to slide on small drag. Defaults to 0.1.
    :param large_slide_distance: The distance to slide on large drag. Defaults to 5.0.
    :param scroll_distance: The distance to scroll. Defaults to 1.0.
    :param update_on_slide_tick: If True, updates on tick events. Defaults to False.
    :param parent: parent widget.
    :return: newly created combo box.
    """

    new_line_edit = IntLineEdit(
        text=text,
        placeholder=placeholder_text,
        tooltip=tooltip,
        edit_width=edit_width,
        fixed_width=fixed_width,
        enable_menu=enable_menu,
        slide_distance=slide_distance,
        small_slide_distance=small_slide_distance,
        large_slide_distance=large_slide_distance,
        scroll_distance=scroll_distance,
        update_on_slide_tick=update_on_slide_tick,
        parent=parent,
    )
    new_line_edit.setReadOnly(read_only)

    return new_line_edit


def text_browser(parent=None):
    """
    Creates a text browser widget.

    :param parent: parent widget.
    :return: newly created text browser.
    """

    new_text_browser = QTextBrowser(parent=parent)

    return new_text_browser


def search_widget(
    placeholder_text: str = "",
    search_line: QLineEdit | None = None,
    parent: QWidget | None = None,
) -> SearchFindWidget:
    """
    Returns widget that allows to do searches within widgets.

    :param placeholder_text: search placeholder text.
    :param search_line: custom line edit widget to use.
    :param parent: parent widget.
    :return: search find widget instance.
    """

    new_widget = SearchFindWidget(search_line=search_line, parent=parent)
    new_widget.set_placeholder_text(str(placeholder_text))

    return new_widget


def search_line_edit(
    placeholder_text: str | None = None,
    parent: QWidget | None = None,
) -> SearchLineEdit:
    """
    Creates a new search line edit widget.

    :param placeholder_text: search placeholder text.
    :param parent: parent widget.
    :return: new search line edit widget.
    """

    new_widget = SearchLineEdit(parent=parent)

    if placeholder_text:
        new_widget.setPlaceholderText(placeholder_text)

    return new_widget


def open_file_line_edit(
    path_filter: str = "",
    validate_path: bool = False,
    path_description: str | None = None,
    parent: QWidget | None = None,
) -> FileSystemPathLineEdit:
    """
    Creates a new line edit widget that opens a file dialog when clicked.

    :param path_filter: file path filter.
    :param validate_path: whether to validate the path.
    :param path_description: optional path description.
    :param parent: parent widget.
    :return: new line edit widget.
    """

    new_line_edit = FileSystemPathLineEdit(
        FileSystemPathLineEdit.Type.File,
        dialog_type=FileSystemPathLineEdit.DialogType.Load,
        path_filter=path_filter,
        validate_path=validate_path,
        path_description=path_description,
        parent=parent,
    )

    return new_line_edit


def save_file_line_edit(
    path_filter: str = "",
    validate_path: bool = False,
    path_description: str | None = None,
    parent: QWidget | None = None,
) -> FileSystemPathLineEdit:
    """
    Creates a new line edit widget that opens a save file dialog when clicked.

    :param path_filter: file path filter.
    :param validate_path: whether to validate the path.
    :param path_description: optional path description.
    :param parent: parent widget.
    :return: new line edit widget.
    """

    new_line_edit = FileSystemPathLineEdit(
        FileSystemPathLineEdit.Type.File,
        dialog_type=FileSystemPathLineEdit.DialogType.Save,
        path_filter=path_filter,
        validate_path=validate_path,
        path_description=path_description,
        parent=parent,
    )

    return new_line_edit


def base_button(
    text: str = "",
    button_icon: QIcon | None = None,
    icon_size: int = 16,
    icon_color: tuple[int, int, int] or None = None,
    icon_color_theme: str | None = None,
    min_width: int | None = None,
    max_width: int | None = None,
    min_height: int | None = None,
    max_height: int | None = None,
    style: int = uiconsts.ButtonStyles.Default,
    tooltip: str = "",
    status_tip: str = "",
    theme_updates: bool = True,
    checkable: bool = False,
    checked: bool = False,
    parent: QWidget | None = None,
) -> BaseButton | BasePushButton:
    """
    Creates an extended PushButton with a transparent background or with its regular style.

    :param text: button text.
    :param button_icon: icon name or QIcon instance.
    :param icon_size: size of the icon in pixels.
    :param icon_color: icon color in 0 to 255 range.
    :param icon_color_theme: color attribute that should be applied from current applied theme.
    :param min_width: minimum width of the button in pixels.
    :param max_width: maximum width of the button in pixels.
    :param min_height: minimum height of the button in pixels.
    :param max_height: maximum height of the button in pixels.
    :param style: the style of the button.
    :param tooltip: tooltip as seen with mouse over.
    :param status_tip: status tip as seen with mouse over.
    :param theme_updates: whether  button style will be updated when current style changes.
    :param checkable: whether the button can be checked.
    :param checked: whether (if checkable is True) button is checked by default.
    :param parent: parent widget.
    :return: newly created button.
    """

    if icon:
        kwargs = dict(
            text=text,
            icon_color_theme=icon_color_theme,
            theme_updates=theme_updates,
            parent=parent,
        )
        new_button = (
            BasePushButton(**kwargs)
            if style == uiconsts.ButtonStyles.Default
            else BaseButton(**kwargs)
        )
        if button_icon:
            new_button.set_icon(button_icon, size=icon_size, colors=icon_color)
    else:
        kwargs = dict(text=text, icon_color_theme=icon_color_theme, parent=parent)
        new_button = (
            BasePushButton(**kwargs)
            if style == uiconsts.ButtonStyles.Default
            else BaseButton(**kwargs)
        )
    if tooltip:
        new_button.setToolTip(tooltip)
    if status_tip:
        new_button.setStatusTip(status_tip)

    if min_width is not None:
        new_button.setMinimumWidth(min_width)
    if max_width is not None:
        new_button.setMaximumWidth(max_width)
    if min_height is not None:
        new_button.setMinimumHeight(min_height)
    if max_height is not None:
        new_button.setMaximumHeight(max_height)
    if checkable:
        new_button.setCheckable(True)
        new_button.setChecked(checked)

    return new_button


def regular_button(
    text: str = "",
    button_icon: str | QIcon | None = None,
    icon_size: int = 16,
    icon_color: tuple[int, int, int] or None = None,
    min_width: int | None = None,
    max_width: int | None = None,
    min_height: int | None = None,
    max_height: int | None = None,
    tooltip: str = "",
    overlay_icon_color: tuple[int, int, int] or None = None,
    overlay_icon: str | QIcon | None = None,
    checkable: bool = False,
    checked: bool = False,
    parent: QWidget | None = None,
) -> QPushButton:
    """
    Creates a standard Qt QPushButton.

    :param text: button text.
    :param or QIcon button_icon: icon name or QIcon instance.
    :param icon_size: size of the icon in pixels.
    :param icon_color: icon color in 0 to 255 range.
    :param min_width: minimum width of the button in pixels.
    :param max_width: maximum width of the button in pixels.
    :param min_height: minimum height of the button in pixels.
    :param max_height: maximum height of the button in pixels.
    :param tooltip: tooltip as seen with mouse over.
    :param overlay_icon_color: color of the overlay image icon.
    :param overlay_icon: the name of the icon image that will overlay on top of the original icon.
    :param checkable: whether the button can be checked.
    :param checked: whether (if checkable is True) button is checked by default.
    :param parent: parent widget.
    :return: newly created button.
    """

    new_button = QPushButton(text, parent=parent)
    if button_icon:
        new_button.setIcon(
            icon.colorize_icon(
                button_icon,
                size=dpi.dpi_scale(icon_size),
                color=icon_color,
                overlay_icon=overlay_icon,
                overlay_color=overlay_icon_color,
            )
        )
    new_button.setToolTip(tooltip)

    if min_width is not None:
        new_button.setMinimumWidth(dpi.dpi_scale(min_width))
    if max_width is not None:
        new_button.setMaximumWidth(dpi.dpi_scale(max_width))
    if min_height is not None:
        new_button.setMinimumHeight(dpi.dpi_scale(min_height))
    if max_height is not None:
        new_button.setMaximumHeight(dpi.dpi_scale(max_height))
    if checkable:
        new_button.setCheckable(True)
        new_button.setChecked(checked)

    return new_button


def rounded_button(
    text: str = "",
    button_icon: QIcon | None = None,
    icon_size: int = 16,
    icon_color: tuple[int, int, int] or None = None,
    tooltip: str = "",
    button_width: int = 24,
    button_height: int = 24,
    checkable: bool = False,
    checked: bool = False,
    parent: QWidget | None = None,
) -> RoundButton:
    """
    Creates a rounded button with an icon within a round circle.

    :param str text: button text.
    :param str or QIcon button_icon: icon name or QIcon instance.
    :param int icon_size: size of the icon in pixels.
    :param tuple(int, int, int) icon_color: icon color in 0 to 255 range.
    :param str tooltip: tooltip as seen with mouse over.
    :param int button_width: button width.
    :param int button_height: button height.
    :param bool checkable: whether the button can be checked.
    :param bool checked: whether (if checkable is True) button is checked by default.
    :param QWidget parent: parent widget.
    :return: newly created button.
    """

    button_icon = button_icon or QIcon()
    if button_icon and not button_icon.isNull():
        button_icon = icon.colorize_icon(button_icon, size=icon_size, color=icon_color)
    new_button = RoundButton(
        text=text, button_icon=button_icon, tooltip=tooltip, parent=parent
    )
    new_button.setFixedSize(QSize(button_width, button_height))
    if checkable:
        new_button.setCheckable(True)
        new_button.setChecked(checked)

    return new_button


def shadowed_button(
    text: str = "",
    button_icon: QIcon | None = None,
    icon_size: int | None = None,
    icon_color: tuple[int, int, int, int] or None = None,
    min_width: int | None = None,
    max_width: int | None = None,
    max_height: int | None = None,
    shadow_height: int = 4,
    force_upper: bool = False,
    tooltip: str = "",
    icon_color_theme: str | None = None,
    theme_updates: bool = True,
    parent: QWidget | None = None,
) -> ShadowedButton:
    """
    Creates a new shadowed button with the icon in a coloured box and a button shadow ath the bottom of the button.

    :param text: button text.
    :param button_icon: icon name to set.
    :param icon_size: optional icon size before DPI scaling.
    :param shadow_height: shadow height.
    :param icon_color: optional icon color which will fill the masked area of the icon.
    :param min_width: minimum width of the button in pixels.
    :param max_width: maximum width of the button in pixels.
    :param max_height: maximum height of the button in pixels.
    :param force_upper: whether to force text to be displayed in upper case/
    :param tooltip: optional tooltip.
    :param icon_color_theme: optional icon color theme to apply.
    :param theme_updates: whether to apply theme updates.
    :param parent: optional parent widget.
    :return: newly created shadowed button.
    """

    new_button = ShadowedButton(
        text=text,
        shadow_height=shadow_height,
        force_upper=force_upper,
        tooltip=tooltip,
        icon_color_theme=icon_color_theme,
        theme_updates=theme_updates,
        parent=parent,
    )
    if button_icon:
        new_button.set_icon(button_icon, colors=icon_color, size=icon_size)
    if max_height is not None:
        new_button.setFixedHeight(max_height)
    if max_width is not None:
        new_button.setMaximumWidth(max_width)
    if min_width is not None:
        new_button.setMinimumWidth(min_width)

    return new_button


def tool_button(
    text: str = "",
    button_icon: QIcon | None = None,
    tooltip: str = "",
    parent: QWidget | None = None,
) -> BaseToolButton:
    """
    Creates a new QToolButton instance.

    :param text: tool button text.
    :param button_icon: tool button icon.
    :param tooltip: optional button tooltip.
    :param parent: tool button parent widget.
    :return: new tool button instance.
    """

    new_tool_button = BaseToolButton(parent=parent)
    new_tool_button.setText(text)
    if icon:
        new_tool_button.image(button_icon)
    if tooltip:
        new_tool_button.setToolTip(tooltip)

    return new_tool_button


def left_aligned_button(
    text: str,
    button_icon: QIcon | None = None,
    tooltip: str = "",
    icon_size_override: int | None = None,
    transparent_background: bool = False,
    padding_override: tuple[int, int, int, int] | None = None,
    alignment: str = "left",
    show_left_click_menu_indicator: bool = False,
    parent: QWidget | None = None,
) -> LeftAlignedButton:
    """
    Creates a left aligned button.

    :param text: button text.
    :param button_icon: button icon.
    :param tooltip: button tooltip.
    :param icon_size_override:
    :param transparent_background:
    :param padding_override:
    :param alignment:
    :param show_left_click_menu_indicator:
    :param parent:
    :return: left aligned button instance.
    """

    icon_size = dpi.dpi_scale(icon_size_override if icon_size_override else 16)
    padding = (
        padding_override if padding_override else dpi.margins_dpi_scale([7, 4, 4, 4])
    )
    alignment_text = f"text-align: {alignment};"
    padding_text = (
        f"padding-left: {padding[0]}px; padding-top: {padding[1]}px; "
        f"padding-right: {padding[2]}px; padding-bottom: {padding[3]}px"
    )
    menu_indicator = (
        ""
        if show_left_click_menu_indicator
        else "QPushButton::menu-indicator{image: none;};"
    )
    transparency = (
        "" if not transparent_background else "background-color: transparent;"
    )
    new_button = LeftAlignedButton(
        text, button_icon=button_icon, tooltip=tooltip, parent=parent
    )
    new_button.setIconSize(QSize(icon_size, icon_size))
    new_button.setStyleSheet(
        "QPushButton {} {} {} {} {} \n{}".format(
            "{", alignment_text, padding_text, transparency, "}", menu_indicator
        )
    )

    return new_button


def styled_button(
    text: str = "",
    button_icon: QIcon | None = None,
    icon_size: int = 16,
    icon_color: tuple[int, int, int] or None = None,
    overlay_icon_color: tuple[int, int, int] or None = None,
    overlay_icon: QIcon | None = None,
    icon_color_theme: str | None = None,
    min_width: int | None = None,
    max_width: int | None = None,
    min_height: int | None = None,
    max_height: int | None = None,
    width: int | None = None,
    height: int | None = None,
    style: int = uiconsts.ButtonStyles.Default,
    tooltip: str = "",
    theme_updates: bool = True,
    checkable: bool = False,
    checked: bool = False,
    force_upper: bool = False,
    button_width: int | None = None,
    button_height: int | None = None,
    parent: QWidget | None = None,
) -> QPushButton | BaseButton | BasePushButton | ShadowedButton | RoundButton:
    """
    Creates a new button with the given options.

    Style 0: Default button with optional text or icon.
    Style 1: Default button with transparent background.
    Style 2: Button with shadow underline (icon in a colored box).
    Style 3: Rounded button with a background color and a colored icon.
    Style 4: Default style using standard Qt PushButton.
    Style 5: Regular Qt label with a small button beside.

    :param text: button text.
    :param button_icon: icon name or QIcon instance.
    :param icon_size: size of the icon in pixels.
    :param icon_color: icon color in 0 to 255 range.
    :param overlay_icon_color: color of the overlay image icon.
    :param overlay_icon: the name of the icon image that overlay on top of the original icon.
    :param icon_color_theme: color attribute that should be applied from current applied theme.
    :param min_width: minimum width of the button in pixels.
    :param max_width: maximum width of the button in pixels.
    :param min_height: minimum height of the button in pixels.
    :param max_height: maximum height of the button in pixels.
    :param width: fixed width of the button in pixels. This one overrides the values defined in min/max values.
    :param height: fixed height of the button in pixels. This one overrides the values defined in min/max values.
    :param style: the style of the button.
    :param tooltip: tooltip as seen with mouse over.
    :param theme_updates: whether  button style will be updated when current style changes.
    :param checkable: whether the button can be checked.
    :param checked: whether (if checkable is True) button is checked by default.
    :param force_upper: whether to show button text as uppercase.
    :param button_width: optional button width.
    :param button_height: optional button height.
    :param parent: parent widget.
    :return: newly created button.
    .note:: button icons are always squared.
    """

    min_width = min_width if width is None else width
    max_width = max_width if width is None else width
    min_height = min_height if height is None else height
    max_height = max_height if height is None else height

    if style in (
        uiconsts.ButtonStyles.Default,
        uiconsts.ButtonStyles.TransparentBackground,
    ):
        new_button = base_button(
            text=text,
            button_icon=button_icon,
            icon_size=icon_size,
            icon_color=icon_color,
            icon_color_theme=icon_color_theme,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            style=style,
            tooltip=tooltip,
            theme_updates=theme_updates,
            checkable=checkable,
            checked=checked,
            parent=parent,
        )

        # TODO: Remove this once we have our custom icon hover color change implemented
        if style == uiconsts.ButtonStyles.TransparentBackground:
            new_button.setStyleSheet("background-color: transparent;")

    elif style == uiconsts.ButtonStyles.IconShadow:
        new_button = shadowed_button(
            text=text,
            button_icon=button_icon,
            icon_color=icon_color,
            icon_color_theme=icon_color_theme,
            min_width=min_width,
            max_width=max_width,
            max_height=max_height,
            tooltip=tooltip,
            theme_updates=theme_updates,
            force_upper=force_upper,
            parent=parent,
        )
    elif style == uiconsts.ButtonStyles.DefaultQt:
        new_button = regular_button(
            text=text,
            button_icon=button_icon,
            icon_size=icon_size,
            icon_color=icon_color,
            overlay_icon_color=overlay_icon_color,
            overlay_icon=overlay_icon,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            tooltip=tooltip,
            checkable=checkable,
            checked=checked,
            parent=parent,
        )
    elif style == uiconsts.ButtonStyles.Rounded:
        new_button = rounded_button(
            text=text,
            button_icon=button_icon,
            icon_size=icon_size,
            icon_color=icon_color,
            tooltip=tooltip,
            button_width=width,
            button_height=height,
            checkable=checkable,
            checked=checked,
            parent=parent,
        )
    elif style == uiconsts.ButtonStyles.SmallLabel:
        new_button = LabelSmallButton(
            text=text, button_icon=button_icon, tooltip=tooltip, parent=parent
        )
    else:
        logger.warning(
            f'Button style "{style}" is not supported. Default button will be created'
        )
        new_button = regular_button(
            text=text,
            button_icon=button_icon,
            icon_size=icon_size,
            icon_color=icon_color,
            overlay_icon_color=overlay_icon_color,
            overlay_icon=overlay_icon,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            tooltip=tooltip,
            checkable=checkable,
            checked=checked,
            parent=parent,
        )

    if button_width is not None:
        new_button.setFixedWidth(button_width)
    if button_height is not None:
        new_button.setFixedHeight(button_height)

    return new_button


def ok_cancel_buttons(
    ok_text: str = "Ok", cancel_text: str = "Cancel", parent: QWidget | None = None
) -> OkCancelButtons:
    """
    Creates a new OkCancelButtons instance.

    :param ok_text: text for the OK button.
    :param cancel_text: text for the Cancel button.
    :param parent: parent widget.
    :return: newly created OkCancelButtons instance.
    """

    return OkCancelButtons(ok_text=ok_text, cancel_text=cancel_text, parent=parent)


def checkbox(
    text: str = "",
    checked: bool = False,
    tooltip: str = "",
    parent: QWidget | None = None,
) -> QCheckBox:
    """
    Creates a basic QCheckBox widget.

    :param str text: checkbox text.
    :param bool checked: true to check by default; False otherwise.
    :param str tooltip: checkbox tooltip.
    :param QWidget parent: parent widget.
    :return: newly x
    """

    new_checkbox = QCheckBox(text=text, parent=parent)
    new_checkbox.setChecked(checked)
    if tooltip:
        new_checkbox.setToolTip(tooltip)

    return new_checkbox


def checkbox_widget(
    text: str = "",
    checked: bool = False,
    tooltip: str = "",
    enable_menu: bool = True,
    right: bool = False,
    label_ratio: int = 0,
    box_ratio: int = 0,
    parent: QWidget | None = None,
) -> BaseCheckBoxWidget:
    """
    Creates a BaseCheckbox widget instance.

    :param str text: checkbox text.
    :param bool checked: true to check by default; False otherwise.
    :param str tooltip: checkbox tooltip.
    :param bool enable_menu: whether to enable checkbox menu.
    :param bool right: whether checkbox label should be placed to the right.
    :param int label_ratio: label layout ratio.
    :param int box_ratio: combobox layout ratio.
    :param QWidget parent: parent widget.
    :return: newly created combo box.
    """

    return BaseCheckBoxWidget(
        text=text,
        checked=checked,
        tooltip=tooltip,
        enable_menu=enable_menu,
        label_ratio=label_ratio,
        box_ratio=box_ratio,
        right=right,
        parent=parent,
    )


def string_edit(
    label_text: str = "",
    edit_text: str = "",
    edit_placeholder: str = "",
    button_text: str | None = None,
    edit_width: int | None = None,
    label_ratio: int = 1,
    button_ratio: int = 1,
    edit_ratio: int = 5,
    tooltip: str = "",
    orientation: Qt.Orientation = Qt.Horizontal,
    enable_menu: bool = False,
    parent: QWidget | None = None,
) -> StringEdit:
    """
    Creates a new string edit widget.

    :param label_text: The text for the label. Defaults to an empty string.
    :param edit_text: The initial text for the text box. Defaults to an empty string.
    :param edit_placeholder: The placeholder text for the text box. Defaults to an empty string.
    :param button_text: The text for the optional button. Defaults to None.
    :param edit_width: The width of the text box. Defaults to None.
    :param label_ratio: The ratio of the label width. Defaults to 1.
    :param button_ratio: The ratio of the button width. Defaults to 1.
    :param edit_ratio: The ratio of the text box width. Defaults to 5.
    :param tooltip: The tooltip text for the widget. Defaults to an empty string.
    :param orientation: The orientation of the widget (horizontal or vertical). Defaults to Qt.Horizontal.
    :param enable_menu: If True, enables a context menu for the text box. Defaults to False.
    :param parent: The parent widget. Defaults to None.
    :return: new string edit widget instance.
    """

    return StringEdit(
        label=label_text,
        edit_text=edit_text,
        edit_placeholder=edit_placeholder,
        button_text=button_text,
        edit_width=edit_width,
        label_ratio=label_ratio,
        button_ratio=button_ratio,
        edit_ratio=edit_ratio,
        tooltip=tooltip,
        orientation=orientation,
        enable_menu=enable_menu,
        parent=parent,
    )


def int_edit(
    label_text: str = "",
    edit_text: str = "",
    edit_placeholder: str = "",
    button_text: str | None = None,
    edit_width: int | None = None,
    label_ratio: int = 1,
    button_ratio: int = 1,
    edit_ratio: int = 5,
    tooltip: str = "",
    orientation: Qt.Orientation = Qt.Horizontal,
    enable_menu: bool = False,
    slide_distance: float = 0.05,
    small_slide_distance: float = 0.01,
    large_slide_distance: float = 1.0,
    scroll_distance: float = 1.0,
    update_on_slide_tick: bool = True,
    parent: QWidget | None = None,
) -> IntEdit:
    """
    Creates a new integer edit widget.

    :param label_text: The text for the label. Defaults to an empty string.
    :param edit_text: The initial text for the text box. Defaults to an empty string.
    :param edit_placeholder: The placeholder text for the text box. Defaults to an empty string.
    :param button_text: The text for the optional button. Defaults to None.
    :param edit_width: The width of the text box. Defaults to None.
    :param label_ratio: The ratio of the label width. Defaults to 1.
    :param button_ratio: The ratio of the button width. Defaults to 1.
    :param edit_ratio: The ratio of the text box width. Defaults to 5.
    :param tooltip: The tooltip text for the widget. Defaults to an empty string.
    :param orientation: The orientation of the widget (horizontal or vertical). Defaults to Qt.Horizontal.
    :param enable_menu: If True, enables a context menu for the text box. Defaults to False.
    :param slide_distance: The distance to slide when using the arrow keys. Defaults to 0.05.
    :param small_slide_distance: The distance to slide when using the arrow keys with the Shift key. Defaults to 0.01.
    :param large_slide_distance: The distance to slide when using the arrow keys with the Ctrl key. Defaults to 1.0.
    :param scroll_distance: The distance to slide when using the mouse wheel. Defaults to 1.0.
    :param update_on_slide_tick: If True, updates the value on each slide tick. Defaults to True.
    :param parent: The parent widget. Defaults to None.
    :return: new string edit widget instance.
    """

    return IntEdit(
        label=label_text,
        edit_text=edit_text,
        edit_placeholder=edit_placeholder,
        button_text=button_text,
        edit_width=edit_width,
        label_ratio=label_ratio,
        button_ratio=button_ratio,
        edit_ratio=edit_ratio,
        tooltip=tooltip,
        orientation=orientation,
        enable_menu=enable_menu,
        slide_distance=slide_distance,
        small_slide_distance=small_slide_distance,
        large_slide_distance=large_slide_distance,
        scroll_distance=scroll_distance,
        update_on_slide_tick=update_on_slide_tick,
        parent=parent,
    )


def float_edit(
    label_text: str = "",
    edit_text: str = "",
    edit_placeholder: str = "",
    button_text: str | None = None,
    edit_width: int | None = None,
    label_ratio: int = 1,
    button_ratio: int = 1,
    edit_ratio: int = 5,
    tooltip: str = "",
    orientation: Qt.Orientation = Qt.Horizontal,
    enable_menu: bool = False,
    rounding: int = 3,
    slide_distance: float = 0.05,
    small_slide_distance: float = 0.01,
    large_slide_distance: float = 1.0,
    scroll_distance: float = 1.0,
    update_on_slide_tick: bool = True,
    parent: QWidget | None = None,
) -> FloatEdit:
    """
    Creates a new integer edit widget.

    :param label_text: The text for the label. Defaults to an empty string.
    :param edit_text: The initial text for the text box. Defaults to an empty string.
    :param edit_placeholder: The placeholder text for the text box. Defaults to an empty string.
    :param button_text: The text for the optional button. Defaults to None.
    :param edit_width: The width of the text box. Defaults to None.
    :param label_ratio: The ratio of the label width. Defaults to 1.
    :param button_ratio: The ratio of the button width. Defaults to 1.
    :param edit_ratio: The ratio of the text box width. Defaults to 5.
    :param tooltip: The tooltip text for the widget. Defaults to an empty string.
    :param orientation: The orientation of the widget (horizontal or vertical). Defaults to Qt.Horizontal.
    :param enable_menu: If True, enables a context menu for the text box. Defaults to False.
    :param rounding: The number of decimal places to round to. Defaults to 3.
    :param slide_distance: The distance to slide when using the arrow keys. Defaults to 0.05.
    :param small_slide_distance: The distance to slide when using the arrow keys with the Shift key. Defaults to 0.01.
    :param large_slide_distance: The distance to slide when using the arrow keys with the Ctrl key. Defaults to 1.0.
    :param scroll_distance: The distance to slide when using the mouse wheel. Defaults to 1.0.
    :param update_on_slide_tick: If True, updates the value on each slide tick. Defaults to True.
    :param parent: The parent widget. Defaults to None.
    :return: new string edit widget instance.
    """

    return FloatEdit(
        label=label_text,
        edit_text=edit_text,
        edit_placeholder=edit_placeholder,
        button_text=button_text,
        edit_width=edit_width,
        label_ratio=label_ratio,
        button_ratio=button_ratio,
        edit_ratio=edit_ratio,
        tooltip=tooltip,
        orientation=orientation,
        enable_menu=enable_menu,
        rounding=rounding,
        slide_distance=slide_distance,
        small_slide_distance=small_slide_distance,
        large_slide_distance=large_slide_distance,
        scroll_distance=scroll_distance,
        update_on_slide_tick=update_on_slide_tick,
        parent=parent,
    )


def collapsible_frame(
    title: str,
    thin: bool = False,
    tooltip: str | None = None,
    collapsed: bool = False,
    collapsable: bool = True,
    checkable: bool = False,
    checked: bool = True,
    content_margins: tuple[int, int, int, int] = uiconsts.MARGINS,
    content_spacing: int = uiconsts.SPACING,
    parent: QWidget | None = None,
) -> CollapsibleFrame | CollapsibleFrameThin:
    """
    Creates a collapsible frame widget.

    :param title: The title of the frame.
    :param thin: Whether to use a thin frame.
    :param tooltip: The tooltip of the frame.
    :param collapsed: Whether the frame is initially collapsed.
    :param collapsable: Whether the frame is collapsible.
    :param checkable: Whether the frame is checkable.
    :param checked: Whether the frame is checked.
    :param content_margins: The content margins.
    :param content_spacing: The content spacing.
    :param parent: The parent widget.
    :return: new collapsible frame widget instance.
    """

    if not thin:
        return CollapsibleFrame(
            title=title,
            tooltip=tooltip,
            collapsed=collapsed,
            collapsable=collapsable,
            checkable=checkable,
            checked=checked,
            content_margins=content_margins,
            content_spacing=content_spacing,
            parent=parent,
        )
    else:
        return CollapsibleFrameThin(
            title=title,
            tooltip=tooltip,
            collapsed=collapsed,
            collapsable=collapsable,
            checkable=checkable,
            checked=checked,
            content_margins=content_margins,
            content_spacing=content_spacing,
            parent=parent,
        )


def divider(
    text: str | None = None,
    shadow: bool = True,
    orientation: Qt.Orientation = Qt.Horizontal,
    alignment: Qt.AlignmentFlag = Qt.AlignLeft,
    parent: QWidget | None = None,
) -> Divider:
    """
    Creates a new divider widget.

    :param text: The text to display on the divider. Defaults to None.
    :param shadow: Whether to display a shadow. Defaults to True.
    :param orientation: The orientation of the divider. Defaults to Qt.Horizontal.
    :param alignment: The alignment of the text. Defaults to Qt.AlignLeft.
    :param parent: The parent widget. Defaults to None.
    :return: new divider widget instance.
    """

    return Divider(
        text=text,
        shadow=shadow,
        orientation=orientation,
        alignment=alignment,
        parent=parent,
    )


def label_divider(text: str = "", parent: QWidget | None = None) -> LabelDivider:
    """
    Creates a new label divider widget.

    :param text: The text to display on the divider. Defaults to an empty string.
    :param parent: The parent widget. Defaults to None.
    :return: new label divider widget instance.
    """

    return LabelDivider(text=text, parent=parent)


def horizontal_line(parent: QWidget | None = None) -> HorizontalLine:
    """
    Creates a new horizontal line widget.

    :param parent: The parent widget. Defaults to None.
    :return: new horizontal line widget instance.
    """

    return HorizontalLine(parent=parent)


def vertical_line(parent: QWidget | None = None) -> VerticalLine:
    """
    Creates a new vertical line widget.

    :param parent: The parent widget. Defaults to None.
    :return: new vertical line widget instance.
    """

    return VerticalLine(parent=parent)


def radio_button_group(
    radio_names: Sequence[str] | None = None,
    tooltips: Sequence[str] | None = None,
    default: int | None = 0,
    vertical: bool = False,
    margins: tuple[int, int, int, int] = (
        uiconsts.REGULAR_PADDING,
        uiconsts.REGULAR_PADDING,
        uiconsts.REGULAR_PADDING,
        0,
    ),
    spacing: int = uiconsts.SMALL_SPACING,
    alignment: Qt.AlignmentFlag | None = None,
    parent: QWidget | None = None,
) -> RadioButtonGroup:
    """
    Creates a radio button group.

    :param radio_names: optional list of radio button names.
    :param tooltips: optional list of tooltips for each one of the radio buttons.
    :param default: optional default button to be checked.
    :param vertical: whether to create buttons horizontally or vertically.
    :param margins: optional margins used for buttons layout.
    :param spacing: optional spacing used for buttons layout.
    :param alignment: optional align for buttons layout.
    :param parent: parent widget.
    """

    return RadioButtonGroup(
        radio_names=radio_names,
        tooltips=tooltips,
        default=default,
        vertical=vertical,
        margins=margins,
        spacing=spacing,
        alignment=alignment,
        parent=parent,
    )


def show_custom_dialog(
    custom_widget: QWidget,
    title: str = "Confirm",
    message: str = "Proceed",
    dialog_icon: str | QIcon = MessageBoxBase.QUESTION,
    default: int = 0,
    button_a: str | None = "OK",
    button_b: str | None = "Cancel",
    button_c: str | None = None,
    parent: QWidget | None = None,
) -> tuple[str, QWidget]:
    """
    Function that shows a dialog with a custom widget.

    :param custom_widget: Custom widget to show in the dialog.
    :param title: Title of the dialog.
    :param message: Message to show in the dialog.
    :param dialog_icon: Icon to show in the dialog.
    :param default: Default button index.
    :param button_a: Text of the first button.
    :param button_b: Text of the second button.
    :param button_c: Text of the third button.
    :param parent: Parent widget of the dialog.
    :return: tuple with the result of the dialog and the custom widget.
    """

    return CustomDialog.show_dialog(
        custom_widget=custom_widget,
        title=title,
        message=message,
        icon=dialog_icon,
        default=default,
        button_a=button_a,
        button_b=button_b,
        button_c=button_c,
        parent=parent,
    )


def line_tab_widget(
    alignment: Qt.AlignmentFlag | None = Qt.AlignCenter, parent: QWidget | None = None
) -> LineTabWidget:
    """
    Creates a new line tab widget.

    :param alignment: The alignment of the tab widget.
    :param parent: The parent widget. Defaults to None.
    :return: new line tab widget instance.
    """

    return LineTabWidget(alignment=alignment, parent=parent)


def sliding_opacity_stacked_widget(
    parent: QWidget | None = None,
) -> SlidingOpacityStackedWidget:
    """
    Creates a new sliding opacity stack widget.

    :param parent: The parent widget. Defaults to None.
    :return: new sliding opacity stack widget instance.
    """

    return SlidingOpacityStackedWidget(parent=parent)


def accordion(parent: QWidget | None = None) -> Accordion:
    """
    Creates a new accordion widget.

    :param parent: The parent widget. Defaults to None.
    :return: new accordion widget instance.
    """

    return Accordion(parent=parent)


def overlay_loading_widget(parent: QWidget | None = None):
    """
    Creates a new overlay loading widget.

    :param parent: The parent widget. Defaults to None.
    :return: new overlay loading widget instance.
    """

    return OverlayLoadingWidget(parent=parent)
