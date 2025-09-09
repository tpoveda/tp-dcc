from __future__ import annotations

import enum

# === Environment Variable Keys ===
MODULES_ENV_VAR_KEY = "MODRIG_COMPONENTS_PATHS"
DESCRIPTORS_ENV_VAR_KEY = "MODRIG_DESCRIPTORS_PATHS"
TEMPLATES_ENV_VAR_KEY = "MODRIG_TEMPLATES_PATHS"
GRAPHS_ENV_VAR_KEY = "MODRIG_GRAPHS_PATHS"

# === File Extensions ===
DESCRIPTOR_EXTENSION = ".descriptor"
TEMPLATE_EXTENSION = ".template"
GRAPH_EXTENSION = ".dgGraph"

# === MetaClasses Types ===
RIG_TYPE = "modRig"
MODULE_TYPE = "modRigModule"
BASE_LAYER_TYPE = "modRigLayer"
GEOMETRY_LAYER_TYPE = "modRigGeometryLayer"
MODULES_LAYER_TYPE = "modRigModulesLayer"
GUIDE_LAYER_TYPE = "modRigGuideLayer"
INPUT_LAYER_TYPE = "modRigInputLayer"
OUTPUT_LAYER_TYPE = "modRigOutputLayer"
XGROUP_LAYER_TYPE = "modRigXGroupLayer"
SKELETON_LAYER_TYPE = "modRigSkeletonLayer"
RIG_LAYER_TYPE = "modRigRigLayer"
LAYER_TYPES = (
    RIG_LAYER_TYPE,
    GUIDE_LAYER_TYPE,
    SKELETON_LAYER_TYPE,
    INPUT_LAYER_TYPE,
    OUTPUT_LAYER_TYPE,
    XGROUP_LAYER_TYPE,
    MODULES_LAYER_TYPE,
    GEOMETRY_LAYER_TYPE,
)

# === Shared MetaData Attribute Names ===
ID_ATTR = "id"
NAME_ATTR = "name"
IS_MOD_RIG_ATTR = "isModRig"
IS_ROOT_ATTR = "isRoot"
IS_MODULE_ATTR = "isComponent"

# === Rig MetaData Attribute Names ===
RIG_VERSION_INFO_ATTR = "versionInfo"
RIG_CONFIG_ATTR = "config"
RIG_BUILD_SCRIPT_CONFIG_ATTR = "buildScriptConfig"
RIG_ROOT_TRANSFORM_ATTR = "rootTransform"
RIG_CONTROL_DISPLAY_LAYER_ATTR = "controlDisplayLayer"
RIG_ROOT_SELECTION_SET_ATTR = "rootSelectionSet"
RIG_CONTROL_SELECTION_SET_ATTR = "controlSelectionSet"
RIG_JOINT_SELECTION_SET_ATTR = "jointSelectionSet"
RIG_SKELETON_SELECTION_SET_ATTR = "skeletonSelectionSet"
RIG_GEOMETRY_SELECTION_SET_ATTR = "geometrySelectionSet"
RIG_BLENDSHAPE_SELECTION_SET_ATTR = "blendShapeSelectionSet"

# === Module MetaData Attribute Names ===
MODULE_VERSION_ATTR = "version"
MODULE_SIDE_ATTR = "side"
MODULE_TYPE_ATTR = "moduleType"
MODULE_IS_ENABLED_ATTR = "enabled"
MODULE_ROOT_TRANSFORM_ATTR = "rootTransform"
MODULE_CONTAINER_ATTR = "container"
MODULE_HAS_GUIDE_ATTR = "hasGuide"
MODULE_HAS_GUIDE_CONTROLS_ATTR = "hasGuideControls"
MODULE_HAS_SKELETON_ATTR = "hasSkeleton"
MODULE_HAS_POLISHED_ATTR = "hasPolished"
MODULE_HAS_RIG_ATTR = "hasRig"
MODULE_DESCRIPTOR_ATTR = "componentDescriptor"
MODULE_GROUP_ATTR = "componentGroup"

