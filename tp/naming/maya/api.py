from __future__ import annotations

import re
import logging

from maya import cmds

from tp.maya.cmds import filtertypes
from tp.maya.cmds.nodeutils import naming

from ..consts import PrefixSuffixType, EditIndexMode

logger = logging.getLogger(__name__)


def trailing_number(name: str) -> tuple[str, int | None, int]:
    """
    Returns the trailing number of a string, the name with the number removed, and the padding of the number.

    Examples:
        - 'shaderName' returns ('shaderName', None, 0).
        - 'shaderName2' returns ('shaderName', 2, 1).
        - 'shader1_Name04' returns ('shader1_Name', 4, 2).
        - 'shaderName_99' returns ('shaderName_', 99, 2).
        - shaderName_0009' returns ('shaderName_', 9, 4).

    :param name: string to get the trailing number from.
    :return: name without the trailing number, the trailing number, and the padding of the number.
    """

    result = re.search(r"\d+$", name)
    if not result:
        return name, None, 0

    number_as_string = result.group()
    name_numberless = name[: -len(number_as_string)]
    padding = len(number_as_string)

    return name_numberless, int(number_as_string), padding


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
    transforms_only: bool = True,
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

    return edit_index_item_objects(
        selected_nodes,
        index,
        text=text,
        mode=mode,
        separator=separator,
        rename_shape=rename_shape,
    )


def shuffle_item_by_index(
    object_to_rename: str,
    index: int,
    offset: int = 1,
    uuid: str | None = None,
    rename_shape: bool = True,
    separator: str = "_",
) -> str:
    """
    Shuffle the position of an item by the given index number.

    Index is the text to move/shuffle, can be negative number.

    Examples:
        'pCube_01_geo' (index 0 = 'pCube', index 1 = '01', index 2 = 'geo')

    :param object_to_rename: name of the object to rename.
    :param index: the index to edit.
    :param offset: the offset to shuffle the index (1 if forward and -1 is backwards).
    :param uuid: optional UUID for the renaming. If given, it will be used for the renaming instead of the object name.
    :param rename_shape: whether to rename the shape nodes as well.
    :param separator: the separator to use for the index item.
    :return: new node name.
    """

    object_to_rename = cmds.ls(uuid, long=True)[0] if uuid else object_to_rename
    long_prefix, namespace, base_name = naming.name_part_types(object_to_rename)
    base_name_parts = base_name.split(separator)

    # If no parts to shuffle, we return the object name.
    if len(base_name_parts) == 1 or offset == 0:
        return object_to_rename

    found_index = check_index_in_name_parts(base_name_parts, index)
    if not found_index:
        return object_to_rename

    # Cannot offset from 0 into a negative number.
    if index == 0 and offset < 0:
        return object_to_rename

    # Cannot offset from -1 into a positive number.
    if index == -1 and offset > 0:
        return object_to_rename

    index_part = base_name_parts[index]
    base_name_parts[index] = base_name_parts[index + offset]
    base_name_parts[index + offset] = index_part
    new_name = naming.join_name_parts(long_prefix, namespace, "_".join(base_name_parts))

    return safe_rename(object_to_rename, new_name, uuid=uuid, rename_shape=rename_shape)


def shuffle_item_by_index_objects(
    objects_to_rename: list[str],
    index: int,
    offset: int = 1,
    separator: str = "_",
    rename_shape: bool = True,
) -> list[str]:
    """
    Shuffle the position of an item by the given index number.

    :param objects_to_rename: list of node names to rename.
    :param index: the index to edit.
    :param offset: the offset to shuffle the index.
    :param separator: the separator to use for the index item.
    :param rename_shape: whether to rename the shape nodes as well.
    :return: list of new node names.
    """

    uuids = cmds.ls(objects_to_rename, uuid=True)
    for i, object_to_rename in enumerate(objects_to_rename):
        shuffle_item_by_index(
            object_to_rename,
            index,
            offset=offset,
            uuid=uuids[i],
            separator=separator,
            rename_shape=rename_shape,
        )

    return cmds.ls(uuids, long=True)


