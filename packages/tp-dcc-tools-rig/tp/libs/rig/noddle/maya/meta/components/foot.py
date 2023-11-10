from __future__ import annotations

import typing

from overrides import override
import maya.cmds as cmds

from tp.core import log
from tp.maya import api
from tp.libs.rig.noddle.core import control
from tp.libs.rig.noddle.maya.meta import animcomponent
from tp.libs.rig.noddle.maya.meta.components import fkik
from tp.libs.rig.noddle.maya.functions import attributes, naming, joints, nodes

if typing.TYPE_CHECKING:
    from tp.libs.rig.noddle.maya.meta.components.character import Character

logger = log.rigLogger


class ReverseFootComponent(animcomponent.AnimComponent):

    ID = 'noddleReverseFoot'

    ROLL_ATTRIBUTE_NAMES = ['footRoll', 'toeRoll', 'heelRoll', 'bank', 'heelTwist', 'toeTwist', 'toeTap']

    @override
    def meta_attributes(self) -> list[dict]:

        attrs = super().meta_attributes()

        attrs.extend([
            dict(name='fkControl', type=api.kMFnMessageAttribute),
            dict(name='rollAxis', type=api.kMFnDataString)
        ])

        return attrs

    @override(check_signature=False)
    def setup(
            self, parent: fkik.FKIKComponent | None = None, character: Character | None = None,
            side: str | None = None, component_name: str = 'foot', start_joint: str | None = None,
            end_joint: str | None = None, rv_chain: str | None = None, foot_locators_group: str | None = None,
            roll_axis: str = 'ry', tag: str = 'body'):

        if not isinstance(parent, fkik.FKIKComponent):
            logger.error(f'{type(parent)}: invalid component parent type: Should be {fkik.FKIKComponent}')
            raise TypeError

        side = side or parent.side

        super().setup(parent=parent, component_name=component_name, side=side, character=character, tag=tag)

        joint_chain = joints.joint_chain(api.node_by_name(start_joint), api.node_by_name(end_joint))
        attributes.add_meta_parent_attribute(joint_chain)
        control_chain = joints.duplicate_chain(
            new_joint_name=[self.indexed_name, 'ctl'], new_joint_side=self.side, original_chain=joint_chain,
            new_parent=parent.control_joints()[-1])

        self._connect_bind_joints(joint_chain)
        self._connect_control_joints(control_chain)

        rv_chain = joints.joint_chain(api.node_by_name(rv_chain))
        foot_locators_group = api.node_by_name(foot_locators_group)

        ball_handle = api.node_by_name(
            cmds.ikHandle(
                name=naming.generate_name([self.indexed_name, 'ball'], side=self.side, suffix='ikh'),
                startJoint=control_chain[0].parent().fullPathName(), endEffector=control_chain[0].fullPathName(),
                sol='ikSCsolver')[0])
        toe_handle = api.node_by_name(
            cmds.ikHandle(
                name=naming.generate_name([self.indexed_name, 'toe'], side=self.side, suffix='ikh'),
                startJoint=control_chain[0].fullPathName(), endEffector=control_chain[1].fullPathName(),
                sol='ikSCsolver')[0])

        toe_locator = None			# type: api.DagNode
        inner_locator = None		# type: api.DagNode
        outer_locator = None		# type: api.DagNode
        heel_locator = None			# type: api.DagNode
        for child in foot_locators_group.iterateChildren(node_types=(api.kTransform,)):
            if 'inner' in child.name(include_namespace=False):
                inner_locator = child
            elif 'outer' in child.name(include_namespace=False):
                outer_locator = child
            elif 'toe' in child.name(include_namespace=False):
                toe_locator = child
            elif 'heel' in child.name(include_namespace=False):
                heel_locator = child

        toe_tap_transform = nodes.create(
            'transform', name=[self.indexed_name, 'tap'], side=self.side, suffix='grp', p=rv_chain[2].fullPathName())
        toe_tap_transform.setParent(rv_chain[1])
        parent.ik_handle.setParent(rv_chain[-1])
        ball_handle.setParent(rv_chain[2])
        toe_handle.setParent(toe_tap_transform)

        foot_locators_group.setParent(parent.ik_control)
        toe_locator.setParent(heel_locator)
        outer_locator.setParent(toe_locator)
        inner_locator.setParent(outer_locator)
        rv_chain[0].setParent(inner_locator)

        parent.param_control.attribute('fkik').connect(self.controls_group.visibility)

        fk_control = control.Control.create(
            name=f'{self.indexed_name}_fk', side=self.side, guide=control_chain[0], parent=parent.fk_controls()[-1],
            delete_guide=False, not_locked_attributes='r', shape='circle_crossed', tag='fk')
        _, orient_constraint_nodes = api.build_constraint(
            control_chain[0],
            drivers={
                'targets': ((fk_control.fullPathName(partial_name=True, include_namespace=False), fk_control),)},
            constraint_type='orient'
        )
        self.add_util_nodes(orient_constraint_nodes)

        parent.param_control.attribute('fkik').connect(ball_handle.ikBlend)
        parent.param_control.attribute('fkik').connect(toe_handle.ikBlend)

        attributes.add_divider(parent.ik_control, attr_name='FOOT')
        for attr_name in ReverseFootComponent.ROLL_ATTRIBUTE_NAMES:
            parent.ik_control.addAttribute(attr_name, type=api.kMFnNumericFloat, default=0.0, keyable=True)

        parent.ik_control.attribute('footRoll').connect(rv_chain[2].attribute(roll_axis))
        parent.ik_control.attribute('toeRoll').connect(toe_locator.rotateX)
        parent.ik_control.attribute('heelRoll').connect(heel_locator.rotateX)
        parent.ik_control.attribute('toeTap').connect(toe_tap_transform.attribute(roll_axis))
        parent.ik_control.attribute('toeTwist').connect(toe_locator.rotateY)
        parent.ik_control.attribute('heelTwist').connect(heel_locator.rotateY)

        bank_condition = api.factory.create_dg_node(
            name=naming.generate_name([self.indexed_name, 'bank'], side=self.side, suffix='cond'),
            node_type='condition')
        bank_condition.operation.set(4 if self.side.lower() == 'r' else 2)
        bank_condition.colorIfFalseR.set(0)
        parent.ik_control.attribute('bank').connect(bank_condition.firstTerm)
        parent.ik_control.attribute('bank').connect(bank_condition.colorIfTrueR)
        parent.ik_control.attribute('bank').connect(bank_condition.colorIfFalseG)
        bank_condition.outColorG.connect(outer_locator.rotateZ)
        bank_condition.outColorR.connect(inner_locator.rotateZ)

        self._connect_controls([fk_control])

        self.connect_to_character(character_component=character, parent=True)
        self.attach_to_component(parent, hook_index=None)

        scale_dict = {fk_control: 0.2}
        self.scale_controls(scale_dict)

        foot_locators_group.setVisible(False)
