from __future__ import annotations

AUTO_LEFT_RIGHT_CHECKBOX_TOOLTIP = """Will automatically try to also find the right side of the given object.
See `Source/Target Rename Options` to set the left/right settings.
Useful for matching full rig setups."""

SOURCE_NAMESPACE_STRING_EDIT_TOOLTIP = """Specify the namespace to be added to all source names.

    - Example: `characterX` will be added to the name (e.g. `characterX:joint1`)."""

SOURCE_LEFT_RIGHT_STRING_EDIT_TOOLTIP = """Specify the left and right identifiers. `Auto Right Side` must be on.

    - Example: `_L`, `R`
    - `joint1_L_jnt` finds `joint1_R_jnt`"""

SOURCE_LEFT_RIGHT_FORCE_PREFIX_CHECKBOX_TOOLTIP = """Forces the left and right identifier to always prefix the name. `
Auto Right Side` must be on.

    - Example: `l`, `r`
    - `l_joint1_jnt` finds `r_joint1_jnt`"""

SOURCE_LEFT_RIGHT_FORCE_SUFFIX_CHECKBOX_TOOLTIP = """Forces the left and right identifier to always suffix the name. 
`Auto Right Side` must be on.

    - Example: `l`, `r`
    - `joint1_jnt_l` finds `joint1_jnt_r`"""

SOURCE_LEFT_RIGHT_SEPARATOR_ON_BORDER_CHECKBOX_TOOLTIP = """While finding the right side an underscore must be on the left or right side of the name.
`Auto Right Side` must be on.

    - Example: '`l`, `r`
    - `joint1_l` finds `joint1_r` or `l_joint1` finds `r_joint1`"""

SOURCE_PREFIX_STRING_EDIT_TOOLTIP = """Specify the prefix to be added to all source names.

    - Example: `prefix_` will be added to the name (e.g. `prefix_joint1`)."""

SOURCE_SUFFIX_STRING_EDIT_TOOLTIP = """Specify the suffix to be added to all source names.

    - Example: `_suffix` will be added to the name (e.g. `joint1_suffix`)."""

MISC_SETTINGS_BUTTON_TOOLTIP = """Misc Settings: 
    - Save and import settings to the scene: Saves data to a node name `noddleSkeletonToRig_networkNode`.
    - Delete the settings from the scene: Deletes the `noddleSkeletonToRig_networkNode`.
    - Reset the UI to defaults.
    - Import and Export column data to disk (JSON)."""

CLEAR_BUTTON_TOOLTIP = """
Clears all the rows in the table."""

ADD_BUTTON_TOOLTIP = """Adds new row.
Select objects sources and then targets to add to the table.
Can select multiple sources and then multiple targets."""

REMOVE_BUTTON_TOOLTIP = """Removes teh selected row/s from the table."""

BUILD_FROM_SKELETON_BUTTON_TOOLTIP = """Builds a Noddle rig from a given skeleton type in the scene.
The source joints are matched to the target Noddle guides IDs.

Use the name options to add namespaces, prefixes and left/right identifiers."""
