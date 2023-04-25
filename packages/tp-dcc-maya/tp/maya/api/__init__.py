#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Maya API
"""

from __future__ import print_function, division, absolute_import

from tp.maya.api.types import *
from tp.maya.api.attributetypes import *

from tp.maya.api import consts
from tp.maya.api import factory
from tp.maya.api import env
from tp.maya.api.base import (
	node_by_name, nodes_by_names, nodes_by_type_names, node_by_object, iterate_selected, selected, select, DGNode,
	DagNode, ObjectSet, ContainerAsset, SkinCluster, BlendShape, DisplayLayer, Mesh, NurbsCurve, IkHandle
)
from tp.maya.api.spaceswitch import (
	CONSTRAINT_TYPES, CONSTRAINT_CLASSES, CONSTRAINTS_ATTR_NAME, build_constraint, iterate_constraints
)
from tp.maya.api.animation import set_rotation_order_over_frames
from tp.maya.api.nodes import root_node
