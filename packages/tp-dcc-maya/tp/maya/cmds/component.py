#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module include data class for components
"""

import maya.cmds
import maya.OpenMaya
import maya.api.OpenMaya

from tp.common.python import helpers
from tp.maya.cmds import exceptions, node, name as name_utils, shape as shape_utils

component_filter = [28, 30, 31, 32, 34, 35, 36, 37, 38, 46, 47]

mesh_filter = [31, 32, 34, 35]
subd_filter = [36, 37, 38]
nurbs_filter = [28, 30]
curve_filter = [28, 30, 40]
surface_filter = [28, 30, 42]

mesh_vert_filter = 31
mesh_edge_filter = 32
mesh_face_filter = 34

lattice_filter = 46
particle_filter = 47


def is_component(component):
    """
    Returns True if the given object is a valid component
    :param component: str, object t otest as component
    :return: bool
    """

    return bool(maya.cmds.filterExpand(component, ex=True, sm=component_filter))


def get_component_count_api(geometry):
    """
    Returns the number of individual components for the given geometry
    :param geometry: str, geometry to query
    :return: int
    """

    if not maya.cmds.objExists(geometry):
        raise exceptions.GeometryExistsException(geometry)

    geo_obj = node.get_mobject(geometry)
    if geo_obj.hasFn(maya.OpenMaya.MFn.kTransform):
        geometry = maya.cmds.listRelatives(geometry, s=True, ni=True, pa=True)[0]

    geo_path = node.get_mdag_path(geometry)
    geo_it = maya.OpenMaya.MItGeometry(geo_path)

    return geo_it.count()


def get_component_count(transform):
    """
    Returns the number of components under a transform
    :param transform: str, name of the transform
    :return: int, number of components under given transform
    """

    components = get_components(transform)

    return len(maya.cmds.ls(components[0], flatten=True))


def get_components_from_shapes(shapes=None):
    """
    Returns the components from the list of shapes
    Only supports cv and vtx components
    :param shapes: list(str), list of shape names
    :return: list(list), components of the given shapes
    """

    components = list()
    if shapes:
        for shape in shapes:
            found_components = None
            if maya.cmds.nodeType(shape) == 'nurbsSurface' or maya.cmds.nodeType(shape) == 'nurbsCurve':
                found_components = '{}.cv[*]'.format(shape)
            elif maya.cmds.nodeType(shape) == 'mesh':
                found_components = '{}.vtx[*]'.format(shape)
            if found_components:
                components.append(found_components)

    return components


def get_components(transform):
    """
    Returns the name of the components under a transform
    :param transform: str, name of a transform
    :return: name of all components under a transforms
    """

    shapes = shape_utils.get_shapes(transform)
    return get_components_from_shapes(shapes)


def get_components_in_hierarchy(transform):
    """
    Returns all the components in the hierarchy
    This includes all transforms with shapes parented under the transform
    :param transform: str, name of a transform
    :return: list(list), name of all components under transform
    """

    shapes = shape_utils.get_shapes_in_hierarchy(transform)

    return get_components_from_shapes(shapes)


def get_shape_from_component(component, component_name='vtx'):
    """
    Given a component, returns the associated shape
    :param component: str
    :param component_name: str, component type ('vtx', 'e', 'f' or 'cv')
    :return: str
    """

    component_shape = None

    if component.find('.{}['.format(component_name)) > -1:
        split_selected = component.split('.{}['.format(component_name))
        if split_selected > 1:
            component_shape = split_selected[0]

    return component_shape


def is_a_vertex(component_name):
    """
    Returns whether given object is a vertex or not
    :param component_name: str
    :return: bool
    """

    if maya.cmds.objExists(component_name) and component_name.find('.vtx[') > -1:
        return True

    return False


def get_vertex_names_from_indices(mesh, indices):
    """
    Returns a list of vertex names from a given list of face indices
    :param mesh: str
    :param indices: list(int)
    :return: list(str)
    """

    found_vertex_names = list()
    for index in indices:
        vertex_name = '{}.vtx[{}]'.format(mesh, index)
        found_vertex_names.append(vertex_name)

    return found_vertex_names


def get_mesh_from_vertex(vertex):
    """
    Returns corresponding mesh of the given vertex
    :param vertex: str
    :return: str
    """

    return get_shape_from_component(vertex, 'vtx')


def get_edges_in_list(components_list):
    """
    Given a list of mesh components, returns anything that its an edge
    :param components_list: list(str)
    :return: list(str)
    """

    found_edges = list()
    if not components_list:
        return found_edges

    for component in components_list:
        if maya.cmds.nodeType(component) == 'mesh':
            if component.find('.e[') > 0:
                found_edges.append(component)

    return found_edges


def edge_to_vertex(edges):
    """
    Returns the vertices that are part of the given edges
    :param edges: list(str)
    :return: list(str)
    """

    found_vertices = list()

    edges = maya.cmds.ls(edges, flatten=True)
    mesh = edges[0].split('.')[0]

    for edge in edges:
        info = maya.cmds.polyInfo(edge, edgeToVertex=True)[0].split()
        vert1 = info[2]
        vert2 = info[3]
        if vert1 not in found_vertices:
            found_vertices.append('{}.vtx[{}]'.format(mesh, vert1))
        if vert2 not in found_vertices:
            found_vertices.append('{}.vtx[{}]'.format(mesh, vert2))

    return found_vertices


def get_mesh_from_edge(edge):
    """
    Returns mesh that corresponds to the given edge
    :param edge: str
    :return: str
    """

    return get_shape_from_component(edge, 'e')


def get_edge_path(edges=None):
    """
    Returns the edge path of the given list of edges
    :param edges: list(str), list of edges along a path (test.e[0])
    :return: list(str), names of edges in the edge path
    """

    maya.cmds.select(clear=True)
    maya.cmds.polySelectSp(edges, loop=True)

    return maya.cmds.ls(sl=True, long=True)


def edges_to_curve(edges, description=None):
    """
    Creates a new curve taking into account given list of edges
    :param edges: list(str), list of edges names (test.e[0], ...)
    :param description: str, name to give to the new curve
    :return: str, new crated curve
    """

    if not description:
        description = get_mesh_from_edge(edges[0])

    maya.cmds.select(edges)
    curve = maya.cmds.polyToCurve(form=2, degree=3)[0]
    curve = maya.cmds.rename(curve, name_utils.find_unique_name('curve_{}'.format(description)))

    return curve


def get_selected_edges():
    """
    Returns all selected edges components from current selection
    :return: list(str)
    """

    selection = maya.cmds.ls(sl=True, flatten=True)
    return get_edges_in_list(selection)


def get_curve_from_cv(cv):
    """
    Given a single CV, get the corresponding curve
    :param cv: str
    :return: str
    """

    return get_shape_from_component(cv, 'cv')


def get_face_indices(list_of_faces):
    """
    Returns a list of face index numbers from a list of face names
    :param list_of_faces: list(str)
    :return: list(int)
    """

    list_of_faces = helpers.force_list(list_of_faces)
    indices = list()
    for face in list_of_faces:
        index = int(face[face.find('[') + 1:face.find(']')])
        indices.append(index)

    return indices


def get_face_names_from_indices(mesh, indices):
    """
    Returns a list of face names from a given list of face indices
    :param mesh: str
    :param indices: list(int)
    :return: list(str)
    """

    found_face_names = list()
    for index in indices:
        face_name = '{}.f[{}]'.format(mesh, index)
        found_face_names.append(face_name)

    return found_face_names


def get_mesh_from_face(face):
    """
    Given a face name, returns the corresponding mesh
    :param face: str
    :return: str
    """

    return get_shape_from_component(face, 'f')


def faces_to_vertices(faces):
    """
    Converts given faces to vertices
    :param faces: list<str>
    :return: list<str>
    """

    faces = maya.cmds.ls(faces, flatten=True)
    verts = list()

    mesh = faces[0].split('.')[0]
    for face in faces:
        info = maya.cmds.polyInfo(face, faceToVertex=True)[0].split()
        sub_verts = info[2:]
        for sub_vert in sub_verts:
            if sub_vert not in verts:
                verts.append('{}.vtx[{}]'.format(mesh, sub_vert))

    return verts
