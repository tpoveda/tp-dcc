from __future__ import annotations

from tp.libs import dcc

from .command import CommandData
from .runner import execute, CommandRunner  # noqa F401

if dcc.is_maya():
    from .maya.command import MayaCommand as Command  # noqa F401
elif dcc.is_unreal():
    from .unreal.command import UnrealCommand as Command  # noqa F401
