from __future__ import annotations

import uuid
import typing
from typing import Union, Iterator, Any

from Qt.QtCore import (
    Qt,
    QObject,
    QSize,
    QModelIndex,
    QAbstractListModel,
    QAbstractTableModel,
    QAbstractItemModel,
)
from Qt.QtWidgets import QMenu, QStyledItemDelegate
from Qt.QtGui import QIcon, QColor, QFont

from ... import dpi
from .roles import UID_ROLE
from .delegates import HtmlDelegate

if typing.TYPE_CHECKING:
    from .tablemodel import TableModel


class BaseDataSource(QObject):
    _ENABLED_COLOR = QColor("#C4C4C4")
    _DISABLED_COLOR = QColor("#5E5E5E")

    def __init__(
        self,
        header_text: str | None = None,
        model: QAbstractListModel
        | QAbstractTableModel
        | QAbstractItemModel
        | None = None,
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
        """Compare the current instance with another object for equality based
        on their unique identifiers (uid).

        Args:
            other: The object to compare with the current instance.

        Returns:
            bool: True if the objects are considered equal, otherwise False.
        """

        return isinstance(other, BaseDataSource) and self.uid == other.uid

    @property
    def uid(self) -> str:
        """The unique identifier of the data source."""

        return self._uid

    @property
    def model(
        self,
    ) -> QAbstractListModel | QAbstractTableModel | QAbstractItemModel | None:
        """The model of the data source."""

        return self._model

    @model.setter
    def model(
        self,
        value: QAbstractListModel | QAbstractTableModel | QAbstractItemModel | None,
    ):
        """Set the model of the data source."""

        self._model = value

    @property
    def children(self) -> list[BaseDataSource]:
        """The children of the data source."""

        return self._children

    @property
    def column_index(self) -> int:
        """The column index of the data source."""

        return self._column_index

    @column_index.setter
    def column_index(self, value: int):
        """Set the column index of the data source."""

        self._column_index = value

    def is_root(self) -> bool:
        """Determine if the current node is the root node.

        Checks whether the current node has a parent node, providing a way to
        identify if it is positioned as the root node in its hierarchical
        structure.

        Returns:
            True if the current node has no parent; False otherwise.
        """

        return self._parent is None

    def row_count(self) -> int:
        """Return the number of child elements in the data structure.

        Returns:
            The total count of child elements.
        """

        return len(self._children)

    # noinspection PyMethodMayBeStatic
    def column_count(self) -> int:
        """Retrieve the number of columns in the data structure.

        Returns:
            The number of columns.
        """

        return 1

    def has_children(self) -> bool:
        """Determine whether the current item has child items.

        Returns:
            True if the current item has one or more child items; False
                otherwise.
        """

        return self.row_count() > 0

    def parent_source(self) -> BaseDataSource | None:
        """Retrieve the parent data source associated with the current instance.

        Notes:
            The parent data source represents a hierarchical relationship
            between data sources, where the current instance depends on or
            inherits properties from the parent.

        Returns:
            The parent data source object associated with the current instance
            if one exists; `None` otherwise.
        """

        return self._parent

    def set_parent_source(self, parent_source: BaseDataSource):
        """Set the parent data source for the current instance and updates the
        hierarchy.

        Notes:
            This method is responsible for establishing a parent-child
            relationship between the current instance and the provided parent
            data source.

            It also ensures that the current instance is removed from the
            children of any previously assigned parent data source, maintaining
            proper hierarchy integrity.

        Args:
            parent_source: The new parent data source to assign. This must be
                an instance of `BaseDataSource` that will become the parent of
                the current instance.
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
        """Retrieve the child data source at the specified index.

        Args:
            index: The position of the child data source to retrieve.

        Returns:
            The child data source at the specified index if valid; `None`
                otherwise.
        """

        if index < self.row_count():
            return self.children[index]

        return None

    def add_child(self, child: BaseDataSource) -> BaseDataSource | None:
        """Add a child data source to the current data source's children
        collection.

        Args:
            child: A `BaseDataSource` instance to be added to the list of
                children.

        Returns:
            Return the added child data source if it was successfully appended
            to the collection or None if the child was already a part of the
            collection.
        """

        if child in self._children:
            return None

        child.model = self.model
        self._children.append(child)

        return child

    def insert_child(self, index: int, child: BaseDataSource) -> bool:
        """Insert a child object at the specified index within the children
        list.

        Notes:
            This method allows adding a child to the internal children list of
            the object at a specific position. If the child already exists in
            the list, it won't be added again, and the method will return False.
            If the child is successfully added, its model attribute will be
            updated to match the current object's model.

        Args:
            index: The position at which to insert the child in the children
                list.
            child: The child to insert into the children list.

        Returns:
            True if the child was successfully added to the children list;
            False if the child was already present.
        """

        if child in self._children:
            return False

        child.model = self.model
        self._children.insert(index, child)

        return True

    def insert_children(self, index: int, children: list[BaseDataSource]):
        """Insert a list of children into a specific position in the existing
        children list.

        Notes:
            The `model` attribute of each child in the inserted list is set to
            match the `model` attribute of the parent.

            The insertion modifies the children list in place.

        Args:
            index: The position at which the list of `children` should be
                inserted. Existing children starting at this index will be
                shifted to the right.
            children: A list of `BaseDataSource` objects that will be inserted
                into the children list. Each object's `model` attribute will
                be updated to align with the parent's `model`.
        """

        for child in children:
            child.model = self.model

        self._children[index:index] = children

    def iterate_children(self, recursive: bool = True) -> Iterator[BaseDataSource]:
        """Iterates ove children of the current data source.

        This method yields each child in the `_children` collection of the
        current instance. If `recursive` is set to `True`, it will recursively
        iterate through all children and their sub-children.

        Args:
            recursive: Whether to iterate through children recursively. If set
                to `False`, only direct children are iterated.

        Yields:
            BaseDataSource: An instance of `BaseDataSource` representing a
                child or sub-child in the hierarchy.
        """

        for child in self._children:
            yield child
            if not recursive:
                continue
            for sub_child in child.iterate_children(recursive=recursive):
                yield sub_child

    def index(self) -> int:
        """Return the index of the current object within its parent's list of
        children.

        Returns:
            The index of the current object in its parent's list of children,
            or 0 if no parent or children exist.
        """

        parent = self.parent_source()
        if parent is not None and parent.children:
            return parent.children.index(self)

        return 0

    def model_index(self) -> QModelIndex:
        """Retrieve the index from the model corresponding to this item based
        on this item UUID.

        Returns:
            The index corresponding to the specified UID if found. Returns an
            invalid `QModelIndex` if the model is not set or no match exists.
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

    # noinspection PyMethodMayBeStatic
    def width(self) -> int:
        """Return the width of the model data sources.

        Returns:
            The width of the data sources of this model.
        """

        return 0

    def custom_roles(self, index: int) -> list[int]:
        """Return a list of custom roles based on the given index.

        Args:
            index: The index to retrieve custom roles for.
        """

        return []

    def data(self, index: int) -> Any:
        """Retrieve data associated with the provided index.

        Args:
            index: An integer representing the position of the desired data
            element in the collection.

        Returns:
            Any: The data associated with the specified index.
        """

        return ""

    def data_by_role(self, index: int, role: Qt.ItemDataRole) -> Any:
        """Retrieve data associated with a given index and a specified role
        in a model.

        Args:
            index: The index of the item in the model for which data needs to
                be retrieved.
            role: The role in which the data is requested.

        Returns:
            The data associated with the given index and specified role.
            The type of the data depends on the role and the implementation of
            the model.
        """

        return ""

    def set_data(self, index: int, value: Any):
        """Set the value at the specified index in a data structure.

        Args:
            index: The position in the data structure where the value will be
                updated or set.
            value: The new value to be assigned at the specified index. The
                type of this value depends on the data structure's expected
                content.
        """

        pass

    def set_data_by_custom_role(self, index: int, data: Any, role: Qt.ItemDataRole):
        """Set the data for the given index and role with the specified value.

        Args:
            index: The index identifying the position in the model.
            data: The value to be assigned to the specified index and role.
            role: The role defining the context or purpose for the data.
        """

        pass

    def user_object(self, index: int) -> Any:
        """Retrieve the user object corresponding to the given index in the
        collection.

        Args:
            index: The index of the user object to retrieve. Must be within
                the valid range of 0 to the total row count minus 1.

        Returns:
            The user object at the specified index if it exists.
        """

        return self.user_objects()[index] if index < self.row_count() else None

    def user_objects(self) -> list[Any]:
        """Retrieve all child objects associated with the current object.

        Returns:
            A list containing the child objects associated with the current
                object.
        """

        return self._children

    def set_user_objects(self, user_objects: list[BaseDataSource]):
        """Set the list of user objects for the instance.

        Args:
            user_objects: A list of user-defined objects. These objects must be
                instances of the `BaseDataSource` type.
        """

        self._children = user_objects

    # noinspection PyMethodMayBeStatic
    def can_fetch_more(self) -> bool:
        """Determine whether more data can be fetched.

        This method checks the current state and decides if fetching
        additional data is possible.

        Notes:
            It can be used as a control mechanism to manage data fetch limits
            in operations where resource consumption needs to be optimized.

        Returns:
            A value indicating whether more data can be fetched. Returns
            `False` if no additional data can be retrieved.
        """

        return False

    def fetch_more(self):
        """Fetch additional data from a source or perform a later operation to
        retrieve more items.

        Notes:
            This is a placeholder method intended to be overridden in a
            subclass or implemented in a derived class to provide specific
            functionality for fetching or retrieving more data or items.
        """

        pass

    def is_checkable(self, index: int) -> bool:
        """Determine whether the given index is checkable.

        Args:
            index: The index to be evaluated as checkable or not.

        Returns:
            Returns False indicating the index is not checkable.
        """

        return False

    def is_enabled(self, index: int) -> bool:
        """Determine whether the specified index is enabled.

        Args:
            index: An integer representing the index to be checked.

        Returns:
            A boolean indicating if the specified index is enabled.
        """

        return True

    def is_selectable(self, index: int) -> bool:
        """Determine whether the given index is selectable.

        This method evaluates the input index and decides if the index meets the
        conditions necessary to be considered selectable. If the index satisfies
        all criteria, the method returns True.

        Args:
            index: The index to evaluate for its selectable status.

        Returns:
            True if the index is selectable; `False` otherwise.
        """

        return True

    def is_editable(self, index: int) -> bool:
        """Determine whether the specified index is editable.

        Args:
            index: An integer representing the index to check.

        Returns:
            `True` if the index is editable; `False` otherwise.
        """

        return self.is_enabled(index)

    # noinspection PyUnusedLocal
    def header_text(self, index: int) -> str:
        """Return the header text corresponding to the given index.

        Args:
            index: The index specifying which header text to retrieve.

        Returns:
            The header text corresponding to the provided index.
        """

        return self._header_text

    # noinspection PyMethodMayBeStatic
    def header_icon(self) -> QIcon:
        """Retrieve the `QIcon` object to be used for the header icon.

        Returns:
            The icon object to be displayed in the header.
        """

        return QIcon()

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def header_vertical_text(self, index: int) -> str | None:
        """Return the vertical text representation for the header at the
        specified index or None if not applicable.

        Args:
            index: The index of the header for which to retrieve the
                vertical text representation.

        Returns:
            The vertical text representation of the header; None if not
                applicable.
        """

        return None

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def header_vertical_icon(self, index: int) -> QIcon:
        """Return a vertical icon for the header based on the provided index.

        Args:
            The index used to determine the appropriate vertical header icon.

        Returns:
            The icon to be displayed in the vertical header.
        """

        return QIcon()

    def tooltip(self, index: int) -> str:
        """Generate a tooltip string by combining header text and data for the
        given index.

        Args:
            index: The index for which the tooltip will be generated.

        Returns:
            A formatted string containing the header text and data for the
            given index, or an empty string if the model is `None`.
        """

        model = self._model
        if model is None:
            return ""

        return f"{self.header_text(index)}:{str(self.data(index))}\n"

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def set_tooltip(self, index: int, value: str) -> bool:
        """Set the tooltip for a specified index with the provided value.

        Args:
            index: The index for which the tooltip is set.
            value: The tooltip text to set.

        Returns:
            True if the tooltip was set successfully; False otherwise.
        """

        return False

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def icon_size(self, index: int) -> QSize:
        """Return the size of an icon for a given index.

        Args:
            index: The index for which the icon size is being retrieved.

        Returns:
            The size of the icon, specifically (16, 16).
        """

        return QSize(16, 16)

    def icon(self, index: int) -> QIcon | None:
        """Retrieve the icon associated with the given index in a data
        structure.

        Args:
            index: The index for which the corresponding icon is to be
                retrieved.

        Returns:
            QIcon | None: The icon associated with the given index; `None` if
                no icon is found.
        """

        return None

    def foreground_color(self, index: int) -> QColor:
        """Determine the appropriate foreground color based on the item's
        enabled and editable state.

        Args:
            index: The index of the item to determine its foreground color.

        Returns:
            The color representing the foreground of the item based on its
                state.
        """

        return (
            self._ENABLED_COLOR
            if self.is_enabled(index) and self.is_editable(index)
            else self._DISABLED_COLOR
        )

    def background_color(self, index: int) -> QColor | None:
        """Determine the background color for a specific index in a data
        structure.

        Args:
            index: The specific index for which the background color is to be
                determined.

        Returns:
            The background color corresponding to the given index if one
            exists; `None` otherwise.
        """

        return None

    def display_changed_color(self, index: int) -> QColor | None:
        """Provide functionality to handle and respond to changes in the color
        display by returning an updated color based on an index or `None` if no
        update occurs.

        Args:
            index: An integer representing the index for the color change.

        Returns:
            The updated color if a change occurs; `None` otherwise.
        """

        return None

    def text_margin(self, index: int) -> int:
        """Return the default text margin value for a given index.

        Args:
            index: The index value used to query the default text margin.

        Returns:
            The default text margin value.
        """

        return self._default_text_margin

    def alignment(self, index: int) -> Qt.AlignmentFlag | Qt.Alignment:
        """Determine and return the alignment flag or alignment for the given
        index.

        Args:
            An integer representing the index to determine the alignment.

        Returns:
            The alignment value corresponding to the given index.
        """

        return Qt.AlignVCenter

    def font(self, index: int) -> QFont | None:
        """Retrieve the font associated with a given index.

        Args:
            index: The index for which the font is to be retrieved.

        Returns:
            The font object if found, `None` otherwise.
        """

        return self._font

    def enums(self, index: int) -> list[str]:
        """Retrieve a list of enumerated values associated with the data
        source.

        Args:
            index: The index for which to retrieve the enumerated values.

        Returns:
            A list of strings representing the enumerated values.
        """

        return []

    def supports_drag(self, index: int) -> bool:
        """Determine whether an item at the specified index supports
        drag-and-drop functionality.

        Args:
            index: The index of the item to check if drag-and-drop
                functionality is supported.

        Returns:
            True if the item at the specified index supports drag-and-drop;
            `False` otherwise.
        """

        return False

    def supports_drop(self, index: int) -> bool:
        """Determines if the specified index supports drop functionality.

        Args:
            index: The index to be checked for drop support.

        Returns:
            True if the index supports drop functionality; `False` otherwise.
        """

        return False

    def mime_data(self, index: int) -> dict[str, Any]:
        """Retrieve and organize mime data based on the provided indices.

        Args:
            index: An integer representing the index for which to retrieve
                mime data.

        Returns:
            A dictionary containing the mime data organized by the provided
                indices.
        """

        return {}

    def drop_mime_data(self, items: list[str], action: Qt.DropAction) -> dict[str, Any]:
        """Process and handle dropped MIME data and performs the specified
        drop action.

        Args:
            items: A list of strings representing the MIME data items to be
                processed.
            action: The action to be performed with the dropped data.

        Returns:
            A dictionary containing the processed results of the dropped
                MIME data.
        """

        return {}

    def insert_row_data_source(self, index: int, **kwargs):
        """Insert a new row within the data source at the specified index.

        Args:
            index: The zero-based index indicating the position where the new
                row should be inserted within the data source.
        """

        pass

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def insert_row_data_sources(self, index: int, count: int, **kwargs) -> bool:
        """Insert multiple rows into a data source starting from a specific
        index.

        Args:
            index: The starting index where the rows will be inserted.
            count: The number of rows to insert into the data source.

        Returns:
            True if the rows were successfully inserted; `False` otherwise.
        """

        return False

    def remove_row_data_source(self, index: int) -> bool:
        """Remove a row from the data source at the specified index, if the
        index is valid.

        Args:
            index: The index of the row to remove.

        Returns:
            `True` if the row at the given index is successfully removed;
                `False` otherwise.
        """

        if index < self.row_count():
            del self._children[index]
            return True

        return False

    def remove_row_data_sources(self, index: int, count: int, **kwargs) -> bool:
        """Remove a specified number of data sources starting from a given
        index within the row data structure.

        Args:
            index: The starting index of the row(s) to be removed.
            count: The number of consecutive rows to remove, starting from the
                specified index.

        Returns:
            `True` if the rows were successfully removed; `False` otherwise.
        """

        if index < self.row_count():
            self._children = self._children[:index] + self._children[index + count :]
            return True

        return False

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def insert_column_data_sources(self, index: int, count: int) -> bool:
        """Insert a specified number of data sources into a column at a given
        index.

        Args:
            index: The zero-based index in the column where the data sources
                should be inserted.
            count: The number of data sources to insert at the specified index.

        Returns:
            `True` if the insertion is successful; `False` otherwise.
        """

        return False

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def remove_column_data_sources(self, index: int, count: int) -> bool:
        """Remove a specified number of column data sources starting from a
        given index.

        Args:
            index: The starting index of the column data sources to be removed.
            count: The number of column data sources to remove.

        Returns:
            `True` if the removal operation was successful; `False` otherwise.
        """

        return False

    def sort(self, index: int = 0, order: Qt.SortOrder = Qt.DescendingOrder):
        """Sort the user-defined objects in the model based on the specified
        index and order.

        This method organizes the user objects by comparing their corresponding
        data values, either in ascending or descending order, as indicated by
        the `order` parameter.

        It extracts tuples of objects and their respective data, sorts the
        tuples according to the data, and subsequently updates the list of user
        objects with the sorted order.

        Args:
            index: The index of the column or value in the data model to use as
                the key for sorting.
            order: The desired sorting order. Use `Qt.AscendingOrder` for
            ascending and `Qt.DescendingOrder` for descending sorting.
        """

        def element(key):
            return key[1]

        to_sort = [(obj, self.data(i)) for i, obj in enumerate(self.user_objects())]
        if order == Qt.DescendingOrder:
            results = [i[0] for i in sorted(to_sort, key=element, reverse=True)]
        else:
            results = [i[0] for i in sorted(to_sort, key=element)]

        self.set_user_objects(results)

    # noinspection PyMethodMayBeStatic
    def delegate(self, parent: QObject) -> QStyledItemDelegate:
        """Return a `QStyledItemDelegate` with the specified parent.

        Args:
            parent: The parent object for the delegate.

        Returns:
            A delegate instance.
        """

        return HtmlDelegate(parent=parent)

    def context_menu(self, selection: list[Any], menu: QMenu):
        """Generate and customize a context menu based on the given selection.

        Args:
            selection: List of currently selected items to be processed for
                context menu generation.
            menu: The QMenu instance that will be modified or populated
                with new options based on the selection.
        """

        pass

    def on_vertical_header_selection(self, index: int):
        """Handle the selection event on the vertical header of a table or
        grid.

        Notes:
            The view calls this method (if this source is attached to
            one) when the vertical header is clicked.

        Args:
            index: The index of the selected vertical header item.
        """

        pass


# noinspection PyMethodMayBeStatic
class RowIntNumericDataSource(BaseDataSource):
    """Class used to represent table rows with integer data."""

    def minimum(self, index: int) -> float:
        """Returns the minimum value at the given index.

        :param index: index to get the minimum value for.
        :return: minimum value at the given index.
        """

        return -99999

    def maximum(self, index: int) -> float:
        """Returns the maximum value at the given index.

        :param index: index to get the maximum value for.
        :return: maximum value at the given index.
        """

        return 99999


# noinspection PyMethodMayBeStatic
class RowDoubleNumericDataSource(BaseDataSource):
    """Class used to represent table rows with double data."""

    def minimum(self, index: int) -> float:
        """Returns the minimum value at the given index.

        :param index: index to get the minimum value for.
        :return: minimum value at the given index.
        """

        return -99999.0

    def maximum(self, index: int) -> float:
        """Returns the maximum value at the given index.

        :param index: index to get the maximum value for.
        :return: maximum value at the given index.
        """

        return 99999.0


class RowEnumerationDataSource(BaseDataSource):
    """Class used to represent table rows with enumeration data."""

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
        """Returns the enumeration values at the given index.

        :param index: index to get the enumeration values for.
        :return: enumeration values at the given index.
        """

        return []

    def set_enums(self, index: int, enums: list[str]) -> bool:
        """Sets the enumeration values at the given index.

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
    """Class used to represent table rows with enumeration data."""

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
        """Returns the enumeration values at the given index.

        :param index: index to get the enumeration values for.
        :return: enumeration values at the given index.
        """

        return self._enums.get(index, [])


# noinspection PyMethodOverriding
class ColumnDataSource(BaseDataSource):
    """Class used to represent table columns."""

    def custom_roles(self, row_data_source: BaseDataSource, index: int) -> list[int]:
        """Assign custom roles to the data in a row based on the provided index.

        Args:
            row_data_source: The data source containing rows of data.
            index: The index of the row within the data source for which
                custom roles are to be generated.

        Returns:
            A list of integers where each integer corresponds to a custom role
            assigned to the elements of the specified row in the data source.
        """

        return []

    def data(self, row_data_source: BaseDataSource, index: int) -> Any:
        """Retrieves the data from the given data source for the specified
        index.

        Args:
            row_data_source: A data source to retrieve the data from. It must be an
                instance of BaseDataSource.
            index: The index of the data to retrieve from the data source.
        """

        return ""

    def data_by_role(
        self, row_data_source: BaseDataSource, index: int, role: Qt.ItemDataRole
    ) -> Any:
        """Retrieve specific data from a data source based on the provided index
        and role.

        Args:
            row_data_source: Data source object implementing `BaseDataSource`
                from which the data will be retrieved.
            index: Integer indicating the specific row or position in the
                data source to fetch the data from.
            role: An enumerator of type Qt.ItemDataRole specifying the role
                or context for which the data should be retrieved.

        Returns:
            Any: Retrieved data from the specified row and role of the data
                source.
        """

        return False

    def set_data(self, row_data_source: BaseDataSource, index: int, value: Any):
        """Set a value in a specific row and column within the data source.

        Args:
            row_data_source: The data source object containing the target row
                and column data.
            index: The column index in the target row where the value
                should be updated.
            value: The new value to be set at the specified column index in
                the row.
        """

        pass

    def tooltip(self, row_data_source: BaseDataSource, index: int) -> str:
        """Generate the tooltip text for a specific data point in a given data
        source.

        Args:
            row_data_source: The data source containing the information for
                generating the tooltip.
            index: The index of the specific data point within the data source
                for which the tooltip is generated.

        Returns:
            A string representing the full tooltip text for the given data
            point.
        """

        return ""

    def icon(self, row_data_source: BaseDataSource, index: int) -> QIcon | None:
        """Retrieve the icon associated with a data row from a specified data
        source at the given index.

        Args:
            row_data_source: Source of data rows from which the icon is fetched.
            index: The index of the row in the data source for which the icon
                is retrieved.

        Returns:
            The icon associated with the row if available; `None` otherwise.
        """

        return None

    def foreground_color(self, row_data_source: BaseDataSource, index: int) -> QColor:
        """Determine the foreground color based on the state of the data
        source and index.

        Args:
            row_data_source: The data source object representing the row.
            index: The integer index identifying the specific row being
                evaluated.

        Returns:
            The color object representing either an enabled state or
                disabled state.
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
        """Determine the background color for a specific row in the data source.

        Args:
            row_data_source: The data source from which the background color
                of the specified row will be retrieved.
            index: The index of the row in the data source for which the
                background color needs to be determined.

        Returns:
            The `QColor` representing the background color of the row if
                available. Returns `None` if no specific background color is
                set.
        """

        return row_data_source.background_color(index)

    def display_changed_color(
        self, row_data_source: BaseDataSource, index: int
    ) -> QColor | None:
        """Display the changed color for the specified data source and index.

        Args:
            row_data_source: The data source object containing the row data
                to be analyzed for the color change.
            index: The index of the data row within the data source to check
                and retrieve its changed color.

        Returns:
            A `QColor` object representing the changed color if available,
                or `None` if no color is determined.
        """

        return None

    def text_margin(self, row_data_source: BaseDataSource, index: int) -> int:
        """Calculate the text margin for a given row in the data source.

        Args:
            row_data_source: The data source providing access to the data
                and related attributes, such as margin information, for
                any given row.
            index: int. The index of the row in the data source for which the
                text margin should be calculated.

        Returns:
            The margin value corresponding to the specified row in the data
                source.
        """

        return row_data_source.text_margin(index)

    def alignment(
        self, row_data_source: BaseDataSource, index: int
    ) -> Qt.AlignmentFlag | Qt.Alignment:
        """Determine the alignment flag or alignment for a given index in
        a data source row.

        Args:
            row_data_source: The source of the data row for which the alignment
                is being determined.
            index: The index of the specific cell in the row for which the
                alignment flag or alignment is required.

        Returns:
            The alignment setting.
        """

        return Qt.AlignVCenter

    def font(self, row_data_source: BaseDataSource, index: int) -> QFont | None:
        """Retrieve the font for the given index in the data source.

        Args:
            row_data_source: The source of the row data that informs the
                intended font for the operation.
            index: The index specifying the row for which the font is to be
                retrieved. The index references the specific entry in the data
                source.

        Returns:
            The font to be used for the specified index, or `None` if no
            specific font is determined.
        """

        return super().font(index)

    def is_checkable(self, row_data_source: BaseDataSource, index: int) -> bool:
        """Determine whether a specific row in a data source is checkable.

        Args:
            row_data_source: The data source containing the row to be checked.
            index: The index of the row in the data source to be inspected.

        Returns:
            `True` if the row is checkable; `False` otherwise.
        """

        return False

    def is_enabled(self, row_data_source: BaseDataSource, index: int) -> bool:
        """Determine whether a specific entry in the data source is enabled.

        Args:
            row_data_source: The data source instance containing rows to check.
            index: The index of the specific row within the data source to
                verify.

        Returns:
            `True` if the specific entry in the data source is enabled;
                `False` otherwise.
        """

        return row_data_source.is_enabled(index)

    def is_selectable(self, row_data_source: BaseDataSource, index: int) -> bool:
        """Determine if a given row data source at a specified index is
        selectable.

        Args:
            row_data_source: A data source from which the row information is
                derived.
            index: The zero-based index of the row in the data source.

        Returns:
            A boolean indicating whether the specified row is selectable.
        """

        return True

    def is_editable(self, row_data_source: BaseDataSource, index: int) -> bool:
        """Determine whether a specific row in the data source is editable.

        This method checks if the row at the given index in the provided data
            source allows editing.

        Args:
            row_data_source: The data source object that provides if a row can
                be edited.
            index: The index of the row within the data source to check for
                editability.

        Returns:
            `True` if the specified row is editable; `False` otherwise.
        """

        return row_data_source.is_editable(index)

    def supports_drag(self, row_data_source: BaseDataSource, index: int) -> bool:
        """Determine whether the drag operation is supported for a specific
        data source at a  given index.

        Args:
            row_data_source: The data source object representing the data row
                to be evaluated.
            index: The position of the data row in the data source for which
                drag support is determined.

        Returns:
            `True` if the drag operation is supported for the specified row
            index in the data source; `False` otherwise.
        """

        return False

    def supports_drop(self, row_data_source: BaseDataSource, index: int) -> bool:
        """Determine if the provided data source supports the "drop"
        operation for a specific row index.

        Args:
            row_data_source: The data source to assess, which must inherit from
                `BaseDataSource`.
            index: The row index within the data source to evaluate for
                whether the "drop" action is supported.

        Returns:
            `True` if the data source supports the "drop" operation for the
            specified row index; `False` otherwise.
        """

        return False

    def mime_data(self, row_data_source: BaseDataSource, indices: list[int]) -> dict:
        """Create and return mime data for a given row data source and its
        indices.

        Args:
            row_data_source: An object implementing the `BaseDataSource`
                interface, serving as the source of the data to process.
            indices: A list of integers representing the indices of the rows
                to be included in the mime data.

        Returns:
            A dictionary containing mime-encoded data for the specified rows
                from the data source.
        """

        return {}

    def mime_text(self, row_data_source: BaseDataSource, index: int) -> str:
        """Retrieve the MIME text representation for a specific row in the
        data source.

        Args:
            row_data_source: The data source from which the MIME text is
                retrieved.
            index: The index of the row in the data source for which the MIME
                text is to be generated.

        Returns:
            A string representing the MIME text for the specified row.
        """

        return ""

    def drop_mime_data(
        self, row_data_source: BaseDataSource, items: list[str], action: Qt.DropAction
    ) -> dict:
        """Handle the dropping of MIME data onto the target data source.

        Args:
            row_data_source: The target data source where items will be dropped.
            items: The list of items being dragged and dropped.
            action: The action to be executed as part of the drop operation.

        Returns:
            A dictionary indicating the outcome of the drop operation,
            which might include any relevant metadata or status information.
        """

        return {}

    def remove_row_data_sources(
        self, row_data_source: BaseDataSource, index: int, count: int
    ) -> bool:
        """Remove a specified number of data sources starting from a given
        index.

        Args:
            row_data_source: The data source object representing the
                collection of data rows to be managed or modified.
            index: The starting index in the data source collection from which
                removals will begin.
            count: The number of row data sources to remove starting from the
                specified index.

        Returns:
            `True` if the removal operation was successful; `False` otherwise.
        """

        return False

    def sort(
        self,
        row_data_source: BaseDataSource,
        index: int = 0,
        order: Qt.SortOrder = Qt.DescendingOrder,
    ):
        """Sort user objects in the provided data source based on the specified
        index and order.

        Args:
            row_data_source: The data source from which user objects are
                retrieved for sorting.
            index: The index of the data column used as a sort key.
            order: The desired sort order, either `Qt.AscendingOrder` or
                `Qt.DescendingOrder`.
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

        row_data_source.set_user_objects(results)


# noinspection PyMethodMayBeStatic
class ColumnIntNumericDataSource(ColumnDataSource):
    """Class used to represent table columns with integer data."""

    def minimum(self, index: int) -> float:
        """Returns the minimum value at the given index.

        :param index: index to get the minimum value for.
        :return: minimum value at the given index.
        """

        return -99999

    def maximum(self, index: int) -> float:
        """Returns the maximum value at the given index.

        :param index: index to get the maximum value for.
        :return: maximum value at the given index.
        """

        return 99999


# noinspection PyMethodMayBeStatic
class ColumnDoubleNumericDataSource(ColumnDataSource):
    """Class used to represent table columns with double data."""

    def minimum(self, index: int) -> float:
        """Returns the minimum value at the given index.

        :param index: index to get the minimum value for.
        :return: minimum value at the given index.
        """

        return -99999.0

    def maximum(self, index: int) -> float:
        """Returns the maximum value at the given index.

        :param index: index to get the maximum value for.
        :return: maximum value at the given index.
        """

        return 99999.0


class ColumnEnumerationDataSource(ColumnDataSource):
    """Class used to represent table columns with enumeration data."""

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
        """Returns the enumeration values at the given index.

        :param row_data_source: row data source to get the enumeration values for.
        :param index: index to get the enumeration values for.
        :return: enumeration values at the given index.
        """

        return self._enums.get(index, [])

    def set_enums(
        self, row_data_source: BaseDataSource, index: int, enums: list[str]
    ) -> bool:
        """Sets the enumeration values at the given index.

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
    """Class used to represent table columns with enumeration data."""

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
        """Returns the enumeration values at the given index.

        :param row_data_source: row data source to get the enumeration values for.
        :param index: index to get the enumeration values for.
        :return: enumeration values at the given index.
        """

        return self._enums.get(index, [])

    def set_enums(
        self, row_data_source: BaseDataSource, index: int, enums: list[str]
    ) -> bool:
        """Sets the enumeration values at the given index.

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
