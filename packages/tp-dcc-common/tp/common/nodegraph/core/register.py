import numbers
from collections import OrderedDict

from Qt.QtGui import QColor

from tp.core import log
from tp.common.nodegraph.core import exceptions

logger = log.tpLogger

DATATYPE_REGISTER = dict()
FUNCTIONS_REGISTER = dict()
FUNCTIONS_QUEUE = OrderedDict()
UNBOUND_FUNCTION_DATA_TYPE = 'UNBOUND'


def instancer(cls):
	return cls()


class DataTypes(object):

	EXEC = 'EXEC'
	STRING = 'STRING'
	NUMERIC = 'NUMERIC'
	BOOLEAN = 'BOOLEAN'
	LIST = 'LIST'


@instancer
class DataType(object):
	"""
	Defines the available socket data types
	"""

	EXEC = {'class': type(None), 'color': QColor('#FFFFFF'), 'label': '', 'default': None}
	STRING = {'class': str, 'color': QColor('#A203F2'), 'label': 'Name', 'default': ''}
	NUMERIC = {'class': numbers.Complex, 'color': QColor('#DEC017'), 'label': 'Number', 'default': 0.0}
	BOOLEAN = {'class': bool, 'color': QColor('#C40000'), 'label': 'Condition', 'default': False}
	LIST = {'class': list, 'color': QColor('#0BC8F1'), 'label': 'List', 'default': list()}

	def __getattr__(self, name):
		if name in DATATYPE_REGISTER:
			return DATATYPE_REGISTER[name]
		else:
			logger.error('Unregistered datatype: {0}'.format(name))
			raise KeyError

	@classmethod
	def basic_types(cls):
		return [(dt, desc) for dt, desc in cls.__dict__.items() if isinstance(desc, dict)]

	@classmethod
	def register_basic_types(cls):
		for type_name, type_dict in cls.basic_types():
			DATATYPE_REGISTER[type_name] = type_dict

	@classmethod
	def register_data_type(cls, type_name, type_class, color, label='custom_data', default_value=None):
		if type_name in DATATYPE_REGISTER.keys():
			logger.error('Datatype {} is already registered!'.format(type_name))
			raise exceptions.InvalidDataTypeRegistrationError

		type_dict = {
			'class': type_class,
			'color': color if isinstance(color, QColor) else QColor(color),
			'label': label,
			'default': default_value
		}
		DATATYPE_REGISTER[type_name.upper()] = type_dict

	@classmethod
	def get_type(cls, type_name):
		"""
		Returns data related with given data type name.

		:param str type_name: data type name.
		:return: data type data dictionary.
		:rtype: dict
		"""

		try:
			return DATATYPE_REGISTER[type_name]
		except KeyError:
			logger.exception('Unregistered data type: {}'.format(type_name))

	@classmethod
	def get_type_name(cls, data_type_dict):
		try:
			type_name = [
				data_type_name for data_type_name, data in DATATYPE_REGISTER.items() if data == data_type_dict][0]
			return type_name
		except IndexError:
			logger.exception('Failed to find data type for class {}'.format(data_type_dict['class']))
			raise IndexError


def register_function(
		fn, source_data_type, identifier, inputs_dict=None, outputs_dict=None, default_values=None, nice_name=None,
		sub_type=None, docstring='', icon=None):


	inputs_dict = inputs_dict or dict()
	outputs_dict = outputs_dict or dict()
	default_values = default_values or list()

	if source_data_type:
		if isinstance(source_data_type, dict):
			data_type_name = DataType.get_type_name(source_data_type)
		else:
			logger.error('Invalid data type passed to registe function: {}'.format(source_data_type))
			raise ValueError
	else:
		data_type_name = UNBOUND_FUNCTION_DATA_TYPE

	if source_data_type:
		source_class = source_data_type.get('class')
		if source_class:
			signature = '{}.{}.{}'.format(source_class.__module__, source_class.__name__, fn.__name__)
		else:
			signature = '{}.{}'.format(fn.__module__, fn.__name__)
	else:
		signature = '{}.{}'.format(fn.__module__, fn.__name__)

	if sub_type:
		signature = '{}({})'.format(signature, sub_type)

	fn_dict = {
		'ref': fn,
		'identifier': identifier,
		'inputs': inputs_dict,
		'outputs': outputs_dict,
		'doc': docstring,
		'icon': icon,
		'nice_name': nice_name,
		'default_values': default_values
	}

	if data_type_name not in FUNCTIONS_QUEUE:
		FUNCTIONS_QUEUE[data_type_name] = dict()
	FUNCTIONS_QUEUE[data_type_name][signature] = fn_dict


def load_registers():

	logger.info('Loading NodeGraph registers ...')

	DATATYPE_REGISTER.clear()

	DataType.register_basic_types()

	for data_type_name in FUNCTIONS_QUEUE.keys():
		if data_type_name not in FUNCTIONS_REGISTER:
			FUNCTIONS_REGISTER[data_type_name] = dict()
		for signature, fn_dict in FUNCTIONS_QUEUE[data_type_name].items():
			FUNCTIONS_REGISTER[data_type_name][signature] = fn_dict
			logger.info('Function registered {} : {}'.format(data_type_name, signature))
	FUNCTIONS_QUEUE.clear()