def shuffle_item_by_index_filtered_type(
    index: int,
    nice_name_type: str,
    offset: int = 1,
    separator: str = "_",
    rename_shape: bool = True,
    search_hierarchy: bool = False,
    selection_only: bool = True,
    dag: bool = False,
    remove_maya_defaults: bool = True,
    transforms_only: bool = True,
) -> list[str]:
    """
    Shuffle the position of an item by the given index number.

    :param index: the index to edit.
    :param nice_name_type: the type of the object to rename.
    :param offset: the offset to shuffle the index.
    :param separator: the separator to use for the index item.
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

    return shuffle_item_by_index_objects(
        selected_nodes,
        index,
        offset=offset,
        separator=separator,
        rename_shape=rename_shape,
    )


def change_suffix_padding(
    object_to_rename: str,
    uuid: str | None = None,
    padding: int = 2,
    add_underscore: bool = True,
    rename_shape: bool = True,
) -> [str]:
    """
    Change the padding of the suffix of the given object.

    :param object_to_rename: node name to rename.
    :param uuid: optional UUID for the renaming. If given, it will be used for the renaming instead of the object name.
    :param padding: the number of padding to use for the numbering (1=1, 2=01, 3=001, ...).
    :param add_underscore: whether to add an underscore between the prefix/suffix and the object name.
    :param rename_shape: whether to rename the shape nodes as well.
    :return: new node name.
    """

    name_without_number, number, _ = trailing_number(object_to_rename)
    if not number:
        return object_to_rename

    print(name_without_number, number)

    new_padding = str(number).zfill(padding)
    name_without_number = (
        name_without_number[:-1]
        if name_without_number[-1] == "_"
        else name_without_number
    )
    new_name = (
        "_".join([name_without_number, new_padding])
        if add_underscore
        else "".join([name_without_number, new_padding])
    )
    safe_rename(object_to_rename, new_name, uuid=uuid, rename_shape=rename_shape)


def change_suffix_padding_objects(
    objects_to_rename: list[str],
    padding: int = 2,
    add_underscore: bool = True,
    rename_shape: bool = True,
) -> list[str]:
    """
    Change the padding of the suffix of the given objects.

    :param objects_to_rename: list of node names to rename.
    :param padding: the number of padding to use for the numbering (1=1, 2=01, 3=001, ...).
    :param add_underscore: whether to add an underscore between the prefix/suffix and the object name.
    :param rename_shape: whether to rename the shape nodes as well.
    :return: list of new node names.
    """

    uuids = cmds.ls(objects_to_rename, uuid=True)
    for i, object_to_rename in enumerate(objects_to_rename):
        change_suffix_padding(
            object_to_rename,
            uuid=uuids[i],
            padding=padding,
            add_underscore=add_underscore,
            rename_shape=rename_shape,
        )

    return cmds.ls(uuids, long=True)


def change_suffix_padding_filter(
    nice_name_type: str,
    padding: int = 2,
    add_underscore: bool = True,
    rename_shape: bool = True,
    search_hierarchy: bool = False,
    selection_only: bool = True,
    dag: bool = False,
    remove_maya_defaults: bool = True,
    transforms_only: bool = True,
) -> list[str]:
    """
    Change the padding of the suffix of the selected objects of the given type.

    :param nice_name_type: the type of the object to rename.
    :param padding: the number of padding to use for the numbering (1=1, 2=01, 3=001, ...).
    :param add_underscore: whether to add an underscore between the prefix/suffix and the object name.
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

    return change_suffix_padding_objects(
        selected_nodes,
        padding=padding,
        add_underscore=add_underscore,
        rename_shape=rename_shape,
    )


def remove_numbers_from_object(
    object_to_rename: str,
    uuid: str | None = None,
    trailing_only: bool = False,
    rename_shape: bool = True,
    remove_underscores: bool = True,
):
    """
    Removes the numbers from the given object name.

    :param object_to_rename: node name to rename.
    :param uuid: optional UUID for the renaming. If given, it will be used for the renaming instead of the object name.
    :param trailing_only: whether to remove only the trailing numbers.
    :param rename_shape: whether to rename the shape nodes as well.
    :param remove_underscores: whether to remove underscores from the object name.
    :return: new node name.
    """

    new_name = object_to_rename.split("|")[-1]
    if not trailing_only:
        new_name = "".join([i for i in new_name if not i.isdigit()])
        if remove_underscores:
            new_name = new_name.replace("__", "_")
    else:
        new_name = object_to_rename.rstrip("0123456789")
    if new_name[-1] == "_" and remove_underscores:
        new_name = new_name[:-1]

    return safe_rename(object_to_rename, new_name, uuid=uuid, rename_shape=rename_shape)


def remove_numbers_from_objects(
    objects_to_rename: list[str],
    trailing_only: bool = False,
    rename_shape: bool = True,
    remove_underscores: bool = True,
):
    """
    Removes the numbers from the given object names.

    :param objects_to_rename: list of node names to rename.
    :param trailing_only: whether to remove only the trailing numbers.
    :param rename_shape: whether to rename the shape nodes as well.
    :param remove_underscores: whether to remove underscores from the object name.
    :return: list of new node names.
    """

    uuids = cmds.ls(objects_to_rename, uuid=True)
    for i, object_to_rename in enumerate(objects_to_rename):
        remove_numbers_from_object(
            object_to_rename,
            uuid=uuids[i],
            trailing_only=trailing_only,
            rename_shape=rename_shape,
            remove_underscores=remove_underscores,
        )

    return cmds.ls(uuids, long=True)


