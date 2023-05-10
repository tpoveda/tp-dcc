# ======================================================================================================================
# MetaClasses Types
# ======================================================================================================================

RIG_TYPE = 'CritRig'						# Crit rig metaclass name


# ======================================================================================================================
# Names for Standard Transform Local Attributes
# ======================================================================================================================
TRANSFORM_ATTRS = ('translate', 'rotate', 'scale')

# ======================================================================================================================
# MetaData Attribute Names
# ======================================================================================================================

CRIT_ID_ATTR = 'critId'
CRIT_VERSION_ATTR = 'critVersion'
CRIT_NAME_ATTR = 'critName'
CRIT_SIDE_ATTR = 'critSide'
CRIT_IS_CRIT_ATTR = 'critIsCrit'
CRIT_IS_ROOT_ATTR = 'critIsRoot'
CRIT_ROOT_TRANSFORM_ATTR = 'critRootTransform'
CRIT_RIG_CONFIG_ATTR = 'critConfig'
CRIT_CONTROL_DISPLAY_LAYER_ATTR = 'critControlDisplayLayer'
CRIT_ROOT_SELECTION_SET_ATTR = 'critRootSelectionSet'
CRIT_CONTROL_SELECTION_SET_ATTR = 'critControlSelectionSet'
CRIT_SKELETON_SELECTION_SET_ATTR = 'critSkeletonSelectionSet'
CRIT_BUILD_SCRIPT_CONFIG_ATTR = 'critBuildScriptConfig'

# ======================================================================================================================
# Descriptor Keys
# ======================================================================================================================

VERSION_DESCRIPTOR_KEY = 'descriptorVersion'
PARENT_DESCRIPTOR_KEY = 'parent'
CONNECTIONS_DESCRIPTOR_KEY = 'connections'
DAG_DESCRIPTOR_KEY = 'dag'
DG_DESCRIPTOR_KEY = 'dg'
SETTINGS_DESCRIPTOR_KEY = 'settings'
NAME_DESCRIPTOR_KEY = 'name'
SIDE_DESCRIPTOR_KEY = 'side'
TYPE_DESCRIPTOR_KEY = 'type'
METADATA_DESCRIPTOR_KEY = 'metadata'
SPACE_SWITCH_DESCRIPTOR_KEY = 'spaceSwitching'
NAMING_PRESET_DESCRIPTOR_KEY = 'namingPreset'
INPUT_LAYER_DESCRIPTOR_KEY = 'inputLayer'
OUTPUT_LAYER_DESCRIPTOR_KEY = 'outputLayer'
GUIDE_LAYER_DESCRIPTOR_KEY = 'guideLayer'
RIG_LAYER_DESCRIPTOR_KEY = 'rigLayer'
SKELETON_LAYER_DESCRIPTOR_KEY = 'skeletonLayer'
LAYER_DESCRIPTOR_KEYS = (
	INPUT_LAYER_DESCRIPTOR_KEY,
	OUTPUT_LAYER_DESCRIPTOR_KEY,
	GUIDE_LAYER_DESCRIPTOR_KEY,
	RIG_LAYER_DESCRIPTOR_KEY,
	SKELETON_LAYER_DESCRIPTOR_KEY
)

# ======================================================================================================================
# Naming Preset Keys
# ======================================================================================================================

DEFAULT_PRESET_NAME = 'CRIT'
DEFAULT_BUILTIN_PRESET_NAME = 'crit'
