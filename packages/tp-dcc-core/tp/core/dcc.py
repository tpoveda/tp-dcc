#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC core functions an classes
"""

import os
import sys
import importlib
import traceback
from functools import wraps
from collections import OrderedDict

from tp.core import consts, log
from tp.common.python import osplatform

logger = log.tpLogger

main = __import__('__main__')

# Cached current DCC name.
CURRENT_DCC = None

# Cached used to store all the reroute paths done during a session.
DCC_REROUTE_CACHE = dict()

# Cached DCC clients
_CLIENTS = dict()


class Dccs(object):
    Standalone = 'standalone'
    Maya = 'maya'
    Max = 'max'
    MotionBuilder = 'mobu'
    Houdini = 'houdini'
    Nuke = 'nuke'
    Unreal = 'unreal'

    ALL = [
        Maya, Max, MotionBuilder, Houdini, Nuke, Unreal
    ]

    nice_names = OrderedDict([
        (Maya, 'Maya'),
        (Max, '3ds Max'),
        (MotionBuilder, 'MotionBuilder'),
        (Houdini, 'Houdini'),
        (Nuke, 'Nuke'),
        (Unreal, 'Unreal')
    ])

    packages = OrderedDict([
        ('cmds', Maya),
        ('pymxs', Max),
        ('pyfbsdk', MotionBuilder),
        ('hou', Houdini),
        ('nuke', Nuke),
        ('unreal', Unreal)
    ])

    # TODO: Add support for both MacOS and Linux
    # TODO: Add missing executables
    executables = {
        Maya: {osplatform.Platforms.Windows: 'maya.exe'},
        Max: {osplatform.Platforms.Windows: '3dsmax.exe'},
        MotionBuilder: {osplatform.Platforms.Windows: 'motionbuilder.exe'},
        Houdini: {osplatform.Platforms.Windows: 'houdinifx.exe'},
        Nuke: {},
        Unreal: {osplatform.Platforms.Windows: 'UE4Editor.exe'}
    }


class DccCallbacks(object):
    Shutdown = (consts.CallbackTypes.Shutdown, {'type': 'simple'})
    Tick = (consts.CallbackTypes.Tick, {'type': 'simple'})
    ScenePreCreated = (consts.CallbackTypes.ScenePreCreated, {'type': 'simple'})
    ScenePostCreated = (consts.CallbackTypes.ScenePostCreated, {'type': 'simple'})
    SceneNewRequested = (consts.CallbackTypes.SceneNewRequested, {'type': 'simple'})
    SceneNewFinished = (consts.CallbackTypes.SceneNewFinished, {'type': 'simple'})
    SceneSaveRequested = (consts.CallbackTypes.SceneSaveRequested, {'type': 'simple'})
    SceneSaveFinished = (consts.CallbackTypes.SceneSaveFinished, {'type': 'simple'})
    SceneOpenRequested = (consts.CallbackTypes.SceneOpenRequested, {'type': 'simple'})
    SceneOpenFinished = (consts.CallbackTypes.SceneOpenFinished, {'type': 'simple'})
    UserPropertyPreChanged = (consts.CallbackTypes.UserPropertyPreChanged, {'type': 'filter'})
    UserPropertyPostChanged = (consts.CallbackTypes.UserPropertyPostChanged, {'type': 'filter'})
    NodeSelect = (consts.CallbackTypes.NodeSelect, {'type': 'filter'})
    NodeAdded = (consts.CallbackTypes.NodeAdded, {'type': 'filter'})
    NodeDeleted = (consts.CallbackTypes.NodeDeleted, {'type': 'filter'})


def dcc_port(base_port, dcc_name=None):
    dcc = dcc_name or current_dcc()
    if not dcc:
        return base_port

    base_dcc_port = base_port
    for dcc_name in Dccs.ALL:
        base_dcc_port += 1
        if dcc_name == dcc:
            return base_dcc_port

    return base_port


def dcc_ports(base_port):
    all_ports = OrderedDict()
    all_ports['base'] = base_port
    for dcc_name in enumerate(Dccs.ALL):
        all_ports[dcc_name] = base_port + 1

    return all_ports


def current_dcc():
    global CURRENT_DCC
    if CURRENT_DCC:
        return CURRENT_DCC

    for dcc_package, dcc_name in Dccs.packages.items():
        if dcc_package in main.__dict__:
            CURRENT_DCC = dcc_name
            break
    if not CURRENT_DCC:
        try:
            import unreal
            CURRENT_DCC = Dccs.Unreal
        except ImportError:
            try:
                if os.path.splitext(os.path.basename(sys.executable))[0].lower() == 'motionbuilder':
                    import pyfbsdk
                    CURRENT_DCC = Dccs.MotionBuilder
                else:
                    CURRENT_DCC = Dccs.Standalone
            except ImportError:
                CURRENT_DCC = Dccs.Standalone

    return CURRENT_DCC


def get_dcc_loader_module():
    """
    Checks DCC we are working on an initializes proper variables
    """

    dcc_mod = None
    for dcc_package, dcc_name in Dccs.packages.items():
        if dcc_package in main.__dict__:
            module_to_import = 'tp.{}.loader'.format(dcc_name)
            try:
                dcc_mod = importlib.import_module(module_to_import)
            except ImportError:
                logger.warning('DCC loader module {} not found!'.format(module_to_import))
                continue
            if dcc_mod:
                break
    if not dcc_mod:
        try:
            import unreal
            dcc_mod = importlib.import_module('tp.unreal.loader')
        except Exception:
            try:
                import pyfbsdk
                dcc_mod = importlib.import_module('tp.mobu.loader')
            except ImportError:
                pass

    return dcc_mod


def reroute(fn):
    """
    Decorator that reroutes the function call on runtime to the specific DCC implementation of the function
    Rerouted function calls are cached, and are only loaded once.
    The used DCC API will be retrieved from the current session, taking into account the current available
    implementations

    :param fn:
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):

        global DCC_REROUTE_CACHE

        dcc = current_dcc()
        if not dcc:
            return None

        # From the current function and DCC we retrieve module path where DCC implementation should be located
        fn_split = fn.__module__.split('.')
        dcc_reroute_path = 'tp.{}'.format(dcc)
        fn_split_str = '.'.join(fn_split[3:])
        if fn_split_str:
            dcc_reroute_path = '{}.{}'.format(dcc_reroute_path, fn_split_str)
        dcc_reroute_path = '{}.dcc'.format(dcc_reroute_path)
        dcc_reroute_fn_path = '{}.{}'.format(dcc_reroute_path, fn.__name__)
        if dcc_reroute_fn_path not in DCC_REROUTE_CACHE:
            try:
                dcc_reroute_module = importlib.import_module(dcc_reroute_path)
            except ImportError as exc:
                raise NotImplementedError(
                    '{} | Function {} not implemented! {}'.format(dcc, dcc_reroute_fn_path, traceback.format_exc()))
            except Exception as exc:
                raise exc

            # Cache reroute call, next calls to that function will use cache data
            if not hasattr(dcc_reroute_module, fn.__name__):
                raise NotImplementedError('{} | Function {} not implemented!'.format(dcc, dcc_reroute_fn_path))

            dcc_reroute_fn = getattr(dcc_reroute_module, fn.__name__)
            DCC_REROUTE_CACHE[dcc_reroute_fn_path] = dcc_reroute_fn

        return DCC_REROUTE_CACHE[dcc_reroute_fn_path](*args, **kwargs)

    return wrapper


def callbacks():
    """
    Return a full list of callbacks based on DccCallbacks dictionary
    :return: list<str>
    """

    new_list = list()
    for k, v in DccCallbacks.__dict__.items():
        if k.startswith('__') or k.endswith('__'):
            continue
        new_list.append(v[0])

    return new_list


def client(key=None, only_clients=False):
    """
    Returns first current active DCC client
    :return: DccClient
    """
    
    from tp.core import dcc

    client = None
    if _CLIENTS:
        if key:
            client = _CLIENTS.get(key, None)
            if client:
                return client()
        else:
            client = _CLIENTS[list(_CLIENTS.keys())[0]]

    if not client:
        if only_clients:
            return None
        return dcc

    return client


def clients():
    """
    Returns all current active DCCs
    :return: list(DccClient)
    """

    if not _CLIENTS:
        return client()

    return [found_client() for found_client in _CLIENTS]


def is_standalone():
    """
    Check if current environment is standalone or not
    :return: bool
    """

    return not any(pkg in list(main.__dict__.keys()) for pkg in Dccs.packages)


def is_maya():
    """
    Checks if Maya is available or not
    :return: bool
    """

    return 'cmds' in main.__dict__


def is_max():
    """
    Checks if Max is available or not
    :return: bool
    """

    return 'MaxPlus' in main.__dict__ or 'pymxs' in main.__dict__


def is_mobu():
    """
    Checks if MotionBuilder is available or not
    :return: bool
    """

    return 'pyfbsdk' in main.__dict__


def is_houdini():
    """
    Checks if Houdini is available or not
    :return: bool
    """

    return 'hou' in main.__dict__


def is_unreal():
    """
    Checks if Houdini is available or not
    :return: bool
    """

    return 'unreal' in main.__dict__


def is_nuke():
    """
    Checks if Nuke is available or not
    :return: bool
    """

    return 'nuke' in main.__dict__


# =================================================================================================================
# GENERAL CLASSES
# =================================================================================================================

class MirrorPlane(object):
    YZ = [-1, 1, 1]
    XZ = [1, -1, 1]
    XY = [1, 1, -1]


# =================================================================================================================
# GENERAL
# =================================================================================================================


@reroute
def get_name():
    """
    Returns the name of the DCC
    :return: str
    """

    raise NotImplementedError()


@reroute
def get_extensions():
    """
    Returns supported extensions of the DCC
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def get_version():
    """
    Returns version of the DCC
    :return: int
    """

    raise NotImplementedError()


@reroute
def get_version_name():
    """
    Returns version of the DCC
    :return: str
    """

    raise NotImplementedError()


@reroute
def is_batch():
    """
    Returns whether DCC is being executed in batch mode or not
    :return: bool
    """

    raise NotImplementedError()


@reroute
def execute_deferred(fn):
    """
    Executes given function in deferred mode
    """

    raise NotImplementedError()


@reroute
def deferred_function(fn, *args, **kwargs):
    """
    Calls given function with given arguments in a deferred way
    :param fn:
    :param args: list
    :param kwargs: dict
    """

    raise NotImplementedError()


@reroute
def is_component_mode():
    """
    Returns whether current DCC selection mode is component mode or not
    :return: bool
    """

    raise NotImplementedError()


@reroute
def enable_component_selection():
    """
    Enables DCC component selection mode
    """

    raise NotImplementedError()


@reroute
def is_plugin_loaded(plugin_name):
    """
    Return whether given plugin is loaded or not
    :param plugin_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def load_plugin(plugin_path, quiet=True):
    """
    Loads given plugin
    :param plugin_path: str
    :param quiet: bool
    """

    raise NotImplementedError()


@reroute
def unload_plugin(plugin_path):
    """
    Unloads the given plugin
    :param plugin_path: str
    """

    raise NotImplementedError()


@reroute
def list_old_plugins():
    """
    Returns a list of old plugins in the current scene
    :return: list<str>
    """

    raise NotImplementedError()


@reroute
def remove_old_plugin(plugin_name):
    """
    Removes given old plugin from current scene
    :param plugin_name: str
    """

    raise NotImplementedError()


@reroute
def set_workspace(workspace_path):
    """
    Sets current workspace to the given path
    :param workspace_path: str
    """

    raise NotImplementedError()


@reroute
def warning(message):
    """
    Prints a warning message
    :param message: str
    :return:
    """

    raise NotImplementedError()


@reroute
def error(message):
    """
    Prints a error message
    :param message: str
    :return:
    """

    raise NotImplementedError()


@reroute
def fit_view(animation=True):
    """
    Fits current viewport to current selection
    :param animation: bool, Animated fit is available
    """

    raise NotImplementedError()


@reroute
def refresh_viewport():
    """
    Refresh current DCC viewport
    """

    raise NotImplementedError()


@reroute
def refresh_viewport():
    """
    Refresh current DCC viewport
    """

    raise NotImplementedError()


@reroute
def refresh_all_viewport():
    """
    Refresh all DCC viewports
    """

    raise NotImplementedError()


@reroute
def focus(object_to_focus):
    """
    Focus in given object
    :param object_to_focus: str
    """

    raise NotImplementedError()


