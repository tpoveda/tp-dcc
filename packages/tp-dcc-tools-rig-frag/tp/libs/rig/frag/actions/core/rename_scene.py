from __future__ import annotations

from overrides import override

from tp.libs.rig.frag import api


class RenameSceneAction(api.BuildAction):
    """
    Renames the current scene for building. Should be performed before all other actions.

    Renaming the scene prevents accidentally saving the blueprint scene after failed builds or other modifications are
    made. The new scene acts as a sandbox for destructive operations and allows one-click re-opening of the blueprint
    scene in order to revert the build.
    """

    id = 'Noddle.RenameScene'
    display_name = 'Rename Scene'
    color = api.ActionColors.Core.value
    category = api.ActionCategories.Core.value
    attribute_definitions = [
        dict(
            name='filename',
            type=api.BuildActionAttribute.Type.String,
            value='{rigName}_built',
            description='The new scene name. Can contain the {rigName} format key.')
    ]

    @override
    def should_abort_on_error(self) -> bool:
        """
        Returns whether the build should be aborted if an error occurs while this action is running.

        :return: True if build should be aborted if error happens while running this action; False otherwise.
        :rtype: bool
        """

        return True

    @override
    def run(self):
        """
        Performs the main functionality of this build action.
        """

        print('Hello World')
