from __future__ import annotations

import uuid
import typing
from typing import Union, Iterator, Any

from Qt.QtCore import Qt, QObject, QSize, QModelIndex
from Qt.QtWidgets import QMenu, QStyledItemDelegate
from Qt.QtGui import QIcon, QColor, QFont

from ... import dpi
from .roles import UID_ROLE
from .delegates import HtmlDelegate

if typing.TYPE_CHECKING:
    from .models import TableModel


# noinspection PyMethodMayBeStatic
class BaseDataSource(QObject):
    """
    Base class used to represent table rows and tree items.
    """

    _ENABLED_COLOR = QColor("#C4C4C4")
    _DISABLED_COLOR = QColor("#5E5E5E")

    def __init__(
        self,
        header_text: str | None = None,
        model: TableModel | None = None,
        parent: BaseDataSource | None = None,
    ):
        super().__init__()

        self._model = model
        self._header_text = header_text or ""
        self._parent = parent
        self._children: list[BaseDataSource] = []
        self._column_index: int = 0
        self._uid = str(uuid.uuid4())
        self._default_text_margin = dpi.dpi_scale(5)
        self._font: QFont | None = None

    def __eq__(self, other: Any) -> bool:
        """
        Returns whether the data source is equal to the given object or not.

        :param other: object to compare to.
        :return: True if the data source is equal to the given object; False otherwise.
        """

        if not isinstance(other, BaseDataSource):
            return False

        return self.uid == other.uid

    @property
    def uid(self) -> str:
        """
        Getter method that returns the unique identifier of the data source.

        :return: unique identifier of the data source.
        """

        return self._uid

    @property
    def model(self) -> TableModel | None:
        """
        Getter method that returns the model of the data source.

        :return: model of the data source.
        """

        return self._model

    @model.setter
    def model(self, value: TableModel | None):
        """
        Setter method that sets the model of the data source.

        :param value: model to set.
        """

        self._model = value

    @property
    def children(self) -> list[BaseDataSource]:
        """
        Getter method that returns children of the data source.

        :return: children of the data source.
        """

        return self._children

    @property
    def column_index(self) -> int:
        """
        Getter method that returns the column index of the data source.

        :return: column index of the data source.
        """

        return self._column_index

    @column_index.setter
    def column_index(self, value: int):
        """
        Setter method that sets the column index of the data source.

        :param value: column index to set.
        """

        self._column_index = value

    def is_root(self) -> bool:
        """
        Returns whether the data source is a root item or not.

        :return: True if the data source is a root item; False otherwise.
        """

        return self._parent is None

    def row_count(self) -> int:
        """
        Returns the total row count of the data source.

        :return: row count.
        """

        return len(self._children)

    def column_count(self) -> int:
        """
        Returns the total column count of the data source.

        :return: column count.
        """

        return 1

    def has_children(self) -> bool:
        """
        Returns whether the data source has children or not.

        :return: True if the data source has children; False otherwise.
        """

        return self.row_count() > 0

    def parent_source(self) -> BaseDataSource | None:
        """
        Returns the parent data source.

        :return: parent data source.
        """

        return self._parent

    def set_parent_source(self, parent_source: BaseDataSource):
        """
        Sets the parent data source.

        :param parent_source: parent data source to set.
        """

        if self._parent is not None:
            try:
                self._parent.children.remove(self)
            except ValueError:
                pass
        self.model = parent_source.model
        self._parent = parent_source
        parent_source.add_child(self)

    def child(self, index: int) -> BaseDataSource | None:
        """
        Returns the child at the given index.

        :param index: index to get the child for.
        :return: child at the given index.
        """

        if index < self.row_count():
            return self.children[index]

        return None

    def add_child(self, child: BaseDataSource) -> BaseDataSource | None:
        """
        Adds a child to the data source.

        :param child: child to add.
        :return: child that was added.
        """

        if child in self._children:
            return None

        child.model = self.model
        self._children.append(child)

        return child

    def insert_child(self, index: int, child: BaseDataSource) -> bool:
        """
        Inserts a child at the given index.

        :param index: index to insert the child at.
        :param child: child to insert.
        :return: True if the child was inserted successfully; False otherwise.
        """

        if child in self._children:
            return False

        child.model = self.model
        self._children.insert(index, child)

        return True

    def insert_children(self, index: int, children: list[BaseDataSource]):
        """
        Inserts children at the given index.

        :param index: index to insert the children at.
        :param children: children to insert.
        """

        for child in children:
            child.model = self.model
        self._children[index:index] = children

    def iterate_children(self, recursive: bool = True) -> Iterator[BaseDataSource]:
        """
        Iterates over the children of the data source.

        :param recursive: whether to iterate recursively or not.
        :return: iterator of the children.
        """

        for child in self._children:
            yield child
            if not recursive:
                continue
            for sub_child in child.iterate_children(recursive=recursive):
                yield sub_child

    def index(self) -> int:
        """
        Returns the index of the data source.

        :return: index of the data source.
        """

        parent = self.parent_source()
        if parent is not None and parent.children:
            return parent.children.index(self)

        return 0

    def model_index(self) -> QModelIndex:
        """
        Returns the model index of the data source.

        :return: model index of the data source.
        """

        if self.model is None:
            return QModelIndex()

        indices = self.model.match(
            self.model.index(0, 0),
            UID_ROLE,
            self.uid,
            1,
            Qt.MatchExactly | Qt.MatchRecursive,
        )

        return indices[0] if indices else QModelIndex()

    def width(self) -> int:
        """
        Returns the width of the data source.

        :return: width of the data source.
        """

        return 0

    def custom_roles(self, index: int) -> list[int]:
        """
        Returns the custom roles at the given index.

        :param index: index to get the custom roles for.
        :return: custom roles at the given index.
        """

        return []

    def data(self, index: int) -> Any:
        """
        Returns the data at the given index.

        :param index: index to get the data for.
        :return: data at the given index.
        """

        return ""

    def data_by_role(self, index: int, role: Qt.ItemDataRole) -> Any:
        """
        Returns the data at the given index by role.

        :param index: index to get the data for.
        :param role: role to get the data for.
        :return: data at the given index by role.
        """

        return ""

    def set_data(self, index: int, value: Any):
        """
        Sets the data at the given index.

        :param index: index to set the data for.
        :param value: value to set.
        """

        pass

    def set_data_by_custom_role(self, index: int, data: Any, role: Qt.ItemDataRole):
        """
        Sets the data at the given index by role.

        :param index: index to set the data for.
        :param data: data to set.
        :param role: role to set the data for.
        """

        pass

    def user_object(self, index: int) -> Any:
        """
        Returns the user object at the given index.

        :param index: index to get the user object for.
        :return: user object at the given index.
        """

        if index < self.row_count():
            return self.user_objects()[index]

    def user_objects(self) -> list[Any]:
        """
        Returns the user objects.

        :return: user objects.
        """

        return self._children

    def set_user_objects(self, user_objects: list[BaseDataSource]):
        """
        Sets the user objects.

        :param user_objects: user objects to set.
        """

        self._children = user_objects

    def can_fetch_more(self) -> bool:
        """
        Returns whether more data can be fetched or not.

        :return: True if more data can be fetched; False otherwise.
        """

        return False

    def fetch_more(self):
        """
        Fetches more data.
        """

        pass

    def header_text(self, index: int) -> str:
        """
        Returns the header text at the given index.

        :param index: index to get the header text for.
        :return: header text at the given index.
        """

        return self._header_text

    def header_icon(self) -> QIcon:
        """
        Returns the header icon.

        :return: header icon.
        """

        return QIcon()

    def header_vertical_text(self, index: int) -> str | None:
        """
        Returns the header vertical text at the given index.

        :param index: index to get the header vertical text for.
        :return: header vertical text at the given index. If None, header text will not be displayed.
        """

        return None

    def header_vertical_icon(self, index: int) -> QIcon:
        """
        Returns the header vertical icon at the given index.

        :param index: index to get the header vertical icon for.
        :return: header vertical icon at the given index.
        """

        return QIcon()

    def tooltip(self, index: int) -> str:
        """
        Returns the tooltip at the given index.

        :param index: index to get the tooltip for.
        :return: tooltip at the given index.
        """

        model = self._model
        if model is None:
            return ""

        return f"{self.header_text(index)}:{str(self.data(index))}\n"

    def set_tooltip(self, index: int, value: str):
        """
        Sets the tooltip at the given index.

        :param index: index to set the tooltip for.
        :param value: value to set.
        """

        pass

    def icon_size(self, index: int) -> QSize:
        """
        Returns the icon size at the given index.

        :param index: index to get the icon size for.
        :return: icon size at the given index.
        """

        return QSize(16, 16)

    def icon(self, index: int) -> QIcon | None:
        """
        Returns the icon at the given index.

        :param index: index to get the icon for.
        :return: icon at the given index.
        """

        return None

    def foreground_color(self, index: int) -> QColor:
        """
        Returns the foreground color at the given index.

        :param index: index to get the foreground color for.
        :return: foreground color at the given index.
        """

        return (
            self._ENABLED_COLOR
            if self.is_enabled(index) and self.is_editable(index)
            else self._DISABLED_COLOR
        )

    def background_color(self, index: int) -> QColor | None:
        """
        Returns the background color at the given index.

        :param index: index to get the background color for.
        :return: background color at the given index.
        """

        return None

    def display_changed_color(self, index: int) -> QColor | None:
        """
        Returns the display changed color at the given index.

        :param index: index to get the display changed color for.
        :return: display changed color at the given index.
        """

        return None

    def text_margin(self, index: int) -> int:
        """
        Returns the text margin at the given index.

        :param index: index to get the text margin for.
        :return: text margin at the given index.
        """

        return self._default_text_margin

    def alignment(self, index: int) -> Qt.AlignmentFlag | Qt.Alignment:
        """
        Returns the alignment at the given index.

        :param index: index to get the alignment for.
        :return: alignment at the given index.
        """

        return Qt.AlignVCenter

    def font(self, index: int) -> QFont | None:
        """
        Returns the font at the given index.

        :param index: index to get the font for.
        :return: font at the given index.
        """

        return self._font

    def is_checkable(self, index: int) -> bool:
        """
        Returns whether the data at the given index is checkable or not.

        :param index: index to check.
        :return: True if the data is checkable; False otherwise.
        """

        return False

    def is_enabled(self, index: int) -> bool:
        """
        Returns whether the data at the given index is enabled or not.

        :param index: index to check.
        :return: True if the data is enabled; False otherwise.
        """

        return True

    def is_selectable(self, index: int) -> bool:
        """
        Returns whether the data at the given index is selectable or not.

        :param index: index to check.
        :return: True if the data is selectable; False otherwise.
        """

        return True

    def is_editable(self, index: int) -> bool:
        """
        Returns whether the data at the given index is editable or not.

        :param index: index to check.
        :return: True if the data is editable; False otherwise.
        """

        return self.is_enabled(index)

    def supports_drag(self, index: int) -> bool:
        """
        Returns whether the data at the given index supports drag or not.

        :param index: index to check.
        :return: True if the data supports drag; False otherwise.
        """

        return False

    def supports_drop(self, index: int) -> bool:
        """
        Returns whether the data at the given index supports drop or not.

        :param index: index to check.
        :return: True if the data supports drop; False otherwise.
        """

        return False

    def mime_data(self, indices: list[int]) -> dict:
        """
        Returns the mime data for the given indices.

        :param indices: indices to get the mime data for.
        :return: mime data for the given indices.
        """

        return {}

    def drop_mime_data(self, items: list[str], action: Qt.DropAction) -> dict:
        """
        Drops the mime data for the given items and action.

        :param items: items to drop the mime data for.
        :param action: drop action to perform.
        :return: mime data for the given items and action.
        """

        return {}

    def insert_row_data_source(self, index: int):
        """
        Inserts row data source at the given index.

        :param index: index to insert the row data source at.
        """

        pass

    def insert_row_data_sources(self, index: int, count: int) -> bool:
        """
        Inserts row data sources at the given index.

        :param index: index to insert the row data sources at.
        :param count: number of row data sources to insert.
        :return: True if the row data sources were inserted successfully; False otherwise.
        """

        return False

    def remove_row_data_source(self, index) -> bool:
        """
        Removes row data source at the given index.

        :param index: index to remove the row data source at.
        :return: True if the row data source was removed successfully; False otherwise.
        """

        if index < self.row_count():
            del self._children[index]
            return True

        return False

    def remove_row_data_sources(self, index: int, count: int) -> bool:
        """
        Removes row data sources at the given index.

        :param index: index to remove the row data sources at.
        :param count: number of row data sources to remove.
        :return: True if the row data sources were removed successfully; False otherwise.
        """

        if index < self.row_count():
            self._children = self._children[:index] + self._children[index + count :]
            return True

        return False

    def insert_column_data_sources(self, index: int, count: int) -> bool:
        """
        Inserts column data sources at the given index.

        :param index: index to insert the column data sources at.
        :param count: number of column data sources to insert.
        :return: True if the column data sources were inserted successfully; False otherwise.
        """

        return False

    def remove_column_data_sources(self, index: int, count: int) -> bool:
        """
        Removes column data sources at the given index.

        :param index: index to remove the column data sources at.
        :param count: number of column data sources to remove.
        :return: True if the column data sources were removed successfully; False otherwise.
        """

        return False

    def sort(self, index: int = 0, order: Qt.SortOrder = Qt.DescendingOrder):
        """
        Sorts the data source.

        :param index: index to sort by.
        :param order: sort order.
        """

        def element(key):
            return key[1]

        to_sort = [(obj, self.data(i)) for i, obj in enumerate(self.user_objects())]
        if order == Qt.DescendingOrder:
            results = [i[0] for i in sorted(to_sort, key=element, reverse=True)]
        else:
            results = [i[0] for i in sorted(to_sort, key=element)]

        self.set_user_objects(results)

    def delegate(self, parent: QObject) -> QStyledItemDelegate:
        """
        Returns the delegate for the data source.

        :param parent: parent widget.
        :return: delegate for the data source.
        """

        return HtmlDelegate(parent=parent)

    def context_menu(self, selection: list[int], menu: QMenu):
        """
        Function that is called before the context menu is shown.
        Allows to add custom actions to the context menu.

        :param selection: selected indexes to get the context menu for.
        :param menu: menu to set the context menu for.
        """

        pass

    def on_vertical_header_selection(self, index: int):
        """
        Function that is triggered by the table view (if this source is attached to one)
        when the vertical header is clicked.

        :param index: row index.
        """

        pass