@reroute
def enable_undo():
    """
    Enables undo functionality
    """

    raise NotImplementedError()


@reroute
def disable_undo():
    """
    Disables undo functionality
    """

    raise NotImplementedError()


# =================================================================================================================
# GUI
# =================================================================================================================

@reroute
def get_dpi(value=1):
    """
    Returns current DPI used by DCC
    :param value: float
    :return: float
    """

    raise NotImplementedError()


@reroute
def get_dpi_scale(value):
    """
    Returns current DPI scale used by DCC
    :param value: float
    :return: float
    """

    raise NotImplementedError()


@reroute
def get_main_window():
    """
    Returns Qt object that references to the main DCC window
    :return:
    """

    raise NotImplementedError()


@reroute
def get_main_menubar():
    """
    Returns Qt object that references to the main DCC menubar
    :return:
    """

    raise NotImplementedError()


@reroute
def is_window_floating(window_name):
    """
    Returns whether or not DCC window is floating
    :param window_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def is_window_floating(window_name):
    """
    Returns whether or not DCC window is floating
    :param window_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def focus_ui_panel(panel_name):
    """
    Focus UI panel with given name
    :param panel_name: str
    """

    raise NotImplementedError()


@reroute
def get_dockable_window_class():
    """
    Returns class that should be used to instance an ew dockable DCC window
    :return: class
    """

    raise NotImplementedError()


@reroute
def get_dialog_result_yes():
    """
    Returns output when a DCC dialog result is accepted
    :return:
    """

    raise NotImplementedError()


@reroute
def get_dialog_result_no():
    """
    Returns output when a DCC dialog result is rejected
    :return:
    """

    raise NotImplementedError()


@reroute
def get_dialog_result_cancel():
    """
    Returns output when a DCC dialog result is cancelled
    :return:
    """

    raise NotImplementedError()


@reroute
def get_dialog_result_close():
    """
    Returns output when a DCC dialog result is close
    :return:
    """

    raise NotImplementedError()


@reroute
def show_message_in_viewport(msg, **kwargs):
    """
    Shows a message in DCC viewport
    :param msg: str, Message to show
    :param kwargs: dict, extra arguments
    """

    raise NotImplementedError()


@reroute
def add_shelf_menu_item(parent, label, command='', icon=''):
    """
    Adds a new menu item
    :param parent:
    :param label:
    :param command:
    :param icon:
    :return:
    """

    raise NotImplementedError()


@reroute
def add_shelf_sub_menu_item(parent, label, icon=''):
    """
    Adds a new sub menu item
    :param parent:
    :param label:
    :param icon:
    :return:
    """

    raise NotImplementedError()


@reroute
def add_shelf_separator(shelf_name):
    """
    Adds a new separator to the given shelf
    :param shelf_name: str
    """

    raise NotImplementedError()


@reroute
def shelf_exists(shelf_name):
    """
    Returns whether given shelf already exists or not
    :param shelf_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def create_shelf(shelf_name, shelf_label=None):
    """
    Creates a new shelf with the given name
    :param shelf_name: str
    :param shelf_label: str
    """

    raise NotImplementedError()


@reroute
def delete_shelf(shelf_name):
    """
    Deletes shelf with given name
    :param shelf_name: str
    """

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


@reroute
def select_file_dialog(title, start_directory=None, pattern=None):
    """
    Shows select file dialog
    :param title: str
    :param start_directory: str
    :param pattern: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def select_folder_dialog(title, start_directory=None):
    """
    Shows select folder dialog
    :param title: str
    :param start_directory: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def save_file_dialog(title, start_directory=None, pattern=None):
    """
    Shows save file dialog
    :param title: str
    :param start_directory: str
    :param pattern: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def get_current_model_panel():
    """
    Returns the current model panel name
    :return: str | None
    """

    raise NotImplementedError()


@reroute
def dock_widget(widget, *args, **kwargs):
    """
    Docks given widget into current DCC UI
    :param widget: QWidget
    :param args:
    :param kwargs:
    :return:
    """
    raise NotImplementedError()


@reroute
def get_all_fonts():
    """
    Returns all fonts available in DCC
    :return: list(str)
    """

    raise NotImplementedError()


# =================================================================================================================
# OBJECTS / NODES
# =================================================================================================================

@reroute
def node_types():
    """
    Returns a dictionary that provides a mapping between tpDcc object types and  Dcc specific node types
    :return: dict
    """

    raise NotImplementedError()


@reroute
def dcc_to_tpdcc_types():
    """
    # Returns a dictionary that provides a mapping between Dcc object types and tpDcc object types
    :return:
    """

    raise NotImplementedError()


@reroute
def dcc_to_tpdcc_str_types():
    """
    Returns a dictionary that provides a mapping between Dcc string object types and tpDcc object types
    :return:
    """

    raise NotImplementedError()


@reroute
def node_tpdcc_type(self, node, as_string=False):
    """
    Returns the DCC object type as a string given a specific tpDcc object type
    :param node: str
    :param as_string: bool
    :return: str
    """

    raise NotImplementedError()


@reroute
def root_node():
    """
    Returns DCC scene root node
    :return: str
    """

    raise NotImplementedError()


@reroute
def node_exists(node_name):
    """
    Returns whether given object exists or not
    :param node_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def object_type(node_name):
    """
    Returns type of given object
    :param node_name: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def node_type(node_name):
    """
    Returns node type of given object
    :param node_name: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def check_object_type(node, node_type, check_sub_types=False):
    """
    Returns whether give node is of the given type or not
    :param node: str
    :param node_type: str
    :param check_sub_types: bool
    :return: bool
    """

    raise NotImplementedError()


@reroute
def node_handle(node_name):
    """
    Returns unique identifier of the given node
    :param node_name str
    :return: str
    """

    raise NotImplementedError()


@reroute
def node_is_empty(node_name, *args, **kwargs):
    """
    Returns whether given node is an empty one
    The concept of empty node can vary depending on the DCC
    :param node_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def node_is_root(node_name):
    """
    Returns whether or not given node is a DCC scene root node
    :param node_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def node_is_selected(node_name):
    """
    Returns whether or not given node is currently selected
    :param node_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def node_is_transform(node_name):
    """
    Returns whether or not given node is a transform node
    :param node_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def node_is_joint(node_name):
    """
    Returns whether or not given node is a joint node
    :param node_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def node_is_locator(node_name):
    """
    Returns whether or not given node is a locator node
    :param node_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def node_is_box_mode(node_name):
    """
    Returns whether or not given node is being displayed as box
    :param node_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def node_is_frozen(node_name):
    """
    Returns whether or not given node is frozen
    :param node_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def node_is_hidden(node_name):
    """
    Returns whether or not given node is hidden
    :param node_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def find_node_by_name(node_name):
    """
    Returns node by its given node.
    This function makes sure that the returned node is an existing node
    :param node_name: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def find_node_by_id(unique_id, full_path=True):
    """
    Returns node by its given id.
    This function makes sure that the returned node is an existing node
    :param unique_id: str
    :param full_path: bool
    :return: str
    """

    raise NotImplementedError()


@reroute
def rename_node(node, new_name, **kwargs):
    """
    Renames given node with new given name
    :param node: str
    :param new_name: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def duplicate_node(node_name, new_node_name='', only_parent=False, return_roots_only=False, rename_children=False):
    """
    Duplicates given object in current scene
    :param node_name: str
    :param new_node_name: str
    :param only_parent: bool, If True, only given node will be duplicated (ignoring its children)
    :param return_roots_only: bool, If True, only the root nodes of the new hierarchy will be returned
    :param rename_children: bool, Whether or not children nodes are renamed
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def delete_node(node_name):
    """
    Removes given node from current scene
    :param node_name: str
    """

    raise NotImplementedError()


@reroute
def create_node(node_type, node_name=None):
    """
    Creates a new node of the given type and with the given name
    :param node_type: str
    :param node_name: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def set_node_normal_display(node, flag):
    """
    Sets whether or not given node is displayed in normal mode
    :param node: str
    :param flag: bool
    """

    raise NotImplementedError()


@reroute
def set_node_template_display(node, flag):
    """
    Sets whether or not given node is displayed in template mode
    :param node: str
    :param flag: bool
    """

    raise NotImplementedError()


@reroute
def set_node_reference_display(node, flag):
    """
    Sets whether or not given node is displayed in reference mode
    :param node: str
    :param flag: bool
    """

    raise NotImplementedError()


@reroute
def set_node_renderable(node, flag):
    """
    Sets whether or not given node is renderable
    :param node: str
    :param flag: bool
    """

    raise NotImplementedError()


@reroute
def set_node_cast_shadows(node, flag):
    """
    Sets whether or not given node can cast shadows
    :param node: str
    :param flag: bool
    """

    raise NotImplementedError()


@reroute
def set_node_receive_shadows(node, flag):
    """
    Sets whether or not given node can receive shadows
    :param node: str
    :param flag: bool
    """

    raise NotImplementedError()


@reroute
def set_node_light_interaction(node, flag):
    """
    Sets whether or not given node can interact with lights
    :param node: str
    :param flag: bool
    """

    raise NotImplementedError()


@reroute
def set_node_has_motion_blur(node, flag):
    """
    Sets whether or not given node can have motion blur
    :param node: str
    :param flag: bool
    """

    raise NotImplementedError()


@reroute
def set_node_is_visible_to_cameras(node, flag):
    """
    Sets whether or not given node is visible by cameras
    :param node: str
    :param flag: bool
    """

    raise NotImplementedError()


@reroute
def set_node_smooth_shading(node, flag):
    """
    Sets whether or not given node has smooth shading
    :param node: str
    :param flag: bool
    """

    raise NotImplementedError()


@reroute
def set_node_is_visible_in_reflections(node, flag):
    """
    Sets whether or not given node is visible in reflections
    :param node: str
    :param flag: bool
    """

    raise NotImplementedError()


@reroute
def set_node_is_visible_in_refractions(node, flag):
    """
    Sets whether or not given node is visible in refractions
    :param node: str
    :param flag: bool
    """

    raise NotImplementedError()


@reroute
def set_node_double_sided(node, flag):
    """
    Sets whether or not given node polygons can be renderer in both back and front directions
    :param node: str
    :param flag: bool
    """

    raise NotImplementedError()


@reroute
def show_node(node):
    """
    Shows given object
    :param node: str
    """

    raise NotImplementedError()


@reroute
def hide_node(node):
    """
    Hides given object
    :param node: str
    """

    raise NotImplementedError()


@reroute
def clean_construction_history(node):
    """
    Removes the construction history of the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def node_attribute_name(node_and_attr):
    """
    Returns the attribute part of a given node name
    :param node_and_attr: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def node_object_color(node):
    """
    Returns the color of the given node
    :param node: str
    :return: list(int, int, int, int)
    """

    raise NotImplementedError()


@reroute
def node_override_enabled(node):
    """
    Returns whether the given node has its display override attribute enabled or not
    :param node: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def node_is_visible(node_name):
    """
    Returns whether given node is visible or not
    :param node_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def node_color(node_name):
    """
    Returns color of the given node
    :param node: str
    :param node: str
    :return:
    """

    raise NotImplementedError()


@reroute
def node_rgb_color(node_name, linear=True):
    """
    Returns color of the given node
    :param node_name: str
    :param linear: bool, Whether or not the RGB should be in linear space (matches viewport color)
    :return:
    """

    raise NotImplementedError()


@reroute
def set_node_color(node_name, color):
    """
    Sets the color of the given node
    :param node_name: str
    :param color:
    """

    raise NotImplementedError()


@reroute
def node_components(node):
    """
    Returns all components of the given node
    :param node: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def node_is_referenced(node):
    """
    Returns whether given node is referenced or not
    :param node: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def node_reference_path(node, without_copy_number=False):
    """
    Returns reference path of the referenced node
    :param node: str
    :param without_copy_number: bool
    :return: str
    """

    raise NotImplementedError()


