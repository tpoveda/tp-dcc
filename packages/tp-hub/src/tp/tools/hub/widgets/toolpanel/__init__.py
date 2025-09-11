from __future__ import annotations

from tp import dcc

if dcc.is_maya():
    from .maya import MayaToolPanelWidget as ToolPanelWidget
else:
    from .base import BaseToolPanelWidget as ToolPanelWidget
