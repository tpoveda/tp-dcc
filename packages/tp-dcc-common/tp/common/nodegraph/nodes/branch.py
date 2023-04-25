from tp.common.nodegraph.core import register
from tp.common.nodegraph.nodes import exec


class BranchNode(exec.ExecNode):

	__identifier__ = 'tp.common.nodegraph.utils'
	NODE_NAME = 'branch'
	IS_EXEC = True
	AUTO_INIT_EXECS = False

	def init_sockets(self, reset=True):
		super(BranchNode, self).init_sockets(reset=reset)

		self.exec_input_socket = self.add_input('input', data_type=register.DataTypes.EXEC)
		self.in_condition = self.add_input('condition', data_type=register.DataTypes.BOOLEAN)
		self.exec_output_socket = self.add_output('True', data_type=register.DataTypes.EXEC)
		self.out_true = self.exec_output_socket
		self.out_false = self.add_output('False', data_type=register.DataTypes.EXEC)
