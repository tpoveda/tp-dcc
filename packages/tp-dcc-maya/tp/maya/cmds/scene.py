#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Maya scene.
"""

from __future__ import annotations

import os
import traceback
from typing import Set, List, Tuple, Iterator

from Qt.QtWidgets import QMessageBox

import maya.cmds as cmds

from tp.core import log
from tp.common.python import path as path_utils
from tp.maya.cmds import workspace, undo

logger = log.tpLogger


def is_new_scene() -> bool:
    """
    Returns whether current Maya scene is an untitled one.

    :return: True if current Maya scene is new; False otherwise.
    :rtype: bool
    """

    return len(cmds.file(query=True, sceneName=True)) == 0


def current_scene_name() -> str | None:
    """
    Returns the name of the current scene opened in Maya.

    :return: Maya scene name.
    :rtype: str or None
    """

    scene_path = cmds.file(query=True, sceneName=True)
    if scene_path:
        return os.path.splitext(os.path.basename(scene_path))[0]

    return None


def scene_file(directory: bool = False) -> str:
    """
    Returns the scene file name or directory of the current scene.

    :param bool directory: whether to return scene name or scene path.
    :return: scene file path.
    :rtype: str
    """

    scene_path = cmds.file(q=True, sn=True)
    if directory and scene_path:
        scene_path = path_utils.dirname(scene_path)

    return scene_path


def scene_file_type() -> str | None:
    """
    Returns the current scene file type.

    :return: scene file type.
    :rtype: str or None
    """

    maya_type = None
    scene_path = cmds.file(query=True, l=True)[0]
    if scene_path.lower().endswith('.ma'):
        maya_type = 'mayaAscii'
    elif scene_path.lower().endswith('.mb'):
        maya_type = 'mayaBinary'

    return maya_type


def new_scene(force: bool = True, do_save: bool = True):
    """
    Creates a new Maya scene
    :param bool force: True if we want to save the scene without any prompt dialog.
    :param bool do_save: True if you want to save the current scene before creating new scene.
    """

    if do_save:
        save()

    if not force:
        res = save()
        if res:
            force = True

    try:
        cmds.file(new=True, force=force)
        cmds.flushIdleQueue()
    except Exception:
        raise

    return True


def import_scene(file_path: str, force: bool = True, do_save: bool = True):
    """
    Imports a Maya scene into the current scene.

    :param str file_path: absolute path of the Maya scene to import.
    :param bool force: True if we want to save the scene without any prompt dialog.
    :param bool do_save: True if you want to save the current scene before importing a new scene.
    """

    if do_save:
        save()

    cmds.file(file_path, i=True, force=force, iv=True, pr=True)


def open_scene(file_path: str, force: bool = True, do_save: bool = True):
    """
    Opens a Maya scene given its file path.

    :param str file_path: absolute path of the Maya scene to open.
    :param bool force: True if we want to save the scene without any prompt dialog
    :param bool do_save: True if you want to save the current scene before opening a new scene
    """

    if do_save:
        save()

    cmds.file(file_path, open=True, force=force)


def reference_scene(file_path: str, namespace: str | None = None):
    """
    References a Maya file.

    :param str file_path: absolute path and filename of the scene we want to reference
    :param str or None namespace: optional namespace to add to the nodes in Maya. If None, default is the name of
        the file.
    """

    if not namespace:
        namespace = os.path.basename(file_path)
        split_name = namespace.split('.')
        if split_name:
            namespace = '_'.join(split_name[:-1])

    cmds.file(file_path, reference=True, mergeNamespacesOnClash=False, namespace=namespace)


def current_scene_is_modified() -> bool:
    """
    Returns whether current scene has been modified.

    :return: True if scene is modified; False otherwise.
    :rtype: bool
    """

    return cmds.file(query=True, modified=True)


def current_directory() -> str:
    """
    Returns the director yof the open scene file.

    :return: current open scene directory.
    :rtype: str
    """

    return os.path.split(current_file_path())[0]


def current_file_path() -> str:
    """
    Returns the path of the open scene file.

    :return: current open scene file path.
    :rtype: str
    """

    if not is_new_scene():
        return os.path.normpath(cmds.file(query=True, sceneName=True))

    return ''


def current_file_name(include_name: bool = True, include_extension: bool = True) -> str:
    """
    Returns the name of the current open scene file.

    :param bool include_name: whether to include file name.
    :param bool include_extension: whether to include file extension.
    :return: current open scene file name.
    :rtype: str
    """

    _, file_name = os.path.split(current_file_path())
    name, extension = os.path.splitext(file_name)
    if include_name and include_extension:
        return file_name
    elif include_name:
        return name
    elif include_extension:
        return extension.lstrip('.')

    return ''


def current_extension() -> str:
    """
    Returns the extension of the current open scene file.

    :return: current open scene file extension.
    :rtype: str
    """

    _, file_name = os.path.split(current_file_path())
    return os.path.splitext(file_name)[1].lstrip('.')


def rename_scene(file_path: str):
    """
    Changes the file path on the current open scene file.

    :param str file_path: absolute file path.
    """

    cmds.file(rename=file_path)


def save_scene():
    """
    Saves any changes to the open scene file.
    """

    if is_new_scene():
        return

    extension = current_extension()
    file_type = 'mayaAscii' if extension.lower() == 'ma' else 'mayaBinary'

    cmds.file(save=True, prompt=False, type=file_type)


def save_scene_as(file_path: str):
    """
    Saves the open scene file in a different location.

    :params str file_path: absolute file path to save current scene into.
    """

    rename_scene(file_path)
    save_scene()


def save() -> bool:
    """
    Saves current scene in current Maya file.

    :return: whether the scene was saved.
    :rtype: bool
    """

    file_check_state = cmds.file(query=True, modified=True)
    if file_check_state:
        msg_box = QMessageBox()
        msg_box.setText('The Maya scene has been modified')
        msg_box.setInformativeText('Do you want to save your changes?')
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.Yes)
        res = msg_box.exec_()
        if res == QMessageBox.Yes:
            cmds.SaveScene()
            return True

    return False


def save_as(file_path: str) -> bool:
    """
    Saves Maya scene into the given file path.

    :param str file_path: file path to save scene into.
    :return: whether the scene was saved.
    :rtype: bool
    """

    saved = False
    if not file_path:
        return saved

    logger.debug('Saving "{}"'.format(file_path))

    file_type = 'mayaAscii'
    if file_path.endswith('.mb'):
        file_type = 'mayaBinary'

    try:
        cmds.file(rename=file_path)
        cmds.file(save=True, type=file_type)
        saved = True
    except Exception:
        logger.error(str(traceback.format_exc()))
        saved = False

    if saved:
        logger.debug('Scene saved successfully into: {}'.format(file_path))
    else:
        if not cmds.about(batch=True):
            cmds.confirmDialog(message='Warning:\n\nMaya was unable to save!', button='Confirm')
        logger.warning('Scene not saved: {}'.format(file_path))

    return saved


def save_as_dialog(window_caption: str = 'Save File?', directory: str = '', ok_caption: str = 'OK'):
    """
    Shows a save file dialog and saves it to the new path and returns the name of the file.

    :param str window_caption: title of the save window.
    :param str directory: default directory.
    :param str ok_caption: ok button text.
    :return: path of the file saved.
    :rtype: str
    """

    if not directory:
        current_file_path = cmds.file(query=True, sceneName=True, shortName=False)
        if not current_file_path:
            directory = workspace.project_sub_directory(sub_directory='scenes')
        else:
            directory = os.path.split(current_file_path)[0]

    maya_files_filter = 'Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb)'
    file_path = cmds.fileDialog2(
        fileFilter=maya_files_filter, caption=window_caption, startingDirectory=directory, okCaption=ok_caption)
    if not file_path:
        return file_path
    file_path = file_path[0]
    if file_path.split('.')[-1] == 'ma':
        cmds.file(rename=file_path)
        cmds.file(force=True, type='mayaAscii', save=True)
    if file_path.split('.')[-1] == 'mb':
        cmds.file(rename=file_path)
        cmds.file(force=True, type='mayaBinary', save=True)
    logger.info(f'File save success: "{file_path}"')

    return file_path


def scene_modified_dialogue() -> str:
    """
    Checks whether current file has already been saved and retunrs 'save', 'discard' or 'cancel'.
    If not saved, opens 'save', 'discard' or 'cancel' window and returns the pressed button.
    If 'save' is clicked it will try to save current file.

    :return: clicked button.
    :rtype: str
    """

    # import here to avoid cyclic imports
    from tp.common.qt.widgets import popups

    scene_modified = current_scene_is_modified()
    if not scene_modified:
        cmds.file(newFile=True, force=True)
        return 'save'

    button_pressed = popups.show_save(title='Save File', message='Creating a new scene, save the current file?')
    if button_pressed == 'save':
        if save_as_dialog():
            return 'save'
        else:
            return 'cancel'

    return button_pressed


def current_project_directory() -> str:
    """
    Returns the current project directory.

    :return: current project directory.
    :rtype: str
    """

    return os.path.normpath(cmds.workspace(query=True, directory=True))


def find_texture_node_pairs() -> Set[Tuple[str, str]]:
    """
    Returns pair with scene texture maya node, texture name of texture dependencies of the current scene that are not
    referenced.

    :return: set of found texture node pairs.
    :rtype: Set[Tuple[str, str]]
    """

    paths = set()
    for f in cmds.ls(long=True, type='file'):
        if cmds.referenceQuery(f, isNodeReferenced=True):
            continue

        texture_path = cmds.getAttr(os.path.normpath('.'.join([f, 'fileTextureName'])))
        if texture_path:
            paths.add((f, texture_path))

    return paths


def iterate_texture_node_pairs(include_references: bool = False) -> Iterator[Tuple[str, str]]:
    """
    Generator function that iterates over all texture node pairs within current scene.

    :param bool include_references: whether to include references.
    :return: iterated texture node paris.
    :rtype: Iterator[Tuple[str, str]]
    """

    for f in cmds.ls(long=True, type='file'):
        if include_references and cmds.referenceQuery(f, isNodeReferenced=True):
            continue
        texture_path = cmds.getAttr(os.path.normpath('.'.join([f, 'fileTextureName'])))
        if texture_path:
            yield f, texture_path


def is_batch() -> bool:
    """
    Returns whether Maya is in batch mode.

    :return: True if Maya is being executed in batch mode; False otherwise.
    :rtype: bool
    """

    return cmds.about(query=True, batch=True)


def scene_cameras(
        include_default_cameras: bool = True, include_non_default_cameras: bool = True,
        get_transforms: bool = False) -> List[str]:
    """
    Returns a list with all cameras in the scene.

    :param bool include_default_cameras: bool, Whether to get default cameras.
    :param bool include_non_default_cameras: Whether to get non default cameras.
    :param bool get_transforms: bool, Whether to return cameras shape or camera transform.
    :return: list of scene camera names.
    :rtype: List[str]
    """

    final_list = list()
    cameras = cmds.ls(type='camera', long=True)
    startup_cameras = [camera for camera in cameras if cmds.camera(cmds.listRelatives(
        camera, parent=True)[0], startupCamera=True, q=True)]
    non_startup_cameras = list(set(cameras) - set(startup_cameras))
    if include_default_cameras:
        final_list.extend(startup_cameras)
    if include_non_default_cameras:
        final_list.extend(non_startup_cameras)

    if get_transforms:
        return map(lambda x: cmds.listRelatives(x, parent=True)[0], final_list)

    return final_list


def top_dag_nodes(exclude_cameras: bool = True, namespace: str | None = None) -> List[str]:
    """
    Returns all transform that are at located in the root scene.

    :param bool exclude_cameras: bool, Whether to include or not cameras.
    :param str or None namespace: optional namespace of the objects that we want to get.
    :return: List[str]
    """

    top_transforms = cmds.ls(assemblies=True)
    if exclude_cameras:
        cameras = scene_cameras(get_transforms=True)
        for camera in cameras:
            if camera in top_transforms:
                top_transforms.remove(camera)

    if namespace:
        found = list()
        for transform in top_transforms:
            if transform.startswith(namespace + ':'):
                found.append(transform)
        top_transforms = found

    return top_transforms


def top_dag_nodes_in_list(list_of_transforms: List[str]):
    """
    Given a list of transforms, returns only the ones at the top of the hierarchy (children of the scene root).

    :param List[str] list_of_transforms: list of transforms node names.
    :return: top hierarchy DAG node names.
    :rtype: List[str]
    """

    found = list()
    for xform in list_of_transforms:
        long_name = cmds.ls(xform, long=True)
        if long_name:
            if long_name[0].count('|') == 1:
                found.append(xform)

    return found


def node_transform_root(node: str, full_path: bool = True) -> str:
    """
    Returns the transform root of the given node taking into account its hierarchy.

    :param str node: node name to get root transform of.
    :param bool full_path: whether to return full path.
    :return: root transform node name.
    :rtype: str
    """

    while True:
        parent = cmds.listRelatives(node, parent=True, fullPath=full_path)
        if not parent:
            break

        node = parent[0]

    return node


def all_parent_nodes(node_name: str) -> List[str]:
    """
    Recursive function that returns all parent nodes of the given Maya node.

    :param str node_name: name of the Maya node.
    :return: list of parent nodes.
    :rtype: List[str]
    """

    def _append_parents(node_name_, node_list_):
        """
        Internal function to recursively append parents to list.

        :param str node_name_: node name to get parents of.
        :param List[str] node_list_: recursive list of found nodes.
        """

        parents = cmds.listRelatives(node_name_, parent=True, fullPath=True, type='transform')
        if parents:
            for parent in parents:
                node_list_.append(parent)
                _append_parents(parent, node_list_)

    node_list = list()
    _append_parents(node_name, node_list)

    return node_list


def all_children_nodes(node_name: str) -> List[str]:
    """
    Recursive function that returns all children nodes of the given node.

    :param str node_name: str
    :return: list of children nodes.
    :rtype: List[str]
    """

    def _append_children(node_name_, node_list_):
        """
        Internal function to recursively append children to list.

        :param str node_name_: node name to get children of.
        :param List[str] node_list_: recursive list of found nodes.
        """

        children = cmds.listRelatives(node_name_, fullPath=True, type='transform')
        if children:
            for child in children:
                node_list_.append(child)
                _append_children(child, node_list_)

    node_list = list()
    _append_children(node_name, node_list)

    return node_list


def sets() -> List[str]:
    """
    Returns a list of sets found in the scene (outliner).

    :return: found list of sets.
    :rtype: List[str]
    """

    found_sets = cmds.ls(type='objectSet')
    top_sets = list()
    for obj_set in found_sets:
        if obj_set == 'defaultObjectSet':
            continue

        outputs = cmds.listConnections(
            obj_set, plugs=False, connections=False, destination=True, source=False, skipConversionNodes=True)
        if not outputs:
            top_sets.append(obj_set)

    return top_sets


def has_unknown_nodes() -> bool:
    """
    Returns whether there are unknown nodes within current scene.

    :return: True current scene contains unknown nodes; False otherwise.
    :rtype: bool
    """

    return cmds.ls(type='unknown') is not None


def has_unknown_plugins() -> bool:
    """
    Returns whether there are unknown plugins within current scene.

    :return: True current scene contains unknown plugins; False otherwise.
    :rtype: bool
    """

    return cmds.unknownPlugin(query=True, list=True) is not None


def delete_unknown_nodes():
    """
    Find all unknown nodes and delete them.
    """

    unknown = cmds.ls(type='unknown')
    deleted = list()
    for n in unknown:
        if cmds.objExists(n):
            cmds.lockNode(n, lock=False)
            cmds.delete(n)
            deleted.append(n)

    logger.debug('Deleted unknowns: {}'.format(deleted))


def delete_turtle_nodes():
    """
    Find all turtle nodes in a scene and delete them
    """

    from tp.maya.cmds import node

    plugin_list = cmds.pluginInfo(query=True, pluginsInUse=True)
    turtle_nodes = list()
    if plugin_list:
        for plugin in plugin_list:
            if plugin[0] == 'Turtle':
                turtle_types = ['ilrBakeLayer',
                                'ilrBakeLayerManager',
                                'ilrOptionsNode',
                                'ilrUIOptionsNode']
                turtle_nodes = node.delete_nodes_of_type(turtle_types)
                break

    logger.debug('Removed Turtle nodes: {}'.format(turtle_nodes))


def delete_unused_plugins():
    """
    Removes all nodes in the scene that belongs to unused plugins (plugins that are not loaded)
    """

    # This functionality is not available in old Maya versions
    list_cmds = dir(cmds)
    if 'unknownPlugin' not in list_cmds:
        return

    unknown_nodes = cmds.ls(type='unknown')
    if unknown_nodes:
        return

    unused = list()
    unknown_plugins = cmds.unknownPlugin(query=True, list=True)
    if unknown_plugins:
        for p in unknown_plugins:
            try:
                cmds.unknownPlugin(p, remove=True)
            except Exception:
                continue
            unused.append(p)

    logger.debug('Removed unused plugins: {}'.format(unused))


def delete_garbage():
    """
    Delete all garbage nodes from scene
    """

    from tp.maya.cmds import helpers, node

    straight_delete_types = list()
    if helpers.maya_version() > 2014:
        straight_delete_types += ['hyperLayout', 'hyperView']       # Maya 2014 crashes when tyring to remove those
        if 'hyperGraphLayout' in straight_delete_types:
            straight_delete_types.remove('hyperGraphLayout')

    deleted_nodes = node.delete_nodes_of_type(straight_delete_types)
    check_connection_node_type = ['shadingEngine', 'partition', 'objectSet']
    check_connection_nodes = list()
    for check_type in check_connection_node_type:
        nodes_of_type = cmds.ls(type=check_type)
        check_connection_nodes += nodes_of_type

    garbage_nodes = list()
    if deleted_nodes:
        garbage_nodes = deleted_nodes

    nodes_to_skip = ['characterPartition']

    for n in check_connection_nodes:
        if not n or not cmds.objExists(n):
            continue
        if n in nodes_to_skip:
            continue
        if node.is_empty(n):
            cmds.lockNode(n, lock=False)
            try:
                cmds.delete(n)
            except Exception:
                pass

            if not cmds.objExists(n):
                garbage_nodes.append(n)

    logger.debug('Delete Garbage Nodes: {}'.format(garbage_nodes))


def clean_scene():
    """
    Cleans invalid nodes from current scene
    """

    delete_unknown_nodes()
    delete_turtle_nodes()
    delete_unused_plugins()
    delete_garbage()


def time() -> int:
    """
    Returns scene current time.

    :return: current time.
    :rtype: int
    """

    return int(cmds.currentTime(query=True))


@undo.undo(state=False)
def set_time(time_value: int):
    """
    Updates current scene time.

    :param int time_value: new scene time.
    """

    cmds.currentTime(time, edit=True)


def auto_key() -> bool:
    """
    Returns the auto-key state.

    :return: True if auto key is enabled; False otherwise.
    :rtype: bool
    """

    return cmds.autoKeyframe(query=True, state=True)


class TrackNodes:
    """
    Helps track new nodes that get added to a scene after a function is called. e.g:
        track_nodes = TrackNodes()
        track_nodes.load()
        custom_funct()
        new_nodes = track_nodes.get_delta()
    """

    def __init__(self, full_path: bool = False):

        self._full_path = full_path

        self._nodes = None                              # type: List[str]
        self._node_type = None                          # type: str
        self._delta = None                              # type: Set[str]

    def load(self, node_type: str | None = None):
        """
        Initializes TrackNodes states.

        :param str node_type: Maya node type we want to track. If not given, all current scene objects wil lbe tracked.
        """

        self._node_type = node_type
        if self._node_type:
            self._nodes = cmds.ls(type=node_type, long=self._full_path)
        else:
            self._nodes = cmds.ls()

    def get_delta(self) -> List[str]:
        """
        Returns the new nodes in the Maya scen created after load() was executed.

        :return: list of new nodes.
        :rtype: List[str]
        """

        if self._node_type:
            current_nodes = cmds.ls(type=self._node_type, long=self._full_path)
        else:
            current_nodes = cmds.ls(long=self._full_path)

        new_set = set(current_nodes).difference(self._nodes)

        return list(new_set)
