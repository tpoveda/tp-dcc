#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Maya Cloth System (nCloth)
"""

import maya.cmds

from tp.core import log
from tp.maya.cmds import attribute as attr_utils

logger = log.tpLogger


def add_ncloth_to_mesh(mesh, world=False):
    maya.cmds.select(clear=True)

    world_flag = 1 if world else 0
    nodes = maya.mel.eval('createNCloth {};'.format(world_flag))
    if not nodes:
        logger.warning('No NCloth created on given mesh: "{}"'.format(mesh))
        return False

    if world:
        output_mesh = attr_utils.attribute_outputs('{}.outputMesh'.format(nodes[0]), node_only=True)
        world_mesh = maya.cmds.rename(output_mesh, 'world_{}'.format(mesh))
        parent = maya.cmds.listRelatives(mesh, p=True)
        if parent:
            maya.cmds.parent(world_mesh, parent[0])

    parent = maya.cmds.listRelatives(nodes[0], p=True)
    parent = maya.cmds.rename(parent, 'nCloth_{}'.format(mesh))
    maya.cmds.setAttr('{}.thickness'.format(parent), 0.02)

    return parent
