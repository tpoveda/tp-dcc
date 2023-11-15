from __future__ import annotations

import enum
import typing

from overrides import override
import maya.cmds as cmds

from tp.maya import api
from tp.libs.rig.noddle import consts
from tp.libs.rig.noddle.core import control
from tp.libs.rig.noddle.maya.meta import animcomponent
from tp.libs.rig.noddle.maya.functions import attributes, naming, joints, curves

if typing.TYPE_CHECKING:
    from tp.libs.rig.noddle.maya.meta.components.character import Character


class SpineComponent(animcomponent.AnimComponent):

    ID = 'noddleSpine'

    @override
    def meta_attributes(self) -> list[dict]:

        attrs = super().meta_attributes()

        attrs.extend([
            dict(name='rootControl', type=api.kMFnMessageAttribute),
            dict(name='hipsControl', type=api.kMFnMessageAttribute),
            dict(name='chestControl', type=api.kMFnMessageAttribute),
        ])

        return attrs

    @override(check_signature=False)
    def setup(
            self, parent: animcomponent.AnimComponent | None = None, component_name: str = 'spine', side: str = 'c',
            tag: str = 'body', character: Character | None = None):

        super().setup(parent=parent, component_name=component_name, side=side, tag=tag, character=character)

    def root_control(self) -> control.Control:
        """
        Returns this component root control.

        :return: root control.
        :rtype: control.Control
        """

        return control.Control(self.sourceNodeByName('rootControl').object())

    def hips_control(self) -> control.Control:
        """
        Returns this component hips control.

        :return: root control.
        :rtype: control.Control
        """

        return control.Control(self.sourceNodeByName('hipsControl').object())

    def chest_control(self) -> control.Control:
        """
        Returns this component chest control.

        :return: root control.
        :rtype: control.Control
        """

        return control.Control(self.sourceNodeByName('chestControl').object())


