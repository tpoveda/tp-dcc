from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from tp.libs.rig.noddle.core.blueprint import BlueprintFile


class BlueprintBuilder:
    """
    Blueprint Builder that handles the build of a blueprint into a full rig.
    """

    def __init__(self, blueprint_file: BlueprintFile, debug: bool | None = None, log_dir: str | None = None):
        super().__init__()

        self._blueprint_file = blueprint_file
        self._builder_name = 'Builder'
        self._current_build_step_path: str | None = None

    @property
    def name(self) -> str:
        """
        Getter method that returns the name of this builder.

        :return: builder name.
        :rtype: str
        """

        return self._builder_name

    @property
    def current_build_step_path(self) -> str:
        """
        Getter method that returns the current build step path.

        :return: current build step path.
        :rtype: str
        """

        return self._current_build_step_path
