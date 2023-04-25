#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with reference
"""

import traceback

import maya.cmds

from tp.core import log
from tp.common.python import helpers

logger = log.tpLogger


def check_reference(ref_node):
    """
    Checks whether given node is a reference or not and raise exception if not.

    :param str ref_node: referece node name.
    """

    if not is_reference(ref_node):
        raise Exception('Object "{}" is not a valid reference node!'.format(ref_node))

    return True


def list_references(parent_namespace=None):
    """
    Returns a list of reference nodes found in the current scene.

    :param str or None parent_namespace: parent namespace to query references nodes from
    :return:
    """

    ref_nodes = list()
    for ref in maya.cmds.ls(type='reference'):
        if 'sharedReferenceNode' in ref or '_UNKNOWN_REF_NODE_' in ref:
            continue
        if parent_namespace:
            if not ref.startswith(parent_namespace):
                continue
        ref_nodes.append(ref)

    return ref_nodes


def is_reference(ref_node):
    """
    Returns whether given node is a valid reference node or not
    :param ref_node: str
    :return: bool
    """

    return ref_node in list_references()


def is_proxy_manager(node):
    """
    Returns whether the given node is a proxy manager or not
    :param node: str
    :return: bool
    """

    if not node or not maya.cmds.objExists(node):
        return False

    if maya.cmds.objectType(node) != 'proxyManager':
        return False

    return True


def is_referenced(node):
    """
    Returns whether the given node is referenced from an external file or not
    :param node: str
    :return: bool
    """

    return maya.cmds.referenceQuery(node, isNodeReferenced=True)


def is_loaded(ref_node):
    """
    Returns whether the referenced associated with the given reference node is currently laoded or not
    :param ref_node: str
    :return: bool
    """

    check_reference(ref_node)

    reference_loaded = not maya.cmds.file(referenceNode=ref_node, query=True, deferReference=True)

    return reference_loaded


def reference_node(node):
    """
    Returns the reference node associated to the given referenced object
    :param node: str
    :return: str
    """

    if not is_referenced(node):
        raise Exception('Object "{}" is not a referenced node!'.format(node))

    ref_node = maya.cmds.referenceQuery(node, referenceNode=True)

    return ref_node


def reference_file(ref_node, without_copy_number=True):
    """
    Returns the reference file associated with the given referenced object or reference node
    :param ref_node: str, reference node to query
    :param without_copy_number: bool
    :return: str
    """

    if not is_reference(ref_node) and not is_referenced(ref_node):
        raise Exception('Object "{}" is not a valid reference node or a node from a reference file!'.format(ref_node))

    ref_file = maya.cmds.referenceQuery(ref_node, filename=True, wcn=without_copy_number)

    return ref_file


def reference_paths(objects, without_copy_number=False):
    """
    Returns the reference paths for the given objects
    :param objects: str or list(str)
    :param without_copy_number: bool
    :return: list(str)
    """

    paths = list()

    objects = helpers.force_list(objects)
    for obj in objects:
        if not is_referenced(obj):
            continue
        paths.append(maya.cmds.referenceQuery(obj, filename=True, wcn=without_copy_number))

    return helpers.remove_dupes(paths)


def reference_data(objects):
    """
    Returns the reference data for the given objects
    :param objects: str or list(str)
    :return: list
    """

    data = list()
    paths = reference_paths(objects)

    for path in paths:
        data.append({
            'filename': path,
            'unresolved': maya.cmds.referenceQuery(path, filename=True, withoutCopyNumber=True),
            'namespace': maya.cmds.referenceQuery(path, namespace=True),
            'node': maya.cmds.referenceQuery(path, referenceNode=True),
        })

    return data


def reference_proxy_manager(ref_node):
    """
    Returns the reference proxy manager attached to the the given reference node
    :param ref_node: str
    :return: str
    """

    if not maya.cmds.attributeQuery('proxyMsg', n=ref_node, ex=True):
        logger.warning(
            'Reference "{}" has no proxyMsg attribute! Unable to determine proxy manager ...'.format(ref_node))
        return None

    proxy_manager = maya.cmds.ls(
        maya.cmds.listConnections(ref_node + '.proxyMsg', s=True, d=False) or list(), type='proxyManager') or list()
    if not proxy_manager:
        logger.warning('Reference "{}" has no valid proxyMsg connections! Unable to determine proxy manager ...')
        return None

    if len(proxy_manager) > 1:
        logger.warning('Multiple proxy manager nodes attached to reference "{}"! Returning first node only ...')
        logger.warning(str(proxy_manager))

    return proxy_manager[0]


def references_from_proxy_manager(proxy_manager):
    """
    Returns reference nodes attached to the given proxy manager node
    :param proxy_manager: str, proxy manager node to get refernce nodes from
    :return: list(str)
    """

    if not is_proxy_manager(proxy_manager):
        raise Exception('Object "{}" is not a valid proxyManager node!'.format(proxy_manager))

    ref_list = maya.cmds.listConnections(proxy_manager + '.proxyList', s=False, d=True) or list()

    return ref_list


def namespace(ref_node):
    """
    Returns the namespace associated with the given reference node
    :param ref_node: str
    :return: str
    """

    check_reference(ref_node)

    namespace = maya.cmds.referenceQuery(ref_node, namespace=True)
    if namespace.startswith(':'):
        namespace = namespace[1:]

    return namespace


def reference_from_namespace(namespace, parent_namespace=None):
    """
    Returns the reference node associated with the given namespace
    :param namespace: str, namespace to query reference node from
    :param parent_namespace: str or None, parent namespace to query reference nodes from
    :return: str or None
    """

    if namespace.endswith(':'):
        namespace = namespace[1:]
    if not maya.cmds.namespace(ex=namespace):
        raise Exception('Namespace "{}" does not exists!'.format(namespace))

    if parent_namespace:
        parent_namespace += ':'
    else:
        parent_namespace = ''

    for ref_node in list_references(parent_namespace):
        try:
            ref_namespace = maya.cmds.referenceQuery(ref_node, namespace=True)
        except Exception:
            continue

        if ref_namespace.startswith(':'):
            ref_namespace = ref_namespace[1:]

        if ref_namespace == parent_namespace + namespace:
            if maya.cmds.attributeQuery('proxyMsg', n=ref_node, ex=True):
                proxy_manager = maya.cmds.ls(
                    maya.cmds.listConnections(
                        ref_node + '.proxyMsg', s=True, d=True) or list(), type='proxyManager') or list()
                if proxy_manager:
                    active_proxy_plug = maya.cmds.connectionInfo(
                        proxy_manager[0] + '.activeProxy', destinationFromSource=True)[0]
                    active_proxy_info = maya.cmds.connectionInfo(active_proxy_plug, destinationFromSource=True)
                    if not active_proxy_info:
                        raise Exception(
                            'Error getting active reference from proxy manager "{}"!'.format(proxy_manager[0]))
                    return maya.cmds.ls(active_proxy_info[0], o=True)[0]

            return ref_node

        logger.warning('Unable to determine reference from namespace: {}'.format(namespace))
        return ''


def all_references_from_namespace(namespace):
    """
    Returns all reference nodes associated with the given namespace
    Used to return all reference nodes associated with a Reference Proxy Manager
    :param namespace: str, namespace to query reference nodes from
    :return: str
    """

    ref_main = reference_from_namespace(namespace)
    proxy_manager = reference_proxy_manager(ref_main)
    ref_list = references_from_proxy_manager(proxy_manager)

    return ref_list


def referenced_nodes(ref_node):
    """
    Returns a list of nodes associated with the the given reference nodes
    :param ref_node: str, refernce node to get list of associated nodes
    :return: list(str)
    """

    check_reference(ref_node)

    nodes = maya.cmds.referenceQuery(ref_node, nodes=True, dagPath=True)
    if not nodes:
        return list()

    return nodes


def import_reference(ref_node):
    """
    Imports the reference associated with the given reference node
    :param ref_node: str
    """

    check_reference(ref_node)

    ref_file = ''
    try:
        ref_file = maya.cmds.referenceQuery(ref_node, filename=True)
    except Exception:
        if maya.cmds.objExists(ref_node):
            logger.warning('No file associated with reference! Deleting node "{}"'.format(ref_node))
            maya.cmds.lockNode(ref_node, long=False)
            maya.cmds.delete(ref_node)
        else:
            maya.cmds.file(ref_file, importReference=True)
            logger.debug('Imported reference "{}" from: "{}"'.format(ref_node, ref_file))


def replace_reference(ref_node, ref_path):
    """
    Replaces the reference file path for a given reference node
    :param ref_node: str, reference node to replace file path for
    :param ref_path: str, new reference file path
    """

    check_reference(ref_node)

    if reference_file(ref_node, without_copy_number=True) == ref_path:
        logger.warning('Reference "{}" already referencing "{}"!'.format(ref_node, ref_path))
        return

    if ref_path.endswith('.ma'):
        ref_type = 'mayaAscii'
    elif ref_path.endswith('.mb'):
        ref_type = 'mayaBinary'
    else:
        raise Exception('Invalid file type ("{}")'.format(ref_path))

    maya.cmds.file(ref_path, loadReference=ref_node, typ=ref_type, options='v=0')

    logger.debug('Replaced reference "{}" using file: "{}"'.format(ref_node, ref_path))

    return ref_path


def remove_reference(ref_node):
    """
    Removes the reference associated with the given reference node
    :param ref_node: str
    """

    check_reference(ref_node)

    ref_file = reference_file(ref_node)
    try:
        maya.cmds.file(referenceNode=ref_node, removeReference=True)
    except Exception as e:
        logger.error('Error removing reference "{}! {} | {}'.format(ref_node, e, traceback.format_exc()))
        return False

    logger.debug('Removed reference "{}"! ("{}")'.format(ref_node, ref_file))

    return True


def unload_reference(ref_node):
    """
    Unloads the reference associated with the given reference node
    :param ref_node: str, reference node to unload
    """

    check_reference(ref_node)

    maya.cmds.file(referenceNode=ref_node, unloadReference=True)

    logger.debug('Unloaded reference "{}"! ("{}")'.format(ref_node, reference_file(ref_node)))


def reload_reference(ref_node):
    """
    Reloads the reference associated with the given reference node
    :param ref_node: str
    """

    check_reference(ref_node)

    maya.cmds.file(referenceNode=ref_node, loadReference=True)

    logger.debug('Reloaded reference "{}"! ("{}")'.format(ref_node, reference_file(ref_node)))
