from __future__ import annotations

from maya import cmds


def get_short_name(long_name: str) -> str:
    """
    Returns the short name of the given long name.

    :param long_name: long name to get the short name from.
    :return: short name.
    """

    return long_name.split("|")[-1] if "|" in long_name else long_name


def get_short_names(long_names: list[str]) -> list[str]:
    """
    Returns the short names of the given long names.

    :param long_names: list of long names to get the short names from.
    :return: list of short names.
    """

    return [get_short_name(long_name) for long_name in long_names]


def get_long_name_from_short_name(short_name: str) -> str:
    """
    Returns the long name of the given short name.

    :param short_name: short name to get the long name from.
    :return: long name.
    """

    return cmds.ls(short_name, long=True)[0]


def get_long_names_from_short_names(short_names: list[str]) -> list[str]:
    """
    Returns the long names of the given short names.

    :param short_names: list of short names to get the long names from.
    :return: list of long names.
    """

    return cmds.ls(short_names, long=True)


def get_unique_short_name(long_name: str) -> str:
    """
    Returns the shortest unique name for the given long name.

    Example:
        '|obj1|rig|mesh' maybe is not a unique Maya name, so we try to find the shortest unique name from it,
        for example, |obj1|rig|.

    Note that world names may be valid (names that start with |), for example, |sphere1 can be a valid name although
    there s another sphere1 node parented under other object.

    :param long_name: long name to get the unique short name from.
    :return: unique short name.
    """

    return cmds.ls(long_name, shortNames=True)[0]


def get_unique_short_names(long_names: list[str]) -> list[str]:
    """
    Returns the shortest unique names for the given long names.

    :param long_names: list of long names to get the unique short names from.
    :return: list of unique short names.
    """

    return cmds.ls(long_names, shortNames=True)


def name_part_types(name: str) -> tuple[str, str, str]:
    """
    Breaks up given node name with the "long name prefix", "namespace" (if exists)
    and "pure name" parts.

    Example 1:
        name: `joint1`
        return '', '', 'joint1'
    Example 2:
        name: `character1:x:root|character1:x:joint0|character1:y:joint1`
        return 'character1:x:root|character1:x:joint0', 'character1:y', 'joint1'

    :param name: name to break up.
    :return: long name prefix, namespace and pure name parts.
    """

    # Long name and/or namespaces.
    if "|" in name:
        name = str(name)
        long_name_parts = name.split("|")
        long_prefix = "".join(long_name_parts[:-1])
        short_name = long_name_parts[-1]
    else:
        short_name = name
        long_prefix = ""

    # Namespaces.
    if ":" in short_name:
        namespace_parts = short_name.split(":")
        pure_name = namespace_parts[-1]
        namespace = ":".join(namespace_parts[:-1])
    else:
        pure_name = short_name
        namespace = ""

    return long_prefix, namespace, pure_name


def join_name_parts(long_prefix: str, namespace: str, pure_name: str):
    """
    Joins given names.

    Example 1 (long names with namespaces)
        long_prefix = 'xx:group1|group2'
        namespace = 'x:y'
        pure_name = 'joint1'
        result = 'xx:group1|group2|x:y:joint1'

    Example 2 (short names)
        long_prefix = ''
        namespace = ''
        pure_name = 'joint1'
        result = 'joint1'

    :param long_prefix: long name prefix.
    :param namespace: namespace (if it exists).
    :param pure_name: name without long prefix or namespace.
    :return: joined name.
    """

    full_name = pure_name
    if namespace:
        full_name = ":".join([namespace, pure_name])
    if long_prefix:
        full_name = "|".join([long_prefix, full_name])

    return full_name


def rename_namespace_suffix_prefix(
    name: str, namespace: str, prefix: str, suffix: str
) -> str:
    """
    Renames given name with a namespace, prefix and suffix.
    Note that this function will not rename the node within the scene, it will only
    return the new name.

    :param name: name to rename.
    :param namespace: namespace to add to the name (.e.g. 'characterX').
    :param prefix: prefix to add to the object name (e.g. 'prefix_' for 'prefix_joint').
    :param suffix: suffix to add to the object name (e.g. '_suffix' for 'joint_suffix').
    :return: new name with namespace, prefix and suffix.
    """

    if not name:
        return ""

    long_prefix, existing_namespace, pure_name = name_part_types(name)
    if prefix:
        pure_name = "".join([prefix, pure_name])
    if suffix:
        pure_name = "".join([pure_name, suffix])
    if namespace:
        if not namespace.endswith(":"):
            pure_name = ":".join([namespace, pure_name])
        else:
            pure_name = "".join([namespace, pure_name])

    return join_name_parts(long_prefix, existing_namespace, pure_name)
