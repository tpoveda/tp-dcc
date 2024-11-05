from __future__ import annotations

FILTERS_TOOLTIP = "Filter renaming with the following options."
NODES_FILTER_TOOLTIP = """Only rename these object types."""
AUTO_SHAPES_TOOLTIP = """When checked, shape nodes will be renamed with the transform names.
Example: `pCube_001` renames it's shape node `pCube_001Shape`."""
RADIO_NAMES_TOOLTIPS = [
    """Rename based on selected objects/nodes.""",
    """Rename the selected object and it's hierarchy below.""",
    """Rename all objects/nodes in the scene.""",
]
BASE_NAME_TOOLTIP = (
    """Select objects in order, objects will be renamed with numeric suffixing."""
)
NUMERIC_PADDING_TOOLTIP = """Numeric padding of the trailing numbers: 
    1: 1, 2, 3, 4, ...
    2: 01, 02, 03, 04, ...
    3: 001, 002, 003, 004, ..."""
SEARCH_REPLACE_TOOLTIP = """Search and replace selected object/node names.
Text in the first text box gets replaced by the second."""
PREFIX_TOOLTIP = """Add a prefix to the selected object/node names."""
PREFIXES_TOOLTIP = """Predefined suffixes to add to the selected object/node names."""
SUFFIX_TOOLTIP = """Add a suffix to the selected object/node names."""
SUFFIXES_TOOLTIP = """Predefined suffixes to add to the selected object/node names."""
REMOVE_PREFIX_TOOLTIP = """Removes the prefix separated by an underscore '_'
'test_pCube1_geo' becomes 'pCube1_geo'"""
REMOVE_SUFFIX_TOOLTIP = """Removes the suffix separated by an underscore '_'
'test_pCube1_geo' becomes 'test_pCube1'"""
INDEX_FRAME_TOOLTIP = """Add/Edit a index, uncerscore separated
    Example: 01_02_03-02_0-1, ..."""
ADD_AT_INDEX_TOOLTIP = """Add _text_ with index value. Examples:
    1: Adds a prefix.
    -1. Adds a suffix.
    2: Adds after the first underscore.
    -2: Adds before the last underscore."""
INSERT_INDEX_COMBO_BOX_TOOLTIP = """Insert:
    - 'geo' at 2: 'object_char_L' become 'object_geo_char_L'
    Replace:
    - 'geo' at -2: 'object_char_L' becomes 'object_geo_L'
    Remove:
    -2: 'object_char_L' becomes 'object_L'"""
INDEX_SHUFFLE_TOOLTIP = """Shuffle the item part of a name, separated by underscores '_'.
The index value is artist friendly and starts at 1.
Negative numbres start at the end values.
Examples:
    - 'object_geo_01' with index -1 (left arrow) will become 'object_01_geo'
    - 'object_geo_01' with index 2 (right arrow) will become 'geo_object_01'"""
RENUMBER_TOOLTIP = """Renumber of change numerical padding.
Replace: Renumbers in selected or hierarchy order. 'object1' becomes 'object_01'.
Append: Renumbers in selected or hierarchy order. 'object1' becomes object1_01'.
Change Padding: Keeps the number and changes padding. 'char1_object3' becomes 'char1_object_03'.
Note that change padding only affects the trailing numbers ('object3' not object3_geo')."""
RENUMBER_PADDING_TOOLTIP = """Numeric padding of the trailing number:
1: 1, 2, 3, 4, ...
2: 01, 02, 03, 04, ...
3: 001, 002, 003, 004, ..."""
REMOVE_ALL_NUMBERS_TOOLTIP = """Remove all numbers from object names. 'object_01' becomes 'object'.
Note that names must not clash with other nodes within scene."""
REMOVE_TAIL_NUMBERS_TOOLTIP = """Remove trailing numbers from object names. 'object1_01' becomes 'object1'.
Note that names must not clash with other nodes within scene."""
NAMESPACE_TOOLTIP = """Edit, Add or Delete namespace (name suffix followed by a colon).
Example: `object:geo` > `object` is the namespace.
Note that namespaces have hierarchies, use the `Namespace Editor` for renaming and advanced features."""
DELETE_NAMESPACE_TOOLTIP = """Deletes the selected namespace/s for the whole scene. Select objects and run.
'scene:geo1' becomes 'geo1'.
This will delete the namespace for all objects in the scene."""
DELETE_UNUSED_NAMESPACES_TOOLTIP = """Delete all/empty namespaces in the scene."""
OPEN_NAMESPACE_EDITOR_TOOLTIP = """Open the Namespace Editor."""
OPEN_REFERENCE_EDITOR_TOOLTIP = """Open the Reference Editor."""
AUTO_SUFFIX_TOOLTIP = """Automatically add a suffix to the selected object/node names based on their types.
- 'pCube1' becomes 'pCube1_geo'.
- 'locator1' becomes 'locator1_loc'"""
MAKE_UNIQUE_NAME_TOOLTIP = """Make the selected object/node names unique by adding a numeric suffix. 
If a name is duplicated it will be renamed with an incremental number. Example:
`myName` becomes `myName_01`
`myName2` becomes `myName3`
`myName_04` becomes `myName_05`"""
