from tp.common.nodegraph.core import node
from tp.common.nodegraph.nodes import group
from tp.common.nodegraph.painters import socket as socket_painters


class BasicNodeA(node.BaseNode):
	"""
	Basic node with 2 inputs and 2 outputs.
	"""

	__identifier__ = 'nodes.basic'
	NODE_NAME = 'node A'

	def __init__(self):
		super(BasicNodeA, self).__init__()

		self.add_input('in A')
		self.add_input('in B')
		self.add_output('out A')
		self.add_output('out B')


class BasicNodeB(node.BaseNode):
	"""
	Basic node with 3 inputs and 3 outputs
	The last input and last output can take multiple connections.
	"""

	__identifier__ = 'nodes.basic'
	NODE_NAME = 'node B'

	def __init__(self):
		super(BasicNodeB, self).__init__()

		self.add_input('single 1')
		self.add_input('single 2')
		self.add_input('multi in', multi_input=True)

		self.add_output('single 1', multi_output=False)
		self.add_output('single 2', multi_output=False)
		self.add_output('multi out', multi_output=False)


class CustomSocketsNode(node.BaseNode):

	__identifier__ = 'nodes.custom.sockets'
	NODE_NAME = 'node'

	def __init__(self):
		super(CustomSocketsNode, self).__init__()

		self.add_input('in', color=(200, 10, 0))
		self.add_output('default')
		self.add_output('square', painter_fn=socket_painters.square_socket_painter)
		self.add_output('triangle', painter_fn=socket_painters.triangle_socket_painter)


class CustomGroupNode(group.GroupNode):

	__identifier__ = 'nodes.group'

	NODE_NAME = 'group node'

	def __init__(self):
		super(CustomGroupNode, self).__init__()

		self.set_color(50, 8, 25)

		self.add_input('in')
		self.add_output('out')
