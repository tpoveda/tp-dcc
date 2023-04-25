#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC functionality for standalone applications
"""

import logging

from tp.core import log, dcc
from tp.common.python import helpers, decorators

logger = log.tpLogger


# =================================================================================================================
# GENERAL
# =================================================================================================================

def get_name():
    """
    Returns the name of the DCC
    :return: str
    """

    return dcc.Dccs.Standalone


def get_extensions():
    """
    Returns supported extensions of the DCC
    :return: list(str)
    """

    return []


def get_version():
    """
    Returns version of the DCC
    :return: int
    """

    return 0


def get_version_name():
    """
    Returns version of the DCC
    :return: str
    """

    return '0.0.0'


def is_batch():
    """
    Returns whether DCC is being executed in batch mode or not
    :return: bool
    """

    return False


def execute_deferred(fn):
    """
    Executes given function in deferred mode
    """

    return fn()


def deferred_function(fn, *args, **kwargs):
    """
    Calls given function with given arguments in a deferred way
    :param fn:
    :param args: list
    :param kwargs: dict
    """

    return fn(*args, **kwargs)


def is_component_mode():
    """
    Returns whether current DCC selection mode is component mode or not
    :return: bool
    """

    return False


def enable_component_selection():
    """
    Enables DCC component selection mode
    """

    return False


def is_plugin_loaded(plugin_name):
    """
    Return whether given plugin is loaded or not
    :param plugin_name: str
    :return: bool
    """

    return False


def load_plugin(plugin_path, quiet=True):
    """
    Loads given plugin
    :param plugin_path: str
    :param quiet: bool
    """

    return False


def unload_plugin(plugin_path):
    """
    Unloads the given plugin
    :param plugin_path: str
    """

    return False


def list_old_plugins():
    """
    Returns a list of old plugins in the current scene
    :return: list<str>
    """

    return list()


def remove_old_plugin(plugin_name):
    """
    Removes given old plugin from current scene
    :param plugin_name: str
    """

    return False


def set_workspace(workspace_path):
    """
    Sets current workspace to the given path
    :param workspace_path: str
    """

    return False


def warning(message):
    """
    Prints a warning message
    :param message: str
    :return:
    """

    logger.warning(message)


def error(message):
    """
    Prints a error message
    :param message: str
    :return:
    """

    logger.error(message)


# =================================================================================================================
# GUI
# =================================================================================================================

def get_dpi(value=1):
    """
    Returns current DPI used by DCC
    :param value: float
    :return: float
    """

    return 1.0


def get_dpi_scale(value):
    """
    Returns current DPI scale used by DCC
    :return: float
    """

    return 1.0


def get_main_window():
    """
    Returns Qt object that references to the main DCC window
    :return:
    """

    return None


def get_main_menubar():
    """
    Returns Qt object that references to the main DCC menubar
    :return:
    """

    return None


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

    from tp.common.qt.widgets import messagebox
    from Qt.QtWidgets import QDialogButtonBox

    new_buttons = None
    if button:
        if helpers.is_string(button):
            if button == 'Yes':
                new_buttons = QDialogButtonBox.Yes
            elif button == 'No':
                new_buttons = QDialogButtonBox.No
        elif isinstance(button, (tuple, list)):
            for i, btn in enumerate(button):
                if i == 0:
                    if btn == 'Yes':
                        new_buttons = QDialogButtonBox.Yes
                    elif btn == 'No':
                        new_buttons = QDialogButtonBox.No
                else:
                    if btn == 'Yes':
                        new_buttons = new_buttons | QDialogButtonBox.Yes
                    elif btn == 'No':
                        new_buttons = new_buttons | QDialogButtonBox.No
    if new_buttons:
        buttons = new_buttons
    else:
        buttons = button or QDialogButtonBox.Yes | QDialogButtonBox.No

    if cancel_button:
        if helpers.is_string(cancel_button):
            if cancel_button == 'No':
                buttons = buttons | QDialogButtonBox.No
            elif cancel_button == 'Cancel':
                buttons = buttons | QDialogButtonBox.Cancel
        else:
            buttons = buttons | QDialogButtonBox.Cancel

    return messagebox.MessageBox.question(None, title=title, text=message, buttons=buttons)


def select_file_dialog(title, start_directory=None, pattern=None):
    """
    Shows select file dialog
    :param title: str
    :param start_directory: str
    :param pattern: str
    :return: str
    """

    from Qt.QtWidgets import QFileDialog

    if not pattern:
        pattern = 'All Files (*.*)'

    return QFileDialog.getOpenFileName(None, title, start_directory, pattern)[0]


def select_folder_dialog(title, start_directory=None):
    """
    Shows select folder dialog
    :param title: str
    :param start_directory: str
    :return: str
    """

    from Qt.QtWidgets import QFileDialog

    return QFileDialog.getExistingDirectory(None, title, start_directory)


def save_file_dialog(title, start_directory=None, pattern=None):
    """
    Shows save file dialog
    :param title: str
    :param start_directory: str
    :param pattern: str
    :return: str
    """

    from Qt.QtWidgets import QFileDialog

    return QFileDialog.getSaveFileName(None, title, start_directory, pattern)[0]

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

    return node


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

    return None


def scene_is_modified():
    """
    Returns whether or not current opened DCC file has been modified by the user or not
    :return: True if current DCC file has been modified by the user; False otherwise
    :rtype: bool
    """

    return True


def new_file(force=True):
    """
    Creates a new file
    :param force: bool
    """

    pass


def open_file(file_path, force=True):
    """
    Open file in given path
    :param file_path: str
    :param force: bool
    """

    pass


def import_file(file_path, force=True, **kwargs):
    """
    Imports given file into current DCC scene
    :param file_path: str
    :param force: bool
    :return:
    """

    pass


def merge_file(file_path, force=True, **kwargs):
    """
    Merges given file into current DCC scene
    :param file_path: str
    :param force: bool
    :return:
    """

    pass


def reference_file(file_path, force=True, **kwargs):
    """
    References given file into current DCC scene
    :param file_path: str
    :param force: bool
    :param kwargs: keyword arguments
    :return:
    """

    pass


def import_obj_file(file_path, force=True, **kwargs):
    """
    Imports OBJ file into current DCC scene
    :param file_path: str
    :param force: bool
    :param kwargs: keyword arguments
    :return:
    """

    pass


def import_fbx_file(file_path, force=True, **kwargs):
    """
    Imports FBX file into current DCC scene
    :param file_path: str
    :param force: bool
    :param kwargs: keyword arguments
    :return:
    """

    pass


def scene_name():
    """
    Returns the name of the current scene
    :return: str
    """

    return ''


# def object_exists(node):
#     """
#     Returns whether given object exists or not
#     :return: bool
#     """
#
#     return False
#
#
# def object_type(node):
#     """
#     Returns type of given object
#     :param node: str
#     :return: str
#     """
#
#     return None
#
#
# def check_object_type(node, node_type, check_sub_types=False):
#     """
#     Returns whether give node is of the given type or not
#     :param node: str
#     :param node_type: str
#     :param check_sub_types: bool
#     :return: bool
#     """
#
#     return False
#
#
# def node_is_empty(node, *args, **kwargs):
#     """
#     Returns whether given node is an empty one.
#     In Maya, an emtpy node is the one that is not referenced, has no child transforms, has no custom attributes
#     and has no connections
#     :param node: str
#     :return: bool
#     """
#
#     return True
#
#
# def node_is_transform(node):
#     """
#     Returns whether or not given node is a transform node
#     :param node: str
#     :return: bool
#     """
#
#     return False
#
#
# def all_scene_objects(full_path=True):
#     """
#     Returns a list with all scene nodes
#     :param full_path: bool
#     :return: list<str>
#     """
#
#     return list()
#
#
# def rename_node(node, new_name, **kwargs):
#     """
#     Renames given node with new given name
#     :param node: str
#     :param new_name: str
#     :return: str
#     """
#
#     return False
#
#
# def rename_transform_shape_nodes(node):
#     """
#     Renames all shape nodes of the given transform node
#     :param node: str
#     """
#
#     return False
#
#
# def show_object(node):
#     """
#     Shows given object
#     :param node: str
#     """
#
#     return False
#
#
# def select_node(node, replace_selection=True, **kwargs):
#     """
#     Selects given object in the current scene
#     :param replace_selection: bool
#     :param node: str
#     """
#
#     return False
#
#
# def select_hierarchy(root=None, add=False):
#     """
#     Selects the hierarchy of the given node
#     If no object is given current selection will be used
#     :param root: str
#     :param add: bool, Whether new selected objects need to be added to current selection or not
#     """
#
#     return False
#
#
# def deselect_node(node):
#     """
#     Deselects given node from current selection
#     :param node: str
#     """
#
#     return False
#
#
# def clear_selection():
#     """
#     Clears current scene selection
#     """
#
#     return False
#
#
# def duplicate_object(node, name='', only_parent=False, return_roots_only=False):
#     """
#     Duplicates given object in current scene
#     :param node: str
#     :param name: str
#     :param only_parent: bool, If True, only given node will be duplicated (ignoring its children)
#     :param return_roots_only: bool, If True, only the root nodes of the new hierarchy will be returned
#     :return: list(str)
#     """
#
#     return False
#
#
# def delete_object(node):
#     """
#     Removes given node from current scene
#     :param node: str
#     """
#
#     return False
#
#
# def clean_construction_history(node):
#     """
#     Removes the construction history of the given node
#     :param node: str
#     """
#
#     return False

