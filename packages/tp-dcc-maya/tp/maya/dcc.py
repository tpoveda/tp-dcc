#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya DCC implementation
"""

import os
import sys
from collections import OrderedDict

import numpy as np

from Qt.QtWidgets import QApplication, QMainWindow

import maya.cmds
import maya.mel
import maya.utils
import maya.api.OpenMaya

from tp.core import consts, log, dcc
from tp.common.python import helpers, path, folder
from tp.common.math import matrix
from tp.maya.om import mathlib as maya_math
from tp.maya.cmds import helpers, gui, node, name, scene, shape, transform, decorators as maya_decorators
from tp.maya.cmds import attribute, namespace, playblast, constants as maya_constants, joint as joint_utils
from tp.maya.cmds import reference as ref_utils, constraint as constraint_utils, shader as shader_utils
from tp.maya.cmds import filtertypes, animation, sequencer, camera as cam_utils, cluster as cluster_utils
from tp.maya.cmds import space as space_utils, geometry as geo_utils, rivet as rivet_utils, color as maya_color
from tp.maya.cmds import directory, follicle as follicle_utils, curve as curve_utils, ik as ik_utils
from tp.maya.cmds import humanik, deformer as deformer_utils, skin as skin_utils, qtutils as maya_qtutils

logger = log.tpLogger


# =================================================================================================================
# GENERAL
# =================================================================================================================

def get_name():
    """
    Returns the name of the DCC
    :return: str
    """

    return dcc.Dccs.Maya


def get_extensions():
    """
    Returns supported extensions of the DCC
    :return: list(str)
    """

    return ['.ma', '.mb']


def get_version():
    """
    Returns version of the DCC
    :return: int
    """

    return helpers.maya_version()


def get_version_name():
    """
    Returns version of the DCC
    :return: str
    """

    return str(helpers.maya_version())


def is_batch():
    """
    Returns whether DCC is being executed in batch mode or not
    :return: bool
    """

    return maya.cmds.about(batch=True)


def execute_deferred(fn):
    """
    Executes given function in deferred mode
    """

    maya.utils.executeDeferred(fn)


def deferred_function(fn, *args, **kwargs):
    """
    Calls given function with given arguments in a deferred way
    :param fn:
    :param args: list
    :param kwargs: dict
    """

    return maya.cmds.evalDeferred(fn, *args, **kwargs)


def is_component_mode():
    """
    Returns whether current DCC selection mode is component mode or not
    :return: bool
    """

    return maya.cmds.selectMode(query=True, component=True)


def enable_component_selection():
    """
    Enables DCC component selection mode
    """

    return maya.cmds.selectMode(component=True)


def is_plugin_loaded(plugin_name):
    """
    Return whether given plugin is loaded or not
    :param plugin_name: str
    :return: bool
    """

    return helpers.is_plugin_loaded(plugin_name)


def load_plugin(plugin_path, quiet=True):
    """
    Loads given plugin
    :param plugin_path: str
    :param quiet: bool
    """

    return helpers.load_plugin(plugin_path, quiet=quiet)


def unload_plugin(plugin_path):
    """
    Unloads the given plugin
    :param plugin_path: str
    """

    return helpers.unload_plugin(plugin_path)


def list_old_plugins():
    """
    Returns a list of old plugins in the current scene
    :return: list(str)
    """

    return helpers.list_old_plugins()


def remove_old_plugin(plugin_name):
    """
    Removes given old plugin from current scene
    :param plugin_name: str
    """

    return helpers.remove_old_plugin(plugin_name)


def set_workspace(workspace_path):
    """
    Sets current workspace to the given path
    :param workspace_path: str
    """

    return maya.mel.eval('setProject \"' + workspace_path + '\"')
    # return maya.cmds.workspace(workspace_path, openWorkspace=True)


def warning(message):
    """
    Prints a warning message
    :param message: str
    :return:
    """

    maya.cmds.warning(message)


def error(message):
    """
    Prints a error message
    :param message: str
    :return:
    """

    maya.cmds.error(message)


def fit_view(animation=True):
    """
    Fits current viewport to current selection
    :param animation: bool, Animated fit is available
    """

    maya.cmds.viewFit(an=animation)


def refresh_viewport():
    """
    Refresh current DCC viewport
    """

    maya.cmds.refresh(currentView=True)


def refresh_all_viewport():
    """
    Refresh all DCC viewports
    """

    maya.cmds.refresh(currentView=False)


def focus(object_to_focus):
    """
    Focus in given object
    :param object_to_focus: str
    """

    maya.cmds.setFocus(object_to_focus)


def enable_undo():
    """
    Enables undo functionality
    """

    maya.cmds.undoInfo(openChunk=True)


def disable_undo():
    """
    Disables undo functionality
    """

    maya.cmds.undoInfo(closeChunk=True)


# =================================================================================================================
# GUI
# =================================================================================================================


def get_dpi(value=1):
    """
    Returns current DPI used by DCC
    :param value: float
    :return: float
    """

    qt_dpi = QApplication.devicePixelRatio() if maya.cmds.about(batch=True) else QMainWindow().devicePixelRatio()

    return max(qt_dpi * value, get_dpi_scale(value))


def get_dpi_scale(value):
    """
    Returns current DPI scale used by DCC
    :return: float
    """

    maya_scale = 1.0 if not hasattr(
        maya.cmds, "mayaDpiSetting") else maya.cmds.mayaDpiSetting(query=True, realScaleValue=True)

    return maya_scale * value


def get_main_window():
    """
    Returns Qt object that references to the main DCC window
    :return:
    """

    return gui.maya_window()


def get_main_menubar():
    """
    Returns Qt object that references to the main DCC menubar
    :return:
    """

    win = get_main_window()
    menu_bar = win.menuBar()

    return menu_bar


def register_resource_path(resources_path):
    """
    Registers path into given DCC so it can find specific resources (such as icons)

    :param resources_path: str, path we want DCC to register
    """

    if not resources_path or not os.path.isdir(resources_path):
        return

    resources_path = path.clean_path(resources_path)
    resources_paths = [resources_path]
    resources_paths.extend(folder.get_folders(resources_path, recursive=True, full_path=True) or list())

    for resource_path in resources_paths:
        if not os.environ.get('XBMLANGPATH', None):
            os.environ['XBMLANGPATH'] = resource_path
        else:
            paths = os.environ['XBMLANGPATH'].split(os.pathsep)
            if resource_path not in paths and os.path.normpath(resource_path) not in paths:
                os.environ['XBMLANGPATH'] = os.environ['XBMLANGPATH'] + os.pathsep + resource_path


def is_window_floating(window_name):
    """
    Returns whether DCC window is floating
    :param window_name: str
    :return: bool
    """

    return gui.is_window_floating(window_name=window_name)


def focus_ui_panel(panel_name):
    """
    Focus UI panel with given name
    :param panel_name: str
    """

    return maya.cmds.setFocus(panel_name)


def get_dockable_window_class():
    from tp.maya.ui import window
    return window.MayaDockedWindow


def get_dialog_result_yes():
    """
    Returns output when a DCC dialog result is accepted
    :return:
    """

    return maya_constants.DialogResult.Yes


def get_dialog_result_no():
    """
    Returns output when a DCC dialog result is rejected
    :return:
    """

    return maya_constants.DialogResult.No


def get_dialog_result_cancel():
    """
    Returns output when a DCC dialog result is cancelled
    :return:
    """

    return maya_constants.DialogResult.Cancel


def get_dialog_result_close():
    """
    Returns output when a DCC dialog result is close
    :return:
    """

    return maya_constants.DialogResult.Close


def show_message_in_viewport(msg, **kwargs):
    """
    Shows a message in DCC viewport
    :param msg: str, Message to show
    :param kwargs: dict, extra arguments
    """

    color = kwargs.get('color', '')
    pos = kwargs.get('pos', 'topCenter')

    if color != '':
        msg = "<span style=\"color:{0};\">{1}</span>".format(color, msg)

    maya.cmds.inViewMessage(amg=msg, pos=pos, fade=True, fst=1000, dk=True)


def add_shelf_menu_item(parent, label, command='', icon=''):
    """
    Adds a new menu item
    :param parent:
    :param label:
    :param command:
    :param icon:
    :return:
    """

    return maya.cmds.menuItem(parent=parent, labelong=label, command=command, image=icon or '')


def add_shelf_sub_menu_item(parent, label, icon=''):
    """
    Adds a new sub menu item
    :param parent:
    :param label:
    :param icon:
    :return:
    """

    return maya.cmds.menuItem(parent=parent, labelong=label, icon=icon or '', subMenu=True)


def add_shelf_separator(shelf_name):
    """
    Adds a new separator to the given shelf
    :param shelf_name: str
    """

    return maya.cmds.separator(
        parent=shelf_name, manage=True, visible=True, horizontalong=False,
        style='shelf', enableBackground=False, preventOverride=False)


def shelf_exists(shelf_name):
    """
    Returns whether given shelf already exists or not
    :param shelf_name: str
    :return: bool
    """

    return gui.shelf_exists(shelf_name=shelf_name)


def create_shelf(shelf_name, shelf_labelong=None):
    """
    Creates a new shelf with the given name
    :param shelf_name: str
    :param shelf_label: str
    """

    return gui.create_shelf(name=shelf_name)


def delete_shelf(shelf_name):
    """
    Deletes shelf with given name
    :param shelf_name: str
    """

    return gui.delete_shelf(shelf_name=shelf_name)


def confirm_dialog(title, message, button=None, cancel_button=None, default_button=None, dismiss_string=None):
    """
    Shows DCC confirm dialog
    :param title:
    :param message:
    :param button:
    :param cancel_button:
    :param default_button:
    :param dismiss_string:
    :return:
    """

    if button and cancel_button and dismiss_string and default_button:
        return maya.cmds.confirmDialog(
            title=title, message=message, button=button, cancelButton=cancel_button,
            defaultButton=default_button, dismissString=dismiss_string)

    if button:
        return maya.cmds.confirmDialog(title=title, message=message)
    else:
        return maya.cmds.confirmDialog(title=title, message=message, button=button)


def select_file_dialog(title, start_directory=None, pattern=None):
    """
    Shows select file dialog
    :param title: str
    :param start_directory: str
    :param pattern: str
    :return: str
    """

    if not pattern:
        pattern = 'All Files (*.*)'

    res = maya.cmds.fileDialog2(fm=1, dir=start_directory, cap=title, ff=pattern)
    if res:
        res = res[0]

    return res


def select_folder_dialog(title, start_directory=None):
    """
    Shows select folder dialog
    :param title: str
    :param start_directory: str
    :return: str
    """

    return directory.select_folder_dialog(title=title, start_directory=start_directory)


def save_file_dialog(title, start_directory=None, pattern=None):
    """
    Shows save file dialog
    :param title: str
    :param start_directory: str
    :param pattern: str
    :return: str
    """

    return directory.save_file_dialog(title=title, start_directory=start_directory, pattern=pattern)


def get_current_model_panel():
    """
    Returns the current model panel name
    :return: str | None
    """

    current_panel = maya.cmds.getPanel(withFocus=True)
    current_panel_type = maya.cmds.getPanel(typeOf=current_panel)

    if current_panel_type not in ['modelPanel']:
        return None

    return current_panel


def dock_widget(widget, *args, **kwargs):
    """
    Docks given widget into current DCC UI
    :param widget: QWidget
    :param args:
    :param kwargs:
    :return:
    """

    return maya_qtutils.dock_widget(widget, *args, **kwargs)


def get_all_fonts():
    """
    Returns all fonts available in DCC
    :return: list(str)
    """

    return maya.cmds.fontDialog(FontList=True) or list()


# =================================================================================================================
# OBJECTS / NODES
# =================================================================================================================

def node_types():
    """
    Returns dictionary that provides a mapping between tpDcc object types and  DCC specific node types
    Can be the situation where a tpDcc object maps to more than one MFn object
    None values are ignored. This is because either do not exist or there is not an equivalent type in Maya
    :return: dict
    """

    return OrderedDict([
        (consts.ObjectTypes.Geometry, [maya.api.OpenMaya.MFn.kMesh, 'mesh']),
        (consts.ObjectTypes.Light, [maya.api.OpenMaya.MFn.kLight, 'light']),
        (consts.ObjectTypes.Camera, [maya.api.OpenMaya.MFn.kCamera, 'camera']),
        (consts.ObjectTypes.Model, [maya.api.OpenMaya.MFn.kTransform, 'transform']),
        (consts.ObjectTypes.Group, [maya.api.OpenMaya.MFn.kTransform, 'transform']),
        (consts.ObjectTypes.Bone, [maya.api.OpenMaya.MFn.kJoint, 'joint']),
        (consts.ObjectTypes.Particle, [
            (maya.api.OpenMaya.MFn.kParticle, maya.api.OpenMaya.MFn.kNParticle), ('particle', 'particle')]),
        (consts.ObjectTypes.Curve, [maya.api.OpenMaya.MFn.kCurve, 'curve']),
        (consts.ObjectTypes.PolyMesh, [maya.api.OpenMaya.MFn.kPolyMesh, 'polyMesh']),
        (consts.ObjectTypes.NurbsSurface, [maya.api.OpenMaya.MFn.kNurbsSurface, 'nurbsSurface']),
        (consts.ObjectTypes.Network, [maya.api.OpenMaya.MFn.kAffect, 'network']),
        (consts.ObjectTypes.Null, [maya.api.OpenMaya.MFn.kLocator, 'locator']),
    ])


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


def dcc_to_tpdcc_str_types():
    """
    Returns a dictionary that provides a mapping between Dcc string object types and tpDcc object types
    :return:
    """

    dcc_to_abstract_str_types = OrderedDict()
    for abstract_type, dcc_type in node_types().items():
        if isinstance(dcc_type[1], (tuple, list)):
            for item in dcc_type[1]:
                dcc_to_abstract_str_types[item] = abstract_type
        else:
            dcc_to_abstract_str_types[dcc_type[1]] = abstract_type


def node_tpdcc_type(node_name, as_string=False):
    """
    Returns the DCC object type as a string given a specific tpDcc object type
    :param node_name: str
    :param as_string: bool
    :return: str
    """

    if as_string:
        node_type = maya.cmds.objectType(node_name)
        if node_type == 'transform':
            return 'transform'

        if node_type in self.DCC_TO_ABSTRACT_STR_TYPES:
            maya_type = self.DCC_TO_ABSTRACT_STR_TYPES[node_type]
            return node_types()[maya_type][1]
    else:
        maya_node = node.get_mobject(node_name)
        maya_api_type = maya_node.apiType()

        # TODO: We are hardcoding node type returns. Maybe we should return a generic transform and let user
        # TODO: to handle shape types by itself.
        if maya_api_type == maya.api.OpenMaya.MFn.kTransform:
            node_shape = node.shape(node_name)
            if node_shape == maya_node:
                return consts.ObjectTypes.Generic
            else:
                if node_shape.hasFn(maya.api.OpenMaya.MFn.kLocator):
                    return consts.ObjectTypes.Null
                else:
                    return consts.ObjectTypes.Geometry

        if maya_api_type in self.DCC_TO_ABSTRACT_TYPES.keys():
            return self.DCC_TO_ABSTRACT_TYPES[maya_api_type]


def root_node():
    """
    Returns DCC scene root node
    :return: str
    """

    return scene.get_root_node()


def node_exists(node_name):
    """
    Returns whether given object exists or not
    :param node_name: str
    :return: bool
    """

    return node.check_node(node_name)


def object_type(node_name):
    """
    Returns type of given object
    :param node_name: str
    :return: str
    """

    return maya.cmds.objectType(node_name)


def node_type(node_name):
    """
    Returns node type of given object
    :param node_name: str
    :return: str
    """

    return maya.cmds.nodeType(node_name)


def check_object_type(node, node_type, check_sub_types=False):
    """
    Returns whether give node is of the given type or not
    :param node: str
    :param node_type: str
    :param check_sub_types: bool
    :return: bool
    """

    is_type = maya.cmds.objectType(node, isType=node_type)
    if not is_type and check_sub_types:
        is_type = maya.cmds.objectType(node, isAType=node_type)

    return is_type


def node_handle(node_name):
    """
    Returns unique identifier of the given node
    :param node_name: str
    :return: str
    """

    node_uuid = maya.cmds.ls(node_name, uuid=True)
    return None if not node_uuid else node_uuid[0]


def node_is_empty(node_name, *args, **kwargs):
    """
    Returns whether given node is an empty one.
    In Maya, an emtpy node is the one that is not referenced, has no child transforms, has no custom attributes
    and has no connections
    :param node_name: str
    :return: bool
    """

    no_user_attributes = kwargs.pop('no_user_attributes', True)
    no_connections = kwargs.pop('no_connections', True)
    return node.is_empty(node_name=node_name, no_user_attributes=no_user_attributes, no_connections=no_connections)


def node_is_root(node_name):
    """
    Returns whether given node is a DCC scene root node
    :param node_name: str
    :return: bool
    """

    if helpers.is_string(node_name):
        node_name = node.get_mobject(node_name)

    return node_name.apiType() == maya.api.OpenMaya.MFn.kWorld


def node_is_selected(node_name):
    """
    Returns whether given node is currently selected
    :param node_name: str
    :return: bool
    """

    current_selection = maya.cmds.ls(sl=True, long=True)
    for obj in current_selection:
        if maya.api.OpenMaya.MFnDependencyNode(obj).name() == maya.api.OpenMaya.MFnDependencyNode(node_name).name():
            return True

    return False


def node_is_transform(node_name):
    """
    Returns whether given node is a transform node
    :param node_name: str
    :return: bool
    """

    return maya.cmds.nodeType(node_name) == 'transform'


def node_is_joint(node_name):
    """
    Returns whether given node is a joint node
    :param node_name: str
    :return: bool
    """

    return maya.cmds.nodeType(node_name) == 'joint'


def node_is_locator(node_name):
    """
    Returns whether given node is a locator node
    :param node_name: str
    :return: bool
    """

    return maya.cmds.nodeType(node_name) == 'locator' or shape.get_shape_node_type(node) == 'locator'


def node_is_hidden(node_name):
    """
    Returns whether given node is hidden
    :param node_name: str
    :return: bool
    """

    if helpers.is_string(node_name):
        return not maya.cmds.getAttr('{}.visibility'.format(node_name))

    return not maya.cmds.getAttr('{}.visibility'.format(node.get_name(node_name)))


def find_node_by_name(node_name):
    """
    Returns node by its given node.
    This function makes sure that the returned node is an existing node
    :param node_name: str
    :return: str
    """

    if not node.check_node(node_name):
        return None

    return node.get_mobject(node_name)


def find_node_by_id(unique_id, full_path=True):
    """
    Returns node by its given id.
    This function makes sure that the returned node is an existing node
    :param unique_id: str
    :param full_path: bool
    :return: str
    """

    node_found = node.get_node_by_id(unique_id, full_path=full_path)
    if not node_found:
        return None

    return node_found
    # return node.get_mobject(node_found)


def rename_node(node, new_name, **kwargs):
    """
    Renames given node with new given name
    :param node: str
    :param new_name: str
    :return: str
    """

    uuid = kwargs.get('uuid', None)
    rename_shape = kwargs.get('rename_shape', True)
    return_long_name = kwargs.get('return_long_name', False)

    return name.rename(node, new_name, uuid=uuid, rename_shape=rename_shape, return_long_name=return_long_name)


def duplicate_node(node_name, new_node_name='', only_parent=False, return_roots_only=False, rename_children=False):
    """
    Duplicates given object in current scene
    :param node_name: str
    :param new_node_name: str
    :param only_parent: bool, If True, only given node will be duplicated (ignoring its children)
    :param return_roots_only: bool, If True, only the root nodes of the new hierarchy will be returned
    :param rename_children: bool, whether children nodes are renamed
    :return: list(str)
    """

    return maya.cmds.duplicate(
        node_name, name=new_node_name, parentOnly=only_parent, returnRootsOnly=return_roots_only)[0]


def delete_node(node_name):
    """
    Removes given node from current scene
    :param node_name: str
    """

    nodes = helpers.force_list(node_name)

    objects_to_delete = list()
    for node_found in nodes:
        if not helpers.is_string(node_found):
            node_found = node.get_name(node_found, fullname=True)
        objects_to_delete.append(node_found)

    return maya.cmds.delete(objects_to_delete)


def create_node(node_type, node_name=None):
    """
    Creates a new node of the given type and with the given name
    :param node_type: str
    :param node_name: str
    :return: str
    """

    return maya.cmds.createNode(node_type, name=node_name)


def set_node_normal_display(node, flag):
    """
    Sets whether given node is displayed in normal mode
    :param node: str
    :param flag: bool
    """

    if flag:
        maya.cmds.setAttr('{}.overrideEnabled'.format(node), True)
    maya.cmds.setAttr('{}.overrideDisplayType'.format(node), 0)


def set_node_template_display(node, flag):
    """
    Sets whether given node is displayed in template mode
    :param node: str
    :param flag: bool
    """

    if flag:
        maya.cmds.setAttr('{}.overrideEnabled'.format(node), True)
    maya.cmds.setAttr('{}.overrideDisplayType'.format(node), 1)


def set_node_reference_display(node, flag):
    """
    Sets whether given node is displayed in reference mode
    :param node: str
    :param flag: bool
    """

    if flag:
        maya.cmds.setAttr('{}.overrideEnabled'.format(node), True)
    maya.cmds.setAttr('{}.overrideDisplayType'.format(node), 2)


def set_node_renderable(node, flag):
    """
    Sets the given node not be renderable or not
    :param node: str
    :param flag: bool
    """

    nodes = helpers.force_list(node)
    shapes_list = list()
    for node_name in nodes:
        shapes_list.extend(shape.get_shapes(node_name) or list())
    for node_shape in shapes_list:
        maya.cmds.setAttr('{}.castsShadows'.format(node_shape), flag)
        maya.cmds.setAttr('{}.receiveShadows'.format(node_shape), flag)
        maya.cmds.setAttr('{}.holdOut'.format(node_shape), flag)
        maya.cmds.setAttr('{}.motionBlur'.format(node_shape), flag)
        maya.cmds.setAttr('{}.primaryVisibility'.format(node_shape), flag)
        maya.cmds.setAttr('{}.smoothShading'.format(node_shape), flag)
        maya.cmds.setAttr('{}.visibleInReflections'.format(node_shape), flag)
        maya.cmds.setAttr('{}.visibleInRefractions'.format(node_shape), flag)
        maya.cmds.setAttr('{}.doubleSided'.format(node_shape), flag)


def set_node_cast_shadows(node, flag):
    """
    Sets whether given node can cast shadows
    :param node: str
    :param flag: bool
    """

    nodes = helpers.force_list(node)
    shapes_list = list()
    for node_name in nodes:
        shapes_list.extend(shape.get_shapes(node_name) or list())
    for node_shape in shapes_list:
        maya.cmds.setAttr('{}.castsShadows'.format(node_shape, flag))


def set_node_receive_shadows(node, flag):
    """
    Sets whether given node can receive shadows
    :param node: str
    :param flag: bool
    """

    nodes = helpers.force_list(node)
    shapes_list = list()
    for node_name in nodes:
        shapes_list.extend(shape.get_shapes(node_name) or list())
    for node_shape in shapes_list:
        maya.cmds.setAttr('{}.receiveShadows'.format(node_shape), flag)


def set_node_light_interaction(node, flag):
    """
    Sets whether given node can interact with lights
    :param node: str
    :param flag: bool
    """

    nodes = helpers.force_list(node)
    shapes_list = list()
    for node_name in nodes:
        shapes_list.extend(shape.get_shapes(node_name) or list())
    for node_shape in shapes_list:
        maya.cmds.setAttr('{}.holdOut'.format(node_shape), flag)


def set_node_has_motion_blur(node, flag):
    """
    Sets whether given node can have motion blur
    :param node: str
    :param flag: bool
    """

    nodes = helpers.force_list(node)
    shapes_list = list()
    for node_name in nodes:
        shapes_list.extend(shape.get_shapes(node_name) or list())
    for node_shape in shapes_list:
        maya.cmds.setAttr('{}.motionBlur'.format(node_shape), flag)


def set_node_is_visible_to_cameras(node, flag):
    """
    Sets whether given node is visible by cameras
    :param node: str
    :param flag: bool
    """

    nodes = helpers.force_list(node)
    shapes_list = list()
    for node_name in nodes:
        shapes_list.extend(shape.get_shapes(node_name) or list())
    for node_shape in shapes_list:
        maya.cmds.setAttr('{}.primaryVisibility'.format(node_shape), flag)


def set_node_smooth_shading(node, flag):
    """
    Sets whether given node has smooth shading
    :param node: str
    :param flag: bool
    """

    nodes = helpers.force_list(node)
    shapes_list = list()
    for node_name in nodes:
        shapes_list.extend(shape.get_shapes(node_name) or list())
    for node_shape in shapes_list:
        maya.cmds.setAttr('{}.smoothShading'.format(node_shape), flag)


def set_node_is_visible_in_reflections(node, flag):
    """
    Sets whether given node is visible in reflections
    :param node: str
    :param flag: bool
    """

    nodes = helpers.force_list(node)
    shapes_list = list()
    for node_name in nodes:
        shapes_list.extend(shape.get_shapes(node_name) or list())
    for node_shape in shapes_list:
        maya.cmds.setAttr('{}.visibleInReflections'.format(node_shape), flag)


def set_node_is_visible_in_refractions(node, flag):
    """
    Sets whether given node is visible in refractions
    :param node: str
    :param flag: bool
    """

    nodes = helpers.force_list(node)
    shapes_list = list()
    for node_name in nodes:
        shapes_list.extend(shape.get_shapes(node_name) or list())
    for node_shape in shapes_list:
        maya.cmds.setAttr('{}.visibleInRefractions'.format(node_shape), flag)


def set_node_double_sided(node, flag):
    """
    Sets whether given node polygons can be renderer in both back and front directions
    :param node: str
    :param flag: bool
    """

    nodes = helpers.force_list(node)
    shapes_list = list()
    for node_name in nodes:
        shapes_list.extend(shape.get_shapes(node_name) or list())
    for node_shape in shapes_list:
        maya.cmds.setAttr('{}.doubleSided'.format(node_shape), flag)


def show_node(node):
    """
    Shows given object
    :param node: str
    """

    return maya.cmds.showHidden(node)


def hide_node(node):
    """
    Hides given node
    :param node: str
    """

    return maya.cmds.hide(node)


def clean_construction_history(node):
    """
    Removes the construction history of the given node
    :param node: str
    """

    return maya.cmds.delete(node, constructionHistory=True)


def node_attribute_name(node_and_attr):
    """
    Returns the attribute part of a given node name
    :param node_and_attr: str
    :return: str
    """

    return attribute.attribute_name(node_and_attr)


def node_object_color(node):
    """
    Returns the color of the given node
    :param node: str
    :return: list(int, int, int, int)
    """

    return maya.cmds.getAttr('{}.objectColor'.format(node))


def node_override_enabled(node):
    """
    Returns whether the given node has its display override attribute enabled or not
    :param node: str
    :return: bool
    """

    return maya.cmds.getAttr('{}.overrideEnabled'.format(node))


def node_is_visible(node_name):
    """
    Returns whether given node is visible or not
    :param node: str
    :return: bool
    """

    return node.is_visible(node=node_name)


def node_color(node_name):
    """
    Returns color of the given node
    :param node_name: str
    :return:
    """

    return attribute.color(node_name)


def node_rgb_color(node_name, linear=True):
    """
    Returns color of the given node
    :param node_name: str
    :param linear: bool, Whether or not the RGB should be in linear space (matches viewport color)
    :return:
    """

    return node.get_rgb_color(node_name, linear=linear)


def set_node_color(node_name, color):
    """
    Sets the color of the given node
    :param node: str
    :param color:
    """

    return attribute.set_color(node_name, color)


def node_components(node_name):
    """
    Returns all components of the given node
    :param node_name: str
    :return: list(str)
    """

    return shape.get_components_from_shapes(node_name)


def node_is_referenced(node):
    """
    Returns whether given node is referenced or not
    :param node: str
    :return: bool
    """

    if not maya.cmds.objExists(node):
        return False

    try:
        return maya.cmds.referenceQuery(node, isNodeReferenced=True)
    except Exception as exc:
        return False


def node_reference_path(node, without_copy_number=False):
    """
    Returns reference path of the referenced node
    :param node: str
    :param without_copy_number: bool
    :return: str
    """

    if not maya.cmds.objExists(node):
        return None

    return maya.cmds.referenceQuery(node, filename=True, wcn=without_copy_number)


def node_unreference(node):
    """
    Unreferences given node
    :param node: str
    """

    ref_node = None
    if ref_utils.is_referenced(node):
        ref_node = ref_utils.reference_node(node)
    elif ref_utils.is_reference(node):
        ref_node = node

    if ref_node:
        return ref_utils.remove_reference(ref_node)


def node_nodes(node):
    """
    Returns referenced nodes of the given node
    :param node: str
    :return: list<str>
    """

    return maya.cmds.referenceQuery(node, nodes=True)


def node_filename(node, no_copy_number=True):
    """
    Returns file name of the given node
    :param node: str
    :param no_copy_number: bool
    :return: str
    """

    return maya.cmds.referenceQuery(node, filename=True, withoutCopyNumber=no_copy_number)


def change_filename(node, new_filename):
    """
    Changes filename of a given reference node
    :param node: str
    :param new_filename: str
    """

    return maya.cmds.file(new_filename, loadReference=node)


def import_reference(filename):
    """
    Imports object from reference node filename
    :param filename: str
    """

    return maya.cmds.file(filename, importReference=True)


def node_is_loaded(node):
    """
    Returns whether given node is loaded or not
    :param node: str
    :return: bool
    """

    return maya.cmds.referenceQuery(node, isLoaded=True)


def node_is_locked(node):
    """
    Returns whether given node is locked or not
    :param node: str
    :return: bool
    """

    return maya.cmds.lockNode(node, q=True, long=True)


def node_children(node, all_hierarchy=True, full_path=True):
    """
    Returns a list of children of the given node
    :param node: str
    :param all_hierarchy: bool
    :param full_path: bool
    :return: list<str>
    """

    return maya.cmds.listRelatives(
        node, children=True, allDescendents=all_hierarchy, shapes=False, fullPath=full_path)


def node_parent(node, full_path=True):
    """
    Returns parent node of the given node
    :param node: str
    :param full_path: bool
    :return: str
    """

    node_parent = maya.cmds.listRelatives(node, parent=True, fullPath=full_path)
    if node_parent:
        node_parent = node_parent[0]

    return node_parent


def node_root(node, full_path=True):
    """
    Returns hierarchy root node of the given node
    :param node: str
    :param full_path: bool
    :return: str
    """

    if not node:
        return None

    return scene.get_node_transform_root(node, full_path=full_path)


def set_parent(node, parent):
    """
    Sets the node parent to the given parent
    :param node: str
    :param parent: str
    """

    return maya.cmds.parent(node, parent)[0]


def set_parent_to_world(node):
    """
    Parent given node to the root world node
    :param node: str
    """

    return maya.cmds.parent(node, world=True)[0]


def delete_history(node):
    """
    Removes the history of the given node
    """

    return transform.delete_history(transform=node)


def list_node_types(type_string):
    """
    List all dependency node types satisfying given classification string
    :param type_string: str
    :return:
    """

    return maya.cmds.listNodeTypes(type_string)


def list_nodes(node_name=None, node_type=None, full_path=True):
    """
    Returns list of nodes with given types. If no type, all scene nodes will be listed
    :param node_name:
    :param node_type:
    :param full_path:
    :return:  list(str)
    """

    if not node_name and not node_type:
        return maya.cmds.ls(long=full_path)

    if node_name and node_type:
        return maya.cmds.ls(node_name, type=node_type, long=full_path)
    elif node_name and not node_type:
        return maya.cmds.ls(node_name, long=full_path)
    elif not node_name and node_type:
        return maya.cmds.ls(type=node_type, long=full_path)


def list_children(node, all_hierarchy=True, full_path=True, children_type=None):
    """
    Returns a list of chlidren nodes of the given node
    :param node:
    :param all_hierarchy:
    :param full_path:
    :param children_type:
    :return:
    """

    if children_type:
        children = maya.cmds.listRelatives(
            node, children=True, allDescendents=all_hierarchy, fullPath=full_path, type=children_type)
    else:
        children = maya.cmds.listRelatives(node, children=True, allDescendents=all_hierarchy, fullPath=full_path)
    if not children:
        return list()

    children.reverse()

    return children


def list_relatives(
        node, all_hierarchy=False, full_path=True, relative_type=None, shapes=False, intermediate_shapes=False):
    """
    Returns a list of relative nodes of the given node
    :param node:
    :param all_hierarchy:
    :param full_path:
    :param relative_type:
    :param shapes:
    :param intermediate_shapes:
    :return:
    """

    if relative_type:
        return maya.cmds.listRelatives(
            node, allDescendents=all_hierarchy, fullPath=full_path, type=relative_type,
            shapes=shapes, noIntermediate=not intermediate_shapes) or list()
    else:
        return maya.cmds.listRelatives(
            node, allDescendents=all_hierarchy, fullPath=full_path, shapes=shapes,
            noIntermediate=not intermediate_shapes) or list()


def list_transforms(full_path=True):
    """
    List all transforms in current scene
    :param full_path:
    :return: list(str)
    """

    return maya.cmds.ls(tr=True, long=full_path)


def node_inherits_transform(node):
    """
    Returns whether given node inherits its parent transforms
    :param node: str
    :return: bool
    """

    return maya.cmds.getAttr('{}.inheritsTransform'.format(node))


def set_node_inherits_transform(node, flag):
    """
    Sets whether given node inherits parent transforms or not
    :param node: str
    :param flag: bool
    """

    return maya.cmds.setAttr('{}.inheritsTransform'.format(node), flag)


def enable_overrides(node):
    """
    Enables overrides in the given node
    :param node: str
    """

    return maya.cmds.setAttr('{}.overrideEnabled'.format(node), True)


def disable_overrides(node):
    """
    Disables in the given node
    :param node: str
    """

    return maya.cmds.setAttr('{}.overrideEnabled'.format(node), False)


def disable_transforms_inheritance(node, lock=False):
    """
    Disables transforms inheritance from given node
    :param node: str
    :param lock: bool
    """

    maya.cmds.setAttr('{}.inheritsTransform'.format(node), False)
    if lock:
        attribute.lock_attributes(node, ['inheritsTransform'], hide=False)


def list_node_parents(node):
    """
    Returns all parent nodes of the given Maya node
    :param node: str
    :return: list(str)
    """

    return scene.get_all_parent_nodes(node)


def create_locator(name='loc'):
    """
    Creates a new locator
    :param name: str
    :return: str
    """

    return maya.cmds.spaceLocator(name=name)[0]


def create_decompose_matrix_node(node_name):
    """
    Creates a new decompose matrix node
    :param node_name: str
    :return: str
    """

    return maya.cmds.createNode('decomposeMatrix', name=node_name)


def node_transforms(node):
    """
    Returns all transforms nodes of a given node
    :param node: str
    :return: list(str)
    """

    return maya.cmds.listRelatives(node, type='transform')


def node_joints(node):
    """
    Returns all oints nodes of a give node
    :param node: str
    :return: list(str)
    """

    return maya.cmds.listRelatives(node, type='joint')


def node_shape_type(node):
    """
    Returns the type of the given shape node
    :param node: str
    :return: str
    """

    return shape.get_shape_node_type(node)


def distance_between_nodes(source_node=None, target_node=None):
    """
    Returns the distance between 2 given nodes
    :param str source_node: first node to start measuring distance from.
        If not given, first selected node will be used.
    :param str target_node: second node to end measuring distance to.
        If not given, second selected node will be used.
    :return: distance between 2 nodes.
    :rtype: float
    """

    return maya_math.distance_between_nodes(source_node, target_node)


# =================================================================================================================
# SHAPES
# =================================================================================================================

def all_shapes_nodes(full_path=True):
    """
    Returns all shapes nodes in current scene
    :param full_path: bool
    :return: list<str>
    """

    return maya.cmds.ls(shapes=True, long=full_path)


def set_shape_parent(shape, transform_node):
    """
    Sets given shape parent
    :param shape: str
    :param transform_node: str
    """

    return maya.cmds.parent(shape, transform_node, r=True, shape=True)


def add_node_to_parent(node, parent_node):
    """
    Add given object under the given parent preserving its local transformations
    :param node: str
    :param parent_node: str
    """

    return maya.cmds.parent(node, parent_node, add=True, s=True)


def node_is_a_shape(node):
    """
    Returns whether given node is a shape one
    :param node: str
    :return: bool
    """

    return shape.is_a_shape(node)


def list_shapes(node, full_path=True, intermediate_shapes=False):
    """
    Returns a list of shapes of the given node
    :param node: str
    :param full_path: bool
    :param intermediate_shapes: bool
    :return: list<str>
    """

    return maya.cmds.listRelatives(
        node, shapes=True, fullPath=full_path, children=True, noIntermediate=not intermediate_shapes)


def list_shapes_of_type(node, shape_type=None, full_path=True, intermediate_shapes=False):
    """
    Returns a list of shapes of the given node
    :param node: str
    :param shape_type: str
    :param full_path: bool
    :param intermediate_shapes: bool
    :return: list<str>
    """

    return shape.get_shapes_of_type(
        node_name=node, shape_type=shape_type, full_path=full_path, no_intermediate=not intermediate_shapes)


def node_has_shape_of_type(node, shape_type):
    """
    Returns whether given node has a shape of the given type attached to it
    :param node: str
    :param shape_type: str
    :return: bool
    """

    return shape.has_shape_of_type(node, shape_type=shape_type)


def list_children_shapes(node, all_hierarchy=True, full_path=True, intermediate_shapes=False):
    """
    Returns a list of children shapes of the given node
    :param node:
    :param all_hierarchy:
    :param full_path:
    :param intermediate_shapes:
    :return:
    """

    if all_hierarchy:
        return shape.get_shapes_in_hierarchy(
            transform_node=node, full_path=full_path, intermediate_shapes=intermediate_shapes)
    else:
        return maya.cmds.listRelatives(
            node, shapes=True, fullPath=full_path, noIntermediate=not intermediate_shapes, allDescendents=False)

    # return maya.cmds.listRelatives(node, shapes=True, fullPath=full_path, children=True,
    # allDescendents=all_hierarchy, noIntermediate=not intermediate_shapes)


def shape_transform(shape_node, full_path=True):
    """
    Returns the transform parent of the given shape node
    :param shape_node: str
    :param full_path: bool
    :return: str
    """

    return maya.cmds.listRelatives(shape_node, parent=True, fullPath=full_path)


def parent_shapes_to_transforms(shapes_list, transforms_list):
    """
    Parents given shapes into given transforms
    :param shapes_list: list(str)
    :param transforms_list: list(str)
    :return: list(str)
    """

    replaced_shapes = list()

    shapes = helpers.force_list(shapes_list)
    transforms = helpers.force_list(transforms_list)
    if len(shapes) != len(transforms):
        return False

    for shape, transform in zip(shapes, transforms):
        shape_xform = node_parent(shape)
        child_shapes = maya.cmds.listRelatives(shape, children=True, shapes=True, ni=True, fullPath=True) or list()
        all_shapes = [shape] + child_shapes
        combined_shape = maya.cmds.parent(all_shapes, transform, shape=True, add=True)[0]
        combined_transform = maya.cmds.listRelatives(combined_shape, parent=True)[0]
        if len(all_shapes) == 1:
            maya.cmds.rename(all_shapes, '{}Shape'.format(node_short_name(shape)))
        else:
            for i, shp in enumerate(all_shapes):
                maya.cmds.rename(shp, '%sShape%02d' % (transform, i))
        # delete old transform
        maya.cmds.delete(shape_xform)
        replaced_shapes.append(combined_transform)

    return replaced_shapes


def rename_shapes(node):
    """node_name_without_namespace
    Rename all shapes of the given node with a standard DCC shape name
    :param node: str
    """

    return shape.rename_shapes(node)


def combine_shapes(target_node, nodes_to_combine_shapes_of, delete_after_combine=True):
    """
    Combines all shapes of the given node
    :param target_node: str
    :param nodes_to_combine_shapes_of: str
    :param delete_after_combine: bool, Whether or not combined shapes should be deleted after
    :return: str, combined shape
    """

    nodes_to_combine_shapes_of = helpers.force_list(nodes_to_combine_shapes_of)
    for obj in nodes_to_combine_shapes_of:
        if shape.is_shape(obj):
            shapes = obj
        else:
            shapes = maya.cmds.listRelatives(obj, s=True, ni=True, f=True)
        maya.cmds.parent(shapes, target_node, s=True, add=True)
        # maya.cmds.delete(obj)
    if delete_after_combine:
        maya.cmds.delete(nodes_to_combine_shapes_of)


def scale_shapes(target_node, scale_value, relative=False):
    """
    Scales given shapes
    :param target_node: str
    :param scale_value: float
    :return: relative, bool
    """

    return shape.scale_shapes(target_node, scale_value, relative=relative)


def shapes_bounding_box_pivot(shapes):
    """
    Returns the bounding box pivot center point of the given meshes
    :param shapes: list(str)
    :return: list(float, float, float)
    """

    components = shape.get_components_from_shapes(shapes)
    bounding = transform.BoundingBox(components)
    pivot = bounding.get_center()

    return pivot


# =================================================================================================================
# FILTERING
# =================================================================================================================

def filter_nodes_by_selected_components(filter_type, nodes=None, full_path=False, **kwargs):
    """
    Function that filter nodes taking into account specific component filters
    Maya Components Filter Type Values
    Handle:                     0
    Nurbs Curves:               9
    Nurbs Surfaces:             10
    Nurbs Curves On Surface:    11
    Polygon:                    12
    Locator XYZ:                22
    Orientation Locator:        23
    Locator UV:                 24
    Control Vertices (CVs):     28
    Edit Points:                30
    Polygon Vertices:           31
    Polygon Edges:              32
    Polygon Face:               34
    Polygon UVs:                35
    Subdivision Mesh Points:    36
    Subdivision Mesh Edges:     37
    Subdivision Mesh Faces:     38
    Curve Parameter Points:     39
    Curve Knot:                 40
    Surface Parameter Points:   41
    Surface Knot:               42
    Surface Range:              43
    Trim Surface Edge:          44
    Surface Isoparms:           45
    Lattice Points:             46
    Particles:                  47
    Scale Pivots:               49
    Rotate Pivots:              50
    Select Handles:             51
    Subdivision Surface:        68
    Polygon Vertex Face:        70
    NURBS Surface Face:         72
    Subdivision Mesh UVs:       73
    :param filter_type: int
    :param nodes: list(str)
    :param full_path: bool
    :param kwargs:
    :return: list(str)
    """

    nodes = nodes or selected_nodes()

    return maya.cmds.filterExpand(nodes, selectionMask=filter_type, fullPath=full_path)


def filter_nodes_by_type(filter_type, search_hierarchy=False, selection_only=True, **kwargs):
    """
    Returns list of nodes in current scene filtered by given filter
    :param filter_type: str, filter used to filter nodes to edit index of
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search all scene objects or only selected ones
    :param kwargs:
    :return: list(str), list of filtered nodes
    """

    dag = kwargs.get('dag', False)
    remove_maya_defaults = kwargs.get('remove_maya_defaults', True)
    transforms_only = kwargs.get('transforms_only', True)

    return filtertypes.filter_by_type(
        filter_type=filter_type, search_hierarchy=search_hierarchy, selection_only=selection_only, dag=dag,
        remove_maya_defaults=remove_maya_defaults, transforms_only=transforms_only) or list()


# =================================================================================================================
# NAMING
# =================================================================================================================

def get_allowed_characters():
    """
    Returns regular expression of allowed characters in current DCC
    :return: str
    """

    return 'A-Za-z0-9_. /+*<>=|-'


def node_name(node):
    """
    Returns the name of the given node
    :param node: str
    :return: str
    """

    return node


def node_short_name(node, **kwargs):
    """
    Returns short name of the given node
    :param node: str
    :return: str
    """

    remove_attribute = kwargs.get('remove_attribute', False)
    remove_namespace = kwargs.get('remove_namespace', False)

    return name.get_basename(node, remove_namespace=remove_namespace, remove_attribute=remove_attribute)


def node_long_name(node):
    """
    Returns long name of the given node
    :param node: str
    :return: str
    """

    return name.get_long_name(node)


def get_mirror_name(name, center_patterns=None, left_patterns=None, right_patterns=None):
    """
    Returns mirrored name of the given name
    :param name: str
    :return: str
    """

    if name_is_center(name, patterns=center_patterns):
        return name

    if name_is_left(name, patterns=left_patterns):
        from_side = consts.SIDE_PATTERNS['left']
        to_side = consts.SIDE_PATTERNS['right']
    elif name_is_left(name, patterns=right_patterns):
        from_side = consts.SIDE_PATTERNS['right']
        to_side = consts.SIDE_PATTERNS['left']
    else:
        return name

    mirror_name = name
    for i, side in enumerate(from_side):
        if name.startswith('{}_'.format(side)):
            mirror_name = '{}_'.format(to_side[i]) + mirror_name[2:]
            break
        elif name.endswith('_{}'.format(side)):
            mirror_name = mirror_name[:-2] + '_{}'.format(to_side[i])
            break
        elif '_{}_'.format(side) in name:
            mirror_name = name.replace('_{}_'.format(side), '_{}_'.format(to_side[i]))
            break

    return mirror_name


def get_mirror_axis(name, mirror_plane):
    """
    Returns mirror axis of the given node name
    :param name: str
    :param mirror_plane: str, mirror plane ("YZ", "XY", "XZ")
    :return: str
    """

    return transform.get_mirror_axis(name, mirror_plane)


def is_axis_mirrored(source_node, target_node, axis, mirror_plane):
    """
    Returns whether given nodes axis are mirrored
    :param source_node: str
    :param target_node: str
    :param axis: list(int)
    :param mirror_plane: str
    :return: bool
    """

    return transform.is_axis_mirrored(source_node, target_node, axis, mirror_plane)


def get_color_of_side(side='C', sub_color=False):
    """
    Returns override color of the given side
    :param side: str
    :param sub_color: fool, whether to return a sub color or not
    :return:
    """

    if name_is_center(side):
        side = 'C'
    elif name_is_left(side):
        side = 'L'
    elif name_is_right(side):
        side = 'R'
    else:
        side = 'C'

    if not sub_color:
        if side == 'L':
            return [0, 0, 255]
        elif side == 'R':
            return [2551, 0, 0]
        else:
            return [255, 255, 0]
    else:
        if side == 'L':
            return [99, 220, 255]
        elif side == 'R':
            return [255, 175, 175]
        else:
            return [227, 172, 121]


def name_is_center(side, patterns=None):
    """
    Returns whether given side is a valid center side or not
    :param side: str
    :param patterns: list<str>
    :return: bool
    """

    if not patterns:
        patterns = consts.SIDE_PATTERNS['center']

    side = str(side)
    for pattern in patterns:
        return side.startswith('{}_'.format(pattern)) or side.endswith(
            '_{}'.format(pattern)) or '_{}_'.format(pattern) in side

    return False


def name_is_left(side, patterns=None):
    """
    Returns whether given side is a valid left side or not
    :param side: str
    :param patterns: list<str>
    :return: bool
    """

    if not patterns:
        patterns = consts.SIDE_PATTERNS['left']

    side = str(side)
    for pattern in patterns:
        if side.startswith('{}_'.format(pattern)) or side.endswith(
                '_{}'.format(pattern)) or '_{}_'.format(pattern) in side or side == pattern:
            return True

    return False


def name_is_right(side, patterns=None):
    """
    Returns whether given side is a valid right side or not
    :param side: str
    :param patterns: list<str>
    :return: bool
    """

    if not patterns:
        patterns = consts.SIDE_PATTERNS['right']

    side = str(side)
    for pattern in patterns:
        if side.startswith('{}_'.format(pattern)) or side.endswith(
                '_{}'.format(pattern)) or '_{}_'.format(pattern) in side or side == pattern:
            return True

    return False


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

    rename_shape = kwargs.get('rename_shape', True)

    if filter_type:
        return name.find_unique_name_by_filter(
            filter_type=filter_type, include_last_number=include_last_number, do_rename=do_rename,
            rename_shape=rename_shape, search_hierarchy=search_hierarchy, selection_only=selection_only,
            dag=False, remove_maya_defaults=True, transforms_only=True)
    else:
        return name.find_unique_name(
            obj_names=obj_names, include_last_number=include_last_number, do_rename=do_rename,
            rename_shape=rename_shape)


def find_available_name(node_name, **kwargs):
    """
    Returns an available object name in current DCC scene
    :param node_name: str
    :param kwargs: dict
    :return: str
    """

    suffix = kwargs.get('suffix', None)
    index = kwargs.get('index', 0)
    padding = kwargs.get('padding', 0)
    letters = kwargs.get('letters', False)
    capital = kwargs.get('capital', False)

    return name.find_available_name(
        name=node_name, suffix=suffix, index=index, padding=padding, letters=letters, capital=capital)


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

    rename_shape = kwargs.get('rename_shape', True)

    if filter_type:
        return name.add_prefix_by_filter(
            prefix=prefix, filter_type=filter_type, rename_shape=rename_shape, add_underscore=add_underscore,
            search_hierarchy=search_hierarchy, selection_only=selection_only, dag=False, remove_maya_defaults=True,
            transforms_only=True)
    else:
        return name.add_prefix(
            prefix=prefix, obj_names=obj_names, add_underscore=add_underscore, rename_shape=rename_shape)


def add_name_suffix(
        suffix, obj_names=None, filter_type=None, add_underscore=False, search_hierarchy=False,
        selection_only=True, **kwargs):
    """
    Add prefix to node name
    :param suffix: str, string to add to the end of the current node
    :param obj_names: str or list(str), name of list of node names to rename
    :param filter_type: str, name of object type to filter the objects to apply changes ('Group, 'Joint', etc)
    :param add_underscore: bool, Whether or not to add underscore before the suffix
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search only selected objects or all scene objects
    :param kwargs:
    """

    rename_shape = kwargs.get('rename_shape', True)

    if filter_type:
        return name.add_suffix_by_filter(
            suffix=suffix, filter_type=filter_type, add_underscore=add_underscore, rename_shape=rename_shape,
            search_hierarchy=search_hierarchy, selection_only=selection_only, dag=False, remove_maya_defaults=True,
            transforms_only=True)
    else:
        return name.add_suffix(
            suffix=suffix, obj_names=obj_names, add_underscore=add_underscore, rename_shape=rename_shape)


def remove_name_prefix(
        obj_names=None, filter_type=None, separator='_', search_hierarchy=False, selection_only=True, **kwargs):
    """
    Removes prefix from node name
    :param obj_names: str or list(str), name of list of node names to rename
    :param filter_type: str, name of object type to filter the objects to apply changes ('Group, 'Joint', etc)
    :param separator: str, separator character for the prefix
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search only selected objects or all scene objects
    :param kwargs:
    """

    rename_shape = kwargs.get('rename_shape', True)

    if filter_type:
        return name.edit_item_index_by_filter(
            index=0, filter_type=filter_type, text='', mode=name.EditIndexModes.REMOVE, separator=separator,
            rename_shape=rename_shape, search_hierarchy=search_hierarchy, selection_only=selection_only, dag=False,
            remove_maya_defaults=True, transforms_only=True)
    else:
        return name.edit_item_index(
            obj_names=obj_names, index=0, mode=name.EditIndexModes.REMOVE, separator=separator,
            rename_shape=rename_shape)


def remove_name_suffix(
        obj_names=None, filter_type=None, separator='_', search_hierarchy=False, selection_only=True, **kwargs):
    """
    Removes suffix from node name
    :param obj_names: str or list(str), name of list of node names to rename
    :param filter_type: str, name of object type to filter the objects to apply changes ('Group, 'Joint', etc)
    :param separator: str, separator character for the suffix
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search only selected objects or all scene objects
    :param kwargs:
    """

    rename_shape = kwargs.get('rename_shape', True)

    if filter_type:
        return name.edit_item_index_by_filter(
            index=-1, filter_type=filter_type, text='', mode=name.EditIndexModes.REMOVE, separator=separator,
            rename_shape=rename_shape, search_hierarchy=search_hierarchy, selection_only=selection_only, dag=False,
            remove_maya_defaults=True, transforms_only=True)
    else:
        return name.edit_item_index(
            obj_names=obj_names, index=-1, mode=name.EditIndexModes.REMOVE, separator=separator,
            rename_shape=rename_shape)


def auto_name_suffix(obj_names=None, filter_type=None, search_hierarchy=False, selection_only=True, **kwargs):
    """
    Automatically add a sufix to node names
    :param obj_names: str or list(str), name of list of node names to rename
    :param filter_type: str, name of object type to filter the objects to apply changes ('Group, 'Joint', etc)
    :param separator: str, separator character for the suffix
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search only selected objects or all scene objects
    :param kwargs:
    """

    rename_shape = kwargs.get('rename_shape', True)

    if filter_type:
        return name.auto_suffix_object_by_type(
            filter_type=filter_type, rename_shape=rename_shape, search_hierarchy=search_hierarchy,
            selection_only=selection_only, dag=False, remove_maya_defaults=True, transforms_only=True)
    else:
        return name.auto_suffix_object(obj_names=obj_names, rename_shape=rename_shape)


def remove_name_numbers(
        obj_names=None, filter_type=None, search_hierarchy=False, selection_only=True, remove_underscores=True,
        trailing_only=False, **kwargs):
    """
    Removes numbers from node names
    :param obj_names: str or list(str), name of list of node names to rename
    :param filter_type: str, name of object type to filter the objects to apply changes ('Group, 'Joint', etc)
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search only selected objects or all scene objects
    :param remove_underscores: bool, Whether or not to remove unwanted underscores
    :param trailing_only: bool, Whether or not to remove only numbers at the ned of the name
    :param kwargs:
    :return:
    """

    rename_shape = kwargs.get('rename_shape', True)

    if filter_type:
        return name.remove_numbers_from_object_by_filter(
            filter_type=filter_type, rename_shape=rename_shape, remove_underscores=remove_underscores,
            trailing_only=trailing_only, search_hierarchy=search_hierarchy, selection_only=selection_only,
            dag=False, remove_maya_defaults=True, transforms_only=True)
    else:
        return name.remove_numbers_from_object(
            obj_names=obj_names, trailing_only=trailing_only, rename_shape=rename_shape,
            remove_underscores=remove_underscores)


def renumber_objects(
        obj_names=None, filter_type=None, remove_trailing_numbers=True, add_underscore=True, padding=2,
        search_hierarchy=False, selection_only=True, **kwargs):
    """
    Removes numbers from node names
    :param obj_names: str or list(str), name of list of node names to rename
    :param filter_type: str, name of object type to filter the objects to apply changes ('Group, 'Joint', etc)
    :param remove_trailing_numbers: bool, Whether to remove trailing numbers before doing the renumber
    :param add_underscore: bool, Whether or not to remove underscore between name and new number
    :param padding: int, amount of numerical padding (2=01, 3=001, etc). Only used if given names has no numbers.
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search only selected objects or all scene objects
    :param kwargs:
    :return:
    """

    rename_shape = kwargs.get('rename_shape', True)

    if filter_type:
        return name.renumber_objects_by_filter(
            filter_type=filter_type, remove_trailing_numbers=remove_trailing_numbers,
            add_underscore=add_underscore, padding=padding, rename_shape=rename_shape,
            search_hierarchy=search_hierarchy, selection_only=selection_only, dag=False, remove_maya_defaults=True,
            transforms_only=True
        )
    else:
        return name.renumber_objects(
            obj_names=obj_names, remove_trailing_numbers=remove_trailing_numbers,
            add_underscore=add_underscore, padding=padding)


def change_suffix_padding(
        obj_names=None, filter_type=None, add_underscore=True, padding=2,
        search_hierarchy=False, selection_only=True, **kwargs):
    """
    Removes numbers from node names
    :param obj_names: str or list(str), name of list of node names to rename
    :param filter_type: str, name of object type to filter the objects to apply changes ('Group, 'Joint', etc)
    :param add_underscore: bool, Whether or not to remove underscore between name and new number
    :param padding: int, amount of numerical padding (2=01, 3=001, etc). Only used if given names has no numbers.
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search only selected objects or all scene objects
    :param kwargs:
    :return:
    """

    rename_shape = kwargs.get('rename_shape', True)

    if filter_type:
        return name.change_suffix_padding_by_filter(
            filter_type=filter_type, add_underscore=add_underscore, padding=padding, rename_shape=rename_shape,
            search_hierarchy=search_hierarchy, selection_only=selection_only, dag=False, remove_maya_defaults=True,
            transforms_only=True
        )
    else:
        return name.change_suffix_padding(obj_names=obj_names, add_underscore=add_underscore, padding=padding)


# =================================================================================================================
# NAMESPACES
# =================================================================================================================

def node_name_without_namespace(node):
    """
    Returns the name of the given node without namespace
    :param node: str
    :return: str
    """

    return name.get_basename(node, remove_namespace=True)


def list_namespaces():
    """
    Returns a list of all available namespaces
    :return: list(str)
    """

    return namespace.get_all_namespaces()


def list_namespaces_from_selection():
    """
    Returns all namespaces of current selected objects
    :return: list(str)
    """

    return namespace.get_namespaces_from_selection()


def namespace_separator():
    """
    Returns character used to separate namespace from the node name
    :return: str
    """

    return '|'


def namespace_exists(name):
    """
    Returns whether given namespace exists in current scene
    :param name: str
    :return: bool
    """

    return namespace.namespace_exists(name)


def unique_namespace(name):
    """
    Returns a unique namespace from the given one
    :param name: str
    :return: str
    """

    return namespace.find_unique_namespace(name)


def node_namespace(node_name, check_node=True, clean=False):
    """
    Returns namespace of the given node
    :param node_name: str
    :param check_node: bool
    :param clean: bool
    :return: str
    """

    if not helpers.is_string(node_name):
        node_name = node.get_name(node_name, fullname=True)

    if node_is_referenced(node_name):
        try:
            found_namespace = maya.cmds.referenceQuery(node_name, namespace=True)
        except Exception as exc:
            found_namespace = namespace.get_namespace(node_name, check_obj=check_node)
    else:
        found_namespace = namespace.get_namespace(node_name, check_obj=check_node)
    if not found_namespace:
        return None

    if clean:
        if found_namespace.startswith('|') or found_namespace.startswith(':'):
            found_namespace = found_namespace[1:]

    return found_namespace


def all_nodes_in_namespace(namespace_name):
    """
    Returns all nodes in given namespace
    :return: list(str)
    """

    return namespace.get_all_in_namespace(namespace_name)


def rename_namespace(current_namespace, new_namespace):
    """
    Renames namespace of the given node
    :param current_namespace: str
    :param new_namespace: str
    :return: str
    """

    return namespace.rename_namepace(current_namespace, new_namespace)


def node_parent_namespace(node):
    """
    Returns namespace of the given node parent
    :param node: str
    :return: str
    """

    return maya.cmds.referenceQuery(node, parentNamespace=True)


def assign_node_namespace(node, node_namespace, force_create=True, **kwargs):
    """
    Assigns a namespace to given node
    :param node: str
    :param node_namespace: str
    :param force_create: bool
    """

    rename_shape = kwargs.get('rename_shape', True)

    return namespace.assign_namespace_to_object(
        node, node_namespace, force_create=force_create, rename_shape=rename_shape)


def scene_namespaces():
    """
    Returns all the available namespaces in the current scene
    :return: list(str)
    """

    return namespace.get_all_namespaces()


def change_namespace(old_namespace, new_namespace):
    """
    Changes old namespace by a new one
    :param old_namespace: str
    :param new_namespace: str
    """

    return maya.cmds.namespace(rename=[old_namespace, new_namespace])


# =================================================================================================================
# SCENE
# =================================================================================================================

def get_current_time():
    """
    Returns current scene time
    :return: int
    """

    return maya.cmds.currentTime(query=True)


def new_scene(force=True, do_save=True):
    """
    Creates a new DCC scene
    :param force: bool, True if we want to save the scene without any prompt dialog
    :param do_save: bool, True if you want to save the current scene before creating new scene
    :return:
    """

    return scene.new_scene(force=force, do_save=do_save)


def scene_is_modified():
    """
    Returns whether current opened DCC file has been modified by the user or not
    :return: True if current DCC file has been modified by the user; False otherwise
    :rtype: bool
    """

    return maya.cmds.file(query=True, modified=True)


def new_file(force=True):
    """
    Creates a new file
    :param force: bool
    """

    maya.cmds.file(new=True, f=force)


def open_file(file_path, force=True):
    """
    Open file in given path
    :param file_path: str
    :param force: bool
    """

    # we must do the check, otherwise depending on the type Maya can crash
    if not file_path or not os.path.isfile(file_path):
        logger.warning('Impossible to open non existent file: "{}"'.format(file_path))
        return

    nodes = maya.cmds.file(file_path, o=True, f=force, returnNewNodes=True)

    scene_ext = os.path.splitext(file_path)[-1]
    scene_type = None
    if scene_ext == '.ma':
        scene_type = 'mayaAscii'
    elif scene_ext == '.mb':
        scene_type = 'mayaBinary'
    if scene_type:
        maya.mel.eval('$filepath = "{}";'.format(file_path))
        maya.mel.eval('addRecentFile $filepath "{}";'.format(scene_type))

    return nodes


def import_file(file_path, force=True, **kwargs):
    """
    Imports given file into current DCC scene
    :param file_path: str
    :param force: bool
    :return:
    """

    # we must do the check, otherwise depending on the type Maya can crash
    if not file_path or not os.path.isfile(file_path):
        logger.warning('Impossible to import non existent file: "{}"'.format(file_path))
        return

    import_type = kwargs.get('type', None)
    options = kwargs.get('options', None)
    ignore_version = kwargs.get('ignore_version', None)
    namespace = kwargs.get('namespace', None)
    unique_namespace = kwargs.get('unique_namespace', True)

    import_kwargs = {
        'i': True,
        'f': force,
        'returnNewNodes': True,
    }
    if ignore_version is not None:
        import_kwargs['ignoreVersion'] = ignore_version
    if namespace:
        import_kwargs['namespace'] = namespace
    if unique_namespace:
        import_kwargs['mergeNamespacesOnClash'] = True
    if import_type:
        import_kwargs['type'] = import_type
    if options:
        import_kwargs['options'] = options

    return maya.cmds.file(file_path, **import_kwargs)


def merge_file(file_path, force=True, **kwargs):
    """
    Merges given file into current DCC scene
    :param file_path: str
    :param force: bool
    :return:
    """

    return import_file(file_path, force=force, **kwargs)


def reference_file(file_path, force=True, **kwargs):
    """
    References given file into current DCC scene
    :param file_path: str
    :param force: bool
    :param kwargs: keyword arguments
    :return:
    """

    # we must do the check, otherwise depending on the type Maya can crash
    if not file_path or not os.path.isfile(file_path):
        logger.warning('Impossible to reference non existent file: "{}"'.format(file_path))
        return

    namespace = kwargs.get('namespace', None)
    if namespace:
        unique_namespace = kwargs.get('unique_namespace', True)
        if unique_namespace:
            return maya.cmds.file(file_path, reference=True, f=force, returnNewNodes=True, namespace=namespace)
        else:
            return maya.cmds.file(
                file_path, reference=True, f=force, returnNewNodes=True,
                mergeNamespacesOnClash=True, namespace=namespace)

    else:
        return maya.cmds.file(file_path, reference=True, f=force, returnNewNodes=True)


def import_obj_file(file_path, force=True, **kwargs):
    """
    Imports OBJ file into current DCC scene
    :param file_path: str
    :param force: bool
    :param kwargs: keyword arguments
    :return:
    """

    if not is_plugin_loaded('objexport.mll'):
        load_plugin('objexport.mll', quiet=True)

    kwargs['type'] = 'OBJ'

    return import_file(file_path, force=force, **kwargs)


def import_fbx_file(file_path, force=True, **kwargs):
    """
    Imports FBX file into current DCC scene
    :param file_path: str
    :param force: bool
    :param kwargs: keyword arguments
    :return:
    """

    if not is_plugin_loaded('fbxmaya.mll'):
        load_plugin('objexport.mll', quiet=True)

    kwargs['type'] = 'FBX export'

    return import_file(file_path, force=force, **kwargs)


def scene_name():
    """
    Returns the name of the current scene
    :return: str
    """

    return maya.cmds.file(query=True, sceneName=True)


def save_current_scene(force=True, **kwargs):
    """
    Saves current scene
    :param force: bool
    """

    path_to_save = kwargs.get('path_to_save', None)
    name_to_save = kwargs.get('name_to_save', None)
    extension_to_save = kwargs.get('extension_to_save', get_extensions()[0])
    current_scene_name = scene_name()
    if current_scene_name:
        extension_to_save = os.path.splitext(current_scene_name)[-1]
    if not extension_to_save.startswith('.'):
        extension_to_save = '.{}'.format(extension_to_save)
    maya_scene_type = 'mayaAscii' if extension_to_save == '.ma' else 'mayaBinary'

    if current_scene_name:
        if path_to_save and name_to_save:
            maya.cmds.file(rename=os.path.join(path_to_save, '{}{}'.format(name_to_save, extension_to_save)))
        return maya.cmds.file(save=True, type=maya_scene_type, f=force)
    else:
        if path_to_save and name_to_save:
            maya.cmds.file(rename=os.path.join(path_to_save, '{}{}'.format(name_to_save, extension_to_save)))
            return maya.cmds.file(save=True, type=maya_scene_type, f=force)
        else:
            if force:
                return maya.cmds.SaveScene()
            else:
                if scene_is_modified():
                    return maya.cmds.SaveScene()
                else:
                    return maya.cmds.file(save=True, type=maya_scene_type)


def export_current_selection(export_path, export_type, force=True, **kwargs):
    """
    Exports current selection to a file
    :param export_path: str
    :param export_type: str
    :param force: bool
    :param kwargs:
    :return:
    """

    options = kwargs.get('options', None)
    preserve_references = kwargs.get('preserve_references', False)

    current_scene_name = scene_name()

    if current_scene_name:
        maya.cmds.file(rename=export_path)

    if options:
        result = maya.cmds.file(
            force=force, options=options, type=export_type, preserveReferences=preserve_references, exportSelected=True)
    else:
        result = maya.cmds.file(
            force=force, type=export_type, preserveReferences=preserve_references, exportSelected=True)

    if current_scene_name:
        maya.cmds.file(rename=current_scene_name)

    return result


def force_rename_to_save_scene():
    """
    Forces current scene to be renamed before it can be saved
    """

    return maya.cmds.file(renameToSave=True)


def all_scene_nodes(full_path=True):
    """
    Returns a list with all scene nodes
    :param full_path: bool
    :return: list<str>
    """

    return maya.cmds.ls(long=full_path)


def default_scene_nodes(full_path=True):
    """
    Returns a list of nodes that are created by default by the DCC when a new scene is created
    :param full_path: bool
    :return: list<str>
    """

    return maya.cmds.ls(defaultNodes=True)


def selected_nodes(full_path=True, **kwargs):
    """
    Returns a list of selected nodes
    :param full_path: bool
    :return: list<str>
    """

    flatten = kwargs.get('flatten', False)

    return maya.cmds.ls(sl=True, long=full_path, flatten=flatten)


def selected_nodes_in_order(full_path=True, **kwargs):
    """
    Returns a list of selected nodes in order of selection
    :param full_path: bool
    :return: list<str>
    """

    flatten = kwargs.get('flatten', False)

    try:
        return maya.cmds.ls(sl=True, long=full_path, flatten=flatten, orderedSelection=True)
    except RuntimeError:
        return maya.cmds.ls(sl=True, long=full_path, flatten=flatten)


def selected_nodes_of_type(node_type, full_path=True):
    """
    Returns a list of selected nodes of given type
    :param node_type: str
    :param full_path: bool
    :return: list(str)
    """

    return maya.cmds.ls(sl=True, type=node_type, long=full_path)


def selected_hilited_nodes(full_path=True):
    """
    Returns a list of selected nodes that are hilited for component selection
    :param full_path: bool
    :return: list(str)
    """

    return maya.cmds.ls(long=full_path, hilite=True)


def select_node(node, replace_selection=True, **kwargs):
    """
    Selects given object in the current scene
    :param replace_selection: bool
    :param node: str
    """

    return maya.cmds.select(node, replace=replace_selection, add=not replace_selection, **kwargs)


def select_nodes_by_rgb_color(node_rgb_color, nodes_to_select=None):
    """
    Selects all nodes with the given color
    :param node_rgb_color: list(float, float, float)
    :param nodes_to_select: list(str), list of nodes to select.
    If not given, all scene nodes will be taken into account
    """

    nodes_to_select = nodes_to_select if nodes_to_select else all_scene_nodes()
    return node.select_nodes_by_rgb_color(nodes_to_select, node_rgb_color)


def select_hierarchy(root=None, add=False):
    """
    Selects the hierarchy of the given node
    If no object is given current selection will be used
    :param root: str
    :param add: bool, Whether new selected objects need to be added to current selection or not
    """

    if not root or not node_exists(root):
        sel = maya.cmds.ls(selection=True)
        for obj in sel:
            if not add:
                maya.cmds.select(clear=True)
            maya.cmds.select(obj, hi=True, add=True)
    else:
        maya.cmds.select(root, hi=True, add=add)


def deselect_node(node):
    """
    Deselects given node from current selection
    :param node: str
    """

    return maya.cmds.select(node, deselect=True)


def clear_selection():
    """
    Clears current scene selection
    """

    return maya.cmds.select(clear=True)


def toggle_xray():
    """
    Toggle XRay functionality (model is displayed with transparency)
    """

    current_panel = maya.cmds.getPanel(withFocus=True)
    try:
        if maya.cmds.modelEditor(current_panel, query=True, xray=True):
            maya.cmds.modelEditor(current_panel, edit=True, xray=False)
        else:
            maya.cmds.modelEditor(current_panel, edit=True, xray=True)
    except Exception as exc:
        logger.warning('Error while toggling xray: {}'.format(exc))


def toggle_xray_on_selection():
    """
    Toggle XRay functionality (model is displayed with transparency) on selected geometry
    """

    selected = maya.cmds.ls(sl=True, dagObjects=True, shapes=True)
    for obj in selected:
        xray_state = maya.cmds.displaySurface(obj, query=True, xRay=True)[0]
        maya.cmds.displaySurface(obj, xRay=not xray_state)


def clean_scene():
    """
    Cleans invalid nodes from current scene
    """

    scene.clean_scene()


# =================================================================================================================
# TRANSFORMS
# =================================================================================================================

def convert_translation(translation):
    """
    Converts given translation into a valid translation to be used with tpDcc
    NOTE: tpDcc uses Y up coordinate axes as the base reference axis
    NOTE: Maya can work with both Y axis and Z axis
    :param translation: tuple(float, float, float)
    :return: tuple(float, float, float)
    """

    if get_up_axis_name().lower() == 'y':
        return translation

    return translation[0], -translation[2], translation[1]


def convert_dcc_translation(translation):
    """
    Converts given tpDcc translation into a translation that DCC can manage
    NOTE: tpDcc uses Y up coordinate axes as the base reference axis
    :param translation: list(float, float, float)
    :return: list(float, float, float)
    """

    if get_up_axis_name().lower() == 'y':
        return translation

    return translation[0], translation[2], -translation[1]


def convert_rotation(rotation):
    """
    Converts given rotation into a valid rotation to be used with tpDcc
    NOTE: tpDcc uses Y up coordinate axes as the base reference axis
    :param rotation: tuple(float, float, float)
    :return: tuple(float, float, float)
    """

    if get_up_axis_name().lower() == 'y':
        return rotation

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

    if get_up_axis_name().lower() == 'y':
        return rotation

    rotation_matrix1 = np.array(matrix.rotation_matrix_xyz(rotation))
    rotation_matrix2 = np.array(matrix.rotation_matrix_xyz([90, 0, 0]))
    rotation_matrix3 = matrix.rotation_matrix_to_xyz_euler(
        rotation_matrix2.dot(rotation_matrix1).dot(np.linalg.inv(rotation_matrix2)))

    return list(rotation_matrix3)


def convert_scale(scale):
    """
    Converts given scale into a valid rotation to be used with tpDcc
    NOTE: tpDcc uses Y up coordinate axes as the base reference axis
    :param scale: tuple(float, float, float)
    :return: tuple(float, float, float)
    """

    if get_up_axis_name().lower() == 'y':
        return scale

    return scale[0], scale[2], scale[1]


def convert_dcc_scale(scale):
    """
    Converts given scale into a scale that DCC can manage
    NOTE: tpDcc uses Y up coordinate axes as the base reference axis
    :param scale: list(float, float, float)
    :return: list(float, float, float)
    """

    if get_up_axis_name().lower() == 'y':
        return scale

    return scale[0], scale[2], scale[1]


def get_up_axis_name():
    """
    Returns the name of the current DCC up axis
    :return: str
    """

    return maya.cmds.upAxis(query=True, axis=True)


def node_world_matrix(node):
    """
    Returns node world matrix of given node
    :param node: str
    :return: list
    """

    return maya.cmds.xform(node, matrix=True, query=True, worldSpace=True)


def set_node_world_matrix(node, world_matrix):
    """
    Sets node world matrix of given node
    :param node: str
    :param world_matrix: list
    :return: list
    """

    return maya.cmds.xform(node, matrix=world_matrix, worldSpace=True)


def node_world_space_translation(node):
    """
    Returns translation of given node in world space
    :param node: str
    :return: list
    """

    return maya.cmds.xform(node, worldSpace=True, q=True, translation=True)


def node_world_bounding_box(node):
    """
    Returns world bounding box of given node
    :param node: str
    :return: list(float, float, float, float, float, float)
    """

    return maya.cmds.xform(node, worldSpace=True, q=True, boundingBox=True)


def set_rotation_axis(node, rotation_axis):
    """
    Sets the rotation axis used by the given node
    :param node: str
    :param rotation_axis: str or int
    """

    if helpers.is_string(rotation_axis):
        rotation_axis = maya_constants.ROTATION_AXES.index(rotation_axis)

    set_attribute_value(node, 'rotateOrder', rotation_axis)


def move_node(node, x, y, z, **kwargs):
    """
    Moves given node
    :param node: str
    :param x: float
    :param y: float
    :param z: float
    :param kwargs:
    """

    relative = kwargs.get('relative', False)
    object_space = kwargs.get('object_space', False)
    world_space = kwargs.get('world_space', True)
    world_space_distance = kwargs.get('world_space_distance', False)
    if object_space:
        world_space = False

    return maya.cmds.move(
        x, y, z, node, relative=relative, os=object_space, ws=world_space, wd=world_space_distance)


def translate_node_in_world_space(node, translation_list, **kwargs):
    """
    Translates given node in world space with the given translation vector
    :param node: str
    :param translation_list:  list(float, float, float)
    """

    relative = kwargs.pop('relative', False)

    return maya.cmds.xform(node, worldSpace=True, t=translation_list, relative=relative)


def translate_node_in_object_space(node, translation_list, **kwargs):
    """
    Translates given node with the given translation vector
    :param node: str
    :param translation_list:  list(float, float, float)
    """

    relative = kwargs.pop('relative', False)

    return maya.cmds.xform(node, objectSpace=True, t=translation_list, relative=relative)


def node_world_space_rotation(node):
    """
    Returns world rotation of given node
    :param node: str
    :return: list
    """

    return maya.cmds.xform(node, worldSpace=True, q=True, rotation=True)


def rotate_node(node, x, y, z, **kwargs):
    """
    Rotates given node
    :param node: str
    :param x: float
    :param y: float
    :param z: float
    :param kwargs:
    """

    relative = kwargs.get('relative', False)
    object_space = kwargs.get('object_space', False)
    world_space = kwargs.get('world_space', True)
    if object_space:
        world_space = False

    return maya.cmds.rotate(x, y, z, node, relative=relative, os=object_space, ws=world_space)


def rotate_node_in_world_space(node, rotation_list, **kwargs):
    """
    Translates given node with the given translation vector
    :param node: str
    :param rotation_list:  list(float, float, float)
    """

    relative = kwargs.pop('relative', False)

    return maya.cmds.xform(node, worldSpace=True, ro=rotation_list, relative=relative)


def rotate_node_in_object_space(node, rotation_list, **kwargs):
    """
    Translates given node with the given translation vector
    :param node: str
    :param rotation_list:  list(float, float, float)
    """

    relative = kwargs.pop('relative', False)

    return maya.cmds.xform(node, objectSpace=True, ro=rotation_list, relative=relative)


def node_world_space_scale(node):
    """
    Returns world scale of given node
    :param node: str
    :return: list
    """

    return maya.cmds.xform(node, worldSpace=True, q=True, scale=True)


def scale_node(node, x, y, z, **kwargs):
    """
    Scales node
    :param node: str
    :param x: float
    :param y: float
    :param z: float
    :param kwargs:
    """

    pivot = kwargs.get('pivot', False)
    relative = kwargs.get('relative', False)

    return maya.cmds.scale(x, y, z, node, pivot=pivot, relative=relative)


def scale_node_in_world_space(node, scale_list, **kwargs):
    """
    Scales given node with the given vector list
    :param node: str
    :param scale_list: list(float, float, float)
    """

    relative = kwargs.pop('relative', False)

    return maya.cmds.xform(node, worldSpace=True, s=scale_list, relative=relative)


def scale_node_in_object_space(node, scale_list, **kwargs):
    """
    Scales given node with the given vector list
    :param node: str
    :param scale_list: list(float, float, float)
    """

    relative = kwargs.pop('relative', False)

    return maya.cmds.xform(node, objectSpace=True, s=scale_list, relative=relative)


def scale_transform_shapes(node, scale_value, **kwargs):
    """
    Scales given node by given scale value
    :param node: str
    :param scale_value: float
    :param kwargs:
    """

    if not isinstance(scale_value, (list, tuple)):
        scale_value = (scale_value, scale_value, scale_value)

    shapes = shape.get_shapes(node) if transform.is_transform(node) else [node]
    components = shape.get_components_from_shapes(shapes)
    pivot = maya.cmds.xform(node, query=True, rp=True, ws=True)
    maya.cmds.scale(scale_value[0], scale_value[1], scale_value[2], components, p=pivot, r=True)


def node_world_space_pivot(node):
    """
    Returns node pivot in world space
    :param node: str
    :return:
    """

    return maya.cmds.xform(node, query=True, rp=True, ws=True)


def mirror_transform(create_if_missing=False, transforms=None, left_to_right=True, **kwargs):
    """
    Mirrors the position of all transforms
    :param create_if_missing:
    :param transforms:
    :param left_to_right:
    :param kwargs:
    """

    prefix = kwargs.pop('prefix', None)
    suffix = kwargs.pop('suffix', None)
    string_search = kwargs.pop('string_search', None)

    return transform.mirror_transform(
        prefix=prefix, suffix=suffix, string_search=string_search, create_if_missing=create_if_missing,
        transforms=transforms, left_to_right=left_to_right)


def get_closest_transform(source_transform, targets):
    """
    Given the list of target transforms, find the closest to the source transform
    :param source_transform: str, name of the transform to test distance to
    :param targets: list<str>, list of targets to test distance against
    :return: str, name of the target in targets that is closest to source transform
    """

    return transform.get_closest_transform(source_transform, targets)


def distance_between_transforms(source_transform, target_transform):
    """
    Returns the total distance between given transform nodes
    :param source_transform: str, name of the source transform node
    :param target_transform: str, name of the target transform node
    :return: float, total distance between both nodes
    """

    return transform.get_distance(source_transform, target_transform)


def rename_transform_shape_nodes(node):
    """
    Renames all shape nodes of the given transform node
    :param node: str
    """

    return shape.rename_shapes(transform_node=node)


def node_matrix(node):
    """
    Returns the world matrix of the given node
    :param node: str
    :return:
    """

    return transform.get_matrix(transform=node, as_list=True)


def set_node_matrix(node, matrix):
    """
    Sets the world matrix of the given node
    :param node: str
    :param matrix: variant, MMatrix or list
    """

    return maya.cmds.xform(node, matrix=matrix, worldSpace=True)


def freeze_transforms(node, translate=True, rotate=True, scale=True, **kwargs):
    """
    Freezes the transformations of the given node and its children
    :param node: str
    :param translate: bool
    :param rotate: bool
    :param scale: str
    """

    normal = kwargs.get('normal', False)
    preserve_normals = kwargs.get('preserve_normals', True)
    clean_history = kwargs.get('clean_history', False)

    return transform.freeze_transforms(
        transform=node, translate=translate, rotate=rotate, scale=scale, normal=normal,
        preserve_normals=preserve_normals, clean_history=clean_history)


def zero_transform_attribute_channels(node):
    """
    Sets to zero all transform attribute channels of the given node (transform rotate and scale)
    :param node: str
    """

    return transform.zero_transform_channels(node)


def create_hierarchy(transforms, replace_str=None, new_str=None):
    """
    Creates a transforms hierarchy with the given list of joints
    :param transforms: list(str)
    :param replace_str: str, if given this string will be replace with the new_str
    :param new_str: str, if given replace_str will be replace with this string
    :return: list(str)
    """

    build_hierarchy = joint_utils.BuildJointHierarchy()
    build_hierarchy.set_transforms(transform)
    if replace_str and new_str:
        build_hierarchy.set_replace(replace_str, new_str)

    return build_hierarchy.create()


def duplicate_hierarchy(transforms, stop_at=None, force_only_these=None, replace_str=None, new_str=None):
    """
    Duplicates given hierarchy of transform nodes
    :param transforms: list(str), list of joints to duplicate
    :param stop_at: str, if given the duplicate process will be stop in the given node
    :param force_only_these: list(str), if given only these list of transforms will be duplicated
    :param replace_str: str, if given this string will be replace with the new_str
    :param new_str: str, if given replace_str will be replace with this string
    :return: list(str)
    """

    transforms = helpers.force_list(transforms)

    duplicate_hierarchy = transform.DuplicateHierarchy(transforms[0])
    if stop_at:
        duplicate_hierarchy.stop_at(stop_at)
    if force_only_these:
        duplicate_hierarchy.only_these(force_only_these)
    if replace_str and new_str:
        duplicate_hierarchy.set_replace(replace_str, new_str)

    return duplicate_hierarchy.create()


def center_pivot(node):
    """
    Centers the pivot of the given node
    :param node: str
    :return:
    """

    return maya.cmds.xform(node, cp=True)


def move_pivot_in_object_space(node, x, y, z):
    """
    Moves the pivot of the given node by the given values in object_space
    :param node: str
    :param x: float
    :param y: float
    :param z: float
    :return: float
    """

    maya.cmds.move(x, y, z, '{}.scalePivot'.format(node), '{}.rotatePivot'.format(node), relative=True)


def move_pivot_in_world_space(node, x, y, z):
    """
    Moves the pivot of the given node by the given values in world space
    :param node: str
    :param x: float
    :param y: float
    :param z: float
    :return: float
    """

    maya.cmds.move(x, y, z, '{}.scalePivot'.format(node), '{}.rotatePivot'.format(node), a=True)


def move_pivot_to_zero(node):
    """
    Moves pivot of given node to zero (0, 0, 0 in the world)
    :param node: str
    """

    return maya.cmds.xform(node, ws=True, a=True, piv=(0, 0, 0))


def reset_node_transforms(node, **kwargs):
    """
    Reset the transformations of the given node and its children
    :param node: str
    """

    # TODO: We should call freze transforms passing apply as False?

    return maya.cmds.ResetTransformations()


def set_node_rotation_axis_in_object_space(node, x, y, z):
    """
    Sets the rotation axis of given node in object space
    :param node: str
    :param x: int
    :param y: int
    :param z: int
    """

    return maya.cmds.xform(node, rotateAxis=[x, y, z], relative=True, objectSpace=True)


def node_bounding_box_size(node):
    """
    Returns the bounding box size of the given node
    :param node: str
    :return: float
    """

    bounding_box = transform.BoundingBox(node).get_shapes_bounding_box()
    size = bounding_box.get_size() if bounding_box else 0.0

    return size


def node_bounding_box_pivot(node):
    """
    Returns the bounding box pivot center of the given node
    :param node: str
    :return: list(float, float, float)
    """

    shapes = shape.get_shapes_of_type(node, shape_type='nurbsCurve')
    components = shape.get_components_from_shapes(shapes)
    bounding = transform.BoundingBox(components)
    pivot = bounding.get_center()

    return pivot


def match_translation(match_to, target_node):
    """
    Match translation of the given node to the translation of the target node
    :param match_to: str
    :param target_node: str
    """

    return transform.MatchTransform(match_to, target_node).translation()


def match_rotation(match_to, target_node):
    """
    Match rotation of the given node to the rotation of the target node
    :param match_to: str
    :param target_node: str
    """

    return transform.MatchTransform(match_to, target_node).rotation()


def match_scale(match_to, target_node):
    """
    Match scale of the given node to the rotation of the target node
    :param match_to: str
    :param target_node: str
    """

    return transform.MatchTransform(match_to, target_node).scale()


def match_translation_rotation(match_to, target_node):
    """
    Match translation and rotation of the target node to the translation and rotation of the source node
    :param match_to: str
    :param target_node: str
    """

    return transform.MatchTransform(match_to, target_node).translation_rotation()


def match_translation_to_rotate_pivot(match_to, target_node):
    """
    Matches target translation to the source transform rotate pivot
    :param match_to: str
    :param target_node: str
    :return:
    """

    return transform.MatchTransform(match_to, target_node).translation_to_rotate_pivot()


def match_transform(match_to, target_node):
    """
    Match the transform (translation, rotation and scale) of the given node to the rotation of the target node
    :param match_to: str
    :param target_node: str
    """

    valid_translate_rotate = transform.MatchTransform(match_to, target_node).translation_rotation()
    valid_scale = transform.MatchTransform(match_to, target_node).scale()

    return bool(valid_translate_rotate and valid_scale)


# =================================================================================================================
# GROUPS
# =================================================================================================================

def create_empty_group(name='grp', parent=None):
    """
    Creates a new empty group node
    Creates a new empty group node
    :param name: str
    :param parent: str or None
    """

    groups = helpers.create_group(name=name, parent=parent, world=True)
    if groups:
        return groups[0]


def create_buffer_group(node, **kwargs):
    """
    Creates a buffer group on top of the given node
    :param node: str
    :return: str
    """

    return transform.create_buffer_group(node, **kwargs)


def get_buffer_group(node, **kwargs):
    """
    Returns buffer group above given node
    :param node: str
    :return: str
    """

    suffix = kwargs.get('suffix', 'buffer')

    return transform.get_buffer_group(node, suffix=suffix)


def group_node(node, name, parent=None):
    """
    Creates a new group and parent give node to it
    :param node: str
    :param name: str
    :param parent: str
    :return: str
    """

    groups = helpers.create_group(name=name, nodes=node, parent=parent, world=True)
    if groups:
        return groups[0]


def create_empty_follow_group(target_transform, **kwargs):
    """
    Creates a new follow group above a target transform
    :param target_transform: str, name of the transform make follow
    :param kwargs:
    :return:
    """

    return space_utils.create_empty_follow_group(target_transform, **kwargs)


def create_follow_group(source_transform, target_transform, **kwargs):
    """
    Creates a group above a target transform that is constrained to the source transform
    :param source_transform: str, name of the transform to follow
    :param target_transform: str, name of the transform make follow
    :param kwargs:
    :return:
    """

    return space_utils.create_follow_group(source_transform, target_transform, **kwargs)


# =================================================================================================================
# CONSTRAINTS
# =================================================================================================================


def list_node_constraints(node):
    """
    Returns all constraints linked to given node
    :param node: str
    :return: list(str)
    """

    return maya.cmds.listRelatives(node, type='constraint')


def create_point_constraint(source, constraint_to, **kwargs):
    """
    Creates a new point constraint
    :param source:
    :param constraint_to:
    :param kwargs:
    :return:
    """

    maintain_offset = kwargs.get('maintain_offset', False)

    return maya.cmds.pointConstraint(constraint_to, source, mo=maintain_offset)[0]


def create_orient_constraint(source, constraint_to, **kwargs):
    """
    Creates a new orient constraint
    :param source:
    :param constraint_to:
    :param kwargs:
    :return:
    """

    maintain_offset = kwargs.get('maintain_offset', False)
    skip = kwargs.get('skip', 'none')

    return maya.cmds.orientConstraint(constraint_to, source, skip=skip, mo=maintain_offset)[0]


def create_scale_constraint(source, constraint_to, **kwargs):
    """
    Creates a new scale constraint
    :param source:
    :param constraint_to:
    :param kwargs:
    :return:
    """

    maintain_offset = kwargs.get('maintain_offset', False)

    return maya.cmds.scaleConstraint(constraint_to, source, mo=maintain_offset)[0]


def create_parent_constraint(source, constraint_to, **kwargs):
    """
    Creates a new parent constraint
    :param source:
    :param constraint_to:
    :param kwargs:
    :return:
    """

    maintain_offset = kwargs.get('maintain_offset', False)
    skip_translate = kwargs.get('skip_translate', 'none')
    skip_rotate = kwargs.get('skip_rotate', 'none')

    return maya.cmds.parentConstraint(
        constraint_to, source, st=skip_translate, sr=skip_rotate, mo=maintain_offset)[0]


def get_axis_aimed_at_child(transform_node):
    """
    Returns the axis that is pointing to the given transform
    :param transform_node: str, name of a transform node
    :return:
    """

    return transform.get_axis_aimed_at_child(transform_node)


def create_aim_constraint(source, point_to, **kwargs):
    """
    Creates a new aim constraint
    :param source: str
    :param point_to: str
    """

    aim_axis = kwargs.pop('aim_axis', (1.0, 0.0, 0.0))
    up_axis = kwargs.pop('up_axis', (0.0, 1.0, 0.0))
    world_up_axis = kwargs.pop('world_up_axis', (0.0, 1.0, 0.0))
    # World Up type: 0: scene up; 1: object up; 2: object rotation up; 3: vector; 4: None
    world_up_type = kwargs.pop('world_up_type', 3)
    world_up_object = kwargs.pop('world_up_object', None)
    weight = kwargs.pop('weight', 1.0)
    maintain_offset = kwargs.pop('maintain_offset', False)
    skip = kwargs.pop('skip', 'none')

    if world_up_object:
        kwargs['worldUpObject'] = world_up_object

    return maya.cmds.aimConstraint(
        point_to, source, aim=aim_axis, upVector=up_axis, worldUpVector=world_up_axis,
        worldUpType=world_up_type, weight=weight, mo=maintain_offset, skip=skip, **kwargs)


def create_pole_vector_constraint(control, handle):
    """
    Creates a new pole vector constraint
    :param control: str
    :param handle: str
    :return: str
    """

    return maya.cmds.poleVectorConstraint(control, handle)[0]


def delete_constraints(node, constraint_type=None):
    """
    Deletes all constraints applied to the given node
    :param node: str
    :param constraint_type: str
    :return: str
    """

    return constraint_utils.delete_constraints(node, constraint_type=constraint_type)


def get_constraint_functions_dict():
    """
    Returns a dict that maps each constraint type with its function in DCC API
    :return: dict(str, fn)
    """

    return {
        'pointConstraint': maya.cmds.pointConstraint,
        'orientConstraint': maya.cmds.orientConstraint,
        'parentConstraint': maya.cmds.parentConstraint,
        'scaleConstraint': maya.cmds.scaleConstraint,
        'aimConstraint': maya.cmds.aimConstraint
    }


def get_constraints():
    """
    Returns all constraints nodes in current DCC scene
    :return: list(str)
    """

    return maya.cmds.listRelatives(type='constraint')


def get_constraint_targets(constraint_node):
    """
    Returns target of the given constraint node
    :param constraint_node: str
    :return: list(str)
    """

    cns = constraint_utils.Constraint()

    return cns.get_targets(constraint_node)


def node_constraint(node, constraint_type):
    """
    Returns a constraint on the transform with the given type
    :param node: str
    :param constraint_type: str
    :return: str
    """

    cns = constraint_utils.Constraint()

    return cns.get_constraint(node, constraint_type=constraint_type)


def node_constraints(node):
    """
    Returns all constraints a node is linked to
    :param node: str
    :return: list(str)
    """

    return maya.cmds.listRelatives(node, type='constraint')


def delete_node_constraints(node):
    """
    Removes all constraints applied to the given node
    :param node: str
    """

    return maya.cmds.delete(maya.cmds.listRelatives(node, ad=True, type='constraint'))


def get_pole_vector_position(transform_init, transform_mid, transform_end, offset=1):
    """
    Given 3 transform (such as arm, elbow, wrist), returns a position where pole vector should be located
    :param transform_init: str, name of a transform node
    :param transform_mid: str, name of a transform node
    :param transform_end: str, name of a transform node
    :param offset: float, offset value for the final pole vector position
    :return: list(float, float, float), pole vector with offset
    """

    return transform.get_pole_vector(transform_init, transform_mid, transform_end, offset=offset)


# =================================================================================================================
# GEOMETRY
# =================================================================================================================

def meshes_are_similar(mesh1, mesh2):
    """
    Checks whether two meshes to see if they have the same vertices, edge and face count
    :param mesh1: str
    :param mesh2: str
    :return: bool
    """

    return geo_utils.is_mesh_compatible(mesh1, mesh2)


def combine_meshes(meshes_to_combine=None, **kwargs):
    """
    Combines given meshes into one unique mesh. If no meshes given, all selected meshes will be combined
    :param meshes_to_combine: list(str) or None
    :return: str
    """

    construction_history = kwargs.get('construction_history', True)
    if not meshes_to_combine:
        meshes_to_combine = maya.cmds.ls(sl=True, long=True)
    if not meshes_to_combine:
        return

    out, unite_node = maya.cmds.polyUnite(*meshes_to_combine)
    if not construction_history:
        delete_history(out)

    return out


def separate_meshes(meshes_to_separate=None, **kwargs):
    """
    Separates given meshes. If no meshes given, all selected meshes will be combined
    :param meshes_to_separate: list(str) or None
    :return: str
    """

    construction_history = kwargs.get('construction_history', True)
    if not meshes_to_separate:
        meshes_to_separate = maya.cmds.ls(sl=True, long=True)
    if not meshes_to_separate:
        return

    res = maya.cmds.polySeparate(*meshes_to_separate)
    out = res[:-1]
    if not construction_history:
        delete_history(out)

    return out


def node_vertex_name(mesh_node, vertex_id):
    """
    Returns the full name of the given node vertex
    :param mesh_node: str
    :param vertex_id: int
    :return: str
    """

    return '{}.vtx[{}]'.format(mesh_node, vertex_id)


def total_vertices(mesh_node):
    """
    Returns the total number of vertices of the given geometry
    :param mesh_node: str
    :return: int
    """

    return maya.cmds.polyEvaluate(mesh_node, vertex=True)


def node_vertex_object_space_translation(mesh_node, vertex_id=None):
    """
    Returns the object space translation of the vertex id in the given node
    :param mesh_node: str
    :param vertex_id: int
    :return:
    """

    if vertex_id is not None:
        vertex_name = node_vertex_name(mesh_node=mesh_node, vertex_id=vertex_id)
    else:
        vertex_name = mesh_node

    return maya.cmds.xform(vertex_name, objectSpace=True, q=True, translation=True)


def node_vertex_world_space_translation(mesh_node, vertex_id=None):
    """
    Returns the world space translation of the vertex id in the given node
    :param mesh_node: str
    :param vertex_id: int
    :return:
    """

    if vertex_id is not None:
        vertex_name = node_vertex_name(mesh_node=mesh_node, vertex_id=vertex_id)
    else:
        vertex_name = mesh_node

    return maya.cmds.xform(vertex_name, worldSpace=True, q=True, translation=True)


def set_node_vertex_object_space_translation(mesh_node, translate_list, vertex_id=None):
    """
    Sets the object space translation of the vertex id in the given node
    :param mesh_node: str
    :param translate_list: list
    :param vertex_id: int
    :return:
    """

    if vertex_id is not None:
        vertex_name = node_vertex_name(mesh_node=mesh_node, vertex_id=vertex_id)
    else:
        vertex_name = mesh_node

    return maya.cmds.xform(vertex_name, objectSpace=True, t=translate_list)


def set_node_vertex_world_space_translation(mesh_node, translate_list, vertex_id=None):
    """
    Sets the world space translation of the vertex id in the given node
    :param mesh_node: str
    :param translate_list: list
    :param vertex_id: int
    :return:
    """

    if vertex_id is not None:
        vertex_name = node_vertex_name(mesh_node=mesh_node, vertex_id=vertex_id)
    else:
        vertex_name = mesh_node

    return maya.cmds.xform(vertex_name, worldSpace=True, t=translate_list)


def create_nurbs_sphere(name='sphere', radius=1.0, **kwargs):
    """
    Creates a new NURBS sphere
    :param name: str
    :param radius: float
    :return: str
    """

    axis = kwargs.get('axis', (0, 1, 0))
    construction_history = kwargs.get('construction_history', True)

    return maya.cmds.sphere(name=name, radius=radius, axis=axis, constructionHistory=construction_history)[0]


def create_nurbs_cylinder(name='cylinder', radius=1.0, height=1.0, **kwargs):
    """
    Creates a new NURBS cylinder
    :param name: str
    :param radius: float
    :param height: float
    :return: str
    """

    axis = kwargs.get('axis', (0, 1, 0))
    construction_history = kwargs.get('construction_history', True)

    return maya.cmds.cylinder(
        name=name, ax=axis, ssw=0, esw=360, r=radius, hr=height, d=3,
        ut=0, tol=0.01, s=8, nsp=1, ch=construction_history)[0]


def create_nurbs_plane(name='plane', width=1.0, length=1.0, patches_u=1, patches_v=1, **kwargs):
    """
    Creates a new NURBS plane
    :param name: str
    :param width: int
    :param length: int
    :param patches_u: float
    :param patches_v: float
    :param kwargs:
    :return:
    """

    axis = kwargs.get('axis', (0, 1, 0))
    construction_history = kwargs.get('construction_history', True)

    return maya.cmds.nurbsPlane(
        name=name, axis=axis, width=width, lengthRatio=length / width, patchesU=patches_u,
        patchesV=patches_v, ch=construction_history)[0]


def convert_surface_to_bezier(surface, **kwargs):
    """
    Rebuilds given surface as a bezier surface
    :param surface: str
    :return:
    """

    replace_original = kwargs.get('replace_original', True)
    construction_history = kwargs.get('construction_history', True)
    spans_u = kwargs.get('spans_u', 4)
    spans_v = kwargs.get('spans_v', 4)
    degree_u = kwargs.get('degree_u', 3)
    degree_v = kwargs.get('degree_v', 3)

    return maya.cmds.rebuildSurface(
        surface, ch=construction_history, rpo=replace_original,
        su=spans_u, sv=spans_v, rt=7, du=degree_u, dv=degree_v)


def create_empty_mesh(mesh_name):
    """
    Creates a new empty mesh
    :param mesh_name:str
    :return: str
    """

    return maya.cmds.polyCreateFacet(
        name=mesh_name, ch=False, tx=1, s=1, p=[(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)])


def attach_transform_to_surface(transform, surface, u=None, v=None, constraint=False, attach_type=None):
    """
    Attaches a transform to given surface
    If no U an V values are given, the command will try to find the closest position on the surface
    :param transform: str, str, name of a transform to follicle to the surface
    :param surface: str, name of a surface to attach follicle to
    :param u: float, U value to attach to
    :param v: float, V value to attach to
    :param constraint: bool
    :param attach_type: bool
    :return: str, name of the follicle created
    """

    if attach_type is None:
        attach_type = 0

    # Follicle
    if attach_type == 0:
        return follicle_utils.follicle_to_surface(transform, surface, constraint=constraint)
    else:
        return rivet_utils.attach_to_surface(transform, surface, constraint=constraint)


def create_nurbs_surface_from_transforms(transforms, name, spans=-1, offset_axis='Y', offset_amount=1):
    """
    Creates a NURBS surface from a list of transforms
    Useful for creating a NURBS surface that follows a spine or tail
    :param transforms: list<str>, list of transforms
    :param name: str, name of the surface
    :param spans: int, number of spans to given to the final surface.
    If -1, the surface will have spans based on the number of transforms
    :param offset_axis: str, axis to offset the surface relative to the transform ('X', 'Y' or 'Z')
    :param offset_amount: int, amount the surface offsets from the transform
    :return: str, name of the NURBS surface
    """

    return geo_utils.transforms_to_nurbs_surface(
        transforms, name, spans=spans, offset_axis=offset_axis, offset_amount=offset_amount)


# =================================================================================================================
# CURVES
# =================================================================================================================

def node_is_curve(node_name):
    """
    Returns whether given node is a valid curve node
    :param node_name: str
    :return: bool
    """

    curve_shapes = get_curve_shapes(node_name)

    return bool(curve_shapes)


def get_curve_shapes(node_name):
    """
    Returns all shapes of the given curve
    :param node_name: str
    :return: list(str)
    """

    curve_shapes = None
    if maya.cmds.nodeType(node_name) == 'transform':
        curve_shapes = maya.cmds.listRelatives(node_name, c=True, s=True, f=True)
        if curve_shapes:
            if maya.cmds.nodeType(curve_shapes[0]) == 'nurbsCurve':
                curve_shapes = maya.cmds.listRelatives(node_name, c=True, s=True, f=True)
    elif maya.cmds.nodeType(node_name) == 'nurbsCurve':
        curve_shapes = maya.cmds.listRelatives(maya.cmds.listRelatives(node_name, p=True)[0], c=True, s=True)

    return curve_shapes


def get_curve_knots(curve_node_name):
    """
    Returns given curve knots
    :param curve_node_name: str
    :return: list(str)
    """

    curve_fn = curve_utils.get_curve_fn(curve=curve_node_name)
    curve_knots = curve_fn.knots()

    return [float(knot) for knot in curve_knots]


def get_curve_knots_positions(curve_node_name, world_space=False):
    """
    Returns given curve knot positions
    :param curve_node_name: str
    :param world_space: bool
    :return: list(tuple(float, float, float))
    """

    space = maya.api.OpenMaya.MSpace.kWorld if world_space else maya.api.OpenMaya.MSpace.kObject
    curve_fn = curve_utils.get_curve_fn(curve=curve_node_name)
    knots = get_curve_knots(curve_node_name)

    knots_positions = list()
    for u in knots:
        knot_position = curve_fn.getPointAtParam(u, space)
        knots_positions.append((knot_position.x, knot_position.y, knot_position.z))

    return knots_positions


def get_curve_degree(curve_node_name):
    """
    Returns given curve degree
    :param curve_node_name: str
    :return: int
    """

    return maya.cmds.getAttr('{}.degree'.format(curve_node_name))


def get_curve_spans(curve_node_name):
    """
    Returns given curve degree
    :param curve_node_name: str
    :return: int
    """

    return maya.cmds.getAttr('{}.spans'.format(curve_node_name))


def get_curve_form(curve_node_name):
    """
    Returns given curve form
    :param curve_node_name: str
    :return: int
    """

    return maya.cmds.getAttr('{}.f'.format(curve_node_name))


def get_curve_cvs(curve_node_name, world_space=False):
    """
    Returns given curve CVs
    :param curve_node_name: str
    :param world_space: bool
    :return: list
    """

    space = maya.api.OpenMaya.MSpace.kWorld if world_space else maya.api.OpenMaya.MSpace.kObject
    curve_fn = curve_utils.get_curve_fn(curve=curve_node_name)
    cv_array = curve_fn.cvPositions(space)
    cv_length = len(cv_array)

    return [(cv_array[i].x, cv_array[i].y, cv_array[i].z) for i in range(cv_length)]


def get_curve_cv_position_in_world_space(curve_node_name, cv_index):
    """
    Returns position of the given CV index in given curve node
    :param curve_node_name: str
    :param cv_index: int
    :return: list(float, float, float)
    """

    return maya.cmds.xform('{}.cv[{}]'.format(curve_node_name, cv_index), query=True, translation=True, worldSpace=True)


def get_curve_cv_position_in_object_space(curve_node_name, cv_index):
    """
    Returns object space position of the given CV index in given curve node
    :param curve_node_name: str
    :param cv_index: int
    :return: list(float, float, float)
    """

    return maya.cmds.xform('{}.cv[{}]'.format(
        curve_node_name, cv_index), query=True, translation=True, objectSpace=True)


def rebuild_curve(curve_node_name, spans, **kwargs):
    """
    Rebuilds curve with given parameters
    :param curve_node_name: str
    :param spans: int
    :param kwargs:
    :return:
    """

    construction_history = kwargs.get('construction_history', True)
    replace_original = kwargs.get('replace_original', False)
    keep_control_points = kwargs.get('keep_control_points', False)
    keep_end_points = kwargs.get('keep_end_points', True)
    keep_tangents = kwargs.get('keep_tangents', True)
    # Degree: 1: linear; 2: quadratic; 3: cubic; 5: quintic; 7: hepetic
    degree = kwargs.get('degree', 3)
    # Rebuild Type: 0: uniform; 1: reduce spans; 2: match knots; 3: remove multiple knots;
    # 4: curvature; 5: rebuild ends; 6: clean
    rebuild_type = kwargs.get('rebuild_type', 0)
    # End Knots: 0: uniform end knots; 1: multiple end knots
    end_knots = kwargs.get('end_knots', 0)
    # Keep range: 0: reparametrize the resulting curve from 0 to 1; 1: keep the original curve parametrization;
    # 2: reparametrize the result from 0 to number of spans
    keep_range = kwargs.get('keep_range', 1)

    return maya.cmds.rebuildCurve(
        curve_node_name, spans=spans, rpo=replace_original, rt=rebuild_type, end=end_knots, kr=keep_range,
        kcp=keep_control_points, kep=keep_end_points, kt=keep_tangents, d=degree, ch=construction_history)


def create_circle_curve(name, **kwargs):
    """
    Creates a new circle control
    :param name: str
    :param kwargs:
    :return: str
    """

    construction_history = kwargs.get('construction_history', True)
    normal = kwargs.get('normal', (1, 0, 0))

    return maya.cmds.circle(n=name, normal=normal, ch=construction_history)[0]


def create_curve(name, degree, cvs, knots, form, **kwargs):
    """
    Creates a new Nurbs curve
    :param name: str, name of the new curve
    :param degree: int
    :param cvs: list(tuple(float, float, float))
    :param knots: list
    :param form: int
    :return: str
    """

    is_2d = kwargs.pop('2d', False)
    rational = kwargs.pop('rational', True)

    num_cvs = len(cvs)
    num_knots = len(knots)

    cv_array = maya.api.OpenMaya.MPointArray(num_cvs, maya.api.OpenMaya.MPoint.kOrigin)
    knots_array = maya.api.OpenMaya.MDoubleArray(num_knots, 0)
    for i in range(num_cvs):
        cv_array[i] = maya.api.OpenMaya.MPoint(cvs[i][0], cvs[i][1], cvs[i][2], 1.0)
    for i in range(num_knots):
        knots_array[i] = knots[i]

    curve_fn = maya.api.OpenMaya.MFnNurbsCurve()
    curve_data = maya.api.OpenMaya.MObject()
    curve_obj = curve_fn.create(
        cv_array,
        knots,
        degree,
        form,
        is_2d,
        rational,
        curve_data
    )

    new_curve = maya.api.OpenMaya.MFnDependencyNode(curve_obj).setName(name)

    return new_curve

    # return maya.cmds.curve(n=name, d=degree, p=points, k=knots, per=periodic)


def create_curve_from_transforms(transforms, spans=None, description='from_transforms'):
    """
    Creates a curve from a list of transforms. Each transform will define a curve CV
    Useful when creating a curve from a joint chain (spines/tails)
    :param transforms: list<str>, list of tranfsorms to generate the curve from. Positions will be used to place CVs
    :param spans: int, number of spans the final curve should have
    :param description: str, description to given to the curve
    :return: str name of the new curve
    """

    return curve_utils.transforms_to_curve(transforms=transforms, spans=spans, description=description)


def create_wire(surface, curves, name='wire', **kwargs):
    """
    Creates a new wire that wires given surface/curve to given curves
    :param surface:str
    :param curves: list(str)
    :param name:str
    :param kwargs:
    :return: str, str
    """

    curves = helpers.force_list(curves)
    dropoff_distance = kwargs.get('dropoff_distance', [])
    group_with_base = kwargs.get('group_with_base', False)

    return maya.cmds.wire(surface, w=curves, n=name, dds=dropoff_distance, gw=group_with_base)


def find_deformer_by_type(geo_obj, deformer_type, **kwargs):
    """
    Given a object find a deformer with deformer_type in its history
    :param geo_obj: str, name of a mesh
    :param deformer_type: str, correspnds to the Maya deformer type (skinCluster, blendShape, etc)
    :return: list(str), names of deformers of type found in the history>
    """

    # Whether to return all the deformer found of the given type or just the first one
    return_all = kwargs.get('return_all', False)

    return deformer_utils.find_deformer_by_type(geo_obj, deformer_type=deformer_type, return_all=return_all)


# =================================================================================================================
# JOINTS
# =================================================================================================================

def create_joint(name, size=1.0, *args, **kwargs):
    """
    Creates a new joint
    :param name: str, name of the new joint
    :param size: float, size of the joint
    :return: str
    """

    pos = kwargs.pop('position', [0, 0, 0])

    return maya.cmds.joint(name=name, rad=size, p=pos)


def orient_joint(joint, **kwargs):
    """
    Orients given joint
    :param joint: str
    :return:
    """

    # Aim At: 0: aim at world X; 1: aim at world Y; 2: aim at world Z; 3: aim at immediate child;
    # 4: aim at immediate parent; 5: aim at local parent (aiming at the parent and the reverseing the direction)
    aim_at = kwargs.get('aim_at', 3)
    # Aim Up At: 0: parent rotation:; 1: child position; 2: parent position; 3: triangle plane
    aim_up_at = kwargs.get('aim_up_at', 0)

    orient = joint_utils.OrientJointAttributes(joint)
    orient.set_default_values()
    orient = joint_utils.OrientJoint(joint)
    orient.set_aim_at(aim_at)
    orient.set_aim_up_at(aim_up_at)

    return orient.run()


def mirror_joint(joint, mirror_plane='YZ', mirror_behavior=True, search_replace=None):
    """
    Mirrors given joint and its hierarchy
    :param joint: str
    :param mirror_plane: str
    :param mirror_behavior: bool
    :param search_replace: list(str)
    :return: list(str)
    """

    # TODO: Add option to cleanup all nodes that are not joints after mirrror (such as constraints)

    if mirror_plane == 'YZ':
        return maya.cmds.mirrorJoint(
            joint, mirrorYZ=True, mirrorBehavior=mirror_behavior, searchReplace=search_replace)
    elif mirror_plane == 'XY':
        return maya.cmds.mirrorJoint(
            joint, mirrorXY=True, mirrorBehavior=mirror_behavior, searchReplace=search_replace)
    else:
        return maya.cmds.mirrorJoint(
            joint, mirrorXZ=True, mirrorBehavior=mirror_behavior, searchReplace=search_replace)


def orient_joints(joints_to_orient=None, **kwargs):
    """
    Orients joints
    :param joints_to_orient: list(str) or None
    :param kwargs:
    :return:
    """

    force_orient_attributes = kwargs.get('force_orient_attributes', False)

    return joint_utils.OrientJointAttributes.orient_with_attributes(
        objects_to_orient=joints_to_orient, force_orient_attributes=force_orient_attributes)


def zero_orient_joint(joints_to_zero_orient):
    """
    Zeroes the orientation of the given joints
    :param joints_to_zero_orient: list(str)
    """

    return joint_utils.OrientJointAttributes.zero_orient_joint(joints_to_zero_orient)


def start_joint_tool():
    """
    Starts the DCC tool used to create new joints/bones
    """

    return joint_utils.start_joint_tool()


def insert_joints(count, root_joint=None):
    """
    Inserts the given number of joints between the root joint and its direct child
    """

    return joint_utils.insert_joints(joint_count=count)


def set_joint_local_rotation_axis_visibility(flag, joints_to_apply=None):
    """
    Sets the visibility of selected joints local rotation axis
    :param flag: bool
    :param joints_to_apply: list(str) or None
    :return: bool
    """

    return joint_utils.set_joint_local_rotation_axis_visibility(joints=joints_to_apply, bool_value=flag)


def get_joint_display_size():
    """
    Returns current DCC joint display size
    :return: float
    """

    return maya.cmds.jointDisplayScale(query=True, absolute=True)


def set_joint_display_size(value):
    """
    Returns current DCC joint display size
    :param value: float
    """

    if value <= 0.0:
        return False

    return maya.cmds.jointDisplayScale(value, absolute=True)


def toggle_xray_joints():
    """
    Toggles XRay joints functionality (joints are rendered in front of the geometry)
    """

    current_panel = maya.cmds.getPanel(withFocus=True)
    if maya.cmds.modelEditor(current_panel, query=True, jointXray=True):
        maya.cmds.modelEditor(current_panel, edit=True, jointXray=False)
    else:
        maya.cmds.modelEditor(current_panel, edit=True, jointXray=True)


def zero_scale_joint(jnt):
    """
    Sets the given scale to zero and compensate the change by modifying the joint translation and rotation
    :param jnt: str
    """

    return maya.cmds.joint(jnt, edit=True, zeroScaleOrient=True)


def set_joint_orient(jnt, orient_axis, secondary_orient_axis=None, **kwargs):
    """
    Sets the joint orientation and scale orientation so that the axis indicated by the first letter in the
    argument will be aligned with the vector from this joint to its first child joint. For example, if the
    argument is "xyz", the x-axis will point towards the child joint. The alignment of the remaining two
    joint orient axes are dependent on whether the -sao/-secondaryAxisOrient flag is used.
    If the secondary_orient_axis flag is used, see the documentation for that flag for how the remaining
    axes are aligned. In the absence of a user specification for the secondary axis orientation, the rotation
    axis indicated by the last letter in the argument will be aligned with the vector perpendicular to first
    axis and the vector from this joint to its parent joint. The remaining axis is aligned according the right
    hand rule. If the argument is "none", the joint orientation will be set to zero and its effect to the
    hierarchy below will be offset by modifying the scale orientation. The flag will be ignored if: A. the
    joint has non-zero rotations when the argument is not "none". B. the joint does not have child joint, or
    the distance to the child joint is zero when the argument is not "none". C. either flag -o or -so is set.
    :param jnt: str, can be one of the following strings: xyz, yzx, zxy, zyx, yxz, xzy, none
    :param orient_axis: str, can be one of the following strings: xyz, yzx, zxy, zyx, yxz, xzy, none
    :param secondary_orient_axis: str, one of the following strings: xup, xdown, yup, ydown, zup, zdown, none. This
        flag is used in conjunction with the -oj/orientJoint flag. It specifies the scene axis that the second
        axis should align with. For example, a flag combination of "-oj yzx -sao yup" would result in the y-axis
         pointing down the bone, the z-axis oriented with the scene's positive y-axis, and the x-axis oriented
         according to the right hand rule.
     :param:
    :return:
    """

    zero_scale_joint = kwargs.get('zero_scale_joint', False)

    return maya.cmds.joint(jnt, edit=True, zso=zero_scale_joint, oj=orient_axis, sao=secondary_orient_axis)


def attach_joints(source_chain, target_chain, **kwargs):
    """
    Attaches a chain of joints to a matching chain
    :param source_chain: list(str)
    :param target_chain: list(str)
    """

    # 0 = Constraint; 1 = Matrix
    attach_type = kwargs.get('attach_type', 0)
    create_switch = kwargs.get('create_switch', True)
    switch_attribute_name = kwargs.get('switch_attribute_name', 'switch')

    attach = joint_utils.AttachJoints(
        source_joints=source_chain, target_joints=target_chain, create_switch=create_switch)
    attach.set_attach_type(attach_type)
    if switch_attribute_name:
        attach.set_switch_attribute_name(switch_attribute_name)
    attach.create()


def get_side_labelling(node):
    """
    Returns side labelling of the given node
    :param node: str
    :return: list(str)
    """

    if not attribute_exists(node, 'side'):
        return 'None'

    side_index = get_attribute_value(node, 'side')

    return maya_constants.SIDE_LABELS[side_index]


def set_side_labelling(node, side_label):
    """
    Sets side labelling of the given node
    :param node: str
    :param side_label: str
    """

    if not side_label or side_label not in maya_constants.SIDE_LABELS or not attribute_exists(node, 'side'):
        return False

    side_index = maya_constants.SIDE_LABELS.index(side_label)

    return set_attribute_value(node, 'side', side_index)


def get_type_labelling(node):
    """
    Returns type labelling of the given node
    :param node: str
    :return: list(str)
    """

    if not attribute_exists(node, 'type'):
        return 'None'

    type_index = get_attribute_value(node, 'type')

    return maya_constants.TYPE_LABELS[type_index]


def set_type_labelling(node, type_label):
    """
    Sets type labelling of the given node
    :param node: str
    :param type_label: str
    """

    if not type_label or type_label not in maya_constants.TYPE_LABELS or not attribute_exists(node, 'type'):
        return False

    type_index = maya_constants.TYPE_LABELS.index(type_label)

    return set_attribute_value(node, 'type', type_index)


def get_other_type_labelling(node):
    """
    Returns other type labelling of the given node
    :param node: str
    :return: list(str)
    """

    if not get_type_labelling(node) == 'Other':
        return ''

    if not attribute_exists(node, 'otherType'):
        return ''

    return get_attribute_value(node, 'otherType')


def set_other_type_labelling(node, other_type_label):
    """
    Sets other type labelling of the given node
    :param node: str
    :param other_type_label: str
    """

    if not get_type_labelling(node) == 'Other' or not attribute_exists(node, 'otherType'):
        return False

    return set_attribute_value(node, 'otherType', str(other_type_label))


def get_draw_label_labelling(node):
    """
    Returns draw label labelling of the given node
    :param node: str
    :return: list(str)
    """

    if not attribute_exists(node, 'drawLabel'):
        return False

    return get_attribute_value(node, 'drawLabel')


def set_draw_label_labelling(node, draw_type_label):
    """
    Sets draw label labelling of the given node
    :param node: str
    :param draw_type_label: str
    """

    if not attribute_exists(node, 'drawLabel'):
        return False

    return set_attribute_value(node, 'drawLabel', bool(draw_type_label))


def get_joint_radius(node):
    """
    Sets given joint radius
    :param node: str
    :return: float
    """

    return maya.cmds.getAttr('{}.radius'.format(node))


def set_joint_radius(node, radius_value):
    """
    Sets given joint radius
    :param node: str
    :param radius_value: float
    """

    return maya.cmds.setAttr('{}.radius'.format(node), radius_value)


# =================================================================================================================
# SKIN
# =================================================================================================================

def create_skin(mesh, influences, **kwargs):
    """
    Creates a new skin deformer node with given influences and apply it to given mesh
    :param mesh: str
    :param influences: list(str)
    :return: str
    """

    name = kwargs.get('name', 'skin')
    only_selected_influences = kwargs.get('only_selected_influences', True)

    return maya.cmds.skinCluster(influences, mesh, tsb=only_selected_influences, n=name)[0]


def get_skin_weights(skin_node, vertices_ids=None):
    """
    Get the skin weights of the given skin deformer node
    :param skin_node: str, name of a skin deformer node
    :param vertices_ids:
    :return: dict(int, list(float)), returns a dictionary where the key is the influence id and the
    value is the list of weights of the influence
    """

    return skin_utils.get_skin_weights(skin_node, vertices_ids=vertices_ids)


def get_skin_blend_weights(skin_deformer):
    """
    Returns the blendWeight values on the given skin node
    :param skin_deformer: str, name of a skin deformer node
    :return: list(float), blend weight values corresponding to point order
    """

    return skin_utils.get_skin_blend_weights(skin_deformer)


def set_skin_blend_weights(skin_deformer, weights):
    """
    Sets the blendWeights on the skinCluster given a list of weights
    :param skin_deformer: str, name of a skinCluster deformer
    :param weights: list<float>, list of weight values corresponding to point order
    """

    return skin_utils.set_skin_blend_weights(skin_deformer, weights)


def get_skin_influences(skin_deformer, short_name=True, return_dict=False):
    """
    Returns the influences connected to the skin cluster
    Returns a dictionary with the keys being the name of the influences being the value at the
    key index where the influence connects to the skinCluster
    :param skin_deformer: str, name of a skinCluster
    :param short_name: bool, Whether to return full name of the influence or not
    :param return_dict: bool, Whether to return a dictionary or not
    :return: variant(dict, list)
    """

    return skin_utils.get_skin_influences(skin_deformer, short_name=short_name, return_dict=return_dict)


def apply_skin_influences_from_data(skin_deformer, influences, influence_dict):
    """
    Updates skin cluster with given influences data
    :param skin_deformer: str
    :param influences: list(str), list of influence names
    :param influence_dict: dict(str, float), list that contains a map between influences and its weights
    :return:
    """

    influence_index = 0
    influence_index_dict = get_skin_influences(skin_deformer, return_dict=True)
    #         progress_bar = progressbar.ProgressBar('Import Skin', len(influence_dict.keys()))
    for influence in influences:
        orig_influence = influence
        if influence.count('|') > 1:
            split_influence = influence.split('|')
            if len(split_influence) > 1:
                influence = split_influence[-1]
        #             progress_bar.status('Importing skin mesh: {}, influence: {}'.format(short_name, influence))
        if 'weights' not in influence_dict[orig_influence]:
            logger.warning('Weights missing for influence: {}. Skipping it ...'.format(influence))
            continue
        weights = influence_dict[orig_influence]['weights']
        if influence not in influence_index_dict:
            continue
        index = influence_index_dict[influence]

        # attr = '{}.weightList[*].weights[{}]'.format(skin_cluster, index)
        # NOTE: his was not faster, zipping zero weights is much faster than setting all the weights
        # maya.cmds.setAttr(attr, *weights )

        for i in range(len(weights)):
            weight = float(weights[i])
            if weight == 0 or weight < 0.0001:
                continue
            attr = 'weightList[{}].weights[{}]'.format(i, index)
            set_attribute_value(skin_deformer, attr, weight)
        #             progress_bar.inc()

        #             if progress_bar.break_signaled():
        #                 break
        influence_index += 1
    #         progress_bar.end()

    set_skin_normalize_weights_mode(skin_deformer, 1)  # interactive normalization
    set_skin_force_normalize_weights(skin_deformer, True)


def get_skin_influence_at_index(index, skin_deformer):
    """
    Returns which influence connect to the skin node at the given index
    :param index: int, index of an influence
    :param skin_deformer: str, name of the skin node to check the index
    :return: str, name of the influence at the given index
    """

    return skin_utils.get_skin_influence_at_index(index, skin_deformer)


def get_skin_envelope(geo_obj):
    """
    Returns envelope value of the skin node in the given geometry object
    :param geo_obj: str, name of the geometry
    :return: float
    """

    return skin_utils.get_skin_envelope(geo_obj)


def set_skin_envelope(geo_obj, envelope_value):
    """
    Sets the envelope value of teh skin node in the given geometry object
    :param geo_obj: str, name of the geometry
    :param envelope_value: float. envelope value
    """

    return skin_utils.set_skin_envelope(geo_obj, envelope_value)


def clear_skin_weights(skin_node):
    """
    Sets all the weights on the given skinCluster to zero
    :param skin_node: str, name of a skinCluster deformer
    """

    return skin_utils.set_skin_weights_to_zero(skin_node)


def set_skin_normalize_weights_mode(skin_node, index_mode):
    """
    Sets the skin normalize mode used by the given skin deformer node
    :param skin_node: str
    :param index_mode: int
    """

    maya.cmds.skinCluster(skin_node, edit=True, normalizeWeights=index_mode)


def set_skin_force_normalize_weights(skin_node, flag):
    """
    Sets whether the skin node weights are forced to be normalized
    :param skin_node: str
    :param flag: bool
    """

    maya.cmds.skinCluster(skin_node, edit=True, forceNormalizeWeights=flag)


def skin_mesh_from_mesh(source_mesh, target_mesh, **kwargs):
    """
    Skins a mesh based on the skinning of another mesh
    Source mesh must be skinned and the target mesh will be skinned with the joints in the source mesh
    The skinning from the source mesh will be projected onto the target mesh
    :param source_mesh: str, name of a mesh
    :param target_mesh: str, name of a mesh
    """

    exclude_joints = kwargs.get('exclude_joints', None)
    include_joints = kwargs.get('include_joints', None)
    uv_space = kwargs.get('uv_space', False)

    return skin_utils.skin_mesh_from_mesh(
        source_mesh, target_mesh, exclude_joints=exclude_joints, include_joints=include_joints, uv_space=uv_space)


# =================================================================================================================
# SELECTION GROUPS
# =================================================================================================================

def get_selection_groups(name=None):
    """
    Returns all selection groups (sets) in current DCC scene
    :param name: str or None
    :return: list(str)
    """

    if name:
        return maya.cmds.ls(name, type='objectSet')
    else:
        return maya.cmds.ls(type='objectSet')


def node_is_selection_group(node):
    """
    Returns whether given node is a selection group (set)
    :param node: str
    :return: bool
    """

    return node_type(node) == 'objectSet'


def create_selection_group(name, empty=False):
    """
    Creates a new DCC selection group
    :param name: str
    :param empty: bool
    :return: str
    """

    return maya.cmds.sets(name=name, empty=empty)


def add_node_to_selection_group(node, selection_group_name, force=True):
    """
    Adds given node to selection group
    :param node: str
    :param selection_group_name: str
    :param force: bool
    :return: str
    """

    if force:
        return maya.cmds.sets(node, edit=True, forceElement=selection_group_name)
    else:
        return maya.cmds.sets(node, edit=True, addElement=selection_group_name)


# =================================================================================================================
# ATTRIBUTES
# =================================================================================================================

def get_valid_attribute_types():
    """
    Returns a list of valid attribute types in current DCC
    :return: list(str)
    """

    return ["int", "long", "enum", "bool", "string", "float", "short", "double", "doubleAngle", "doubleLinear"]


def get_valid_blendable_attribute_types():
    """
    Returns a list of valid blendable attribute types in current DCC
    :return: list(str)
    """

    return ["int", "long", "float", "short", "double", "doubleAngle", "doubleLinear"]


def attribute_default_value(node, attribute_name):
    """
    Returns default value of the attribute in the given node
    :param node: str
    :param attribute_name: str
    :return: object
    """

    try:
        return maya.cmds.attributeQuery(attribute_name, node=node, listDefault=True)[0]
    except Exception:
        try:
            return maya.cmds.addAttr('{}.{}'.format(node, attribute_name), query=True, dv=True)
        except Exception:
            return None


def list_attributes(node, **kwargs):
    """
    Returns list of attributes of given node
    :param node: str
    :return: list<str>
    """

    return maya.cmds.listAttr(node, **kwargs)


def list_user_attributes(node):
    """
    Returns list of user defined attributes
    :param node: str
    :return: list<str>
    """

    return maya.cmds.listAttr(node, userDefined=True) or list()


def add_bool_attribute(node, attribute_name, default_value=False, **kwargs):
    """
    Adds a new boolean attribute into the given node
    :param node: str
    :param attribute_name: str
    :param default_value: bool
    :return:
    """

    lock = kwargs.pop('lock', False)
    channel_box_display = kwargs.pop('channel_box_display', True)
    keyable = kwargs.pop('keyable', True)

    maya.cmds.addAttr(node, ln=attribute_name, at='bool', dv=default_value, **kwargs)
    if not node_is_referenced(node):
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, lock=lock, channelBox=channel_box_display)
    maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, keyable=keyable)


def add_integer_attribute(node, attribute_name, default_value=0, **kwargs):
    """
    Adds a new float attribute into the given node
    :param node: str
    :param attribute_name: str
    :param default_value: float
    :return:
    """

    lock = kwargs.pop('lock', False)
    channel_box_display = kwargs.get('channel_box_display', True)
    keyable = kwargs.pop('keyable', True)
    min_value = kwargs.pop('min_value', -sys.maxsize - 1)
    max_value = kwargs.pop('max_value', sys.maxsize + 1)

    maya.cmds.addAttr(
        node, ln=attribute_name, at='long', dv=default_value, min=float(min_value), max=float(max_value), **kwargs)
    maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, lock=lock, channelBox=channel_box_display)
    maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, keyable=keyable)


def add_float_attribute(node, attribute_name, default_value=0.0, **kwargs):
    """
    Adds a new float attribute into the given node
    :param node: str
    :param attribute_name: str
    :param default_value: float
    :return:
    """

    lock = kwargs.pop('lock', False)
    channel_box_display = kwargs.get('channel_box_display', True)
    keyable = kwargs.pop('keyable', True)
    min_value = kwargs.pop('min_value', float(-sys.maxsize - 1))
    max_value = kwargs.pop('max_value', float(sys.maxsize + 1))

    maya.cmds.addAttr(node, ln=attribute_name, at='float', dv=default_value, min=min_value, max=max_value, **kwargs)
    maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, lock=lock, channelBox=channel_box_display)
    maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, keyable=keyable)


def add_double_attribute(node, attribute_name, default_value=0.0, **kwargs):
    """
    Adds a new boolean float into the given node
    :param node: str
    :param attribute_name: str
    :param default_value: float
    :return:
    """

    lock = kwargs.pop('lock', False)
    channel_box_display = kwargs.get('channel_box_display', True)
    keyable = kwargs.pop('keyable', True)
    min_value = kwargs.pop('min_value', float(-sys.maxsize - 1))
    max_value = kwargs.pop('max_value', float(sys.maxsize + 1))

    maya.cmds.addAttr(
        node, ln=attribute_name, at='double', dv=default_value, min=min_value, max=max_value, **kwargs)
    maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, lock=lock, channelBox=channel_box_display)
    maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, keyable=keyable)


def add_string_attribute(node, attribute_name, default_value='', **kwargs):
    """
    Adds a new string attribute into the given node
    :param node: str
    :param attribute_name: str
    :param default_value: str
    """

    lock = kwargs.pop('lock', False)
    channel_box_display = kwargs.get('channel_box_display', True)
    keyable = kwargs.pop('keyable', True)

    maya.cmds.addAttr(node, ln=attribute_name, dt='string', **kwargs)
    maya.cmds.setAttr('{}.{}'.format(node, attribute_name), default_value, type='string')
    if not node_is_referenced(node):
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, lock=lock)
    maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, channelBox=channel_box_display)
    maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, keyable=keyable)


def add_string_array_attribute(node, attribute_name, **kwargs):
    """
    Adds a new string array attribute into the given node
    :param node: str
    :param attribute_name: str
    :param keyable: bool
    """

    lock = kwargs.get('lock', False)
    channel_box_display = kwargs.get('channel_box_display', True)
    keyable = kwargs.pop('keyable', True)

    maya.cmds.addAttr(node, ln=attribute_name, dt='stringArray', **kwargs)
    maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, lock=lock, channelBox=channel_box_display)
    maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, keyable=keyable)


def add_title_attribute(node, attribute_name, **kwargs):
    """
    Adds a new title attribute into the given node
    :param node: str
    :param attribute_name: str
    :param kwargs:
    :return:
    """

    return attribute.create_title(node, attribute_name)


def add_message_attribute(node, attribute_name, **kwargs):
    """
    Adds a new message attribute into the given node
    :param node: str
    :param attribute_name: str
    """

    lock = kwargs.get('lock', False)
    channel_box_display = kwargs.get('channel_box_display', True)
    keyable = kwargs.pop('keyable', True)

    maya.cmds.addAttr(node, ln=attribute_name, at='message', **kwargs)
    maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, lock=lock, channelBox=channel_box_display)
    maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, keyable=keyable)


def add_enum_attribute(node, attribute_name, value, **kwargs):
    """
    Adds a new enum attribute into the given node
    :param node: str
    :param attribute_name: str
    :param value: list(str)
    :param kwargs:
    :return:
    """

    lock = kwargs.get('lock', False)
    channel_box_display = kwargs.get('channel_box_display', True)
    keyable = kwargs.pop('keyable', True)
    default_value = kwargs.pop('default_value', 0)

    maya.cmds.addAttr(node, ln=attribute_name, attributeType='enum', enumName=value, dv=default_value, **kwargs)
    maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, lock=lock, channelBox=channel_box_display)
    maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, keyable=keyable)


def get_enum_attribute_values(node, attribute_name):
    """
    Return list of enum attribute values in the given attribute
    :param node: str
    :param attribute_name: str
    :return: list(str)
    """

    return maya.cmds.addAttr('{}.{}'.format(node, attribute_name), query=True, enumName=True)


def set_enum_attribute_value(node, attribute_name, value):
    """
    Return list of enum attribute values in the given attribute
    :param node: str
    :param attribute_name: str
    :param value: str
    """

    return maya.cmds.addAttr('{}.{}'.format(node, attribute_name), edit=True, enumName=value)


def attribute_query(node, attribute_name, **kwargs):
    """
    Returns attribute qyer
    :param node: str
    :param attribute_name: str
    :param kwargs:
    :return:
    """

    return maya.cmds.attributeQuery(attribute_name, node=node, **kwargs)[0]


def attribute_exists(node, attribute_name):
    """
    Returns whether given attribute exists in given node
    :param node: str
    :param attribute_name: str
    :return: bool
    """

    return maya.cmds.attributeQuery(attribute_name, node=node, exists=True)


def is_attribute_locked(node, attribute_name):
    """
    Returns whether given attribute is locked or not
    :param node: str
    :param attribute_name: str
    :return: bool
    """

    return maya.cmds.getAttr('{}.{}'.format(node, attribute_name), lock=True)


def is_attribute_connected(node, attribute_name):
    """
    Returns whether given attribute is connected or not
    :param node: str
    :param attribute_name: str
    :return: bool
    """

    return attribute.is_connected('{}.{}'.format(node, attribute_name))


def get_minimum_attribute_value_exists(node, attribute_name):
    """
    Returns whether minimum value for given attribute is defined
    :param node: str
    :param attribute_name: str
    :return: bool
    """

    return maya.cmds.attributeQuery(attribute_name, node=node, minExists=True)


def get_maximum_attribute_value_exists(node, attribute_name):
    """
    Returns whether maximum value for given attribute is defined
    :param node: str
    :param attribute_name: str
    :return: bool
    """

    return maya.cmds.attributeQuery(attribute_name, node=node, maxExists=True)


def get_maximum_integer_attribute_value(node, attribute_name):
    """
    Returns the maximum value that a specific integer attribute has set
    :param node: str
    :param attribute_name: str
    :return: float
    """

    return maya.cmds.attributeQuery(attribute_name, max=True, node=node)[0]


def set_maximum_integer_attribute_value(node, attribute_name, max_value):
    """
    Sets the maximum value that a specific integer attribute has set
    :param node: str
    :param attribute_name: str
    :param max_value: float
    """

    return maya.cmds.addAttr('{}.{}'.format(node, attribute_name), edit=True, maxValue=max_value, hasMaxValue=True)


def get_maximum_float_attribute_value(node, attribute_name):
    """
    Returns the maximum value that a specific float attribute has set
    :param node: str
    :param attribute_name: str
    :return: float
    """

    return maya.cmds.attributeQuery(attribute_name, max=True, node=node)[0]


def set_maximum_float_attribute_value(node, attribute_name, max_value):
    """
    Sets the maximum value that a specific float attribute has set
    :param node: str
    :param attribute_name: str
    :param max_value: float
    """

    return maya.cmds.addAttr('{}.{}'.format(node, attribute_name), edit=True, maxValue=max_value, hasMaxValue=True)


def get_minimum_integer_attribute_value(node, attribute_name):
    """
    Returns the minimum value that a specific integer attribute has set
    :param node: str
    :param attribute_name: str
    :return: float
    """

    return maya.cmds.attributeQuery(attribute_name, min=True, node=node)[0]


def set_minimum_integer_attribute_value(node, attribute_name, min_value):
    """
    Sets the minimum value that a specific integer attribute has set
    :param node: str
    :param attribute_name: str
    :param min_value: float
    """

    return maya.cmds.addAttr('{}.{}'.format(node, attribute_name), edit=True, minValue=min_value, hasMinValue=True)


def get_minimum_float_attribute_value(node, attribute_name):
    """
    Returns the minimum value that a specific float attribute has set
    :param node: str
    :param attribute_name: str
    :return: float
    """

    return maya.cmds.attributeQuery(attribute_name, min=True, node=node)[0]


def set_minimum_float_attribute_value(node, attribute_name, min_value):
    """
    Sets the minimum value that a specific float attribute has set
    :param node: str
    :param attribute_name: str
    :param min_value: float
    """

    return maya.cmds.addAttr('{}.{}'.format(node, attribute_name), edit=True, minValue=min_value, hasMinValue=True)


def show_attribute(node, attribute_name):
    """
    Shows attribute in DCC UI
    :param node: str
    :param attribute_name: str
    """

    return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), channelBox=True)


def hide_attribute(node, attribute_name):
    """
    Hides attribute in DCC UI
    :param node: str
    :param attribute_name: str
    """

    maya.cmds.setAttr('{}.{}'.format(node, attribute_name), keyable=False)
    return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), channelBox=False)


def hide_attributes(node, attributes_list):
    """
    Hides given attributes in DCC UI
    :param node: str
    :param attributes_list: list(str)
    """

    return attribute.hide_attributes(node, attributes_list)


def lock_attributes(node, attributes_list, **kwargs):
    """
    Locks given attributes in DCC UI
    :param node: str
    :param attributes_list: list(str)
    :param kwargs:
    """

    hide = kwargs.get('hide', False)

    return attribute.lock_attributes(node, attributes_list, hide=hide)


def keyable_attribute(node, attribute_name):
    """
    Makes given attribute keyable
    :param node: str
    :param attribute_name: str
    """

    return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), keyable=True)


def unkeyable_attribute(node, attribute_name):
    """
    Makes given attribute unkeyable
    :param node: str
    :param attribute_name: str
    """

    return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), keyable=False)


def lock_attribute(node, attribute_name):
    """
    Locks given attribute in given node
    :param node: str
    :param attribute_name: str
    """

    return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), lock=True)


def unlock_attribute(node, attribute_name):
    """
    Locks given attribute in given node
    :param node: str
    :param attribute_name: str
    """

    return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), lock=False)


def hide_translate_attributes(node):
    """
    Hides all translate transform attributes of the given node
    :param node: str
    """

    return attribute.hide_translate(node)


def lock_translate_attributes(node):
    """
    Locks all translate transform attributes of the given node
    :param node: str
    """

    return attribute.lock_translate_attributes(node, hide=False)


def unlock_translate_attributes(node):
    """
    Unlocks all translate transform attributes of the given node
    :param node: str
    """

    return attribute.unlock_translate_attributes(node)


def hide_rotate_attributes(node):
    """
    Hides all rotate transform attributes of the given node
    :param node: str
    """

    return attribute.hide_rotate(node)


def lock_rotate_attributes(node):
    """
    Locks all rotate transform attributes of the given node
    :param node: str
    """

    return attribute.lock_rotate_attributes(node, hide=False)


def unlock_rotate_attributes(node):
    """
    Unlocks all rotate transform attributes of the given node
    :param node: str
    """

    return attribute.unlock_rotate_attributes(node)


def hide_scale_attributes(node):
    """
    Hides all scale transform attributes of the given node
    :param node: str
    """

    return attribute.hide_scale(node)


def lock_scale_attributes(node):
    """
    Locks all scale transform attributes of the given node
    :param node: str
    """

    return attribute.lock_scale_attributes(node, hide=False)


def unlock_scale_attributes(node):
    """
    Unlocks all scale transform attributes of the given node
    :param node: str
    """

    return attribute.unlock_scale_attributes(node)


def hide_visibility_attribute(node):
    """
    Hides visibility attribute of the given node
    :param node: str
    """

    return attribute.hide_visibility(node)


def lock_visibility_attribute(node):
    """
    Locks visibility attribute of the given node
    :param node: str
    """

    return attribute.lock_attributes(node, ['visibility'], hide=False)


def unlock_visibility_attribute(node):
    """
    Unlocks visibility attribute of the given node
    :param node: str
    """

    return attribute.unlock_attributes(node, ['visibility'])


def hide_scale_and_visibility_attributes(node):
    """
    Hides scale and visibility attributes of the given node
    :param node: str
    """

    hide_scale_attributes(node)
    hide_visibility_attribute(node)


def lock_scale_and_visibility_attributes(node):
    """
    Locks scale and visibility attributes of the given node
    :param node: str
    """

    lock_scale_attributes(node)
    lock_visibility_attribute(node)


def hide_keyable_attributes(node, **kwargs):
    """
    Hides all node attributes that are keyable
    :param node: str
    """

    skip_visibility = kwargs.get('skip_visibility')

    return attribute.hide_keyable_attributes(node, skip_visibility=skip_visibility)


def lock_keyable_attributes(node, **kwargs):
    """
    Locks all node attributes that are keyable
    :param node: str
    """

    return attribute.lock_keyable_attributes(node, hide=False)


def get_attribute_value(node, attribute_name):
    """
    Returns the value of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :return: variant
    """

    return attribute.attribute(obj=node, attr=attribute_name)


def get_attribute_type(node, attribute_name):
    """
    Returns the type of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :return: variant
    """

    return maya.cmds.getAttr('{}.{}'.format(node, attribute_name), type=True)


def set_attribute_by_type(node, attribute_name, attribute_value, attribute_type):
    """
    Sets the value of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :param attribute_value: variant
    :param attribute_type: str
    """

    if attribute_type == 'string':
        return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), attribute_value, type=attribute_type)
    else:
        return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), attribute_value)


def set_boolean_attribute_value(node, attribute_name, attribute_value):
    """
    Sets the boolean value of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :param attribute_value: int
    :return:
    """

    return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), bool(attribute_value))


def set_numeric_attribute_value(node, attribute_name, attribute_value, clamp=False):
    """
    Sets the integer value of the given attribute in the given node
   :param node: str
    :param attribute_name: str
    :param attribute_value: int
    :param clamp: bool
    :return:
    """

    return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), attribute_value, clamp=clamp)


def set_integer_attribute_value(node, attribute_name, attribute_value, clamp=False):
    """
    Sets the integer value of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :param attribute_value: int
    :param clamp: bool
    :return:
    """

    return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), int(attribute_value), clamp=clamp)


def set_float_attribute_value(node, attribute_name, attribute_value, clamp=False):
    """
    Sets the integer value of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :param attribute_value: int
    :param clamp: bool
    :return:
    """

    return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), float(attribute_value), clamp=clamp)


def set_string_attribute_value(node, attribute_name, attribute_value):
    """
    Sets the string value of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :param attribute_value: str
    """

    return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), str(attribute_value), type='string')


def set_float_vector3_attribute_value(node, attribute_name, attribute_value):
    """
    Sets the vector3 value of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :param attribute_value: str
    """

    return maya.cmds.setAttr(
        '{}.{}'.format(node, attribute_name),
        float(attribute_value[0]), float(attribute_value[1]), float(attribute_value[2]), type='double3')


def set_attribute_value(node, attribute_name, attribute_value, **kwargs):
    """
    Sets attribute to given node
    :param node:
    :param attribute_name:
    :param attribute_value:
    :param kwargs:
    :return:
    """

    if type(attribute_value) is bool:
        set_boolean_attribute_value(node=node, attribute_name=attribute_name, attribute_value=attribute_value)
    elif type(attribute_value) is int:
        set_integer_attribute_value(
            node=node, attribute_name=attribute_name, attribute_value=attribute_value, **kwargs)
    elif type(attribute_value) is float:
        set_float_attribute_value(
            node=node, attribute_name=attribute_name, attribute_value=attribute_value, **kwargs)
    elif helpers.is_string(attribute_value):
        set_string_attribute_value(node=node, attribute_name=attribute_name, attribute_value=attribute_value)
    elif type(attribute_value) in [list, tuple]:
        if len(attribute_value) == 3:
            set_float_vector3_attribute_value(
                node=node, attribute_name=attribute_name, attribute_value=attribute_value)
        else:
            raise NotImplementedError(
                'Vector Type of length: {} is not supported yet!'.format(type(len(attribute_value))))
    else:
        raise NotImplementedError('Type {} is not supported yet: {}!'.format(type(attribute_value), attribute_name))


def reset_transform_attributes(node):
    """
    Reset all transform attributes of the given node
    :param node: str
    """

    for axis in 'xyz':
        for xform in 'trs':
            xform_attr = '{}{}'.format(xform, axis)
            if xform == 's':
                set_attribute_value(node, xform_attr, 1.0)
            else:
                set_attribute_value(node, xform_attr, 0.0)

    for shear_attr in ['shearXY', 'shearXZ', 'shearYZ']:
        set_attribute_value(node, shear_attr, 0.0)


def delete_attribute(node, attribute_name):
    """
    Deletes given attribute of given node
    :param node: str
    :param attribute_name: str
    """

    return maya.cmds.deleteAttr(n=node, at=attribute_name)


def delete_multi_attribute(node, attribute_name, attribute_index):
    """
    Deletes given multi attribute of given node
    :param node: str
    :param attribute_name:str
    :param attribute_index: int or str
    """

    return maya.cmds.removeMultiInstance('{}.{}[{}]'.format(node, attribute_name, attribute_index))


def delete_user_defined_attributes(node):
    """
    Removes all attributes in the given node that have been created by a user
    :param node: str
    """

    return attribute.remove_user_defined_attributes(node)


def connect_attribute(source_node, source_attribute, target_node, target_attribute, force=False):
    """
    Connects source attribute to given target attribute
    :param source_node: str
    :param source_attribute: str
    :param target_node: str
    :param target_attribute: str
    :param force: bool
    """

    return maya.cmds.connectAttr(
        '{}.{}'.format(source_node, source_attribute), '{}.{}'.format(target_node, target_attribute), force=force)


def disconnect_attribute(node, attribute_name):
    """
    Disconnects source attribute to given target attribute
    :param node: str
    :param attribute: str
    """

    return attribute.disconnect_attribute('{}.{}'.format(node, attribute_name))


def connect_multiply(source_node, source_attribute, target_node, target_attribute, value=0.1, multiply_name=None):
    """
    Connects source attribute into target attribute with a multiply node inbetween
    :param source_node: str
    :param source_attribute: str
    :param target_node: str
    :param target_attribute: str
    :param value: float, value of the multiply node
    :param multiply_name: str
    :return: str, name of the created multiply node
    """

    return attribute.connect_multiply(
        '{}.{}'.format(source_node, source_attribute), '{}.{}'.format(target_node, target_attribute),
        value=value, name=multiply_name)


def connect_translate(source_node, target_node):
    """
    Connects the translation of the source node into the rotation of the target node
    :param source_node: str
    :param target_node: str
    """

    return attribute.connect_translate(source_node, target_node)


def connect_rotate(source_node, target_node):
    """
    Connets the rotation of the source node into the rotation of the target node
    :param source_node: str
    :param target_node: str
    """

    return attribute.connect_rotate(source_node, target_node)


def connect_scale(source_node, target_node):
    """
    Connects the scale of the source node into the rotation of the target node
    :param source_node: str
    :param target_node: str
    """

    return attribute.connect_scale(source_node, target_node)


def connect_visibility(node, attr, target_node, default_value=True):
    """
    Connect the visibility of the target node into an attribute
    :param node: str, name of a node. If it does not exists, it will ber created
    :param attr: str, attribute name of a node. If it does not exists, it will ber created
    :param target_node: str, target node to connect its visibility into the attribute
    :param default_value: bool, Whether you want the visibility on/off by default
    """

    return attribute.connect_visibility(
        '{}.{}'.format(node, attr), target_node, default_value=default_value)


def connect_message_attribute(source_node, target_node, message_attribute, force=False):
    """
    Connects the message attribute of the input_node into a custom message attribute on target_node
    :param source_node: str, name of a node
    :param target_node: str, name of a node
    :param message_attribute: str, name of the message attribute to create and connect into. If already exists,
    just connect
    :param force, Whether or not force the connection of the message attribute
    """

    return attribute.connect_message(source_node, target_node, message_attribute, force=force)


def get_message_attributes(node, **kwargs):
    """
    Returns all message attributes of the give node
    :param node: str
    :return: list(str)
    """

    user_defined = kwargs.get('user_defined', True)

    return attribute.message_attributes(node, user_defined=user_defined)


def get_attribute_input(attribute_node, **kwargs):
    """
    Returns the input into given attribute
    :param attribute_node: str, full node and attribute (node.attribute) attribute we want to retrieve inputs of
    :param kwargs:
    :return: str
    """

    node_only = kwargs.get('node_only', False)

    return attribute.attribute_input(attribute_node, node_only=node_only)


def get_message_input(node, message_attribute):
    """
    Get the input value of a message attribute
    :param node: str
    :param message_attribute: str
    :return: object
    """

    return attribute.message_input(node=node, message=message_attribute)


def store_world_matrix_to_attribute(node, attribute_name='origMatrix', **kwargs):
    """
    Stores world matrix of given transform into an attribute in the same transform
    :param node: str
    :param attribute_name: str
    :param kwargs:
    """

    skip_if_exists = kwargs.get('skip_if_exists', False)

    return attribute.store_world_matrix_to_attribute(
        transform=node, attribute_name=attribute_name, skip_if_exists=skip_if_exists)


def list_connections(node, attribute_name, **kwargs):
    """
    List the connections of the given out attribute in given node
    :param node: str
    :param attribute_name: str
    :return: list<str>
    """

    return maya.cmds.listConnections('{}.{}'.format(node, attribute_name), **kwargs)


def list_connections_of_type(node, connection_type):
    """
    Returns a list of connections with the given type in the given node
    :param node: str
    :param connection_type: str
    :return: list<str>
    """

    return maya.cmds.listConnections(node, type=connection_type)


def list_node_connections(node):
    """
    Returns all connections of the given node
    :param node: str
    :return: list(str)
    """

    return maya.cmds.listConnections(node)


def list_source_destination_connections(node):
    """
    Returns source and destination connections of the given node
    :param node: str
    :return: list<str>
    """

    return maya.cmds.listConnections(node, source=True, destination=True)


def list_source_connections(node):
    """
    Returns source connections of the given node
    :param node: str
    :return: list<str>
    """

    return maya.cmds.listConnections(node, source=True, destination=False)


def list_destination_connections(node):
    """
    Returns source connections of the given node
    :param node: str
    :return: list<str>
    """

    return maya.cmds.listConnections(node, source=False, destination=True)


# =================================================================================================================
# MATERIALS/SHADERS
# =================================================================================================================

def default_shaders():
    """
    Returns a list with all thte default shadres of the current DCC
    :return: str
    """

    return shader_utils.get_default_shaders()


def create_surface_shader(shader_name, **kwargs):
    """
    Creates a new basic DCC surface shader
    :param shader_name: str
    :return: str
    """

    return_shading_group = kwargs.get('return_shading_group', False)

    shader = maya.cmds.shadingNode('surfaceShader', name=shader_name, asShader=True)
    sg = maya.cmds.sets(name='{}SG'.format(shader), renderable=True, noSurfaceShader=True, empty=True)
    maya.cmds.connectAttr('{}.outColor'.format(shader), '{}.surfaceShader'.format(sg), force=True)

    if return_shading_group:
        return sg

    return shader


def apply_shader(material, node):
    """
    Applies material to given node
    :param material: str
    :param node: str
    """

    shading_group = None
    if maya.cmds.nodeType(material) in ['surfaceShader', 'lambert']:
        shading_groups = maya.cmds.listConnections(material, type='shadingEngine')
        shading_group = shading_groups[0] if shading_groups else None
    elif maya.cmds.nodeType(material) == 'shadingEngine':
        shading_group = material
    if not shading_group:
        logger.warning('Impossible to apply material "{}" into "{}"'.format(material, node))
        return False

    maya.cmds.sets(node, e=True, forceElement=shading_group)


def list_materials(skip_default_materials=False, nodes=None):
    """
    Returns a list of materials in the current scene or given nodes
    :param skip_default_materials: bool, Whether to return also standard materials or not
    :param nodes: list(str), list of nodes we want to search materials into. If not given, all scene materials
        will be retrieved
    :return: list(str)
    """

    if nodes:
        all_materials = maya.cmds.ls(nodes, materials=True)
    else:
        all_materials = maya.cmds.ls(materials=True)

    if skip_default_materials:
        default_materials = shader_utils.get_default_shaders()
        for material in default_materials:
            if material in all_materials:
                all_materials.remove(material)

    return all_materials


def create_lambert_material(name='lambert', color=None, transparency=None, **kwargs):
    """
    Creates a new lambert material
    :param name: str
    :param color: tuple(float, float, float)
    :param transparency: float
    :param kwargs:
    :return: str
    """

    no_surface_shader = kwargs.get('no_surface_shader', False)
    shading_group_name = kwargs.get('shading_group_name', '{}SG'.format(name))

    new_material = maya.cmds.shadingNode('lambert', asShader=True, name=name)
    render_set = maya.cmds.sets(
        renderable=True, noSurfaceShader=no_surface_shader, empty=True, name=shading_group_name)
    maya.cmds.connectAttr('{}.outColor'.format(new_material), '{}.surfaceShader'.format(render_set))
    maya.cmds.setAttr('{}.outColor'.format(new_material), type='double3', *color)
    if color:
        maya.cmds.setAttr('{}.color'.format(new_material), type='double3', *color)
    if transparency:
        maya.cmds.setAttr('{}.transparency'.format(new_material), type='double3', *transparency)

    return new_material


# =================================================================================================================
# CAMERA
# =================================================================================================================

def is_camera(node_name):
    """
    Returns whether given node is a camera or not
    :param node_name: str
    :return: bool
    """

    return cam_utils.is_camera(node_name)


def get_all_cameras(full_path=True):
    """
    Returns all cameras in the scene
    :param full_path: bool
    :return: list(str)
    """

    return cam_utils.get_all_cameras(exclude_standard_cameras=True, return_transforms=True, full_path=full_path)


def get_current_camera(full_path=True):
    """
    Returns camera currently being used in scene
    :param full_path: bool
    :return: list(str)
    """

    return cam_utils.get_current_camera(full_path=full_path)


def look_through_camera(camera_name):
    """
    Updates DCC viewport to look through given camera
    :param camera_name: str
    :return:
    """

    return maya.cmds.lookThru(camera_name)


def get_camera_focal_length(camera_name):
    """
    Returns focal length of the given camera
    :param camera_name: str
    :return: float
    """

    return maya.cmds.getAttr('{}.focalLength'.format(camera_name))


# =================================================================================================================
# IK
# =================================================================================================================

def create_ik_handle(name, start_joint, end_joint, solver_type=None, curve=None, **kwargs):
    """
    Creates a new IK handle
    :param name: str
    :param start_joint: str
    :param end_joint: str
    :param solver_type: str
    :param curve: str
    :param kwargs:
    :return: str
    """

    if solver_type is None:
        solver_type = ik_utils.IkHandle.SOLVER_SC

    handle = ik_utils.IkHandle(name)
    handle.set_solver(solver_type)
    handle.set_start_joint(start_joint)
    handle.set_end_joint(end_joint)
    if curve and maya.cmds.objExists(curve):
        handle.set_curve(curve)

    return handle.create()


def create_spline_ik_stretch(
        curve, joints, node_for_attribute=None, create_stretch_on_off=False, stretch_axis='X', **kwargs):
    """
    Makes the joints stretch on the curve
    :param curve: str, name of the curve that joints are attached via Spline IK
    :param joints: list<str>, list of joints attached to Spline IK
    :param node_for_attribute: str, name of the node to create the attributes on
    :param create_stretch_on_off: bool, Whether to create or not extra attributes to slide the stretch value on/off
    :param stretch_axis: str('X', 'Y', 'Z'), axis that the joints stretch on
    :param kwargs:
    """

    create_bulge = kwargs.get('create_bulge', True)

    return ik_utils.create_spline_ik_stretch(
        curve, joints, node_for_attribute=node_for_attribute, create_stretch_on_off=create_stretch_on_off,
        scale_axis=stretch_axis, create_bulge=create_bulge)


# =================================================================================================================
# CONTROLS
# =================================================================================================================

def set_parent_controller(control, parent_controller):
    """
    Sets the parent controller of the given control
    :param control: str
    :param parent_controller: str
    """

    return maya.cmds.controller(control, parent_controller, p=True)


def get_control_colors():
    """
    Returns control colors available in DCC
    :return: list(float, float, float)
    """

    return maya_color.CONTROL_COLORS


def set_control_color(control_node, color=None):
    """
    Sets the color of the given control node
    :param control_node: str
    :param color: int or list(float, float, float)
    """

    shapes = maya.cmds.listRelatives(control_node, s=True, ni=True, f=True)
    for shp in shapes:
        if maya.cmds.attributeQuery('overrideEnabled', node=shp, exists=True):
            maya.cmds.setAttr(shp + '.overrideEnabled', True)
        if color is not None:
            if maya.cmds.attributeQuery('overrideRGBColors', node=shp, exists=True) and type(color) != int:
                maya.cmds.setAttr(shp + '.overrideRGBColors', True)
                if type(color) in [list, tuple]:
                    maya.cmds.setAttr(shp + '.overrideColorRGB', color[0], color[1], color[2])
            elif maya.cmds.attributeQuery('overrideColor', node=shp, exists=True):
                if type(color) == int and -1 < color < 32:
                    maya.cmds.setAttr(shp + '.overrideColor', color)
        else:
            if control_node.startswith('l_') or control_node.endswith('_l') or '_l_' in control_node:
                maya.cmds.setAttr(shp + '.overrideColor', 6)
            elif control_node.startswith('r_') or control_node.endswith('_r') or '_r_' in control_node:
                maya.cmds.setAttr(shp + '.overrideColor', 13)
            else:
                maya.cmds.setAttr(shp + '.overrideColor', 22)


# =================================================================================================================
# ANIMATION
# =================================================================================================================

def get_start_frame():
    """
    Returns current start frame
    :return: int
    """

    return animation.active_frame_range()[0]


def set_start_frame(start_frame):
    """
    Sets current start frame
    :param start_frame: int
    """

    return animation.set_start_frame(start_frame)


def get_end_frame():
    """
    Returns current end frame
    :return: int
    """

    return animation.active_frame_range()[1]


def set_end_frame(end_frame):
    """
    Sets current end frame
    :param end_frame: int
    """

    return animation.set_end_frame(end_frame)


def get_current_frame():
    """
    Returns current frame set in time slider
    :return: int
    """

    return gui.current_frame()


def set_current_frame(frame):
    """
    Sets the current frame in time slider
    :param frame: int
    """

    return gui.set_current_frame(frame)


def get_time_slider_range():
    """
    Return the time range from Maya time slider
    :return: list<int, int>
    """

    return gui.get_time_slider_range(highlighted=False)


def set_keyframe(node, attribute_name=None, **kwargs):
    """
    Sets keyframe in given attribute in given node
    :param node: str
    :param attribute_name: str
    :param kwargs:
    :return:
    """

    if attribute_name:
        return maya.cmds.setKeyframe('{}.{}'.format(node, attribute_name), **kwargs)
    else:
        return maya.cmds.setKeyframe(node, **kwargs)


def copy_key(node, attribute_name, time=None):
    """
    Copy key frame of given node
    :param node: str
    :param attribute_name: str
    :param time: bool
    :return:
    """

    if time:
        return maya.cmds.copyKey('{}.{}'.format(node, attribute_name), time=time)
    else:
        return maya.cmds.copyKey('{}.{}'.format(node, attribute_name))


def cut_key(node, attribute_name, time=None):
    """
    Cuts key frame of given node
    :param node: str
    :param attribute_name: str
    :param time: str
    :return:
    """

    if time:
        return maya.cmds.cutKey('{}.{}'.format(node, attribute_name), time=time)
    else:
        return maya.cmds.cutKey('{}.{}'.format(node, attribute_name))


def paste_key(node, attribute_name, option, time, connect):
    """
    Paste copied key frame
    :param node: str
    :param attribute_name: str
    :param option: str
    :param time: (int, int)
    :param connect: bool
    :return:
    """

    return maya.cmds.pasteKey('{}.{}'.format(node, attribute_name), option=option, time=time, connect=connect)


def offset_keyframes(node, attribute_name, start_time, end_time, duration):
    """
    Offset given node keyframes
    :param node: str
    :param attribute_name: str
    :param start_time: int
    :param end_time: int
    :param duration: float
    """

    return maya.cmds.keyframe(
        '{}.{}'.format(node, attribute_name), relative=True, time=(start_time, end_time), timeChange=duration)


def find_next_key_frame(node, attribute_name, start_time, end_time):
    """
    Returns next keyframe of the given one
    :param node: str
    :param attribute_name: str
    :param start_time: int
    :param end_time: int
    """

    return maya.cmds.findKeyframe('{}.{}'.format(node, attribute_name), time=(start_time, end_time), which='next')


def set_flat_key_frame(node, attribute_name, start_time, end_time):
    """
    Sets flat tangent in given keyframe
    :param node: str
    :param attribute_name: str
    :param start_time: int
    :param end_time: int
    """

    return maya.cmds.keyTangent('{}.{}'.format(node, attribute_name), time=(start_time, end_time), itt='flat')


def find_first_key_in_anim_curve(curve):
    """
    Returns first key frame of the given curve
    :param curve: str
    :return: int
    """

    return maya.cmds.findKeyframe(curve, which='first')


def find_last_key_in_anim_curve(curve):
    """
    Returns last key frame of the given curve
    :param curve: str
    :return: int
    """

    return maya.cmds.findKeyframe(curve, which='last')


def copy_anim_curve(curve, start_time, end_time):
    """
    Copies given anim curve
    :param curve: str
    :param start_time: int
    :param end_time: int
    """

    return maya.cmds.copyKey(curve, time=(start_time, end_time))


def export_shot_animation_curves(anim_curves_to_export, export_file_path, start_frame, end_frame, *args, **kwargs):
    """
    Exports given shot animation curves in the given path and in the given frame range
    :param anim_curves_to_export: list(str), animation curves to export
    :param export_file_path: str, file path to export animation curves information into
    :param start_frame: int, start frame to export animation from
    :param end_frame: int, end frame to export animation until
    :param args:
    :param kwargs:
    :return:
    """

    sequencer_least_key = kwargs.get('sequencer_least_key', None)
    sequencer_great_key = kwargs.get('sequencer_great_key', None)

    return sequencer.export_shot_animation_curves(
        anim_curves_to_export=anim_curves_to_export, export_file_path=export_file_path, start_frame=start_frame,
        end_frame=end_frame, sequencer_least_key=sequencer_least_key, sequencer_great_key=sequencer_great_key)


def import_shot_animation_curves(anim_curves_to_import, import_file_path, start_frame, end_frame):
    """
    Imports given shot animation curves in the given path and in the given frame range
    :param anim_curves_to_import: list(str), animation curves to import
    :param import_file_path: str, file path to import animation curves information fron
    :param start_frame: int, start frame to import animation from
    :param end_frame: int, end frame to import animation until
    :param args:
    :param kwargs:
    """

    return sequencer.import_shot_animation_curves(
        anim_curves_to_import=anim_curves_to_import, import_file_path=import_file_path,
        start_frame=start_frame, end_frame=end_frame)


def node_animation_curves(node):
    """
    Returns all animation curves of the given node
    :param node: str
    :return:
    """

    return animation.node_animation_curves(node)


def all_animation_curves():
    """
    Returns all animation located in current DCC scene
    :return: list(str)
    """

    return animation.all_anim_curves()


def all_keyframes_in_anim_curves(anim_curves=None):
    """
    Retursn al keyframes in given anim curves
    :param anim_curves: list(str)
    :return: list(str)
    """

    return animation.all_keyframes_in_anim_curves(anim_curves)


def key_all_anim_curves_in_frames(frames, anim_curves=None):
    """
    Inserts keyframes on all animation curves on given frame
    :param frame: list(int)
    :param anim_curves: list(str)
    """

    return animation.key_all_anim_curves_in_frames(frames=frames, anim_curves=anim_curves)


def remove_keys_from_animation_curves(range_to_delete, anim_curves=None):
    """
    Inserts keyframes on all animation curves on given frame
    :param range_to_delete: list(int ,int)
    :param anim_curves: list(str)
    """

    return animation.delete_keys_from_animation_curves_in_range(
        range_to_delete=range_to_delete, anim_curves=anim_curves)


def check_anim_curves_has_fraction_keys(anim_curves, selected_range=None):
    """
    Returns whether given curves have or not fraction keys
    :param anim_curves: list(str)
    :param selected_range: list(str)
    :return: bool
    """

    return animation.check_anim_curves_has_fraction_keys(anim_curves=anim_curves, selected_range=selected_range)


def convert_fraction_keys_to_whole_keys(animation_curves=None, consider_selected_range=False):
    """
    Find keys on fraction of a frame and insert a key on the nearest whole number frame
    Useful to make sure that no keys are located on fraction of frames
    :param animation_curves: list(str)
    :param consider_selected_range: bool
    :return:
    """

    return animation.convert_fraction_keys_to_whole_keys(
        animation_curves=animation_curves, consider_selected_range=consider_selected_range)


def set_active_frame_range(start_frame, end_frame):
    """
    Sets current animation frame range
    :param start_frame: int
    :param end_frame: int
    """

    return animation.set_active_frame_range(start_frame, end_frame)


def is_auto_keyframe_enabled():
    """
    Returns whether auto keyframe mode is enabled
    :return: bool
    """

    return animation.is_auto_keyframe_enabled()


def set_auto_keyframe_enabled(flag):
    """
    Enables/Disables auto keyframe mode
    :param flag: bool
    """

    return animation.set_auto_keyframe_enabled(flag)


# =================================================================================================================
# CLUSTERS
# =================================================================================================================

def create_cluster(objects, cluster_name='cluster', **kwargs):
    """
    Creates a new cluster in the given objects
    :param objects: list(str)
    :param cluster_name: str
    :return: list(str)
    """

    relative = kwargs.pop('relative', False)

    return maya.cmds.cluster(objects, n=find_unique_name(cluster_name), relative=relative, **kwargs)


def create_cluster_surface(
        surface, name, first_cluster_pivot_at_start=True, last_cluster_pivot_at_end=True, join_ends=False):
    """
    Creates a new clustered surface
    :param surface: str
    :param name: str
    :param first_cluster_pivot_at_start: str
    :param last_cluster_pivot_at_end: str
    :param join_ends: bool
    :return: list(str), list(str)
    """

    cluster_surface = cluster_utils.ClusterSurface(surface, name)
    cluster_surface.set_first_cluster_pivot_at_start(first_cluster_pivot_at_start)
    cluster_surface.set_last_cluster_pivot_at_end(last_cluster_pivot_at_end)
    cluster_surface.set_join_ends(join_ends)
    cluster_surface.create()

    return cluster_surface.get_cluster_handle_list(), cluster_surface.get_cluster_list()


def create_cluster_curve(
        curve, name, first_cluster_pivot_at_start=True, last_cluster_pivot_at_end=True, join_ends=False):
    """
    Creates a new clustered curve
    :param curve: str
    :param name: str
    :param first_cluster_pivot_at_start: str
    :param last_cluster_pivot_at_end: str
    :param last_cluster_pivot_at_end: str
    :param join_ends: bool
    :return: list(str), list(str)
    """

    cluster_curve = cluster_utils.ClusterCurve(curve, name)
    cluster_curve.set_first_cluster_pivot_at_start(first_cluster_pivot_at_start)
    cluster_curve.set_last_cluster_pivot_at_end(last_cluster_pivot_at_end)
    cluster_curve.set_join_ends(join_ends)
    cluster_curve.create()

    return cluster_curve.get_cluster_handle_list(), cluster_curve.get_cluster_list()


# =================================================================================================================
# RENDER
# =================================================================================================================

def get_playblast_formats():
    """
    Returns a list of supported formats for DCC playblast
    :return: list(str)
    """

    return playblast.get_playblast_formats()


def get_playblast_compressions(playblast_format):
    """
    Returns a list of supported compressions for DCC playblast
    :param playblast_format: str
    :return: list(str)
    """

    return playblast.get_playblast_compressions(format=playblast_format)


def get_viewport_resolution_width():
    """
    Returns the default width resolution of the current DCC viewport
    :return: int
    """

    current_panel = gui.active_editor()
    if not current_panel:
        return 0

    return maya.cmds.control(current_panel, query=True, width=True)


def get_viewport_resolution_height():
    """
    Returns the default height resolution of the current DCC viewport
    :return: int
    """

    current_panel = gui.active_editor()
    if not current_panel:
        return 0

    return maya.cmds.control(current_panel, query=True, height=True)


def get_renderers():
    """
    Returns dictionary with the different renderers supported by DCC
    :return: dict(str, str)
    """

    active_editor = gui.active_editor()
    if not active_editor:
        return {}

    renderers_ui = maya.cmds.modelEditor(active_editor, query=True, rendererListUI=True)
    renderers_id = maya.cmds.modelEditor(active_editor, query=True, rendererList=True)

    renderers = dict(zip(renderers_ui, renderers_id))

    return renderers


def get_default_render_resolution_width():
    """
    Sets the default resolution of the current DCC panel
    :return: int
    """

    return maya.cmds.getAttr('defaultResolution.width')


def get_default_render_resolution_height():
    """
    Sets the default resolution of the current DCC panel
    :return: int
    """

    return maya.cmds.getAttr('defaultResolution.height')


def get_default_render_resolution_aspect_ratio():
    """
    Returns the default resolution aspect ratio of the current DCC render settings
    :return: float
    """

    return maya.cmds.getAttr('defaultResolution.deviceAspectRatio')


def open_render_settings():
    """
    Opens DCC render settings options
    """

    gui.open_render_settings_window()


def all_scene_shots():
    """
    Returns all shots in current scene
    :return: list(str)
    """

    return sequencer.get_all_scene_shots()


def shot_is_muted(shot_node):
    """
    Returns whether given shot node is muted
    :param shot_node: str
    :return: bool
    """

    return sequencer.get_shot_is_muted(shot_node)


def shot_track_number(shot_node):
    """
    Returns track where given shot node is located
    :param shot_node: str
    :return: int
    """

    return sequencer.get_shot_track_number(shot_node)


def shot_start_frame_in_sequencer(shot_node):
    """
    Returns the start frame of the given shot in sequencer time
    :param shot_node: str
    :return: int
    """

    return sequencer.get_shot_start_frame_in_sequencer(shot_node)


def shot_end_frame_in_sequencer(shot_node):
    """
    Returns the end frame of the given shot in sequencer time
    :param shot_node: str
    :return: int
    """

    return sequencer.get_shot_end_frame_in_sequencer(shot_node)


def shot_pre_hold(shot_node):
    """
    Returns shot prehold value
    :param shot_node: str
    :return: int
    """

    return sequencer.get_shot_post_hold(shot_node)


def shot_post_hold(shot_node):
    """
    Returns shot posthold value
    :param shot_node: str
    :return: int
    """

    return sequencer.get_shot_pre_hold(shot_node)


def shot_scale(shot_node):
    """
    Returns the scale of the given shot
    :param shot_node: str
    :return: int
    """

    return sequencer.get_shot_scale(shot_node)


def shot_start_frame(shot_node):
    """
    Returns the start frame of the given shot
    :param shot_node: str
    :return: int
    """

    return sequencer.get_shot_start_frame(shot_node)


def set_shot_start_frame(shot_node, start_frame):
    """
    Sets the start frame of the given shot
    :param shot_node: str
    :param start_frame: int
    :return: int
    """

    return maya.cmds.setAttr('{}.startFrame'.format(shot_node), start_frame)


def shot_end_frame(shot_node):
    """
    Returns the end frame of the given shot
    :param shot_node: str
    :return: int
    """

    return sequencer.get_shot_end_frame(shot_node)


def set_shot_end_frame(shot_node, end_frame):
    """
    Sets the end frame of the given shot
    :param shot_node: str
    :param end_frame: int
    :return: int
    """

    return maya.cmds.setAttr('{}.endFrame'.format(shot_node), end_frame)


def shot_camera(shot_node):
    """
    Returns camera associated given node
    :param shot_node: str
    :return: str
    """

    return sequencer.get_shot_camera(shot_node)


# =================================================================================================================
# HUMAN IK (HIK)
# =================================================================================================================

def get_scene_hik_characters():
    """
    Returns all HumanIK characters in current scene
    :return: list(str)
    """

    return humanik.get_scene_characters() or list()


# =================================================================================================================
# DECORATORS
# =================================================================================================================

def undo_decorator():
    """
    Returns undo decorator for current DCC
    """

    return maya_decorators.undo_chunk


def repeat_last_decorator(command_name=None):
    """
    Returns repeat last decorator for current DCC
    """

    return maya_decorators.repeat_static_command(command_name)


def enable_wait_cursor():
    """
    Enables wait cursor in current DCC
    """

    return maya.cmds.waitCursor(state=True)


def disable_wait_cursor():
    """
    Enables wait cursor in current DCC
    """

    return maya.cmds.waitCursor(state=False)


def suspend_refresh_decorator():
    """
    Returns suspend refresh decorator for current DCC
    """

    return maya_decorators.suspend_refresh


def restore_selection_decorator():
    """
    Returns decorators that select again the objects that were selected before executing the decorated function
    """

    return maya_decorators.restore_selection