# === Guide MetaData Attribute Names ===
IS_GUIDE_ATTR = "isGuide"
GUIDE_SHAPE_ATTR = "guideShape"
GUIDE_PIVOT_SHAPE_ATTR = "pivotShape"
GUIDE_PIVOT_COLOR_ATTR = "pivotColor"
GUIDE_SNAP_PIVOT_ATTR = "guideSnapPivot"
GUIDE_SHAPE_PRIMARY_ATTR = "guideShapePrimary"
GUIDE_AUTO_ALIGN_AIM_VECTOR_ATTR = "autoAlignAimVector"
GUIDE_AUTO_ALIGN_UP_VECTOR_ATTR = "autoAlignUpVector"
GUIDE_AUTO_ALIGN_ATTR = "autoAlign"
GUIDE_MIRROR_ATTR = "mirror"
GUIDE_MIRROR_BEHAVIOR_ATTR = "mirrorBehavior"
GUIDE_MIRROR_PLANE_ATTR = "mirrorPlane"
GUIDE_MIRROR_SCALED_ATTR = "mirrorScaled"
GUIDE_DISPLAY_AXIS_SHAPE_ATTR = "displayAxisShape"
GUIDE_CONNECTORS_ATTR = "guideConnectors"


# === Module Descriptor Attribute Names ===
DESCRIPTOR_CACHE_INFO_ATTR = f"{MODULE_DESCRIPTOR_ATTR}.DefCacheInfo"
DESCRIPTOR_CACHE_GUIDE_DAG_ATTR = (
    f"{MODULE_DESCRIPTOR_ATTR}.DescriptorCacheGuideLayerDag"
)
DESCRIPTOR_CACHE_GUIDE_DG_ATTR = f"{MODULE_DESCRIPTOR_ATTR}.DescriptorCacheGuideLayerDg"
DESCRIPTOR_CACHE_GUIDE_SETTINGS_ATTR = (
    f"{MODULE_DESCRIPTOR_ATTR}.DescriptorCacheGuideLayerSettings"
)
DESCRIPTOR_CACHE_GUIDE_METADATA_ATTR = (
    f"{MODULE_DESCRIPTOR_ATTR}.DescriptorCacheGuideLayerMetadata"
)
DESCRIPTOR_CACHE_SKELETON_DAG_ATTR = (
    f"{MODULE_DESCRIPTOR_ATTR}.DescriptorCacheSkeletonLayerDag"
)
DESCRIPTOR_CACHE_SKELETON_SETTINGS_ATTR = (
    f"{MODULE_DESCRIPTOR_ATTR}.DescriptorCacheSkeletonLayerSettings"
)
DESCRIPTOR_CACHE_SKELETON_METADATA_ATTR = (
    f"{MODULE_DESCRIPTOR_ATTR}.DescriptorCacheSkeletonLayerMetadata"
)
DESCRIPTOR_CACHE_INPUT_DAG_ATTR = (
    f"{MODULE_DESCRIPTOR_ATTR}.DescriptorCacheInputLayerDag"
)
DESCRIPTOR_CACHE_INPUT_SETTINGS_ATTR = (
    f"{MODULE_DESCRIPTOR_ATTR}.DescriptorCacheInputLayerSettings"
)
DESCRIPTOR_CACHE_INPUT_METADATA_ATTR = (
    f"{MODULE_DESCRIPTOR_ATTR}.DescriptorCacheInputLayerMetadata"
)
DESCRIPTOR_CACHE_OUTPUT_DAG_ATTR = (
    f"{MODULE_DESCRIPTOR_ATTR}.DescriptorCacheOutputLayerDag"
)
DESCRIPTOR_CACHE_OUTPUT_SETTINGS_ATTR = (
    f"{MODULE_DESCRIPTOR_ATTR}.DescriptorCacheOutputLayerSettings"
)
DESCRIPTOR_CACHE_OUTPUT_METADATA_ATTR = (
    f"{MODULE_DESCRIPTOR_ATTR}.DescriptorCacheOutputLayerMetadata"
)
DESCRIPTOR_CACHE_RIG_DAG_ATTR = f"{MODULE_DESCRIPTOR_ATTR}.DescriptorCacheRigLayerDag"
DESCRIPTOR_CACHE_RIG_DG_ATTR = f"{MODULE_DESCRIPTOR_ATTR}.DescriptorCacheRigLayerDg"
DESCRIPTOR_CACHE_RIG_SETTINGS_ATTR = (
    f"{MODULE_DESCRIPTOR_ATTR}.DescriptorCacheRigLayerSettings"
)
DESCRIPTOR_CACHE_RIG_METADATA_ATTR = (
    f"{MODULE_DESCRIPTOR_ATTR}.DescriptorCacheRigLayerMetadata"
)
DESCRIPTOR_CACHE_SPACE_SWITCHING_ATTR = (
    f"{MODULE_DESCRIPTOR_ATTR}.DescriptorCacheSpaceSwitching"
)

