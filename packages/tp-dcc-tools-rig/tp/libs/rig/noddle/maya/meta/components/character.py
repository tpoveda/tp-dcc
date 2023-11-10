from __future__ import annotations

from typing import Iterable, Iterator

from overrides import override
import maya.cmds as cmds

from tp.core import log
from tp.maya import api
from tp.libs.rig.noddle import consts
from tp.libs.rig.noddle.core import control
from tp.libs.rig.noddle.maya.meta import component
from tp.libs.rig.noddle.maya.functions import attributes, joints, rig, outliner

logger = log.rigLogger


class Character(component.Component):

    ID = 'noddleCharacter'

    TOP_RIG_NODE_NAME = consts.CharacterMembers.top_node.value
    CONTROL_RIG_GROUP_NAME = consts.CharacterMembers.control_rig.value
    DEFORMATION_RIG_GROUP_NAME = consts.CharacterMembers.deformation_rig.value
    LOCATORS_GROUP_NAME = consts.CharacterMembers.locators.value
    UTILS_GROUP_NAME = consts.CharacterMembers.util_group.value
    GEOMETRY_GROUP_NAME = consts.CharacterMembers.geometry.value
    WORLD_SPACE_LOCATOR_NAME = consts.CharacterMembers.world_space.value

    IGNORE_EXISTING_CONSTRAINTS_ON_SKELETON_ATTACHMENT = False

    @override
    def meta_attributes(self) -> list[dict]:

        attrs = super().meta_attributes()

        attrs.extend([
            dict(name='characterName', type=api.kMFnDataString),
            dict(name='rootCtl', type=api.kMFnMessageAttribute),
            dict(name='controlRig', type=api.kMFnMessageAttribute),
            dict(name='deformationRig', type=api.kMFnMessageAttribute),
            dict(name='geometryGroup', type=api.kMFnMessageAttribute),
            dict(name='locatorsGroup', type=api.kMFnMessageAttribute),
            dict(name='worldLocator', type=api.kMFnMessageAttribute),
            dict(name='utilsGrp', type=api.kMFnMessageAttribute),
            dict(name='rootMotionJoint', type=api.kMFnMessageAttribute),
        ])

        return attrs

    @override(check_signature=False)
    def setup(self, parent: component.Component | None = None, component_name: str = 'character', tag: str = 'character'):

        super().setup(parent=parent, component_name=component_name, side='char', tag=tag)

        root_control = control.Control.create(
            name='character', side='c', offset_group=False, not_locked_attributes='trs', shape='character', tag='root',
            orient_axis='y')
        root_control.group.rename(self.TOP_RIG_NODE_NAME)

        control_rig = api.factory.create_dag_node(self.CONTROL_RIG_GROUP_NAME, 'transform', parent=root_control)
        deformation_rig = api.factory.create_dag_node(self.DEFORMATION_RIG_GROUP_NAME, 'transform', parent=root_control)
        locators_group = api.factory.create_dag_node(self.LOCATORS_GROUP_NAME, 'transform', parent=root_control)
        utils_group = api.factory.create_dag_node(self.UTILS_GROUP_NAME, 'transform', parent=root_control)
        world_locator = api.node_by_name(str(cmds.spaceLocator(n=self.WORLD_SPACE_LOCATOR_NAME)[0]))
        world_locator.setParent(locators_group)
        locators_group.setVisible(False)

        if not cmds.objExists(self.GEOMETRY_GROUP_NAME):
            geometry_group = api.factory.create_dag_node(self.GEOMETRY_GROUP_NAME, 'transform', parent=root_control)
        else:
            geometry_group = api.node_by_name(self.GEOMETRY_GROUP_NAME)
            geometry_group.setParent(root_control)
        geometry_group.inheritsTransform.set(False)

        attributes.add_meta_parent_attribute(
            [control_rig, deformation_rig, geometry_group, locators_group, world_locator, utils_group])

        self.attribute('characterName').set(component_name)
        root_control.attribute(consts.MPARENT_ATTR_NAME).connect(self.rootCtl)
        control_rig.attribute(consts.MPARENT_ATTR_NAME).connect(self.controlRig)
        deformation_rig.attribute(consts.MPARENT_ATTR_NAME).connect(self.deformationRig)
        geometry_group.attribute(consts.MPARENT_ATTR_NAME).connect(self.geometryGroup)
        locators_group.attribute(consts.MPARENT_ATTR_NAME).connect(self.locatorsGroup)
        world_locator.attribute(consts.MPARENT_ATTR_NAME).connect(self.worldLocator)
        utils_group.attribute(consts.MPARENT_ATTR_NAME).connect(self.utilsGrp)

        root_control.addAttribute('Scale', value=1.0, default=1.0, type=api.kMFnNumericFloat, keyable=True)
        root_control.Scale.connect(root_control.scaleX)
        root_control.Scale.connect(root_control.scaleY)
        root_control.Scale.connect(root_control.scaleZ)

        if self.clamped_size() > 0.0:
            root_control.scale_shapes(self.clamped_size())

        attributes.lock(root_control, ['sx', 'sy', 'sz'])

        self.set_outliner_color(18)

    def control_rig_group(self) -> api.DagNode:
        """
        Returns the node under rig controls should be placed within the scene hierarchy.

        :return: control rig group.
        :rtype: api.DagNode
        """

        return self.sourceNodeByName('controlRig')

    def deformation_rig_group(self) -> api.DagNode:
        return self.sourceNodeByName('deformationRig')

    def geometry_group(self) -> api.DagNode:
        return self.sourceNodeByName('geometryGroup')

    def locators_group(self) -> api.DagNode:
        return self.sourceNodeByName('geometryGroup')

    def utils_group(self) -> api.DagNode:
        return self.sourceNodeByName('utilsGrp')

    def root_control(self) -> control.Control:
        return control.Control(node=self.attribute('rootCtl').sourceNode().object())

    def world_locator(self) -> api.DagNode:
        return self.sourceNodeByName('worldLocator')

    def set_outliner_color(self, color: int | str | Iterable[float, float, float]):
        """
        Sets the color of the character root control within outliner panel.

        :param int or str or Iterable[float, float, float] color: outliner color to set.
        """

        outliner.set_color(self.root_control, color)

    def size(self, axis: str = 'y') -> float:
        """
        Returns the size of the character based on the bounding box of the geometry group.

        :param str axis: axis to get size from.
        :return: character size.
        :rtype: float
        """

        bounding_box = cmds.exactWorldBoundingBox(self.geometry_group.fullPathName())
        if axis == 'x':
            return bounding_box[3] - bounding_box[0]
        elif axis == 'y':
            return bounding_box[4] - bounding_box[1]
        elif axis == 'z':
            return bounding_box[5] - bounding_box[2]

    def clamped_size(self) -> float:
        """
        Returns the clamped size of the character based on the bounding box of the geometry group.

        :return: character clamped size.
        :rtype: float
        """

        return max(self.size('y') * 0.3, self.size('x') * 0.3)

    def save_bind_pose(self):
        """
        Saves the current control pose into the bindPose attribute of the controls transform node.
        """

        controls = rig.list_controls()
        for found_control in controls:
            found_control.write_bind_pose()
        logger.info(f'Written {len(controls)} bind poses')

    def add_root_motion(
            self, follow_object: api.DagNode, root_joint: str | None = None,
            children: list[api.Joint] | None = None, up_axis: str = 'y') -> api.Joint:
        """
        Creates the root motion and connects it to the given follow object.

        :param api.DagNode follow_object: node that root joint should follow.
        :param str or None root_joint: name of the root joint. If not given, a new root joint will be created.
        :param List[api.Joint] or None children: optional list of joints to parent under the root joint.
        :param str up_axis: root joint up axis. This axis will not be constrained.
        :return: root joint instance.
        :rtype: api.Joint
        """

        root_joint = api.node_by_name(root_joint) if root_joint else None
        root_joint = root_joint or joints.create_root_joint(children=children)
        root_joint.setParent(self.deformation_rig_group)
        attributes.add_meta_parent_attribute([root_joint])
        _, point_constraint_nodes = api.build_constraint(
            root_joint,
            drivers={'targets': ((follow_object.fullPathName(partial_name=True, include_namespace=False), follow_object),)},
            constraint_type='point', maintainOffset=True, skip=up_axis
        )
        self.add_util_nodes(point_constraint_nodes)
        root_joint.attribute(consts.MPARENT_ATTR_NAME).connect(self.attribute('rootMotionJoint'))

        return root_joint

    def iterate_components(self) -> Iterator[component.Component]:
        """
        Generator function that iterates over all component connected to this character.

        :return: iterated components.
        :rtype: Iterator[component.Component]
        """

        for meta_child in self.iterate_meta_children(depth_limit=1):
            yield meta_child

    def components(self) -> list[component.Component]:
        """
        Function that returns all components connected to this character.

        :return: components.
        :rtype: List[component.Component]
        """

        return list(self.iterate_components())

    def attach_to_skeleton(self):
        """
        Attaches character components into the character skeleton.
        """

        for found_component in self.components():
            found_component.attach_to_skeleton()
