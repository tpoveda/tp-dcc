#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with directories and files in 3ds Max
"""

from pymxs import runtime as rt


def get_current_project():
    """
    Returns current project path
    :return: str
    """

    return rt.pathConfig.getCurrentProjectFolder()


def set_current_project(project_path):
    """
    Sets current project path
    :param project_path: str
    """

    return rt.pathConfig.setCurrentProjectFolder(project_path)


# NOTE: Valid names for Max directories (we should include functions for all of them)
# font | #Scene | #import | #Export | #help | #expression | #preview | #image | #Sound | #plugcfg | #maxstart
# | #vpost | #drivers | #autoback | #matlib | #scripts | #startupScripts | #defaults | #renderPresets | #ui
# | #maxroot | #renderoutput | #animations | #archives | #Photometric | #renderassets | #userScripts | #userMacros
# | #userStartupScripts | #temp | #userIcons | #maxData | #downloads | #proxies | #assemblies | #pageFile
# | #hardwareShadersCache | #plugcfg_ln | #ui_ln | #autodeskcloud | #privateExchangeStoreInstallPath
# | #publicExchangeStoreInstallPath | #privatePluginPackageInstallPath | #publicPluginPackageInstallPath
# | #userStartupTemplates | #macroScripts | #web | #maxSysIcons | #cfd | #systemImage | #systemPhotometric
# | #systemSound | #systemCFD | #fluidSimulations | #userSettings | #userTools
def get_scenes_directory():
    return rt.pathConfig.getDir(rt.Name('scene'))


def get_previews_directory():
    return rt.pathConfig.getDir(rt.Name('preview'))


def select_file_dialog(title, start_directory=None, pattern=None):
    """
    Shows select file dialog
    :param title: str
    :param start_directory: str
    :param pattern: str
    :return: str
    """

    start_directory = start_directory or ''
    return rt.getOpenFileName(caption=rt.Name(title), filename=start_directory, types=pattern)


def select_folder_dialog(title, start_directory=None):
    """
    Shows select folder dialog
    :param title: str
    :param start_directory: str
    :return: str
    """

    raise NotImplementedError()


def save_file_dialog(title, start_directory=None, pattern=None):
    """
    Shows save file dialog
    :param title: str
    :param start_directory: str
    :param pattern: str
    :return: str
    """

    start_directory = start_directory or ''
    return rt.getSaveFileName(caption=rt.Name(title), filename=start_directory, types=pattern)