DESCRIPTOR_CACHE_ATTR_NAMES = (
    DESCRIPTOR_CACHE_INFO_ATTR,
    DESCRIPTOR_CACHE_GUIDE_DAG_ATTR,
    DESCRIPTOR_CACHE_GUIDE_SETTINGS_ATTR,
    DESCRIPTOR_CACHE_GUIDE_METADATA_ATTR,
    DESCRIPTOR_CACHE_GUIDE_DG_ATTR,
    DESCRIPTOR_CACHE_SKELETON_DAG_ATTR,
    DESCRIPTOR_CACHE_SKELETON_SETTINGS_ATTR,
    DESCRIPTOR_CACHE_SKELETON_METADATA_ATTR,
    DESCRIPTOR_CACHE_INPUT_DAG_ATTR,
    DESCRIPTOR_CACHE_INPUT_SETTINGS_ATTR,
    DESCRIPTOR_CACHE_INPUT_METADATA_ATTR,
    DESCRIPTOR_CACHE_OUTPUT_DAG_ATTR,
    DESCRIPTOR_CACHE_OUTPUT_SETTINGS_ATTR,
    DESCRIPTOR_CACHE_OUTPUT_METADATA_ATTR,
    DESCRIPTOR_CACHE_RIG_DAG_ATTR,
    DESCRIPTOR_CACHE_RIG_DG_ATTR,
    DESCRIPTOR_CACHE_RIG_SETTINGS_ATTR,
    DESCRIPTOR_CACHE_RIG_METADATA_ATTR,
    DESCRIPTOR_CACHE_SPACE_SWITCHING_ATTR,
)

# === Layer MetaData Attribute Names ===
LAYER_EXTRA_NODES_ATTR = "extraNodes"
LAYER_ROOT_TRANSFORM_ATTR = "rootTransform"
LAYER_CONNECTORS_ATTR = "connectors"
LAYER_CONNECTOR_ID_ATTR = "connectorId"
LAYER_CONNECTOR_NODE_NAME_ATTR = "connectorNodeName"
LAYER_CONNECTOR_NODE_TYPE_ATTR = "connectorNodeType"
LAYER_CONNECTOR_CANDIDATES_ATTR = "connectorCandidates"
LAYER_CONNECTOR_CANDIDATE_NODE_ATTR = "connectorCandidateNode"
LAYER_CONNECTOR_ATTR = "connector"
LAYER_CONNECTOR_START_ATTR = "connectorStart"
LAYER_CONNECTOR_END_ATTR = "connectorEnd"
LAYER_CONNECTOR_ATTRIBUTE_HOLDER_ATTR = "connectorAttributeHolder"
LAYER_SETTING_NODES_ATTR = "settingNodes"
LAYER_SETTING_NODE_ATTR = "settingNode"
LAYER_SETTING_NAME_ATTR = "settingName"
LAYER_TAGGED_NODE_ATTR = "taggedNode"
LAYER_TAGGED_NODE_SOURCE_ATTR = "taggedNodeSource"
LAYER_TAGGED_NODE_ID_ATTR = "taggedNodeId"

