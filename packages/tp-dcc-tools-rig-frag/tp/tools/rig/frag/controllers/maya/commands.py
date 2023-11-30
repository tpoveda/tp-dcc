from __future__ import annotations

from overrides import override

from tp.maya.api import command
from tp.tools.rig.frag.core.blueprint import BlueprintModel


class RenameStepCommand(command.MayaCommand):

    id = 'frag.builder.buildstep.rename'
    creator = 'Tomas Poveda'
    is_undoable = True
    is_enabled = True

    _blueprint_model: BlueprintModel | None = None
    _old_name = ''
    _new_path: str | None = None

    @override
    def resolve_arguments(self, arguments: dict) -> dict | None:
        blueprint_model = BlueprintModel.get()
        if blueprint_model is None:
            self.display_warning('Must supply the blueprint model instance to the command')
            return

        self._blueprint_model = blueprint_model

    @override(check_signature=False)
    def do(
            self, blueprint_model: BlueprintModel | None = None, step_path: str | None = None,
            new_name: str | None = None):

        step = self._blueprint_model.step(step_path)
        self._old_name = step.name if step else ''
        self._new_path = self._blueprint_model.rename_step(step_path, new_name)
        if self._new_path is None:
            raise RuntimeError('Failed to rename BuildStep')

    @override
    def undo(self):
        if self._new_path is None:
            return

        self._blueprint_model.rename_step(self._new_path, self._old_name)
