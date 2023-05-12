import json
from collections import OrderedDict

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

from tp.common.python import decorators
from tp.maya.cmds import helpers
from tp.maya.api import base, attributetypes, nodes
from tp.maya.om import factory

CONSTRAINT_TYPES = ('parent', 'point', 'orient', 'scale', 'aim', 'matrix')
TP_CONSTRAINTS_ATTR_NAME = 'tpConstraints'
TP_CONSTRAINT_TYPE_ATTR_NAME = 'tpConstraintType'
TP_CONSTRAINT_KWARGS_ATTR_NAME = 'tpConstraintKwargs'
TP_CONSTRAINT_CONTROLLER_ATTR_NAME = 'tpConstraintController'
TP_CONSTRAINT_CONTROL_ATTR_NAME = 'tpConstraintControlAttrName'
TP_CONSTRAINT_TARGETS_ATTR_NAME = 'tpConstraintTargets'
TP_CONSTRAINT_SPACE_LABEL_ATTR_NAME = 'tpConstraintSpaceLabel'
TP_CONSTRAINT_SPACE_TARGET_ATTR_NAME = 'tpConstraintSpaceTarget'
TP_CONSTRAINT_NODES_ATTR_NAME = 'tpConstraintNodes'
TP_CONSTRAINT_TYPE_INDEX = 0
TP_CONSTRAINT_KWARGS_INDEX = 1
TP_CONSTRAINT_CONTROLLER_INDEX = 2
TP_CONSTRAINT_CONTROL_ATTR_NAME_INDEX = 3
TP_CONSTRAINT_TARGETS_INDEX = 4
TP_CONSTRAINT_SPACE_LABEL_INDEX = 0
TP_CONSTRAINT_SPACE_TARGET_INDEX = 1
TP_CONSTRAINT_NODES_INDEX = 5


def has_constraint(node):
	"""
	Returns whether this node is constrained by another.

	:param tp.maya.api.base.DagNode node: node to search for attached constraints.
	:return: True if node is attached to a constraint; False otherwise.
	:rtype: bool
	"""

	for i in iterate_constraints(node):
		return True

	return False


def iterate_constraints(node):
	"""
	Generator function that iterates over all attached constraints by iterating over the compound array attribute
	called "constraints".

	:param tp.maya.api.base.DagNode node: node to iterate.
	:return: iterated constraints.
	:rtype: generator(Constraint)
	"""

	array = node.attribute(TP_CONSTRAINTS_ATTR_NAME)
	if array is None:
		return
	for plug_element in array:
		type_value = plug_element.child(0).value()
		if not type_value:
			continue
		yield create_constraint_factory(type_value, node, plug_element)


def create_constraint_factory(constraint_type, driven_node, constraint_meta_plug, track=True):
	"""
	Factory function that allows to create different Constraint classes based on given type.

	:param str constraint_type: type of the attribute to create.
	:param tp.maya.api.DagNode driven_node: node to drive.
	:param tp.maya.api.Plug constraint_meta_plug: constraint plug.
	:param bool track: whether the constraint and all nodes created should be tracked via metadata.
	:return: new constraint instance.
	:rtype: Constraint
	:raises NotImplementedError: if given constraint type is not supported.
	"""

	constraint_class = CONSTRAINT_CLASSES.get(constraint_type)
	if constraint_class is None:
		raise NotImplementedError('Constraint of type {} is not supported'.format(constraint_type))

	constraint_instance = constraint_class(track=track)
	constraint_instance.set_driven(driven_node, constraint_meta_plug)

	return constraint_instance


