#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya utility functions and classes
"""

import os
import sys
import stat
import shutil
import platform
from functools import partial
from typing import Tuple, Dict, Callable, Any

import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as OpenMaya

from tp.core import log
from tp.common.python import helpers, path
from tp.maya.cmds import time, gui

logger = log.tpLogger


class SelectionMasks(object):
    """
    https://help.autodesk.com/cloudhelp/2017/ENU/Maya-Tech-Docs/CommandsPython/filterExpand.html
    """

    Handle = 0
    NurbsCurves = 9
    NurbsSurfaces = 10
    NurbsCurvesOnSurface = 11
    Polygon = 12
    LocatorXYZ = 22
    OrientationLocator = 23
    LocatorUV = 24
    ControlVertices = 28
    CVs = 28
    EditPoints = 30
    PolygonVertices = 31
    PolygonEdges = 32
    PolygonFace = 34
    PolygonUVs = 35
    SubdivisionMeshPoints = 36
    SubdivisionMeshEdges = 37
    SubdivisionMeshFaces = 38
    CurveParameterPoints = 39
    CurveKnot = 40
    SurfaceParameterPoints = 41
    SurfaceKnot = 42
    SurfaceRange = 43
    TrimSurfaceEdge = 44
    SurfaceIsoparms = 45
    LatticePoints = 46
    Particles = 47
    ScalePivots = 49
    RotatePivots = 50
    SelectHandles = 51
    SubdivisionSurface = 68
    PolygonVertexFace = 70
    NurbsSurfaceFace = 72
    SubdivisionMeshUVs = 73


def get_version():
    """
    Returns version of the executed Maya, or 0 if not Maya version is found.

    :return: version of Maya.
    :rtype: int
    """

    return int(cmds.about(version=True))


def api_version():
    """
    Returns the Maya API version.

    :return: version of Maya API.
    :rtype: int
    """

    return int(cmds.about(api=True))


def float_version():
    """
    Returns the Maya version as a float value.

    :return: version of Maya as float value.
    :rtype: float
    """

    return mel.eval('getApplicationVersionAsFloat')


def maya_location(maya_version):
    """
    Returns the absolute path where Maya is installed.

    :param int maya_version: Maya version to find.
    :return: folder path to the Maya install folder.
    :rtype: str
    """

    location = os.environ.get('MAYA_LOCATION', '')
    if location:
        return location

    if platform.system() == 'Windows':
        location = os.path.join('C:\\', 'Program Files', 'Autodesk', 'Maya%s' % maya_version)
    elif platform.system() == 'Darwin':
        return os.path.join('/Applications', 'Autodesk', 'maya{0}'.format(maya_version), 'Maya.app', 'Contents')
    else:
        location = os.path.join('usr', 'autodesk', 'maya{0}- x64'.format(maya_version))
        
    return location


def maya_script_paths():
    """
    Returns a list of Maya script paths, retrieved from MAYA_SCRIPT_PATH environment variable.

    :return: list of script paths.
    :rtype: list(str)
    """

    try:
        return os.environ['MAYA_SCRIPT_PATH'].split(os.path.pathsep)
    except KeyError:
        logger.debug('Could not find MAYA_SCRIPT_PATH in environment')
        raise


def maya_module_paths():
    """
    Returns a list of Maya module paths, retrieved from MAYA_MODULE_PATH environment variable.

    :return: list of module paths.
    :rtype: list(str)
    """

    try:
        return os.environ['MAYA_MODULE_PATH'].split(os.path.pathsep)
    except KeyError:
        logger.debug('Could not find MAYA_MODULE_PATH in environment')
        raise


def maya_plugin_paths():
    """
    Returns a list of Maya plugin paths, retrieved from MAYA_PLUG_IN_PATH environment variable.

    :return: list of plugin paths.
    :rtype: list(str)
    """

    try:
        return os.environ['MAYA_PLUG_IN_PATH'].split(os.path.pathsep)
    except KeyError:
        logger.debug('Could not find MAYA_PLUG_IN_PATH in environment')
        raise


def python_path():
    """
    Returns a list of paths, retrieved from PYTHONPATH environment variable.

    :return: list of Python paths.
    :rtype: list(str)
    """

    try:
        return os.environ['PYTHONPATH'].split(os.path.pathsep)
    except KeyError:
        logger.debug('Could not find PYTHONPATH in environment')
        raise


def maya_icon_path():
    """
    Returns a list of Maya icon paths, retrieved from XBMLANGPATH environment variable.

    :return: list of icon paths.
    :rtype: list(str)
    """

    try:
        return os.environ['XBMLANGPATH'].split(os.path.pathsep)
    except KeyError:
        logger.debug('Could not find XBMLANGPATH in environment')
        raise


def environment():
    """
    Returns Maya main environment and returns info as a dictionary.

    :return: Maya environment data.
    :rtype: dict
    """

    return {
        'MAYA_SCRIPT_PATH': maya_script_paths(),
        'MAYA_PLUG_IN_PATH': maya_plugin_paths(),
        'MAYA_MODULE_IN_PATH': maya_module_paths(),
        'PYTHONPATH': python_path(),
        'XBMLANGPATH': maya_icon_path(),
        'sys.path': sys.path.split(os.pathsep),
        'PATH': os.environ['PATH'].split(os.pathsep)
    }


def print_environment():
    """
    Logs Maya environment to the logger.
    """

    logger.info("\nMAYA_SCRIPT_PATHs are: \n %s" % maya_script_paths())
    logger.info("\nMAYA_PLUG_IN_PATHs are: \n %s" % maya_plugin_paths())
    logger.info("\nMAYA_MODULE_PATHs are: \n %s" % maya_module_paths())
    logger.info("\nPYTHONPATHs are: \n %s" % python_path())
    logger.info("\nXBMLANGPATHs are: \n %s" % maya_icon_path())
    logger.info("\nsys.paths are: \n %s" % sys.path.split(os.pathsep))


def mayapy(maya_version):
    """
    Returns the location of the Mayapy executable path for the given Maya version.

    :param int maya_version: Maya version to work with.
    :return: Myaapy executable absolute path.
    :rtype: str
    """

    pyexe = os.path.join(maya_location(maya_version), 'bin', 'mayapy')
    if platform.system() == 'Windows':
        pyexe += '.exe'

    return pyexe


def is_standalone():
    """
    Returns whether Maya is being executed in batch mode.

    :return: True if Maya is being executed in batch mode; False otherwise.
    :rtype: bool
    """

    return not hasattr(cmds, 'about') or cmds.about(batch=True)


def up_axis():
    """
    Returns up axis of the Maya scene
    :return: str, ('y' or 'z')
    """

    return cmds.upAxis(axis=True, query=True)


def create_group(name, nodes=None, world=False, parent=None):
    """
    Creates new group with the given names
    :param name: str, name of the group
    :param nodes: bool
    :param world: bool
    :param parent: str, parent node of the group
    :return:
    """

    if not name:
        return

    nodes = helpers.force_list(nodes)

    name = helpers.force_list(name)
    parent = helpers.force_list(parent)
    if parent:
        parent = parent[0]

    found = list()

    for n in name:
        if not cmds.objExists(n):
            if world:
                if nodes:
                    n = cmds.group(*nodes, name=n, world=True)
                else:
                    n = cmds.group(name=n, empty=True, world=True)
            else:
                if nodes:
                    n = cmds.group(*nodes, name=n)
                else:
                    n = cmds.group(name=n, empty=True)

        if parent and cmds.objExists(parent):
            actual_parent = cmds.listRelatives(n, p=True)
            if actual_parent:
                actual_parent = actual_parent[0]
            if parent != actual_parent:
                cmds.parent(n, parent)

        found.append(n)

    return found


def selection_iterator():
    """
    Returns an iterator of Maya objects currently selected
    :return: iterator
    """

    selection = OpenMaya.MSelectionList()
    OpenMaya.MGlobal.getActiveSelectionList(selection)
    selection_iter = OpenMaya.MItSelectionList(selection)
    while not selection_iter.isDone():
        obj = OpenMaya.MObject()
        selection_iter.getDependNode(obj)
        yield obj
        selection_iter.next()


def selection_to_list():
    """
    Returns the current maya selection in a list form
    :return: list(variant)
    """

    selected_objs = (cmds.ls(sl=True, flatten=True))
    return selected_objs


def objects_of_mtype_iterator(object_type):
    """
    Returns a iterator of Maya objects filtered by object type
    :param object_type: enum value used to identify Maya objects
    :return: SceneObject:_abstract_to_native_object_type
    """

    if not isinstance(object_type, (tuple, list)):
        object_type = [object_type]
    for obj_type in object_type:
        obj_iter = OpenMaya.MItDependencyNodes(obj_type)
        while not obj_iter.isDone():
            yield obj_iter.thisNode()
            obj_iter.next()


def current_time_unit():

    """
    Returns the current time unit name
    :return:  str, name of the current fps
    """

    return cmds.currentUnit(query=True, time=True)


def set_current_time_unit(time_unit):
    """
    Sets current time unit
    :param time_unit: STR
    """
    return cmds.currentUnit(time=time_unit)


def create_mtime(value, unit=None):

    """
    Constructs an OpenMaya.MTime with the provided value. If unit is None, unit is set to the
    current unit setting in Maya
    :param value: time value
    :param unit: int, Time unit value
    :return: OpenMaya.MTime
    """

    if unit is None:
        unit = current_time_unit()
    return OpenMaya.MTime(value, time.fps_to_mtime[unit])


def mfn_apy_type_map():

    """
    Returns a dictionary mapping all apiType values to their apiTypeStr
    A few values have duplicate keys so the names are inside a list.
    :return: dict, A dict mapping int values to list of OpenMaya.MFn constant names
    """

    out = dict()
    for name in dir(OpenMaya.MFn):
        value = getattr(OpenMaya.MFn, name)
        if name.startswith('k'):
            out.setdefault(value, []).append(name)

    return out


def maya_version():
    """
    Returns version of the executed Maya, or 0 if not Maya version is found
    @returns: int, Version of Maya
    """

    return int(cmds.about(version=True))


def maya_api_version():
    """
    Returns the Maya version
    @returns: int, Version of Maya
    """

    return int(cmds.about(api=True))


def global_variable(var_name):
    """
    Returns the value of a MEL global variable
    @param var_name: str, name of the MEL global variable
    """

    return mel.eval("$tempVar = {0}".format(var_name))


def maya_python_interpreter_path():
    """
    Returns the path to Maya Python interpretet path
    :return: str
    """

    return str(sys.executable).replace('maya.exe', 'mayapy.exe')


def error(message, prefix=''):
    """
    Shows an error message on output
    :param message: str, Error message to show
    :param prefix: str, Prefix to the errors message
    """

    if len(message) > 160:
        print(message)
        cmds.error(prefix + ' | ' + 'Check Maya Console for more information!')
        return False
    cmds.error(prefix + ' | {0}'.format(message))
    return False


def warning(message, prefix=''):
    """
    Shows a warning message on output
    :param message: str, Warning message to show
    :param prefix: str, Prefix to the warning message
    """

    if len(message) > 160:
        print(message)
        cmds.warning(prefix + ' | ' + 'Check Maya Console for more information!')
        return True
    cmds.warning(prefix + ' | {0}'.format(message))
    return True


def add_button_to_current_shelf(enable=True,
                                name="tpShelfButton",
                                width=234,
                                height=34,
                                manage=True,
                                visible=True,
                                annotation="",
                                label="",
                                image1="commandButton.png",
                                style="iconAndTextCentered",
                                command="",
                                check_if_already_exists=True):
    """
    Adds a new button to the current selected Maya shelf
    :param enable: bool, True if the new button should be enabled or not
    :param name:  str, Name of the button
    :param width: int, Width for the new button
    :param height: int, Height for the new window
    :param manage: bool
    :param visible: bool, True if the button should be vsiible
    :param annotation: str, Annotation for the new shelf button
    :param label: str, Label of the button
    :param image1: str, Image name of the button icon
    :param style: str, style for the shelf button
    :param command: str, command that the button should execute
    :param check_if_already_exists: bool, True if you want to check if that button already exists in the shelf
    """

    if check_if_already_exists:
        curr_shelf = gui.current_shelf()
        shelf_buttons = cmds.shelfLayout(curr_shelf, ca=True, query=True)
        for shelf_btn in shelf_buttons:
            if cmds.control(shelf_btn, query=True, docTag=True):
                doc_tag = cmds.control(shelf_btn, query=True, docTag=True)
                if doc_tag == name:
                    return
    cmds.shelfButton(
        parent=gui.current_shelf(), enable=True, width=34, height=34, manage=True,
        visible=True, annotation=annotation, label=label, image1=image1, style=style, command=command)


def set_tool(name):
    """
    Sets the current tool (translate, rotate, scale) that is being used inside Maya viewport
    @param name: str, name of the tool to select: 'move', 'rotate', or 'scale'
    """

    context_lookup = {
        'move': "$gMove",
        'rotate': "$gRotate",
        'scale': "$gSacle"
    }
    tool_context = global_variable(context_lookup[name])
    cmds.setToolTo(tool_context)


def in_view_log(color='', *args):
    """
    Logs some info into the Maya viewport
    :param color: color to use in the text
    :param args: text concatenation to show
    """

    text = ''
    for item in args:
        text += ' '
        text += str(item)

    if color != '':
        text = "<span style=\"color:{0};\">{1}</span>".format(color, text)

    cmds.inViewMessage(amg=text, pos='topCenter', fade=True, fst=1000, dk=True)


def display_info(info_msg):
    """
    Displays info message in Maya
    :param info_msg: str, info text to display
    """

    info_msg = info_msg.replace('\n', '\ntp:\t\t')
    OpenMaya.MGlobal.displayInfo('tp:\t\t' + info_msg)
    logger.debug('\n{}'.format(info_msg))


def display_warning(warning_msg):
    """
    Displays warning message in Maya
    :param warning_msg: str, warning text to display
    """

    warning_msg = warning_msg.replace('\n', '\ntp:\t\t')
    OpenMaya.MGlobal.displayWarning('tp:\t\t' + warning_msg)
    logger.warning('\n{}'.format(warning_msg))


def display_error(error_msg):
    """
    Displays error message in Maya
    :param error_msg: str, error text to display
    """

    error_msg = error_msg.replace('\n', '\ntp:\t\t')
    OpenMaya.MGlobal.displayError('tp:\t\t' + error_msg)
    logger.error('\n{}'.format(error_msg))


def file_has_student_line(filename):
    """
    Returns True if the given Maya file has a student license on it
    :param filename: str
    :return: bool
    """

    if not os.path.exists(filename):
        logger.error('File "{}" does not exists!'.format(filename))
        return False

    if filename.endswith('.mb'):
        logger.warning('Student License Check is not supported in binary files!')
        return True

    with open(filename, 'r') as f:
        lines = f.readlines()

    for line in lines:
        if 'createNode' in line:
            return False
        if 'fileInfo' in line and 'student' in line:
            return True

    return False


def clean_student_line(filename=None):
    """
    Clean the student line from the given Maya file name
    :param filename: str
    """

    changed = False

    if not filename:
        filename = cmds.file(query=True, sn=True)

    if not os.path.exists(filename):
        logger.error('File "{}" does not exists!'.format(filename))
        return False

    if not file_has_student_line(filename=filename):
        logger.info('File is already cleaned: no student line found!')
        return False

    if not filename.endswith('.ma'):
        logger.info('Maya Binary files cannot be cleaned!')
        return False

    with open(filename, 'r') as f:
        lines = f.readlines()
    step = len(lines) / 4

    no_student_filename = filename[:-3] + '.no_student.ma'
    with open(no_student_filename, 'w') as f:
        step_count = 0
        for line in lines:
            step_count += 1
            if 'fileInfo' in line:
                if 'student' in line:
                    changed = True
                    continue
            f.write(line)
            if step_count > step:
                logger.debug('Updating File: {}% ...'.format(100 / (len(lines) / step_count)))
                step += step

    if changed:
        os.chmod(filename, stat.S_IWUSR | stat.S_IREAD)
        shutil.copy2(no_student_filename, filename)

        try:
            os.remove(no_student_filename)
        except Exception as exc:
            logger.warning('Error while cleanup no student file process files ... >> {}'.format(exc))
            return False

        logger.info('Student file cleaned successfully!')

    return True


def is_plugin_loaded(plugin_name):
    """
    Return whether given plugin is loaded or not
    :param plugin_name: str
    :return: bool
    """

    return cmds.pluginInfo(plugin_name, query=True, loaded=True)


def load_plugin(plugin_name, quiet=True):
    """
    Loads plugin with the given name (full path)
    :param plugin_name: str, name or path of the plugin to load
    :param quiet: bool, Whether to show info to user that plugin has been loaded or not
    """

    if is_plugin_loaded(plugin_name):
        return True

    try:
        cmds.loadPlugin(plugin_name, quiet=quiet)
    except Exception as exc:
        if not quiet:
            logger.error('Impossible to load plugin: {} | {}'.format(plugin_name, exc))
        return False

    return True


def unload_plugin(plugin_name):
    """
    Unloads the given plugin
    :param plugin_name: str
    """

    if not is_plugin_loaded(plugin_name):
        return False

    return cmds.unloadPlugin(plugin_name)


def add_trusted_plugin_location_path(allowed_path):
    """
    Adds the given path to the list of trusted plugin locations.

    :param str allowed_path: path to add do trusted plugin locations list.
    :return: True if the operation was successfull; False otherwise.
    :rtype: bool
    """

    if float_version() < 2022:
        return False

    allowed_path = path.clean_path(allowed_path)
    allowed_paths = cmds.optionVar(query='SafeModeAllowedlistPaths')
    if allowed_path in allowed_paths:
        return False

    cmds.optionVar(stringValueAppend=('SafeModeAllowedlistPaths', allowed_path))

    return True


def remove_trusted_plugin_location_path(allowed_path):
    """
    Removes the given path from the list of trusted plugin locations.

    :param str allowed_path: path to remove from trusted plugin locations list.
    :return: True if the operation was successfull; False otherwise.
    :rtype: bool
    """

    if float_version() < 2022:
        return False

    allowed_path = path.clean_path(allowed_path)
    allowed_paths = cmds.optionVar(query='SafeModeAllowedlistPaths')
    if allowed_path not in allowed_paths:
        return False

    path_index = allowed_paths.index(allowed_path)
    cmds.optionVar(removeFromArray=('SafeModeAllowedlistPaths', path_index))

    return True


def list_old_plugins():
    """
    Returns a list of old plugins in the current scene
    :return: list(str)
    """

    return cmds.unknownPlugin(query=True, list=True)


def remove_old_plugin(plugin_name):
    """
    Removes given old plugin from current scene
    :param plugin_name: str
    """

    return cmds.unknownPlugin(plugin_name, remove=True)


def project_rule(rule):
    """
    Get the full path of the rule of the project
    :param rule: str
    :return: str
    """

    workspace = cmds.workspace(query=True, rootDirectory=True)
    workspace_folder = cmds.workspace(fileRuleEntry=rule)
    if not workspace_folder:
        logger.warning(
            'File Rule Entry "{}" has no value, please check if the rule name is typed correctly!'.format(rule))

    return os.path.join(workspace, workspace_folder)


def create_mel_procedure(python_fn, args=(), return_type=''):
    """
    Creates a valid MEL procedure to be called that invokes Python function.
    Two procedures with a temporary name are created in global MEL and Python spaces, for this reason no parameter
    passing is supported
    :param python_fn:
    :param args:
    :param return_type:
    """

    # create procedure name
    proc_name = 'tpDccProc{}{}'.format(id(python_fn), python_fn.__name__)

    # create link to method in global Python space
    sys.modules['__main__'].__dict__[proc_name] = python_fn

    # create MEL procedure
    mel_args = ",".join(map(lambda a: "%s $%s" % (a[0], a[1]), args))
    python_args = ','.join(map(lambda a: '\'"+$%s+"\'' % a[1], args))
    return_str = 'return' if return_type != '' else ''
    mel_code = 'global proc %s %s(%s) { %s python ("%s(%s)");  }' % (
        return_type, proc_name, mel_args, return_str, proc_name, python_args)
    mel.eval(mel_code)

    return proc_name


def mel_global_variable_value(variable_name):
    """
    Returns the value of the given MEL global variable.

    :param str variable_name: name of the MEL global varaible value of we want to retrieve.
    :return: value of MEL global variable.
    :rtype: str
    """

    return mel.eval('${} = ${};'.format(variable_name, variable_name))


def create_repeat_command_for_function(fn: Callable, *args: Tuple, **kwargs: Dict):
    """
    Helper function that updates Maya repeat last command with the given function.

    :param Callable fn: function to repeat.
    :param Tuple args: tuple of positional arguments to pass to the function.
    :param Dict kwargs: keyword arguments to pass to the function.
    ..note:: only functions/staticmethods/classmethods are supported.
    ..code-block:: python
        def test_fn(first_arg, keyword_arg=None):
            print(first_arg, keyword)

        create_repeat_command_for_function(test_fn, 'hello world', keyword=0)
    """

    _RepeatCommandStorage.set_repeat_command(fn, args, kwargs)
    command = f'python(\"import {__name__};{__name__}._RepeatCommandStorage.run_current_repeat_command()\");'
    cmds.repeatLast(addCommand=command, addCommandLabel=fn.__name__)


def create_repeat_last_command_decorator(fn: Callable) -> Any:
    """
    Decoratof function which updates Maya repeat command with the decorated function.

    :param Callable fn: function to repeat.
    :return: result output.
    :rtype: Any
    ..note:: all args/kwargs of the decorated function will be passed to the repeat command.
    ..note:: only functions/staticmethods/classmethods are supported.
    """

    def _inner_function(*args: Tuple, **kwargs: Dict):
        result = fn(*args, **kwargs)
        create_repeat_command_for_function(fn, *args, **kwargs)
        return result

    return _inner_function


class _RepeatCommandStorage:
    """
    Internal storage internal class for commands to repeat.
    """

    _FUNCTION_TO_REPEAT = None          # type: partial

    @staticmethod
    def run_current_repeat_command():
        """
        Executes the current repeat function if any.
        """

        fn = _RepeatCommandStorage._FUNCTION_TO_REPEAT
        if fn is not None:
            fn()

    @staticmethod
    def set_repeat_command(fn: Callable, args: Tuple, kwargs: Dict):
        """
        Sets the current repeat function.

        :param Callable fn: repeat function.
        :param Tuple args: arguments to pass to the repeat function when executing.
        :param Dict kwargs: keyword arguments to pass to the repeat function when executing.
        """

        _RepeatCommandStorage._FUNCTION_TO_REPEAT = partial(fn, *args, **kwargs)

    @staticmethod
    def flush():
        """
        Clears out the current repeat function.
        """

        _RepeatCommandStorage._FUNCTION_TO_REPEAT = None
