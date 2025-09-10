from __future__ import annotations

import typing

from Qt.QtCore import (
    Qt,
    QObject,
    QModelIndex,
    QSortFilterProxyModel,
    QRegularExpression,
)

if typing.TYPE_CHECKING:
    from .data import BaseDataSource
    from .treemodel import TreeModel


class LeafTreeFilterProxyModel(QSortFilterProxyModel):
    """A proxy model that filters a tree model to only show leaf nodes."""

    def __init__(self, sort: bool = True, parent: QObject | None = None):
        super().__init__(parent=parent)

        self.setSortCaseSensitivity(Qt.CaseInsensitive)

        if sort:
            self.setDynamicSortFilter(True)
            self.setFilterKeyColumn(0)

    def setFilterFixedString(self, pattern: str):
        """Set the filter pattern for the model.

        Args:
            pattern: The pattern to filter the model by. If the pattern is
                less than 2 characters, it will be set to an empty string.
        """

        super().setFilterFixedString(pattern if len(pattern) >= 2 else "")

    def filterAcceptsRow(self, row_num: int, source_parent: QModelIndex) -> bool:
        """Determine if the filter should accept the row at the given index.

        Args:
            row_num: The row number to check.
            source_parent: The parent index of the row in the source model.

        Returns:
            True if the filter should accept the row; False otherwise.
        """

        search_exp = self.filterRegularExpression()
        search_exp.setPatternOptions(QRegularExpression.CaseInsensitiveOption)
        if not search_exp.isValid():
            return True

        # Look at the node hierarchy iteratively to see if we should keep.
        # noinspection PyTypeChecker
        model: TreeModel = self.sourceModel()
        if not source_parent.isValid():
            item = model.root().child(row_num)
        else:
            model_index = model.index(row_num, self.filterKeyColumn(), source_parent)
            if not model_index.isValid():
                return False
            item = model.item_from_index(model_index)

        return self._match(search_exp, item, self.filterKeyColumn())

    def _match(
        self, search_expr: QRegularExpression, item: BaseDataSource, column: int
    ) -> bool:
        """Recursively check if the item or any of its children match the
        search expression.

        Args:
            search_expr: The regular expression to match against.
            item: The item to check for a match.
            column: The column index to check in the item's data.

        Returns:
            True if the item or any of its children match the search
            expression; False otherwise.
        """

        if search_expr.match(item.data(column)).capturedStart() != -1:
            return True
        for idx in range(item.row_count()):
            child_item = item.child(idx)
            if self._match(search_expr, child_item, column):
                return True

        return False
