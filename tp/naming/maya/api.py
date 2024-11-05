from __future__ import annotations

import enum
import logging

from maya import cmds

from tp.maya.cmds import filtertypes
from tp.maya.cmds.nodeutils import naming

logger = logging.getLogger(__name__)


class PrefixSuffixType(enum.Enum):
    """
    Enum that defines the type of prefix or suffix to apply to the given object.
    """

    Prefix = "prefix"
    Suffix = "suffix"


class EditIndexMode(enum.Enum):
    """
    Enum that defines the mode to edit the index item.
    """

    Insert = "insert"
    Replace = "replace"
    Remove = "remove"


def rename_shape_nodes(
    node_name: str, uuid: str | None = None, return_long_name: bool = False
) -> list[str]:
    """
    Renames the shape nodes of the given transform/joint node.

    :param node_name: node name to rename the shape nodes from.
    :param uuid: optional UUID for the renaming. If given, it will be used for the renaming instead of the object name.
    :param return_long_name: whether to return the long name of the object.
    :return: list of new shape node names.
    """

    new_shape_names: list[str] = []
    node_name = node_name if not uuid else cmds.ls(uuid, long=True)[0]
    shapes = cmds.listRelatives(node_name, shapes=True, fullPath=True)
    if not shapes:
        return new_shape_names
    short_name = naming.get_short_name(node_name)
    shape_uuids = cmds.ls(shapes, uuid=True)
    for uuid in shape_uuids:
        new_shape = cmds.rename(
            cmds.ls(uuid, long=True)[0], f"{short_name}Shape", ignoreShape=True
        )
        new_shape_names.append(
            naming.get_long_name_from_short_name(new_shape)
            if return_long_name
            else new_shape
        )

    return new_shape_names


def rename_shape_nodes_from_list(node_names: list[str], return_long_name: bool = False):
    """
    Renames the shape nodes of the given transform/joint nodes from the given list.

    :param node_names: list of node names to rename the shape nodes from.
    :param return_long_name: whether to return the long name of the object.
    :return: list of new shape node names.
    """

    new_shape_names: list[str] = []
    for node_name in node_names:
        new_shape_names.extend(
            rename_shape_nodes(node_name, return_long_name=return_long_name)
        )

    return new_shape_names


def safe_rename(
    name: str,
    new_name: str,
    uuid: str,
    rename_shape: bool = True,
    return_long_name: bool = True,
) -> str:
    """
    Safe rename given object name with the new name. The safe renaming checks for:
         - If given, UUIDs are used for the renaming.
         - Checks for invalid names.
         - Checks for numbers starting a name.
         - Checks for locked nodes.

    :param name: object name to rename.
    :param new_name: new name (can be in long format).
    :param uuid: optional UUID for the renaming. If given, it will be used for the renaming instead of the object name.
    :param rename_shape: whether to rename the shape nodes as well.
    :param return_long_name: whether to return the long name of the object.
    :return: new object name.
    """

    name = cmds.ls(uuid, long=True)[0] if uuid else name

    short_name = naming.get_short_name(name)
    new_short_name = naming.get_short_name(new_name)
    if short_name == new_short_name:
        if rename_shape:
            rename_shape_nodes(name, uuid=None)
        return name

    if cmds.lockNode(name, query=True)[0]:
        logger.warning(f"Node {name} is locked and cannot be renamed.")
        return name

    if new_short_name[0].isdigit():
        logger.warning("Maya node names cannot start with numbers.")
        return name
    if ":" in new_short_name:
        new_pure_name = new_short_name.split(":")[-1]
        if new_pure_name[0].isdigit():
            logger.warning("Maya names cannot start with numbers.")
            return name

    renamed_name = cmds.rename(name, new_short_name, ignoreShape=True)
    if rename_shape:
        rename_shape_nodes(renamed_name, uuid=None)

    return (
        naming.get_long_name_from_short_name(renamed_name)
        if return_long_name
        else renamed_name
    )


def safe_rename_objects(
    objects_to_rename: list[str],
    new_names: list[str],
    uuids: list[str] | None = None,
    rename_shape: bool = True,
    return_long_names: bool = True,
) -> list[str]:
    """
    Safe rename list of given object names with the new names. The safe renaming checks for:
         - If given, UUIDs are used for the renaming.
         - Checks for invalid names.
         - Checks for numbers starting a name.
         - Checks for locked nodes.

    :param objects_to_rename: list of object names to rename.
    :param new_names: list of new names (can be in long format).
    :param uuids: optional list of UUIDs for the renaming. If given, it will be used for the renaming instead of the
        object names.
    :param rename_shape: whether to rename the shape nodes as well.
    :param return_long_names: whether to return the long names of the objects.
    :return: list of new object names.
    """

    renamed_object_names: list[str] = []
    uuids = uuids or cmds.ls(objects_to_rename, uuid=True)
    for i, name in enumerate(objects_to_rename):
        renamed_object_names.append(
            safe_rename(
                name,
                new_names[i],
                uuids[i],
                rename_shape=rename_shape,
                return_long_name=return_long_names,
            )
        )

    return renamed_object_names


