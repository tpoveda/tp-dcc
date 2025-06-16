from __future__ import annotations


class ModRigError(Exception):
    """Base class for all ModRig errors."""

    MSG = ""

    def __init__(self, msg: str = "", *args, **kwargs):
        super().__init__(str(msg), *args)


class RigDuplicationError(ModRigError):
    """Exception raised when a rig is duplicated in the scene."""

    MSG = "Duplicated rigs in the scene, please use namespace filtering: {}"

    def __init__(self, dupes, *args, **kwargs):
        msg = self.MSG.format(dupes)
        super().__init__(msg, *args, **kwargs)
