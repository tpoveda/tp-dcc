from __future__ import annotations

from tp.core import command


def rename_step(step_path: str, new_name: str):
    """
    Renames a step path located within given blueprint model with the new name.

    :param str step_path: path of the build step to rename.
    :param str new_name: new build step name.
    """

    return command.execute('noddle.rig.builder.buildstep.rename', **locals())