def add_constraint_attribute(node):
	"""
	Creates and returns the "constraints" compound attribute, which is used to store all incoming constraints no
	matter how they are created. If the attribute already exists, it will be returned.

	:param tp.maya.api.base.DagNode node: node to create compound attribute in.
	:return: constraint compound attribute.
	:rtype: tp.maya.api.base.Plug
	"""

	if node.hasAttribute(TP_CONSTRAINTS_ATTR_NAME):
		return node.attribute(TP_CONSTRAINTS_ATTR_NAME)

	constraint_plug = node.addCompoundAttribute(
		name=TP_CONSTRAINTS_ATTR_NAME, type=attributetypes.kMFnCompoundAttribute, isArray=True, attr_map=[
			dict(name=TP_CONSTRAINT_TYPE_ATTR_NAME, type=attributetypes.kMFnDataString),
			dict(name=TP_CONSTRAINT_KWARGS_ATTR_NAME, type=attributetypes.kMFnDataString),
			dict(name=TP_CONSTRAINT_CONTROLLER_ATTR_NAME, type=attributetypes.kMFnMessageAttribute),
			dict(name=TP_CONSTRAINT_CONTROL_ATTR_NAME, type=attributetypes.kMFnDataString),
			dict(name=TP_CONSTRAINT_TARGETS_ATTR_NAME, type=attributetypes.kMFnCompoundAttribute, isArray=True, children=[
				dict(name=TP_CONSTRAINT_SPACE_LABEL_ATTR_NAME, type=attributetypes.kMFnDataString),
				dict(name=TP_CONSTRAINT_SPACE_TARGET_ATTR_NAME, type=attributetypes.kMFnMessageAttribute)]),
			dict(name=TP_CONSTRAINT_NODES_ATTR_NAME, type=attributetypes.kMFnMessageAttribute, isArray=True)
		]
	)

	return constraint_plug


def build_constraint(driven, drivers, constraint_type='parent', track=True, **kwargs):
	"""
	Builds a space switching ready constraint.

	:param tp.maya.api.base.DagNode driven: transform to drive.
	:param dict drivers: a dict containing the target information.
	:param str constraint_type: constraint type.
	:param bool track: whether the constraint and all nodes created should be tracked via metadata.
	:param dict kwargs: extra keyword arguments.
	:keyword bool maintainOffset: whether to maintain offset transformation after constraint is applied.
	:return: tuple containing the constraint instance and the constraint extra nodes.
	:rtype: tuple(Constraint, list(tp.maya.api.base.DagNode))
	"""

	assert constraint_type in CONSTRAINT_TYPES, 'Constraint of type: {} is not supported'.format(constraint_type)

	constraint_attr = None
	if track:
		attr_name = drivers.get('attributeName', '')
		for last_constraint in iterate_constraints(driven):
			if attr_name and attr_name == last_constraint.controller_attribute_name():
				utilities =  last_constraint.build(drivers, **kwargs)
				return last_constraint, utilities
			constraint_attr = last_constraint.plug_element
		if constraint_attr is None:
			constraint_attr = add_constraint_attribute(driven)[0]
		else:
			latest_constraint_index = constraint_attr.logicalIndex()
			constraint_attr = driven.attribute(TP_CONSTRAINTS_ATTR_NAME)[latest_constraint_index + 1]

	constraint = create_constraint_factory(constraint_type, driven, constraint_attr, track=track)

	return constraint, constraint.build(drivers, **kwargs)


def delete_constraints(nodes, mod=None):
	"""
	Deletes all the constraints of the given nodes.

	:param list(tp.maya.api.base.DagNode) nodes: nodes we want to delete constraints of.
	:param OpenMaya.MDagModifier or None mod: optional modifier to add to.
	:return: modifier used to run the operation.
	:rtype: OpenMaya.MDagModifier
	"""

	mod = mod or OpenMaya.MDagModifier()
	for node in nodes:
		for constraint in iterate_constraints(node):
			constraint.delete(mod=mod, apply=False)
		delete_constraint_map_attribute(node, mod=mod)

	return mod


