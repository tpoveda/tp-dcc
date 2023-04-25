from tp.common.nodegraph.nodes import exec


class FunctionNode(exec.ExecNode):

	NODE_NAME = 'function'
	IS_EXEC = True
	AUTO_INIT_EXECS = True

	def __init__(self):

		self._fn_signature = ''
		self._fn_desc = dict()

		super(FunctionNode, self).__init__()
