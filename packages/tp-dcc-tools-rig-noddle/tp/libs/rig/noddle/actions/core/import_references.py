from __future__ import annotations

from overrides import override

from tp.libs.rig.noddle import api


class ImportReferencesAction(api.BuildAction):
    """
    Imports all file references into the scene.
    """

    id = 'Noddle.ImportReferences'
    display_name = 'Import References'
    color = api.ActionColors.Core.value
    category = api.ActionCategories.Core.value
    attribute_definitions = [
        dict(
            name='loadUnloaded',
            type=api.BuildActionAttribute.Type.Bool,
            value=True),
        dict(
            name='depthLimit',
            type=api.BuildActionAttribute.Type.Int,
            value=10,
            min=1),
        dict(
            name='removeNamespace',
            type=api.BuildActionAttribute.Type.Bool,
            value=True),
    ]

    @override
    def run(self):
        """
        Performs the main functionality of this build action.
        """

        print('Hello World')
