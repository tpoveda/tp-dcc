#!#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes to work with HumanIK
"""

import os

import maya.cmds
import maya.mel
import maya.app.hik.retargeter

from tp.core import log, dcc
from tp.common.python import path as path_utils
from tp.maya.cmds import helpers

logger = log.tpLogger


class HIKBoneNames(object):
    Hips = 'Hips'
    HipsTranslation = 'HipsTranslation'
    Head = 'Head'
    LeftArm = 'LeftArm'
    LeftArmRoll = 'LeftArmRoll'
    LeftFoot = 'LeftFoot'
    LeftForeArm = 'LeftForeArm'
    LeftForeArmRoll = 'LeftForeArmRoll'
    LeftHand = 'LeftHand'
    LeftFingerBase = 'LeftFingerBase'
    LeftHandIndex1 = 'LeftHandIndex1'
    LeftHandIndex2 = 'LeftHandIndex2'
    LeftHandIndex3 = 'LeftHandIndex3'
    LeftHandIndex4 = 'LeftHandIndex4'
    LeftHandMiddle1 = 'LeftHandMiddle1'
    LeftHandMiddle2 = 'LeftHandMiddle2'
    LeftHandMiddle3 = 'LeftHandMiddle3'
    LeftHandMiddle4 = 'LeftHandMiddle4'
    LeftHandPinky1 = 'LeftHandPinky1'
    LeftHandPinky2 = 'LeftHandPinky2'
    LeftHandPinky3 = 'LeftHandPinky3'
    LeftHandPinky4 = 'LeftHandPinky4'
    LeftHandRing1 = 'LeftHandRing1'
    LeftHandRing2 = 'LeftHandRing2'
    LeftHandRing3 = 'LeftHandRing3'
    LeftHandRing4 = 'LeftHandRing4'
    LeftHandThumb1 = 'LeftHandThumb1'
    LeftHandThumb2 = 'LeftHandThumb2'
    LeftHandThumb3 = 'LeftHandThumb3'
    LeftHandThumb4 = 'LeftHandThumb4'
    LeftInHandThumb = 'LeftInHandThumb'
    LeftInHandIndex = 'LeftInHandIndex'
    LeftInHandMiddle = 'LeftInHandMiddle'
    LeftInHandPinky = 'LeftInHandPinky'
    LeftInHandRing = 'LeftInHandRing'
    LeftInHandExtraFinger = 'LeftInHandExtraFinger'
    LeftHandExtraFinger1 = 'LeftHandExtraFinger1'
    LeftHandExtraFinger2 = 'LeftHandExtraFinger2'
    LeftHandExtraFinger3 = 'LeftHandExtraFinger3'
    LeftHandExtraFinger4 = 'LeftHandExtraFinger4'
    LeftLeg = 'LeftLeg'
    LeftLegRoll = 'LeftLegRoll'
    LeftShoulder = 'LeftShoulder'
    LeftToeBase = 'LeftToeBase'
    LeftUpLeg = 'LeftUpLeg'
    LeftUpLegRoll = 'LeftUpLegRoll'
    Neck = 'Neck'
    Neck1 = 'Neck1'
    Neck2 = 'Neck2'
    Neck3 = 'Neck3'
    Neck4 = 'Neck4'
    Neck5 = 'Neck5'
    Neck6 = 'Neck6'
    Neck7 = 'Neck7'
    Neck8 = 'Neck8'
    Neck9 = 'Neck9'
    Reference = 'Reference'
    RightArm = 'RightArm'
    RightArmRoll = 'RightArmRoll'
    RightFoot = 'RightFoot'
    RightForeArm = 'RightForeArm'
    RightForeArmRoll = 'RightForeArmRoll'
    RightHand = 'RightHand'
    RightFingerBase = 'RightFingerBase'
    RightHandIndex1 = 'RightHandIndex1'
    RightHandIndex2 = 'RightHandIndex2'
    RightHandIndex3 = 'RightHandIndex3'
    RightHandIndex4 = 'RightHandIndex4'
    RightHandMiddle1 = 'RightHandMiddle1'
    RightHandMiddle2 = 'RightHandMiddle2'
    RightHandMiddle3 = 'RightHandMiddle3'
    RightHandMiddle4 = 'RightHandMiddle4'
    RightHandPinky1 = 'RightHandPinky1'
    RightHandPinky2 = 'RightHandPinky2'
    RightHandPinky3 = 'RightHandPinky3'
    RightHandPinky4 = 'RightHandPinky4'
    RightHandRing1 = 'RightHandRing1'
    RightHandRing2 = 'RightHandRing2'
    RightHandRing3 = 'RightHandRing3'
    RightHandRing4 = 'RightHandRing4'
    RightHandThumb1 = 'RightHandThumb1'
    RightHandThumb2 = 'RightHandThumb2'
    RightHandThumb3 = 'RightHandThumb3'
    RightHandThumb4 = 'RightHandThumb4'
    RightInHandThumb = 'RightInHandThumb'
    RightInHandIndex = 'RightInHandIndex'
    RightInHandMiddle = 'RightInHandMiddle'
    RightInHandPinky = 'RightInHandPinky'
    RightInHandRing = 'RightInHandRing'
    RightInHandExtraFinger = 'RightInHandExtraFinger'
    RightHandExtraFinger1 = 'LeftHandExtraFinger1'
    RightHandExtraFinger2 = 'RightHandExtraFinger2'
    RightHandExtraFinger3 = 'RightHandExtraFinger3'
    RightHandExtraFinger4 = 'RightHandExtraFinger4'
    RightLeg = 'RightLeg'
    RightLegRoll = 'RightLegRoll'
    RightShoulder = 'RightShoulder'
    RightToeBase = 'RightToeBase'
    RightUpLeg = 'RightUpLeg'
    RightUpLegRoll = 'RightUpLegRoll'
    Spine = 'Spine'
    Spine1 = 'Spine1'
    Spine2 = 'Spine2'
    Spine3 = 'Spine3'
    Spine4 = 'Spine4'
    Spine5 = 'Spine5'
    Spine6 = 'Spine6'
    Spine7 = 'Spine7'
    Spine8 = 'Spine8'
    Spine9 = 'Spine9'
    LeftFootThumb1 = 'LeftFootThumb1'
    LeftFootThumb2 = 'LeftFootThumb2'
    LeftFootThumb3 = 'LeftFootThumb3'
    LeftFootThumb4 = 'LeftFootThumb4'
    LeftFootIndex1 = 'LeftFootIndex1'
    LeftFootIndex2 = 'LeftFootIndex2'
    LeftFootIndex3 = 'LeftFootIndex3'
    LeftFootIndex4 = 'LeftFootIndex4'
    LeftFootMiddle1 = 'LeftFootMiddle1'
    LeftFootMiddle2 = 'LeftFootMiddle2'
    LeftFootMiddle3 = 'LeftFootMiddle3'
    LeftFootMiddle4 = 'LeftFootMiddle4'
    LeftFootRing1 = 'LeftFootRing1'
    LeftFootRing2 = 'LeftFootRing2'
    LeftFootRing3 = 'LeftFootRing3'
    LeftFootRing4 = 'LeftFootRing4'
    LeftFootPinky1 = 'LeftFootPinky1'
    LeftFootPinky2 = 'LeftFootPinky2'
    LeftFootPinky3 = 'LeftFootPinky3'
    LeftFootPinky4 = 'LeftFootPinky4'
    LeftFootExtraFinger1 = 'LeftFootExtraFinger1'
    LeftFootExtraFinger2 = 'LeftFootExtraFinger2'
    LeftFootExtraFinger3 = 'LeftFootExtraFinger3'
    LeftFootExtraFinger4 = 'LeftFootExtraFinger4'
    RightFootThumb1 = 'RightFootThumb1'
    RightFootThumb2 = 'RightFootThumb2'
    RightFootThumb3 = 'RightFootThumb3'
    RightFootThumb4 = 'RightFootThumb4'
    RightFootIndex1 = 'RightFootIndex1'
    RightFootIndex2 = 'RightFootIndex2'
    RightFootIndex3 = 'RightFootIndex3'
    RightFootIndex4 = 'RightFootIndex4'
    RightFootMiddle1 = 'RightFootMiddle1'
    RightFootMiddle2 = 'RightFootMiddle2'
    RightFootMiddle3 = 'RightFootMiddle3'
    RightFootMiddle4 = 'RightFootMiddle4'
    RightFootRing1 = 'RightFootRing1'
    RightFootRing2 = 'RightFootRing2'
    RightFootRing3 = 'RightFootRing3'
    RightFootRing4 = 'RightFootRing4'
    RightFootPinky1 = 'RightFootPinky1'
    RightFootPinky2 = 'RightFootPinky2'
    RightFootPinky3 = 'RightFootPinky3'
    RightFootPinky4 = 'RightFootPinky4'
    RightFootExtraFinger1 = 'RightFootExtraFinger1'
    RightFootExtraFinger2 = 'RightFootExtraFinger2'
    RightFootExtraFinger3 = 'RightFootExtraFinger3'
    RightFootExtraFinger4 = 'RightFootExtraFinger4'
    LeftInFootThumb = 'LeftInFootThumb ='
    LeftInFootIndex = 'LeftInFootIndex'
    LeftInFootMiddle = 'LeftInFootMiddle'
    LeftInFootRing = 'LeftInFootRing'
    LeftInFootPinky = 'LeftInFootPinky'
    LeftInFootExtraFinger = 'LeftInFootExtraFinger'
    RightInFootThumb = 'RightInFootThumb'
    RightInFootIndex = 'RightInFootIndex'
    RightInFootMiddle = 'RightInFootMiddle'
    RightInFootRing = 'RightInFootRing'
    RightInFootPinky = 'RightInFootPinky'
    RightInFootExtraFinger = 'RightInFootExtraFinger'
    LeftShoulderExtra = 'LeftShoulderExtra'
    RightShoulderExtra = 'RightShoulderExtra'
    LeafLeftUpLegRoll1 = 'LeafLeftUpLegRoll1'
    LeafLeftLegRoll1 = 'LeafLeftLegRoll1'
    LeafRightUpLegRoll1 = 'LeafRightUpLegRoll1'
    LeafRightLegRoll1 = 'LeafRightLegRoll1'
    LeafLeftArmRoll1 = 'LeafLeftArmRoll1'
    LeafLeftForeArmRoll1 = 'LeafLeftForeArmRoll1'
    LeafRightArmRoll1 = 'LeafRightArmRoll1'
    LeafRightForeArmRoll1 = 'LeafRightForeArmRoll1'
    LeafLeftUpLegRoll2 = 'LeafLeftUpLegRoll2'
    LeafLeftLegRoll2 = 'LeafLeftLegRoll2'
    LeafRightUpLegRoll2 = 'LeafRightUpLegRoll2'
    LeafRightLegRoll2 = 'LeafRightLegRoll2'
    LeafLeftArmRoll2 = 'LeafLeftArmRoll2'
    LeafLeftForeArmRoll2 = 'LeafLeftForeArmRoll2'
    LeafRightArmRoll2 = 'LeafRightArmRoll2'
    LeafRightForeArmRoll2 = 'LeafRightForeArmRoll2'
    LeafLeftUpLegRoll3 = 'LeafLeftUpLegRoll3'
    LeafLeftLegRoll3 = 'LeafLeftLegRoll3'
    LeafRightUpLegRoll3 = 'LeafRightUpLegRoll3'
    LeafRightLegRoll3 = 'LeafRightLegRoll3'
    LeafLeftArmRoll3 = 'LeafLeftArmRoll3'
    LeafLeftForeArmRoll3 = 'LeafLeftForeArmRoll3'
    LeafRightArmRoll3 = 'LeafRightArmRoll3'
    LeafRightForeArmRoll3 = 'LeafRightForeArmRoll3'
    LeafLeftUpLegRoll4 = 'LeafLeftUpLegRoll4'
    LeafLeftLegRoll4 = 'LeafLeftLegRoll4'
    LeafRightUpLegRoll4 = 'LeafRightUpLegRoll4'
    LeafRightLegRoll4 = 'LeafRightLegRoll4'
    LeafLeftArmRoll4 = 'LeafLeftArmRoll4'
    LeafLeftForeArmRoll4 = 'LeafLeftForeArmRoll4'
    LeafRightArmRoll4 = 'LeafRightArmRoll4'
    LeafRightForeArmRoll4 = 'LeafRightForeArmRoll4'
    LeafLeftUpLegRoll5 = 'LeafLeftUpLegRoll5'
    LeafLeftLegRoll5 = 'LeafLeftLegRoll5'
    LeafRightUpLegRoll5 = 'LeafRightUpLegRoll5'
    LeafRightLegRoll5 = 'LeafRightLegRoll5'
    LeafLeftArmRoll5 = 'LeafLeftArmRoll5'
    LeafLeftForeArmRoll5 = 'LeafLeftForeArmRoll5'
    LeafRightArmRoll5 = 'LeafRightArmRoll5'
    LeafRightForeArmRoll5 = 'LeafRightForeArmRoll5'


HIK_BONES = {
    HIKBoneNames.Reference: {'index': 0},
    HIKBoneNames.Hips: {'index': 1},
    HIKBoneNames.LeftUpLeg: {'index': 2},
    HIKBoneNames.LeftLeg: {'index': 3},
    HIKBoneNames.LeftFoot: {'index': 4},
    HIKBoneNames.RightUpLeg: {'index': 5},
    HIKBoneNames.RightLeg: {'index': 6},
    HIKBoneNames.RightFoot: {'index': 7},
    HIKBoneNames.Spine: {'index': 8},
    HIKBoneNames.LeftArm: {'index': 9},
    HIKBoneNames.LeftForeArm: {'index': 10},
    HIKBoneNames.LeftHand: {'index': 11},
    HIKBoneNames.RightArm: {'index': 12},
    HIKBoneNames.RightForeArm: {'index': 13},
    HIKBoneNames.RightHand: {'index': 14},
    HIKBoneNames.Head: {'index': 15},
    HIKBoneNames.LeftToeBase: {'index': 16},
    HIKBoneNames.RightToeBase: {'index': 17},
    HIKBoneNames.LeftShoulder: {'index': 18},
    HIKBoneNames.RightShoulder: {'index': 19},
    HIKBoneNames.Neck: {'index': 20},
    HIKBoneNames.LeftFingerBase: {'index': 21},
    HIKBoneNames.RightFingerBase: {'index': 22},
    HIKBoneNames.Spine1: {'index': 23},
    HIKBoneNames.Spine2: {'index': 24},
    HIKBoneNames.Spine3: {'index': 25},
    HIKBoneNames.Spine4: {'index': 26},
    HIKBoneNames.Spine5: {'index': 27},
    HIKBoneNames.Spine6: {'index': 28},
    HIKBoneNames.Spine7: {'index': 29},
    HIKBoneNames.Spine8: {'index': 30},
    HIKBoneNames.Spine9: {'index': 31},
    HIKBoneNames.Neck1: {'index': 32},
    HIKBoneNames.Neck2: {'index': 33},
    HIKBoneNames.Neck3: {'index': 34},
    HIKBoneNames.Neck4: {'index': 35},
    HIKBoneNames.Neck5: {'index': 36},
    HIKBoneNames.Neck6: {'index': 37},
    HIKBoneNames.Neck7: {'index': 38},
    HIKBoneNames.Neck8: {'index': 39},
    HIKBoneNames.Neck9: {'index': 40},
    HIKBoneNames.LeftUpLegRoll: {'index': 41},
    HIKBoneNames.LeftLegRoll: {'index': 42},
    HIKBoneNames.RightUpLegRoll: {'index': 43},
    HIKBoneNames.RightLegRoll: {'index': 44},
    HIKBoneNames.LeftArmRoll: {'index': 45},
    HIKBoneNames.LeftForeArmRoll: {'index': 46},
    HIKBoneNames.RightArmRoll: {'index': 47},
    HIKBoneNames.RightForeArmRoll: {'index': 48},
    HIKBoneNames.HipsTranslation: {'index': 49},
    HIKBoneNames.LeftHandThumb1: {'index': 50},
    HIKBoneNames.LeftHandThumb2: {'index': 51},
    HIKBoneNames.LeftHandThumb3: {'index': 52},
    HIKBoneNames.LeftHandThumb4: {'index': 53},
    HIKBoneNames.LeftHandIndex1: {'index': 54},
    HIKBoneNames.LeftHandIndex2: {'index': 55},
    HIKBoneNames.LeftHandIndex3: {'index': 56},
    HIKBoneNames.LeftHandIndex4: {'index': 57},
    HIKBoneNames.LeftHandMiddle1: {'index': 58},
    HIKBoneNames.LeftHandMiddle2: {'index': 59},
    HIKBoneNames.LeftHandMiddle3: {'index': 60},
    HIKBoneNames.LeftHandMiddle4: {'index': 61},
    HIKBoneNames.LeftHandRing1: {'index': 62},
    HIKBoneNames.LeftHandRing2: {'index': 63},
    HIKBoneNames.LeftHandRing3: {'index': 64},
    HIKBoneNames.LeftHandRing4: {'index': 65},
    HIKBoneNames.LeftHandPinky1: {'index': 66},
    HIKBoneNames.LeftHandPinky2: {'index': 67},
    HIKBoneNames.LeftHandPinky3: {'index': 68},
    HIKBoneNames.LeftHandPinky4: {'index': 69},
    HIKBoneNames.LeftHandExtraFinger1: {'index': 70},
    HIKBoneNames.LeftHandExtraFinger2: {'index': 71},
    HIKBoneNames.LeftHandExtraFinger3: {'index': 72},
    HIKBoneNames.LeftHandExtraFinger4: {'index': 73},
    HIKBoneNames.RightHandThumb1: {'index': 74},
    HIKBoneNames.RightHandThumb2: {'index': 75},
    HIKBoneNames.RightHandThumb3: {'index': 76},
    HIKBoneNames.RightHandThumb4: {'index': 77},
    HIKBoneNames.RightHandIndex1: {'index': 78},
    HIKBoneNames.RightHandIndex2: {'index': 79},
    HIKBoneNames.RightHandIndex3: {'index': 80},
    HIKBoneNames.RightHandIndex4: {'index': 81},
    HIKBoneNames.RightHandMiddle1: {'index': 82},
    HIKBoneNames.RightHandMiddle2: {'index': 83},
    HIKBoneNames.RightHandMiddle3: {'index': 84},
    HIKBoneNames.RightHandMiddle4: {'index': 85},
    HIKBoneNames.RightHandRing1: {'index': 86},
    HIKBoneNames.RightHandRing2: {'index': 87},
    HIKBoneNames.RightHandRing3: {'index': 88},
    HIKBoneNames.RightHandRing4: {'index': 89},
    HIKBoneNames.RightHandPinky1: {'index': 90},
    HIKBoneNames.RightHandPinky2: {'index': 91},
    HIKBoneNames.RightHandPinky3: {'index': 92},
    HIKBoneNames.RightHandPinky4: {'index': 93},
    HIKBoneNames.RightHandExtraFinger1: {'index': 94},
    HIKBoneNames.RightHandExtraFinger2: {'index': 95},
    HIKBoneNames.RightHandExtraFinger3: {'index': 96},
    HIKBoneNames.RightHandExtraFinger4: {'index': 97},
    HIKBoneNames.LeftFootThumb1: {'index': 98},
    HIKBoneNames.LeftFootThumb2: {'index': 99},
    HIKBoneNames.LeftFootThumb3: {'index': 100},
    HIKBoneNames.LeftFootThumb4: {'index': 101},
    HIKBoneNames.LeftFootIndex1: {'index': 102},
    HIKBoneNames.LeftFootIndex2: {'index': 103},
    HIKBoneNames.LeftFootIndex3: {'index': 104},
    HIKBoneNames.LeftFootIndex4: {'index': 105},
    HIKBoneNames.LeftFootMiddle1: {'index': 106},
    HIKBoneNames.LeftFootMiddle2: {'index': 107},
    HIKBoneNames.LeftFootMiddle3: {'index': 108},
    HIKBoneNames.LeftFootMiddle4: {'index': 109},
    HIKBoneNames.LeftFootRing1: {'index': 110},
    HIKBoneNames.LeftFootRing2: {'index': 111},
    HIKBoneNames.LeftFootRing3: {'index': 112},
    HIKBoneNames.LeftFootRing4: {'index': 113},
    HIKBoneNames.LeftFootPinky1: {'index': 114},
    HIKBoneNames.LeftFootPinky2: {'index': 115},
    HIKBoneNames.LeftFootPinky3: {'index': 116},
    HIKBoneNames.LeftFootPinky4: {'index': 117},
    HIKBoneNames.LeftFootExtraFinger1: {'index': 118},
    HIKBoneNames.LeftFootExtraFinger2: {'index': 119},
    HIKBoneNames.LeftFootExtraFinger3: {'index': 120},
    HIKBoneNames.LeftFootExtraFinger4: {'index': 121},
    HIKBoneNames.RightFootThumb1: {'index': 122},
    HIKBoneNames.RightFootThumb2: {'index': 123},
    HIKBoneNames.RightFootThumb3: {'index': 124},
    HIKBoneNames.RightFootThumb4: {'index': 125},
    HIKBoneNames.RightFootIndex1: {'index': 126},
    HIKBoneNames.RightFootIndex2: {'index': 127},
    HIKBoneNames.RightFootIndex3: {'index': 128},
    HIKBoneNames.RightFootIndex4: {'index': 129},
    HIKBoneNames.RightFootMiddle1: {'index': 130},
    HIKBoneNames.RightFootMiddle2: {'index': 131},
    HIKBoneNames.RightFootMiddle3: {'index': 132},
    HIKBoneNames.RightFootMiddle4: {'index': 133},
    HIKBoneNames.RightFootRing1: {'index': 134},
    HIKBoneNames.RightFootRing2: {'index': 135},
    HIKBoneNames.RightFootRing3: {'index': 136},
    HIKBoneNames.RightFootRing4: {'index': 137},
    HIKBoneNames.RightFootPinky1: {'index': 138},
    HIKBoneNames.RightFootPinky2: {'index': 139},
    HIKBoneNames.RightFootPinky3: {'index': 140},
    HIKBoneNames.RightFootPinky4: {'index': 141},
    HIKBoneNames.RightFootExtraFinger1: {'index': 142},
    HIKBoneNames.RightFootExtraFinger2: {'index': 143},
    HIKBoneNames.RightFootExtraFinger3: {'index': 144},
    HIKBoneNames.RightFootExtraFinger4: {'index': 145},
    HIKBoneNames.LeftInHandThumb: {'index': 146},
    HIKBoneNames.LeftInHandIndex: {'index': 147},
    HIKBoneNames.LeftInHandMiddle: {'index': 148},
    HIKBoneNames.LeftInHandRing: {'index': 149},
    HIKBoneNames.LeftInHandPinky: {'index': 150},
    HIKBoneNames.LeftInHandExtraFinger: {'index': 151},
    HIKBoneNames.RightInHandThumb: {'index': 152},
    HIKBoneNames.RightInHandIndex: {'index': 153},
    HIKBoneNames.RightInHandMiddle: {'index': 154},
    HIKBoneNames.RightInHandRing: {'index': 155},
    HIKBoneNames.RightInHandPinky: {'index': 156},
    HIKBoneNames.RightInHandExtraFinger: {'index': 157},
    HIKBoneNames.LeftInFootThumb: {'index': 158},
    HIKBoneNames.LeftInFootIndex: {'index': 159},
    HIKBoneNames.LeftInFootMiddle: {'index': 160},
    HIKBoneNames.LeftInFootRing: {'index': 161},
    HIKBoneNames.LeftInFootPinky: {'index': 162},
    HIKBoneNames.LeftInFootExtraFinger: {'index': 163},
    HIKBoneNames.RightInFootThumb: {'index': 164},
    HIKBoneNames.RightInFootIndex: {'index': 165},
    HIKBoneNames.RightInFootMiddle: {'index': 166},
    HIKBoneNames.RightInFootRing: {'index': 167},
    HIKBoneNames.RightInFootPinky: {'index': 168},
    HIKBoneNames.RightInFootExtraFinger: {'index': 169},
    HIKBoneNames.LeftShoulderExtra: {'index': 170},
    HIKBoneNames.RightShoulderExtra: {'index': 171},
    HIKBoneNames.LeafLeftUpLegRoll1: {'index': 172},
    HIKBoneNames.LeafLeftLegRoll1: {'index': 173},
    HIKBoneNames.LeafRightUpLegRoll1: {'index': 174},
    HIKBoneNames.LeafRightLegRoll1: {'index': 175},
    HIKBoneNames.LeafLeftArmRoll1: {'index': 176},
    HIKBoneNames.LeafLeftForeArmRoll1: {'index': 177},
    HIKBoneNames.LeafRightArmRoll1: {'index': 178},
    HIKBoneNames.LeafRightForeArmRoll1: {'index': 179},
    HIKBoneNames.LeafLeftUpLegRoll2: {'index': 180},
    HIKBoneNames.LeafLeftLegRoll2: {'index': 181},
    HIKBoneNames.LeafRightUpLegRoll2: {'index': 182},
    HIKBoneNames.LeafRightLegRoll2: {'index': 183},
    HIKBoneNames.LeafLeftArmRoll2: {'index': 184},
    HIKBoneNames.LeafLeftForeArmRoll2: {'index': 185},
    HIKBoneNames.LeafRightArmRoll2: {'index': 186},
    HIKBoneNames.LeafRightForeArmRoll2: {'index': 187},
    HIKBoneNames.LeafLeftUpLegRoll3: {'index': 188},
    HIKBoneNames.LeafLeftLegRoll3: {'index': 189},
    HIKBoneNames.LeafRightUpLegRoll3: {'index': 190},
    HIKBoneNames.LeafRightLegRoll3: {'index': 191},
    HIKBoneNames.LeafLeftArmRoll3: {'index': 192},
    HIKBoneNames.LeafLeftForeArmRoll3: {'index': 193},
    HIKBoneNames.LeafRightArmRoll3: {'index': 194},
    HIKBoneNames.LeafRightForeArmRoll3: {'index': 195},
    HIKBoneNames.LeafLeftUpLegRoll4: {'index': 196},
    HIKBoneNames.LeafLeftLegRoll4: {'index': 197},
    HIKBoneNames.LeafRightUpLegRoll4: {'index': 198},
    HIKBoneNames.LeafRightLegRoll4: {'index': 199},
    HIKBoneNames.LeafLeftArmRoll4: {'index': 200},
    HIKBoneNames.LeafLeftForeArmRoll4: {'index': 201},
    HIKBoneNames.LeafRightArmRoll4: {'index': 202},
    HIKBoneNames.LeafRightForeArmRoll4: {'index': 203},
    HIKBoneNames.LeafLeftUpLegRoll5: {'index': 204},
    HIKBoneNames.LeafLeftLegRoll5: {'index': 205},
    HIKBoneNames.LeafRightUpLegRoll5: {'index': 206},
    HIKBoneNames.LeafRightLegRoll5: {'index': 207},
    HIKBoneNames.LeafLeftArmRoll5: {'index': 208},
    HIKBoneNames.LeafLeftForeArmRoll5: {'index': 209},
    HIKBoneNames.LeafRightArmRoll5: {'index': 210},
    HIKBoneNames.LeafRightForeArmRoll5: {'index': 211}
}


class HIKSkeletonGeneratorAttrs(object):
    WantUpperArmRollBone = 'WantUpperArmRollBone'
    WantLowerArmRollBone = 'WantLowerArmRollBone'
    WantUpperLegRollBone = 'WantUpperLegRollBone'
    WantLowerLegRollBone = 'WantLowerLegRollBone'
    NbUpperArmRollBones = 'NbUpperArmRollBones'
    NbLowerArmRollBones = 'NbLowerArmRollBones'
    NbUpperLegRollBones = 'NbUpperLegRollBones'
    NbLowerLegRollBones = 'NbLowerLegRollBones'
    SpineCount = 'SpineCount'
    NeckCount = 'NeckCount'
    ShoulderCount = 'ShoulderCount'
    FingerJointCount = 'FingerJointCount'
    WantMiddleFinger = 'WantMiddleFinger'
    WantIndexFinger = 'WantIndexFinger'
    WantRingFinger = 'WantRingFinger'
    WantPinkyFinger = 'WantPinkyFinger'
    WantThumb = 'WantThumb'
    WantExtraFinger = 'WantExtraFinger'
    ToeJointCount = 'ToeJointCount'
    WantIndexToe = 'WantIndexToe'
    WantRingToe = 'WantRingToe'
    WantMiddleToe = 'WantMiddleToe'
    WantPinkyToe = 'WantPinkyToe'
    WantBigToe = 'WantBigToe'
    WantFootThumb = 'WantFootThumb'
    WantFingerBase = 'WantFingerBase'
    WantToeBase = 'WantToeBase'
    WantInHandJoint = 'WantInHandJoint'
    WantInFootJoint = 'WantInFootJoint'
    WantHipsTranslation = 'WantHipsTranslation'


HIK_SKELETON_GENERATOR_DEFAULTS = {
    HIKSkeletonGeneratorAttrs.WantUpperArmRollBone: 0,
    HIKSkeletonGeneratorAttrs.WantLowerArmRollBone: 0,
    HIKSkeletonGeneratorAttrs.WantUpperLegRollBone: 0,
    HIKSkeletonGeneratorAttrs.WantLowerLegRollBone: 0,
    HIKSkeletonGeneratorAttrs.NbUpperArmRollBones: 0,
    HIKSkeletonGeneratorAttrs.NbLowerArmRollBones: 0,
    HIKSkeletonGeneratorAttrs.NbUpperLegRollBones: 0,
    HIKSkeletonGeneratorAttrs.NbLowerLegRollBones: 0,
    HIKSkeletonGeneratorAttrs.SpineCount: 3,
    HIKSkeletonGeneratorAttrs.NeckCount: 1,
    HIKSkeletonGeneratorAttrs.ShoulderCount: 1,
    HIKSkeletonGeneratorAttrs.FingerJointCount: 3,
    HIKSkeletonGeneratorAttrs.WantMiddleFinger: 1,
    HIKSkeletonGeneratorAttrs.WantIndexFinger: 1,
    HIKSkeletonGeneratorAttrs.WantRingFinger: 1,
    HIKSkeletonGeneratorAttrs.WantPinkyFinger: 1,
    HIKSkeletonGeneratorAttrs.WantThumb: 1,
    HIKSkeletonGeneratorAttrs.WantExtraFinger: 0,
    HIKSkeletonGeneratorAttrs.ToeJointCount: 3,
    HIKSkeletonGeneratorAttrs.WantIndexToe: 0,
    HIKSkeletonGeneratorAttrs.WantRingToe: 0,
    HIKSkeletonGeneratorAttrs.WantMiddleToe: 0,
    HIKSkeletonGeneratorAttrs.WantPinkyToe: 0,
    HIKSkeletonGeneratorAttrs.WantBigToe: 0,
    HIKSkeletonGeneratorAttrs.WantFootThumb: 0,
    HIKSkeletonGeneratorAttrs.WantFingerBase: 0,
    HIKSkeletonGeneratorAttrs.WantToeBase: 0,
    HIKSkeletonGeneratorAttrs.WantInHandJoint: 1,
    HIKSkeletonGeneratorAttrs.WantInFootJoint: 0,
    HIKSkeletonGeneratorAttrs.WantHipsTranslation: 0
}


# ==============================================================================================================
# HIK CHARACTER
# ==============================================================================================================

def create_character(character_name, character_namespace=None, lock=True):
    """
    Creates a HumanIK character and tries to use the given name to name the new character
    :param character_name: str, name of the new HumanIK character
    """

    if character_namespace and not character_namespace.endswith(':'):
        character_namespace = '{}:'.format(character_namespace)
    character_namespace = character_namespace or ''

    character_definition = maya.mel.eval('hikCreateCharacter("{0}")'.format(character_name))
    set_current_character(character_definition)

    try:
        maya.mel.eval('hikUpdateCharacterList()')
        maya.mel.eval('hikSelectDefinitionTab()')
    except Exception:
        pass

    for bone_name, bone_data in HIK_BONES.items():
        bone_full_name = '{}{}'.format(character_namespace, bone_name)
        if not dcc.node_exists(bone_full_name):
            logger.debug('HIK bone "{}" not found in scene!'.format(bone_name))
            continue
        bone_index = bone_data['index']
        set_character_object(character_definition, bone_full_name, bone_index, 0)

    property_node = get_properties_node(character_definition)

    dcc.set_attribute_value(property_node, 'ForceActorSpace', 0)
    dcc.set_attribute_value(property_node, 'ScaleCompensationMode', 1)
    dcc.set_attribute_value(property_node, 'Mirror', 0)
    dcc.set_attribute_value(property_node, 'HipsHeightCompensationMode', 1)
    dcc.set_attribute_value(property_node, 'AnkleProximityCompensationMode', 1)
    dcc.set_attribute_value(property_node, 'AnkleHeightCompensationMode', 0)
    dcc.set_attribute_value(property_node, 'MassCenterCompensationMode', 1)

    if lock:
        maya.mel.eval('hikToggleLockDefinition')
    # else:
    #     generator_node = maya.cmds.createNode('HIKSkeletonGeneratorNode')
        # dcc.connect_attribute(
        #     generator_node, 'CharacterNode', character_definition, 'SkeletonGenerator', force=True)

    return character_definition


def rename_character(character):
    """
    Opens a dialog that allows the user to rename the given HumanIK character
    """

    maya.mel.eval('hikSetCurrentCharacter("{0}");  hikRenameDefinition();'.format(character))


def get_current_character():
    """
    Returns the name of the current HumanIK character
    :return: str
    """

    return maya.mel.eval('hikGetCurrentCharacter()') or 'None'


def set_current_character(character):
    """
    Sets the given HumanIK character as the global current HumanIK
    """

    maya.mel.eval('hikSetCurrentCharacter("{}");'.format(character))
    maya.mel.eval('hikUpdateCharacterList()')
    maya.mel.eval('hikSetCurrentSourceFromCharacter("{}")'.format(character))
    maya.mel.eval('hikUpdateSourceList()')


def get_character_nodes(node):
    """
    Returns all character nodes in the given HumanIk character definition node
    :param node: str
    :return: list(str
    """

    if not is_character_definition(node):
        raise Exception(
            'Invalid character definition node! Object "{}" does not exists or '
            'is not a valid HIKCharacterNode!'.format(node))

    character_nodes = maya.mel.eval('hikGetSkeletonNodes "{}"'.format(node))

    return character_nodes


def get_scene_characters():
    """
    Returns a list of names for all HumanIK characters in the current scene
    """

    return maya.mel.eval('hikGetSceneCharacters()') or []


def delete_whole_character(character):
    """
    Deletes the given HumanIK character
    It deletes its control rig (if any), its skeleton (if any) and its character definition
    """

    maya.mel.eval("""
    hikSetCurrentCharacter("{0}"); hikDeleteControlRig(); hikDeleteSkeleton_noPrompt();
    """.format(character))


def is_character_definition(node):
    """
    Returns whether or not given node is an HumanIK character node
    :param node: str
    :return: bool
    """

    if not dcc.node_exists(node):
        return False

    if dcc.object_type(node) != 'HIKCharacterNode':
        return False

    return True


def is_character_definition_locked(node):
    """
    Returns whether or not given HumanIK character node is locked
    :param node: str
    :return: bool
    """

    if not is_character_definition(node):
        raise Exception(
            'Invalid character definition node! Object "{}" does not exists or '
            'is not a valid HIKCharacterNode!'.format(node))

    lock = maya.cmds.getAttr('{}.InputCharacterizationLock'.format(node))

    return lock


def set_character_definition_lock_status(node, lock_state=True):
    """
    Sets the lock status of the given HumanIk character definition
    :param node: str
    :param lock_state: bool
    :return: int, lock state
    """

    if not is_character_definition(node):
        raise Exception(
            'Invalid character definition node! Object "{}" does not exists or '
            'is not a valid HIKCharacterNode!'.format(node))

    is_locked = is_character_definition_locked(node)

    if lock_state != is_locked:
        maya.mel.eval('hikToggleLockDefinition')

    return int(lock_state)


def reset_current_source():
    """
    Resets current character definition source
    :return:
    """

    return maya.mel.eval('hikSetCurrentSource(hikNoneString())')


def set_character_source(character_node, source):
    """
    Sets current character source
    :param character_node: str
    :param source: str
    """

    # HIK Character Controls Tool
    maya.mel.eval('HIKCharacterControlsTool')

    current_character = get_current_character()
    set_current_character(character_node)

    # set character source
    maya.mel.eval('hikSetCurrentSource("{}")'.format(source))
    maya.mel.eval('hikUpdateSourceList()')
    maya.mel.eval('hikUpdateCurrentSourceFromUI()')
    maya.mel.eval('hikUpdateContextualUI()')
    maya.mel.eval('hikControlRigSelectionChangedCallback')

    # restore current character
    if character_node != current_character:
        set_current_character(current_character)


def set_character_object(character_node, character_bone, bone_id, delete_bone=False):
    """
    Sets a node in the given character definition
    :param character_node: str
    :param character_bone: str
    :param bone_id: str
    :param delete_bone: bool
    :return:
    """

    maya.mel.eval(
        'setCharacterObject("{}", "{}", "{}", "{}")'.format(
            character_bone, character_node, str(bone_id), str(int(delete_bone))))


def get_node_count(character_node=None):
    if character_node:
        return maya.mel.eval('hikGetNodeCount("{}")'.format(character_node))
    else:
        return maya.mel.eval('hikGetNodeCount()')


# ==============================================================================================================
# HIK SKELETON
# ==============================================================================================================

def create_skeleton(character_name='Character1', attrs_dict=None):
    """
    Creates a new HumanIk skeleton
    """

    if attrs_dict is None:
        attrs_dict = dict()

    sync_skeleton_generator_from_ui()

    create_character(character_name=character_name, lock=False)
    current_name = get_current_character()
    if not current_name:
        return False

    skeleton_generator_node = create_skeleton_generator_node(current_name)
    if not skeleton_generator_node:
        logger.warning('Was not possible to create HIK Skeleton Generator node.')
        return False

    load_default_human_ik_pose_onto_skeleton_generator_node(skeleton_generator_node)
    set_skeleton_generator_defaults(skeleton_generator_node)
    set_skeleton_generator_attrs(skeleton_generator_node, attrs_dict)

    reset_current_source()

    # If we have no characters yet, select the newly created character to refresh both the character and sources list
    dcc.select_node(current_name)
    update_current_character_from_scene()
    update_definition_ui()
    select_skeleton_tab()

    return True


def get_skeleton_node(character, index):
    """
    Returns skeleton node of the given character in the given index
    :param character: str
    :param index: int
    :return: str
    """

    return maya.mel.eval('hikGetSkNode("{}", {})'.format(character, index))


def get_skeleton_definition(character):
    """
    Returns skeleton definition of the given character
    :param character: str, HIK character name
    :return: dict
    """

    hik_bones = dict()
    hik_count = maya.cmds.hikGetNodeCount()
    for i in range(hik_count):
        bone = get_skeleton_node(character, i)
        if not bone:
            continue
        hik_name = maya.cmds.GetHIKNodeName(i)
        hik_bones[hik_name] = {'bone': bone, 'hik_id': i}

    return hik_bones


def set_skeleton_definition(character, definition_info):
    """
    Sets skeleton definition to the given character
    :param character: str
    :param definition_info: dict
    """

    for hik_name, bone_info in definition_info.items():
        bone = bone_info.get('bone', None)
        bone_id = bone_info.get('hik_id', None)
        if not bone:
            continue
        if bone_id is None:
            bone_id = HIK_BONES.get(hik_name, dict()).get('index', None)
        if bone_id is None:
            continue

        set_character_object(character, bone, bone_id, delete_bone=False)

    update_definition_ui()


# ==============================================================================================================
# HIK GENERATOR NODE
# ==============================================================================================================

def get_skeleton_generator_node(character):
    """
    Returns the name of the skeleton generator node associated with teh given HumanIK
    character if it exists, or an empty string otherwise
    :param character: str, HumanIK character name
    """

    return maya.mel.eval('hikGetSkeletonGeneratorNode("{0}")'.format(character)) or ''


def create_skeleton_generator_node(character_node):
    """
    Creates a new HIK Skeleton Generator node (HIKSkeletonGeneratorNode)
    :param character_node: str
    :return:str
    """

    skeleton_generator_node = maya.cmds.createNode('HIKSkeletonGeneratorNode')
    dcc.set_attribute_value(skeleton_generator_node, 'isHistoricallyInteresting', 0)
    dcc.connect_attribute(skeleton_generator_node, 'CharacterNode', character_node, 'SkeletonGenerator')

    return skeleton_generator_node


def set_skeleton_generator_defaults(skeleton_generator_node):
    """
    Sets given Skeleton Generator node to its defaults values
    :param skeleton_generator_node: str
    """

    for attr_name, default_value in HIK_SKELETON_GENERATOR_DEFAULTS.items():
        if not dcc.attribute_exists(skeleton_generator_node, attr_name):
            logger.warning(
                'Impossible to reset {} because that attribute was not found in '
                'HIK Skeleton generator node: "{}"'.format(attr_name, skeleton_generator_node))
            continue
        dcc.set_attribute_value(skeleton_generator_node, attr_name, default_value)


def set_skeleton_generator_attrs(skeleton_generator_node, attrs_dict):

    for attr_name, attr_value in attrs_dict.items():
        if not dcc.attribute_exists(skeleton_generator_node, attr_name):
            logger.warning(
                'Impossible to set {} because that attribute was not found in '
                'HIK Skeleton generator node "{}"'.format(attr_name, skeleton_generator_node))
            continue
        dcc.set_attribute_value(skeleton_generator_node, attr_name, attr_value)


def load_default_human_ik_pose_onto_skeleton_generator_node(skeleton_generator_node):
    """
    Loads default HumanIk pose into given HIK generator node
    :param skeleton_generator_node: str
    :return: bool
    """

    default_pose_file = get_default_human_ik_pose_file()
    if not os.path.isfile(default_pose_file):
        logger.warning(
            'Impossible to load default HumanIk pose becaue pose file was not found: {}'.format(default_pose_file))
        return False

    load_pose_onto_skeleton_generator_node(skeleton_generator_node, pose_name=default_pose_file)


def load_pose_onto_skeleton_generator_node(skeleton_generator_node, pose_name):
    """
    Loads given pose file into given HIK generator node
    :param skeleton_generator_node: str
    :param pose_name: str
    """

    return maya.mel.eval(
        'hikReadCharPoseFileOntoSkeletonGeneratorNode("{}", "{}")'.format(skeleton_generator_node, pose_name))


def sync_current_pose_to_skeleton_generator(character_node, skeleton_generator_node):
    """
    Regenerates HIK skeleton from the skeleton generator node.
    :param character_node: str
    :param skeleton_generator_node: str
    :return:
    """

    node_count = get_node_count()
    print(node_count)


def update_skeleton_from_skeleton_generator_node(character_node):
    pass


def sync_skeleton_generator_from_ui():
    """
    Syncs the skeleton generator settings from t he UI
    """

    if dcc.is_batch():
        return False

    current_name = get_current_character()
    if not current_name:
        return False

    skeleton_generator_node = get_skeleton_generator_node(current_name)
    if not skeleton_generator_node:
        return False

    sync_current_pose_to_skeleton_generator(current_name, skeleton_generator_node)
    # update_skeleton_from_skeleton_generator_node(current_name, 1.0)


# ==============================================================================================================
# HIK PROPERTIES NODE
# ==============================================================================================================

def get_properties_node(character_node):
    """
    Returns HIKProperty2State node of the given HumanIk Character node
    :param character_node: str
    :return: str
    """

    if not is_character_definition(character_node):
        raise Exception(
            'Invalid character definition node! Object "{}" does not exists or '
            'is not a valid HIKCharacterNode!'.format(character_node))

    try:
        property_node = maya.mel.eval('getProperty2StateFromCharacter("{}")'.format(character_node))
    except Exception:
        connections = maya.cmds.listConnections('{}.propertyState'.format(character_node), s=True, d=False)
        if not connections:
            raise Exception(
                'Unable to determine HIKProperty2State nodef rom character definition node "{}"!'.format(
                    character_node))

        if len(connections) > 1:
            logger.warning(
                'Multiple HIKProperty2State nodes found for character definition "{}"! '
                'Returning first item only ...'.format(character_node))

        property_node = connections[0]

    return property_node


# ==============================================================================================================
# HIK SOLVER NODE
# ==============================================================================================================

def get_solver_node(character_node):
    """
    Returns HIKSolverNode  node of the given HumanIk Character node
    :param character_node: str
    :return: str
    """

    if not is_character_definition(character_node):
        raise Exception(
            'Invalid character definition node! Object "{}" does not exists or '
            'is not a valid HIKCharacterNode!'.format(character_node))

    connections = maya.cmds.ls(maya.cmds.listConnections(
        '{}.OutputPropertySetState'.format(character_node), d=True, s=False) or list(), type='HIKSolverNode')
    if not connections:
        raise Exception('Unable to determine HIKSolverNode from character definition node "{}"!'.format(character_node))

    if len(connections) > 1:
        logger.warning(
            'Multiple HIKSolverNode nodes found for character definition "{}"! Returning first item only ...'.format(
                character_node))

    return connections[0]


# ==============================================================================================================
# HIK RETARGET NODE
# ==============================================================================================================

def get_retarget_node(character_node):
    """
    Returns HIKRetargeterNode node of the given HumanIk Character node
    :param character_node: str
    :return: str
    """

    if not is_character_definition(character_node):
        raise Exception(
            'Invalid character definition node! Object "{}" does not exists or '
            'is not a valid HIKCharacterNode!'.format(character_node))

    connections = maya.cmds.ls(maya.cmds.listConnections(
        '{}.OutputPropertySetState'.format(character_node), d=True, s=False) or list(), type='HIKRetargeterNode')
    if not connections:
        raise Exception('Unable to determine HIKRetargeterNode from character definition node "{}"!'.format(
            character_node))

    if len(connections) > 1:
        logger.warning(
            'Multiple HIKRetargeterNode  nodes found for character definition "{}"! '
            'Returning first item only ...'.format(character_node))

    return connections[0]


# ==============================================================================================================
# HIK CUSTOM RIG
# ==============================================================================================================

def get_custom_rig_retarget_node(character_node):
    """
    Returns CustomRigRetargeterNode node of the given HumanIk Character node
    :param character_node: str
    :return: str
    """

    if not is_character_definition(character_node):
        raise Exception(
            'Invalid character definition node! Object "{}" does not exists or '
            'is not a valid HIKCharacterNode!'.format(character_node))

    connections = maya.cmds.ls(
        maya.cmds.listConnections(character_node, d=True, s=False) or list(), type='CustomRigRetargeterNode')
    if not connections:
        return None

    if len(connections) > 1:
        logger.warning(
            'Multiple CustomRigRetargeterNode  nodes found for character definition "{}"! '
            'Returning first item only ...'.format(character_node))

    return connections[0]


def create_custom_rig(character_node=None):
    """
    Creates a new custom rig HIK node
    :param character_node: str or None
    :return:
    """

    character_node = character_node or get_current_character()
    if not character_node:
        return

    return maya.mel.eval('hikCreateCustomRig("{}")'.format(character_node))


def export_custom_rig_mapping(character_node, file_path):
    """
    Exports custom rig mapping from given character HIK node into given file path
    :param character_node: str
    :param file_path: str
    """

    custom_rig_retarget_node = get_custom_rig_retarget_node(character_node)
    if not custom_rig_retarget_node:
        logger.warning('No custom rig retarget node found connected to HIK character "{}"'.format(character_node))
        return

    retargeter = maya.app.hik.retargeter.HIKRetargeter(character_node)
    retargeter.fromGraph(custom_rig_retarget_node)
    retargeter.write(file_path)

    return True


def import_custom_rig_mapping(character_node, file_path):
    """
    Imports custom rig mapping for given character HIK node from given file path
    :param character_node: str
    :param file_path: str
    """

    custom_rig_retarget_node = get_custom_rig_retarget_node(character_node)
    if custom_rig_retarget_node:
        logger.warning('custom rig retarget found connected to HIK character "{}". Import only works if no '
                       'retarget node is found'.format(character_node))
        return False

    retargeter = maya.app.hik.retargeter.HIKRetargeter()
    if retargeter.read(path_utils.clean_path(file_path), character_node):
        retargeter.toGraph()

    select_custom_rig_tab()


# ==============================================================================================================
# HIK UI
# ==============================================================================================================

def update_current_character_from_scene():
    """
    Updates the current character variable to the last character in scene
    """

    return maya.mel.eval('hikUpdateCurrentCharacterFromScene()')


def update_definition_ui():
    """
    Updates all skeleton definitions related UI
    """

    return maya.mel.eval('hikUpdateDefinitionUI()')


def select_skeleton_tab():
    """
    Selects Human IK Skeleton tab in UI
    """

    return maya.mel.eval('hikSelectSkeletonTab()')


def select_definition_tab():
    """
    Selects Human IK Definition tab in UI
    """

    return maya.mel.eval('hikSelectDefinitionTab()')


def select_control_rig_tab():
    """
    Selects Human IK Control Rig tab in UI
    """

    return maya.mel.eval('hikSelectControlRigTab()')


def select_custom_rig_tab():
    """
    Selects Human IK Custom Rig tab in UI
    """

    return maya.mel.eval('hikSelectCustomRigTab()')


def is_skeleton_tab_selected():
    """
    Returns whether or not Human IK Skeleton tab is selected in UI
    :return: bool
    """

    return maya.mel.eval('hikIsSkeletonTabSelected()')


def is_definition_tab_selected():
    """
    Returns whether or not Human IK Definition tab is selected in UI
    :return: bool
    """

    return maya.mel.eval('hikIsDefinitionTabSelected()')


def is_control_rig_tab_selected():
    """
    Returns whether or not Human IK Control Rig tab is selected in UI
    :return: bool
    """

    return maya.mel.eval('hikIsControlRigTabSelected()')


def is_custom_rig_tab_selected():
    """
    Returns whether or not Human IK Custom Rig tab is selected in UI
    :return: bool
    """

    return maya.mel.eval('hikIsCustomRigTabSelected()')


# ==============================================================================================================
# HIK UTILS
# ==============================================================================================================


def load_human_ik_plugin():
    """
    Load all required HumanIK commands and plugins
    """

    maya_location = os.getenv('MAYA_LOCATION', None)
    if not maya_location or not os.path.isdir(maya_location):
        logger.warning(
            'Impossible to load HumanIK commands/plugins because Maya location was not found: {}!'.format(
                maya_location))
        return False

    # Source HumanIK files
    maya.mel.eval('source "' + maya_location + '/scripts/others/hikGlobalUtils.mel"')
    maya.mel.eval('source "' + maya_location + '/scripts/others/hikCharacterControlsUI.mel"')
    maya.mel.eval('source "' + maya_location + '/scripts/others/hikDefinitionOperations.mel"')
    maya.mel.eval('source "' + maya_location + '/scripts/others/CharacterPipeline.mel"')
    maya.mel.eval('source "' + maya_location + '/scripts/others/characterSelector.mel"')

    # Load HumanIK plugins
    if not helpers.is_plugin_loaded('mayaHIK'):
        helpers.register_plugin('mayaHIK')
    if not helpers.is_plugin_loaded('mayaCharacterization'):
        helpers.register_plugin('mayaCharacterization')
    if not helpers.is_plugin_loaded('retargeterNodes'):
        helpers.register_plugin('retargeterNodes')

    # HIK Character Controls Tool
    maya.mel.eval('HIKCharacterControlsTool')

    return True


def initialize():
    """
    Makes sure that HumanIK tool is loaded and visible
    """

    if maya.mel.eval('exists hikGetCurrentCharacter'):
        character = get_current_character()
    else:
        character = ''

    maya.mel.eval('HIKCharacterControlsTool();')

    set_current_character(character)


def update_hik_tool():
    """
    Refreshes HumanIK tool UI so that fits the current HumanIK character
    """

    maya.mel.eval("""
    if (hikIsCharacterizationToolUICmdPluginLoaded())
    {
        hikUpdateCharacterList();
        hikUpdateSourceList();
        hikUpdateContextualUI();
    }
    """)


def none_string():
    """
    Returns the string that should be display when no HumanIK character is selected
    :return: str
    """
    try:
        return maya.mel.eval('hikNoneString()') or ''
    except Exception:
        return ''


def get_default_human_ik_pose_file():
    """
    Returns the path where file that stores default HumanIK pose is located
    :return: str
    """

    script_path = str(maya.mel.eval(
        'whatIs "hikReadCharPoseFileOntoSkeletonGeneratorNode"')).replace('Mel procedure found in: ', '')
    dir_name = os.path.dirname(script_path)
    pose_file_name = os.path.normpath(os.path.join(dir_name, 'Biped_Template.hik')).replace('\\', '/')

    return pose_file_name


def bake_animation(character_node):
    """
    Bakes the animation of the given character node
    :param character_node: str
    :return: list(str), list of bones used for the animation baking process
    """

    bones = get_character_nodes(character_node)

    maya.cmds.bakeResult(
        bones, simulation=True, t=[1, 55], sampleBy=1, disableImplicitControl=True, preserveOutsideKeys=False,
        sparseAnimCurveBake=False, removeBakedAttributeFromLayer=False, bakeOnOverrideLayer=False,
        minimizeRotation=False, at=['tx', 'ty', 'tz', 'rx', 'ry', 'rz'])

    return bones