def renumber_objects_with_single_name(
    new_name: str,
    objects_to_rename: list[str],
    padding: int = 2,
    rename_shape: bool = True,
) -> list[str]:
    """
    Renames the objects in the list to be:
        - 'newName_01'
        - 'newName_02'
        - 'newName_03'
        - ...

    :param new_name: new name suffix to name all given objects.
    :param objects_to_rename: list of node names to rename.
    :param padding: the number of padding to use for the numbering (1=1, 2=01, 3=001, ...).
    :param rename_shape: whether to rename the shape nodes as well.
    :return: lst of new node names.
    """

    new_names: list[str] = []
    for i in range(len(objects_to_rename)):
        new_names.append("_".join([new_name, str(i + 1).zfill(padding)]))

    return safe_rename_objects(objects_to_rename, new_names, rename_shape=rename_shape)


def rename_selected_objects(
    base_name: str,
    nice_name_type: str,
    padding: int = 2,
    rename_shape: bool = True,
    hierarchy: bool = False,
) -> list[str]:
    """
    Renames the selected nodes in the selection order to be:
        - 'baseName_01'
        - 'baseName_02'
        - 'baseName_03'
        - ...

    :param base_name: new base name for all the objects.
    :param nice_name_type: the type of the object to rename.
    :param padding: the number of padding to use for the numbering (1=1, 2=01, 3=001, ...).
    :param rename_shape: whether to rename the shape nodes as well.
    :param hierarchy: whether to rename the hierarchy of the selected nodes.
    :return: lst of new node names.
    """

    selected_nodes = filtertypes.filter_by_type(
        nice_name_type,
        search_hierarchy=hierarchy,
        selection_only=True,
        transforms_only=True,
        include_constraints=True,
    )
    if not selected_nodes:
        return []

    # Rename twice to avoid clashing issues, when the objects aren't in hierarchies.
    renamed_names = renumber_objects_with_single_name(
        "tpTempXXX", selected_nodes, padding=padding, rename_shape=rename_shape
    )
    return renumber_objects_with_single_name(
        base_name, renamed_names, padding=padding, rename_shape=rename_shape
    )


def search_replace_name(
    name: str,
    search_text: str,
    replace_text: str,
    uuid: str | None = None,
    rename_shape: bool = True,
) -> str:
    """
    Renames the given node name with the given replace text in the given search text.

    :param name: node name to rename.
    :param search_text: text to search for, this text will be replaced.
    :param replace_text: replace text that replaces the search text.
    :param uuid: optional UUID for the renaming. If given, it will be used for the renaming instead of the object name.
    :param rename_shape: whether to rename the shape nodes as well.
    :return: new node name.
    """

    long_prefix, namespace, base_name = naming.name_part_types(name)
    base_name = base_name.replace(search_text, replace_text)
    new_name = naming.join_name_parts(long_prefix, namespace, base_name)

    return safe_rename(name, new_name, uuid=uuid, rename_shape=rename_shape)


def search_replace_objects(
    objects_to_rename: list[str],
    search_text: str,
    replace_text: str,
    rename_shape: bool = True,
) -> list[str]:
    """
    Renames a list of node names with the given replace text in the given search text.

    :param objects_to_rename: list of node names to rename.
    :param search_text: text to search for, this text will be replaced.
    :param replace_text: replace text that replaces the search text.
    :param rename_shape: whether to rename the shape nodes as well.
    :return: list of new node names.
    """

    uuids = cmds.ls(objects_to_rename, uuid=True)
    for i, object_to_rename in enumerate(objects_to_rename):
        search_replace_name(
            object_to_rename,
            search_text,
            replace_text,
            uuid=uuids[i],
            rename_shape=rename_shape,
        )

    return cmds.ls(uuids, long=True)