# noinspection PyMethodMayBeStatic
class RowIntNumericDataSource(BaseDataSource):
    """
    Class used to represent table rows with integer data.
    """

    def minimum(self, index: int) -> float:
        """
        Returns the minimum value at the given index.

        :param index: index to get the minimum value for.
        :return: minimum value at the given index.
        """

        return -99999

    def maximum(self, index: int) -> float:
        """
        Returns the maximum value at the given index.

        :param index: index to get the maximum value for.
        :return: maximum value at the given index.
        """

        return 99999


# noinspection PyMethodMayBeStatic
class RowDoubleNumericDataSource(BaseDataSource):
    """
    Class used to represent table rows with double data.
    """

    def minimum(self, index: int) -> float:
        """
        Returns the minimum value at the given index.

        :param index: index to get the minimum value for.
        :return: minimum value at the given index.
        """

        return -99999.0

    def maximum(self, index: int) -> float:
        """
        Returns the maximum value at the given index.

        :param index: index to get the maximum value for.
        :return: maximum value at the given index.
        """

        return 99999.0


class RowEnumerationDataSource(BaseDataSource):
    """
    Class used to represent table rows with enumeration data.
    """

    def __init__(
        self,
        header_text: str | None = None,
        model: TableModel | None = None,
        parent: BaseDataSource | None = None,
    ):
        super().__init__(header_text=header_text, model=model, parent=parent)

        self._enums: dict[int, list[str]] = {}
        self._current_index: dict[int, int] = {}

    # noinspection PyMethodMayBeStatic
    def enums(self, index: int) -> list[str]:
        """
        Returns the enumeration values at the given index.

        :param index: index to get the enumeration values for.
        :return: enumeration values at the given index.
        """

        return []

    def set_enums(self, index: int, enums: list[str]) -> bool:
        """
        Sets the enumeration values at the given index.

        :param index: index to set the enumeration values for.
        :param enums: enumeration values to set.
        :return: True if the enumeration values were set successfully; False otherwise.
        """

        current_enums = self._enums.get(index, [])
        new_index: int = 0
        if current_enums and index in self._current_index:
            current_enum_value = current_enums[self._current_index[index]]
            try:
                new_index = enums.index(current_enum_value)
            except ValueError:
                # This happens when the previous enum no longer exists.
                pass
        self._current_index[index] = new_index
        self._enums[index] = enums

        return True


