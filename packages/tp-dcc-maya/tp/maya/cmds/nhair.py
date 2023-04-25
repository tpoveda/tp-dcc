#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Maya Hair System (nHair)
"""

import maya.cmds

from tp.common.python import helpers
from tp.maya.cmds import name as name_utils, attribute as attr_utils


def create_hair_system(name=None, nucleus_node=None):
    """
    Creates a new hair system (nHair)
    :param name: str, name of the hair system.
    :param nucleus_node: str, name of a nucleus node to attach to the hair system
    :return: list(str, str), [hair system, hair system shape]
    """

    name = 'hairSystem_{}'.format(name) if name else 'hairSystem'
    hair_system_shape = maya.cmds.createNode('hairSystem')
    hair_system = maya.cmds.listRelatives(hair_system_shape, p=True)
    hair_system = maya.cmds.rename(hair_system, name_utils.find_unique_name(name))
    hair_system_shape = maya.cmds.listRelatives(hair_system, shapes=True)[0]
    maya.cmds.connectAttr('time1.outTime', '{}.currentTime'.format(hair_system_shape))

    if nucleus_node:
        connect_hair_system_to_nucleus(hair_system, nucleus_node)

    return hair_system, hair_system_shape


def connect_hair_system_to_nucleus(hair_system, nucleus_node):
    """
    Connects given hair system to given nucleus node
    :param hair_system: str, name of a hair system (nHair)
    :param nucleus_node: str, name of a nucleus node
    """

    hair_system_shape = maya.cmds.listRelatives(hair_system, shapes=True)[0]
    maya.cmds.connectAttr('{}.startFrame'.format(nucleus_node), '{}.startFrame'.format(hair_system_shape))
    indices = attr_utils.indices('{}.inputActive'.format(nucleus_node))
    current_index = indices[-1] + 1 if indices else 0
    maya.cmds.connectAttr(
        '{}.currentState'.format(hair_system_shape), '{}.inputActive[{}]'.format(nucleus_node, current_index))
    maya.cmds.connectAttr(
        '{}.startState'.format(hair_system_shape), '{}.inputActiveStart[{}]'.format(nucleus_node, current_index))
    maya.cmds.connectAttr(
        '{}.outputObjects[{}]'.format(nucleus_node, current_index), '{}.nextState'.format(hair_system_shape))
    maya.cmds.setAttr('{}.active'.format(hair_system_shape), 1)
    maya.cmds.refresh()


def create_hair_follicle(name=None, hair_system=None, uv=None):
    """
    Creates a new hair follicle
    :param name: str, name of the follicle
    :param hair_system: str, name of the hair system we want to connect follicle into
    :param uv: list(float, float), follicle uvs
    :return: list(str, str), [follicle name, follicle shape name]
    """

    name = 'follicle_{}'.format(name) if name else 'follicle'
    uv = helpers.force_list(uv)
    follicle_shape = maya.cmds.createNode('follicle')
    follicle = maya.cmds.listRelatives(follicle_shape, p=True)
    follicle = maya.cmds.rename(follicle, name_utils.find_unique_name(name))
    follicle_shape = maya.cmds.listRelatives(follicle, shapes=True)[0]
    maya.cmds.setAttr('{}.startDirection'.format(follicle_shape), 1)
    maya.cmds.setAttr('{}.restPose'.format(follicle_shape), 1)
    maya.cmds.setAttr('{}.degree'.format(follicle_shape), 3)
    if uv:
        maya.cmds.setAttr('{}.parameterU'.format(follicle), uv[0])
        maya.cmds.setAttr('{}.parameterV'.format(follicle), uv[1])
    if hair_system:
        connect_follicle_to_hair_system(follicle, hair_system)
    maya.cmds.connectAttr('{}.outTranslate'.format(follicle_shape), '{}.translate'.format(follicle))
    maya.cmds.connectAttr('{}.outRotate'.format(follicle_shape), '{}.rotate'.format(follicle))


def connect_follicle_to_hair_system(follicle, hair_system):
    """
    Connects given follicle to given hair system (nCloth)
    :param follicle: str, name of the follicle we want to connect
    :param hair_system: str, name of the hair system
    """

    indices = attr_utils.indices('{}.inputHair'.format(hair_system))
    current_index = indices[-1] + 1 if indices else 0
    maya.cmds.connectAttr('{}.outHair'.format(follicle), '{}.inputHair[{}]'.format(hair_system, current_index), f=True)
    maya.cmds.connectAttr(
        '{}.outputHair[{}]'.format(hair_system, current_index), '{}.currentPosition'.format(follicle), f=True)
