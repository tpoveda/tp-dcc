from tp.common.qt import api as qt

DEFAULT_GROUP_NAME = 'NewCharacter1'
DEFAULT_MAP_NAME = 'Map1'
COMMAND_TYPES = ['Select', 'Reset', 'Key', 'Toggle', 'Pose', 'Range']

DEFAULT_MAP_BACKGROUND_COLOR = qt.QColor(qt.Qt.darkGray)
SELECTED_BORDER_COLOR = qt.QColor(67, 255, 163)

MIME_COLOR_MODIFIER = 'ColorButton/Modifier'

CREATE_NEW_MAP_TOOLTIP = 'Creates a new map based on the options you have given.'
EDIT_MAP_TOOLTIP = 'Edits a current selected map based on the options you have given.'
IMPORT_MAP_TOOLTIP = 'Import a data file to create to map.'
EXPORT_MAP_TOOLTIP = 'Export current map to data file.'