def selected_nodes(full_path=True, **kwargs):
    """
    Returns a list of selected nodes
    :param full_path: bool
    :return: list<str>
    """

    return list()


# def selected_nodes_of_type(node_type, full_path=True):
#     """
#     Returns a list of selected nodes of given type
#     :param node_type: str
#     :param full_path: bool
#     :return: list(str)
#     """
#
#     return list()
#
#
# def selected_hilited_nodes(full_path=True):
#     """
#     Returns a list of selected nodes that are hilited for component selection
#     :param full_path: bool
#     :return: list(str)
#     """
#
#     return list()

# def get_control_colors():
#     """
#     Returns control colors available in DCC
#     :return: list(float, float, float)
#     """
#
#     return []
#
#
# def get_all_fonts():
#     """
#     Returns all fonts available in DCC
#     :return: list(str)
#     """
#
#     # TODO: We can use Qt to retrieve system fonts
#     return []

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

    return dict()


def dcc_to_tpdcc_types():
    """
    # Returns a dictionary that provides a mapping between Dcc object types and tpDcc object types
    :return:
    """

    pass


def dcc_to_tpdcc_str_types():
    """
    Returns a dictionary that provides a mapping between Dcc string object types and tpDcc object types
    :return:
    """

    pass


def node_tpdcc_type(self, node, as_string=False):
    """
    Returns the DCC object type as a string given a specific tpDcc object type
    :param node: str
    :param as_string: bool
    :return: str
    """

    pass