class FKIKSpineComponent(SpineComponent):

    ID = 'noddleFkIkSpine'

    class Hooks(enum.Enum):

        ROOT = 0
        HIPS = 1
        MID = 2
        CHEST = 3

    @override
    def meta_attributes(self) -> list[dict]:

        attrs = super().meta_attributes()

        attrs.extend([
            dict(name='fkControls', type=api.kMFnMessageAttribute, isArray=True, indexMatters=False),
            dict(name='midControl', type=api.kMFnMessageAttribute),
            dict(name='ikCurve', type=api.kMFnMessageAttribute),
        ])

        return attrs

    @override(check_signature=False)
    def setup(
            self, parent: animcomponent.AnimComponent | None = None, component_name: str = 'spine', side: str = 'c',
            tag: str = 'body', hook: int = 0, character: Character | None = None, start_joint: str | None = None,
            end_joint: str | None = None, up_axis: str = 'y', forward_axis: str = 'x'):

        super().setup(parent=parent, component_name=component_name, side=side, tag=tag, character=character)

        joint_chain = joints.joint_chain(api.node_by_name(start_joint), api.node_by_name(end_joint))
        joints.validate_rotations(joint_chain)
        attributes.add_meta_parent_attribute(joint_chain)
        control_chain = joints.duplicate_chain(
            new_joint_name=[self.indexed_name, 'ctl'], new_joint_side=self.side, original_chain=joint_chain,
            new_parent=self.joints_group())

        ik_curve_points = [list(joint.translation(space=api.kWorldSpace)) for joint in joint_chain]
        ik_curve = curves.curve_from_points(
            name=naming.generate_name([self.indexed_name, 'ik'], side=self.side, suffix='crv'),
            points=ik_curve_points, parent=self.no_scale_group())
        attributes.add_meta_parent_attribute([ik_curve])
        cmds.rebuildCurve(ik_curve.fullPathName(), d=3, kep=True, rpo=True, ch=False, tol=0.01, spans=4)
        ik_handle = api.node_by_name(
            cmds.ikHandle(
                name=naming.generate_name(self.component_name, side=self.side, suffix='ikh'),
                startJoint=control_chain[0].fullPathName(), endEffector=control_chain[-1].fullPathName(),
                curve=ik_curve.fullPathName(), sol='ikSplineSolver', rootOnCurve=True, parentCurve=False,
                createCurve=False, simplifyCurve=False)[0])
        ik_handle.setParent(self.parts_group())

        control_locator = api.node_by_name(cmds.spaceLocator(n='temp_control_loc')[0])
        control_locator.setTranslation(api.Vector(*cmds.pointOnCurve(ik_curve.fullPathName(), pr=0.0, top=True)))
        root_control = control.Control.create(
            name=f'{self.indexed_name}_root', side=self.side, guide=control_locator, delete_guide=False,
            parent=self.controls_group(), joint=False, not_locked_attributes='tr', color='red', shape='root',
            orient_axis=up_axis)
        hips_control = control.Control.create(
            name=f'{self.indexed_name}_hips', side=self.side, guide=control_chain[0], delete_guide=False,
            parent=root_control, joint=True, not_locked_attributes='tr', shape='circle_down_arrow', orient_axis=up_axis)
        control_locator.setTranslation(api.Vector(*cmds.pointOnCurve(ik_curve.fullPathName(), pr=0.5, top=True)))
        mid_control = control.Control.create(
            name=f'{self.indexed_name}_mid', side=self.side, guide=control_locator, delete_guide=False,
            parent=root_control, joint=True, not_locked_attributes='tr', shape='circle_up_arrow',
            orient_axis=up_axis)
        mid_control.addAttribute('followChest', type=api.kMFnNumericFloat, default=0.0, keyable=True)
        mid_control.addAttribute('followHips', type=api.kMFnNumericFloat, default=0.0, keyable=True)
        chest_control = control.Control.create(
            name=f'{self.indexed_name}_chest', side=self.side, guide=control_chain[-1], delete_guide=False,
            parent=root_control, joint=True, not_locked_attributes='tr', shape='chest', orient_axis=up_axis)
        cmds.delete(cmds.orientConstraint(
            chest_control.group.fullPathName(), hips_control.group.fullPathName(), mid_control.group.fullPathName()))
        for ctrl in [hips_control, mid_control, chest_control]:
            ctrl.rotate_shape((0, 0, -90))

        cns, parent_constraint_nodes = api.build_constraint(
            mid_control.group,
            drivers={
                'targets': (
                    (hips_control.fullPathName(partial_name=True, include_namespace=False), hips_control),
                    (chest_control.fullPathName(partial_name=True, include_namespace=False), chest_control),
                )
            },
            constraint_type='parent', maintainOffset=True
        )
        self.add_util_nodes(parent_constraint_nodes)
        mid_control.followHips.connect(cns.constraint_node.target[0].child(cns.CONSTRAINT_TARGET_INDEX))
        mid_control.followChest.connect(cns.constraint_node.target[1].child(cns.CONSTRAINT_TARGET_INDEX))

        skin_cluster = api.node_by_name(cmds.skinCluster(
            [hips_control.joint.fullPathName(), mid_control.joint.fullPathName(), chest_control.joint.fullPathName()],
            ik_curve.fullPathName(), n=naming.generate_name(self.component_name, self.side, suffix='skin'))[0])
        self.add_util_nodes([skin_cluster])

        ik_handle.dTwistControlEnable.set(True)
        ik_handle.dWorldUpType.set(4)
        hips_control.attribute('worldMatrix')[0].connect(ik_handle.dWorldUpMatrix)
        chest_control.attribute('worldMatrix')[0].connect(ik_handle.dWorldUpMatrixEnd)
        ik_handle.dWorldUpVectorZ.set(1)
        ik_handle.dWorldUpVectorY.set(0)
        ik_handle.dWorldUpVectorEndZ.set(1)
        ik_handle.dWorldUpVectorEndY.set(0)

        control_locator.setTranslation(api.Vector(*cmds.pointOnCurve(ik_curve.fullPathName(), pr=0.25, top=True)))
        fk1_control = control.Control.create(
            name=f'{self.indexed_name}_fk', side=self.side, guide=control_locator, delete_guide=False,
            parent=root_control, joint=True, not_locked_attributes='tr', shape='circle_up_arrow',
            orient_axis=up_axis)
        cmds.delete(cmds.orientConstraint(
            hips_control.group.fullPathName(), mid_control.group.fullPathName(), fk1_control.group.fullPathName()))
        fk1_control.rotate_shape((0, 0, -90))

        control_locator.setTranslation(api.Vector(*cmds.pointOnCurve(ik_curve.fullPathName(), pr=0.75, top=True)))
        fk2_control = control.Control.create(
            name=f'{self.indexed_name}_fk', side=self.side, guide=control_locator, delete_guide=True,
            parent=fk1_control, joint=True, not_locked_attributes='tr', shape='circle_up_arrow',
            orient_axis=up_axis)
        cmds.delete(cmds.orientConstraint(
            hips_control.group.fullPathName(), mid_control.group.fullPathName(), fk2_control.group.fullPathName()))
        cmds.matchTransform(fk2_control.joint.fullPathName(), control_chain[-1].fullPathName())
        cmds.makeIdentity(fk2_control.joint.fullPathName(), apply=True)
        fk2_control.rotate_shape((0, 0, -90))

        _, parent_constraint_nodes = api.build_constraint(
            chest_control.group,
            drivers={
                'targets': (
                    (fk2_control.joint.fullPathName(partial_name=True, include_namespace=False), fk2_control.joint),
                )
            },
            constraint_type='parent', maintainOffset=True
        )
        self.add_util_nodes(parent_constraint_nodes)

        self._connect_bind_joints(joint_chain)
        self._connect_control_joints(control_chain)
        self._connect_controls([root_control, hips_control, mid_control, chest_control, fk1_control, fk2_control])
        self._connect_settings([mid_control.attribute('followChest'), mid_control.attribute('followHips')])

        for fk_control in [fk1_control, fk2_control]:
            fk_control.attribute(consts.MPARENT_ATTR_NAME).connect(
                self.attribute('fkControls').nextAvailableDestElementPlug())
        root_control.attribute(consts.MPARENT_ATTR_NAME).connect(self.attribute('rootControl'))
        hips_control.attribute(consts.MPARENT_ATTR_NAME).connect(self.attribute('hipsControl'))
        mid_control.attribute(consts.MPARENT_ATTR_NAME).connect(self.attribute('midControl'))
        chest_control.attribute(consts.MPARENT_ATTR_NAME).connect(self.attribute('chestControl'))
        ik_curve.attribute(consts.MPARENT_ATTR_NAME).connect(self.attribute('ikCurve'))

        self.add_hook(root_control, 'root')
        self.add_hook(control_chain[0], 'hips')
        self.add_hook(mid_control, 'mid')
        self.add_hook(control_chain[-1], 'chest')

        self.connect_to_character(character_component=character, parent=True)
        self.attach_to_component(parent, hook)

        scale_dict = {
            root_control: 0.4,
            hips_control: 0.35,
            mid_control: 0.3,
            chest_control: 0.25,
            fk1_control: 0.35,
            fk2_control: 0.35
        }
        self.scale_controls(scale_dict)

        ik_handle.setVisible(False)
        self.parts_group().setVisible(False)
        self.joints_group().setVisible(False)

    def mid_control(self) -> control.Control:
        """
        Returns this component mid-control.

        :return: mid control.
        :rtype: control.Control
        """

        return control.Control(self.sourceNodeByName('rootControl').object())

    def fk1_control(self) -> control.Control:
        """
        Returns this component FK first control.

        :return: FK first control.
        :rtype: control.Control
        """

        return control.Control(self.attribute('fkControls')[0].sourceNode().object())

    def fk2_control(self) -> control.Control:
        """
        Returns this component FK second control.

        :return: FK second control.
        :rtype: control.Control
        """

        return control.Control(self.attribute('fkControls')[1].sourceNode().object())

    def pivot_control(self) -> control.Control | None:
        """
        Returns this component pivot control.

        :return: pivot control.
        :rtype: control.Control
        """

        if not self.hasAttribute('pivotControl'):
            return None

        return control.Control(self.sourceNodeByName('pivotControl').object())

    def ik_curve(self) -> api.DagNode | None:
        """
        Returns this component IK curve.

        :return: IK curve.
        :rtype: api.DagNode
        """

        return self.attribute('ikCurve').sourceNode()

    def root_hook_index(self) -> int:
        """
        Returns root hook index.

        :return: root hook index.
        :rtype: int
        """

        return self.Hooks.ROOT.value

    def hips_hook_index(self) -> int:
        """
          Returns hips hook index.

          :return: hips hook index.
          :rtype: int
          """

        return self.Hooks.HIPS.value

    def mid_hook_index(self) -> int:
        """
          Returns mid hook index.

          :return: mid hook index.
          :rtype: int
          """

        return self.Hooks.MID.value

    def chest_hook_index(self) -> int:
        """
          Returns chest hook index.

          :return: chest hook index.
          :rtype: int
          """

        return self.Hooks.CHEST.value