def add_constraint_map(
		drivers, driven, controller, controller_attr_name, utilities, constraint_type, meta_element_plug,
		kwargs_map=None):
	"""
	Adds a mapping of drivers and utilities to the constraint compound array attribute.

	:param drivers:
	:param driven:
	:param controller:
	:param controller_attr_name:
	:param utilities:
	:param constraint_type:
	:param meta_element_plug:
	:param kwargs_map:
	:return:
	"""

	kwargs_map = kwargs_map or dict()
	compound_plug = add_constraint_attribute(driven)
	if not meta_element_plug:
		for element in compound_plug:
			element_constraint_type = element.child(TP_CONSTRAINT_TYPE_INDEX).value()
			if not element_constraint_type or element_constraint_type == constraint_type:
				meta_element_plug = element
				break
			if meta_element_plug is None:
				meta_element_plug = compound_plug[0]
	constraint_type_plug = meta_element_plug.child(TP_CONSTRAINT_TYPE_INDEX)
	kwargs_plug = meta_element_plug.child(TP_CONSTRAINT_KWARGS_INDEX)

	if controller is not None:
		controller_plug = meta_element_plug.child(TP_CONSTRAINT_CONTROLLER_INDEX)
		controller_name_plug = meta_element_plug.child(TP_CONSTRAINT_CONTROL_ATTR_NAME_INDEX)
		controller.message.connect(controller_plug)
		controller_name_plug.set(controller_attr_name)

	targets_plug = meta_element_plug.child(TP_CONSTRAINT_TARGETS_INDEX)
	constraints_plug = meta_element_plug.child(TP_CONSTRAINT_NODES_INDEX)
	constraint_type_plug.set(constraint_type)
	kwargs_plug.set(json.dumps(kwargs_map))

	index = 0
	driver_element = targets_plug.nextAvailableDestElementPlug()
	for driver_label, driver in drivers:
		index += 1
		driver_element.child(TP_CONSTRAINT_SPACE_LABEL_INDEX).set(driver_label)
		if driver:
			driver.message.connect(driver_element.child(TP_CONSTRAINT_SPACE_TARGET_INDEX))
		driver_element = targets_plug[index]

	for constraint_node in utilities:
		constraint_node.message.connect(constraints_plug.nextAvailableDestElementPlug())

	return compound_plug


def delete_constraint_map_attribute(node, mod=None):
	"""
	Removes the constraint metadata if it is present on given node.

	:param tp.maya.api.base.DGNode node: node to remove metadata from.
	:param OpenMaya.MDGModifier or None mod: optional modifier to add to.
	:return: used modifier to run the operation.
	:rtype: OpenMaya.MDGModifier
	"""

	constraint_attr = node.attribute(TP_CONSTRAINTS_ATTR_NAME)
	if constraint_attr is None:
		return mod

	mod = mod or OpenMaya.MDGModifier()
	if constraint_attr.numConnectedElements() > 0:
		for attr in constraint_attr:
			if attr.numConnectedChildren() < 1:
				continue
			target_attr = attr.child(4)
			controller_attr = attr.child(2)
			extra_nodes_attr = attr.child(5)
			controller_attr.disconnectAll(mod=mod)
			if target_attr.numConnectedElements() > 0:
				for element in target_attr:
					if element.numConnectedElements() < 1:
						continue
					element.child(1).disconnectAll(mod=mod)
			if extra_nodes_attr.numConnectedElements() < 1:
				continue
			for element in extra_nodes_attr:
				element.disconnectAll(mod=mod)

	# we need to separate the disconnect from the deletion to avoid crashes.
	mod.doIt()
	constraint_attr.delete(mod=mod)

	return mod


