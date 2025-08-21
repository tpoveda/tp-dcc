from __future__ import annotations

from tp import dcc


if dcc.is_unreal():
    from tp.unreal.qt.widgets.window import UnrealWindow as Window  # noqa: F401
else:
    from tp.libs.qt.widgets.frameless import FramelessWindow as Window  # noqa: F401
