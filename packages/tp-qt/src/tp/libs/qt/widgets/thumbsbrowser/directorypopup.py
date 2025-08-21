from __future__ import annotations

from Qt.QtCore import Qt
from Qt.QtWidgets import QWidget, QAbstractItemView

from ..window import Window
from ..viewmodel.treeview import TreeViewWidget
from ..layouts import VerticalLayout, HorizontalLayout
from ... import dpi


class DirectoryPopup(Window):
    def __init__(
        self,
        auto_hide: bool = False,
        attach_to_parent: bool = True,
        parent: QWidget | None = None,
    ):
        self._auto_hide = auto_hide
        self._attach_to_parent = attach_to_parent

        super().__init__(parent=parent)

    # noinspection PyAttributeOutsideInit
    def setup_widgets(self):
        """Setup widgets for the directory popup."""

        self._tree_view_widget = TreeViewWidget(parent=self)
        self._tree_view_widget.set_searchable(False)
        self._tree_view_widget.set_show_title_label(False)
        self._tree_view_widget.set_header_hidden(True)
        self._tree_view_widget.set_indentation(dpi.dpi_scale(10))
        self._tree_view_widget.set_drag_drop_mode(QAbstractItemView.InternalMove)
        self._tree_view_widget.tree_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def setup_layouts(self, main_layout: VerticalLayout):
        """Setup layouts for the directory popup."""

        header_layout = HorizontalLayout()
        header_layout.setSpacing(6)
        header_layout.setContentsMargins(0, 2, 5, 2)
        self._title_bar.corner_contents_layout.addLayout(header_layout)

        main_layout.addWidget(self._tree_view_widget)
