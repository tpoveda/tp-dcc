#!#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related to names
"""

import re

import maya.cmds

from tp.core import log
from tp.common.python import helpers, strings, name as naming_utils

logger = log.tpLogger


class EditIndexModes(object):

    INSERT = 'insert'
    REPLACE = 'replace'
    REMOVE = 'remove'


class FindUniqueName(naming_utils.FindUniqueString, object):
    """
    This class allows to find a name that does not clash with other names in the Maya scene
    It will increment the last number in hte name
    If no number is found, it will append a 1 to the end of the name
    """

    def __init__(self, name):
        super(FindUniqueName, self).__init__(name)

        self.work_on_last_number = True

    def get_last_number(self, bool_value):
        """
        Sets to update last number to get unique name or not
        :param bool_value: bool
        """

        self.work_on_last_number = bool_value

    def _get_scope_list(self):
        """
        Internal function used to get the scope list for the increment string
        :return: list<str>
        """

        if maya.cmds.objExists(self.increment_string):
            return [self.increment_string]

        return list()

    def _format_string(self, number):
        """
        Internal function to get the unique name format
        :param number: int
        """

        if number == 0:
            number = 1
            self.increment_string = '{}_{}'.format(self.test_string, number)

        if number > 1:
            if self.work_on_last_number:
                self.increment_string = naming_utils.increment_last_number(self.increment_string)
            else:
                self.increment_string = naming_utils.increment_first_number(self.increment_string)

    def _get_number(self):
        """
        Internal function to get the number on the string that we want to make unique
        :return: int
        """

        if self.work_on_last_number:
            number = naming_utils.get_last_number(self.test_string)
        else:
            number = naming_utils.get_first_number(self.test_string)
        if number is None:
            return 0

        return number


def get_compatible_name(name_str):
    """
    Converts given string to a valid Maya string
    :param name_str: str
    :return: str
    """

    return ''.join([c if c.isalnum() else '_' for c in name_str])


def remove_namespace_from_string(name):
    """
    Removes namespace from given string. Does not matter if the given name is a short or long one
    :param name: str
    :return: str
    """

    sub_name = name.split('.')
    if not sub_name:
        return ''

    return sub_name[-1]


def get_basename(obj, remove_namespace=True, remove_attribute=False):
    """
    Get the base name in a hierarchy name (a|b|c -> returns c)
    :param obj: str, name to get base name from
    :param remove_namespace: bool, Whether to remove or not namespace from the base name
    :param remove_attribute: bool, Whether to remove or not attribute from the base name
    :return: str
    """

    split_name = obj.split('|')
    base_name = split_name[-1]

    if remove_attribute:
        base_name_split = base_name.split('.')
        base_name = base_name_split[0]

    if remove_namespace:
        split_base_name = base_name.split(':')
        return split_base_name[-1]

    return base_name


def get_short_name(obj):
    """
    Returns short name of given Maya object
    :param obj: str
    :return: str
    """

    try:
        obj = obj.meta_node
    except Exception:
        pass

    node_names = maya.cmds.ls(obj, shortNames=True)
    if node_names:
        if len(node_names) == 1:
            return node_names[0]
        logger.warning('Too many objects named "{}"'.format(obj))
        for i, o in enumerate(node_names):
            logger.warning(' ' * 4 + '{0}: "{1}"'.format(i, o))
        raise ValueError('Get Node Short Name || More than one object with name {}'.format(obj))
    raise ValueError('Get Node Short Name || No object with name {} exists'.format(obj))


def get_long_name(obj):
    """
    Returns long name of given Maya object
    :param obj: str
    :return: str
    """

    try:
        obj = obj.meta_node
    except Exception:
        pass

    node_names = maya.cmds.ls(obj, long=True)
    if node_names:
        if len(node_names) == 1:
            return node_names[0]
        logger.error('Too many objects named "{}"'.format(obj))
        for i, o in enumerate(node_names):
            logger.error(' ' * 4 + '{0}: "{1}"'.format(i, o))
        raise ValueError('Get Node Long Name || More than one object with name {}'.format(obj))

    raise ValueError('Get Node Long Name || No object with name {} exists'.format(obj))


def get_node_name_parts(obj_name):
    """
    Breaks different Maya node name parts and returns them:
        - objectName: a:a:grpA|a:a:grpB|a:b:pSphere1
        - long_prefix: a:a:grpA|a:a:grpB
        - namespace: 'a:b
        - basename': 'pSphere1'
    :param obj_name: str, name of Maya node
    :return: tuple(str, str, str), tuple with long_prefix, namespace and basename
    """

    if '|' in obj_name:
        obj_name = str(obj_name)
        long_name_parts = obj_name.split('|')
        long_prefix = ''.join(long_name_parts[:-1])
        short_name = long_name_parts[-1]
    else:
        short_name = obj_name
        long_prefix = ''

    if ':' in short_name:
        namespace_parts = short_name.split(':')
        base_name = namespace_parts[-1]
        namespace = ':'.join(namespace_parts[:-1])
    else:
        base_name = short_name
        namespace = ''

    return long_prefix, namespace, base_name


def join_node_name_parts(long_prefix, namespace, base_name):
    """
    Joins given Maya name parts (long_prefix, namesapcne and base_name) to create a full Maya node name
    :param long_prefix: str, long prefix of the node ('a:grp1|grp2'). It can be empty ('')
    :param namespace: str, namespace if exists (b:c). It can be empty ('')
    :param base_name: str, base name of the Maya node (pSphere1')
    :return: str, joined maya name (a:grp1|grp2|b:c:pSphere1)
    """

    full_name = base_name
    if namespace:
        full_name = ':'.join([namespace, base_name])
    if long_prefix:
        full_name = '|'.join([long_prefix, full_name])

    return full_name


def get_reference_prefix(node=None):
    """
    Returns reference prefix is given node name has ne
    :param node: str, object to get reference prefix from
    :return: str
    """

    if maya.cmds.referenceQuery(node, isNodeReferenced=True):
        split_prefix = node.split(':')
        return ':'.join(split_prefix[:-1])

    return False


def is_unique(name):
    """
    Returns whether a name is unique or not in the scene
    :param name: str, name to check
    :return: bool
    """

    objs = maya.cmds.ls(name)
    count = len(objs)
    if count > 1:
        return False
    if count == 1:
        return True

    return True


def prefix_name(node, prefix, name, separator='_'):
    """
    Renames Maya node by adding given prefix to its name
    :param node: str, name of the Maya node we want to rename
    :param prefix: str, prefix to add to the name
    :param name: str, name of the node
    :param separator: str, separator used
    :return:  str, new node name
    """

    new_name = maya.cmds.rename(node, '{}{}{}'.format(prefix, separator, name))

    return new_name


def prefix_hierarchy(top_group, prefix):
    """
    Adds a prefix to all hierarchy objects
    :param top_group: str, name of the top node of the hierarchy
    :param prefix: str, prefix to add in front of top_group name and its children
    :return: list<str>, list with renamed hierarchy names including top_group
    """

    relatives = maya.cmds.listRelatives(top_group, ad=True, f=True)
    relatives.append(top_group)
    renamed = list()
    prefix = prefix.strip()
    for child in relatives:
        short_name = get_basename(child)
        new_name = maya.cmds.rename(child, '{}_{}'.format(prefix, short_name))
        renamed.append(new_name)
    renamed.reverse()

    return renamed


def pad_number(name):
    """
    Renames given node name with pad
    :param name: str, node name we want to pad
    :return: str
    """

    pad_name = naming_utils.pad_number(name=name)
    renamed = maya.cmds.rename(name, pad_name)

    return renamed


def find_unique_name(obj_names=None, uuid=None, include_last_number=True, do_rename=False, rename_shape=True):
    """
    Finds a unique name by adding a number to the end
    :param obj_names: str or list(str), name to start from
    :param uuid: str
    :param include_last_number: bool, Whether to include last number or not
    :param do_rename: bool
    :param rename_shape: bool
    :return: str or list(str)
    """

    def _find_unique_name(obj_name, obj_uuid=None):

        if obj_uuid:
            obj_name = maya.cmds.ls(obj_uuid, long=True)[0]

        if not maya.cmds.objExists(obj_name):
            return obj_name

        unique = FindUniqueName(obj_name)
        unique.get_last_number(include_last_number)

        unique_name = unique.get()

        if do_rename:
            return rename(obj_name, unique_name, uuid=obj_uuid, rename_shape=rename_shape)
        else:
            return unique_name

    if not obj_names:
        obj_names = maya.cmds.ls(sl=True, long=True)

    if isinstance(obj_names, (tuple, list)):
        uuid_list = maya.cmds.ls(obj_names, uuid=True)
        for i, obj in enumerate(obj_names):
            _find_unique_name(obj, uuid_list[i])
        return maya.cmds.ls(uuid_list, long=True)
    else:
        return _find_unique_name(obj_names, uuid)


def find_unique_name_by_filter(
        filter_type, include_last_number=True, do_rename=False, rename_shape=True, search_hierarchy=False,
        selection_only=True, dag=False, remove_maya_defaults=True, transforms_only=True):
    """
    Finds a unique name by adding a number to the end filtering by given filter
    :param filter_type: str, filter used to filter nodes to add prefix to
    :param include_last_number: bool, Whether to include last number or not
    :param do_rename: bool
    :param rename_shape: bool, Whether or not to also rename shape nodes of the renamed node
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search all scene objects or only selected ones
    :param dag: bool, Whether to return only DAG nodes
    :param remove_maya_defaults: Whether to ignore Maya default nodes or not
    :param transforms_only: bool, Whether to return only transform nodes or not
    :return: list(str), list of new node names
    """

    from tp.maya.cmds import filtertypes

    filtered_obj_list = filtertypes.filter_by_type(
        filter_type=filter_type, search_hierarchy=search_hierarchy, selection_only=selection_only, dag=dag,
        remove_maya_defaults=remove_maya_defaults, transforms_only=transforms_only)
    if not filtered_obj_list:
        logger.warning('No objects filtered with type "{}" found!'.format(filter_type))
        return

    return find_unique_name(
        obj_names=filtered_obj_list, include_last_number=include_last_number, do_rename=do_rename,
        rename_shape=rename_shape)


def find_available_name(name, suffix=None, index=0, padding=0, letters=False, capital=False):
    """
    Recursively find a free name matching specified criteria
    @param name: str, Name to check if already exists in the scene
    @param suffix: str, Suffix for the name
    @param index: int, Index of the name
    @param padding: int, Padding for the characters/numbers
    @param letters: bool, True if we want to use letters when renaming multiple nodes
    @param capital: bool, True if we want letters to be capital
    """

    if not maya.cmds.objExists(name):
        return name

    if letters is True:
        letter = strings.get_alpha(index - 1, capital)
        test_name = '%s_%s' % (name, letter)
    else:
        test_name = '%s_%s' % (name, str(index).zfill(padding + 1))

    if suffix:
        test_name = '%s_%s' % (test_name, suffix)

    # if object exists, try next index
    if maya.cmds.objExists(test_name):
        return find_available_name(name, suffix, index + 1, padding, letters, capital)

    return test_name


def rename(name, new_name, uuid=None, rename_shape=True, return_long_name=True):
    """
    Renames object
    :param name: str, name of the object to be renamed in short or long format
    :param new_name: str, new name of the object
    :param uuid: str, optional unique has id
    :param rename_shape: bool, Whether to rename shape nodes automatically to match transform nodes
    :param return_long_name: bool, Whether to return short or long name if rename process is correct
    :return: str
    """

    if uuid:
        name = maya.cmds.ls(uuid, long=True)[0]
    obj_short_name = get_basename(name, remove_namespace=False)
    new_short_name = get_basename(new_name, remove_namespace=False)
    if obj_short_name == new_short_name:
        return name
    if maya.cmds.lockNode(name, query=True)[0]:
        logger.warning('Node "{}" is loced and cannot be renamed!'.format(name))
        return name
    if not new_short_name:
        logger.warning('Names cannot be an empty string')
        return name
    if new_short_name[0].isdigit():
        logger.warning('Names cannot start with numbers')
        return name
    if ':' in new_short_name:
        new_pure_name = new_short_name.split(':')[-1]
        if new_pure_name[0].isdigit():
            logger.warning('Names cannot start with numbers')
            return name

    renamed_name = maya.cmds.rename(name, new_short_name, ignoreShape=not rename_shape)

    if return_long_name:
        return get_long_name(renamed_name)

    return renamed_name


def check_suffix_exists(obj_name, suffix):
    """
    Checks whether given suffix in given Maya node or not
    :param obj_name: str, name of the object to check suffix of
    :param suffix: str, suffix to check
    :return: bool, Whether given suffix already exists in given node or not
    """

    base_name_split = obj_name.split('_')
    if base_name_split[0] == suffix.replace('_', ''):
        return True

    return False


def check_prefix_exists(obj_name, prefix):
    """
    Checks whether given prefix exists in given Maya node or not
    :param obj_name: str, name of the object to check prefix of
    :param prefix: str, prefix to check
    :return: bool, Whether given prefix already exists in given node or not
    """

    long_prefix, namespace, base_name = get_node_name_parts(obj_name)
    base_name_slit = base_name.split('_')
    if base_name_slit[0] == prefix.replace('_', ''):
        return True

    return False


def add_prefix(prefix, obj_names=None, uuid=None, add_underscore=False, rename_shape=True, check_existing_prefix=True):
    """
    Adds a prefix to given object name
    You can pass an UUID instead of an object name to avoid problems with hierarchies or when
    renaming while parenting nodes
    :param prefix: str, prefix to add
    :param obj_names: str, name of the node to add prefix to. If not given, selected nodes will be used
    :param uuid: str, optional UUID of the node we want to add prefix to. If given, obj_name will be ignored
    :param add_underscore: bool, Whether or not to add underscore after the prefix
    :param rename_shape: bool, Whether or not to also rename shape nodes of the renamed node
    :param check_existing_prefix: bool, Whether or not to check if the prefix already exists before adding it.
        If the prefix already exits, the operation is skipped
    :return: str, new name of the node
    """

    def _add_prefix(obj_name, obj_uuid=None):
        prefix_exists = False
        if check_existing_prefix:
            prefix_exists = check_prefix_exists(obj_name, prefix)
        if not prefix_exists:
            if add_underscore:
                prefix_to_add = '{}_'.format(prefix)
            else:
                prefix_to_add = prefix
            long_prefix, namespace, base_name = get_node_name_parts(obj_name)
            base_name = ''.join([prefix_to_add, base_name])
            new_name = join_node_name_parts(long_prefix, namespace, base_name)
        else:
            new_name = obj_name

        return rename(obj_name, new_name, uuid=obj_uuid, rename_shape=rename_shape)

    if not obj_names:
        obj_names = maya.cmds.ls(sl=True, long=True)

    if isinstance(obj_names, (tuple, list)):
        uuid_list = maya.cmds.ls(obj_names, uuid=True)
        for i, obj in enumerate(obj_names):
            _add_prefix(obj, uuid_list[i])
        return maya.cmds.ls(uuid_list, long=True)
    else:
        return _add_prefix(obj_names, uuid)


def add_suffix(suffix, obj_names=None, uuid=None, add_underscore=False, rename_shape=True, check_existing_suffix=True):
    """
    Adds a suffix to given object name
    You can pass an UUID instead of an object name to avoid problems with hierarchies or when
    renaming while parenting nodes
    :param suffix: str, suffix to add
    :param obj_names: str, name of the node to add suffix to. If not given, selected nodes will be used
    :param uuid: str, optional UUID of the node we want to add suffix to. If given, obj_name will be ignored
    :param add_underscore: bool, Whether or not to add underscore before the suffix
    :param rename_shape: bool, Whether or not to also rename shape nodes of the renamed node
    :param check_existing_suffix: bool, Whether or not to check if the suffix already exists before adding it.
        If the suffix already exits, the operation is skipped
    :return: str, new name of the node
    """

    def _add_suffix(obj_name, obj_uuid=None):
        suffix_exists = False
        if check_existing_suffix:
            suffix_exists = check_suffix_exists(obj_name, suffix)
        if not suffix_exists:
            if add_underscore:
                suffix_to_add = '_{}'.format(suffix)
            else:
                suffix_to_add = suffix
            new_name = ''.join([obj_name, suffix_to_add])
        else:
            new_name = obj_name

        return rename(obj_name, new_name, uuid=obj_uuid, rename_shape=rename_shape)

    if not obj_names:
        obj_names = maya.cmds.ls(sl=True, long=True)

    if isinstance(obj_names, (tuple, list)):
        uuid_list = maya.cmds.ls(obj_names, uuid=True)
        for i, obj in enumerate(obj_names):
            _add_suffix(obj, uuid_list[i])
        return maya.cmds.ls(uuid_list, long=True)
    else:
        return _add_suffix(obj_names, uuid)


def add_prefix_by_filter(prefix, filter_type, add_underscore=False, rename_shape=True, search_hierarchy=False,
                         selection_only=True, dag=False, remove_maya_defaults=True, transforms_only=True):
    """
    Adds a prefix to filtered by types nodes.
    :param prefix: str, prefix to add
    :param filter_type: str, filter used to filter nodes to add prefix to
    :param add_underscore: bool, Adds an underscore betrween the number and the new one
    :param rename_shape: bool, Whether or not to also rename shape nodes of the renamed node
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search all scene objects or only selected ones
    :param dag: bool, Whether to return only DAG nodes
    :param remove_maya_defaults: Whether to ignore Maya default nodes or not
    :param transforms_only: bool, Whether to return only transform nodes or not
    :return: list(str), list of new node names
    """

    from tp.maya.cmds import filtertypes

    filtered_obj_list = filtertypes.filter_by_type(
        filter_type=filter_type, search_hierarchy=search_hierarchy, selection_only=selection_only, dag=dag,
        remove_maya_defaults=remove_maya_defaults, transforms_only=transforms_only)
    if not filtered_obj_list:
        logger.warning('No objects filtered with type "{}" found!'.format(filter_type))
        return

    return add_prefix(
        prefix=prefix, obj_names=filtered_obj_list, add_underscore=add_underscore, rename_shape=rename_shape)


def add_suffix_by_filter(suffix, filter_type, add_underscore=False, rename_shape=True, search_hierarchy=False,
                         selection_only=True, dag=False, remove_maya_defaults=True, transforms_only=True):
    """
    Adds a prefix to filtered by types nodes.
    :param suffix: str, suffix to add
    :param filter_type: str, filter used to filter nodes to add suffix to
    :param add_underscore: bool, Whether or not to add underscore before the suffix
    :param rename_shape: bool, Whether or not to also rename shape nodes of the renamed node
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search all scene objects or only selected ones
    :param dag: bool, Whether to return only DAG nodes
    :param remove_maya_defaults: Whether to ignore Maya default nodes or not
    :param transforms_only: bool, Whether to return only transform nodes or not
    :return: list(str), list of new node names
    """

    from tp.maya.cmds import filtertypes

    filtered_obj_list = filtertypes.filter_by_type(
        filter_type=filter_type, search_hierarchy=search_hierarchy, selection_only=selection_only, dag=dag,
        remove_maya_defaults=remove_maya_defaults, transforms_only=transforms_only)
    if not filtered_obj_list:
        logger.warning('No objects filtered with type "{}" found!'.format(filter_type))
        return

    return add_suffix(
        suffix=suffix, obj_names=filtered_obj_list, add_underscore=add_underscore, rename_shape=rename_shape)


def change_suffix_padding(obj_names=None, uuid=None, padding=2, add_underscore=True, rename_shape=True):
    """
    Changes the suffix numerical padding of an object
    :param obj_names: str or list(str), name of Maya object to change suffix of
    :param uuid: str, optional unique has id
    :param padding: amount of numerical padding
    :param add_underscore: bool, Adds an underscore betrween the number and the new one
    :param rename_shape: bool, Whether to rename shape nodes automatically to match transform nodes
    :return: str, new name of the object
    """

    def _change_suffix_padding(obj_name, obj_uuid):
        name_no_number, number, current_padding = naming_utils.get_trailing_number_data(obj_name)
        if not number:
            return obj_name

        new_padding = str(number).zfill(padding)
        if name_no_number[-1] == '_':
            name_no_number = name_no_number[:-1]

        if add_underscore:
            new_name = '_'.join([name_no_number, new_padding])
        else:
            new_name = ''.join([name_no_number, new_padding])

        return rename(obj_name, new_name, uuid=obj_uuid, rename_shape=rename_shape, return_long_name=True)

    if not obj_names:
        obj_names = maya.cmds.ls(sl=True, long=True)

    if isinstance(obj_names, (tuple, list)):
        uuid_list = maya.cmds.ls(obj_names, uuid=True)
        for i, obj in enumerate(obj_names):
            _change_suffix_padding(obj, uuid_list[i])
        return maya.cmds.ls(uuid_list, long=True)
    else:
        return _change_suffix_padding(obj_names, uuid)


def change_suffix_padding_by_filter(
        filter_type, padding=2, add_underscore=True, rename_shape=True, search_hierarchy=False,
        selection_only=True, dag=False, remove_maya_defaults=True, transforms_only=True):
    """
    Changes the suffix numerical padding of an object by filtering
    :param filter_type: str, filter used to filter nodes to edit index of
    :param padding: amount of numerical padding
    :param add_underscore: bool, Adds an underscore betrween the number and the new one
    :param rename_shape: bool, Whether to rename shape nodes automatically to match transform nodes
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search all scene objects or only selected ones
    :param dag: bool, Whether to return only DAG nodes
    :param remove_maya_defaults: Whether to ignore Maya default nodes or not
    :param transforms_only: bool, Whether to return only transform nodes or not
    :return: str, new name of the object
    """

    from tp.maya.cmds import filtertypes

    filtered_obj_list = filtertypes.filter_by_type(
        filter_type=filter_type, search_hierarchy=search_hierarchy, selection_only=selection_only, dag=dag,
        remove_maya_defaults=remove_maya_defaults, transforms_only=transforms_only)
    if not filtered_obj_list:
        logger.warning('No objects filtered with type "{}" found!'.format(filter_type))
        return

    return change_suffix_padding(
        obj_names=filtered_obj_list, padding=padding, add_underscore=add_underscore, rename_shape=rename_shape)


def check_index_in_list(name_list, index):
    """
    Returns whether or not given index exists in a list of names
    For example:
        name_list: ['a', 'b']
         0 exists, 'a', so we return True
         1 exists, 'b', so we return True
        -1 exists, 'b', so we return True
         2 does not exists, we return False
    :param name_list: list(str), name split in components
    :param index: int, positive or negative index number
    :return: bool, Whether given index exists or not in names list
    """

    list_length = len(name_list)
    if index < 0:
        check_length = abs(index)
    else:
        check_length = index + 1
    if check_length > list_length:
        return False

    return True


def edit_item_index(obj_names, index, text='', mode=EditIndexModes.INSERT, separator='_', rename_shape=True, uuid=None):
    """
    Splits object node name by given separator and edits the position based on the given index
    You can pass an UUID instead of an object name to avoid problems with hierarchies or when
    renaming while parenting nodes
    :param obj_names: str, current name of the object we want edit index of
    :param index: int, positive or negative index number (['pSphere', 'grp'] -> 0='pSphere'; 1='grp'; -1='grp')
    :param text: str, text to insert or replace
    :param mode: str, the edit mode to execute:
        - insert: inserts (adds) a new text in the given position
        - remove: removes the given text at the given position
        - replace: overwrites exiting text in given position with the new given text
    :param separator: str, text used to split the node name
    :param rename_shape: bool, Whether to rename shape nodes automatically to match transform nodes
    :param uuid: str, optional unique hash id
    :return: str, new name of the object
    """

    def _edit_item_index(obj_name, index_, obj_uuid=None):
        long_prefix, namespace, base_name = get_node_name_parts(obj_name)
        base_name_list = base_name.split(separator)
        if not check_index_in_list(base_name_list, index_):
            return obj_name

        if mode == EditIndexModes.REMOVE:
            if len(base_name_list) == 1:
                logger.warning('Not enough name parts to rename: {}'.format(base_name_list[0]))
                return obj_name
            del base_name_list[index_]
        elif mode == EditIndexModes.REPLACE:
            if not text:
                del base_name_list[index_]
            else:
                base_name_list[index_] = text
        elif mode == EditIndexModes.INSERT:
            if not text:
                return obj_name
            neg = False
            if index_ < 0:
                index_ += 1
                neg = True
            # Append to end if index is zero and negative
            if index_ == 0 and neg:
                base_name_list.append(text)
            # Append to begin if index is zero and non negative
            elif index_ == 0 and not neg:
                base_name_list = [text] + base_name_list
            else:
                base_name_list.insert(index_, text)

        base_name = separator.join(base_name_list)
        new_name = join_node_name_parts('', namespace, base_name)

        return rename(obj_name, new_name, uuid=obj_uuid, rename_shape=rename_shape)

    if not obj_names:
        obj_names = maya.cmds.ls(sl=True, long=True)

    if isinstance(obj_names, (tuple, list)):
        uuid_list = maya.cmds.ls(obj_names, uuid=True)
        for i, obj in enumerate(obj_names):
            _edit_item_index(obj, index, uuid_list[i])
        return maya.cmds.ls(uuid_list, long=True)
    else:
        return _edit_item_index(obj_names, index, uuid)


def edit_item_index_by_filter(index, filter_type, text='', mode=EditIndexModes.INSERT, separator='_',
                              rename_shape=True, search_hierarchy=False, selection_only=True, dag=False,
                              remove_maya_defaults=True, transforms_only=True):
    """
    Splits object node name by given separator and edits the position based on the given index
    :param index: int, positive or negative index number (['pSphere', 'grp'] -> 0='pSphere'; 1='grp'; -1='grp')
    :param filter_type: str, filter used to filter nodes to edit index of
    :param text: str, text to insert or replace
    :param mode: str, the edit mode to execute:
        - insert: inserts (adds) a new text in the given position
        - remove: removes the given text at the given position
        - replace: overwrites exiting text in given position with the new given text
    :param separator: str, text used to split the node name
    :param rename_shape: bool, Whether to rename shape nodes automatically to match transform nodes
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search all scene objects or only selected ones
    :param dag: bool, Whether to return only DAG nodes
    :param remove_maya_defaults: Whether to ignore Maya default nodes or not
    :param transforms_only: bool, Whether to return only transform nodes or not
    :return: str, new name of the object
    """

    from tp.maya.cmds import filtertypes

    filtered_obj_list = filtertypes.filter_by_type(
        filter_type=filter_type, search_hierarchy=search_hierarchy, selection_only=selection_only, dag=dag,
        remove_maya_defaults=remove_maya_defaults, transforms_only=transforms_only)
    if not filtered_obj_list:
        logger.warning('No objects filtered with type "{}" found!'.format(filter_type))
        return

    return edit_item_index(
        obj_names=filtered_obj_list, index=index, text=text, mode=mode, separator=separator, rename_shape=rename_shape)


def auto_suffix_object(obj_names, uuid=None, rename_shape=True):
    """
    Adds a suffix to given object based on its Maya type
    You can pass an UUID instead of an object name to avoid problems with hierarchies or when
    renaming while parenting nodes
    :param obj_names: str, name of the node we want to rename
    :param uuid: str, optional unique has id
    :param rename_shape: bool, Whether to rename shape nodes automatically to match transform nodes
    :return:
    """

    def _auto_suffix_obj(obj_name, obj_uuid=None):
        if uuid:
            obj_name = maya.cmds.ls(uuid, long=True)[0]

        obj_type = maya.cmds.objectType(obj_name)
        if obj_type == 'transform':
            shape_nodes = maya.cmds.listRelatives(obj_name, shapes=True, fullPath=True)
            if not shape_nodes:
                obj_type = 'group'
            else:
                obj_type = maya.cmds.objectType(shape_nodes[0])
        elif obj_type == 'joint':
            shape_nodes = maya.cmds.listRelatives(obj_name, shapes=True, fullPath=True)
            if shape_nodes and maya.cmds.objectType(shape_nodes[0]) == 'nurbsCurve':
                obj_type = 'controller'
        if obj_type == 'nurbsCurve':
            connections = maya.cmds.listConnections('{}.message'.format(obj_name))
            if connections:
                for node in connections:
                    if maya.cmds.nodeType(node) == 'controller':
                        obj_type = 'controller'
                        break

        if obj_type not in auto_suffix:
            return obj_name
        else:
            suffix = auto_suffix[obj_type]

        existing_suffix = obj_name.split('_')[-1]
        if existing_suffix == suffix:
            return obj_name

        return add_suffix(
            obj_names=obj_name, suffix=suffix, uuid=obj_uuid, add_underscore=True, rename_shape=rename_shape)

    if not obj_names:
        obj_names = maya.cmds.ls(sl=True, long=True)

    naming_config = configs.get_config('tpDcc-naming')
    if not naming_config:
        auto_suffix = dict()
    else:
        auto_suffix = naming_config.get('auto_suffixes', default=dict())
    if not auto_suffix:
        logger.warning(
            'Impossible to launch auto suffix functionality because no auto suffixes are defined for Maya!')
        return None

    if isinstance(obj_names, (tuple, list)):
        uuid_list = maya.cmds.ls(obj_names, uuid=True)
        for i, obj in enumerate(obj_names):
            _auto_suffix_obj(obj, uuid_list[i])
        return maya.cmds.ls(uuid_list, long=True)
    else:
        return _auto_suffix_obj(obj_names, uuid)


def auto_suffix_object_by_type(
        filter_type, rename_shape=True, search_hierarchy=False, selection_only=True, dag=False,
        remove_maya_defaults=True, transforms_only=True):
    """
    Adds a suffix to given object based on its Maya type and given filter
    :param filter_type: str, filter used to filter nodes to add suffix to
    :param rename_shape: bool, Whether to rename shape nodes automatically to match transform nodes
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search all scene objects or only selected ones
    :param dag: bool, Whether to return only DAG nodes
    :param remove_maya_defaults: Whether to ignore Maya default nodes or not
    :param transforms_only: bool, Whether to return only transform nodes or not
    :return: list(str), list of rename nodes
    """

    from tp.maya.cmds import filtertypes

    filtered_obj_list = filtertypes.filter_by_type(
        filter_type=filter_type, search_hierarchy=search_hierarchy, selection_only=selection_only, dag=dag,
        remove_maya_defaults=remove_maya_defaults, transforms_only=transforms_only)
    if not filtered_obj_list:
        logger.warning('No objects filtered with type "{}" found!'.format(filter_type))
        return

    return auto_suffix_object(obj_names=filtered_obj_list, rename_shape=rename_shape)


def remove_numbers_from_object(
        obj_names=None, uuid=None, trailing_only=False, rename_shape=True, remove_underscores=True):
    """
    Removes all numbers from given node names
    You can pass an UUID instead of an object name to avoid problems with hierarchies or when
    renaming while parenting nodes
    :param obj_names: str, current name of the object we want to remove numbers from
    :param uuid: str, optional unique hash id
    :param trailing_only: bool, Whether or not to remove only numbers at the ned of the name
    :param rename_shape: bool, Whether to rename shape nodes automatically to match transform nodes
    :param remove_underscores: bool, Whether or not to remove unwanted underscores
    :return: str or list(str), new names for the node or nodes
    """

    def _remove_numbers_from_object(obj_name, obj_uuid=None):
        new_name = obj_name.split('|')[-1]
        if not trailing_only:
            new_name = ''.join([name_char for name_char in new_name if not name_char.isdigit()])
            if remove_underscores:
                new_name = new_name.replace('__', '_')
        else:
            new_name = obj_name.rstrip('0123456789')
        if new_name[-1] == '_' and remove_underscores:
            new_name = new_name[:-1]

        return rename(obj_name, new_name, uuid=obj_uuid, rename_shape=rename_shape)

    if not obj_names:
        obj_names = maya.cmds.ls(sl=True, long=True)

    if isinstance(obj_names, (tuple, list)):
        uuid_list = maya.cmds.ls(obj_names, uuid=True)
        for i, obj in enumerate(obj_names):
            _remove_numbers_from_object(obj, uuid_list[i])
        return maya.cmds.ls(uuid_list, long=True)
    else:
        return _remove_numbers_from_object(obj_names, uuid)


def remove_numbers_from_object_by_filter(
        filter_type, trailing_only=False, rename_shape=True, remove_underscores=True, search_hierarchy=False,
        selection_only=True, dag=False, remove_maya_defaults=True, transforms_only=True):
    """
    Removes all numbers from given node names by given filter
    :param filter_type: str, filter used to filter nodes to edit index of
    :param trailing_only: bool, Whether or not to remove only numbers at the ned of the name
    :param rename_shape: bool, Whether to rename shape nodes automatically to match transform nodes
    :param remove_underscores: bool, Whether or not to remove unwanted underscores
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search all scene objects or only selected ones
    :param dag: bool, Whether to return only DAG nodes
    :param remove_maya_defaults: Whether to ignore Maya default nodes or not
    :param transforms_only: bool, Whether to return only transform nodes or not
    :return: str or list(str), new names for the node or nodes
    """

    from tp.maya.cmds import filtertypes

    filtered_obj_list = filtertypes.filter_by_type(
        filter_type=filter_type, search_hierarchy=search_hierarchy, selection_only=selection_only, dag=dag,
        remove_maya_defaults=remove_maya_defaults, transforms_only=transforms_only)
    if not filtered_obj_list:
        logger.warning('No objects filtered with type "{}" found!'.format(filter_type))
        return

    return remove_numbers_from_object(
        obj_names=filtered_obj_list, trailing_only=trailing_only, rename_shape=rename_shape,
        remove_underscores=remove_underscores)


def renumber_objects(obj_names=None, remove_trailing_numbers=True, add_underscore=True, padding=2, rename_shape=True):
    """
    Renumber a given object or list of objects
        remove_trailing_numbers=True, add_underscore=True, padding=2 == ['a1', 'b1'] -> ['a_01', 'b_02']
        remove_trailing_numbers=True, add_unerscore=True, padding=3 == ['a1', 'b1'] -> ['a_001', 'b_002']
        remove_trailing_numbers=True, add_unerscore=False, padding=1 == ['a1', 'b1'] -> ['a1', 'b2']
    :param obj_names: list(str), list of Maya node names to renumber
    :param remove_trailing_numbers: bool, Whether to remove trailing numbers before doing the renumber
    :param add_underscore: bool, Whether or not to remove underscore between name and new number
    :param padding: int, amount of numerical padding (2=01, 3=001, etc). Only used if given names has no numbers.
    :param rename_shape: bool, Whether to rename shape nodes automatically to match transform nodes
    :return: list(str), list of new renumbered names
    """

    obj_names = helpers.force_list(obj_names)
    if not obj_names:
        obj_names = maya.cmds.ls(sl=True, long=True)

    uuid_list = maya.cmds.ls(obj_names, uuid=True)
    for i, obj in enumerate(obj_names):
        if remove_trailing_numbers:
            obj = remove_numbers_from_object(obj, uuid=uuid_list[i], trailing_only=True)
        number_suffix = str(i + 1).zfill(padding)
        if add_underscore:
            number_suffix = '_{}'.format(number_suffix)
        new_name = ''.join([obj, number_suffix])
        rename(obj, new_name, uuid=uuid_list[i], rename_shape=rename_shape)

    return maya.cmds.ls(uuid_list, long=True)


def renumber_objects_by_filter(
        filter_type, remove_trailing_numbers=True, add_underscore=True, padding=2, rename_shape=True,
        search_hierarchy=False, selection_only=True, dag=False, remove_maya_defaults=True, transforms_only=True):
    """
    Renumber a given object or list of objects by given filter criteria
        remove_trailing_numbers=True, add_underscore=True, padding=2 == ['a1', 'b1'] -> ['a_01', 'b_02']
        remove_trailing_numbers=True, add_unerscore=True, padding=3 == ['a1', 'b1'] -> ['a_001', 'b_002']
        remove_trailing_numbers=True, add_unerscore=False, padding=1 == ['a1', 'b1'] -> ['a1', 'b2']
    :param filter_type: str, filter used to filter nodes to edit index of
    :param remove_trailing_numbers: bool, Whether to remove trailing numbers before doing the renumber
    :param add_underscore: bool, Whether or not to remove underscore between name and new number
    :param padding: int, amount of numerical padding (2=01, 3=001, etc). Only used if given names has no numbers.
    :param rename_shape: bool, Whether to rename shape nodes automatically to match transform nodes
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search all scene objects or only selected ones
    :param dag: bool, Whether to return only DAG nodes
    :param remove_maya_defaults: Whether to ignore Maya default nodes or not
    :param transforms_only: bool, Whether to return only transform nodes or not
    :return: list(str), list of new renumbered names
    """

    from tp.maya.cmds import filtertypes

    filtered_obj_list = filtertypes.filter_by_type(
        filter_type=filter_type, search_hierarchy=search_hierarchy, selection_only=selection_only, dag=dag,
        remove_maya_defaults=remove_maya_defaults, transforms_only=transforms_only)
    if not filtered_obj_list:
        logger.warning('No objects filtered with type "{}" found!'.format(filter_type))
        return

    return renumber_objects(
        obj_names=filtered_obj_list, remove_trailing_numbers=remove_trailing_numbers, padding=padding,
        add_underscore=add_underscore, rename_shape=rename_shape)


def wildcard_to_regex(wildcard):
    """
    Converts a * syntax into a parsed regular expression

    Maya wildcard validation:
        1. Maya does not support '-' characters so we change those characters by '_'
        2. Maya uses | as separators, so we scape them
        3. We need to replace any '*' into .+'
        4. Expression must end with $

    :param wildcard: str, wildcard to parse. If not wildcard is provided, we match everything.
    :return: str
    """

    if not wildcard:
        expression = '.*'
    else:
        wildcard = wildcard.replace('-', '_')
        expression = re.sub(r'(?<!\\)\|', r'\|', wildcard)
        expression = re.sub(r'(?<!\\)\*', r'.*', expression)
        if not expression[-1] == '$':
            expression += '$'

    regex = re.compile(expression, flags=re.I)

    return regex


short = get_short_name
base = get_basename
long = get_long_name