class RowEnumerationButtonDataSource(BaseDataSource):
    """
    Class used to represent table rows with enumeration data.
    """

    def __init__(
        self,
        header_text: str | None = None,
        model: TableModel | None = None,
        parent: BaseDataSource | None = None,
    ):
        super().__init__(header_text=header_text, model=model, parent=parent)

        self._enums: dict[int, list[str]] = {}
        self._current_index: dict[int, int] = {}

    def enums(self, index: int) -> list[str]:
        """
        Returns the enumeration values at the given index.

        :param index: index to get the enumeration values for.
        :return: enumeration values at the given index.
        """

        return self._enums.get(index, [])


# noinspection PyMethodOverriding
class ColumnDataSource(BaseDataSource):
    """
    Class used to represent table columns.
    """

    def custom_roles(self, row_data_source: BaseDataSource, index: int) -> list[int]:
        """
        Overrides `custom_roles` to return the custom roles at the given index.

        :param row_data_source: row data source to get the custom roles for.
        :param index: index to get the custom roles for.
        :return: custom roles at the given index.
        """

        return []

    def data(self, row_data_source: BaseDataSource, index: int) -> Any:
        """
        Overrides `data` function to return the data at the given index.

        :param row_data_source: row data source to get the data for.
        :param index: column index to get the data for.
        :return: data at the given index.
        """

        return ""

    def data_by_role(
        self, row_data_source: BaseDataSource, index: int, role: Qt.ItemDataRole
    ) -> Any:
        """
        Overrides `data_by_role` function to return the data at the given index by role.

        :param row_data_source: row data source to get the data for.
        :param index: index to get the data for.
        :param role: role to get the data for.
        :return: data at the given index by role.
        """

        return False

    def set_data(self, row_data_source: BaseDataSource, index: int, value: Any):
        """
        Overrides `set_data` function to sets the data at the given index.

        :param row_data_source: row data source to set the data for.
        :param index: column index to set the data for.
        :param value: value to set.
        """

        pass

    def tooltip(self, row_data_source: BaseDataSource, index: int) -> str:
        """
        Overrides `tooltip` function to return the tooltip at the given index.

        :param row_data_source: row data source to get the tooltip for.
        :param index: index to get the tooltip for.
        :return: tooltip at the given index.
        """

        return ""

    def icon(self, row_data_source: BaseDataSource, index: int) -> QIcon | None:
        """
        Returns the icon at the given index.

        :param row_data_source: row data source to get the icon for.
        :param index: index to get the icon for.
        :return: icon at the given index.
        """

        return None

    def foreground_color(self, row_data_source: BaseDataSource, index: int) -> QColor:
        """
        Overrides `foreground_color` function to return the foreground color at the given index.

        :param row_data_source: row data source to get the foreground color for.
        :param index: index to get the foreground color for.
        :return: foreground color at the given index.
        """

        return (
            self._ENABLED_COLOR
            if self.is_enabled(row_data_source, index)
            and self.is_editable(row_data_source, index)
            else self._DISABLED_COLOR
        )

    def background_color(
        self, row_data_source: BaseDataSource, index: int
    ) -> QColor | None:
        """
        Overrides `background_color` function to return the background color at the given index.

        :param row_data_source: row data source to get the background color for.
        :param index: index to get the background color for.
        :return: background color at the given index.
        """

        return row_data_source.background_color(index)

    def display_changed_color(
        self, row_data_source: BaseDataSource, index: int
    ) -> QColor | None:
        """
        Overrides `display_changed_color` function  to return the display changed color at the given index.

        :param row_data_source: row data source to get the display changed color for.
        :param index: index to get the display changed color for.
        :return: display changed color at the given index.
        """

        return None

    def text_margin(self, row_data_source: BaseDataSource, index: int) -> int:
        """
        Overrides `text_margin` function to return the text margin at the given index.

        :param row_data_source: row data source to get the text margin for.
        :param index: index to get the text margin for.
        :return: text margin at the given index.
        """

        return row_data_source.text_margin(index)

    def alignment(
        self, row_data_source: BaseDataSource, index: int
    ) -> Qt.AlignmentFlag | Qt.Alignment:
        """
        Overrides `alignment` function to return the alignment at the given index.

        :param row_data_source: row data source to get the alignment for.
        :param index: index to get the alignment for.
        :return: alignment at the given index.
        """

        return Qt.AlignVCenter

    def font(self, row_data_source: BaseDataSource, index: int) -> QFont | None:
        """
        Overrides `font` function to return the font at the given index.

        :param row_data_source: row data source to get the font for.
        :param index: index to get the font for.
        :return: font at the given index.
        """

        return super().font(index)

    def is_checkable(self, row_data_source: BaseDataSource, index: int) -> bool:
        """
        Overrides `is_checkable` function to return whether the data at the given index is checkable or not.

        :param row_data_source: row data source to check the data for.
        :param index: index to check.
        :return: True if the data is checkable; False otherwise.
        """

        return False

    def is_enabled(self, row_data_source: BaseDataSource, index: int) -> bool:
        """
        Overrides `is_enabled` function to return whether the data at the given index is enabled or not.

        :param row_data_source: row data source to check the data for.
        :param index: index to check.
        :return: True if the data is enabled; False otherwise.
        """

        return row_data_source.is_enabled(index)

    def is_selectable(self, row_data_source: BaseDataSource, index: int) -> bool:
        """
        Overrides `is_selectable` function to return whether the data at the given index is selectable or not.

        :param row_data_source: row data source to check the data for.
        :param index: index to check.
        :return: True if the data is selectable; False otherwise.
        """

        return True

    def is_editable(self, row_data_source: BaseDataSource, index: int) -> bool:
        """
        Overrides `is_editable` function to return whether the data at the given index is editable or not.

        :param row_data_source: row data source to check the data for.
        :param index: index to check.
        :return: True if the data is editable; False otherwise.
        """

        return row_data_source.is_editable(index)

    def supports_drag(self, row_data_source: BaseDataSource, index: int) -> bool:
        """
        Overrides `supports_drag` function to return whether the data at the given index supports drag or not.

        :param row_data_source: row data source to check the data for.
        :param index: index to check.
        :return: True if the data supports drag; False otherwise.
        """

        return False

    def supports_drop(self, row_data_source: BaseDataSource, index: int) -> bool:
        """
        Overrides `supports_drop` function to return whether the data at the given index supports drop or not.

        :param row_data_source: row data source to check the data for.
        :param index: index to check.
        :return: True if the data supports drop; False otherwise.
        """

        return False

    def mime_data(self, row_data_source: BaseDataSource, indices: list[int]) -> dict:
        """
        Overrides `mime_data` function to return the mime data for the given indices.

        :param row_data_source: row data source to get the mime data for.
        :param indices: indices to get the mime data for.
        :return: mime data for the given indices.
        """

        return {}

    def drop_mime_data(
        self, row_data_source: BaseDataSource, items: list[str], action: Qt.DropAction
    ) -> dict:
        """
        Overrides `drop_mime_data` function to drop the mime data for the given items and action.

        :param row_data_source: row data source to drop the mime data for.
        :param items: items to drop the mime data for.
        :param action: drop action to perform.
        :return: mime data for the given items and action.
        """

        return {}

    def remove_row_data_sources(
        self, row_data_source: BaseDataSource, index: int, count: int
    ) -> bool:
        """
        Overrides `remove_row_data_sources` function to remove row data sources at the given index.

        :param row_data_source: row data source to remove the row data sources for.
        :param index: index to remove the row data sources at.
        :param count: number of row data sources to remove.
        :return: True if the row data sources were removed successfully; False otherwise.
        """

        return False

    def sort(
        self,
        row_data_source: BaseDataSource,
        index: int = 0,
        order: Qt.SortOrder = Qt.DescendingOrder,
    ):
        """
        Overrides `sort` function to sort the data source.

        :param row_data_source: row data source to sort.
        :param index: index to sort by.
        :param order: sort order.
        """

        def element(key):
            return key[1] or ""

        to_sort = [
            (obj, self.data(row_data_source, i))
            for i, obj in enumerate(row_data_source.user_objects())
        ]
        if order == Qt.DescendingOrder:
            results = [i[0] for i in sorted(to_sort, key=element, reverse=True)]
        else:
            results = [i[0] for i in sorted(to_sort, key=element)]

        self.set_user_objects(results)


