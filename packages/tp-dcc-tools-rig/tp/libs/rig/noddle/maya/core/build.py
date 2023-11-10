from __future__ import annotations

import maya.cmds as cmds

from tp.maya.cmds import gui
from tp.maya.om import nodes

from tp.libs.rig.noddle.core import build
from tp.libs.rig.noddle.maya.meta.components import character
from tp.libs.rig.noddle.maya.functions import assets


class MayaBuild(build.Build):

    CHARACTER_CLASS = character.Character

    def __init__(self, asset_type: str, asset_name: str, existing_character: str | None = None):

        cmds.scriptEditorInfo(e=True, sr=True)
        cmds.file(new=True, force=True)

        try:
            super().__init__(asset_type, asset_name, existing_character=existing_character)
        except Exception:
            self.logger.exception('Something went wrong during building process', exc_info=True)
        finally:
            cmds.scriptEditorInfo(edit=True, suppressResults=False)

    def create_character_component(self):
        if self._existing_character:
            return self.CHARACTER_CLASS(nodes.mobject(self._existing_character))

        return super().create_character_component()

    def import_model(self):
        assets.import_model()

    def import_skeleton(self):
        assets.import_skeleton()

    def post(self):
        cmds.select(clear=True)
        gui.set_xray_joints(True)
        cmds.viewFit(self.character.root_control.group.fullPathName())
        self.character.geometry_group.overrideEnabled.set(True)
        self.character.geometry_group.overrideColor.set(1)
