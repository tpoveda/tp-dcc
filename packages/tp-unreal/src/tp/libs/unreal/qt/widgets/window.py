from __future__ import annotations

import unreal

from tp.libs.qt.widgets.frameless import FramelessWindow


class UnrealWindow(FramelessWindow):
    """Base class for Unreal Windows."""

    def __init__(self, *args, **kwargs):
        parent = kwargs.get("parent", None)
        super().__init__(*args, **kwargs)

        if not parent and self.parent_container:
            unreal.parent_external_window_to_slate(
                self.parent_container.winId(),
                unreal.SlateParentWindowSearchMethod.MAIN_WINDOW,
            )

    def show_window(self):
        super().show_window()

        # This is a workaround to parent the window to the Unreal Editor.
        if self.parent_container:
            unreal.parent_external_window_to_slate(
                self.parent_container.winId(),
                unreal.SlateParentWindowSearchMethod.MAIN_WINDOW,
            )
