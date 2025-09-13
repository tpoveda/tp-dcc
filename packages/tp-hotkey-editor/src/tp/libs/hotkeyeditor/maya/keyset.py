from __future__ import annotations

from maya import cmds
from loguru import logger

from ..keyset import KeySet


class MayaKeySet(KeySet):
    def delete_from_host(self) -> bool:
        """Deletes the key set from the Maya.

        Returns:
            `True` if the key set was deleted; `False` otherwise.
        """

        if not cmds.hotkeySet(self._name, exists=True):
            logger.warning(f'Key set "{self._name}" does not exist in Maya')
            return False

        cmds.hotkeySet(self._name, edit=True, delete=True)

        return True
