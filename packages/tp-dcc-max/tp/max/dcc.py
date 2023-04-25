#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC functionality for 3ds Max
"""

from collections import OrderedDict

from Qt.QtWidgets import QApplication, QMainWindow

import numpy as np

from pymxs import runtime as rt

from tp.core import dcc
from tp.common.math import matrix
from tp.common.python import decorators, path as path_utils

from tp.max.core import gui, helpers, scene, directory, viewport, constants as max_constants, node as node_utils
from tp.max.core import name as name_utils


# =================================================================================================================
# GENERAL
# =================================================================================================================

def get_name():
    """
    Returns the name of the DCC
    :return: str
    """

    return dcc.Dccs.Max


def get_extensions():
    """
    Returns supported extensions of the DCC
    :return: list(str)
    """

    return ['.max']


def get_version():
    """
    Returns version of the DCC
    :return: int
    """

    return int(helpers.get_max_version())


def get_version_name():
    """
    Returns version of the DCC
    :return: str
    """

    return str(helpers.get_max_version())


def is_batch():
    """
    Returns whether DCC is being executed in batch mode or not
    :return: bool
    """

    # TODO: Find a way to check if 3ds Max is being executed in batch mode or not
    return False


def set_workspace(workspace_path):
    """
    Sets current workspace to the given path
    :param workspace_path: str
    """

    return rt.pathConfig.setCurrentProjectFolder(workspace_path)


def fit_view(animation=True):
    """
    Fits current viewport to current selection
    :param animation: bool, Animated fit is available
    """

    # Zoom Extents Selected action
    rt.actionMan.executeAction(0, "310")


# =================================================================================================================
# GUI
# =================================================================================================================

def get_dpi(value=1):
    """
    Returns current DPI used by DCC
    :param value: float
    :return: float
    """

    qt_dpi = QApplication.devicePixelRatio() if is_batch() else QMainWindow().devicePixelRatio()

    return qt_dpi * value


def get_dpi_scale(value):
    """
    Returns current DPI scale used by DCC
    :return: float
    """

    # TODO: As far as I know there is kno way to return DPI info from 3ds Max
    return 1.0


def get_main_window():
    """
    Returns Qt object that references to the main DCC window
    :return:
    """

    return gui.get_max_window()


def get_main_menubar():
    """
    Returns Qt object that references to the main DCC menubar
    :return:
    """

    win = get_main_window()
    menu_bar = win.menuBar()

    return menu_bar


def select_file_dialog(title, start_directory=None, pattern=None):
    """
    Shows select file dialog
    :param title: str
    :param start_directory: str
    :param pattern: str
    :return: str
    """

    return directory.open_file_dialog(caption=title, start_directory=start_directory, filters=pattern)


def save_file_dialog(title, start_directory=None, pattern=None):
    """
    Shows save file dialog
    :param title: str
    :param start_directory: str
    :param pattern: str
    :return: str
    """

    return directory.save_file_dialog(caption=title, start_directory=start_directory, filters=pattern)


# =================================================================================================================
# OBJECTS / NODES
# =================================================================================================================

def node_types():
    """
    Returns dictionary that provides a mapping between tpDcc object types and  DCC specific node types
    Can be the situation where a tpDcc object maps maps to more than one MFn object
    None values are ignored. This is because either do not exists or there is not equivalent type in Maya
    :return: dict
    """

    return OrderedDict()


def dcc_to_tpdcc_types():
    """
    Returns a dictionary that provides a mapping between Dcc object types and tpDcc object types
    :return:
    """

    dcc_to_abstract_types = OrderedDict()
    for abstract_type, dcc_type in node_types().items():
        if isinstance(dcc_type[0], (tuple, list)):
            for item in dcc_type[0]:
                dcc_to_abstract_types[item] = abstract_type
        else:
            dcc_to_abstract_types[dcc_type[0]] = abstract_type


def rename_node(node, new_name, **kwargs):
    """
    Renames given node with new given name
    :param node: str
    :param new_name: str
    :return: str
    """

    pymxs_node = node_utils.get_pymxs_node(node)
    pymxs_node.name = new_name

    return pymxs_node.name


# =================================================================================================================
# NAMING
# =================================================================================================================

def find_unique_name(
        obj_names=None, filter_type=None, include_last_number=True, do_rename=False,
        search_hierarchy=False, selection_only=True, **kwargs):
    """
    Returns a unique node name by adding a number to the end of the node name
    :param obj_names: str, name or list of names to find unique name from
    :param filter_type: str, find unique name on nodes that matches given filter criteria
    :param include_last_number: bool
    :param do_rename: bool
   :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search only selected objects or all scene object
    :return: str
    """

    return name_utils.find_unique_name(obj_names=obj_names)


def add_name_prefix(
        prefix, obj_names=None, filter_type=None, add_underscore=False, search_hierarchy=False,
        selection_only=True, **kwargs):
    """
    Add prefix to node name
    :param prefix: str, string to add to the start of the current node
    :param obj_names: str or list(str), name of list of node names to rename
    :param filter_type: str, name of object type to filter the objects to apply changes ('Group, 'Joint', etc)
    :param add_underscore: bool, Whether or not to add underscore before the suffix
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search only selected objects or all scene objects
    :param kwargs:
    """

    selected_nodes, _ = scene.get_selected_nodes()
    if not selected_nodes:
        return

    for node in selected_nodes:
        new_name = '{}{}'.format(prefix, node.name)
        rename_node(node, new_name)


# =================================================================================================================
# SCENE
# =================================================================================================================

def new_scene(force=True, do_save=True):
    """
    Creates a new DCC scene
    :param force: bool, True if we want to save the scene without any prompt dialog
    :param do_save: bool, True if you want to save the current scene before creating new scene
    :return:
    """

    return scene.new_scene(force=force, do_save=do_save)


def node_exists(node):
    """
    Returns whether given object exists or not
    :return: bool
    """

    node = node_utils.get_pymxs_node(node)
    return rt.isValidNode(node)


def select_node(node, replace_selection=True, **kwargs):
    """
    Selects given object in the current scene
    :param replace_selection: bool
    :param node: str
    """

    node = node_utils.get_pymxs_node(node)

    if replace_selection:
        return rt.select(node)
    else:
        return rt.selectMore(node)


def deselect_node(node):
    """
    Deselects given node from current selection
    :param node: str
    """

    node = node_utils.get_pymxs_node(node)
    return rt.deselect(node)


def clear_selection():
    """
    Clears current scene selection
    """

    return rt.clearSelection()


def selected_nodes(full_path=True, **kwargs):
    """
    Returns a list of selected nodes
    :param full_path: bool
    :return: list(str)
    """

    # By default, we return always selected nodes as handles
    as_handle = kwargs.get('as_handle', True)
    current_selection = rt.getCurrentSelection()
    if as_handle:
        current_selection = [node.handle for node in current_selection]
    return list(current_selection)


# =================================================================================================================
# ATTRIBUTES
# =================================================================================================================

def is_attribute_locked(node, attribute_name):
    """
    Returns whether given attribute is locked or not
    :param node: str
    :param attribute_name: str
    :return: bool
    """

    node = node_utils.get_pymxs_node(node)
    lock_flags = list(rt.getTransformLockFlags(node))

    xform_attrs = [
        max_constants.TRANSLATION_ATTR_NAME, max_constants.ROTATION_ATTR_NAME, max_constants.SCALE_ATTR_NAME]
    for name, flags_list in zip(xform_attrs, [[0, 1, 2], [3, 4, 5], [6, 7, 8]]):
        if name in attribute_name:
            if attribute_name == name:
                for flag_index in flags_list:
                    if not lock_flags[flag_index]:
                        return False
                return True
            else:
                for i, (axis, flag_value) in enumerate(zip('XYZ', flags_list)):
                    flag_index = flags_list[i]
                    if attribute_name == '{}{}'.format(name, axis) and lock_flags[flag_index]:
                        return True

    return False


def lock_translate_attributes(node):
    """
    Locks all translate transform attributes of the given node
    :param node: str
    """

    node = node_utils.get_pymxs_node(node)
    lock_flags = list(rt.getTransformLockFlags(node))
    lock_flags[0] = True
    lock_flags[1] = True
    lock_flags[2] = True
    to_bit_array = list()
    for i, elem in enumerate(lock_flags):
        if elem:
            to_bit_array.append(i + 1)
    ms_array = helpers.convert_python_list_to_maxscript_bit_array(to_bit_array)

    return rt.setTransformLockFlags(node, ms_array)


def unlock_translate_attributes(node):
    """
    Unlocks all translate transform attributes of the given node
    :param node: str
    """

    node = node_utils.get_pymxs_node(node)
    lock_flags = list(rt.getTransformLockFlags(node))
    lock_flags[0] = False
    lock_flags[1] = False
    lock_flags[2] = False
    to_bit_array = list()
    for i, elem in enumerate(lock_flags):
        if elem:
            to_bit_array.append(i + 1)
    ms_array = helpers.convert_python_list_to_maxscript_bit_array(to_bit_array)

    return rt.setTransformLockFlags(node, ms_array)


def lock_rotate_attributes(node):
    """
    Locks all rotate transform attributes of the given node
    :param node: str
    """

    node = node_utils.get_pymxs_node(node)
    lock_flags = list(rt.getTransformLockFlags(node))
    lock_flags[3] = True
    lock_flags[4] = True
    lock_flags[5] = True
    to_bit_array = list()
    for i, elem in enumerate(lock_flags):
        if elem:
            to_bit_array.append(i + 1)
    ms_array = helpers.convert_python_list_to_maxscript_bit_array(to_bit_array)

    return rt.setTransformLockFlags(node, ms_array)


def unlock_rotate_attributes(node):
    """
    Unlocks all rotate transform attributes of the given node
    :param node: str
    """

    node = node_utils.get_pymxs_node(node)
    lock_flags = list(rt.getTransformLockFlags(node))
    lock_flags[3] = False
    lock_flags[4] = False
    lock_flags[5] = False
    to_bit_array = list()
    for i, elem in enumerate(lock_flags):
        if elem:
            to_bit_array.append(i + 1)
    ms_array = helpers.convert_python_list_to_maxscript_bit_array(to_bit_array)

    return rt.setTransformLockFlags(node, ms_array)


def lock_scale_attributes(node):
    """
    Locks all scale transform attributes of the given node
    :param node: str
    """

    node = node_utils.get_pymxs_node(node)
    lock_flags = list(rt.getTransformLockFlags(node))
    lock_flags[6] = True
    lock_flags[7] = True
    lock_flags[8] = True
    to_bit_array = list()
    for i, elem in enumerate(lock_flags):
        if elem:
            to_bit_array.append(i + 1)
    ms_array = helpers.convert_python_list_to_maxscript_bit_array(to_bit_array)

    return rt.setTransformLockFlags(node, ms_array)


def unlock_scale_attributes(node):
    """
    Unlocks all scale transform attributes of the given node
    :param node: str
    """

    node = node_utils.get_pymxs_node(node)
    lock_flags = list(rt.getTransformLockFlags(node))
    lock_flags[6] = False
    lock_flags[7] = False
    lock_flags[8] = False
    to_bit_array = list()
    for i, elem in enumerate(lock_flags):
        if elem:
            to_bit_array.append(i + 1)
    ms_array = helpers.convert_python_list_to_maxscript_bit_array(to_bit_array)

    return rt.setTransformLockFlags(node, ms_array)


def get_attribute_value(node, attribute_name):
    """
    Returns the value of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :return: variant
    """

    node = node_utils.get_pymxs_node(node)

    try:
        return rt.getProperty(node, attribute_name)
    except Exception:
        return None


def set_integer_attribute_value(node, attribute_name, attribute_value, clamp=False):
    """
    Sets the integer value of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :param attribute_value: int
    :param clamp: bool
    :return:
    """

    node = node_utils.get_pymxs_node(node)
    xform_attrs = [
        max_constants.TRANSLATION_ATTR_NAME, max_constants.ROTATION_ATTR_NAME, max_constants.SCALE_ATTR_NAME]

    for xform_attr in xform_attrs:
        if xform_attr in attribute_name:
            xform = attribute_name[:-1]
            axis = attribute_name[-1]
            if axis.lower() not in max_constants.AXES:
                continue
            axis_index = max_constants.AXES.index(axis.lower())
            xform_controller = rt.getPropertyController(node.controller, xform)
            # TODO: For now we only support default transform controllers (Bezier Float for translation,
            # TODO: Euler_XYZ for rotation and Bezier Scale for scale). Support other controller types.

            if xform == max_constants.TRANSLATION_ATTR_NAME or xform == max_constants.ROTATION_ATTR_NAME:
                xform_channel = rt.getPropertyController(xform_controller, '{} {}'.format(axis.lower(), xform))
                xform_channel.value = attribute_value
                return
            elif xform == max_constants.SCALE_ATTR_NAME:
                current_scale = xform_controller.value
                current_scale[axis_index] = attribute_value
                xform_controller.value = current_scale
                return

    try:
        return rt.setProperty(node, attribute_name, attribute_value)
    except Exception:
        pass


def set_float_attribute_value(node, attribute_name, attribute_value, clamp=False):
    """
    Sets the integer value of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :param attribute_value: int
    :param clamp: bool
    :return:
    """

    node = node_utils.get_pymxs_node(node)
    xform_attrs = [
        max_constants.TRANSLATION_ATTR_NAME, max_constants.ROTATION_ATTR_NAME, max_constants.SCALE_ATTR_NAME]

    for xform_attr in xform_attrs:
        if xform_attr in attribute_name:
            xform = attribute_name[:-1]
            axis = attribute_name[-1]
            if axis.lower() not in max_constants.AXES:
                continue
            axis_index = max_constants.AXES.index(axis.lower())
            xform_controller = rt.getPropertyController(node.controller, xform)
            # TODO: For now we only support default transform controllers (Bezier Float for translation,
            # TODO: Euler_XYZ for rotation and Bezier Scale for scale). Support other controller types.

            if xform == max_constants.TRANSLATION_ATTR_NAME or xform == max_constants.ROTATION_ATTR_NAME:
                xform_channel = rt.getPropertyController(xform_controller, '{} {}'.format(axis.lower(), xform))
                xform_channel.value = attribute_value
                return
            elif xform == max_constants.SCALE_ATTR_NAME:
                current_scale = xform_controller.value
                current_scale[axis_index] = attribute_value
                xform_controller.value = current_scale
                return

    try:
        return rt.setProperty(node, attribute_name, attribute_value)
    except Exception:
        pass


def new_file(force=True):
    """
    Creates a new file
    :param force: bool
    """

    scene.new_scene(force=force)


def open_file(file_path, force=True):
    """
    Open file in given path
    :param file_path: str
    :param force: bool
    """

    if force:
        return rt.loadMaxFile(file_path)

    file_check_state = rt.getSaveRequired()
    if not file_check_state:
        return rt.loadMaxFile(file_path)

    if rt.checkForSave():
        return rt.loadMaxFile(file_path, quiet=True)

    return None


def import_file(file_path, force=True, **kwargs):
    """
    Imports given file into current DCC scene
    :param file_path: str
    :param force: bool
    :return:
    """

    return rt.importFile(file_path, noPrompt=force)


def merge_file(file_path, force=True, **kwargs):
    """
    Merges given file into current DCC scene
    :param file_path: str
    :param force: bool
    :return:
    """

    return rt.mergeMAXFile(file_path)

# def reference_file(file_path, force=True, **kwargs):
#     """
#     References given file into current DCC scene
#     :param file_path: str
#     :param force: bool
#     :param kwargs: keyword arguments
#     :return:
#     """
#
#     pass


def import_obj_file(file_path, force=True, **kwargs):
    """
    Imports OBJ file into current DCC scene
    :param file_path: str
    :param force: bool
    :param kwargs: keyword arguments
    :return:
    """

    if force:
        return rt.importFile(file_path, rt.readValue(rt.StringStream('#noPrompt')), using='OBJIMP')
    else:
        return rt.importFile(file_path, using='OBJIMP')


def import_fbx_file(file_path, force=True, **kwargs):
    """
    Imports FBX file into current DCC scene
    :param file_path: str
    :param force: bool
    :param kwargs: keyword arguments
    :return:
    """

    skin = kwargs.get('skin', True)
    animation = kwargs.get('animation', True)

    rt.FBXExporterSetParam("Mode", rt.readvalue(rt.StringStream('#create')))
    # rt.FBXExporterSetParam("Skin", skin)
    # rt.FBXExporterSetParam("Animation", animation)

    if force:
        return rt.importFile(file_path, rt.readValue(rt.StringStream('#noPrompt')))
    else:
        return rt.importFile(file_path)


def scene_name():
    """
    Returns the name of the current scene
    :return: str
    """

    return scene.get_scene_name()


def save_current_scene(force=True, **kwargs):
    """
    Saves current scene
    :param force: bool
    """

    path_to_save = kwargs.get('path_to_save', None)
    name_to_save = kwargs.get('name_to_save', None)
    extension_to_save = kwargs.get('extension_to_save', get_extensions()[0])

    current_scene_name = rt.maxFileName
    if not extension_to_save.startswith('.'):
        extension_to_save = '.{}'.format(extension_to_save)
    name_to_save = name_to_save or current_scene_name
    if not name_to_save:
        return

    file_to_save = path_utils.join_path(path_to_save, name_to_save)
    if not file_to_save.endswith(extension_to_save):
        file_to_save = '{}{}'.format(file_to_save, extension_to_save)

    if force:
        return rt.saveMaxFile(file_to_save, quiet=True)
    else:
        file_check_state = rt.getSaveRequired()
        if not file_check_state:
            return rt.saveMaxFile(file_to_save)
        if rt.checkForSave():
            return rt.saveMaxFile(file_to_save)


def refresh_viewport():
    """
    Refresh current DCC viewport
    """

    viewport.force_redraw()


def enable_undo():
    """
    Enables undo functionality
    """

    return False


def disable_undo():
    """
    Disables undo functionality
    """

    return False


def get_all_fonts():
    """
    Returns all fonts available in DCC
    :return: list(str)
    """

    return list()


def get_control_colors():
    """
    Returns control colors available in DCC
    :return: list(tuple(float, float, float))
    """

    return list()


# =================================================================================================================
# TRANSFORMS
# =================================================================================================================

def convert_translation(translation):
    """
    Converts given translation into a valid translation to be used with tpDcc
    NOTE: tpDcc uses Y up coordinate axes as the base reference axis
    NOTE: 3ds Max works with Z up axis. We must do the conversion.
    :param translation: list(float, float, float)
    :return: list(float, float, float)
    """

    return translation[0], -translation[2], translation[1]


def convert_dcc_translation(translation):
    """
    Converts given tpDcc translation into a translation that DCC can manage
    NOTE: tpDcc uses Y up coordinate axes as the base reference axis
    :param translation: list(float, float, float)
    :return: list(float, float, float)
    """

    return translation[0], translation[2], -translation[1]


def convert_rotation(rotation):
    """
    Converts given rotation into a valid rotation to be used with tpDcc
    NOTE: tpDcc uses Y up coordinate axes as the base reference axis
    NOTE: 3ds Max works with Z up axis. We must do the conversion.
    :param rotation: tuple(float, float, float)
    :return: tuple(float, float, float)
    """

    rotation_matrix1 = np.array(matrix.rotation_matrix_xyz(rotation))
    rotation_matrix2 = np.array(matrix.rotation_matrix_xyz([-90, 0, 0]))
    rotation_matrix3 = matrix.rotation_matrix_to_xyz_euler(
        rotation_matrix2.dot(rotation_matrix1).dot(np.linalg.inv(rotation_matrix2)))

    return list(rotation_matrix3)


def convert_dcc_rotation(rotation):
    """
    Converts given rotation into a rotation that DCC can manage
    NOTE: tpDcc uses Y up coordinate axes as the base reference axis
    :param rotation: list(float, float, float)
    :return: list(float, float, float)
    """

    rotation_matrix1 = np.array(matrix.rotation_matrix_xyz(rotation))
    rotation_matrix2 = np.array(matrix.rotation_matrix_xyz([90, 0, 0]))
    rotation_matrix3 = matrix.rotation_matrix_to_xyz_euler(
        rotation_matrix2.dot(rotation_matrix1).dot(np.linalg.inv(rotation_matrix2)))

    return list(rotation_matrix3)


def convert_scale(scale):
    """
    Converts given scale into a valid rotation to be used with tpDcc
    NOTE: tpDcc uses Y up coordinate axes as the base reference axis
    NOTE: 3ds Max works with Z up axis. We must do the conversion.
    :param scale: tuple(float, float, float)
    :return: tuple(float, float, float)
    """

    return scale[0], scale[2], scale[1]


def convert_dcc_scale(scale):
    """
    Converts given scale into a scale that DCC can manage
    NOTE: tpDcc uses Y up coordinate axes as the base reference axis
    :param scale: list(float, float, float)
    :return: list(float, float, float)
    """

    return scale[0], scale[2], scale[1]


# =================================================================================================================
# DECORATORS
# =================================================================================================================

def undo_decorator():
    """
    Returns undo decorator for current DCC
    """

    return decorators.empty_decorator


def repeat_last_decorator(command_name=None):
    """
    Returns repeat last decorator for current DCC
    """

    return decorators.empty_decorator


def suspend_refresh_decorator():
    """
    Returns decorators that selects again the objects that were selected before executing the decorated function
    """

    return decorators.empty_decorator


def restore_selection_decorator():
    """
    Returns decorators that selects again the objects that were selected before executing the decorated function
    """

    return decorators.empty_decorator
