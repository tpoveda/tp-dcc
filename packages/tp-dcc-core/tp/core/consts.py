#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains constant definitions for tpDcc
"""

# ======================================================================================================================
# General Constants
# ======================================================================================================================

PREFERENCES_FOLDER = 'preferences'          # name of the folder where packages store preferences files.
INTERFACE_FOLDER = 'interface'              # folder where package interface will be located within preferences folder.
PREFERENCE_EXTENSION = '.pref'              # extension used by tpDcc Tools framework preference files.
PREFERENCE_SETTINGS_KEY = 'settings'


# ======================================================================================================================
# Tools Constants
# ======================================================================================================================

TOOL_IDENTIFIER = 'ID'
TOOL_VERSION_IDENTIFIER = 'VERSION'


# ======================================================================================================================
# Dcc Agnostic Constants
# ======================================================================================================================


class WrapperTypes:
    """
    Enumerator that defines available DCC agnostic wrapper types
    """

    Shape = 0
    Transform = 1
    Pointer = 2


class ObjectTypes:
    """
    Enumerator that defines available DCC agnostic object types
    """

    Generic = 0
    Sphere = 1
    Box = 2
    Cylinder = 3
    Capsule = 4
    Geometry = 5
    Model = 6
    PolyMesh = 7
    NurbsSurface = 8
    Curve = 9
    Light = 10
    Camera = 11
    Group = 12
    Null = 13
    Bone = 14
    Particle = 15
    Network = 16
    Circle = 17
    Biped = 18


class CallbackTypes:
    """
    Enumerator that defines available DCC agnostic callback types
    """

    Shutdown = 'Shutdown'
    Tick = 'Tick'
    ScenePreCreated = 'ScenePreCreated'
    ScenePostCreated = 'ScenePostCreated'
    SceneNewRequested = 'SceneNewRequested'
    SceneNewFinished = 'SceneNewFinished'
    SceneSaveRequested = 'SceneSaveRequested'
    SceneSaveFinished = 'SceneSaveFinished'
    SceneOpenRequested = 'SceneOpenRequested'
    SceneOpenFinished = 'SceneOpenFinished'
    UserPropertyPreChanged = 'UserPropertyPreChanged'
    UserPropertyPostChanged = 'UserPropertyPostChanged'
    NodeSelect = 'NodeSelect'
    NodeAdded = 'NodeAdded'
    NodeDeleted = 'NodeDeleted'
    ReferencePreLoaded = 'ReferencePreLoaded'
    ReferencePostLoaded = 'ReferencePostLoaded'
