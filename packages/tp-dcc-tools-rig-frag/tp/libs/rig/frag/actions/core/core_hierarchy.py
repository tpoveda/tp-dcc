from __future__ import annotations

from overrides import override

from tp.libs.rig.frag import api


class BuildCoreHierarchyAction(api.BuildAction):
    """
    Builds the core hierarchy of the rig.

    This creates a group for one of the rig's main features (controls, joints, meshes, etc) and parents the
    corresponding nodes to it.
    """

    id = 'Noddle.BuildCoreHierarchy'
    display_name = 'Create Hierarchy'
    color = api.ActionColors.Core.value
    category = api.ActionCategories.Core.value
    attribute_definitions = [
        dict(
            name='groupName',
            type=api.BuildActionAttribute.Type.String,
            description='The name of the group. If empty, will use the root node of the rig.'),
        dict(
            name='groupVisible',
            type=api.BuildActionAttribute.Type.Bool,
            value=True,
            description='Whether the group should be visible or not in the built rig.'),
        dict(
            name='allNodes',
            type=api.BuildActionAttribute.Type.Bool,
            value=False,
            description='If True, include all remaining unorganized nodes in this group'),
        dict(
            name='nodes',
            type=api.BuildActionAttribute.Type.NodeList,
            optional=True,
            description='The nodes to include in this group.'),
    ]

    @override
    def run(self):
        """
        Performs the main functionality of this build action.
        """

        print('Hello World')