class Constraint(object):

	ID = ''

	def __init__(self, driven=None, plug_element=None, track=True):
		super(Constraint, self).__init__()

		if driven and not plug_element or (plug_element and not driven):
			raise ValueError('if driven or plug_element are specified, both of them must be specified')

		self._driven = driven
		self._plug_element = plug_element
		self._track = track
		self._constraint_node = None

	# ==================================================================================================================
	# PROPERTIES
	# ==================================================================================================================

	@property
	def plug_element(self):
		return self._plug_element

	@property
	def constraint_node(self):
		return self._constraint_node

	# ==================================================================================================================
	# ABSTRACT METHODS
	# ==================================================================================================================

	@decorators.abstractmethod
	def build(self, drivers, **constraint_kwargs):
		"""
		Builds the constraint with given keyword arguments.

		:param list(tp.maya.api.DagNode) drivers: nodes to be driven by the constraint.
		:param dict constraint_kwargs: constraint keyword arguments.
		:return: list of created nodes.
		:rtype: list(tp.maya.api.base.DGNode)
		"""

		raise NotImplementedError('Build method must be implemented in subclasses')

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def driven(self):
		"""
		Returns constraint driven node.

		:return: driven node.
		:rtype: tp.maya.api.base.DagNode or None
		"""

		return self._driven

	def set_driven(self, node, plug_element):
		"""
		Sets the driven node for the constraint.

		:param tp.maya.api.base.DagNode node: driven node.
		:param tp.maya.api.base.Plug plug_element: plug element
		"""

		self._driven = node
		self._plug_element = plug_element

	def iterate_drivers(self):
		"""
		Generator function that iterates over all driver nodes of the constraint.

		:return: iterated driver nodes.
		:rtype: generator(tp.maya.api.base.DagNode)
		"""

		if not self._plug_element:
			return

		for target_element in self._plug_element.child(TP_CONSTRAINT_TARGETS_INDEX):
			source_node = target_element.child(TP_CONSTRAINT_SPACE_TARGET_INDEX).sourceNode()
			label = target_element.child(TP_CONSTRAINT_SPACE_LABEL_INDEX).value()
			if label:
				yield label, source_node

	def delete(self, mod=None, apply=True):
		"""
		Deletes constraint.

		:param OpenMaya.MDGModifier or None mod: optional modifier to add to.
		:param bool apply: whether to immediately apply delete operation.
		:return: True if the constraint was deleted successfully; False otherwise.
		:rtype: bool
		"""

		# disconnect connections from utilities nodes and delete them
		for target_plug in self._plug_element.child(TP_CONSTRAINT_NODES_INDEX):
			source_plug = target_plug.source()
			if not source_plug:
				continue
			util_node = source_plug.node()
			for source_plug, dest_plug in util_node.iterateConnections(True, False):
				source_plug.disconnect(dest_plug, mod=mod, apply=apply)
			util_node.delete(mod=mod, apply=False)

		# delete control attribute
		controller_node = self._plug_element.child(TP_CONSTRAINT_CONTROLLER_INDEX).sourceNode()
		if controller_node is not None:
			attr_name = self._plug_element.child(TP_CONSTRAINT_CONTROL_ATTR_NAME_INDEX).value()
			control_attr = controller_node.attribute(attr_name)
			if control_attr is not None:
				control_attr.delete(mod=mod, apply=apply)

		# remove multi instance element plug
		self._plug_element.delete(mod=mod, apply=apply)

		return True




