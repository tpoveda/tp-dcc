#!#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains constants definitions for tp-dcc-maya
"""

from enum import Enum


class DebugLevels(Enum):
    Disabled = 0
    Low = 1
    Mid = 2
    High = 3


class ScriptLanguages(Enum):
    Python = 0
    MEL = 1
    CSharp = 2
    CPlusPlus = 3
    Manifest = 4


class DialogResult(object):
    Yes = 'Yes'
    No = 'No'
    Cancel = 'No'
    Close = 'No'


SIDE_LABELS = ['Center', 'Left', 'Right', 'None']
TYPE_LABELS = [
    'None', 'Root', 'Hip', 'Knee', 'Foot', 'Toe', 'Spine', 'Neck', 'Head', 'Collar', 'Shoulder', 'Elbow', 'Hand',
    'Finger', 'Thumb', 'PropA', 'PropB', 'PropC', 'Other', 'Index Finger', 'Middle Finger', 'Ring Finger',
    'Pinky Finger', 'Extra Finger', 'Big Toe', 'Index Toe', 'Middle Toe', 'Ring Toe', 'Pinky Toe', 'Foot Thumb'
]

AXES = ['x', 'y', 'z']
ROTATION_AXES = ['xyz', 'yzx', 'zxy', 'xzy', 'yxz', 'zyx']
TRANSLATION_ATTR_NAME = 'translate'
ROTATION_ATTR_NAME = 'rotate'
SCALE_ATT_NAME = 'scale'