# === Geometry Layer MetaData Attribute Names ===
GEOMETRY_LAYER_GEOMETRIES_ATTR = "geometries"
GEOMETRY_LAYER_GEOMETRY_ATTR = "geometry"
GEOMETRY_LAYER_CACHE_GEOMETRY_ATTR = "cache"

# === Modules Layer MetaData Attribute Names ===
MODULES_LAYER_MODULE_GROUPS_ATTR = "componentGroups"
MODULES_LAYER_MODULE_GROUP_NAME_ATTR = "groupName"
MODULES_LAYER_GROUP_MODULES_ATTR = "groupComponents"

# === Guides Layer MetaData Attribute Names ===
GUIDES_LAYER_GUIDES_ATTR = "guides"
GUIDES_LAYER_GUIDE_ID_ATTR = "guideId"
GUIDES_LAYER_GUIDE_NODE_ATTR = "guideNode"
GUIDES_LAYER_SRTS_ATTR = "srts"
GUIDES_LAYER_SHAPE_NODE_ATTR = "shapeNode"
GUIDES_LAYER_SOURCE_GUIDES_ATTR = "sourceGuides"
GUIDES_LAYER_SOURCE_GUIDE_ATTR = "sourceGuide"
GUIDES_LAYER_CONSTRAINT_NODES_ATTR = "constraintNodes"
GUIDES_LAYER_GUIDE_MIRROR_ROTATION_ATTR = "guideMirrorRotation"
GUIDES_LAYER_GUIDE_AUTO_ALIGN_ATTR = "guideAutoAlign"
GUIDES_LAYER_GUIDE_AIM_VECTOR_ATTR = "guideAimVector"
GUIDES_LAYER_GUIDE_UP_VECTOR_ATTR = "guideUpVector"
GUIDES_LAYER_GUIDE_VISIBILITY_ATTR = "guideVisibility"
GUIDES_LAYER_GUIDE_CONTROL_VISIBILITY_ATTR = "guideControlVisibility"
GUIDES_LAYER_PIN_SETTINGS_ATTR = "pinSettings"
GUIDES_LAYER_PINNED_ATTR = "pinned"
GUIDES_LAYER_PINNED_CONSTRAINTS_ATTR = "pinnedConstraints"
GUIDES_LAYER_LIVE_LINK_NODES_ATTR = "liveLinkNodes"
GUIDES_LAYER_LIVE_LINK_IS_ACTIVE_ATTR = "isLiveLinkActive"
GUIDES_LAYER_CONNECTOR_GROUP_ATTR = "connectorGroup"
GUIDES_LAYER_DG_GRAPH_ATTR = "dgGraph"
GUIDES_LAYER_DG_GRAPH_ID_ATTR = "dgGraphId"
GUIDES_LAYER_DG_GRAPH_NODES_ATTR = "dgGraphNodes"
GUIDES_LAYER_DG_GRAPH_NODE_ID_ATTR = "dgGraphNodeId"
GUIDES_LAYER_DG_GRAPH_NODE_ATTR = "dgGraphNode"
GUIDES_LAYER_DG_GRAPH_NAME_ATTR = "dgGraphName"
GUIDES_LAYER_DG_GRAPH_METADATA_ATTR = "dgGraphMetadata"
GUIDES_LAYER_DG_GRAPH_INPUT_NODE_ATTR = "dgGraphInputNode"
GUIDES_LAYER_DG_GRAPH_OUTPUT_NODE_ATTR = "dgGraphOutputNode"

# === Shared Descriptor Keys === #
METADATA_DESCRIPTOR_KEY = "metadata"
DAG_DESCRIPTOR_KEY = "dag"
DG_DESCRIPTOR_KEY = "dg"
SETTINGS_DESCRIPTOR_KEY = "settings"

