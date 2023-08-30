from tp.common.qt import api as qt

DEFAULT_GROUP_NAME = 'NewCharacter1'
DEFAULT_MAP_NAME = 'Map1'
DEFAULT_MAP_WIDTH = 400
DEFAULT_MAP_HEIGHT = 400

COMMAND_TYPES = ['Select', 'Reset', 'Key', 'Toggle', 'Pose', 'Range']

DEFAULT_MAP_BACKGROUND_COLOR = qt.QColor(qt.Qt.darkGray)
SELECTED_BORDER_COLOR = qt.QColor(67, 255, 163)
FONT_DB = qt.QFontDatabase()
FONT_FAMILIES = FONT_DB.families()


MIME_TEMPLATE = 'AnimPicker/Template'
MIME_TEMPLATE_SIZE = 'AnimPicker/Template-Size'
MIME_COLOR_MODIFIER = 'ColorButton/Modifier'
MIME_COLOR = 'ToolDialog/Color'
MIME_NEW_BUTTON = 'ToolDialog/NewButton'
MIME_IMAGE = 'ToolDialog/Image'
MIME_IMAGE_PATH = 'ToolDialog/Image-Path'
MIME_IMAGE_RECT = 'ToolDialog/Image-Rect'
MIME_IMAGE_BUTTON_SIZE = 'ToolDialog/Image-ButtonSize'
MIME_COMMAND = 'ToolDialog/Command'
MIME_LABEL = 'ToolDialog/Label'
MIME_FONT_FAMILY = 'ToolDialog/Font-Family'
MIME_FONT_SIZE = 'ToolDialog/Font-Size'
MIME_FONT_BOLD = 'ToolDialog/Font-Bold'
MIME_FONT_ITALIC = 'ToolDialog/Font-Italic'
MIME_DRAG_COMBO_TEXT = 'DragComboBox/Text'
MIME_CUSTOM_LABEL = 'ToolDialog/Custom-Label'
MIME_SLIDER_COMMAND = 'ToolDialog/Slider-Command'

CREATE_NEW_MAP_TOOLTIP = 'Creates a new map based on the options you have given.'
EDIT_MAP_TOOLTIP = 'Edits a current selected map based on the options you have given.'
IMPORT_MAP_TOOLTIP = 'Import a data file to create to map.'
EXPORT_MAP_TOOLTIP = 'Export current map to data file.'
COPY_PREFIX_TOOLTIP = 'Copy prefix from selected object.'

NAME_REGEX = qt.QRegExp('\\w+')

SCROLL_THICKNESS = 12
SCROLL_WAITING_TIME = 3000


def default_color(option: str) -> qt.QColor:
	"""
	Returns the default color for the given option.

	:param str option: option to get color value of.
	:return: option color.
	:rtype: qt.QColor
	"""

	if option == 'RtIK':
		color = qt.QColor.fromRgbF(0.7, 0.4, 0.7)
	elif option == 'RtFK':
		color = qt.QColor.fromRgbF(0.7, 0.4, 0.4)
	elif option == 'CnIK':
		color = qt.QColor.fromRgbF(0.4, 0.7, 0.4)
	elif option == 'CnFK':
		color = qt.QColor.fromRgbF(0.7, 0.7, 0.4)
	elif option == 'LfIK':
		color = qt.QColor.fromRgbF(0.4, 0.5, 0.7)
	elif option == 'LfFK':
		color = qt.QColor.fromRgbF(0.4, 0.6, 0.6)
	elif option == 'Grey':
		color = qt.QColor.fromRgbF(0.4, 0.4, 0.4)
	elif option == 'OK':
		color = qt.QColor.fromRgbF(0.5, 0.7, 0.8)
	elif option == 'Cancel':
		color = qt.QColor.fromRgbF(0.7, 0.5, 0.4)
	elif option == 'Warn':
		color = qt.QColor.fromRgbF(0.7, 0.2, 0.2)
	elif option == 'Collapse':
		color = qt.QColor.fromRgbF(0.15, 0.15, 0.15)
	elif option == 'Subtle':
		color = qt.QColor.fromRgbF(0.48, 0.48, 0.6)
	else:
		return qt.QColor.fromRgbF(0.0, 0.0, 0.0)
	if option:
		color.ann = option + ' Color'

	return color


class WaitState:
	Wait = 0
	GoBack = 1
	Proceed = 2


class Attachment:
	NOT_VALID = 0
	TOP = 1
	BOTTOM = 2
	LEFT = 4
	RIGHT = 8

	@classmethod
	def is_top(cls, value: int) -> bool:
		"""
		Returns whether given value corresponds to a top attachment.

		:param int value: attachment value.
		:return: True if attachment value corresponds to a top one; False otherwise.
		:rtype: bool
		"""

		return bool(value & cls.TOP)
