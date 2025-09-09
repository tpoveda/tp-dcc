from __future__ import annotations

import typing

from tp.libs.plugin import Plugin

if typing.TYPE_CHECKING:
    from .rig import Rig


class BaseBuildScript(Plugin):
    """Base class for build scripts.

    Build scripting allows a user to run custom Python code during each build
    stage.

    These build scripts will also be saved into the rig configuration, so
    when the rig is loaded at a later time, the same build scripts will be
    executed again.

    Rig configuration handles the discovery of the available build scripts.
    """

    id: str = ''

    def __init__(self):
        super().__init__()

        self._rig: Rig | None = None\

    @property
    def rig(self) -> Rig | None:
        """The rig instance the build script is associated with."""

        return self._rig

    @rig.setter
    def rig(self, rig: Rig):
        """Set the rig instance the build script is associated with."""

        self._rig = rig