def search_replace_filtered_type(
    search_text: str,
    replace_text: str,
    nice_name_type: str,
    rename_shape: bool = True,
    search_hierarchy: bool = False,
    selection_only: bool = True,
    dag: bool = False,
    remove_maya_defaults: bool = True,
    transform_only: bool = True,
) -> list[str]:
    """
    Search and replace the given text in the selected objects of the given type.

    :param search_text: text to search for.
    :param replace_text: text to replace with.
    :param nice_name_type: the type of the object to rename.
    :param rename_shape: whether to rename the shape nodes as well.
    :param search_hierarchy: whether to search the hierarchy of the selected nodes.
    :param selection_only: whether to search only the selected nodes.
    :param dag: whether to search only the DAG nodes.
    :param remove_maya_defaults: whether to remove Maya default names.
    :param transform_only: whether to search only transform nodes.
    :return: list of new node names.
    """

    selected_nodes = filtertypes.filter_by_type(
        nice_name_type,
        search_hierarchy=search_hierarchy,
        selection_only=selection_only,
        dag=dag,
        remove_maya_defaults=remove_maya_defaults,
        transforms_only=transform_only,
        include_constraints=True,
    )
    if not selected_nodes:
        return []

    return search_replace_objects(
        selected_nodes, search_text, replace_text, rename_shape=rename_shape
    )


def check_suffix_prefix_exists(
    name: str, suffix_prefix: str, suffix_prefix_type: PrefixSuffixType
) -> bool:
    """
    Checks whether the given suffix or prefix exists.

    :param name: name of the object to be renamed.
    :param suffix_prefix: suffix or prefix to check.
    :param suffix_prefix_type: the type of suffix or prefix to check.
    :return: True if a suffix or prefix is found; False otherwise.
    :raises ValueError: If the given suffix/prefix type is invalid.
    """

    if suffix_prefix_type == PrefixSuffixType.Prefix:
        _, _, base_name = naming.name_part_types(name)
        base_name_list = base_name.split("_")
        return True if base_name_list[0] == suffix_prefix.replace("_", "") else False
    elif suffix_prefix_type == PrefixSuffixType.Suffix:
        name_split = name.split("_")
        return True if name_split[-1] == suffix_prefix.replace("_", "") else False
    else:
        raise ValueError(f"Invalid suffix/prefix type: {suffix_prefix_type}")


def prefix_suffix_object(
    object_to_rename: str,
    prefix_suffix: str,
    prefix_suffix_type: PrefixSuffixType = PrefixSuffixType.Suffix,
    uuid: str | None = None,
    add_underscore: bool = True,
    rename_shape: bool = True,
    check_existing_suffix_prefix: bool = True,
):
    """
    Prefixes or suffixes the given object name with the given prefix or suffix type.

    :param object_to_rename: node name to rename.
    :param prefix_suffix: the prefix or suffix to apply.
    :param prefix_suffix_type: the type of prefix or suffix to apply.
    :param uuid: optional UUID for the renaming. If given, it will be used for the renaming instead of the object name.
    :param add_underscore: whether to add an underscore between the prefix/suffix and the object name.
    :param rename_shape: whether to rename the shape nodes as well.
    :param check_existing_suffix_prefix: whether to check for existing suffix/prefix and remove them.
    :return: new node name.
    :raises ValueError: If the given suffix/prefix type is invalid.
    """

    suffix_prefix_exists = (
        check_suffix_prefix_exists(object_to_rename, prefix_suffix, prefix_suffix_type)
        if check_existing_suffix_prefix
        else False
    )

    if prefix_suffix_type == PrefixSuffixType.Prefix:
        if not suffix_prefix_exists:
            if add_underscore:
                prefix_suffix = f"{prefix_suffix}_"
            long_prefix, namespace, base_name = naming.name_part_types(object_to_rename)
            base_name = "".join([prefix_suffix, base_name])
            new_name = naming.join_name_parts(long_prefix, namespace, base_name)
        else:
            new_name = object_to_rename
    elif prefix_suffix_type == PrefixSuffixType.Suffix:
        if not suffix_prefix_exists:
            if add_underscore:
                prefix_suffix = f"_{prefix_suffix}"
            new_name = "".join([object_to_rename, prefix_suffix])
        else:
            new_name = object_to_rename
    else:
        raise ValueError(f"Invalid suffix/prefix type: {prefix_suffix_type}")

    return safe_rename(object_to_rename, new_name, uuid=uuid, rename_shape=rename_shape)


