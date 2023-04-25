#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains rig utils functions for Maya
"""

import math

import maya.cmds

from tp.core import log, dcc
from tp.common.python import helpers
from tp.maya.cmds import constraint as cns_utils, attribute as attr_utils, transform as transform_utils
from tp.maya.cmds import joint as jnt_utils, animation as anim_utils, space as space_utils, skin as skin_utils
from tp.maya.cmds import shape as shape_utils, geometry as geo_utils, rivet as rivet_utils, ik as ik_utils

logger = log.tpLogger


class RigSwitch(object):
    """
    Creates a switch between different rigs on a buffer joint
    """

    def __init__(self, switch_joint, switch_attribute_name='switch'):
        """
        Constructor
        :param switch_joint: str, name of a buffer joint with switch attribute
        """

        self._switch_joint = switch_joint
        self._attribute_name = switch_attribute_name
        self._groups = dict()
        self._control_name = None
        self._conditions = dict()

        if not maya.cmds.objExists('{}.{}'.format(switch_joint, switch_attribute_name)):
            logger.warning('{} is most likely not a buffer joint with switch attribute'.format(switch_joint))

        weight_count = self.get_weight_count()
        if not weight_count:
            logger.warning('{} has no weights!'.format(weight_count))

        for i in range(weight_count):
            self._groups[i] = None

    @property
    def switch_joint(self):
        return self._switch_joint

    @property
    def attribute_name(self):
        return self._attribute_name

    @property
    def groups(self):
        return self._groups

    @property
    def control_name(self):
        return self._control_name

    @property
    def conditions(self):
        return self._conditions

    def create(self):
        if self._control_name and maya.cmds.objExists(self._control_name):
            weight_count = self.get_weight_count()
            var = attr_utils.NumericAttribute(self._attribute_name)
            var.set_min_value(0)
            max_value = weight_count - 1
            if max_value > var._get_max_value():
                max_value = var._get_max_value()
            var.set_max_value(max_value)
            var.set_keyable(True)
            var.create(self._control_name)
            attr_name = var.get_name()
            maya.cmds.connectAttr(attr_name, '{}.{}'.format(self._switch_joint, self._attribute_name))
        elif not self._control_name or not maya.cmds.objExists(self._control_name):
            attr_name = '{}.{}'.format(self._switch_joint, self._attribute_name)
        else:
            logger.error('Impossible to create RigSwitch Attribute ...')
            return

        for key in self._groups.keys():
            groups = self._groups[key]
            if not groups:
                continue
            for group in groups:
                self._conditions[group] = attr_utils.connect_equal_condition(
                    attr_name, '{}.visibility'.format(group), key)

    def get_weight_count(self):
        edit_cns = cns_utils.Constraint()
        cns = edit_cns.get_constraint(self._switch_joint, 'parentConstraint')
        if cns:
            weight_count = edit_cns.get_weight_count(cns)
        else:
            switch_nodes = cns_utils.SpaceSwitch().get_space_switches(self._switch_joint)
            if switch_nodes:
                sources = cns_utils.SpaceSwitch().get_source(switch_nodes[0])
                weight_count = len(sources)
            else:
                weight_count = 0

        return weight_count

    def add_groups_to_index(self, index, groups):
        """
        A switch joint is meant to switch visibility between rigs
        By adding groups you define their visibility when switch attributes changes
        An index 0 means the group will be visible when the switch is 0 and invisible when is 1
        :param index: int, index on the switch. Need sto be an integer value event though switch is a float
        :param groups: list<str>, list of groups that should have visibility attached to the given index
        """

        groups = helpers.force_list(groups)
        if not self._switch_joint or not maya.cmds.objExists(self._switch_joint):
            logger.warning('Swtich joint {} does not exists!'.format(self._switch_joint))
            return

        weight_count = self.get_weight_count()
        if weight_count < (index + 1):
            logger.warning(
                'Adding groups to index {} is undefined. {}.switch does not have that many inputs'.format(
                    index, self._switch_joint))

        self._groups[index] = groups

    def set_attribute_control(self, transform):
        """
        Set where the switch attribute should be stored
        :param transform: str, name of a transform
        """

        self._control_name = transform

    def set_attribute_name(self, attr_name):
        """
        Sets the name of the switch attribute on the attribute control
        :param attr_name: str, name for the switch attribute
        """

        self._attribute_name = attr_name


class StretchyChain(object):
    """
    Class that allow to setup stretch chain setup
    """

    def __init__(self):
        self._side = 'C'
        self._joints = list()
        self._inputs = list()
        self._attribute_node = None
        self._distance_offset_attribute = None
        self._add_damp = False
        self._stretch_offsets = list()
        self._distance_offset = None
        self._scale_axis = 'X'
        self._name = 'stretch'
        self._simple = False
        self._per_joint_stretch = True
        self._vector = False
        self._extra_joint = None
        self._damp_name = 'dampen'
        self._scale_offset = 1
        self._attribute_name = 'autoStretch'
        self._default_vaue = 0
        self._create_title = True
        self._stretch_condition = None
        self._divide_distance = None
        self._plus_total_offset = None
        self._orig_distance = None

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_joints(self, joints):
        """
        Sets the joints that will be stretched by the system
        :param joints: list(str)
        """

        self._joints = joints

    def set_node_for_attributes(self, node_name):
        """
        Sets the the node that will have the attributes to manage stretchy setup
        :param node_name: str
        """

        self._attribute_node = node_name

    def set_scale_axis(self, axis_letter):
        """
        Sets the axis where the stretch will occur
        :param axis_letter: str ('X', 'Y', 'Z')
        """

        self._scale_axis = axis_letter.capitalize()

    def set_distance_offset(self, attr):
        """
        Sets the distance offset
        :param attr: float
        """

        self._distance_offset_attribute = attr

    def set_vector_instead_of_matrix(self, flag):
        self._vector = flag

    def set_add_damp(self, flag, damp_name=None):
        self._add_damp = flag
        if damp_name:
            self._damp_name = damp_name

    def set_simple(self, flag):
        self._simple = flag

    def set_description(self, description):
        self._name = '{}_{}'.format(self._name, description)

    def set_per_joint_stretch(self, flag):
        self._per_joint_stretch = flag

    def set_scale_attribute_offset(self, value):
        self._scale_offset = value

    def set_extra_joint(self, joint):
        self._extra_joint = joint

    def set_attribute_name(self, attr_name):
        self._attribute_name = attr_name

    def set_default_value(self, value):
        self._default_vaue = value

    def set_create_title(self, flag):
        self._create_title = flag

    def create(self):
        top_locator, bottom_locator = self._build_stretch_locators()
        if self._simple:
            for jnt in self._joints[:-1]:
                distance_offset = self._create_distance_offset()
                self._create_stretch_distance(top_locator, bottom_locator, distance_offset)
                divide_distance = self._create_divide_distance()
                dcc.connect_attribute(distance_offset, 'outputX', divide_distance, 'input1X')
                dcc.connect_attribute(divide_distance, 'outputX', jnt, 'scale{}'.format(self._scale_axis))
        else:
            stretch_condition = self._create_stretch_condition()
            distance_offset = self._create_distance_offset(stretch_condition=stretch_condition)
            self._create_stretch_distance(top_locator, bottom_locator, distance_offset)
            stretch_on_off = self._create_stretch_on_off(stretch_condition)
            divide_distance = self._create_divide_distance(stretch_condition, stretch_on_off)
            stretch_offsets = self._create_offsets(divide_distance)

            if self._attribute_node:
                self._create_attributes(stretch_on_off)
                self._create_offset_attributes(stretch_offsets)
                if self._extra_joint:
                    self._add_joint(self._extra_joint)
                if self._add_damp:
                    self._create_damp(distance_offset, [
                        '{}.firstTerm'.format(stretch_condition), '{}.colorIfTrueR'.format(stretch_condition),
                        '{}}.color2R'.format(stretch_on_off), '{}.input2X'.format(divide_distance)])

            if self._distance_offset_attribute:
                self._create_other_distance_offset(distance_offset)

        return top_locator, bottom_locator

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _get_joint_count(self):
        return len(self._joints)

    def _get_length(self):
        length = 0
        joint_count = self._get_joint_count()
        for i in range(joint_count):
            if i + 1 == joint_count:
                break
            current_joint = self._joints[i]
            next_joint = self._joints[i + 1]
            distance = dcc.distance_between_nodes(current_joint, next_joint)
            length += distance

        return length

    def _build_stretch_locators(self):
        top_distance_locator = dcc.create_empty_group(
            name=dcc.find_unique_name('locator_topDistance_{}'.format(self._name)))
        match = dcc.match_translation_rotation(self._joints[0], top_distance_locator)

        bottom_distance_locator = dcc.create_empty_group(
            name=dcc.find_unique_name('locator_bottomDistance_{}'.format(self._name)))
        match = dcc.match_translation_rotation(self._joints[-1], top_distance_locator)

        if not self._attribute_node:
            self._attribute_node = top_distance_locator

        return top_distance_locator, bottom_distance_locator

    def _create_distance_offset(self, stretch_condition=None):
        multiply = attr_utils.MultiplyDivideNode('offset_{}'.format(self._name))
        multiply.set_operation(2)
        multiply.set_input2(1, 1, 1)

        if stretch_condition:
            multiply.outputX_out('{}.secondTerm'.format(stretch_condition))
            multiply.outputX_out('{}.colorIfFalseR'.format(stretch_condition))

        return multiply.node

    def _create_stretch_distance(self, top_locator, bottom_locator, distance_offset):
        distance_between = dcc.create_node(
            node_name=dcc.find_unique_name('distanceBetween_{}'.format(self._name)), node_type='distanceBetween')
        if self._vector:
            dcc.connect_attribute(top_locator, 'translate', distance_between, 'point1')
            dcc.connect_attribute(bottom_locator, 'translate', distance_between, 'point2')
        else:
            dcc.connect_attribute(top_locator, 'worldMatrix', distance_between, 'inMatrix1')
            dcc.connect_attribute(bottom_locator, 'worldMatrix', distance_between, 'inMatrix2')
        dcc.connect_attribute(distance_between, 'distance', distance_offset, 'input1X')

        return distance_between

    def _create_divide_distance(self, stretch_condition=None, stretch_on_off=None):
        multiply = attr_utils.MultiplyDivideNode('distance_{}'.format(self._name))
        multiply.set_operation(2)
        multiply.set_input2(self._get_length(), 1, 1)

        if stretch_condition:
            if stretch_on_off:
                multiply.input1X_in('{}.outputR'.format(stretch_on_off))
            else:
                multiply.input1X_in('{}.outColorR'.format(stretch_on_off))

        self._divide_distance = multiply.node

        return multiply.node

    def _create_stretch_condition(self):
        total_length = self._get_length()
        condition = dcc.create_node(
            node_name=dcc.find_unique_name('{}_stretchCondition'.format(self._name)), node_type='condition')
        dcc.set_integer_attribute_value(condition, 'operation', 2)
        dcc.set_integer_attribute_value(condition, 'firstTerm', total_length)
        dcc.set_integer_attribute_value(condition, 'colorIfTrueR', total_length)
        self._stretch_condition = condition

        return condition

    def _create_stretch_on_off(self, stretch_condition):
        blend = dcc.create_node(
            node_name=dcc.find_unique_name('blendColors_{}'.format(self._name)), node_type='blendColors')
        dcc.set_integer_attribute_value(blend, 'color2R', self._get_length())
        dcc.set_integer_attribute_value(blend, 'blender', 1)
        dcc.connect_attribute(stretch_condition, 'outColorR', blend, 'color1R')

        return blend

    def _create_offsets(self, divide_distance):
        stretch_offsets = list()

        plus_total_offset = dcc.create_node(
            node_name=dcc.find_unique_name('plusMinusAverage_total_offset_{}'.format(
                self._name)), node_type='plusMinusAverage')
        self._plus_total_offset = plus_total_offset
        dcc.set_integer_attribute_value(plus_total_offset, 'operation', 3)

        for i in range(self._get_joint_count() - 1):
            var_name = 'offset{}'.format(i + 1)
            multiply = attr_utils.connect_multiply(
                '{}.outputX'.format(divide_distance), '{}.scale{}'.format(self._joints[i], self._scale_axis), 1)
            dcc.add_double_attribute(multiply, var_name, min_value=0.1, default_value=self._scale_offset)

            if self._scale_offset != 1:
                offset_multiply = dcc.create_node(
                    node_name='multiplyDivide_scaleOffset', node_type='multiplyDivide')
                dcc.connect_attribute(multiply, var_name, offset_multiply, 'input1X')
                offset_value = 1.0 / self._scale_offset
                dcc.set_float_attribute_value(offset_multiply, 'input2X', offset_value)
                dcc.connect_attribute(offset_multiply, 'outputX', multiply, 'input2X')
                dcc.connect_attribute(offset_multiply, 'outputX', plus_total_offset, 'input1D[{}]'.format(i + 1))
            elif self._scale_offset == 1:
                dcc.connect_attribute(multiply, var_name, multiply, 'input1X')
                dcc.connect_attribute(multiply, var_name, plus_total_offset, 'input1D[{}]'.format(i + 1))

            stretch_offsets.append(multiply)

        orig_distance_multiply = dcc.create_node(
            node_name=dcc.find_unique_name('multiplyDivide_orig_distance_{}'.format(self._name)),
            node_type='multiplyDivide')
        self._orig_distance = orig_distance_multiply
        length = self._get_length()
        dcc.set_float_attribute_value(orig_distance_multiply, 'input1X', length)
        dcc.connect_attribute(plus_total_offset, 'output1D', orig_distance_multiply, 'input2X')

        self._stretch_offsets = stretch_offsets

        return stretch_offsets

    def _create_attributes(self, stretch_on_off):
        if self._create_title:
            dcc.add_title_attribute(self._attribute_node, 'STRETCH')

        dcc.add_double_attribute(
            self._attribute_node, self._attribute_name, min_value=0, max_value=1, default_value=self._default_vaue)
        dcc.connect_attribute(self._attribute_node, self._attribute_name, stretch_on_off, 'blender')

    def _create_offset_attributes(self, stretch_offsets):
        for i in range(len(stretch_offsets)):
            attr_name = 'stretech_{}'.format(i + 1)
            dcc.add_double_attribute(
                self._attribute_node, attr_name, min_value=0.1, default_value=self._scale_offset,
                keyable=bool(self._per_joint_stretch))
            dcc.connect_attribute(self._attribute_node, attr_name, stretch_offsets[i], 'offset{}'.format(i + 1))

    def _add_joint(self, jnt):
        index = len(self._stretch_offsets) + 1
        var_offset = 'offset{}'.format(index)
        var_stretch = 'stretch_{}'.format(index)
        multiply = attr_utils.connect_multiply(
            '{}.outputX'.format(self._divide_distance), '{}.scale{}'.format(jnt, self._scale_axis), 1)
        dcc.add_double_attribute(multiply, var_offset, min_value=0.1, default_value=1)
        dcc.connect_attribute(multiply, var_offset, multiply, 'input2X')
        dcc.connect_attribute(multiply, var_offset, self._plus_total_offset, 'input1D[{}]'.format(index))
        dcc.add_double_attribute(
            self._attribute_node, var_stretch, min_value=0.1, default_value=1, keyable=bool(self._per_joint_stretch))
        dcc.connect_attribute(self._attribute_node, var_stretch, multiply, 'offset{}'.format(index))
        child_joints = dcc.node_joints(jnt)
        if child_joints:
            dst = dcc.distance_between_nodes(jnt, child_joints[0])
            length = dcc.get_attribute_value(self._orig_distance, 'input1X')
            length += dst
            dcc.set_float_attribute_value(self._orig_distance, 'input1X', length)

    def _create_damp(self, distance_offset, plugs):
        min_length = dcc.distance_between_nodes(self._joints[0], self._joints[-1])
        dcc.add_double_attribute(self._attribute_node, self._damp_name, min_value=0, max_value=1)
        remap = dcc.create_node(
            node_name='{}_remapValue_{}'.format(self._damp_name, self._name), node_type='remapValue')
        dcc.set_float_attribute_value(remap, 'value[2].value_Position', 0.4)
        dcc.set_float_attribute_value(remap, 'value[2].value_FloatValue', 0.666)
        dcc.set_float_attribute_value(remap, 'value[2].value_Interp', 3)
        dcc.set_float_attribute_value(remap, 'value[3].value_Position', 0.7)
        dcc.set_float_attribute_value(remap, 'value[3].value_FloatValue', 0.9166)
        dcc.set_float_attribute_value(remap, 'value[3].value_Interp', 1)
        multi = dcc.create_node(
            node_name='{}_offset_{}'.format(self._damp_name, self._name), node_type='multiplyDivide')
        add_double = dcc.create_node(
            node_name='{}_addDouble_{}'.format(self._damp_name, self._name), node_type='addDoubleLinear')
        dcc.connect_attribute(self._orig_distance, 'outputX', multi, 'input1X')
        dcc.connect_attribute(self._attribute_node, self._damp_name, multi, 'input2X')
        dcc.connect_attribute(multi, 'outputX', add_double, 'input1')
        dcc.connect_attribute(self._orig_distance, 'outputX', add_double, 'input2')
        dcc.connect_attribute(add_double, 'output', remap, 'inputMax')
        dcc.connect_attribute(self._orig_distance, 'outputX', remap, 'outputMax')
        dcc.set_float_attribute_value(remap, 'inputMin', min_length)
        dcc.set_float_attribute_value(remap, 'outputMin', min_length)
        dcc.connect_attribute(distance_offset, 'outputX', remap, 'inputValue')
        for plug in plugs:
            node_short_name = dcc.node_short_name(plug)
            node_attr_name = dcc.node_attribute_name(plug)
            dcc.connect_attribute(remap, 'outValue', node_short_name, node_attr_name)

    def _create_other_distance_offset(self, distance_offset):
        multiply = attr_utils.MultiplyDivideNode('distanceOffset_{}'.format(self._name))
        plug = '{}.input2X'.format(distance_offset)
        input_to_plug = dcc.get_attribute_input(plug)
        multiply.input1X_in(input_to_plug)
        multiply.input2X_in(self._distance_offset_attribute)
        multiply.outputX_out(plug)


class StretchyElbowLock(object):
    def __init__(self, three_joints, three_controls):
        """
        Creates an elbow lock stretchy on the given three joints
        :param three_joints: list(str), three joints
        :param three_controls: list(str), controls that transforms the correspond joint in IK setup
        """

        self._joints = three_joints
        self._controls = three_controls
        self._parent = None
        self._axis_letter = 'X'
        self._attribute_contrtol = three_controls[-1]
        self._lock_attribute_control = three_controls[1]
        self._description = 'rig'
        self._use_translate = False
        self._value = 0
        self._distance_full = None
        self._top_aim_transform = None
        self._top_locator = None
        self._bottom_locator = None
        self._stretch_locators = None
        self._soft_locator = None
        self._do_create_soft_ik = False
        self._duplicated_joints = None

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    @property
    def soft_locator(self):
        return self._soft_locator

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_stretch_axis(self, axis_letter):
        self._axis_letter = axis_letter.upper()

    def set_lock_attribute_control(self, control_name):
        self._lock_attribute_control = control_name

    def set_attribute_control(self, control_name):
        self._attribute_contrtol = control_name

    def set_description(self, description):
        self._description = description

    def set_use_translate_for_stretch(self, flag):
        self._use_translate = flag

    def set_use_this_overall_distance_node(self, distance_node):
        self._distance_full = distance_node

    def set_default_value(self, value):
        self._value = value

    def set_top_aimn_transform(self, transform):
        self._top_aim_transform = transform

    def set_parent(self, transform):
        self._parent = transform

    def set_create_soft_ik(self, flag):
        self._do_create_soft_ik = flag

    def create(self):
        self._build_locators()

        attribute_control = self._attribute_contrtol
        if not attribute_control:
            attribute_control = self._controls[-1]
        lock_control = self._lock_attribute_control

        self._add_attribute(lock_control, 'lock')
        dcc.set_minimum_integer_attribute_value(lock_control, 'lock', 0)
        dcc.set_maximum_integer_attribute_value(lock_control, 'lock', 1)
        self._add_attribute(attribute_control, 'stretch', default=self._value)
        dcc.set_minimum_integer_attribute_value(attribute_control, 'stretch', 0)
        dcc.set_maximum_integer_attribute_value(attribute_control, 'stretch', 1)
        self._add_attribute(attribute_control, 'nudge')

        self._duplicate_joints()

        dst_a = self._create_distance(self._duplicated_joints[0], self._duplicated_joints[1])
        dst_b = self._create_distance(self._duplicated_joints[1], self._duplicated_joints[2])
        default_dst_double_linear = self._connect_double_linear(
            '{}.distance'.format(dst_a), '{}.distance'.format(dst_b))
        dst_a = self._rename(dst_a, 'defaultTop')
        dst_b = self._rename(dst_b, 'defaultBtm')

        if self._distance_full:
            distance_full = self._distance_full
        else:
            distance_full = self._create_distance(self._top_locator, self._bottom_locator)
        distance_top = self._create_distance(self._controls[0], self._controls[1])
        distance_bottom = self._create_distance(self._controls[1], self._controls[-1])
        distance_full = self._rename(distance_full, 'full')
        distance_top = self._rename(distance_top, 'top')
        distance_bottom = self._rename(distance_bottom, 'btm')
        mult = self._multiply_divide(
            '{}.distance'.format(distance_full), '{}.output'.format(default_dst_double_linear))
        dcc.set_integer_attribute_value(mult, 'operation', 2)
        mult = self._rename(mult, 'stretch')
        condition = self._condition(
            '{}.outputX'.format(mult),
            '{}.distance'.format(distance_full), '{}.output'.format(default_dst_double_linear))

        blend_two_stretch = dcc.create_node(node_type='blendTwoAttr')
        blend_two_stretch = self._rename(blend_two_stretch, 'stretch')
        dcc.set_integer_attribute_value(blend_two_stretch, 'input[0]', 1)
        dcc.connect_attribute(condition, 'outColorR', blend_two_stretch, 'input[1]')
        dcc.connect_attribute(attribute_control, 'stretch', blend_two_stretch, 'attributesBlender')

        nudge_offset = dcc.create_node('multDoubleLinear')
        nudge_offset = self._rename(nudge_offset, 'nudgeOffset')
        dcc.connect_attribute(attribute_control, 'nudge', nudge_offset, 'input1')
        dcc.set_float_attribute_value(nudge_offset, 'input2', 0.001)
        nudge_double_linear = self._connect_double_linear(
            '{}.output'.format(blend_two_stretch), '{}.output'.format(nudge_offset))
        nudge_double_linear = self._rename(nudge_double_linear, 'nudge')

        mult_lock = self._multiply_divide('{}.distance'.format(distance_top), '{}.distance'.format(dst_a))
        mult_lock = self._rename(mult_lock, 'lock')
        dcc.set_integer_attribute_value(mult_lock, 'operation', 2)
        dcc.connect_attribute(distance_bottom, 'distance', mult_lock, 'input1Y')
        dcc.connect_attribute(distance_bottom, 'distance', mult_lock, 'input2Y')
        top_lock_blend = self._blend_two_attr('{}.output'.format(nudge_double_linear), '{}.outputX'.format(mult_lock))
        top_lock_blend = self._rename(top_lock_blend, 'lockTop')
        dcc.connect_attribute(lock_control, 'lock', top_lock_blend, 'attributesBlender')
        btm_lock_blend = self._blend_two_attr('{}.output'.format(nudge_double_linear), '{}.outputY'.format(mult_lock))
        btm_lock_blend = self._rename(btm_lock_blend, 'lockBtm')
        dcc.connect_attribute(lock_control, 'lock', btm_lock_blend, 'attributesBlender')

        top_mult = dcc.create_node('multDoubleLinear')
        top_mult = self._rename(top_mult, 'top')
        dcc.connect_attribute(top_lock_blend, 'output', top_mult, 'input2')

        if self._use_translate:
            dcc.set_float_attribute_value(
                top_mult, 'input1',
                dcc.get_attribute_value(self._joints[1], 'translate{}'.format(self._axis_letter)))
            dcc.connect_attribute(top_mult, 'output', self._joints[1], 'translate{}'.format(self._axis_letter))
        else:
            dcc.set_integer_attribute_value(top_mult, 'input1', 1)
            dcc.connect_attribute(top_mult, 'output', self._joints[0], 'scale{}'.format(self._axis_letter))

        bottom_mult = dcc.create_node('multDoubleLinear')
        bottom_mult = self._rename(bottom_mult, 'btm')
        dcc.connect_attribute(btm_lock_blend, 'output', bottom_mult, 'input2')

        if self._use_translate:
            dcc.set_float_attribute_value(
                bottom_mult, 'input1',
                dcc.get_attribute_value(self._joints[2], 'translate{}'.format(self._axis_letter)))
            dcc.connect_attribute(bottom_mult, 'output', self._joints[2], 'translate{}'.format(self._axis_letter))
        else:
            dcc.set_integer_attribute_value(bottom_mult, 'input1', 1)
            dcc.connect_attribute(bottom_mult, 'output', self._joints[1], 'scale{}'.format(self._axis_letter))

        if self._do_create_soft_ik:
            soft = SoftIk(self._joints)
            soft.set_attribute_control(self._attribute_contrtol)
            soft.set_control_distance_attribute('{}.distance'.format(distance_full))
            soft.set_default_distance_attribute('{}.output'.format(default_dst_double_linear))
            soft.set_description(self._description)
            soft.set_top_aim_transform(self._top_aim_transform)
            soft.set_bottom_control(self._controls[-1])
            soft.set_ik_locator_parent(self._parent)
            self._soft_locator = soft.create()

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _build_locators(self):
        self._top_locator = dcc.create_locator(name='distanceLocator_top_{}'.format(self._description))
        self._bottom_locator = dcc.create_locator(name='distanceLocator_bottom_{}'.format(self._description))
        dcc.set_parent(self._top_locator, self._controls[0])
        dcc.zero_transform_attribute_channels(self._top_locator)
        dcc.set_parent(self._bottom_locator, self._controls[-1])
        dcc.zero_transform_attribute_channels(self._bottom_locator)
        dcc.hide_node(self._top_locator)
        dcc.hide_node(self._bottom_locator)
        self._stretch_locators = [self._top_locator, self._bottom_locator]

    def _add_attribute(self, node, attribute_name, default=0):
        dcc.add_title_attribute(node, 'STRETCH')
        dcc.add_integer_attribute(node, attribute_name, default_value=default, keyable=True)

    def _duplicate_joints(self):
        duplicates = dcc.duplicate_hierarchy(self._joints[0], force_only_these=self._joints)
        found = list()
        for dup, orig in zip(duplicates, self._joints):
            new = dcc.rename_node(dup, 'default_{}'.format(orig))
            found.append(new)

        dcc.hide_node(found[0])

        self._duplicated_joints = found

    def _create_distance(self, transform_a, transform_b):
        distance_node = dcc.create_node(node_type='distanceBetween')
        dcc.connect_attribute(transform_a, 'worldMatrix', distance_node, 'inMatrix1')
        dcc.connect_attribute(transform_b, 'worldMatrix', distance_node, 'inMatrix2')

        return distance_node

    def _connect_double_linear(self, attr_a, attr_b, input_attr=None):
        add_double_linear = dcc.create_node('addDoubleLinear')
        maya.cmds.connectAttr(attr_a, '{}.input1'.format(add_double_linear))
        maya.cmds.connectAttr(attr_b, '{}.input2'.format(add_double_linear))
        if input_attr:
            maya.cmds.connectAttr('{}.output'.format(add_double_linear), input_attr)

        return add_double_linear

    def _rename(self, old_name, new_name):
        return maya.cmds.rename(
            old_name,
            dcc.find_unique_name('{}_{}_{}'.format(dcc.node_type(old_name), new_name, self._description)))

    def _multiply_divide(self, attr_a, attr_b, input_attr=None):
        mult = dcc.create_node('multiplyDivide')
        maya.cmds.connectAttr(attr_a, '{}.input1X'.format(mult))
        maya.cmds.connectAttr(attr_b, '{}.input2X'.format(mult))
        if input_attr:
            maya.cmds.connectAttr('{}.outputX'.format(mult), input_attr)

        return mult

    def _condition(self, color_if_true_attr, first_term_attr, second_term_attr):
        condition = dcc.create_node('condition')
        maya.cmds.connectAttr(color_if_true_attr, '{}.colorIfTrueR'.format(condition))
        maya.cmds.connectAttr(first_term_attr, '{}.firstTerm'.format(condition))
        maya.cmds.connectAttr(second_term_attr, '{}.secondTerm'.format(condition))

        return condition

    def _blend_two_attr(self, attr_a, attr_b, input_attr=None):
        blend_two = dcc.create_node('blendTwoAttr')
        maya.cmds.connectAttr(attr_a, '{}.input[0]'.format(blend_two))
        maya.cmds.connectAttr(attr_b, '{}.input[1]'.format(blend_two))
        if input_attr:
            maya.cmds.connectAttr('{}.output'.format(blend_two), input_attr)

        return blend_two


class SoftIk(object):
    def __init__(self, joints):
        self._joints = joints
        self._description = None
        self._attribute_control = None
        self._default_distance_attribute = None
        self._control_distance_attribute = None
        self._top_aim_attribute = None
        self._top_aim_transform = None
        self._ik_locator_parent = None
        self._bottom_control = None
        self._attribute_name = 'softBuffer'
        self._nice_attribute_name = 'soft'

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_description(self, description):
        self._description = description

    def set_attribute_control(self, control_name, attribute_name=None):
        self._attribute_contrtol = control_name
        if attribute_name:
            self._nice_attribute_name = attribute_name

    def set_control_distance_attribute(self, control_distance_attribute):
        self._control_distance_attribute = control_distance_attribute

    def set_default_distance_attribute(self, default_distance_attribute):
        self._default_distance_attribute = default_distance_attribute

    def set_top_aim_transform(self, transform):
        self._top_aim_transform = transform

    def set_ik_locator_parent(self, transform):
        self._ik_locator_parent = transform

    def set_bottom_control(self, control_name):
        self._bottom_control = control_name

    def create(self):
        locator = self._build_soft_graph()

        return locator

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _rename(self, old_name, new_name):
        return dcc.rename_Node(old_name, dcc.find_unique_name(
            '{}_{}_{}'.format(dcc.nodetype(old_name), new_name, self._description)))

    def _add_attribute(self, node, attribute_name, default=0):
        dcc.add_integer_attribute(node, attribute_name, default_value=default, keyable=True)

        return '{}.{}'.format(node, attribute_name)

    def _create_attributes(self, soft_buffer_node):
        attr = self._add_attribute(soft_buffer_node, self._attribute_name)
        nice_attr = self._add_attribute(self._attribute_contrtol, self._nice_attribute_name, 0)
        anim_utils.quick_driven_key(nice_attr, attr, [0, 1], [0.001, 1], infinite=True)
        dcc.unkeyable_attribute(soft_buffer_node, self._attribute_name)
        dcc.set_minimum_integer_attribute_value(self._attribute_contrtol, self._nice_attribute_name, 0)
        dcc.set_maximum_integer_attribute_value(self._attribute_contrtol, self._nice_attribute_name, 2)

    def _build_soft_graph(self):
        chain_distance = jnt_utils.get_joints_chain_length(self._joints)
        subtract_soft = self._rename(dcc.create_node('plusMinusAverage'), 'subtractSoft')
        self._create_attributes(subtract_soft)
        soft_attr = '{}.{}'.format(subtract_soft, self._attribute_name)
        dcc.set_integer_attribute_value(subtract_soft, 'operation', 2)
        if not self._default_distance_attribute:
            dcc.set_float_attribute_value(subtract_soft, 'input1D[0]', chain_distance)
        else:
            maya.cmds.connectAttr(self._default_distance_attribute, '{}.input1D[0]'.format(subtract_soft))
        subtract_soft_total = self._rename(maya.cmds.createNode('plusMinusAverage'), 'subtractSoftTotal')
        maya.cmds.setAttr('{}.operation'.format(subtract_soft_total), 2)
        maya.cmds.connectAttr(self._control_distance_attribute, '{}.input1D[0]'.format(subtract_soft_total))
        dcc.connect_attribute(subtract_soft, 'output1D', subtract_soft_total, 'input1D[1]')
        divide_soft = self._rename(maya.cmds.createNode('multiplyDivide'), 'divideSoft')
        dcc.set_integer_attribute_value(divide_soft, 'operation', 2)
        dcc.connect_attribute(subtract_soft_total, 'output1D', divide_soft, 'input1X')
        maya.cmds.connectAttr(soft_attr, '{}.input2X'.format(divide_soft))
        negate = self._rename(dcc.create_node('multiplyDivide'), 'negateSoft')
        dcc.set_integer_attribute_value(negate, 'input1X', -1)
        dcc.connectAttr(divide_soft, 'outputX', 'input2X', negate)
        power_soft = self._rename(dcc.create_node('multiplyDivide'), 'powerSoft')
        exp_value = math.exp(1)
        dcc.set_integer_attribute_value(power_soft, 'operation', 3)
        dcc.set_float_attribute_value(power_soft, 'input1X', exp_value)
        dcc.connect_attribute(negate, 'outputX', power_soft, 'input2X')
        power_mult_soft = self._rename(dcc.create_node('multiplyDivide'), 'powerMultSoft')
        maya.cmds.connectAttr(soft_attr, '{}.input1X'.format(power_mult_soft))
        dcc.connect_attribute(power_soft, 'outputX', power_mult_soft, 'input2X')
        subtract_end_soft = self._rename(dcc.create_node('plusMinusAverage'), 'subtractEndSoft')
        dcc.set_integer_attribute_value(subtract_end_soft, 'operation', 2)
        if not self._default_distance_attribute:
            dcc.set_float_attribute_value(subtract_end_soft, 'input1D[0]', chain_distance)
        else:
            maya.cmds.connectAttr(self._default_distance_attribute, '{}.input1D[0]'.format(subtract_end_soft))
        dcc.connect_attribute(power_mult_soft, 'outputX', subtract_end_soft, 'input1D[1]')
        inside_condition = self._rename(dcc.create_node('condition'), 'insideSoft')
        maya.cmds.connectAttr(self._control_distance_attribute, '{}.firstTerm'.format(inside_condition))
        dcc.connect_attribute(subtract_soft, 'output1D', inside_condition, 'secondTerm')
        dcc.set_integer_attribute_value(inside_condition, 'operation', 2)
        dcc.connect_attribute(subtract_end_soft, 'output1D', inside_condition, 'colorIfTrueR')
        maya.cmds.connectAttr(self._control_distance_attribute, '{}.colorIfFalseR'.format(inside_condition))

        locator = dcc.create_locator(name='locator_{}'.format(self._description))
        dcc.match_translation_rotation(self._joints[-1], locator)
        if self._ik_locator_parent:
            dcc.set_parent(locator, self._ik_locator_parent)
        if self._top_aim_transform:
            follow = space_utils.create_follow_group(self._top_aim_transform, locator)
            transform_utils.zero_transform_channels(locator)
            dcc.set_node_inherits_transform(follow, False)
        dcc.connect_attribute(inside_condition, 'outColorR', locator, 'translateX')
        if self._bottom_control:
            new_grp = dcc.create_empty_group(name='softOnOff_{}'.format(self._description))
            cns = dcc.create_point_constraint(new_grp, self._bottom_control)
            cns_edit = cns_utils.Constraint()
            cns_edit.create_switch(self._attribute_contrtol, 'stretch', constraint=cns)
            locator = new_grp

        return locator


class RiggedLine(object):
    """
    Creates a line rig that connects two transforms
    Useful when creating pole vector setups
    """

    def __init__(self, top_transform, bottom_transform, name):
        self._name = name
        self._top = top_transform
        self._bottom = bottom_transform
        self._local = False
        self._extra_joint = None
        self._top_group = None
        self._curve = None
        self._cluster1 = None
        self._cluster2 = None

    def create(self):
        """
        Creates rig line setup
        :return: str, name of the top group that contains rig line setup
        """

        self._create_top_group()
        self._create_curve()
        self._create_clusters()
        self._match_clusters()
        self._constrain_clusters()

        return self._top_group

    def set_local(self, flag):
        """
        Sets whether or not rig line setup should be remain local to the origin or not
        :param flag:
        :return:
        """

        self._local = flag

    def _create_top_group(self):
        """
        Internal function that creates group for top transform
        """

        self._top_group = maya.cmds.group(empty=True, n='guideLineGroup_{}'.format(self._name))
        maya.cmds.setAttr('{}.inheritsTransform'.format(self._top_group), 0)

    def _create_curve(self):
        """
        Internal function that creates curve that connects both transforms
        """

        self._curve = maya.cmds.curve(
            d=1, p=[(0, 0, 0), (0, 0, 0)], k=[0, 1], n=dcc.find_unique_name('guideLine_%s' % self._name))
        maya.cmds.delete(self._curve, ch=True)
        shapes = shape_utils.get_shapes(self._curve)
        maya.cmds.rename(shapes[0], '{}Shape'.format(self._curve))
        maya.cmds.setAttr('{}.template'.format(self._curve), True)
        maya.cmds.parent(self._curve, self._top_group)

    def _create_cluster(self, curve, cv):
        """
        Internal function that creates a new cluster in the given curve and in given curve CV
        :param curve: str
        :param cv: int
        :return: list(str, str), cluster node and cluster transform
        """

        cluster, transform = maya.cmds.cluster('{}.cv[{}]'.format(self._curve, cv))
        transform = maya.cmds.rename(
            transform, dcc.find_unique_name('{}_cv{}_guideLineCluster'.format(self._name, cv)))
        cluster = maya.cmds.rename(
            '{}Cluster'.format(transform), dcc.find_unique_name('{}_cv{}_clusterGuideLine'.format(self._name, cv)))
        maya.cmds.hide(transform)
        maya.cmds.parent(transform, self._top_group)

        return [cluster, transform]

    def _create_clusters(self):
        """
        Internal function that creates all clusters used by the rig line setup
        """

        self._cluster1 = self._create_cluster(self._curve, 0)
        self._cluster2 = self._create_cluster(self._curve, 1)

    def _match_clusters(self):
        """
        Internal function that match cluster positions with the positions of the rig line controls
        """

        dcc.match_translation_to_rotate_pivot(self._top, self._cluster1[1])
        dcc.match_translation_to_rotate_pivot(self._bottom, self._cluster2[1])

    def _constrain_clusters(self):
        """
        Internal function that constraints controls to the clusters
        """

        if self._local:
            offset1 = maya.cmds.group(empty=True, n='buffer_{}'.format(self._cluster1[1]))
            offset2 = maya.cmds.group(empty=True, n='buffer_{}'.format(self._cluster2[1]))
            maya.cmds.parent(offset1, offset2, self._top_group)
            maya.cmds.parent(self._cluster1[1], offset1)
            maya.cmds.parent(self._cluster2[1], offset2)
            dcc.match_translation(self._top, offset1)
            dcc.match_translation(self._bottom, offset2)
            cns_utils.constraint_local(self._top, offset1)
            cns_utils.constraint_local(self._bottom, offset2)
        else:
            maya.cmds.pointConstraint(self._top, self._cluster1[1])
            maya.cmds.pointConstraint(self._bottom, self._cluster2[1])


class TwistRibbon(object):
    """
    Creates twist ribon setup
    """

    def __init__(self, joint, end_transform=None):
        super(TwistRibbon, self).__init__()

        self._joint = joint
        self._end_transform = end_transform
        self._joints = list()                               # List of joints twist rig will affect
        self._rivets = list()                               # List of rivets generated by twist ribbon rig setup
        self._joints_count = 5                              # Total amount of joint that will be generated
        self._control_transforms = list()                   # List of controls generated by twist ribbon rig setup
        self._description = 'section'                       # Description used by twist ribbon rig setup
        self._ribbon_offset_axis = 'Y'                             # Ribbon surface offset axis
        self._ribbon_offset_amount = 1                             # Ribbon surface offset amount
        self._dual_quaternion = False                       # Sets whether or not twist setup will use dual quaternion
        self._attach_directly = False
        self._top_locator = None                            # Top locator for the twist ribbon rig setup
        self._bottom_locator = None                         # Bottom locator for the twist ribbon rig setup
        self._group = None
        self._surface = None
        self._rivets_group = None                           # Group whtere created rivets will be parented into
        self._top_parent = None
        self._bottom_parent = None
        self._top_constraint = None
        self._top_constraint_type = None
        self._bottom_constraint = None
        self._bottom_constraint_type = None
        self._top_twist_fix = False
        self._bottom_twist_fix = False
        self._top_ik = None
        self._bottom_ik = None
        self._top_joint = None
        self._bottom_joint = None

    # ==============================================================================================
    # PROPERTIES
    # ==============================================================================================

    @property
    def surface(self):
        return self._surface

    @property
    def group(self):
        return self._group

    @property
    def joints(self):
        return self._joints

    @property
    def top_locator(self):
        return self._top_locator

    @property
    def bottom_locator(self):
        return self._bottom_locator

    @property
    def top_ik(self):
        return self._top_ik

    @property
    def bottom_ik(self):
        return self._bottom_ik

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def create(self):

        self._control_transforms = list()

        top_locator = dcc.create_locator(
            dcc.find_unique_name('locator_twistRibbonTop_{}'.format(self._description)))
        bottom_locator = dcc.create_locator(
            dcc.find_unique_name('locator_twistRibbonBottom_{}'.format(self._description)))

        if not self._end_transform:
            children = dcc.list_children(self._joint, children_type='joint')
            if not children:
                logger.warning(
                    'No child found for {}. Could not create twist ribbon rig setup.'.format(self._joint))
                return []
            temp_group = children[0]
        else:
            temp_group = self._end_transform

        self._group = dcc.create_empty_group(dcc.find_unique_name('twistRibbon_{}'.format(self._description)))

        self._surface = geo_utils.transforms_to_nurbs_surface(
            [self._joint, temp_group], name=self._description,
            offset_axis=self._ribbon_offset_axis, offset_amount=self._ribbon_offset_amount)

        if self._dual_quaternion:
            maya.cmds.rebuildSurface(
                self._surface, constructionHistory=False, replaceOriginal=True, rebuildType=0, endKnots=1, keepRange=0,
                keepControlPoints=0, keepCorners=0, spansU=1, degreeU=1, spansV=2, degreeV=3, tolerance=0.01,
                fitRebuild=0, direction=2)

        dcc.set_parent(self._surface, self._group)
        if not self._joints:
            self._joints = geo_utils.nurbs_surface_u_to_transforms(
                self._surface, self._description, count=self._joint_count)

        self._rivets_group = dcc.create_empty_group(
            dcc.find_unique_name('twistRibbon_rivets_{}'.format(self._description)))
        dcc.set_parent(self._rivets_group, self._group)

        for joint in self._joints:
            maya.cmds.delete(maya.cmds.orientConstraint(self._joint, joint))
            maya.cmds.makeIdentity(joint, apply=True, r=True)
            rivet = rivet_utils.attach_to_surface(joint, self._surface, constraint=self._attach_directly)
            relatives = dcc.list_relatives(rivet, relative_type='transform')
            if relatives:
                self._control_transforms.apepnd(relatives[1])
            shapes = shape_utils.get_shapes(rivet)
            dcc.hide_node(shapes)
            dcc.set_parent(rivet, self._rivets_group)
            self._rivets.append(rivet)

        skin_surface = skin_utils.SkinJointSurface(self._surface, self._description)
        skin_surface.set_joint_u(True)
        skin_surface.create()
        skin = skin_surface.get_skin()

        joints = skin_surface.get_joints_list()
        if self._dual_quaternion:
            dcc.delete_node(joints[1:-1])
            joints = [joints[0], joints[-1]]
        else:
            maya.cmds.setAttr('{}.skinningMethod'.format(skin), 0)

        self._top_locator = top_locator
        self._bottom_locator = bottom_locator
        self._top_joint = joints[0]
        self._bottom_joint = joints[1]

        dcc.match_translation_to_rotate_pivot(joints[0], top_locator)
        dcc.match_translation_to_rotate_pivot(joints[-1], bottom_locator)
        dcc.set_parent(joints[0], top_locator)
        dcc.set_parent(joints[-1], bottom_locator)

        maya.cmds.skinPercent(skin, self._surface, normalize=True)
        dcc.hide_node(joints)

        if self._top_parent and dcc.node_exists(self._top_parent):
            dcc.set_parent(self._top_locator, self._top_parent)
        if self._bottom_parent and dcc.node_exists(self._bottom_parent):
            dcc.set_parent(self._bottom_locator, self._bottom_parent)

        if self._top_constraint and dcc.node_exists(self._top_constraint):
            eval('cmds.{}({}, {}, mo=True)'.format(self._top_constraint_type, self._top_constraint, top_locator))
        if self._bottom_constraint and dcc.node_exists(self._bottom_constraint):
            eval('cmds.{}({}, {}, mo=True)'.format(
                self._bottom_constraint_type, self._bottom_constraint, bottom_locator))

        if self._top_twist_fix:
            self._create_top_twister_joint()
        if self._bottom_twist_fix:
            self._create_bottom_twister_joint()

        return [top_locator, bottom_locator]

    def set_description(self, description):
        """
        Sets the description name used by the twist ribbon rig setup
        :param description: str
        """

        self._description = str(description)

    def set_joints(self, joints_list):
        """
        Sets the list of joints twist ribbon rig setup will affect
        :param joints_list: list(str)
        """

        self._joints = joints_list

    def set_joints_count(self, value):
        """
        Set the total amount of joints that twist ribbon rig setup will create
        :param value: int
        """

        self._joints_count = int(value)

    def set_ribbon_offset_axis(self, axis_letter):
        """
        Sets the axis ('X', 'Y', 'Z') that will be used to offset the ribbon surface
        :param axis_letter: str
        """

        self._ribbon_offset_axis = axis_letter

    def set_ribbon_offset_amount(self, value):
        """
        Sets the offset amount that will be used to displace ribbon surface
        :param value: float
        """

        self._ribbon_offset_amount = value

    def set_dual_quaternion(self, flag, enable_twist_fix=True):
        """
        Sets whether or not dual quaternion will be used by twist ribbon rig setup
        :param flag: bool
        :param enable_twist_fix: bool
        """

        self._dual_quaternion = flag
        if enable_twist_fix:
            self._top_twist_fix = True
            self._bottom_twist_fix = True

    def set_attach_directly(self, flag):
        self._attach_directly = flag

    def set_top_parent(self, transform):
        self._top_parent = transform

    def set_bottom_parent(self, transform):
        self._bottom_parent = transform

    def set_top_constraint(self, transform, constraint_type='parentConstraint'):
        self._top_constraint = transform
        self._top_constraint_type = constraint_type

    def set_bottom_constraint(self, transform, constraint_type='parentConstraint'):
        self._bottom_constraint = transform
        self._bottom_constraint_type = constraint_type

    def set_top_twist_fix(self, flag):
        self._top_twist_fix = flag

    def set_bottom_twist_fix(self, flag):
        self._bottom_twist_fix = flag

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _create_top_twister_joint(self):
        joint1, joint2, ik = ik_utils.create_ik_chain(
            self._bottom_locator, self._top_locator, 'twist_topFix_{}'.format(
                self._description), ik_utils.IkHandle.SOLVER_RP)
        maya.cmds.hide(joint1, joint2)
        self._top_ik = ik
        xform = dcc.create_buffer_group(joint1)
        dcc.set_parent(xform, self._top_locator)
        dcc.set_parent(ik, self._bottom_locator)
        maya.cmds.hide(joint1, ik)

    def _create_bottom_twister_joint(self):
        joint1, joint2, ik = ik_utils.create_ik_chain(
            self._bottom_locator, self._top_locator, 'twist_bottomFix_{}'.format(
                self._description), ik_utils.IkHandle.SOLVER_RP)
        maya.cmds.hide(joint1, joint2)
        self._bottom_ik = ik
        xform = dcc.create_buffer_group(joint1)
        dcc.set_parent(xform, self._bottom_locator)
        dcc.set_parent(ik, self._top_locator)
        maya.cmds.hide(joint1, ik)


def parent_shape_in_place(transform, shape_source, keep_source=True, replace_shapes=False, snap_first=False):
    """
    Parents a curve shape in place into a the transform of a given node
    :param transform: str, object to we want to parent shape into
    :param shape_source: str, curve shape to parent
    :param keep_source: bool, Whether to keep the curve shape parented also
    :param replace_shapes: bool, Whether to remove the objects original shapes or not
    :param snap_first: bool, Whether to snap shape to transform before parenting
    :return: bool, Whether the operation was successful or not
    """

    # TODO: Finish

    shape_source = helpers.force_list(shape_source)

    for shape in shape_source:
        maya.cmds.parent(shape, transform, add=True, shape=True)


def create_follow_fade(source_guide, drivers, skip_lower=0.0001):
    """
    Creates a multiply divide for each transform in drivers with a weight value based on the distance from source guide
    :param source_guide: str, name of a transform in maya to calculate distance from
    :param drivers: list(str), list of drivers to apply fade based in the distance from source guide
    :param skip_lower: float, distance below which multiplyDivide no fading stops
    :return: list(str), list of multiplyDivide nodes created
    """

    distance_list, distance_dict, original_distance_order = transform_utils.get_ordered_distance_and_transform(
        source_guide, drivers)
    multiplies = list()

    if not distance_list[-1] > 0:
        return multiplies

    for dst in original_distance_order:
        scaler = 1.0 - (dst / distance_list[-1])
        if scaler <= skip_lower:
            continue
        multi = attr_utils.MultiplyDivideNode(source_guide)
        multi.set_input2(scaler, scaler, scaler)
        multi.input1X_in('{}.translateX'.format(source_guide))
        multi.input1Y_in('{}.translateY'.format(source_guide))
        multi.input1Z_in('{}.translateZ'.format(source_guide))

        for driver in distance_dict[dst]:
            multi.outputX_out('{}.translateX'.format(driver))
            multi.outputY_out('{}.translateY'.format(driver))
            multi.outputZ_out('{}.translateZ'.format(driver))

        multi_dict = dict()
        multi_dict['node'] = multi
        multi_dict['source'] = source_guide
        multi_dict['target'] = driver           # ???
        multiplies.append(multi_dict)

    return multiplies