def remove_numbers_filtered_type(
    nice_name_type: str,
    trailing_only: bool = False,
    remove_underscores: bool = True,
    rename_shape: bool = True,
    search_hierarchy: bool = False,
    selection_only: bool = True,
    dag: bool = False,
    remove_maya_defaults: bool = True,
    transforms_only: bool = True,
) -> list[str]:
    """
    Removes the numbers from the selected objects of the given type.

    :param nice_name_type: the type of the object to rename.
    :param trailing_only: whether to remove only the trailing numbers.
    :param remove_underscores: whether to remove underscores from the object name.
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

    return remove_numbers_from_objects(
        selected_nodes,
        trailing_only=trailing_only,
        rename_shape=rename_shape,
        remove_underscores=remove_underscores,
    )


def renumber_objects(
    objects_to_rename: list[str],
    remove_trailing_numbers: bool = True,
    padding: int = 2,
    add_underscore: bool = True,
    rename_shape: bool = True,
) -> list[str]:
    """
    Renames the objects in the list to be:
        - 'baseName_01'
        - 'baseName_02'
        - 'baseName_03'
        - ...

    :param objects_to_rename: list of node names to rename.
    :param remove_trailing_numbers: whether to remove the trailing numbers.
    :param padding: the number of padding to use for the numbering (1=1, 2=01, 3=001, ...).
    :param add_underscore: whether to add an underscore between the prefix/suffix and the object name.
    :param rename_shape: whether to rename the shape nodes as well.
    :return: list of new node names.
    """

    uuids = cmds.ls(objects_to_rename, uuid=True)
    for i, object_to_rename in enumerate(objects_to_rename):
        if remove_trailing_numbers:
            object_to_rename = remove_numbers_from_object(
                object_to_rename, uuid=uuids[i], trailing_only=True
            )
        number_suffix = str(i + 1).zfill(padding)
        if add_underscore:
            number_suffix = f"_{number_suffix}"
        new_name = "".join([object_to_rename, number_suffix])
        safe_rename(
            object_to_rename, new_name, uuid=uuids[i], rename_shape=rename_shape
        )

    return cmds.ls(uuids, long=True)


def renumber_filtered_type(
    nice_name_type: str,
    remove_trailing_numbers: bool = True,
    padding: int = 2,
    add_underscore: bool = True,
    rename_shape: bool = True,
    search_hierarchy: bool = False,
    selection_only: bool = True,
    dag: bool = False,
    remove_maya_defaults: bool = True,
    transforms_only: bool = True,
) -> list[str]:
    """
    Renames the selected nodes in the selection order to be:
        - 'baseName_01'
        - 'baseName_02'
        - 'baseName_03'
        - ...

    :param nice_name_type: the type of the object to rename.
    :param remove_trailing_numbers: whether to remove the trailing numbers.
    :param padding: the number of padding to use for the numbering (1=1, 2=01, 3=001, ...).
    :param add_underscore: whether to add an underscore between the prefix/suffix and the object name.
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

    return renumber_objects(
        selected_nodes,
        remove_trailing_numbers=remove_trailing_numbers,
        padding=padding,
        add_underscore=add_underscore,
        rename_shape=rename_shape,
    )


def assign_namespace(
    object_to_rename: str,
    namespace: str,
    remove_namespace: bool = False,
    uuid: str | None = None,
    rename_shape: bool = True,
) -> str:
    """
    Assigns or removes a namespace to the given object.

    :param object_to_rename: node name to rename.
    :param namespace: namespace to add or remove.
    :param remove_namespace: whether to remove namespace.
    :param uuid: optional UUID for the renaming. If given, it will be used for the renaming instead of the object name.
    :param rename_shape: whether to rename the shape nodes as well.
    :return: new node name.
    """

    long_prefix, found_namespace, base_name = naming.name_part_types(object_to_rename)
    if namespace == found_namespace and not remove_namespace:
        return object_to_rename

    new_name = naming.join_name_parts(
        long_prefix, namespace if not remove_namespace else "", base_name
    )

    return safe_rename(object_to_rename, new_name, uuid=uuid, rename_shape=rename_shape)


def remove_empty_namespaces() -> list[str]:
    """
    Recursive function that removes all empty namespaces in the scene.

    :return: list of removed namespaces.
    """

    deleted_namespaces: list[str] = []

    def _num_children(_ns):
        return _ns.count(":")

    found_namespaces: list[str] = cmds.namespaceInfo(
        listOnlyNamespaces=True, recurse=True
    )
    found_namespaces.sort(key=_num_children, reverse=True)
    for namespace in found_namespaces:
        try:
            cmds.namespace(removeNamespace=namespace)
            deleted_namespaces.append(namespace)
        except RuntimeError:
            # Namespace is not empty.
            pass
    if deleted_namespaces:
        logger.debug(f"Namespaces removed: {deleted_namespaces}")

    return deleted_namespaces