class ParentConstraint(Constraint):

	ID = 'parent'
	CONSTRAINT_TARGET_INDEX = 1
	CONSTRAINT_FN = 'parentConstraint'

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def build(self, drivers, **constraint_kwargs):
		"""
		Builds the constraint with given keyword arguments.

		:param list(tp.maya.api.DagNode) drivers: nodes to be driven by the constraint.
		:param dict constraint_kwargs: constraint keyword arguments.
		:return: list of created nodes.
		:rtype: list(tp.maya.api.base.DGNode)
		"""

		space_node = drivers.get('spaceNode')
		attr_name = drivers.get('attributeName', 'parent')
		target_info = drivers['targets']

		# check whether the constraint needs to be rebuilt if the request node is the same as the current target
		new_target_structure = OrderedDict(self.iterate_drivers())
		new_target_structure.update(OrderedDict(target_info))
		requires_update = False
		for index, (request_label, request_node) in enumerate(target_info):
			existing_target = new_target_structure.get(request_label)
			if existing_target is not None or existing_target != request_node:
				requires_update = True
			new_target_structure[request_label] = request_node
		if not requires_update:
			return list()

		indexing = [index for index, (_, request_node) in enumerate(target_info) if request_node]

		if self._track:
			self.delete()

		driven = self.driven()
		cmds_fn = getattr(cmds, self.CONSTRAINT_FN)
		constraint_kwargs = {str(k): v for k, v in constraint_kwargs.items()}
		target_nodes = [target for _, target in new_target_structure.items() if target]

		self.pre_construct_constraint(driven, target_nodes, constraint_kwargs)

		constraint = cmds_fn(
			[target.fullPathName() for target in target_nodes], driven.fullPathName(), **constraint_kwargs)[0]
		constraint = base.node_by_name(constraint)

		self.post_construct_constraint(driven, target_nodes, constraint, constraint_kwargs)

		self._constraint_node = constraint

		if not space_node:
			if self._track:
				add_constraint_map(
					target_info, driven, None, '', [constraint], self.ID, meta_element_plug=self._plug_element,
					kwargs_map=constraint_kwargs)
			return [constraint]

		raise NotImplementedError

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def pre_construct_constraint(self, driven, target_nodes, constraint_kwargs):
		"""
		Function that is called before the constraint is created.

		:param tp.maya.api.base.DagNode driven: constraint driven node.
		:param list(tp.maya.api.base.DagNode) target_nodes: list of target nodes.
		:param dict constraint_kwargs: constraint keyword arguments.
		"""

		pass

	def post_construct_constraint(self, driven, target_nodes, constraint, constraint_kwargs):
		"""
		Function that is called after the constraint is created.

		:param tp.maya.api.base.DagNode driven: constraint driven node.
		:param list(tp.maya.api.base.DagNode) target_nodes: list of target nodes.
		:param tp.maya.api.base.DagNode constraint: created constraint node.
		:param dict constraint_kwargs: constraint keyword arguments.
		"""

		pass


class PointConstraint(ParentConstraint):

	ID = 'point'
	CONSTRAINT_TARGET_INDEX = 4
	CONSTRAINT_FN = 'pointConstraint'


class OrientConstraint(ParentConstraint):

	ID = 'orient'
	CONSTRAINT_TARGET_INDEX = 4
	CONSTRAINT_FN = 'orientConstraint'


class ScaleConstraint(ParentConstraint):

	ID = 'scale'
	CONSTRAINT_TARGET_INDEX = 2
	CONSTRAINT_FN = 'scaleConstraint'


class AimConstraint(ParentConstraint):

	ID = 'aim'
	CONSTRAINT_TARGET_INDEX = 4
	CONSTRAINT_FN = 'aimConstraint'