def prefix_suffix_objects(
    objects_to_rename: list[str],
    prefix_suffix: str,
    prefix_suffix_type: PrefixSuffixType = PrefixSuffixType.Suffix,
    add_underscore: bool = False,
    rename_shape: bool = True,
    check_existing_suffix_prefix: bool = True,
) -> list[str]:
    """
    Prefixes or suffixes the given object names with the given prefix or suffix type.

    :param objects_to_rename: list of node names to rename.
    :param prefix_suffix: the prefix or suffix to apply.
    :param prefix_suffix_type: the type of prefix or suffix to apply.
    :param add_underscore: whether to add an underscore between the prefix/suffix and the object name.
    :param rename_shape: whether to rename the shape nodes as well.
    :param check_existing_suffix_prefix: whether to check for existing suffix/prefix and remove them.
    :return: list of new node names.
    """

    uuids = cmds.ls(objects_to_rename, uuid=True)
    for i, object_to_rename in enumerate(objects_to_rename):
        prefix_suffix_object(
            object_to_rename,
            prefix_suffix,
            prefix_suffix_type=prefix_suffix_type,
            uuid=uuids[i],
            add_underscore=add_underscore,
            rename_shape=rename_shape,
            check_existing_suffix_prefix=check_existing_suffix_prefix,
        )

    return cmds.ls(uuids, long=True)


def prefix_suffix_filtered_type(
    prefix_suffix: str,
    nice_name_type: str,
    prefix_suffix_type: PrefixSuffixType,
    rename_shape: bool = True,
    search_hierarchy: bool = False,
    selection_only: bool = True,
    dag: bool = False,
    remove_maya_defaults: bool = True,
    transforms_only: bool = True,
):
    """
    Prefixes or suffixes the selected objects of the given type.
    If `nice_name_type` is given, this function will filter and prefix/suffix based on the type.

    :param prefix_suffix: the prefix or suffix to apply.
    :param nice_name_type: the type of the object to rename.
    :param prefix_suffix_type: the type of prefix or suffix to apply.
    :param rename_shape: whether to rename the shape nodes as well.
    :param search_hierarchy: whether to search the hierarchy of the selected nodes.
    :param selection_only: whether to search only the selected nodes.
    :param dag: whether to search only the DAG nodes.
    :param remove_maya_defaults: whether to remove Maya default names.
    :param transforms_only: whether to search only transform nodes.
    :return: list of new node names.
    """

    selected_nodes = filtertypes.filter_by_type(
        nice_name_type,
        search_hierarchy=search_hierarchy,
        selection_only=selection_only,
        dag=dag,
        remove_maya_defaults=remove_maya_defaults,
        transforms_only=transforms_only,
        include_constraints=True,
    )
    if not selected_nodes:
        return []

    return prefix_suffix_objects(
        selected_nodes,
        prefix_suffix,
        prefix_suffix_type=prefix_suffix_type,
        rename_shape=rename_shape,
        add_underscore=False,
    )


def check_index_in_name_parts(name_parts: list[str], index: int) -> bool:
    """
    Returns whether an index in the given name parts is found.

    :param name_parts: list of name parts separated by a separator character (usually, an underscore).
    :param index: index number, that can be negative.
    :return:  True if the index exits in the name parts; False otherwise.
    """

    list_length = len(name_parts)
    check_length = abs(index) if index < 0 else index + 1
    return False if check_length > list_length else True


def edit_index_item_object(
    object_to_rename: str,
    index: int,
    text: str = "",
    mode: EditIndexMode = EditIndexMode.Insert,
    separator="_",
    rename_shape: bool = True,
    uuid: str | None = None,
) -> str:
    """
    Split given node name by the given separator and edit the position by given index number.

    Supported modes:
        - Insert: inserts (add) a new value into that position.
        - Replace: overwrites the text at that position.
        - Remove: removes the text by index at that position.

    Examples:
        'pCube_01_geo' (index 0 = 'pCube', index 1 = '01', index 2 = 'geo')
        with index=1 and text='variantA' the result would be:
            - Insert: 'pCube_variantA_01_geo'
            - Replace: 'pCube_variantA_geo'
            - Remove: 'pCube_01_geo'

    :param object_to_rename: node name to rename.
    :param index: the index to edit.
    :param text: the text to insert or replace.
    :param mode: the mode to edit the index item.
    :param separator: the separator to use for the index item.
    :param rename_shape: whether to rename the shape nodes as well.
    :param uuid: optional UUID for the renaming. If given, it will be used for the renaming instead of the object name.
    :return: new node name.
    :raises ValueError: If the given mode is invalid.
    """

    _, namespace, base_name = naming.name_part_types(object_to_rename)
    base_name_list = base_name.split(separator)

    # If the given is not valid, we return the object name.
    if not check_index_in_name_parts(base_name_list, index):
        return object_to_rename

    if mode == EditIndexMode.Insert:
        if not text:
            return object_to_rename
        neg = False
        if index < 0:
            index += 1
            neg = True
        if index == 0 and neg:
            base_name_list.append(text)
        elif index == 0 and not neg:
            base_name_list = [text] + base_name_list
        else:
            base_name_list.insert(index, text)
    elif mode == EditIndexMode.Replace:
        if not text:
            del base_name_list[index]
        else:
            base_name_list[index] = text
    elif mode == EditIndexMode.Remove:
        if len(base_name_list) == 1:
            logger.warning(
                f"There are not enough name parts to rename: {base_name_list[0]}"
            )
            return object_to_rename
        del base_name_list[index]
    else:
        raise ValueError(f"Invalid mode: {mode}")

    base_name = separator.join(base_name_list)
    new_name = naming.join_name_parts("", namespace, base_name)
    return safe_rename(object_to_rename, new_name, uuid=uuid, rename_shape=rename_shape)