# noinspection PyMethodMayBeStatic
class ColumnIntNumericDataSource(ColumnDataSource):
    """
    Class used to represent table columns with integer data.
    """

    def minimum(self, index: int) -> float:
        """
        Returns the minimum value at the given index.

        :param index: index to get the minimum value for.
        :return: minimum value at the given index.
        """

        return -99999

    def maximum(self, index: int) -> float:
        """
        Returns the maximum value at the given index.

        :param index: index to get the maximum value for.
        :return: maximum value at the given index.
        """

        return 99999


# noinspection PyMethodMayBeStatic
class ColumnDoubleNumericDataSource(ColumnDataSource):
    """
    Class used to represent table columns with double data.
    """

    def minimum(self, index: int) -> float:
        """
        Returns the minimum value at the given index.

        :param index: index to get the minimum value for.
        :return: minimum value at the given index.
        """

        return -99999.0

    def maximum(self, index: int) -> float:
        """
        Returns the maximum value at the given index.

        :param index: index to get the maximum value for.
        :return: maximum value at the given index.
        """

        return 99999.0


class ColumnEnumerationDataSource(ColumnDataSource):
    """
    Class used to represent table columns with enumeration data.
    """

    def __init__(
        self,
        header_text: str | None = None,
        model: TableModel | None = None,
        parent: BaseDataSource | None = None,
    ):
        super().__init__(header_text=header_text, model=model, parent=parent)

        self._enums: dict[int, list[str]] = {}
        self._current_index: dict[int, int] = {}

    def enums(self, row_data_source: BaseDataSource, index: int) -> list[str]:
        """
        Returns the enumeration values at the given index.

        :param row_data_source: row data source to get the enumeration values for.
        :param index: index to get the enumeration values for.
        :return: enumeration values at the given index.
        """

        return self._enums.get(index, [])

    def set_enums(
        self, row_data_source: BaseDataSource, index: int, enums: list[str]
    ) -> bool:
        """
        Sets the enumeration values at the given index.

        :param row_data_source: row data source to set the enumeration values for.
        :param index: index to set the enumeration values for.
        :param enums: enumeration values to set.
        :return: True if the enumeration values were set successfully; False otherwise.
        """

        current_enums = self._enums.get(index, [])
        new_index: int = 0
        if current_enums and index in self._current_index:
            current_enum_value = current_enums[self._current_index[index]]
            try:
                new_index = enums.index(current_enum_value)
            except ValueError:
                # This happens when the previous enum no longer exists.
                pass
        self._current_index[index] = new_index
        self._enums[index] = enums

        return True


