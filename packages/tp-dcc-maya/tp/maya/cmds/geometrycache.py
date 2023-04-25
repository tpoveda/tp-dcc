#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Geometry Cache related functionality for Maya
"""

import os

import maya.cmds
import maya.mel


def load_abc_import_plugin():
    """
    Loads Alembic Import Maya Plugin (AbcImport)
    """

    if not maya.cmds.pluginInfo('AbcImport', query=True, loaded=True):
        try:
            maya.cmds.loadPlugin('AbcImport', quiet=True)
        except Exception:
            raise Exception('Error while loading AbcImport Maya plugin!')


def load_abc_export_plugin():
    """
    Loads Alembic Export Maya Plugin (AbcExport)
    """

    if not maya.cmds.pluginInfo('AbcExport', query=True, loaded=True):
        try:
            maya.cmds.loadPlugin('AbcExport', quiet=True)
        except Exception:
            raise Exception('Error while loading AbcExport Maya plugin!¡')


def load_gpu_cache_plugin():
    """
    Loads GPU Cache Maya Plugin (gpuCache)
    """

    if not maya.cmds.pluginInfo('gpuCache', query=True, loaded=True):
        try:
            maya.cmds.loadPlugin('gpuCache', quiet=True)
        except Exception:
            raise Exception('Error while loading gpuCache Maya plugin!')


def is_alembic_node(node):
    """
    Returns whether or not given node is a valid Alembic cache node
    :param node: str, name of the object to query
    :return: bool
    """

    if not maya.cmds.objExists(node):
        return False

    if maya.cmds.objectType(node) != 'AlembicNode':
        return False

    return True


def is_gpu_cache_node(node):
    """
    Returns whether or not given node is a valid GPU cache node
    :param node: name of the object to query
    :return: bool
    """

    if not maya.cmds.objExists(node):
        return False

    if maya.cmds.objectType(node) != 'gpuCache':
        return False

    return True


def connect_time(cache_node, time_attr='time1.outTime'):
    """
    Connects a given driver attribute to the time input for a named cache node
    :param cache_node: str, cache connect to connect time into
    :param time_attr: str, attribute name to drive the cache node time value
    """

    if not maya.cmds.objExists(time_attr):
        raise Exception('Time attribute "{}" does not exist!'.format(time_attr))

    maya.cmds.connectAttr(time_attr, '{}.time'.format(cache_node), force=True)


def disconnect_time(cache_node):
    """
    Disconnects the time attribute for the given cache node
    :param cache_node: str, cache node to disconnect time from
    """

    time_connection = maya.cmds.listConnections(
        '{}.time'.format(cache_node), source=True, destination=False, plugs=True)
    if not time_connection:
        return

    maya.cmds.disconnectAttr(time_connection[0], '{}.time'.format(cache_node))


def alembic_time_offset(offset_node, offset_attr='alembicTimeOffset', cache_list=None):
    """
    Configures a time offset attribute to control the incoming time value for the given cache nodes
    :param offset_node: str, node that will hold the time offset attribute
    :param offset_attr: str, time offset attribute name
    :param cache_list: list(str), list of cache nodes to connect to time offset
    """

    if not cache_list:
        return ''

    if not maya.cmds.objExists(offset_node):
        raise Exception('Offset node "{}" does not exist!'.format(offset_node))

    if not offset_attr:
        offset_attr = 'alembicTimeOffset'

    if not maya.cmds.objExists('{}.{}'.format(offset_node, offset_attr)):
        maya.cmds.addAttr(offset_node, ln=offset_attr, at='long', dv=0, k=True)

    for cache in cache_list:
        time_connection = maya.cmds.listConnections('{}.time'.format(cache), s=True, d=True, p=True)
        if not time_connection:
            time_connection = ['time1.outTime']

        add_node = maya.cmds.createNode('addDoubleLinear', n='{}_abcOffset_addDoubleLinear'.format(cache))

        maya.cmds.connectAttr(time_connection[0], '{}.input1'.format(add_node), force=True)
        maya.cmds.connectAttr('{}.{}'.format(offset_node, offset_attr), '{}.input2'.format(add_node), force=True)
        maya.cmds.connectAttr('{}.output'.format(add_node), '{}.time'.format(cache), force=True)

    return '{}.{}'.format(offset_node, offset_attr)


def import_cache_to_geometry(geometry, cache_file):
    """
    Imports and connects geometry cache file to the given geometry
    :param geometry: str, geometry to load cache to
    :param cache_file: str, geometry cache file path to load
    """

    if not maya.cmds.objExists(geometry):
        raise Exception('Geometry "{}" does not exist!'.format(geometry))

    if not os.path.isfile(cache_file):
        raise Exception('Cache file "{}" does not exist!'.format(cache_file))

    maya.mel.eval('doImportCacheFile "' + cache_file + '" "" {"' + geometry + '"} {}')


def import_cache_to_geometries(geo_list, cache_directory, cache_file_list=None, extension='.abc'):
    """
    Imports and connects geometry cache files from a given path to the input geometry list
    :param geo_list: list(str), list of geometry load cache to
    :param cache_directory: str, directory path to load cache files from
    :param cache_file_list: list(str), list of cache files to load. If empty, geometry shape nodes will be used
    :param extension: list(str), str, cache file extension
    """

    if not os.path.isdir(cache_directory):
        raise Exception('Cache Directory "{}" does not exist!'.format(cache_directory))
    if not cache_directory.endswith('/'):
        cache_directory += '/'

    if cache_file_list is None:
        cache_file_list = list()

    if cache_file_list and not (len(cache_file_list) == len(geo_list)):
        raise Exception('Cache files and gemetries list have not the same amount of elements!')

    if not extension.endswith('.'):
        extension = '.{}'.format(extension)

    for i in range(len(geo_list)):
        if not maya.cmds.objExists(geo_list[i]):
            raise Exception('Geometry "{}" does not exist!'.format(geo_list[i]))
        if cache_file_list:
            cache_file = '{}{}{}'.format(cache_directory, cache_file_list[i], extension)
        else:
            shape_list = maya.cmds.listRelatives(geo_list[i], s=True, ni=True, pa=True)
            if not shape_list:
                raise Exception('No valid shape found for geometry!')
            geo_shape = shape_list[0]
            cache_file = '{}{}{}'.format(cache_directory, geo_shape, extension)

        if not os.path.isfile(cache_file):
            raise Exception('Cache file "{}" does not exist!'.format(cache_file))

        import_cache_to_geometry(geo_list[i], cache_file)


def export_cache_from_geometry(
        geometry, cache_file, start_frame=1, end_frame=100, use_time_line=True,
        file_per_frame=False, cache_per_geo=True, force_export=False):
    """
    Exports caches from given geometries
    :param geometry: str, geometry to export cache from
    :param cache_file: str, output file name
    :param start_frame: int, start frame for cache output
    :param end_frame: int, end frame for cache output
    :param use_time_line: bool, get start and enf frames from the time line
    :param file_per_frame: bool, write file per frame or in a single file
    :param cache_per_geo: bool, write file per shape or single file
    :param force_export: bool, force export even if it overwrites existing files
    """

    version = 5                 # 2010
    refresh = 1                 # Refresh during caching
    use_prefix = 0              # Name as prefix
    cache_action = 'export'     # Cache actino ('add', 'replace', 'merge', 'mergeDelete' or 'export'

    if use_time_line:
        start_frame = maya.cmds.playbackOptions(query=True, ast=True)
        end_frame = maya.cmds.playbackOptions(query=True, aet=True)

    if file_per_frame:
        cache_dist = 'OneFilePerFrame'
    else:
        cache_dist = 'OneFile'

    file_name = cache_file.split('/')[-1]
    cache_dir = cache_file.replace(file_name, '')
    base_name = file_name.replace('.' + file_name.split('.')[-1], '')

    maya.cmds.select(geometry)
    maya.mel.eval('doCreateGeometryCache ' + str(version) + ' {"0","' + str(start_frame) + '","' + str(
        end_frame) + '","' + cache_dist + '","' + str(refresh) + '","' + cache_dir + '","' + str(
        int(cache_per_geo)) + '","' + base_name + '","' + str(use_prefix) + '","' + cache_action + '","' + str(
        int(force_export)) + '","1","1","0","0","mcc" };')


def import_abc_cache(cache_path='', cache_name='', namespace='', parent='', mode='import', debug=False):
    """
    Imports an alembic cache from file
    :param cache_path: str, alembic cache file path
    :param cache_name: str, alembic cache name. If empty, file name will be used
    :param namespace: str, namespace for cache
    :param parent: str, reparent the whole hierarchy under an existing node in the current scene
    :param mode: str, import mode ('import', 'open' or 'replace')
    :param debug: bool, whether turn on or off debug messages
    """

    from tpDcc.dccs.maya.core import namespace as namespace_utils

    if not os.path.isfile(cache_path):
        raise Exception('Cache Path "{}" does not exist!')

    load_abc_import_plugin()

    if not cache_name:
        cache_base = os.path.basename(cache_path)
        cache_name = os.path.splitext(cache_base)[-1]

    if namespace:
        if maya.cmds.namespace(ex=namespace):
            index = 1
            while maya.cmds.namespace(ex='{}{}'.format(namespace, index)):
                index += 1
            namespace = '{}{}'.format(namespace, index)

    cache_node = maya.cmds.AbcImport(cache_path, mode=mode, debug=debug)
    cache_node = maya.cmds.rename(cache_node, '{}Cache'.format(cache_name))

    cache_list = maya.cmds.listConnections(cache_node, s=False, d=True)

    root_list = list()
    for cache_item in cache_list:
        root = cache_item
        while maya.cmds.listRelatives(root, p=True) is not None:
            root = maya.cmds.listRelatives(root, p=True, pa=True,)[0]
        if not root_list.count(root):
            root_list.append(root)

    if namespace:
        for root in root_list:
            namespace_utils.add_hierarchy_to_namespace(root, namespace)

    if parent:
        if not maya.cmds.objExists(parent):
            parent = maya.cmds.group(empty=True, n=parent)

        maya.cmds.parent(root_list, parent)

    return cache_node


def import_gpu_cache(cache_path, cache_name=None, namespace='', unique_namespace=True):
    """
    Import GPU Alembic cache from file
    :param cache_path: str, alembic cache file path
    :param cache_name: str, alembic cache name. If empty, filename will be used
    :param namespace: str, namespace of the imported gpu alembic node
    :param unique_namespace: bool
    """

    if not os.path.isfile(cache_path):
        raise Exception('Cache Path "{}" does not exist!'.format(cache_path))

    load_abc_import_plugin()

    if not cache_name:
        cache_base = os.path.basename(cache_path)
        cache_name = os.path.splitext(cache_base)[0]

    if namespace:
        if maya.cmds.namespace(ex=namespace) and unique_namespace:
            index = 1
            while maya.cmds.namespace(ex='{}{}'.format(namespace, index)):
                index += 1
            namespace = '{}{}'.format(namespace, index)

    cache_node = maya.cmds.createNode('gpuCache', name='{}Shape'.format(cache_name))
    cache_parent = maya.cmds.listRelatives(cache_node, p=True, pa=True)
    cache_parent = maya.cmds.rename(cache_parent, cache_name)

    maya.cmds.setAttr('{}.cacheFileName'.format(cache_node), cache_path, type='string')

    if namespace:
        if not maya.cmds.namespace(ex=namespace):
            maya.cmds.namespace(add=namespace)

        cache_parent = maya.cmds.rename(cache_parent, '{}:{}'.format(namespace, cache_parent))
        cache_node = maya.cmds.listRelatives(cache_parent, s=True, pa=True)[0]

    return cache_node


def load_abc_from_gpu_cache(gpu_cache_node, debug=False):
    """
    Loads ALembic cache from a given gpuCache node
    :param gpu_cache_node: str, gpu cache node to replace with alembic cache
    :param debug: bool, print debug info
    """

    from tpDcc.dccs.maya.core import namespace as namespace_utils

    if not is_gpu_cache_node(gpu_cache_node):
        raise Exception('Object "{}" is not a valid GPU Cache node!'.format(gpu_cache_node))

    load_abc_import_plugin()

    cache_path = maya.cmds.getAttr('{}.cacheFileName'.format(gpu_cache_node))
    cache_xform = maya.cmds.listRelatives(gpu_cache_node, p=True, pa=True)[0]
    cache_parent = maya.cmds.listRelatives(cache_xform, p=True, pa=True)
    if not cache_parent:
        cache_parent = ''

    cache_namespace = namespace_utils.namespace(name=gpu_cache_node)

    cache_name = gpu_cache_node
    # if gpu_cache_node.count('Cache'):
    #     cache_name = gpu_cache_node.replace('Cache', '')

    maya.cmds.delete(cache_xform)

    cache_node = import_abc_cache(
        cache_path, cache_name=cache_name, namespace=cache_namespace, parent=cache_parent, mode='import', debug=debug)

    if cache_parent:
        maya.cmds.parent(cache_xform, cache_parent)

    return cache_node
