from __future__ import annotations

import typing

from Qt.QtCore import QObject

from tp.libs.qt.widgets.thumbsbrowser.thumbslist.model import ThumbsListModel

from .constants import DCC_SCENE_EXTENSION

if typing.TYPE_CHECKING:
    from tp.preferences.directory import DirectoryPath
    from tp.libs.qt.widgets.thumbsbrowser.thumbslist.view import ThumbsListView


class AssetSceneModel(ThumbsListModel):
    """Model for DCC Scene browser."""

    def __init__(
        self,
        view: ThumbsListView,
        extensions: list[str] | None = None,
        directories: list[DirectoryPath] | None = None,
        chunk_count: int | None = None,
        uniform_icons: bool = False,
        parent: QObject | None = None,
    ):
        super().__init__(
            view=view,
            extensions=extensions or [DCC_SCENE_EXTENSION],
            directories=directories,
            chunk_count=chunk_count,
            uniform_icons=uniform_icons,
            parent=parent,
        )
