from __future__ import annotations

import timeit

import maya.cmds as cmds

from tp.maya.om import nodes
from tp.bootstrap import log
from tp.maya.cmds import gui
from tp.libs.rig.noddle.core import project, asset
from tp.libs.rig.noddle.functions import assets
from tp.libs.rig.noddle.meta.components import character


class Build:

	CHARACTER_CLASS = character.Character

	def __init__(self, asset_type: str, asset_name: str, existing_character: str | None = None):
		super().__init__()

		self.logger = log.get_logger('.'.join([__name__, '_'.join([asset_type, asset_name])]))

		self._project = project.Project.get()
		if not self._project:
			self.logger.warning('Project is not set')
			return

		cmds.scriptEditorInfo(e=True, sr=True)
		cmds.file(new=True, force=True)

		self._start_time = timeit.default_timer()
		self.logger.info('Initializing new build...')

		try:

			# set the asset and import model and latest skeleton file
			self._asset = asset.Asset(self._project, asset_name, asset_type)
			assets.import_model()
			assets.import_skeleton()

			# create character component
			if existing_character:
				self._character = self.CHARACTER_CLASS(nodes.mobject(existing_character))
			else:
				self._character = self.CHARACTER_CLASS(component_name=asset_name)

			self.run()
			self._character.save_bind_pose()
			self.post()

			cmds.select(clear=True)
			gui.set_xray_joints(True)
			cmds.viewFit(self.character.root_control.group.fullPathName())
			self.character.geometry_group.overrideEnabled.set(True)
			self.character.geometry_group.overrideColor.set(1)

			self.logger.info('Build finished in {0:.2f}s'.format(timeit.default_timer() - self._start_time))
		except Exception:
			self.logger.exception('Something went wrong during building process', exc_info=True)
		finally:
			cmds.scriptEditorInfo(edit=True, suppressResults=False)


	@property
	def project(self) -> project.Project:
		return self._project

	@property
	def asset(self) -> asset.Asset:
		return self._asset

	@property
	def character(self):
		return self._character

	@property
	def start_time(self) -> float:
		return self._start_time

	def run(self):
		pass

	def post(self):
		pass