@reroute
def node_unreference(node):
    """
    Unreferences given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def node_nodes(node):
    """
    Returns referenced nodes of the given node
    :param node: str
    :return: list<str>
    """

    raise NotImplementedError()


@reroute
def node_filename(node, no_copy_number=True):
    """
    Returns file name of the given node
    :param node: str
    :param no_copy_number: bool
    :return: str
    """

    raise NotImplementedError()


@reroute
def change_filename(node, new_filename):
    """
    Changes filename of a given reference node
    :param node: str
    :param new_filename: str
    """

    raise NotImplementedError()


@reroute
def import_reference(filename):
    """
    Imports object from reference node filename
    :param filename: str
    """

    raise NotImplementedError()


@reroute
def node_is_loaded(node):
    """
    Returns whether given node is loaded or not
    :param node: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def node_is_locked(node):
    """
    Returns whether given node is locked or not
    :param node: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def node_children(node, all_hierarchy=True, full_path=True):
    """
    Returns a list of children of the given node
    :param node: str
    :param all_hierarchy: bool
    :param full_path: bool
    :return: list<str>
    """

    raise NotImplementedError()


@reroute
def node_parent(node, full_path=True):
    """
    Returns parent node of the given node
    :param node: str
    :param full_path: bool
    :return: str
    """

    raise NotImplementedError()


@reroute
def node_root(node, full_path=True):
    """
    Returns hierarchy root node of the given node
    :param node: str
    :param full_path: bool
    :return: str
    """

    raise NotImplementedError()


@reroute
def set_parent(node, parent):
    """
    Sets the node parent to the given parent
    :param node: str
    :param parent: str
    """

    raise NotImplementedError()


@reroute
def set_parent_to_world(node):
    """
    Parent given node to the root world node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def delete_history(node):
    """
    Removes the history of the given node
    """

    raise NotImplementedError()


@reroute
def list_node_types(type_string):
    """
    List all dependency node types satisfying given classification string
    :param type_string: str
    :return:
    """

    raise NotImplementedError()


@reroute
def list_nodes(node_name=None, node_type=None, full_path=True):
    """
    Returns list of nodes with given types. If no type, all scene nodes will be listed
    :param node_name:
    :param node_type:
    :param full_path:
    :return:  list<str>
    """

    raise NotImplementedError()


@reroute
def list_children(node, all_hierarchy=True, full_path=True, children_type=None):
    """
    Returns a list of children nodes of the given node
    :param node:
    :param all_hierarchy:
    :param full_path:
    :param children_type:
    :return:
    """

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


@reroute
def list_transforms(full_path=True):
    """
    List all transforms in current scene
    :param full_path:
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def node_inherits_transform(node):
    """
    Returns whether or not given node inherits its parent transforms
    :param node: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def set_node_inherits_transform(node, flag):
    """
    Sets whether or not given node inherits parent transforms or not
    :param node: str
    :param flag: bool
    """

    raise NotImplementedError()


@reroute
def enable_overrides(node):
    """
    Enables overrides in the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def disable_overrides(node):
    """
    Disables in the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def disable_transforms_inheritance(node, lock=False):
    """
    Disables transforms inheritance from given node
    :param node: str
    :param lock: bool
    """

    raise NotImplementedError()


@reroute
def list_node_parents(node):
    """
    Returns all parent nodes of the given Maya node
    :param node: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def create_locator(name='loc'):
    """
    Creates a new locator
    :param name: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def create_decompose_matrix_node(node_name):
    """
    Creates a new decompose matrix node
    :param node_name: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def node_transforms(node):
    """
    Returns all transforms nodes of a given node
    :param node: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def node_joints(node):
    """
    Returns all oints nodes of a give node
    :param node: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def node_shape_type(node):
    """
    Returns the type of the given shape node
    :param node: str
    :return: str
    """

    raise NotImplementedError()


# =================================================================================================================
# SHAPES
# =================================================================================================================

@reroute
def all_shapes_nodes(full_path=True):
    """
    Returns all shapes nodes in current scene
    :param full_path: bool
    :return: list<str>
    """

    raise NotImplementedError()


@reroute
def set_shape_parent(shape, transform_node):
    """
    Sets given shape parent
    :param shape: str
    :param transform_node: str
    """

    raise NotImplementedError()


@reroute
def add_node_to_parent(node, parent_node):
    """
    Add given object under the given parent preserving its local transformations
    :param node: str
    :param parent_node: str
    """

    raise NotImplementedError()


@reroute
def node_is_a_shape(node):
    """
    Returns whether or not given node is a shape one
    :param node: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def list_shapes(node, full_path=True, intermediate_shapes=False):
    """
    Returns a list of shapes of the given node
    :param node: str
    :param full_path: bool
    :param intermediate_shapes: bool
    :return: list<str>
    """

    raise NotImplementedError()


@reroute
def list_shapes_of_type(node, shape_type=None, full_path=True, intermediate_shapes=False):
    """
    Returns a list of shapes of the given node
    :param node: str
    :param shape_type: str
    :param full_path: bool
    :param intermediate_shapes: bool
    :return: list<str>
    """

    raise NotImplementedError()


@reroute
def node_has_shape_of_type(node, shape_type):
    """
    Returns whether or not given node has a shape of the given type attached to it
    :param node: str
    :param shape_type: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def list_children_shapes(node, all_hierarchy=True, full_path=True):
    """
    Returns a list of children shapes of the given node
    :param node:
    :param all_hierarchy:
    :param full_path:
    :return:
    """

    raise NotImplementedError()


@reroute
def shape_transform(shape_node):
    """
    Returns the transform parent of the given shape node
    :param shape_node: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def parent_shapes_to_transforms(shapes_list, transforms_list):
    """
    Parents given shapes into given transforms
    :param shapes_list: list(str)
    :param transforms_list: list(str)
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def rename_shapes(node):
    """
    Rename all shapes of the given node with a standard DCC shape name
    :param node: str
    """

    raise NotImplementedError()


@reroute
def combine_shapes(target_node, nodes_to_combine_shapes_of, delete_after_combine=True):
    """
    Combines all shapes of the given node
    :param target_node: str
    :param nodes_to_combine_shapes_of: str
    :param delete_after_combine: bool, Whether or not combined shapes should be deleted after
    :return: str, combined shape
    """

    raise NotImplementedError()


@reroute
def scale_shapes(target_node, scale_value, relative=False):
    """
    Scales given shapes
    :param target_node: str
    :param scale_value: float
    :return: relative, bool
    """

    raise NotImplementedError()


@reroute
def shapes_bounding_box_pivot(shapes):
    """
    Returns the bounding box pivot center point of the given meshes
    :param shapes: list(str)
    :return: list(float, float, float)
    """

    raise NotImplementedError()


# =================================================================================================================
# FILTERING
# =================================================================================================================

@reroute
def filter_nodes_by_selected_components(filter_type, nodes=None, full_path=False, **kwargs):
    """
    Function that filter nodes taking into account specific component filters
    :param filter_type: int
    :param nodes: list(str)
    :param full_path: bool
    :param kwargs:
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def filter_nodes_by_type(filter_type, search_hierarchy=False, selection_only=True, **kwargs):
    """
    Returns list of nodes in current scene filtered by given filter
    :param filter_type: str, filter used to filter nodes to edit index of
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search all scene objects or only selected ones
    :param kwargs:
    :return: list(str), list of filtered nodes
    """

    raise NotImplementedError()


# =================================================================================================================
# NAMING
# =================================================================================================================

@reroute
def get_allowed_characters():
    """
    Returns regular expression of allowed characters in current DCC
    :return: str
    """

    raise NotImplementedError()


@reroute
def node_name(node):
    """
    Returns the name of the given node
    :param node: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def node_short_name(node, **kwargs):
    """
    Returns short name of the given node
    :param node: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def node_long_name(node):
    """
    Returns long name of the given node
    :param node: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def get_mirror_name(name, center_patterns=None, left_patterns=None, right_patterns=None):
    """
    Returns mirrored name of the given name
    :param name: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def get_mirror_axis(name, mirror_plane):
    """
    Returns mirror axis of the given node name
    :param name: str
    :param mirror_plane: str, mirror plane ("YZ", "XY", "XZ")
    :return: str
    """

    raise NotImplementedError()


