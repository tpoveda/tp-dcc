from __future__ import annotations

from overrides import override

from tp.libs.rig.frag import api


class CreateRigAction(api.BuildAction):
    """
    Imports all file references into the scene.
    """

    id = 'Noddle.CreateRig'
    display_name = 'Create Rig'
    color = api.ActionColors.Core.value
    category = api.ActionCategories.Core.value

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
