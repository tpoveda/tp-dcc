from __future__ import annotations

import typing

from Qt.QtWidgets import QWidget

from tp.libs.qt.widgets.frames import EmbeddedWindow

if typing.TYPE_CHECKING:
    from ..model import ThumbsListModel


class InfoEmbeddedWindow(EmbeddedWindow):
    """An embedded window for displaying information."""

    def __init__(
        self,
        default_visibility: bool = False,
        margins: tuple[int, int, int, int] = (0, 0, 0, 0),
        parent: QWidget | None = None,
    ):
        """Initialize the InfoEmbeddedWindow.

        Args:
            margins: The margins for the embedded window.
        """
        super().__init__(
            default_visibility=default_visibility, margins=margins, parent=parent
        )

        self._model: ThumbsListModel | None = None

    def set_model(self, model: ThumbsListModel):
        """Set the model for the embedded window.

        Args:
            model: The model to set.
        """

        self._model = model
        self._model.itemSelectionChanged.connect(self._on_model_item_selection_changed)

    def _on_model_item_selection_changed(self, image: str, item):
        print("Item selection changed ...")
