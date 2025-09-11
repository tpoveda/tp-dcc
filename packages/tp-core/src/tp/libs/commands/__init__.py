from __future__ import annotations

from tp import dcc

from .command import CommandData  # noqa F401
from .runner import execute, CommandRunner  # noqa F401

if dcc.is_maya():
    from .maya.command import MayaCommand as Command  # noqa F401
elif dcc.is_unreal():
    from .unreal.command import UnrealCommand as Command  # noqa F401
