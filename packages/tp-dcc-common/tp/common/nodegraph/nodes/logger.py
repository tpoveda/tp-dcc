from tp.core import log
from tp.common.nodegraph.core import consts, register
from tp.common.nodegraph.nodes import exec

logger = log.tpLogger


class PrintNode(exec.ExecNode):

	__identifier__ = 'tp.common.nodegraph.utils'
	NODE_NAME = 'print'
	IS_EXEC = True
	AUTO_INIT_EXECS = True

	def __init__(self):
		super(PrintNode, self).__init__()

		self.create_property('Message', value='', widget_type=consts.PropertiesEditorWidgets.TEXT_EDIT)

	def init_sockets(self, reset=True):
		super(PrintNode, self).init_sockets(reset=reset)

		self.message = self.add_input('Message', data_type=register.DataTypes.STRING)

	def execute(self):
		message = self.input_data(self.message)
		print(str(message))


class LoggerNode(exec.ExecNode):

	__identifier__ = 'tp.common.nodegraph.utils'
	NODE_NAME = 'logger'
	IS_EXEC = True
	AUTO_INIT_EXECS = True

	def __init__(self):
		super(LoggerNode, self).__init__()

		self.create_property('Message', value='', widget_type=consts.PropertiesEditorWidgets.TEXT_EDIT)
		self.create_property('As Info', value=True, widget_type=consts.PropertiesEditorWidgets.CHECKBOX)
		self.create_property('As Warning', value=False, widget_type=consts.PropertiesEditorWidgets.CHECKBOX)
		self.create_property('As Error', value=False, widget_type=consts.PropertiesEditorWidgets.CHECKBOX)

	def init_sockets(self, reset=True):
		super(LoggerNode, self).init_sockets(reset=reset)

		self.message = self.add_input('Message', data_type=register.DataTypes.STRING)
		self.as_info = self.add_input('As Info', data_type=register.DataTypes.BOOLEAN)
		self.as_warning = self.add_input('As Warning', data_type=register.DataTypes.BOOLEAN)
		self.as_error = self.add_input('As Error', data_type=register.DataTypes.BOOLEAN)

	def execute(self):
		message = self.input_data(self.message)
		if self.input_data(self.as_info):
			logger.info(message)
		if self.input_data(self.as_warning):
			logger.warning(message)
		if self.input_data(self.as_error):
			logger.error(message)