def root_node():
    """
    Returns DCC scene root node
    :return: str
    """

    return None


def node_exists(node_name):
    """
    Returns whether given object exists or not
    :param node_name: str
    :return: bool
    """

    return False


# =================================================================================================================
# JOINTS
# =================================================================================================================

def get_joint_radius(node):
    """
    Sets given joint radius
    :param node: str
    :return: float
    """

    return 1.0


def set_joint_radius(node, radius_value):
    """
    Sets given joint radius
    :param node: str
    :param radius_value: float
    """

    pass


# =================================================================================================================
# CONTROLS
# =================================================================================================================

def set_parent_controller(control, parent_controller):
    """
    Sets the parent controller of the given control
    :param control: str
    :param parent_controller: str
    """

    pass


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

    pass


def get_control_colors():
    """
    Returns control colors available in DCC
    :return: list(float, float, float)
    """

    return list()


def set_control_color(control_node, color=None):
    """
    Sets the color of the given control node
    :param control_node: str
    :param color: int or list(float, float, float)
    """

    pass


# =================================================================================================================
# ANIMATION
# =================================================================================================================

def get_start_frame():
    """
    Returns current start frame
    :return: int
    """

    return 0


def get_end_frame():
    """
    Returns current end frame
    :return: int
    """

    return 0


def get_current_frame():
    """
    Returns current frame set in time slider
    :return: int
    """

    return 0


def set_current_frame(frame):
    """
    Sets the current frame in time slider
    :param frame: int
    """

    pass


def get_time_slider_range():
    """
    Return the time range from Maya time slider
    :return: list<int, int>
    """

    return [0, 0]


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


def restore_selection_decorator():
    """
    Returns decorators that selects again the objects that were selected before executing the decorated function
    """

    return decorators.empty_decorator