@reroute
def is_axis_mirrored(source_node, target_node, axis, mirror_plane):
    """
    Returns whether or not given nodes axis are mirrored
    :param source_node: str
    :param target_node: str
    :param axis: list(int)
    :param mirror_plane: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def get_color_of_side(side='C', sub_color=False):
    """
    Returns override color of the given side
    :param side: str
    :param sub_color: fool, whether to return a sub color or not
    :return:
    """

    raise NotImplementedError()


@reroute
def name_is_center(side, patterns=None):
    """
    Returns whether given side is a valid center side or not
    :param side: str
    :param patterns: list<str>
    :return: bool
    """

    raise NotImplementedError()


@reroute
def name_is_left(side, patterns=None):
    """
    Returns whether given side is a valid left side or not
    :param side: str
    :param patterns: list<str>
    :return: bool
    """

    raise NotImplementedError()


@reroute
def name_is_right(side, patterns=None):
    """
    Returns whether given side is a valid right side or not
    :param side: str
    :param patterns: list<str>
    :return: bool
    """

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


@reroute
def find_available_name(self, *args, **kwargs):
    """
    Returns an available object name in current DCC scene
    :param args: list
    :param kwargs: dict
    :return: str
    """

    raise NotImplementedError()


@reroute
def add_name_prefix(
        prefix, obj_names=None, filter_type=None, search_hierarchy=False, selection_only=True, **kwargs):
    """
    Add prefix to node name
    :param prefix: str, string to add to the start of the current node name
    :param obj_names: str or list(str), name of list of node names to rename
    :param filter_type: str, name of object type to filter the objects to apply changes ('Group, 'Joint', etc)
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search only selected objects or all scene objects
    :param kwargs:
    """

    raise NotImplementedError()


@reroute
def add_name_suffix(
        suffix, obj_names=None, filter_type=None, search_hierarchy=False, selection_only=True, **kwargs):
    """
    Add suffix to node name
    :param suffix: str, string to add to the end of the current node name
    :param obj_names: str or list(str), name of list of node names to rename
    :param filter_type: str, name of object type to filter the objects to apply changes ('Group, 'Joint', etc)
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search only selected objects or all scene objects
    :param kwargs:
    """

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


# =================================================================================================================
# NAMESPACE
# =================================================================================================================

@reroute
def node_name_without_namespace(node):
    """
    Returns the name of the given node without namespace
    :param node: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def list_namespaces():
    """
    Returns a list of all available namespaces
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def list_namespaces_from_selection():
    """
    Returns all namespaces of current selected objects
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def namespace_separator():
    """
    Returns character used to separate namespace from the node name
    :return: str
    """

    raise NotImplementedError()


@reroute
def namespace_exists(name):
    """
    Returns whether or not given namespace exists in current scene
    :param name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def unique_namespace(name):
    """
    Returns a unique namespace from the given one
    :param name: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def node_namespace(node_name, check_node=True, clean=False):
    """
    Returns namespace of the given node
    :param node_name: str
    :param check_node: bool
    :param clean: bool
    :return: str
    """

    raise NotImplementedError()


@reroute
def all_nodes_in_namespace(namespace_name):
    """
    Returns all nodes in given namespace
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def rename_namespace(current_namespace, new_namespace):
    """
    Renames namespace of the given node
    :param current_namespace: str
    :param new_namespace: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def node_parent_namespace(node):
    """
    Returns namespace of the given node parent
    :param node: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def assign_node_namespace(node, node_namespace, force_create=True, **kwargs):
    """
    Assigns a namespace to given node
    :param node: str
    :param node_namespace: str
    :param force_create: bool
    """

    raise NotImplementedError()


@reroute
def scene_namespaces():
    """
    Returns all the available namespaces in the current scene
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def change_namespace(old_namespace, new_namespace):
    """
    Changes old namespace by a new one
    :param old_namespace: str
    :param new_namespace: str
    """

    raise NotImplementedError()


# =================================================================================================================
# SCENE
# =================================================================================================================

@reroute
def get_current_time():
    """
    Returns current scene time
    :return: int
    """

    raise NotImplementedError()


@reroute
def new_scene(force=True, do_save=True):
    """
    Creates a new DCC scene
    :param force: bool, True if we want to save the scene without any prompt dialog
    :param do_save: bool, True if you want to save the current scene before creating new scene
    :return:
    """

    raise NotImplementedError()


@reroute
def scene_is_modified():
    """
    Returns whether or not current opened DCC file has been modified by the user or not
    :return: True if current DCC file has been modified by the user; False otherwise
    :rtype: bool
    """

    raise NotImplementedError()


@reroute
def new_file(force=True):
    """
    Creates a new file
    :param force: bool
    """

    raise NotImplementedError()


@reroute
def open_file(file_path, force=True):
    """
    Open file in given path
    :param file_path: str
    :param force: bool
    """

    raise NotImplementedError()


@reroute
def import_file(file_path, force=True, **kwargs):
    """
    Imports given file into current DCC scene
    :param file_path: str
    :param force: bool
    :return:
    """

    raise NotImplementedError()


@reroute
def merge_file(file_path, force=True, **kwargs):
    """
    Merges given file into current DCC scene
    :param file_path: str
    :param force: bool
    :return:
    """

    raise NotImplementedError()


@reroute
def reference_file(file_path, force=True, **kwargs):
    """
    References given file into current DCC scene
    :param file_path: str
    :param force: bool
    :param kwargs: keyword arguments
    :return:
    """

    raise NotImplementedError()


@reroute
def import_obj_file(file_path, force=True, **kwargs):
    """
    Imports OBJ file into current DCC scene
    :param file_path: str
    :param force: bool
    :param kwargs: keyword arguments
    :return:
    """

    raise NotImplementedError()


@reroute
def import_fbx_file(file_path, force=True, **kwargs):
    """
    Imports FBX file into current DCC scene
    :param file_path: str
    :param force: bool
    :param kwargs: keyword arguments
    :return:
    """

    raise NotImplementedError()


@reroute
def scene_name():
    """
    Returns the name of the current scene
    :return: str
    """

    raise NotImplementedError()


@reroute
def scene_is_modified():
    """
    Returns whether current scene has been modified or not since last save
    :return: bool
    """

    raise NotImplementedError()


@reroute
def save_current_scene(force=True, **kwargs):
    """
    Saves current scene
    :param force: bool
    """

    raise NotImplementedError()


@reroute
def export_current_selection(export_path, export_type, force=True, **kwargs):
    """
    Exports current selection to a file
    :param export_path: str
    :param export_type: str
    :param force: bool
    :param kwargs:
    :return:
    """

    raise NotImplementedError()


@reroute
def force_rename_to_save_scene():
    """
    Forces current scene to be renamed before it can be saved
    """

    raise NotImplementedError()


@reroute
def all_scene_nodes(full_path=True):
    """
    Returns a list with all scene nodes
    :param full_path: bool
    :return: list<str>
    """

    raise NotImplementedError()


@reroute
def default_scene_nodes(full_path=True):
    """
    Returns a list of nodes that are created by default by the DCC when a new scene is created
    :param full_path: bool
    :return: list<str>
    """

    raise NotImplementedError()


@reroute
def selected_nodes(full_path=True, **kwargs):
    """
    Returns a list of selected nodes
    :param full_path: bool
    :return: list<str>
    """

    raise NotImplementedError()


@reroute
def selected_nodes_in_order(full_path=True, **kwargs):
    """
    Returns a list of selected nodes in order of selection
    :param full_path: bool
    :return: list<str>
    """

    raise NotImplementedError()


@reroute
def selected_nodes_of_type(node_type, full_path=True):
    """
    Returns a list of selected nodes of given type
    :param node_type: str
    :param full_path: bool
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def selected_hilited_nodes(full_path=True):
    """
    Returns a list of selected nodes that are hilited for component selection
    :param full_path: bool
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def select_node(node, replace_selection=True, **kwargs):
    """
    Selects given object in the current scene
    :param replace_selection: bool
    :param node: str
    """

    raise NotImplementedError()


@reroute
def select_nodes_by_rgb_color(node_rgb_color, nodes_to_select=None):
    """
    Selects all nodes with the given color
    :param node_rgb_color: list(float, float, float)
    :param nodes_to_select: list(str), list of nodes to select.
    If not given, all scene nodes will be taken into account
    """

    raise NotImplementedError()


@reroute
def select_hierarchy(root=None, add=False):
    """
    Selects the hierarchy of the given node
    If no object is given current selection will be used
    :param root: str
    :param add: bool, Whether new selected objects need to be added to current selection or not
    """

    raise NotImplementedError()


@reroute
def deselect_node(node):
    """
    Deselects given node from current selection
    :param node: str
    """

    raise NotImplementedError()


@reroute
def clear_selection():
    """
    Clears current scene selection
    """

    raise NotImplementedError()


@reroute
def toggle_xray():
    """
    Toggles XRay functionality (model is displayed with transparency)
    """

    raise NotImplementedError()


@reroute
def toggle_xray_on_selection():
    """
    Toggles XRay functionality (model is displayed with transparency) on selected geometry
    """

    raise NotImplementedError()


@reroute
def clean_scene():
    """
    Cleans invalid nodes from current scene
    """

    raise NotImplementedError()


# =================================================================================================================
# TRANSFORMS
# =================================================================================================================


@reroute
def convert_translation(translation):
    """
    Converts given translation into a valid translation to be used with tpDcc
    NOTE: tpDcc uses Y up coordinate axes as the base reference axis
    :param translation: list(float, float, float)
    :return: list(float, float, float)
    """

    raise NotImplementedError()


@reroute
def convert_dcc_translation(translation):
    """
    Converts given tpDcc translation into a translation that DCC can manage
    NOTE: tpDcc uses Y up coordinate axes as the base reference axis
    :param translation: list(float, float, float)
    :return: list(float, float, float)
    """

    raise NotImplementedError()


@reroute
def convert_rotation(rotation):
    """
    Converts given rotation into a valid rotation to be used with tpDcc
    NOTE: tpDcc uses Y up coordinate axes as the base reference axis
    :param rotation: list(float, float, float)
    :return: list(float, float, float)
    """

    raise NotImplementedError()


@reroute
def convert_dcc_rotation(rotation):
    """
    Converts given rotation into a rotation that DCC can manage
    NOTE: tpDcc uses Y up coordinate axes as the base reference axis
    :param rotation: list(float, float, float)
    :return: list(float, float, float)
    """

    raise NotImplementedError()


@reroute
def convert_scale(scale):
    """
    Converts given scale into a valid rotation to be used with tpDcc
    NOTE: tpDcc uses Y up coordinate axes as the base reference axis
    :param scale: list(float, float, float)
    :return: list(float, float, float)
    """

    raise NotImplementedError()


@reroute
def convert_dcc_scale(scale):
    """
    Converts given scale into a scale that DCC can manage
    NOTE: tpDcc uses Y up coordinate axes as the base reference axis
    :param scale: list(float, float, float)
    :return: list(float, float, float)
    """

    raise NotImplementedError()


@reroute
def get_up_axis_name():
    """
    Returns the name of the current DCC up axis
    :return: str
    """

    raise NotImplementedError()


@reroute
def node_world_matrix(node):
    """
    Returns node world matrix of given node
    :param node: str
    :return: list
    """

    raise NotImplementedError()


@reroute
def set_node_world_matrix(node, world_matrix):
    """
    Sets node world matrix of given node
    :param node: str
    :param world_matrix: list
    :return: list
    """

    raise NotImplementedError()


@reroute
def node_world_space_translation(node):
    """
    Returns world translation of given node
    :param node: str
    :return: list
    """

    raise NotImplementedError()


@reroute
def node_world_bounding_box(node):
    """
    Returns node_world_bounding_box box of given node
    :param node: str
    :return:
    """

    raise NotImplementedError()


@reroute
def set_rotation_axis(node, rotation_axis):
    """
    Sets the rotation axis used by the given node
    :param node: str
    :param rotation_axis: str or int
    """

    raise NotImplementedError()


@reroute
def move_node(node, x, y, z, **kwargs):
    """
    Moves given node
    :param node: str
    :param x: float
    :param y: float
    :param z: float
    :param kwargs:
    """

    raise NotImplementedError()


@reroute
def translate_node_in_world_space(node, translation_list, **kwargs):
    """
    Translates given node with the given translation vector
    :param node: str
    :param translation_list:  list(float, float, float)
    """

    raise NotImplementedError()


@reroute
def translate_node_in_object_space(node, translation_list, **kwargs):
    """
    Translates given node with the given translation vector
    :param node: str
    :param translation_list:  list(float, float, float)
    """

    raise NotImplementedError()


@reroute
def node_world_space_rotation(node):
    """
    Returns world rotation of given node
    :param node: str
    :return: list
    """

    raise NotImplementedError()


@reroute
def rotate_node(node, x, y, z, **kwargs):
    """
    Rotates given node
    :param node: str
    :param x: float
    :param y: float
    :param z: float
    :param kwargs:
    """

    raise NotImplementedError()


@reroute
def rotate_node_in_world_space(node, rotation_list, **kwargs):
    """
    Translates given node with the given translation vector
    :param node: str
    :param rotation_list:  list(float, float, float)
    """

    raise NotImplementedError()


@reroute
def rotate_node_in_object_space(node, rotation_list, **kwargs):
    """
    Translates given node with the given translation vector
    :param node: str
    :param rotation_list:  list(float, float, float)
    """

    raise NotImplementedError()


@reroute
def node_world_space_scale(node):
    """
    Returns world scale of given node
    :param node: str
    :return: list
    """

    raise NotImplementedError()


@reroute
def scale_node(node, x, y, z, **kwargs):
    """
    Scales node
    :param node: str
    :param x: float
    :param y: float
    :param z: float
    :param kwargs:
    """

    raise NotImplementedError()


@reroute
def scale_node_in_world_space(node, scale_list, **kwargs):
    """
    Scales given node with the given vector list
    :param node: str
    :param scale_list: list(float, float, float)
    """

    raise NotImplementedError()


@reroute
def scale_node_in_object_space(node, scale_list, **kwargs):
    """
    Scales given node with the given vector list
    :param node: str
    :param scale_list: list(float, float, float)
    """

    raise NotImplementedError()


@reroute
def scale_transform_shapes(node, scale_value, **kwargs):
    """
    Scales given node by given scale value
    :param node: str
    :param scale_value: float
    :param kwargs:
    """

    raise NotImplementedError()


@reroute
def node_world_space_pivot(node):
    """
    Returns node pivot in world space
    :param node: str
    :return:
    """

    raise NotImplementedError()


@reroute
def mirror_transform(create_if_missing=False, transforms=None, left_to_right=True, **kwargs):
    """
    Mirrors the position of all transforms
    :param create_if_missing:
    :param transforms:
    :param left_to_right:
    :param kwargs:
    """

    raise NotImplementedError()


@reroute
def get_closest_transform(source_transform, targets):
    """
    Given the list of target transforms, find the closest to the source transform
    :param source_transform: str, name of the transform to test distance to
    :param targets: list<str>, list of targets to test distance against
    :return: str, name of the target in targets that is closest to source transform
    """

    raise NotImplementedError()


@reroute
def distance_between_transforms(source_transform, target_transform):
    """
    Returns the total distance between given transform nodes
    :param source_transform: str, name of the source transform node
    :param target_transform: str, name of the target transform node
    :return: float, total distance between both nodes
    """

    raise NotImplementedError()


@reroute
def rename_transform_shape_nodes(node):
    """
    Renames all shape nodes of the given transform node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def node_matrix(node):
    """
    Returns the world matrix of the given node
    :param node: str
    :return:
    """

    raise NotImplementedError()


@reroute
def set_node_matrix(node, matrix):
    """
    Sets the world matrix of the given node
    :param node: str
    :param matrix: variant
    :return:
    """

    raise NotImplementedError()


@reroute
def freeze_transforms(node, translate=True, rotate=True, scale=True, **kwargs):
    """
    Freezes the transformations of the given node and its children
    :param node: str
    :param translate: bool
    :param rotate: bool
    :param scale: str
    """

    raise NotImplementedError()


@reroute
def zero_transform_attribute_channels(node):
    """
    Sets to zero all transform attribute channels of the given node (transform rotate and scale)
    :param node: str
    """

    raise NotImplementedError()


@reroute
def create_hierarchy(transforms, replace_str=None, new_str=None):
    """
    Creates a transforms hierarchy with the given list of joints
    :param transforms: list(str)
    :param replace_str: str, if given this string will be replace with the new_str
    :param new_str: str, if given replace_str will be replace with this string
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


@reroute
def center_pivot(node):
    """
    Centers the pivot of the given node
    :param node: str
    :return:
    """

    raise NotImplementedError()


@reroute
def move_pivot_in_object_space(node, x, y, z):
    """
    Moves the pivot of the given node by the given values in object_space
    :param node: str
    :param x: float
    :param y: float
    :param z: float
    :return: float
    """

    raise NotImplementedError()


@reroute
def move_pivot_in_world_space(node, x, y, z):
    """
    Moves the pivot of the given node by the given values in world space
    :param node: str
    :param x: float
    :param y: float
    :param z: float
    :return: float
    """

    raise NotImplementedError()


@reroute
def move_pivot_to_zero(node):
    """
    Moves pivot of given node to zero (0, 0, 0 in the world)
    :param node: str
    """

    raise NotImplementedError()


@reroute
def reset_node_transforms(node, **kwargs):
    """
    Reset the transformations of the given node and its children
    :param node: str
    """

    raise NotImplementedError()


@reroute
def set_node_rotation_axis_in_object_space(node, x, y, z):
    """
    Sets the rotation axis of given node in object space
    :param node: str
    :param x: int
    :param y: int
    :param z: int
    """

    raise NotImplementedError()


@reroute
def node_bounding_box_size(node):
    """
    Returns the bounding box size of the given node
    :param node: str
    :return: float
    """

    raise NotImplementedError()


@reroute
def node_bounding_box_pivot(node):
    """
    Returns the bounding box pivot center of the given node
    :param node: str
    :return: list(float, float, float)
    """

    raise NotImplementedError()


@reroute
def match_translation(match_to, target_node):
    """
    Match translation of the given node to the translation of the target node
    :param match_to: str
    :param target_node: str
    """

    raise NotImplementedError()


@reroute
def match_rotation(match_to, target_node):
    """
    Match rotation of the given node to the rotation of the target node
    :param match_to: str
    :param target_node: str
    """

    raise NotImplementedError()


@reroute
def match_scale(match_to, target_node):
    """
    Match scale of the given node to the rotation of the target node
    :param match_to: str
    :param target_node: str
    """

    raise NotImplementedError()


@reroute
def match_translation_rotation(match_to, target_node):
    """
    Match translation and rotation of the target node to the translation and rotation of the source node
    :param match_to: str
    :param target_node: str
    """

    raise NotImplementedError()


@reroute
def match_translation_to_rotate_pivot(match_to, target_node):
    """
    Matches target translation to the source transform rotate pivot
    :param match_to: str
    :param target_node: str
    :return:
    """

    raise NotImplementedError()


@reroute
def match_transform(match_to, target_node):
    """
    Match the transform (translation, rotation and scale) of the given node to the rotation of the target node
    :param match_to: str
    :param target_node: str
    """

    raise NotImplementedError()


# =================================================================================================================
# GROUPS
# =================================================================================================================

@reroute
def create_empty_group(name='grp', parent=None):
    """
    Creates a new empty group node
    :param name: str
    :param parent: str or None
    """

    raise NotImplementedError()


@reroute
def create_buffer_group(node, **kwargs):
    """
    Creates a buffer group on top of the given node
    :param node: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def get_buffer_group(node, **kwargs):
    """
    Returns buffer group above given node
    :param node: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def group_node(node, name, parent=None):
    """
    Creates a new group and parent give node to it
    :param node: str
    :param name: str
    :param parent: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def create_empty_follow_group(target_transform, **kwargs):
    """
    Creates a new follow group above a target transform
    :param target_transform: str, name of the transform make follow
    :param kwargs:
    :return:
    """

    raise NotImplementedError()


@reroute
def create_follow_group(source_transform, target_transform, **kwargs):
    """
    Creates a group above a target transform that is constrained to the source transform
    :param source_transform: str, name of the transform to follow
    :param target_transform: str, name of the transform make follow
    :param kwargs:
    :return:
    """

    raise NotImplementedError()


# =================================================================================================================
# CONSTRAINTS
# =================================================================================================================

@reroute
def list_node_constraints(node):
    """
    Returns all constraints linked to given node
    :param node: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def create_point_constraint(source, constraint_to, **kwargs):
    """
    Creates a new point constraint
    :param source:
    :param constraint_to:
    :param kwargs:
    :return:
    """

    raise NotImplementedError()


@reroute
def create_orient_constraint(source, constraint_to, **kwargs):
    """
    Creates a new orient constraint
    :param source:
    :param constraint_to:
    :param kwargs:
    :return:
    """

    raise NotImplementedError()


@reroute
def create_scale_constraint(source, constraint_to, **kwargs):
    """
    Creates a new scale constraint
    :param source:
    :param constraint_to:
    :param kwargs:
    :return:
    """

    raise NotImplementedError()


@reroute
def create_parent_constraint(source, constraint_to, **kwargs):
    """
    Creates a new parent constraint
    :param source:
    :param constraint_to:
    :param kwargs:
    :return:
    """

    raise NotImplementedError()


@reroute
def create_aim_constraint(source, point_to, **kwargs):
    """
    Creates a new aim constraint
    :param source: str
    :param point_to: str
    """

    raise NotImplementedError()


@reroute
def create_pole_vector_constraint(control, handle):
    """
    Creates a new pole vector constraint
    :param control: str
    :param handle: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def delete_constraints(node, constraint_type=None):
    """
    Deletes all constraints applied to the given node
    :param node: str
    :param constraint_type: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def get_constraint_functions_dict():
    """
    Returns a dict that maps each constraint type with its function in DCC API
    :return: dict(str, fn)
    """

    raise NotImplementedError()


@reroute
def get_constraints():
    """
    Returns all constraints nodes in current DCC scene
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def get_constraint_targets(constraint_node):
    """
    Returns target of the given constraint node
    :param constraint_node: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def node_constraint(node, constraint_type):
    """
    Returns a constraint on the transform with the given type
    :param node: str
    :param constraint_type: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def node_constraints(node):
    """
    Returns all constraints a node is linked to
    :param node: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def delete_node_constraints(node):
    """
    Removes all constraints applied to the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def get_pole_vector_position(transform_init, transform_mid, transform_end, offset=1):
    """
    Given 3 transform (such as arm, elbow, wrist), returns a position where pole vector should be located
    :param transform_init: str, name of a transform node
    :param transform_mid: str, name of a transform node
    :param transform_end: str, name of a transform node
    :param offset: float, offset value for the final pole vector position
    :return: list(float, float, float), pole vector with offset
    """

    raise NotImplementedError()


# =================================================================================================================
# GEOMETRY
# =================================================================================================================

@reroute
def meshes_are_similar(mesh1, mesh2):
    """
    Checks whether two meshes to see if they have the same vertices, edge and face count
    :param mesh1: str
    :param mesh2: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def combine_meshes(meshes_to_combine=None, **kwargs):
    """
    Combines given meshes into one unique mesh. If no meshes given, all selected meshes will be combined
    :param meshes_to_combine: list(str) or None
    :return: str
    """

    raise NotImplementedError()


@reroute
def separate_meshes(meshes_to_separate=None, **kwargs):
    """
    Separates given meshes. If no meshes given, all selected meshes will be combined
    :param meshes_to_separate: list(str) or None
    :return: str
    """

    raise NotImplementedError()


@reroute
def node_vertex_name(mesh_node, vertex_id):
    """
    Returns the full name of the given node vertex
    :param mesh_node: str
    :param vertex_id: int
    :return: str
    """

    raise NotImplementedError()


@reroute
def total_vertices(mesh_node):
    """
    Returns the total number of vertices of the given geometry
    :param mesh_node: str
    :return: int
    """

    raise NotImplementedError()


@reroute
def node_vertex_object_space_translation(mesh_node, vertex_id=None):
    """
    Returns the object space translation of the vertex id in the given node
    :param mesh_node: str
    :param vertex_id: int
    :return:
    """

    raise NotImplementedError()


@reroute
def node_vertex_world_space_translation(mesh_node, vertex_id=None):
    """
    Returns the world space translation of the vertex id in the given node
    :param mesh_node: str
    :param vertex_id: int
    :return:
    """

    raise NotImplementedError()


@reroute
def set_node_vertex_object_space_translation(mesh_node, translate_list, vertex_id=None):
    """
    Sets the object space translation of the vertex id in the given node
    :param mesh_node: str
    :param translate_list: list
    :param vertex_id: int
    :return:
    """

    raise NotImplementedError()


@reroute
def set_node_vertex_world_space_translation(mesh_node, translate_list, vertex_id=None):
    """
    Sets the world space translation of the vertex id in the given node
    :param mesh_node: str
    :param translate_list: list
    :param vertex_id: int
    :return:
    """

    raise NotImplementedError()


@reroute
def create_nurbs_sphere(name='sphere', radius=1.0, **kwargs):
    """
    Creates a new NURBS sphere
    :param name: str
    :param radius: float
    :return: str
    """

    raise NotImplementedError()


@reroute
def create_nurbs_cylinder(name='sphere', radius=1.0, **kwargs):
    """
    Creates a new NURBS cylinder
    :param name: str
    :param radius: float
    :return: str
    """

    raise NotImplementedError()


@reroute
def create_nurbs_plane(name='plane', width=1.0, length=1.0, patches_u=1, patches_v=1, **kwargs):
    """
    Creates a new NURBS plane
    :param name: str
    :param width: float
    :param length: float
    :param patches_u: int
    :param patches_v: int
    :param kwargs:
    :return:
    """

    raise NotImplementedError()


@reroute
def convert_surface_to_bezier(surface, **kwargs):
    """
    Rebuilds given surface as a bezier surface
    :param surface: str
    :return:
    """

    raise NotImplementedError()


@reroute
def create_empty_mesh(mesh_name):
    """
    Creates a new empty mesh
    :param mesh_name:str
    :return: str
    """

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


# =================================================================================================================
# CURVES
# =================================================================================================================

@reroute
def node_is_curve(node_name):
    """
    Returns whether or not given node is a valid curve node
    :param node_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def get_curve_shapes(node_name):
    """
    Returns all shapes of the given curve
    :param node_name: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def get_curve_knots(node_name):
    """
    Returns given curve knots
    :param node_name: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def get_curve_knots_positions(curve_node_name, world_space=False):
    """
    Returns given curve knot positions
    :param curve_node_name: str
    :param world_space: bool
    :return: list(tuple(float, float, float))
    """

    raise NotImplementedError()


@reroute
def get_curve_degree(curve_node_name):
    """
    Returns given curve degree
    :param curve_node_name: str
    :return: float
    """

    raise NotImplementedError()


@reroute
def get_curve_spans(curve_node_name):
    """
    Returns given curve degree
    :param curve_node_name: str
    :return: float
    """

    raise NotImplementedError()


@reroute
def get_curve_form(curve_node_name):
    """
    Returns given curve form
    :param curve_node_name: str
    :return: int
    """

    raise NotImplementedError()


@reroute
def get_curve_cvs(curve_node_name, world_space=False):
    """
    Returns given curve CVs
    :param curve_node_name: str
    :param world_space: bool
    :return: list
    """

    raise NotImplementedError()


@reroute
def get_curve_cv_position_in_world_space(curve_node_name, cv_index):
    """
    Returns world space position of the given CV index in given curve node
    :param curve_node_name: str
    :param cv_index: int
    :return: list(float, float, float)
    """

    raise NotImplementedError()


@reroute
def get_curve_cv_position_in_object_space(curve_node_name, cv_index):
    """
    Returns object space position of the given CV index in given curve node
    :param curve_node_name: str
    :param cv_index: int
    :return: list(float, float, float)
    """

    raise NotImplementedError()


@reroute
def rebuild_curve(curve_node_name, spans, **kwargs):
    """
    Rebuilds curve with given parameters
    :param curve_node_name: str
    :param spans: int
    :param kwargs:
    :return:
    """

    raise NotImplementedError()


@reroute
def scale_curve(curve_node_name, scale_value, **kwargs):
    """
    Scales given curve by given scale value
    :param curve_node_name: str
    :param scale_value: float
    :param kwargs:
    """

    raise NotImplementedError()


@reroute
def create_circle_curve(name, **kwargs):
    """
    Creates a new circle control
    :param name: str
    :param kwargs:
    :return: str
    """

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


@reroute
def create_curve_from_transforms(transforms, spans=None, description='from_transforms'):
    """
    Creates a curve from a list of transforms. Each transform will define a curve CV
    Useful when creating a curve from a joint chain (spines/tails)
    :param transforms: list<str>, list of tranfsorms to generate the curve from. Positions will be used to place CVs
    :param spans: int, number of spans the final curve should have
    :param description: str, description to given to the curve
    :return: str name of the new curve
    """

    raise NotImplementedError()


@reroute
def create_wire(surface, curves, name='wire', **kwargs):
    """
    Creates a new wire that wires given surface to given curves
    :param surface:str
    :param curves: list(str)
    :param name:str
    :param kwargs:
    :return: str, str
    """

    raise NotImplementedError()


# =================================================================================================================
# DEFORMERS
# =================================================================================================================

@reroute
def find_deformer_by_type(geo_obj, deformer_type, **kwargs):
    """
    Given a object find a deformer with deformer_type in its history
    :param geo_obj: str, name of a mesh
    :param deformer_type: str, correspnds to the Maya deformer type (skinCluster, blendShape, etc)
    :return: list(str), names of deformers of type found in the history
    """

    raise NotImplementedError()


# =================================================================================================================
# JOINTS
# =================================================================================================================

@reroute
def create_joint(name, size=1.0, *args, **kwargs):
    """
    Creates a new joint
    :param name: str, name of the new joint
    :param size: float, size of the joint
    :return: str
    """

    raise NotImplementedError()


@reroute
def orient_joint(joint, **kwargs):
    """
    Orients given joint
    :param joint: str
    :return:
    """

    raise NotImplementedError()


@reroute
def mirror_joint(joint, mirror_plane='YZ', mirror_behavior=True, search_replace=None):
    """
    Mirrors given joint and its hierarchy
    :param joint: str
    :param mirror_plane: str
    :param mirror_behavior: bool
    :param search_replace: list(str)
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def orient_joints(joints_to_orient=None, **kwargs):
    """
    Orients joints
    :param joints_to_orient: list(str) or None
    :param kwargs:
    :return:
    """

    raise NotImplementedError()


@reroute
def zero_orient_joint(joints_to_zero_orient):
    """
    Zeroes the orientation of the given joints
    :param joints_to_zero_orient: list(str)
    """

    raise NotImplementedError()


@reroute
def start_joint_tool():
    """
    Starts the DCC tool used to create new joints/bones
    """

    raise NotImplementedError()


@reroute
def insert_joints(count, root_joint=None):
    """
    Inserts the given number of joints between the root joint and its direct child
    """

    raise NotImplementedError()


@reroute
def set_joint_local_rotation_axis_visibility(flag, joints_to_apply=None):
    """
    Sets the visibility of selected joints local rotation axis
    :param flag: bool
    :param joints_to_apply: list(str) or None
    :return: bool
    """

    raise NotImplementedError()


@reroute
def get_joint_display_size():
    """
    Returns current DCC joint display size
    :return: float
    """

    raise NotImplementedError()


@reroute
def set_joint_display_size(value):
    """
    Returns current DCC joint display size
    :param value: float
    """

    raise NotImplementedError()


@reroute
def toggle_xray_joints():
    """
    Toggles XRay joints functionality (joints are rendered in front of the geometry)
    """

    raise NotImplementedError()


@reroute
def zero_scale_joint(jnt):
    """
    Sets the given scale to zero and compensate the change by modifying the joint translation and rotation
    :param jnt: str
    """

    raise NotImplementedError()


@reroute
def set_joint_orient(jnt, orient_axis, secondary_orient_axis=None, **kwargs):
    """
    Sets the joint orientation and scale orientation so that the axis indicated by the first letter in the
     argument will be aligned with the vector from this joint to its first child joint.
    :param jnt: str
    :param orient_axis: str
    :param secondary_orient_axis: str
    :return:
    """

    raise NotImplementedError()


@reroute
def attach_joints(source_chain, target_chain, **kwargs):
    """
    Attaches a chain of joints to a matching chain
    :param source_chain: str
    :param target_chain: str
    """

    raise NotImplementedError()


@reroute
def get_side_labelling(node):
    """
    Returns side labelling of the given node
    :param node: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def set_side_labelling(node, side_label):
    """
    Sets side labelling of the given node
    :param node: str
    :param side_label: str
    """

    raise NotImplementedError()


@reroute
def get_type_labelling(node):
    """
    Returns type labelling of the given node
    :param node: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def set_type_labelling(node, type_label):
    """
    Sets type labelling of the given node
    :param node: str
    :param type_label: str
    """

    raise NotImplementedError()


@reroute
def get_other_type_labelling(node):
    """
    Returns other type labelling of the given node
    :param node: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def set_other_type_labelling(node, other_type_label):
    """
    Sets other type labelling of the given node
    :param node: str
    :param other_type_label: str
    """

    raise NotImplementedError()


@reroute
def get_draw_label_labelling(node):
    """
    Returns draw label labelling of the given node
    :param node: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def set_draw_label_labelling(node, draw_type_label):
    """
    Sets draw label labelling of the given node
    :param node: str
    :param draw_type_label: str
    """

    raise NotImplementedError()


@reroute
def get_joint_radius(node):
    """
    Returns given joint radius
    :param node: str
    :return: float
    """

    raise NotImplementedError()


@reroute
def set_joint_radius(node, radius_value):
    """
    Sets given joint radius
    :param node: str
    :param radius_value: float
    """

    raise NotImplementedError()


# =================================================================================================================
# SKIN
# =================================================================================================================

@reroute
def create_skin(mesh, influences, **kwargs):
    """
    Creates a new skin deformer node with given influences and apply it to given mesh
    :param mesh: str
    :param influences: list(str)
    :return: str
    """

    raise NotImplementedError()


@reroute
def get_skin_weights(skin_node, vertices_ids=None):
    """
    Get the skin weights of the given skin deformer node
    :param skin_node: str, name of a skin deformer node
    :param vertices_ids:
    :return: dict(int, list(float)), returns a dictionary where the key is the influence id and the
    value is the list of weights of the influence
    """

    raise NotImplementedError()


@reroute
def get_skin_blend_weights(skin_deformer):
    """
    Returns the blendWeight values on the given skin node
    :param skin_deformer: str, name of a skin deformer node
    :return: list(float), blend weight values corresponding to point order
    """

    raise NotImplementedError()


@reroute
def set_skin_blend_weights(skin_deformer, weights):
    """
    Sets the blendWeights on the skinCluster given a list of weights
    :param skin_deformer: str, name of a skinCluster deformer
    :param weights: list<float>, list of weight values corresponding to point order
    """

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


@reroute
def apply_skin_influences_from_data(skin_deformer, influences, influence_dict):
    """
    Updates skin cluster with given influences data
    :param skin_deformer: str
    :param influences: list(str), list of influence names
    :param influence_dict: dict(str, float), list that contains a map between influences and its weights
    :return:
    """

    raise NotImplementedError()


@reroute
def get_skin_influence_at_index(index, skin_deformer):
    """
    Returns which influence connect to the skin node at the given index
    :param index: int, index of an influence
    :param skin_deformer: str, name of the skin node to check the index
    :return: str, name of the influence at the given index
    """

    raise NotImplementedError()


@reroute
def get_skin_envelope(geo_obj):
    """
    Returns envelope value of the skin node in the given geometry object
    :param geo_obj: str, name of the geometry
    :return: float
    """

    raise NotImplementedError()


@reroute
def set_skin_envelope(geo_obj, envelope_value):
    """
    Sets the envelope value of teh skin node in the given geometry object
    :param geo_obj: str, name of the geometry
    :param envelope_value: float. envelope value
    """

    raise NotImplementedError()


@reroute
def set_skin_normalize_weights_mode(skin_node, index_mode):
    """
    Sets the skin normalize mode used by the given skin deformer node
    :param skin_node: str
    :param index_mode: int
    """

    raise NotImplementedError()


@reroute
def set_skin_force_normalize_weights(skin_node, flag):
    """
    Sets whether or not the skin node weights are forced to be normalized
    :param skin_node: str
    :param flag: bool
    """

    raise NotImplementedError()


@reroute
def skin_mesh_from_mesh(source_mesh, target_mesh, **kwargs):
    """
    Skins a mesh based on the skinning of another mesh
    Source mesh must be skinned and the target mesh will be skinned with the joints in the source mesh
    The skinning from the source mesh will be projected onto the target mesh
    :param source_mesh: str, name of a mesh
    :param target_mesh: str, name of a mesh
    """

    raise NotImplementedError()


# =================================================================================================================
# SELECTION GROUPS
# =================================================================================================================

@reroute
def get_selection_groups(name=None):
    """
    Returns all selection groups (sets) in current DCC scene
    :param name: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def node_is_selection_group(node):
    """
    Returns whether or not given node is a selection group (set)
    :param node: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def create_selection_group(name, empty=False):
    """
    Creates a new DCC selection group
    :param name: str
    :param empty: bool
    :return: str
    """

    raise NotImplementedError()


@reroute
def add_node_to_selection_group(node, selection_group_name, force=True):
    """
    Adds given node to selection group
    :param node: str
    :param selection_group_name: str
    :param force: bool
    :return: str
    """

    raise NotImplementedError()


@reroute
def clear_skin_weights(skin_node):
    """
    Sets all the weights on the given skinCluster to zero
    :param skin_node: str, name of a skinCluster deformer
    """

    raise NotImplementedError()


# =================================================================================================================
# ATTRIBUTES
# =================================================================================================================

@reroute
def get_valid_attribute_types():
    """
    Returns a list of valid attribute types in current DCC
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def get_valid_blendable_attribute_types():
    """
    Returns a list of valid blendable attribute types in current DCC
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def attribute_default_value(node, attribute_name):
    """
    Returns default value of the attribute in the given node
    :param node: str
    :param attribute_name: str
    :return: object
    """

    raise NotImplementedError()


@reroute
def list_attributes(node, **kwargs):
    """
    Returns list of attributes of given node
    :param node: str
    :return: list<str>
    """

    raise NotImplementedError()


@reroute
def list_user_attributes(node):
    """
    Returns list of user defined attributes
    :param node: str
    :return: list<str>
    """

    raise NotImplementedError()


@reroute
def add_bool_attribute(node, attribute_name, default_value=False, **kwargs):
    """
    Adds a new boolean attribute into the given node
    :param node: str
    :param attribute_name: str
    :param default_value: bool
    :return:
    """

    raise NotImplementedError()


@reroute
def add_integer_attribute(node, attribute_name, default_value=0, **kwargs):
    """
    Adds a new float attribute into the given node
    :param node: str
    :param attribute_name: str
    :param default_value: float
    :return:
    """

    raise NotImplementedError()


@reroute
def add_float_attribute(node, attribute_name, default_value=0.0, **kwargs):
    """
    Adds a new boolean float into the given node
    :param node: str
    :param attribute_name: str
    :param default_value: float
    :return:
    """

    raise NotImplementedError()


@reroute
def add_double_attribute(node, attribute_name, default_value=0.0, **kwargs):
    """
    Adds a new boolean float into the given node
    :param node: str
    :param attribute_name: str
    :param default_value: float
    :return:
    """

    raise NotImplementedError()


@reroute
def add_string_attribute(node, attribute_name, default_value='', **kwargs):
    """
    Adds a new string attribute into the given node
    :param node: str
    :param attribute_name: str
    :param default_value: str
    """

    raise NotImplementedError()


@reroute
def add_string_array_attribute(node, attribute_name, **kwargs):
    """
    Adds a new string array attribute into the given node
    :param node: str
    :param attribute_name: str
    """

    raise NotImplementedError()


@reroute
def add_title_attribute(node, attribute_name, **kwargs):
    """
    Adds a new title attribute into the given node
    :param node: str
    :param attribute_name: str
    :param kwargs:
    :return:
    """

    raise NotImplementedError()


@reroute
def add_message_attribute(node, attribute_name, **kwargs):
    """
    Adds a new message attribute into the given node
    :param node: str
    :param attribute_name: str
    """

    raise NotImplementedError()


@reroute
def add_enum_attribute(node, attribute_name, value, **kwargs):
    """
    Adds a new enum attribute into the given node
    :param node: str
    :param attribute_name: str
    :param value: list(str)
    :param kwargs:
    :return:
    """

    raise NotImplementedError()


@reroute
def get_enum_attribute_values(node, attribute_name):
    """
    Return list of enum attribute values in the given attribute
    :param node: str
    :param attribute_name: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def set_enum_attribute_value(node, attribute_name, value):
    """
    Return list of enum attribute values in the given attribute
    :param node: str
    :param attribute_name: str
    :param value: str
    """

    raise NotImplementedError()


@reroute
def attribute_query(node, attribute_name, **kwargs):
    """
    Returns attribute qyer
    :param node: str
    :param attribute_name: str
    :param kwargs:
    :return:
    """

    raise NotImplementedError()


@reroute
def attribute_exists(node, attribute_name):
    """
    Returns whether given attribute exists in given node
    :param node: str
    :param attribute_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def is_attribute_locked(node, attribute_name):
    """
    Returns whether given attribute is locked or not
    :param node: str
    :param attribute_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def is_attribute_connected(node, attribute_name):
    """
    Returns whether given attribute is connected or not
    :param node: str
    :param attribute_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def is_attribute_connected_to_attribute(source_node, source_attribute_name, target_node, target_attribute_name):
    """
    Returns whether given source attribute is connected or not to given target attribute
    :param source_node: str
    :param source_attribute_name: str
    :param target_node: str
    :param target_attribute_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def get_minimum_attribute_value_exists(node, attribute_name):
    """
    Returns whether or not minimum value for given attribute is defined
    :param node: str
    :param attribute_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def get_maximum_attribute_value_exists(node, attribute_name):
    """
    Returns whether or not maximum value for given attribute is defined
    :param node: str
    :param attribute_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def get_maximum_integer_attribute_value(node, attribute_name):
    """
    Returns the maximum value that a specific integer attribute has set
    :param node: str
    :param attribute_name: str
    :return: float
    """

    raise NotImplementedError()


@reroute
def set_maximum_integer_attribute_value(node, attribute_name, max_value):
    """
    Sets the maximum value that a specific integer attribute has set
    :param node: str
    :param attribute_name: str
    :param max_value: float
    """

    raise NotImplementedError()


@reroute
def get_maximum_float_attribute_value(node, attribute_name):
    """
    Returns the maximum value that a specific attribute has set
    :param node: str
    :param attribute_name: str
    :return: float
    """

    raise NotImplementedError()


@reroute
def set_maximum_float_attribute_value(node, attribute_name, max_value):
    """
    Sets the maximum value that a specific attribute has set
    :param node: str
    :param attribute_name: str
    :param max_value: float
    """

    raise NotImplementedError()


@reroute
def get_minimum_integer_attribute_value(node, attribute_name):
    """
    Returns the minimum value that a specific integer attribute has set
    :param node: str
    :param attribute_name: str
    :return: float
    """

    raise NotImplementedError()


@reroute
def set_minimum_integer_attribute_value(node, attribute_name, min_value):
    """
    Sets the minimum value that a specific integer attribute has set
    :param node: str
    :param attribute_name: str
    :param min_value: float
    """

    raise NotImplementedError()


@reroute
def get_minimum_float_attribute_value(node, attribute_name):
    """
    Returns the minimum value that a specific float attribute has set
    :param node: str
    :param attribute_name: str
    :return: float
    """

    raise NotImplementedError()


@reroute
def set_minimum_float_attribute_value(node, attribute_name, min_value):
    """
    Sets the minimum value that a specific float attribute has set
    :param node: str
    :param attribute_name: str
    :param min_value: float
    """

    raise NotImplementedError()


@reroute
def show_attribute(node, attribute_name):
    """
    Shows attribute in DCC UI
    :param node: str
    :param attribute_name: str
    """

    raise NotImplementedError()


@reroute
def hide_attribute(node, attribute_name):
    """
    Hides attribute in DCC UI
    :param node: str
    :param attribute_name: str
    """

    raise NotImplementedError()


@reroute
def hide_attributes(node, attributes_list):
    """
    Hides given attributes in DCC UI
    :param node: str
    :param attributes_list: list(str)
    """

    raise NotImplementedError()


@reroute
def lock_attributes(node, attributes_list, **kwargs):
    """
    Locks given attributes in DCC UI
    :param node: str
    :param attributes_list: list(str)
    :param kwargs:
    """

    raise NotImplementedError()


@reroute
def keyable_attribute(node, attribute_name):
    """
    Makes given attribute keyable
    :param node: str
    :param attribute_name: str
    """

    raise NotImplementedError()


@reroute
def unkeyable_attribute(node, attribute_name):
    """
    Makes given attribute unkeyable
    :param node: str
    :param attribute_name: str
    """

    raise NotImplementedError()


@reroute
def lock_attribute(node, attribute_name):
    """
    Locks given attribute in given node
    :param node: str
    :param attribute_name: str
    """

    raise NotImplementedError()


@reroute
def unlock_attribute(node, attribute_name):
    """
    Locks given attribute in given node
    :param node: str
    :param attribute_name: str
    """

    raise NotImplementedError()


@reroute
def hide_translate_attributes(node):
    """
    Hides all translate transform attributes of the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def lock_translate_attributes(node):
    """
    Locks all translate transform attributes of the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def unlock_translate_attributes(node):
    """
    Unlocks all translate transform attributes of the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def hide_rotate_attributes(node):
    """
    Hides all rotate transform attributes of the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def lock_rotate_attributes(node):
    """
    Locks all rotate transform attributes of the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def unlock_rotate_attributes(node):
    """
    Unlocks all rotate transform attributes of the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def hide_scale_attributes(node):
    """
    Hides all scale transform attributes of the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def lock_scale_attributes(node):
    """
    Locks all scale transform attributes of the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def unlock_scale_attributes(node):
    """
    Unlocks all scale transform attributes of the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def hide_visibility_attribute(node):
    """
    Hides visibility attribute of the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def lock_visibility_attribute(node):
    """
    Locks visibility attribute of the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def unlock_visibility_attribute(node):
    """
    Unlocks visibility attribute of the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def hide_scale_and_visibility_attributes(node):
    """
    Hides scale and visibility attributes of the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def lock_scale_and_visibility_attributes(node):
    """
    Locks scale and visibility attributes of the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def hide_keyable_attributes(node, **kwargs):
    """
    Hides all node attributes that are keyable
    :param node: str
    """

    raise NotImplementedError()


@reroute
def lock_keyable_attributes(node):
    """
    Locks all node attributes that are keyable
    :param node: str
    """

    raise NotImplementedError()


@reroute
def get_attribute_value(node, attribute_name):
    """
    Returns the value of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :return: variant
    """

    raise NotImplementedError()


@reroute
def get_attribute_type(node, attribute_name):
    """
    Returns the type of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :return: variant
    """

    raise NotImplementedError()


@reroute
def set_attribute_by_type(node, attribute_name, attribute_value, attribute_type):
    """
    Sets the value of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :param attribute_value: variant
    :param attribute_type: str
    """

    raise NotImplementedError()


@reroute
def set_boolean_attribute_value(node, attribute_name, attribute_value):
    """
    Sets the boolean value of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :param attribute_value: int
    :return:
    """

    raise NotImplementedError()


@reroute
def set_numeric_attribute_value(node, attribute_name, attribute_value, clamp=False):
    """
    Sets the integer value of the given attribute in the given node
   :param node: str
    :param attribute_name: str
    :param attribute_value: int
    :param clamp: bool
    :return:
    """

    raise NotImplementedError()


@reroute
def set_integer_attribute_value(node, attribute_name, attribute_value, clamp=False):
    """
    Sets the integer value of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :param attribute_value: int
    :param clamp: bool
    :return:
    """

    raise NotImplementedError()


@reroute
def set_float_attribute_value(node, attribute_name, attribute_value, clamp=False):
    """
    Sets the integer value of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :param attribute_value: int
    :param clamp: bool
    :return:
    """

    raise NotImplementedError()


@reroute
def set_string_attribute_value(node, attribute_name, attribute_value):
    """
    Sets the string value of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :param attribute_value: str
    """

    raise NotImplementedError()


@reroute
def set_float_vector3_attribute_value(node, attribute_name, attribute_value):
    """
    Sets the float vector3 value of the given attribute in the given node
    :param node: str
    :param attribute_name: str
    :param attribute_value: str
    """

    raise NotImplementedError()


@reroute
def set_attribute_value(node, attribute_name, attribute_value, **kwargs):
    """
    Sets attribute to given node
    :param node:
    :param attribute_name:
    :param attribute_value:
    :param kwargs:
    :return:
    """

    raise NotImplementedError()


@reroute
def reset_transform_attributes(node):
    """
    Reset all transform attributes of the given node
    :param node: str
    """

    raise NotImplementedError()


@reroute
def delete_attribute(node, attribute_name):
    """
    Deletes given attribute of given node
    :param node: str
    :param attribute_name: str
    """

    raise NotImplementedError()


@reroute
def delete_multi_attribute(node, attribute_name, attribute_index):
    """
    Deletes given multi attribute of given node
    :param node: str
    :param attribute_name:str
    :param attribute_index: int or str
    """

    raise NotImplementedError()


@reroute
def delete_user_defined_attributes(node):
    """
    Removes all attributes in the given node that have been created by a user
    :param node: str
    """

    raise NotImplementedError()


@reroute
def connect_attribute(source_node, source_attribute, target_node, target_attribute, force=False):
    """
    Connects source attribute to given target attribute
    :param source_node: str
    :param source_attribute: str
    :param target_node: str
    :param target_attribute: str
    :param force: bool
    """

    raise NotImplementedError()


@reroute
def disconnect_attribute(node, attribute_name):
    """
    Disconnects source attribute to given target attribute
    :param node: str
    :param attribute_name: str
    """

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


@reroute
def connect_translate(source_node, target_node):
    """
    Connects the translation of the source node into the rotation of the target node
    :param source_node: str
    :param target_node: str
    """

    raise NotImplementedError()


@reroute
def connect_rotate(source_node, target_node):
    """
    Connects the rotation of the source node into the rotation of the target node
    :param source_node: str
    :param target_node: str
    """

    raise NotImplementedError()


@reroute
def connect_scale(source_node, target_node):
    """
    Connects the scale of the source node into the rotation of the target node
    :param source_node: str
    :param target_node: str
    """

    raise NotImplementedError()


@reroute
def connect_visibility(control_and_attr, target_node, default_value=True):
    """
    Connect the visibility of the target node into an attribute
    :param control_and_attr: str, node.attribute name of a node. If it does not exists, it will ber created
    :param target_node: str, target node to connect its visibility into the attribute
    :param default_value: bool, Whether you want the visibility on/off by default
    """

    raise NotImplementedError()


@reroute
def connect_message_attribute(source_node, target_node, message_attribute, force=False):
    """
    Connects the message attribute of the input_node into a custom message attribute on target_node
    :param source_node: str, name of a node
    :param target_node: str, name of a node
    :param message_attribute: str, name of the message attribute to create and connect into. If already exists,
    :param force, Whether or not force the connection of the message attribute
    just connect
    """

    raise NotImplementedError()


@reroute
def get_message_attributes(node, **kwargs):
    """
    Returns all message attributes of the give node
    :param node: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def get_attribute_input(attribute_node, **kwargs):
    """
    Returns the input into given attribute
    :param attribute_node: str, full node and attribute (node.attribute) attribute we want to retrieve inputs of
    :param kwargs:
    :return: str
    """

    raise NotImplementedError()


@reroute
def get_message_input(node, message_attribute):
    """
    Get the input value of a message attribute
    :param node: str
    :param message_attribute: str
    :return: object
    """

    raise NotImplementedError()


@reroute
def store_world_matrix_to_attribute(node, attribute_name='origMatrix', **kwargs):
    """
    Stores world matrix of given transform into an attribute in the same transform
    :param node: str
    :param attribute_name: str
    :param kwargs:
    """

    raise NotImplementedError()


@reroute
def list_connections(node, attribute_name, **kwargs):
    """
    List the connections of the given out attribute in given node
    :param node: str
    :param attribute_name: str
    :return: list<str>
    """

    raise NotImplementedError()


@reroute
def list_connections_of_type(node, connection_type):
    """
    Returns a list of connections with the given type in the given node
    :param node: str
    :param connection_type: str
    :return: list<str>
    """

    raise NotImplementedError()


@reroute
def list_node_connections(node):
    """
    Returns all connections of the given node
    :param node: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def list_source_destination_connections(node):
    """
    Returns source and destination connections of the given node
    :param node: str
    :return: list<str>
    """

    raise NotImplementedError()


@reroute
def list_source_connections(node):
    """
    Returns source connections of the given node
    :param node: str
    :return: list<str>
    """

    raise NotImplementedError()


@reroute
def list_destination_connections(node):
    """
    Returns source connections of the given node
    :param node: str
    :return: list<str>
    """

    raise NotImplementedError()


# =================================================================================================================
# MATERIALS/SHADERS
# =================================================================================================================

@reroute
def default_shaders():
    """
    Returns a list with all thte default shadres of the current DCC
    :return: str
    """

    raise NotImplementedError()


@reroute
def create_surface_shader(shader_name, **kwargs):
    """
    Creates a new basic DCC surface shader
    :param shader_name: str
    :return: str
    """

    raise NotImplementedError()


@reroute
def apply_shader(material, node):
    """
    Applies shader to given node
    :param material: str
    :param node: str
    """

    raise NotImplementedError()


@reroute
def list_materials(skip_default_materials=False, nodes=None):
    """
    Returns a list of materials in the current scene or given nodes
    :param skip_default_materials: bool, Whether to return also standard materials or not
    :param nodes: list(str), list of nodes we want to search materials into. If not given, all scene materials
        will be retrieved
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def create_lambert_material(name='lambert', color=None, transparency=1.0, **kwargs):
    """
    Creates a new lambert material
    :param name: str
    :param color: tuple(float, float, float)
    :param transparency: float
    :param kwargs:
    :return: str
    """

    raise NotImplementedError()


# =================================================================================================================
# CAMERA
# =================================================================================================================

@reroute
def is_camera(node_name):
    """
    Returns whether given node is a camera or not
    :param node_name: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def get_all_cameras(full_path=True):
    """
    Returns all cameras in the scene
    :param full_path: bool
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def get_current_camera(full_path=True):
    """
    Returns camera currently being used in scene
    :param full_path: bool
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def look_through_camera(camera_name):
    """
    Updates DCC viewport to look through given camera
    :param camera_name: str
    :return:
    """

    raise NotImplementedError()


@reroute
def get_camera_focal_length(camera_name):
    """
    Returns focal length of the given camera
    :param camera_name: str
    :return: float
    """

    raise NotImplementedError()


# =================================================================================================================
# IK
# =================================================================================================================

@reroute
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

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


# =================================================================================================================
# CONTROLS
# =================================================================================================================

@reroute
def set_parent_controller(control, parent_controller):
    """
    Sets the parent controller of the given control
    :param control: str
    :param parent_controller: str
    """

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


@reroute
def get_control_colors():
    """
    Returns control colors available in DCC
    :return: list(float, float, float)
    """

    raise NotImplementedError()


@reroute
def set_control_color(control_node, color=None):
    """
    Sets the color of the given control node
    :param control_node: str
    :param color: int or list(float, float, float)
    """

    raise NotImplementedError()


# =================================================================================================================
# ANIMATION
# =================================================================================================================

@reroute
def get_start_frame():
    """
    Returns current start frame
    :return: int
    """

    raise NotImplementedError()


@reroute
def set_start_frame(start_frame):
    """
    Sets current start frame
    :param start_frame: int
    """

    raise NotImplementedError()


@reroute
def get_end_frame():
    """
    Returns current end frame
    :return: int
    """

    raise NotImplementedError()


@reroute
def set_end_frame(end_frame):
    """
    Sets current end frame
    :param end_frame: int
    """

    raise NotImplementedError()


@reroute
def get_current_frame():
    """
    Returns current frame set in time slider
    :return: int
    """

    raise NotImplementedError()


@reroute
def set_current_frame(frame):
    """
    Sets the current frame in time slider
    :param frame: int
    """

    raise NotImplementedError()


@reroute
def get_time_slider_range():
    """
    Return the time range from Maya time slider
    :return: list<int, int>
    """

    raise NotImplementedError()


@reroute
def set_keyframe(node, attribute_name=None, **kwargs):
    """
    Sets keyframe in given attribute in given node
    :param node: str
    :param attribute_name: str
    :param kwargs:
    :return:
    """

    raise NotImplementedError()


@reroute
def copy_key(node, attribute_name, time=None):
    """
    Copy key frame of given node
    :param node: str
    :param attribute_name: str
    :param time: bool
    :return:
    """

    raise NotImplementedError()


@reroute
def cut_key(node, attribute_name, time=None):
    """
    Cuts key frame of given node
    :param node: str
    :param attribute_name: str
    :param time: bool
    :return:
    """

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


@reroute
def offset_keyframes(node, attribute_name, start_time, end_time, duration):
    """
    Offset given node keyframes
    :param node: str
    :param attribute_name: str
    :param start_time: int
    :param end_time: int
    :param duration: float
    """

    raise NotImplementedError()


@reroute
def find_next_key_frame(node, attribute_name, start_time, end_time):
    """
    Returns next keyframe of the given one
    :param node: str
    :param attribute_name: str
    :param start_time: int
    :param end_time: int
    """

    raise NotImplementedError()


@reroute
def set_flat_key_frame(node, attribute_name, start_time, end_time):
    """
    Sets flat tangent in given keyframe
    :param node: str
    :param attribute_name: str
    :param start_time: int
    :param end_time: int
    """

    raise NotImplementedError()


@reroute
def find_first_key_in_anim_curve(curve):
    """
    Returns first key frame of the given curve
    :param curve: str
    :return: int
    """

    raise NotImplementedError()


@reroute
def find_last_key_in_anim_curve(curve):
    """
    Returns last key frame of the given curve
    :param curve: str
    :return: int
    """

    raise NotImplementedError()


@reroute
def copy_anim_curve(curve, start_time, end_time):
    """
    Copies given anim curve
    :param curve: str
    :param start_time: int
    :param end_time: int
    """

    raise NotImplementedError()


@reroute
def export_shot_animation_curves(anim_curves_to_export, export_file_path, start_frame, end_frame, **kwargs):
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

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


@reroute
def node_animation_curves(node):
    """
    Returns all animation curves of the given node
    :param node: str
    :return:
    """

    raise NotImplementedError()


@reroute
def all_animation_curves():
    """
    Returns all animation located in current DCC scene
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def all_keyframes_in_anim_curves(anim_curves=None):
    """
    Retursn al keyframes in given anim curves
    :param anim_curves: list(str)
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def key_all_anim_curves_in_frames(frames, anim_curves=None):
    """
    Inserts keyframes on all animation curves on given frame
    :param frames: list(int)
    :param anim_curves: list(str)
    """

    raise NotImplementedError()


@reroute
def remove_keys_from_animation_curves(range_to_delete, anim_curves=None):
    """
    Inserts keyframes on all animation curves on given frame
    :param range_to_delete: list(int ,int)
    :param anim_curves: list(str)
    """

    raise NotImplementedError()


@reroute
def check_anim_curves_has_fraction_keys(anim_curves, selected_range=None):
    """
    Returns whether or not given curves have or not fraction keys
    :param anim_curves: list(str)
    :param selected_range: list(str)
    :return: bool
    """

    raise NotImplementedError()


@reroute
def convert_fraction_keys_to_whole_keys(animation_curves, consider_selected_range=False):
    """
    Find keys on fraction of a frame and insert a key on the nearest whole number frame
    Useful to make sure that no keys are located on fraction of frames
    :param animation_curves: list(str)
    :param consider_selected_range: bool
    :return:
    """

    raise NotImplementedError()


@reroute
def set_active_frame_range(start_frame, end_frame):
    """
    Sets current animation frame range
    :param start_frame: int
    :param end_frame: int
    """

    raise NotImplementedError()


@reroute
def is_auto_keyframe_enabled():
    """
    Returns whether or not auto keyframe mode is enabled
    :return: bool
    """

    raise NotImplementedError()


@reroute
def set_auto_keyframe_enabled(flag):
    """
    Enables/Disables auto keyframe mode
    :param flag: bool
    """

    raise NotImplementedError()


# =================================================================================================================
# CLUSTERS
# =================================================================================================================

@reroute
def create_cluster(objects, cluster_name='cluster', **kwargs):
    """
    Creates a new cluster in the given objects
    :param objects: list(str)
    :param cluster_name: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


@reroute
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

    raise NotImplementedError()


# =================================================================================================================
# RENDER
# =================================================================================================================

@reroute
def get_playblast_formats():
    """
    Returns a list of supported formats for DCC playblast
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def get_playblast_compressions(playblast_format):
    """
    Returns a list of supported compressions for DCC playblast
    :param playblast_format: str
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def get_viewport_resolution_width():
    """
    Returns the default width resolution of the current DCC viewport
    :return: int
    """

    raise NotImplementedError()


@reroute
def get_viewport_resolution_height():
    """
    Returns the default height resolution of the current DCC viewport
    :return: int
    """

    raise NotImplementedError()


@reroute
def get_renderers():
    """
    Returns dictionary with the different renderers supported by DCC
    :return: dict(str, str)
    """

    raise NotImplementedError()


@reroute
def get_default_render_resolution_width():
    """
    Returns the default width resolution of the current DCC render settings
    :return: int
    """

    raise NotImplementedError()


@reroute
def get_default_render_resolution_height():
    """
    Returns the default height resolution of the current DCC render settings
    :return: int
    """

    raise NotImplementedError()


@reroute
def get_default_render_resolution_aspect_ratio():
    """
    Returns the default resolution aspect ratio of the current DCC render settings
    :return: float
    """

    raise NotImplementedError()


@reroute
def open_render_settings():
    """
    Opens DCC render settings options
    """

    raise NotImplementedError()


@reroute
def all_scene_shots():
    """
    Returns all shots in current scene
    :return: list(str)
    """

    raise NotImplementedError()


@reroute
def shot_is_muted(shot_node):
    """
    Returns whether or not given shot node is muted
    :param shot_node: str
    :return: bool
    """

    raise NotImplementedError()


@reroute
def shot_track_number(shot_node):
    """
Returns track where given shot node is located
    :param shot_node: str
    :return: int
    """

    raise NotImplementedError()


@reroute
def shot_start_frame_in_sequencer(shot_node):
    """
    Returns the start frame of the given shot in sequencer time
    :param shot_node: str
    :return: int
    """

    raise NotImplementedError()


@reroute
def shot_end_frame_in_sequencer(shot_node):
    """
    Returns the end frame of the given shot in sequencer time
    :param shot_node: str
    :return: int
    """

    raise NotImplementedError()


@reroute
def get_pre_hold(shot_node):
    """
    Returns shot prehold value
    :param shot_node: str
    :return: int
    """

    raise NotImplementedError()


@reroute
def get_post_hold(shot_node):
    """
    Returns shot posthold value
    :param shot_node: str
    :return: int
    """

    raise NotImplementedError()


@reroute
def shot_scale(shot_node):
    """
    Returns the scale of the given shot
    :param shot_node: str
    :return: int
    """

    raise NotImplementedError()


@reroute
def shot_start_frame(shot_node):
    """
    Returns the start frame of the given shot
    :param shot_node: str
    :return: int
    """

    raise NotImplementedError()


@reroute
def set_shot_start_frame(shot_node, start_frame):
    """
    Sets the start frame of the given shot
    :param shot_node: str
    :param start_frame: int
    :return: int
    """

    raise NotImplementedError()


@reroute
def shot_end_frame(shot_node):
    """
    Returns the end frame of the given shot
    :param shot_node: str
    :return: int
    """

    raise NotImplementedError()


@reroute
def set_shot_end_frame(shot_node, end_frame):
    """
    Sets the end frame of the given shot
    :param shot_node: str
    :param end_frame: int
    :return: int
    """

    raise NotImplementedError()


@reroute
def shot_camera(shot_node):
    """
    Returns camera associated given node
    :param shot_node: str
    :return: str
    """

    raise NotImplementedError()


# =================================================================================================================
# HUMAN IK (HIK)
# =================================================================================================================


@reroute
def get_scene_hik_characters():
    """
    Returns all HumanIK characters in current scene
    :return: list(str)
    """

    raise NotImplementedError()


# =================================================================================================================
# DECORATORS
# =================================================================================================================

@reroute
def undo_decorator():
    """
    Returns undo decorator for current DCC
    """

    raise NotImplementedError()


@reroute
def repeat_last_decorator(command_name=None):
    """
    Returns repeat last decorator for current DCC
    """

    raise NotImplementedError()


@reroute
def enable_wait_cursor():
    """
    Enables wait cursor in current DCC
    """

    raise NotImplementedError()


@reroute
def disable_wait_cursor():
    """
    Enables wait cursor in current DCC
    """

    raise NotImplementedError()


@reroute
def suspend_refresh_decorator():
    """
    Returns suspend refresh decorator for current DCC
    """

    raise NotImplementedError()


@reroute
def restore_selection_decorator():
    """
    Selects again the objects that were selected before executing the decorated function
    """

    raise NotImplementedError()
