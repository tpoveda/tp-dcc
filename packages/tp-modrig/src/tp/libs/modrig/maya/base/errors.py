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


class ModuleDoesNotExistError(ModRigError):
    """Exception raised when a module does not exist in the scene."""

    MSG = "Module does not exist in the scene."


class MissingMetaNodeRootTransform(ModRigError):
    """Exception raised when a meta-node does not have a root transform."""

    MSG = "Missing Root transform on meta-node: {}"


class MissingModuleType(ModRigError):
    """Exception raised when a module type is not found in the module
    manager.
    """

    MSG = "Missing modules of type: {}, from Modules manager."

    def __init__(self, component_type, *args, **kwargs):
        msg = self.MSG.format(component_type)
        super().__init__(msg, *args, **kwargs)
