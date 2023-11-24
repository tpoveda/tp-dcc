from __future__ import annotations

from overrides import override

from tp.libs.rig.noddle import api


class SetAttributeDefaultsAction(api.BuildAction):
    """
    Ses the default attribute values on animation controls, so they can be reset easily later.
    """

    id = 'Noddle.SetAttributeDefaults'
    display_name = 'Set Attribute Defaults'
    color = api.ActionColors.Controls.value
    category = api.ActionCategories.Controls.value
    attribute_definitions = [
        dict(
            name='useAnimControls',
            type=api.BuildActionAttribute.Type.Bool,
            value=True,
            description='If True, set defaults for all animation controls, works in additon to the explicit nodes.'),
        dict(
            name='nodes',
            type=api.BuildActionAttribute.Type.NodeList,
            optional=True,
            description='List of nodes to set defaults on.'),
        dict(
            name='extraAttrs',
            type=api.BuildActionAttribute.Type.StringList,
            value=['space'],
            description='List of extra attributes to set defaults for.'),
        dict(
            name='includeNonKeyable',
            type=api.BuildActionAttribute.Type.Bool,
            value=False,
            description='If True, set defaults for all keyable and non-keyable attributes.'),
    ]

    @override
    def run(self):
        """
        Performs the main functionality of this build action.
        """

        print('Hello World')