class ColumnEnumerationButtonDataSource(ColumnDataSource):
    """
    Class used to represent table columns with enumeration data.
    """

    def __init__(
        self,
        header_text: str | None = None,
        model: TableModel | None = None,
        parent: BaseDataSource | None = None,
    ):
        super().__init__(header_text=header_text, model=model, parent=parent)

        self._enums: dict[int, list[str]] = {}
        self._current_index: dict[int, int] = {}

    def enums(self, row_data_source: BaseDataSource, index: int) -> list[str]:
        """
        Returns the enumeration values at the given index.

        :param row_data_source: row data source to get the enumeration values for.
        :param index: index to get the enumeration values for.
        :return: enumeration values at the given index.
        """

        return self._enums.get(index, [])

    def set_enums(
        self, row_data_source: BaseDataSource, index: int, enums: list[str]
    ) -> bool:
        """
        Sets the enumeration values at the given index.

        :param row_data_source: row data source to set the enumeration values for.
        :param index: index to set the enumeration values for.
        :param enums: enumeration values to set.
        :return: True if the enumeration values were set successfully; False otherwise.
        """

        current_enums = self._enums.get(index, [])
        new_index: int = 0
        if current_enums and index in self._current_index:
            current_enum_value = current_enums[self._current_index[index]]
            try:
                new_index = enums.index(current_enum_value)
            except ValueError:
                # This happens when the previous enum no longer exists.
                pass
        self._current_index[index] = new_index
        self._enums[index] = enums

        return True


BaseDataSourceType = Union[
    BaseDataSource,
    RowIntNumericDataSource,
    RowDoubleNumericDataSource,
    RowEnumerationDataSource,
    RowEnumerationButtonDataSource,
]

ColumnDataSourceType = Union[
    ColumnDataSource,
    ColumnIntNumericDataSource,
    ColumnDoubleNumericDataSource,
    ColumnEnumerationDataSource,
    ColumnEnumerationButtonDataSource,
]
