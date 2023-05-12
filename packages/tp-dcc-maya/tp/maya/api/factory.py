import maya.cmds as cmds

from tp.maya.api import base
from tp.maya.om import factory


def create_dag_node(name, node_type, parent=None, mod=None, apply=True):
	"""
	Creates a new DAG node and if a parent is specified, then parent the new node.

	:param str name: name of the DAG node to create.
	:param str node_type: type of the DAG node to create.
	:param base.DagNode or None parent:
	:param OpenMaya.MDagModifier or None mod: optional Maya modifier to apply.
	:param bool apply: whether to apply modifier immediately.
	:return: newly created Maya object instance.
	:rtype: base.DagNode
	"""

	parent_node = parent.object() if parent else None
	return base.node_by_object(
		factory.create_dag_node(name=name, node_type=node_type, parent=parent_node, mod=mod, apply=apply))


def create_dg_node(name, node_type, mod=None, apply=True):
	"""
	Creates a dependency graph node and returns the node Maya object.

	:param str name: new name of the node.
	:param str node_type: Maya node type to create.
	:param OpenMaya.MDGModifier or None mod: optional Maya modifier to apply.
	:param bool apply: whether to apply modifier immediately.
	:return: newly created Maya object instance.
	:rtype: base.DGNode
	"""

	return base.node_by_object(factory.create_dg_node(name=name, node_type=node_type, mod=mod, apply=apply))


def create_mult_matrix(name, inputs, output):
	"""
	Creates a multMatrix node.

	:param str name: name of the node.
	:param list(tp.maya.api.base.Plug) inputs: input plugs.
	:param tp.maya.api.base.Plug or None output: output plug.
	:return: created multMatrix node.
	:rtype: tp.maya.api.base.DGNode
	"""

	mult_matrix = create_dg_node(name, 'multMatrix')
	compound = mult_matrix.matrixIn
	for i in range(1, len(inputs)):
		_input = inputs[i]
		if isinstance(_input, base.Plug):
			_input.connect(compound.element(i))
			continue
		compound.element(i).set(_input)
	_input = inputs[0]
	if isinstance(_input, base.Plug):
		_input.connect(compound.element(0))
	else:
		compound.element(0).set(_input)
	if output is not None:
		mult_matrix.matrixSum.connect(output)

	return mult_matrix


def create_decompose(
		name, destination, translate_values=(True, True, True), rotation_values=(True, True, True),
		scale_values=(True, True, True), input_matrix_plug=None):
	"""
	Creates decompose node and connects it to the given destination node.

	:param str name: name of the node.
	:param base.DGNode destination: node to connect to.
	:param tuple(bool) translate_values: X, Y, Z to apply for the translation channel.
	:param tuple(bool) rotation_values: X, Y, Z to apply for the rotation channel.
	:param tuple(bool) scale_values: X, Y, Z to apply for the scale channel.
	:param base.Plug or None input_matrix_plug: optional input matrix plug to connect from.
	:return: created decompose node.
	:rtype: base.DGNode
	"""

	decompose = create_dg_node(name, 'decomposeMatrix')

	if input_matrix_plug is not None:
		input_matrix_plug.connect(decompose.inputMatrix)

	if destination:
		decompose.outputTranslate.connect(destination.translate, children=translate_values)
		decompose.outputRotate.connect(destination.rotate, children=rotation_values)
		decompose.outputScale.connect(destination.scale, children=scale_values)

	return decompose


def create_controller_tag(node, name, parent=None, visibility_plug=None):
	"""
	Creates a new Maya kControllerTag node into this control.

	:param api.DagNode node: node to tag.
	:param str name: name of the newly created controller tag.
	:param ControlNode parent: optional controller tag control parent.
	:param api.Plug visibility_plug: visibility plug to connect to.
	:return: newly created controller tag instance.
	:rtype: api.DGNode
	"""

	new_controller = create_dg_node(name, 'controller')
	node.message.connect(new_controller.controllerObject)
	if visibility_plug is not None:
		visibility_plug.connect(new_controller.visibilityMode)
	if parent is not None:
		new_controller.attribute('parent').connect(parent.children.nextAvailableDestElementPlug())

	return new_controller


def create_display_layer(name):
	"""
	Creates a new display layer with given name.

	:param str name: name of the display layer.
	:return: newly created display layer instance.
	:rtype: api.DGNode
	"""

	return base.node_by_name(cmds.createDisplayLayer(name=name, empty=True))
