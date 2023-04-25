#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with attributes
"""

import maya.cmds

from tp.core import dcc
from tp.common.python import helpers
from tp.maya.om import mathlib
from tp.maya.cmds import attribute, name as name_utils, transform as transform_utils, shape as shape_utils


class Constraints(object):
    PARENT = 'parentConstraint'
    POINT = 'pointConstraint'
    ORIENT = 'orientConstraint'
    SCALE = 'scaleConstraint'
    AIM = 'aimConstraint'


class Constraint(object):
    """
    Class that wraps constraint functionality
    """

    EDITABLE_CONSTRAINTS = [
        Constraints.PARENT, Constraints.POINT, Constraints.ORIENT, Constraints.SCALE, Constraints.AIM
    ]

    def __init__(self):
        self._set_to_last = False
        self._remaps = list()

    @property
    def remaps(self):
        return self._remaps

    def get_constraint(self, xform, constraint_type):
        """
        Find a constraint on the transform with the given type
        :param xform: str, name ofa transform node that is constrained
        :param constraint_type: str, type of constraint to search for
        :return: str, name of the constraint
        """

        return eval('maya.cmds.{}("{}", query=True)'.format(constraint_type, xform))

    def get_transform(self, constraint):
        """
        Returns the transform that the constraint is currently constraining
        :param constraint: str, name of the constraint
        :return: variant, str || None, name of the transform that is being constrained if exists; None otherwise
        """

        xform = attribute.attribute_input('{}.constraintParentInverseMatrix'.format(constraint))
        if not xform:
            return None

        cns = xform.split('.')

        return cns[0]

    def has_constraint(self, xform):
        """
        Returns whether given transform node is being affected by a constraint or not
        :param xform: str, name of a transform node
        :return: bool
        """

        for cns in self.EDITABLE_CONSTRAINTS:
            const = self.get_constraint(xform, cns)
            if const:
                return True

        return False

    def get_weight_count(self, constraint):
        """
        Returns the number of input weights (transforms) feed in the constraint
        :param constraint: str, name of the constraint
        :return: int
        """

        return len(maya.cmds.ls('{}.target[*]'.format(constraint)))

    def get_weight_names(self, constraint):
        """
        Returns the names of the input weights (transforms) feed in the constraint
        :param constraint: str, name of the constraint
        :return: lsit<str>
        """

        cns_type = self._get_constraint_type(constraint)
        if cns_type == Constraints.SCALE:
            found_attrs = list()
            weights = maya.cmds.ls('{}.target[*]'.format(constraint))
            attrs = maya.cmds.listAttr(constraint, k=True)
            for attr in attrs:
                for i in range(len(weights)):
                    if attr.endswith('W{}'.format(i)):
                        found_attrs.append(attr)
                        break

            return found_attrs

        return eval('maya.cmds.{}("{}", query=True, weightAliasList=True)'.format(cns_type, constraint))

    def get_targets(self, constraint):
        """
        Returns the transforms that are influencing the constraint
        :param constraint: str, the name of the constraint
        :return: list<str>, name of the transforms affecting the constraint
        """

        xform = self.get_transform(constraint)
        cns_type = self._get_constraint_type(constraint)

        return eval('maya.cmds.{}("{}", query=True, targetList=True)'.format(cns_type, xform))

    def remove_target(self, target, constraint):
        """
        Removes a target from the given constraint
        NOTE: Only works if the constraint has all its original connections intact
        :param target: str, name of the transform target to remove
        :param constraint: str, name of a constraint that has target affecting it
        :return: bool, Whether the operation was successful or not
        """

        xform = self.get_transform(constraint)
        cns_type = self._get_constraint_type(constraint)

        return eval('maya.cmds.{}("{}", "{}", remove=True)'.format(cns_type, target, xform))

    def set_interpolation(self, int_value, constraint):
        """
        Set the interpolation type of the constraint
        :param int_value: int, index of the interpolation type
        :param constraint: str, name of the constraint
        """

        maya.cmds.setAttr('{}.interpType'.format(constraint, int_value))

    def set_auto_use_last_number(self, flag):
        """
        Sets whether auto use last number is enabled or not
        :param flag: bool
        """

        self._set_to_last = flag

    def create_title(self, node, constraint, title_name='FOLLOW'):
        """
        Creates a title enum attribute based on the targets feeding into a constraint
        The enum will have the name of the transforms affecting the constraint
        :param node: str, name of the node to add the title to
        :param constraint: str, name of a constraint. Should be affected by multiple transforms
        :param title_name: str, name to give to the title attribute
        """

        targets = self.get_targets(constraint)
        names = list()
        for i, target in enumerate(targets):
            name = target
            if target.startswith('follower_'):
                parent = maya.cmds.listRelatives(target, p=True)
                if parent:
                    parent = parent[0]
                    if parent.startswith('CNT_'):
                        name = parent
            name = '{}.{}'.format(i, name)
            names.append(name)

        attribute.create_title(node, title_name, names)

    def create_switch(self, node, attr, constraint):
        """
        Creates a switch over all the target weights
        :param node: str, name of the node to add the switch attribute to
        :param attr: str, name to give the switch attribute
        :param constraint: str, name of the constraint with multiple weight target transforms affecting it
        """

        attrs = self.get_weight_names(constraint)
        remap = attribute.RemapAttributesToAttribute(node, attr)
        remap.create_attributes(constraint, attrs)
        remap.create()
        self._remaps.extend(remap.remaps)

        if self._set_to_last:
            maya.cmds.setAttr('{}.{}'.format(node, attribute), (len(attrs) - 1))

    def delete_constraints(self, xform, constraint_type=None):
        """
        Removes constraints from given node
        :param xform: str
        :param constraint_type: str
        """

        if not constraint_type:
            for cns_type in self.EDITABLE_CONSTRAINTS:
                cns = self.get_constraint(xform, cns_type)
                if cns:
                    maya.cmds.delete(cns)
        else:
            cns = self.get_constraint(xform, constraint_type)
            if cns:
                maya.cmds.delete(cns)

    def _get_constraint_type(self, constraint):
        """
        Returns the type of the given constraint node
        :param constraint: str, name of constraint node
        :return: str
        """

        return maya.cmds.nodeType(constraint)


class MatrixConstraintNodes(object):
    def __init__(self, source_transform, target_transform=None):
        self._connect_translate = True
        self._connect_rotate = True
        self._connect_scale = True
        self._source = helpers.force_list(source_transform)
        self._target = target_transform
        self._decompose = True

        if target_transform:
            self.description = target_transform
        else:
            self.description = 'Constraint'

        self._node_decompose_matrix = None
        self._joint_orient_quat_to_euler = None

    def create(self):
        """
        Creates the matrix decomnpose setup
        """

        self._create_decompose()

    def set_description(self, description):
        """
        Set the description of the node names generated
        :param description: str
        """

        self.description = description

    def set_decompose(self, flag):
        """
        Set if decompose matrix needs to be created or not
        :param flag: bool
        """

        self._decompose = flag

    def set_connect_translate(self, flag):
        """
        Set if translate needs to be connect in the matrix decompose node
        :param flag: bool
        """

        self._connect_translate = flag

    def set_connect_rotate(self, flag):
        """
        Set if rotate needs to be connect in the matrix decompose node
        :param flag: bool
        """

        self._connect_rotate = flag

    def set_connect_scale(self, flag):
        """
        Set if scale needs to be connect in the matrix decompose node
        :param flag: bool
        """

        self._connect_scale = flag

    def _create_decompose(self):
        """
        Internal function used to create decomposeMatrix nodes
        """

        if self._decompose:
            self._node_decompose_matrix = maya.cmds.createNode('decomposeMatrix', self.description)

    def _connect_decompose(self, matrix_attribute):
        """
        Internal function sued to connect decompose matrix to the target node
        :param matrix_attribute: str
        """

        maya.cmds.connectAttr(matrix_attribute, '{}.inputMatrix'.format(self._node_decompose_matrix))
        if self._connect_translate:
            maya.cmds.connectAttr(
                '{}.outputTranslate'.format(self._node_decompose_matrix), '{}.translate'.format(self._target))
        if self._connect_rotate:
            if maya.cmds.nodeType(self._target) == 'joint':
                maya.cmds.connectAttr(
                    '{}.outputTranslate'.format(self._node_decompose_matrix, '{}.jointOrient'.format(self._target)))
            else:
                maya.cmds.connectAttr(
                    '{}.outputRotate'.format(self._node_decompose_matrix), '{}.rotate'.format(self._target))
        if self._connect_scale:
            maya.cmds.connectAttr(
                '{}.outputScale'.format(self._node_decompose_matrix), '{}.scale'.format(self._target))

    def _create_joint_offset(self):
        euler_to_quat = maya.cmds.createNode('eulerToQuat', name_utils.find_unique_name(self.description))
        quat_invert = maya.cmds.createNode('quatInvert', name_utils.find_unique_name(self.description))
        quat_prod = maya.cmds.createNode('quatProd', name_utils.find_unique_name(self.description))
        self._joint_orient_quat_to_euler = maya.cmds.createNode(
            'quatToEuler', name_utils.find_unique_name(self.description))

        maya.cmds.connectAttr('{}.jointOrient'.format(self._target), '{}.inputRotate'.format(euler_to_quat))
        maya.cmds.connectAttr('{}.outputQuat'.format(euler_to_quat), '{}.inputQuat'.format(quat_invert))
        maya.cmds.connectAttr('{}.outputQuat'.format(self._node_decompose_matrix), '{}.input1Quat'.format(quat_prod))
        maya.cmds.connectAttr('{}.outputQuat'.format(quat_invert), '{}.input2Quat'.format(quat_prod))
        maya.cmds.connectAttr(
            '{}.outputQuat'.format(quat_prod), '{}.inputQuat'.format(self._joint_orient_quat_to_euler))
        maya.cmds.connectAttr(
            '{}.outputRotate'.format(self._joint_orient_quat_to_euler), '{}.rotate'.format(self._target))


class MatrixConstraint(MatrixConstraintNodes, object):
    def __init__(self, source_transform, target_transform=None):
        super(MatrixConstraint, self).__init__(source_transform, target_transform)

        self._main_source = self._source[0]
        self.node_multiply_matrix = None
        self._use_target_parent_matrix = False
        self._maintain_offset = True

    def create(self):
        super(MatrixConstraint, self).create()
        self._create_matrix_constraint()

    def set_use_target_parent_matrix(self, flag):
        self._use_target_parent_matrix = flag

    def set_maintain_offset(self, flag):
        self._maintain_offset = flag

    def _create_matrix_constraint(self):
        mult = maya.cmds.createNode('multMatrix', self.description)
        self.node_multiply_matrix = mult
        maya.cmds.aliasAttr('jointOrientMatrix', '{}.matrixIn[0]'.format(mult))

        maya.cmds.aliasAttr('offsetMatrix', '{}.matrixIn[1]'.format(mult))
        maya.cmds.aliasAttr('targetMatrix', '{}.matrixIn[2]'.format(mult))
        maya.cmds.aliasAttr('parentMatrix', '{}.matrixIn[3]'.format(mult))

        maya.cmds.connectAttr('{}.worldMatrix'.format(self._main_source), '{}.targetMatrix'.format(mult))

        if not self._target:
            return

        target_matrix = maya.cmds.getAttr('{}.worldMatrix', self._target)
        if self._maintain_offset:
            source_inverse_matrix = maya.cmds.getAttr('{}.worldInverseMatrix'.format(self._main_source))
            offset = mathlib.multiply_matrix(target_matrix, source_inverse_matrix)
            maya.cmds.setAttr('{}.offsetMatrix'.format(mult), offset, type='matrix')

        if self._use_target_parent_matrix:
            parent = maya.cmds.listRelatives(self._target, p=True)
            if parent:
                maya.cmds.connectAttr('{}.inverseMatrix'.format(parent[0]), '{}.parentMatrix'.format(mult))
        else:
            maya.cmds.connectAttr('{}.parentInverseMatrix'.format(self._target), '{}.parentMatrix'.format(mult))

        if self._node_decompose_matrix:
            self._connect_decompose('{}.matrixSum'.format(mult))


class SpaceSwitch(MatrixConstraintNodes):
    def __init__(self, sources=None, target=None):
        if sources is None:
            sources = list()
        super(SpaceSwitch, self).__init__(sources, target)

        self._node_weight_add_matrix = None
        self._node_choice = None
        self._input_attribute = None
        self._weight_attributes = list()

        self._use_weight = False
        self._switch_names = list()
        self._attribute_node = target
        self._attribute_name = 'switch'
        self._maintain_offset = True

        self._create_title = True
        self._title_name = None

    def create(self, create_switch=False):
        super(SpaceSwitch, self).create()
        switch_node = self._create_space_switch()
        if create_switch:
            self.create_switch(self._attribute_node, self._attribute_name, switch_node)

        return switch_node

    def get_space_switches(self, target):
        attrs = ['translate', 'rotate', 'scale']
        found = list()
        for attr_name in attrs:
            attr = attr_name
            node_and_attr = '{}.{}'.format(target, attr)
            input_value = attribute.attribute_input(node_and_attr, node_only=True)
            if input_value:
                if maya.cmds.nodeType(input_value) == 'decomposeMatrix':
                    found.append(input_value)
                    break

        selector_dict = dict()
        for other in found:
            input_value = attribute.attribute_input('{}.inputMatrix'.format(other), node_only=True)
            if maya.cmds.nodeType(input_value) == 'choice':
                selector_dict[input_value] = None
            if maya.cmds.nodeType(input_value) == 'wtAddMatrix':
                selector_dict[input_value] = None

        found = list()
        for key in selector_dict:
            found.append(key)

        return found

    def get_source(self, switch_node):
        found = list()
        if maya.cmds.nodeType(switch_node) == 'choice':
            indices = attribute.indices('{}.input'.format(switch_node))
            for index in indices:
                input_attr = '{}.input[{}]'.format(switch_node, index)
                matrix_sum = attribute.attribute_input(input_attr, node_only=True)
                matrix_attr = '{}.targetMatrix'.format(matrix_sum)
                if maya.cmds.objExists(matrix_attr):
                    xform = attribute.attribute_input(matrix_attr, node_only=True)
                    found.append(xform)
        elif maya.cmds.nodeType(switch_node) == 'wtAddMatrix':
            indices = attribute.indices('{}.wtMatrix'.format(switch_node))
            for index in indices:
                input_attr = '{}.wtMatrix[{}].matrixIn'.format(switch_node, index)
                matrix_sum = attribute.attribute_input(input_attr, node_only=True)
                matrix_attr = '{}.targetMatrix'.format(matrix_sum)
                if maya.cmds.objExists(matrix_attr):
                    xform = attribute.attribute_input(matrix_attr, node_only=True)
                    found.append(xform)

        return found

    def add_source(self, source_transform, target_transform, switch_node):
        self._description = target_transform
        self._target = target_transform
        self._add_source(source_transform, switch_node)

    def set_use_weight(self, flag):
        self._use_weight = flag

    def set_input_attribute(self, node, attr, switch_names=None):
        if switch_names is None:
            switch_names = list()

        self._attribute_node = node
        self._attribute_name = attr
        self._switch_names = switch_names

    def set_maintain_offset(self, flag):
        self._maintain_offset = flag

    def set_create_title(self, flag, title_name=None):
        self._create_title = flag
        self._title_name = title_name

    def create_switch(self, node, attr, switch_node=None):
        """
        Creates a swith over all target weights
        :param node: str, name of the node to add switch attribute to
        :param attr:  str, name to give to the switch attribute
        :param switch_node, str, either the choice or wtAddMatrix node of the setup. Use get_space_switches to find them
        """

        if self._create_title:
            if self._title_name:
                attribute.create_title(node, self._title_name)
            else:
                attribute.create_title(node, 'SPACE')

        if maya.cmds.nodeType(switch_node) == 'choice':
            sources = self.get_source(switch_node)
            if self._switch_names:
                switch_names = self._switch_names
            else:
                switch_names = list()
                for source in sources:
                    switch_name = source
                    switch_names.append(switch_name)

            var = attribute.EnumAttribute(attr)
            var.set_node(node)
            var.set_keyable(True)
            var.create(node)
            var.set_enum_names(switch_names)
            var.set_locked(False)
            var.set_value(len(switch_names) - 1)
            var.connect_out('{}.selector'.format(switch_node))
        elif maya.cmds.nodeType(switch_node) == 'wtAddMatrix':
            indices = attribute.indices('{}.wtMatrix'.format(switch_node))
            attrs = list()
            for index in indices:
                attrs.append('wtMatrix[{}].weightIn'.format(index))
            remap = attribute.RemapAttributesToAttribute(node, attr)
            remap.create_attributes(switch_node, attrs)
            remap.create()

            if len(attrs) > 1:
                try:
                    maya.cmds.setAttr('{}.{}'.format(node, attr), (len(attrs) - 1))
                except Exception:
                    pass
            elif len(attrs) == 1:
                maya.cmds.setAttr('{}.wtMatrix[0].weightIn'.format(switch_node), 1)

    def _add_source(self, source, switch_node):
        matrix = MatrixConstraint(source, self._target)
        matrix.set_maintain_offset(self._maintain_offset)
        matrix.set_decompose(False)
        node_type = maya.cmds.nodeType(switch_node)
        if node_type == 'wtAddMatrix':
            slot_index = attribute.available_slot('{}.wtMatrix'.format(switch_node))
            matrix.set_description('{}_{}'.format(slot_index + 1, self.description))
            matrix.create()
            matrix_node = matrix.node_multiply_matrix
            maya.cmds.connectAttr(
                '{}.matrixSum'.format(matrix_node), '{}.wtMatrix[{}].matrixIn'.format(switch_node, slot_index))
            weight_attr = 'wtMatrix[{}].weightIn'.format(slot_index)
            self._weight_attributes.append(weight_attr)
        if node_type == 'choice':
            slot_index = attribute.available_slot('{}.input'.format(switch_node))
            matrix.set_description('{}_{}'.format(slot_index + 1, self.description))
            matrix.create()
            matrix_node = matrix.node_multiply_matrix
            maya.cmds.connectAttr(
                '{}.matrixSum'.format(matrix_node), '{}.input[{}]'.format(self._node_choice, slot_index))

    def _create_space_switch(self):
        if self._use_weight:
            self._node_weight_add_matrix = maya.cmds.createNode('wtAddMatrix', self.description)
            matrix_attr = '{}.matrixSum'.format(self._node_weight_add_matrix)
            switch_node = self._node_weight_add_matrix
        else:
            self._node_choice = maya.cmds.createNode('choice', self.description)
            matrix_attr = '{}.output'.format(self._node_choice)
            switch_node = self._node_choice

        if switch_node:
            for source in self._source:
                self._add_source(source, switch_node)

        if self._node_decompose_matrix:
            self._connect_decompose(matrix_attr)

        return switch_node


def has_constraint(xform):
    """
    Returns whether given transform node is being affected by a constraint or not
    :param xform: str, name of a transform node
    :return: bool
    """

    cns = Constraint()
    return cns.has_constraint(xform)


def delete_constraints(xform, constraint_type=None):
    """
    Deletes all constraints in given transform
    :param xform: str, name of the transform
    :param constraint_type: str, type of the constraints types we want to delete. None to delete all types
    """

    cns = Constraint()
    cns.delete_constraints(xform, constraint_type)


def scale_constraint_to_local(scale_constraint):
    """
    Scale constraint can work wrong when given the parent matrix
    Disconnect the parent matrix to fix its behaviour
    Reconnect using scale_constraint_to_world if applying multiple constraints
    :param scale_constraint: str, name of the scale constraint to work on
    """

    cns = Constraint()
    weight_count = cns.get_weight_count(scale_constraint)
    attribute.disconnect_attribute('{}.constraintParentInverseMatrix'.format(scale_constraint))

    for i in range(weight_count):
        attribute.disconnect_attribute('{}.target[{}].targetParentMatrix'.format(scale_constraint, i))


def scale_constraint_to_world(scale_constraint):
    """
    Works with scale_constraint_to_local
    :param scale_constraint: str, name of scale constraint affected by scale_constraint_to_local
    """

    cns = Constraint()
    weight_count = cns.get_weight_count(scale_constraint)
    node = attribute.attribute_outputs('{}.constraintScaleX'.format(scale_constraint), node_only=True)
    if node:
        maya.cmds.connectAttr(
            '{}.parentInverseMatrix'.format(node[0]), '{}.constraintParentInverseMatrix'.format(scale_constraint))

    for i in range(weight_count):
        target = attribute.attribute_input('{}.target[{}].targetScale'.format(scale_constraint, i), True)
        maya.cmds.connectAttr(
            '{}.parentInverseMatrix'.format(target), '{}.target[{}].targetParentMatrix'.format(scale_constraint, i))


def constraint_local(source_transform, target_transform, parent=False, scale_connect=False,
                     constraint='parentConstraint', use_duplicate=False):
    """
    Constraints a target transform to a source one in a way that allows for setups to remain local to the origin.
    Useful when a control needs to move with a rig, but move something at the origin only when the control moves
    :param source_transform: str, name of a transform
    :param target_transform: str, name of a transform
    :param parent: bool, If False, the setup uses a local group to constraint the target transform. Otherwise,
        it will parent the target_transform under the local group
    :param scale_connect: bool, Whether to also asd a scale constraint or not
    :param constraint: str, the type of constraint to use ('parentConstraint', 'pointConstraint', 'orientConstraint')
    :param use_duplicate: bool
    :return: tuple(str, str), the local group that constraints the target transforms and the buffer group above the
        local group
    """

    if use_duplicate:
        local_group = maya.cmds.duplicate(source_transform, n='local_{}'.format(source_transform))[0]
        attribute.remove_user_defined_attributes(local_group)
        children = maya.cmds.listRelatives(local_group)
        if children:
            maya.cmds.delete(children)
        dup_parent = maya.cmds.listRelatives(local_group, p=True)
        if dup_parent:
            maya.cmds.parent(local_group, w=True)
        buffer_group = transform_utils.create_buffer_group(local_group, use_duplicate=True)
    else:
        local_group = maya.cmds.group(empty=True, n=dcc.find_unique_name('local_{}'.format(source_transform)))
        transform_utils.MatchTransform(target_transform, local_group).translation_rotation()
        transform_utils.MatchTransform(target_transform, local_group).scale()
        if shape_utils.has_shape_of_type(source_transform, 'follicle'):
            buffer_group = maya.cmds.group(empty=True, n='buffer_{}'.format(local_group))
            maya.cmds.parent(local_group, buffer_group)
        else:
            buffer_group = transform_utils.create_buffer_group(local_group, copy_scale=True)
        parent_world = maya.cmds.listRelatives(source_transform, p=True)
        if parent_world:
            if not shape_utils.has_shape_of_type(source_transform, 'follicle'):
                parent_world = parent_world[0]
                transform_utils.MatchTransform(parent_world, buffer_group).translation_rotation()

    if not local_group:
        return

    attribute.connect_translate(source_transform, local_group)
    attribute.connect_rotate(source_transform, local_group)
    if scale_connect:
        attribute.connect_scale(source_transform, local_group)
    if parent:
        maya.cmds.parent(target_transform, local_group)

    if not parent:
        if constraint == 'parentConstraint':
            maya.cmds.parentConstraint(local_group, target_transform, mo=True)
        if constraint == 'pointConstraint':
            maya.cmds.pointConstraint(local_group, target_transform, mo=True)
        if constraint == 'orientConstraint':
            maya.cmds.orientConstraint(local_group, target_transform, mo=True)
        if scale_connect:
            attribute.connect_scale(source_transform, target_transform)

    attribute.connect_message(local_group, source_transform, 'out_local')

    return local_group, buffer_group