# === Module Descriptor Keys ===
MODULE_NAME_DESCRIPTOR_KEY = "name"
MODULE_SIDE_DESCRIPTOR_KEY = "side"
MODULE_TYPE_DESCRIPTOR_KEY = "type"
MODULE_VERSION_DESCRIPTOR_KEY = "descriptorVersion"
MODULE_DESCRIPTION_DESCRIPTOR_KEY = "description"
MODULE_PARENT_DESCRIPTOR_KEY = "parent"
MODULE_CONNECTIONS_DESCRIPTOR_KEY = "connections"

MODULE_NAMING_PRESET_DESCRIPTOR_KEY = "namingPreset"
MODULE_SPACE_SWITCH_DESCRIPTOR_KEY = "spaceSwitching"
MODULE_GUIDE_LAYER_DESCRIPTOR_KEY = "guideLayer"
MODULE_INPUT_LAYER_DESCRIPTOR_KEY = "inputLayer"
MODULE_OUTPUT_LAYER_DESCRIPTOR_KEY = "outputLayer"
MODULE_RIG_LAYER_DESCRIPTOR_KEY = "rigLayer"

# === Guide Layer Descriptor Keys ===
GUIDE_MANUAL_ORIENT_DESCRIPTOR_KEY = "manualOrient"
GUIDE_LAYER_GUIDE_VISIBILITY_DESCRIPTOR_KEY = "guideVisibility"
GUIDE_LAYER_GUIDE_CONTROL_VISIBILITY_DESCRIPTOR_KEY = "guideControlVisibility"
GUIDE_LAYER_PIN_SETTINGS_DESCRIPTOR_KEY = "pinSettings"
GUIDE_LAYER_PINNED_DESCRIPTOR_KEY = "pinned"
GUIDE_LAYER_PINNED_CONSTRAINTS_DESCRIPTOR_KEY = "pinnedConstraints"

# === Naming Preset Keys ===
DEFAULT_PRESET_NAME = "modRig"

# === Names for Standard Transform Local Attributes ===
TRANSFORM_ATTRS = ("translate", "rotate", "scale")

# === Default Colors === #
DEFAULT_GUIDE_PIVOT_COLOR = (1.0, 1.0, 0.0)
DEFAULT_SKELETON_JOINT_COLOR = (0.0, 0.001, 0.117)

# === Guide Alignment === #
DEFAULT_AIM_VECTOR = (1.0, 0.0, 0.0)
DEFAULT_UP_VECTOR = (0.0, 1.0, 0.0)

# === Guide Types === #
GUIDE_TYPE_NURBS_CURVE = 0
GUIDE_TYPE_NURBS_SURFACE = 1

# === Build Scripts === #


class BuildScriptFunctionType(enum.IntEnum):
    """Enumeration of the different types of build script functions."""

    Guide = enum.auto()
    Skeleton = enum.auto()
    Rig = enum.auto()
    Polish = enum.auto()
    DeleteGuideLayer = enum.auto()
    DeleteSkeletonLayer = enum.auto()
    DeleteRigLayer = enum.auto()
    DeleteModule = enum.auto()
    DeleteModules = enum.auto()
    DeleteRig = enum.auto()


BUILD_SCRIPT_FUNCTION_MAPPING = {
    BuildScriptFunctionType.Guide: ("pre_guide_build", "post_guide_build"),
    BuildScriptFunctionType.Skeleton: ("pre_skeleton_build", "post_skeleton_build"),
    BuildScriptFunctionType.Rig: ("pre_rig_build", "post_rig_build"),
    BuildScriptFunctionType.Polish: ("pre_polish_build", "post_polish_build"),
    BuildScriptFunctionType.DeleteGuideLayer: ("pre_delete_guide_layer", None),
    BuildScriptFunctionType.DeleteSkeletonLayer: ("pre_delete_skeleton_layer", None),
    BuildScriptFunctionType.DeleteRigLayer: ("pre_delete_rig_layer", None),
    BuildScriptFunctionType.DeleteModule: ("pre_delete_module", None),
    BuildScriptFunctionType.DeleteModules: ("pre_delete_modules", None),
    BuildScriptFunctionType.DeleteRig: ("pre_delete_rig", None),
}