class MatrixConstraint(Constraint):

	ID = 'matrix'

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def build(self, drivers, decompose=False, **constraint_kwargs):
		"""
		Builds the constraint with given keyword arguments.

		:param list(tp.maya.api.DagNode) drivers: nodes to be driven by the constraint.
		:param bool decompose: use decompose node to create the constraint.
		:param dict constraint_kwargs: constraint keyword arguments.
		:return: list of created nodes.
		:rtype: list(tp.maya.api.base.DGNode)
		"""

		if helpers.maya_version() >= 2020 and not decompose:
			return MatrixConstraint._build_offset_parent_matrix_constraint(
				self.driven(), drivers, self._track, **constraint_kwargs)

		return MatrixConstraint._build_matrix_constraint(self.driven(), drivers, self._track, **constraint_kwargs)

	# ==================================================================================================================
	# CLASS METHODS
	# ==================================================================================================================

	@classmethod
	def _build_offset_parent_matrix_constraint(cls, driven, drivers, track=True, **constraint_kwargs):
		"""
		Internal function that creates an offset parent matrix constraint.

		:param tp.maya.api.DagNode driven: constraint driven node.
		:param list(dict) drivers: dictionary containing targets info.
		:param bool track: whether the constraint and all nodes created should be tracked via metadata.
		:param dict constraint_kwargs: extra constraint keyword arguments.
		:return: list of constraint related nodes created.
		:rtype: list(tp.maya.api.base.DGNode)
		"""

		maintain_offset = constraint_kwargs.get('maintainOffset', False)
		skip_translate = constraint_kwargs.get('skipTranslate', [False, False, False])
		skip_rotate = constraint_kwargs.get('skipRotate', [False, False, False])
		skip_scale = constraint_kwargs.get('skipScale', [False, False, False])
		name = driven.fullPathName(partial_name=True, include_namespace=False)
		target_info = drivers['targets']
		_, target_nodes = zip(*target_info)
		driver = target_nodes[0]
		compose_name = '_'.join([name, 'pickMtx'])
		skip_translate = any(i for i in skip_translate)
		skip_rotate = any(i for i in skip_rotate)
		skip_scale = any(i for i in skip_scale)

		utilities = list()
		current_world_matrix = driven.worldMatrix()
		if any((skip_scale, skip_translate, skip_rotate)):
			pick_matrix = base.create_dg(compose_name, 'pickMatrix')
			driver.attribute('worldMatrix')[0].connect(pick_matrix.inputMatrix)
			pick_matrix.useTranslate = not skip_translate
			pick_matrix.useRotate = not skip_rotate
			pick_matrix.useScale = not skip_scale
			pick_matrix.outputMatrix.connect(driven.offsetParentMatrix)
			utilities.append(pick_matrix)
		else:
			driver.attribute('worldMatrix')[0].connect(driven.offsetParentMatrix)

		if maintain_offset:
			driven.setMatrix(current_world_matrix * driven.offsetParentMatrix.value().inverse())
		else:
			driven.resetTransform(translate=True, rotate=True, scale=True)

		if track:
			add_constraint_map(target_info, driven, None, '', utilities, cls.ID, None, kwargs_map=constraint_kwargs)

		return utilities

	@classmethod
	def _build_matrix_constraint(cls, driven, drivers, track=True, **constraint_kwargs):
		"""
		Internal function that creates a matrix constraint.

		:param tp.maya.api.DagNode driven: constraint driven node.
		:param list(dict) drivers: dictionary containing targets info.
		:param bool track: whether the constraint and all nodes created should be tracked via metadata.
		:param dict constraint_kwargs: extra constraint keyword arguments.
		:return: list of constraint related nodes created.
		:rtype: list(tp.maya.api.base.DGNode)
		"""

		maintain_offset = constraint_kwargs.get('maintainOffset', False)
		skip_translate = constraint_kwargs.get('skipTranslate', [False, False, False])
		skip_rotate = constraint_kwargs.get('skipRotate', [False, False, False])
		skip_scale = constraint_kwargs.get('skipScale', [False, False, False])
		name = driven.fullPathName(partial_name=True, include_namespace=False)
		target_info = drivers['targets']
		_, target_nodes = zip(*target_info)
		driver = target_nodes[0]
		compose_name = '_'.join([name, 'wMtxCompose'])

		utilities = list()
		if maintain_offset:
			offset = nodes.offset_matrix(driver.object(), driven.object())
			offset_name = '_'.join([name, 'wMtxOffset'])
			mult_matrix = factory.create_mult_matrix(
				offset_name, inputs=(offset, driver.attribute('worldMatrix')[0], driven.parentInverseMatrix()),
				output=None)
			output_plug = mult_matrix.matrixSum
			utilities.append(mult_matrix)
		else:
			output_plug = driver.attribute('worldMatrix')[0]

		decompose = factory.create_decompose(
			compose_name, destination=driven, translate_values=skip_translate or (), rotation_values=skip_rotate or (),
			scale_values=skip_scale or ())
		driver.rotateOrder.connect(decompose.inputRotateOrder)
		output_plug.connect(decompose.inputMatrix)
		utilities.append(decompose)

		if track:
			add_constraint_map(target_info, driven, None, '', utilities, cls.ID, kwargs_map=constraint_kwargs)

		return utilities


CONSTRAINT_CLASSES = {
	'parent': ParentConstraint,
	'point': PointConstraint,
	'orient': OrientConstraint,
	'scale': ScaleConstraint,
	'aim': AimConstraint,
	'matrix': MatrixConstraint
}
