# #! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility methods related to Maya rivets
"""

import maya.cmds

from tp.core import dcc
from tp.common.python import helpers, name as name_utils
from tp.common. math import vec3
from tp.maya import api
from tp.maya.cmds import geometry, attribute, transform as transform_utils, mesh as mesh_utils
from tp.maya.cmds import constraint as constraint_utils


class Rivet(object):
    def __init__(self, name):
        self._surface = None
        self._edges = list()
        self._name = name
        self._aim_constraint = None
        self._uv = [0.5, 0.5]
        self._create_joint = False
        self._surface_created = False
        self._percent_on = True
        self._local = False
        self._point_on_surface = None

    @property
    def rivet(self):
        return self._rivet

    def set_surface(self, surface, u, v):
        self._surface = surface
        self._uv = [u, v]

    def set_create_joint(self, flag):
        self._create_joint = flag

    def set_edges(self, edges):
        self._edges = edges

    def set_percent_on(self, flag):
        self._percent_on = flag

    def set_local(self, flag):
        self._local = flag

    def create(self):
        if not self._surface and self._edges:
            self._create_surface()

        self._create_rivet()
        self._create_point_on_surface()
        self._create_aim_constraint()
        self._connect()

        maya.cmds.parent(self._aim_constraint, self._rivet)

        if self._surface_created:
            self._correct_bow_tie()

        return self._rivet

    def _create_surface(self):
        mesh = self._edges[0].split('.')[0]
        shape = geometry.get_mesh_shape(mesh)
        edge_index_1 = name_utils.get_last_number(self._edges[0])
        edge_index_2 = name_utils.get_last_number(self._edges[1])
        vert_iterator = api.IterateEdges(shape)
        vert_ids = vert_iterator.get_connected_vertices(edge_index_1)
        edge_to_curve_1 = maya.cmds.createNode(
            'polyEdgeToCurve', n=dcc.find_unique_name('rivetCurve1_{}'.format(self._name)))
        maya.cmds.setAttr(
            '{}.inputComponents'.format(edge_to_curve_1), 2,
            'vtx[{}]'.format(vert_ids[0]), 'vtx[{}]'.format(vert_ids[1]), type='componentList')
        vert_iterator = api.IterateEdges(shape)
        vert_ids = vert_iterator.get_connected_vertices(edge_index_2)
        edge_to_curve_2 = maya.cmds.createNode(
            'polyEdgeToCurve', n=dcc.find_unique_name('rivetCurve2_{}'.format(self._name)))
        maya.cmds.setAttr(
            '{}.inputComponents'.format(edge_to_curve_2), 2,
            'vtx[{}]'.format(vert_ids[0]), 'vtx[{}]'.format(vert_ids[1]), type='componentList')
        maya.cmds.connectAttr('{}.worldMatrix'.format(mesh), '{}.inputMat'.format(edge_to_curve_1))
        maya.cmds.connectAttr('{}.outMesh'.format(mesh), '{}.inputPolymesh'.format(edge_to_curve_1))
        maya.cmds.connectAttr('{}.worldMatrix'.format(mesh), '{}.inputMat'.format(edge_to_curve_2))
        maya.cmds.connectAttr('{}.outMesh'.format(mesh), '{}.inputPolymesh'.format(edge_to_curve_2))
        loft = maya.cmds.createNode('loft', n=dcc.find_unique_name('rivetLoft_{}'.format(self._name)))
        maya.cmds.setAttr('{}.ic'.format(loft), s=2)
        maya.cmds.setAttr('{}.u'.format(loft), True)
        maya.cmds.setAttr('{}.rsn'.format(loft), True)
        maya.cmds.setAttr('{}.degree'.format(loft), 1)
        maya.cmds.setAttr('{}.autoReverse'.format(loft), 0)
        maya.cmds.connectAttr('{}.oc'.format(edge_to_curve_1), '{}.ic[0]'.format(loft))
        maya.cmds.connectAttr('{}.oc'.format(edge_to_curve_2), '{}.ic[1]'.format(loft))

        self._surface = loft
        self._surface_created = True

    def _create_rivet(self):
        if self._create_joint:
            dcc.clear_selection()
            self._rivet = dcc.create_joint(name=dcc.find_unique_name('joint_{}'.format(self._name)))
        else:
            self._rivet = dcc.create_locator(name=dcc.find_unique_name('rivet_{}'.format(self._name)))

    def _create_point_on_surface(self):
        self._point_on_surface = maya.cmds.createNode(
            'pointOnSurfaceInfo', n=dcc.find_unique_name('pointOnSurface_{}'.format(self._surface)))
        maya.cmds.setAttr('{}.turnOnPercentage'.format(self._point_on_surface), self._percent_on)
        maya.cmds.setAttr('{}.parameterU'.format(self._point_on_surface), self._uv[0])
        maya.cmds.setAttr('{}.parameterV'.format(self._point_on_surface), self._uv[1])

    def _create_aim_constraint(self):
        self._aim_constraint = maya.cmds.createNode(
            'aimConstraint', n=dcc.find_unique_name('aimConstraint_{}'.format(self._surface)))
        maya.cmds.setAttr('{}.aimVector'.format(self._aim_constraint), 0, 1, 0, type='double3')
        maya.cmds.setAttr('{}.upVector'.format(self._aim_constraint), 0, 0, 1, type='double3')

    def _connect(self):
        if maya.cmds.objExists('{}.worldSpace'.format(self._surface)):
            if self._local:
                maya.cmds.connectAttr(
                    '{}.local'.format(self._surface), '{}.inputSurface'.format(self._point_on_surface))
            else:
                maya.cmds.connectAttr(
                    '{}.worldSpace'.format(self._surface), '{}.inputSurface'.format(self._point_on_surface))

        if maya.cmds.objExists('{}.outputSurface'.format(self._surface)):
            maya.cmds.connectAttr(
                '{}.outputSurface'.format(self._surface), '{}.inputSurface'.format(self._point_on_surface))

        maya.cmds.connectAttr('{}.position'.format(self._point_on_surface), '{}.translate'.format(self._rivet))
        maya.cmds.connectAttr(
            '{}.normal'.format(self._point_on_surface), '{}.target[0].targetTranslate'.format(self._aim_constraint))
        maya.cmds.connectAttr(
            '{}.tangentV'.format(self._point_on_surface), '{}.worldUpVector'.format(self._aim_constraint))
        maya.cmds.connectAttr('{}.constraintRotateX'.format(self._aim_constraint), '{}.rotateX'.format(self._rivet))
        maya.cmds.connectAttr('{}.constraintRotateY'.format(self._aim_constraint), '{}.rotateY'.format(self._rivet))
        maya.cmds.connectAttr('{}.constraintRotateZ'.format(self._aim_constraint), '{}.rotateZ'.format(self._rivet))

    def _get_angle(self, surface, flip):
        if flip:
            maya.cmdssetAttr('{}.reverse[0]'.format(self._surface), 1)
        else:
            maya.cmdssetAttr('{}.reverse[0]'.format(self._surface), 0)
        parent_surface = maya.cmds.listRelatives(surface, p=True)[0]
        vector1 = maya.cmds.xforem('{}.cv[0][0]'.format(parent_surface), q=True, ws=True, t=True)
        vector2 = maya.cmds.xforem('{}.cv[0][1]'.format(parent_surface), q=True, ws=True, t=True)
        position = maya.cmds.xform(self._rivet, q=True, ws=True, t=True)
        vector_a = vec3.Vector3(vector1[0], vector1[1], vector1[2])
        vector_b = vec3.Vector3(vector2[0], vector2[1], vector2[2])
        vector_pos = vec3.Vector3(position[0], position[1], position[2])
        vector_1 = vector_a - vector_pos
        vector_2 = vector_b - vector_pos
        vector_1 = vector_1.get_vector()
        vector_2 = vector_2.get_vector()
        angle = maya.cmds.angleBetween(vector_1, vector_2)[-1]

        return angle

    def _correct_bow_tie(self):
        surface = maya.cmds.createNode('nurbsSurface')
        maya.cmds.connectAttr('{}.outputSurface'.format(self._surface), '{}.create'.format(surface))
        angle_1 = self._get_angle(surface, flip=False)
        angle_2 = self._get_angle(surface, flip=True)
        if angle_1 < angle_2:
            maya.cmds.setAttr('{}.reverse[0]'.format(self._surface), 0)
        if angle_1 > angle_2:
            maya.cmds.setAttr('{}.reverse[0]'.format(self._surface), 1)
        parent_surface = maya.cmds.listRelatives(surface, p=True)[0]
        maya.cmds.delete(parent_surface)


def attach_to_mesh(transform, mesh, deform=False, priority=None, face=None, point_constraint=False, auto_parent=False,
                   hide_shape=True, inherit_transform=False, local=False, rotate_pivot=False, constraint=True):
    """
    Attach the center point of a transform (including its hierarchy and shapes) to the mesh using a rivet
    NOTE: If you need to attach to the rotate pivot of the transform make sure to set rotate_pivot = True
    :param transform: str, name of a transform
    :param mesh: str, name of a mesh
    :param deform: bool, Whether to deform into position instead of transform. This will create a cluster
    :param priority: str, name of a transform to attach instead of transform. Useful i you need to attach to something
        close to transform, but actually you want to attach the parent instead
    :param face: int, index of a face on the mesh, to creat the rivet on. Useful i the algorithm does not automatically
        attach to the best face
    :param point_constraint: bool, Whether to attach with just a point constraint or not
    :param auto_parent: bool, Whether to parent the rivet under the same parent as transform
    :param hide_shape: bool, Whether to hide the shape of the rivet locator. Useful when parenting the rivet under a
        control
    :param inherit_transform: bool, Whether to have the inheritTransform attribute of the rivet on or off
    :param local: bool, Whether to constraint the transform to the rivet locally. This allow the rivet to be grouped
        and the group can move without affecting the transform
    :param rotate_pivot: bool, Whether to find the closest face to the rotate pivot of the transform. If not, it will
        search the center of the transform (including shapes)
    :param constraint: bool, Whether to parent the transform under the rivet or not
    :return: str, name of the rivet
    """

    parent = None
    if auto_parent:
        parent = maya.cmds.listRelatives(transform, p=True)
    shape = geometry.get_mesh_shape(mesh)

    if not mesh_utils.is_a_mesh(transform):
        rotate_pivot = True
    if rotate_pivot:
        position = maya.cmds.xform(transform, q=True, rp=True, ws=True)
    else:
        position = transform_utils.get_center(transform)

    if not face:
        try:
            face_fn = api.MeshFunction(shape)
            face_id = face_fn.get_closest_face(position)
        except Exception:
            face_fn = api.IteratePolygonFaces(shape)
            face_id = face_fn.get_closest_face(position)

    if face:
        face_id = face

    face_iter = api.IteratePolygonFaces(shape)
    edges = face_iter.get_edges(face_id)
    edge_1 = '{}.e[{}]'.format(mesh, edges[0])
    edge_2 = '{}.e[{}]'.format(mesh, edges[2])

    transform = helpers.force_list(transform)
    if not priority:
        priority = transform[0]

    rivet = Rivet(priority)
    rivet.set_edges([edge_1, edge_2])
    rivet = rivet.create()
    orig_rivet = rivet
    rivet = maya.cmds.group(empty=True, n='offset_{}'.format(rivet), p=orig_rivet)
    transform_utils.MatchTransform(orig_rivet, rivet).translation_rotation()

    if deform:
        for xform in transform:
            cluster, handle = maya.cmds.cluster(xform, n=dcc.find_unique_name('rivetCluster_{}'.format(xform)))
            maya.cmds.hide(handle)
            maya.cmds.parent(handle, rivet)

    if constraint:
        if not deform and not local:
            for xform in transform:
                if point_constraint:
                    maya.cmds.pointConstraint(rivet, xform, mo=True)
                else:
                    maya.cmds.parentConstraint(rivet, xform, mo=True)

        if local and not deform:
            for xform in transform:
                if point_constraint:
                    local, xform = constraint_utils.constraint_local(rivet, xform, constraint='pointConstraint')
                else:
                    local, xform = constraint_utils.constraint_local(rivet, xform, constraint='parentConstraint')
                if auto_parent:
                    maya.cmds.parent(xform, parent)
                attribute.connect_transforms(orig_rivet, xform)
    else:
        maya.cmds.parenet(transform, rivet)

    if not inherit_transform:
        maya.cmds.setAttr('{}.inheritsTransform'.format(orig_rivet), 0)

    if parent and auto_parent:
        maya.cmds.parent(rivet, parent)

    if hide_shape:
        maya.cmds.hide('{}Shape'.format(orig_rivet))

    return orig_rivet


def attach_to_surface(transform, surface, u=None, v=None, constraint=True):
    """
    Attach the transform to the surface using a rivet
    :param transform: str, name of a transform
    :param surface: str, name of the surface to attach transform to
    :param u: float, U value to attach hto
    :param v: float, V value to attach to
    :param constraint: bool
    :return: str, name of the rivet
    """

    position = maya.cmds.xform(transform, query=True, ws=True, t=True)
    uv = [u, v]
    if not u or not v:
        uv = geometry.get_closest_parameter_on_surface(surface, position)

    rivet = Rivet(transform)
    rivet.set_surface(surface, uv[0], uv[1])
    rivet.set_create_joint(False)
    rivet.set_percent_on(False)
    rivet.create()

    if constraint:
        loc = maya.cmds.spaceLocator(n='locator_{}'.format(rivet.rivet))[0]
        maya.cmds.parent(loc, rivet.rivet)
        transform_utils.MatchTransform(transform, loc).translation_rotation()
        maya.cmds.parentConstraint(loc, transform, mo=True)
    else:
        maya.cmds.parent(transform, rivet.rivet)

    return rivet.rivet