def edit_index_item_objects(
    objects_to_rename: list[str],
    index: int,
    text: str = "",
    mode: EditIndexMode = EditIndexMode.Insert,
    separator: str = "_",
    rename_shape: bool = True,
) -> list[str]:
    """
    Split node names by the given separator and edit the position by given index number.

    Supported modes:
        - Insert: inserts (add) a new value into that position.
        - Replace: overwrites the text at that position.
        - Remove: removes the text by index at that position.

    Examples:
        'pCube_01_geo' (index 0 = 'pCube', index 1 = '01', index 2 = 'geo')
        with index=1 and text='variantA' the result would be:
            - Insert: 'pCube_variantA_01_geo'
            - Replace: 'pCube_variantA_geo'
            - Remove: 'pCube_01_geo'

    :param objects_to_rename: list of node names to rename.
    :param index: the index to edit.
    :param text: the text to insert or replace.
    :param mode: the mode to edit the index item.
    :param separator: the separator to use for the index item.
    :param rename_shape: whether to rename the shape nodes as well.
    :return: list of new node names.
    """

    uuids = cmds.ls(objects_to_rename, uuid=True)
    for i, object_to_rename in enumerate(objects_to_rename):
        edit_index_item_object(
            object_to_rename,
            index,
            text=text,
            mode=mode,
            separator=separator,
            rename_shape=rename_shape,
            uuid=uuids[i],
        )

    return cmds.ls(uuids, long=True)


def edit_index_item_filtered_type(
    index: int,
    nice_name_type: str,
    text: str = "",
    mode: EditIndexMode = EditIndexMode.Insert,
    separator: str = "_",
    rename_shape: bool = True,
    search_hierarchy: bool = False,
    selection_only: bool = True,
    dag: bool = False,
    remove_maya_defaults: bool = True,
    transform_only: bool = True,
) -> list[str]:
    """
    Split node names by the given separator and edit the position by given index number.
    If `nice_name_type` is given, this function will filter and edit the index item based on the type.

    Supported modes:
        - Insert: inserts (add) a new value into that position.
        - Replace: overwrites the text at that position.
        - Remove: removes the text by index at that position.

    Examples:
        'pCube_01_geo' (index 0 = 'pCube', index 1 = '01', index 2 = 'geo')
        with index=1 and text='variantA' the result would be:
            - Insert: 'pCube_variantA_01_geo'
            - Replace: 'pCube_variantA_geo'
            - Remove: 'pCube_01_geo'

    :param index: the index to edit.
    :param nice_name_type: the type of the object to rename.
    :param text: the text to insert or replace.
    :param mode: the mode to edit the index item.
    :param separator: the separator to use for the index item.
    :param rename_shape: whether to rename the shape nodes as well.
    :param search_hierarchy: whether to search the hierarchy of the selected nodes.
    :param selection_only: whether to search only the selected nodes.
    :param dag: whether to search only the DAG nodes.
    :param remove_maya_defaults: whether to remove Maya default names.
    :param transform_only: whether to search only transform nodes.
    :return: list of new node names.
    """

    selected_nodes = filtertypes.filter_by_type(
        nice_name_type,
        search_hierarchy=search_hierarchy,
        selection_only=selection_only,
        dag=dag,
        remove_maya_defaults=remove_maya_defaults,
        transforms_only=transform_only,
        include_constraints=True,
    )
    if not selected_nodes:
        return []

    return edit_index_item_objects(
        selected_nodes,
        index,
        text=text,
        mode=mode,
        separator=separator,
        rename_shape=rename_shape,
    )
