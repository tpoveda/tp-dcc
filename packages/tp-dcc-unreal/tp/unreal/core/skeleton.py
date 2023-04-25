#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Unreal skeleton related classes
"""

import natsort

from tp.core import dcc
from tp.common.python import helpers


class UnrealSkeleton(object):

    class PartSides(object):
        LEFT = 'l'
        RIGHT = 'r'

    class PartNames(object):
        MASTER = 'master'
        ROOT = 'root'
        PELIVS = 'pelvis'
        SPINE = 'spine'
        CLAVICLE = 'clavicle'
        NECK = 'neck'
        HEAD = 'head'
        UPPERARM = 'upperarm'
        LOWERARM = 'lowerarm'
        HAND = 'hand'
        THIGH = 'thigh'
        CALF = 'calf'
        FOOT = 'foot'
        TOE = 'toe'
        INDEX = 'index'
        MIDDLE = 'middle'
        PINKY = 'pinky'
        RING = 'ring'
        THUMB = 'thumb'

    def __init__(self, joints_list):
        self._joints = joints_list

    def add_joints(self, joints_list):
        self._joints.extend(joints_list)
        self._joints = helpers.remove_dupes(self._joints)

    def get_master_joint(self):
        return UnrealSkeleton.PartNames.MASTER

    def get_root_joint(self):
        return UnrealSkeleton.PartNames.ROOT

    def get_pelvis_joint(self):
        return UnrealSkeleton.PartNames.PELIVS

    def get_head_joint(self):
        return UnrealSkeleton.PartNames.HEAD

    def get_spine_joints(self):
        return self._get_joints(UnrealSkeleton.PartNames.SPINE)

    def get_clavicle_joint(self, side=None):
        return self._get_joint_name(UnrealSkeleton.PartNames.CLAVICLE, side=side or UnrealSkeleton.PartSides.LEFT)

    def get_neck_joints(self):
        return self._get_joints(UnrealSkeleton.PartNames.NECK)

    def get_upper_arm_joint(self, side=None):
        return self._get_joint_name(UnrealSkeleton.PartNames.UPPERARM, side=side or UnrealSkeleton.PartSides.LEFT)

    def get_lower_arm_joint(self, side=None):
        return self._get_joint_name(UnrealSkeleton.PartNames.LOWERARM, side=side or UnrealSkeleton.PartSides.LEFT)

    def get_arm_joints(self, side=None):
        upper_arm_joint = self.get_upper_arm_joint(side=side)
        lower_arm_joint = self.get_lower_arm_joint(side=side)
        hand_joint = self.get_hand_joint(side=side)

        return [upper_arm_joint, lower_arm_joint, hand_joint]

    def get_hand_joint(self, side=None):
        return self._get_joint_name(UnrealSkeleton.PartNames.HAND, side=side or UnrealSkeleton.PartSides.LEFT)

    def get_thigh_joint(self, side=None):
        return self._get_joint_name(UnrealSkeleton.PartNames.THIGH, side=side or UnrealSkeleton.PartSides.LEFT)

    def get_calf_joint(self, side=None):
        return self._get_joint_name(UnrealSkeleton.PartNames.CALF, side=side or UnrealSkeleton.PartSides.LEFT)

    def get_leg_joints(self, side=None):
        thigh_leg_joint = self.get_thigh_joint(side=side)
        calf_leg_joint = self.get_calf_joint(side=side)
        foot_joint = self.get_foot_joint(side=side)

        return [thigh_leg_joint, calf_leg_joint, foot_joint]

    def get_feet_joints(self, side=None):
        foot_joint = self.get_foot_joint(side=side)
        toe_joint = self.get_toe_joint(side=side)

        return [foot_joint, toe_joint]

    def get_foot_joint(self, side=None):
        return self._get_joint_name(UnrealSkeleton.PartNames.FOOT, side=side or UnrealSkeleton.PartSides.LEFT)

    def get_toe_joint(self, side=None):
        return self._get_joint_name(UnrealSkeleton.PartNames.TOE, side=side or UnrealSkeleton.PartSides.LEFT)

    def get_index_finger_joints(self, side=None):
        return self._get_joints(UnrealSkeleton.PartNames.INDEX, side=side or UnrealSkeleton.PartSides.LEFT)

    def get_middle_finger_joints(self, side=None):
        return self._get_joints(UnrealSkeleton.PartNames.MIDDLE, side=side or UnrealSkeleton.PartSides.LEFT)

    def get_pinky_finger_joints(self, side=None):
        return self._get_joints(UnrealSkeleton.PartNames.PINKY, side=side or UnrealSkeleton.PartSides.LEFT)

    def get_ring_finger_joints(self, side=None):
        return self._get_joints(UnrealSkeleton.PartNames.RING, side=side or UnrealSkeleton.PartSides.LEFT)

    def get_thumb_finger_joints(self, side=None):
        return self._get_joints(UnrealSkeleton.PartNames.THUMB, side=side or UnrealSkeleton.PartSides.LEFT)

    def _get_joint_name(self, name, index=None, side=None):
        if index is not None:
            name = '{}_{}'.format(name, index)
        if side is not None:
            name = '{}_{}'.format(name, side)

        for joint in self._joints:
            if dcc.node_short_name(joint) == name:
                return joint

        return None

    def _get_joints(self, part_name, side=None):
        joints = [joint for joint in self._joints if dcc.node_short_name(joint).startswith(part_name)]
        if side:
            joints = [joint for joint in joints if dcc.node_short_name(joint).endswith('_{}'.format(side))]

        return natsort.natsorted(joints)
