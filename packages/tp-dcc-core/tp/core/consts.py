#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains constant definitions for tpDcc
"""

# =======~============ GENERAL
PROJECTS_NAME = 'project.json'
PREFERENCES_FOLDER = 'preferences'          # name of the folder where packages store preferences files.
INTERFACE_FOLDER = 'interface'              # folder where package interface will be located within preferences folder.
PREFERENCE_EXTENSION = '.pref'              # extension used by tpDcc Tools framework preference files.
PREFERENCE_SETTINGS_KEY = 'settings'

# =======~============ TOOLS
TOOL_IDENTIFIER = 'ID'
TOOL_VERSION_IDENTIFIER = 'VERSION'


class Axis(object):
    X = 'x'
    Y = 'y'
    Z = 'z'


class Environment(object):
    DEV = 'development'
    PROD = 'production'


# =================== TYPES
class WrapperTypes(object):
    Shape = 0
    Transform = 1
    Pointer = 2


class ObjectTypes(object):
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


class CallbackTypes(object):
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


class UnitSystem(object):
    Inches = 0
    Feet = 1
    Millimeters = 2
    Centimeters = 3
    Meters = 4
    Kilometers = 5
    Yards = 6
    Miles = 7


class MaterialAttributeTypes(object):
    Int = 0
    Float = 1
    String = 2
    Path = 3
    Color = 4
    Bool = 5


class MaterialTypes(object):
    Standard = 0


SIDE_PATTERNS = {
    'center': ['C', 'c', 'Center', 'ct', 'center', 'middle', 'm'],
    'left': ['L', 'l', 'Left', 'left', 'lf'],
    'right': ['R', 'r', 'Right', 'right', 'rt']
}
