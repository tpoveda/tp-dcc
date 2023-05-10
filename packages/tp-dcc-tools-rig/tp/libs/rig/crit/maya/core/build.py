import timeit

import maya.cmds as cmds

from tp.core import log
from tp.libs.rig.crit.core import project, asset
from tp.libs.rig.crit.maya.core import rig
from tp.libs.rig.crit.library.functions import assets

logger = log.rigLogger


class Build:

	RIG_CLASS = rig.Rig

	def __init__(self, asset_type: str, asset_name: str, existing_character=None):
		super().__init__()

		# get project instance
		self._project = project.Project.get()
		if not self._project:
			logger.warning('Project is not set!')
			return

		cmds.scriptEditorInfo(edit=True, suppressResults=True)
		try:
			# start build
			cmds.file(new=True, force=True)
			self._start_time = timeit.default_timer()
			logger.info('Initializing new build...')

			# import model and skeleton
			self._asset = asset.Asset(self._project, asset_name, asset_type)
			assets.import_model()
			assets.import_skeleton()
			if existing_character:
				self._rig = self.RIG_CLASS(meta=existing_character)
				self._rig.start_session()
			else:
				self._rig = self.RIG_CLASS()
				self._rig.start_session(asset_name)

			# override build methods
			self.run()
			logger.info('Running post build...')
			self.post()

			cmds.select(clear=True)

			logger.info('Build finished in {0:.2f}s'.format(timeit.default_timer() - self._start_time))
		finally:
			cmds.scriptEditorInfo(edit=True, suppressResults=False)

	@property
	def project(self) -> project.Project:
		return self._project

	@property
	def asset(self) -> asset.Asset:
		return self._asset

	@property
	def rig(self):
		return self._rig

	@property
	def start_time(self) -> float:
		return self._start_time

	def run(self):
		pass

	def post(self):
		pass