def remove_namespace_from_object(
    object_to_rename: str, uuid: str | None = None, rename_shape: bool = True
) -> str:
    """
    Removes the namespace from given object by renaming it.
    Namespace will not be removed.

    :param object_to_rename: name of the object we want to remove namespace from.
    :param uuid: optional UUID for the renaming. If given, it will be used for the renaming instead of the object name.
    :param rename_shape: whether to rename the shape nodes as well.
    :return: new object name.
    """

    long_prefix, _, base_name = naming.name_part_types(object_to_rename)
    new_name = naming.join_name_parts(long_prefix, "", base_name)
    return safe_rename(object_to_rename, new_name, uuid=uuid, rename_shape=rename_shape)


def empty_and_delete_namespace(namespace: str, rename_shape: bool = True) -> bool:
    """
    Returns given namespace from scene and renames all associated objects.

    :param namespace: namespace to remove.
    :param rename_shape: whether to rename the shape nodes as well.
    :return: True if namespace was deleted successfully; False otherwise.
    """

    namespace_objects = cmds.namespaceInfo(
        namespace, listNamespace=True, fullName=True, dagPath=True
    )
    uuids = cmds.ls(namespace_objects, uuid=True)
    if namespace_objects:
        for i, namespace_object in enumerate(namespace_objects):
            remove_namespace_from_object(
                namespace_object, uuid=uuids[i], rename_shape=rename_shape
            )

    try:
        cmds.namespace(removeNamespace=namespace)
        return True
    except RuntimeError:
        logger.warning(
            f"The current namespace {namespace} is either not empty or not found."
        )

    return False


def delete_namespaces(objects_to_rename: list[str], rename_shape: bool = True) -> bool:
    """
    Removes the namespace from the scene from the first selected object.

    :param objects_to_rename: list of objects to rename.
    :param rename_shape: whether to rename the shape nodes as well.
    :return: True if namespace was deleted successfully; False otherwise.
    """

    if not objects_to_rename:
        return False

    object_to_rename = objects_to_rename[0]
    namespace = naming.name_part_types(object_to_rename)[1]
    if not namespace:
        logger.warning(
            f"Namespace not found on first selected object: {object_to_rename}"
        )
        return False

    success = empty_and_delete_namespace(namespace, rename_shape=rename_shape)

    return success


def delete_selected_namespace(rename_shape: bool = True) -> bool:
    """
    Removes the namespace from the scene from the first selected object.
    Note that this operation will affect all associated objects.

    :param rename_shape: whether to rename the shape nodes as well.
    :return: True if namespace was deleted successfully; False otherwise.
    """

    selected_objects = cmds.ls(selection=True, long=True)
    if not selected_objects:
        logger.warning("No objects selected, please select an object with a namespace.")
        return False

    return delete_namespaces(selected_objects, rename_shape=rename_shape)


def create_assign_namespace_objects(
    objects_to_rename: list[str],
    namespace: str,
    remove_namespace: bool = False,
    rename_shape: bool = True,
) -> list[str]:
    """
    Creates/Removes a namespace from filtered objects.

    :param objects_to_rename: list of node names to rename.
    :param namespace: namespace to add or remove.
    :param remove_namespace: whether to remove namespace.
    :param rename_shape: whether to rename the shape nodes as well.
    :return: list of new node names.
    """

    # Create namespace if necessary.
    if not cmds.namespace(exists=namespace):
        cmds.namespace(set=":")
        cmds.namespace(add=namespace)

    uuids = cmds.ls(objects_to_rename, uuid=True)
    for i, object_to_rename in enumerate(objects_to_rename):
        assign_namespace(
            object_to_rename,
            namespace,
            remove_namespace=remove_namespace,
            uuid=uuids[i],
            rename_shape=rename_shape,
        )

    # Delete unused namespaces.
    cmds.namespace(set=":")
    remove_empty_namespaces()

    return cmds.ls(uuids, long=True)


def create_assign_namespace_filtered_type(
    namespace: str,
    nice_name_type: str,
    remove_namespace: bool = False,
    rename_shape: bool = True,
    search_hierarchy: bool = False,
    selection_only: bool = True,
    dag: bool = False,
    remove_maya_defaults: bool = True,
    transforms_only: bool = True,
) -> list[str]:
    """
    Creates/Removes a namespace from filtered objects.

    :param namespace: namespace to add or remove.
    :param nice_name_type: the type of the object to rename.
    :param remove_namespace: whether to remove namespace.
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

    return create_assign_namespace_objects(
        selected_nodes,
        namespace=namespace,
        remove_namespace=remove_namespace,
        rename_shape=rename_shape,
    )
