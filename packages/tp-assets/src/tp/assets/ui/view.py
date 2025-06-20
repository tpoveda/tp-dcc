from __future__ import annotations

from tp.libs.qt.widgets.window import Window


class AssetsView(Window):
    """Assets view window."""

    def __init__(self, title="Assets Browser", width=1000, height=600, **kwargs):
        super().__init__(title=title, width=width, height=height, **kwargs)
