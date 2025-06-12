from __future__ import annotations

from tp.libs.python.decorators import Singleton
from tp.libs.commands.runner import BaseCommandRunner

from tp.libs.commands.unreal.command import UnrealCommand


class UnrealCommandRunner(BaseCommandRunner, metaclass=Singleton):
    """Unreal Command runner implementation"""

    def __init__(self):
        super().__init__(interface=UnrealCommand)
