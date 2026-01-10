"""Constants for the metadata system.

This module contains all attribute names and type mappings used by the
metadata network system.
"""

from __future__ import annotations

from ..om import attributetypes

# =============================================================================
# Attribute Names
# =============================================================================

# Attribute storing the metaclass type identifier.
META_CLASS_ATTR_NAME: str = "tpMetaClass"

# Attribute storing the version of the metaclass.
META_VERSION_ATTR_NAME: str = "tpMetaVersion"

# Array attribute storing connections to parent metanodes.
META_PARENT_ATTR_NAME: str = "tpMetaParent"

# Array attribute storing connections to child meta nodes.
META_CHILDREN_ATTR_NAME: str = "tpMetaChildren"

# Attribute storing an optional tag for the metanode.
META_TAG_ATTR_NAME: str = "tpMetaTag"

# Attribute storing a unique identifier (GUID) for the meta node.
META_GUID_ATTR_NAME: str = "tpMetaGuid"


# =============================================================================
# Type Mappings
# =============================================================================

# Mapping from Python types to Maya attribute type constants.
# Used for automatic attribute creation with correct Maya types.
TYPE_TO_MAYA_ATTR: dict[type, int] = {
    str: attributetypes.kMFnDataString,
    int: attributetypes.kMFnNumericInt,
    float: attributetypes.kMFnNumericDouble,
    bool: attributetypes.kMFnNumericBoolean,
    list: attributetypes.kMFnNumeric3Double,
    tuple: attributetypes.kMFnNumeric3Double,
}

# Mapping from Maya attribute type constants to Python types.
# Used for converting attribute values to appropriate Python types.
MAYA_ATTR_TO_TYPE: dict[int, type] = {
    attributetypes.kMFnDataString: str,
    attributetypes.kMFnNumericInt: int,
    attributetypes.kMFnNumericDouble: float,
    attributetypes.kMFnNumericFloat: float,
    attributetypes.kMFnNumericBoolean: bool,
    attributetypes.kMFnNumeric3Double: list,
    attributetypes.kMFnNumeric3Float: list,
}


# =============================================================================
# Reserved Attribute Names
# =============================================================================

# Set of attribute names that are reserved by the metadata system.
# These should not be used as user-defined attribute names.
RESERVED_ATTR_NAMES: frozenset[str] = frozenset(
    {
        META_CLASS_ATTR_NAME,
        META_VERSION_ATTR_NAME,
        META_PARENT_ATTR_NAME,
        META_CHILDREN_ATTR_NAME,
        META_TAG_ATTR_NAME,
        META_GUID_ATTR_NAME,
    }
)
