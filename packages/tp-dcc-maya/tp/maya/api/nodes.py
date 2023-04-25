from tp.maya.api import base
from tp.maya.om import nodes


def root_node(node, node_type):
	"""
	Recursively traverses up the hierarchy until finding the first object that does not have a parent.

	:param tp.maya.api.base.DagNode node: Dag node instance to get root of.
	:param OpenMaya.MFn.kType node_type: node type for the root node.
	:return: found root node.
	:rtype: tp.maya.api.base.DagNode
	"""

	return base.node_by_object(nodes.root_node(node.object(), node_type=node_type))
