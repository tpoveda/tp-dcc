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
