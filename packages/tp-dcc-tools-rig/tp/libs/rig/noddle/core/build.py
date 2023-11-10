from __future__ import annotations

import timeit

from tp.bootstrap import log
from tp.libs.rig.noddle.core import project, asset


class Build:

    CHARACTER_CLASS = None

    def __init__(self, asset_type: str, asset_name: str, existing_character: str | None = None):
        super().__init__()

        self._asset_type = asset_type
        self._asset_name = asset_name
        self._existing_character = existing_character

        self.logger = log.get_logger('.'.join([__name__, '_'.join([asset_type, asset_name])]))

        self._project = project.Project.get()
        if not self._project:
            self.logger.warning('Project is not set')
            return

        self._start_time = timeit.default_timer()
        self.logger.info('Initializing new build...')

        # set the asset and import model and latest skeleton file
        self._asset = asset.Asset(self._project, asset_name, asset_type)
        self.import_model()
        self.import_skeleton()

        # create character component
        self._character = self.create_character_component()

        self.run()
        self._character.save_bind_pose()
        self.post()

        self.logger.info('Build finished in {0:.2f}s'.format(timeit.default_timer() - self._start_time))

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

    def pre(self):
        pass

    def create_character_component(self):
        return self.CHARACTER_CLASS(component_name=self._asset_name) if self.CHARACTER_CLASS else None

    def import_model(self):
        pass

    def import_skeleton(self):
        pass

    def run(self):
        pass

    def post(self):
        pass
