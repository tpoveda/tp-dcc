#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Maya API
"""

from __future__ import print_function, division, absolute_import

from maya.api import OpenMaya, OpenMayaRender, OpenMayaUI, OpenMayaAnim

from tp.maya.api.types import *
from tp.maya.api.attributetypes import *
from tp.maya.api import consts
from tp.maya.api import factory
from tp.maya.api import env
from tp.maya.api.base import (
	node_by_name, nodes_by_names, nodes_by_type_names, node_by_object, iterate_selected, selected, select,
	lock_node_context, plug_by_name, lock_node_plug_context, lock_state_attr_context, DGNode, DagNode, ObjectSet,
	ContainerAsset, SkinCluster, BlendShape, DisplayLayer, Mesh, NurbsCurve, IkHandle, Joint, Plug,
	LOCAL_TRANSLATE_ATTRS, LOCAL_ROTATE_ATTRS, LOCAL_SCALE_ATTRS, LOCAL_TRANSFORM_ATTRS
)
from tp.maya.api.spaceswitch import (
	CONSTRAINT_TYPES, CONSTRAINT_CLASSES, TP_CONSTRAINTS_ATTR_NAME, build_constraint, iterate_constraints
)
from tp.maya.api.animation import set_rotation_order_over_frames
from tp.maya.api.nodes import root_node, average_position, average_normal_vector
from tp.maya.om.utils import is_valid_mobject, is_valid_mobject_handle, int_to_mtransform_rotation_order
from tp.maya.om.mathlib import (
	X_AXIS_VECTOR, Y_AXIS_VECTOR, Z_AXIS_VECTOR, X_AXIS_INDEX, Y_AXIS_INDEX, Z_AXIS_INDEX, AXIS_VECTOR_BY_INDEX,
	AXIS_NAME_BY_INDEX, AXIS_INDEX_BY_NAME, is_vector_negative, two_point_normal, three_point_normal,
	closest_point_on_plane, perpendicular_axis_from_align_vectors, look_at
)
