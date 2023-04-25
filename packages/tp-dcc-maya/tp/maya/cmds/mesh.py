#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with meshes
"""

from collections import defaultdict

import maya.cmds
import maya.mel
import maya.api.OpenMaya

from tp.core import log
from tp.common.python import helpers
from tp.maya import api
from tp.maya.cmds import helpers as maya_helpers, exceptions, node

logger = log.tpLogger


def check_mesh(mesh):
    """
    Checks if a node is a valid mesh and raise a exception if the mesh is not valid
    :param mesh: str, name of the mesh to be checked
    :return: bool, True if the given ode is a mesh node
    """

    if not is_mesh(mesh):
        raise exceptions.MeshException(mesh)


def is_a_mesh(mesh):
    """
    Checks whether the given node is a mesh or has a shape that is a mesh
    :param mesh: str
    :return: bool
    """

    return maya.cmds.objExists('{}.vtx[0]'.format(mesh))


def is_mesh(mesh):
    """
    Check if the given object is a polygon mesh or transform parent of a mesh
    :param mesh: str, object to query
    :return: bool
    """

    if not maya.cmds.objExists(mesh):
        return False

    if 'transform' in maya.cmds.nodeType(mesh, i=True):
        mesh_shape = maya.cmds.ls(maya.cmds.listRelatives(mesh, s=True, ni=True, pa=True) or [], type='mesh')
        if not mesh_shape:
            return False
        mesh = mesh_shape[0]

    if maya.cmds.objectType(mesh) != 'mesh':
        return False

    return True


def get_meshes_from_nodes(nodes, search_child_node=False, full_path=False, mesh=True, nurbs=False):
    """
    Function that returns polygon meshes from given nodes
    :param nodes: list(str)
    :param search_child_node: bool
    :param full_path: bool
    :param mesh: bool
    :param nurbs: bool
    :return: list(str)
    """

    nodes = helpers.force_list(nodes)
    polygon_meshes = list()

    if search_child_node:
        parent_nodes = nodes
        for n in parent_nodes:
            try:
                found_nodes = maya.cmds.listRelatives(n, ad=True, c=True, type='transform', fullPath=full_path, s=False)
            except Exception:
                pass
            if found_nodes is not None:
                nodes += found_nodes

    for n in nodes:
        if mesh:
            try:
                mesh_node = maya.cmds.listRelatives(n, s=True, pa=True, type='mesh', fullPath=True)
                if mesh_node:
                    polygon_meshes.append(n)
            except Exception:
                pass
        if nurbs:
            try:
                nurbs_node = maya.cmds.listRelatives(s=True, pa=True, type='nurbsSurface', fullPath=True)
                if nurbs_node:
                    polygon_meshes.append(nurbs_node)
            except Exception:
                pass

    if len(polygon_meshes) > 0:
        return polygon_meshes
    else:
        return list()


def is_open(mesh):
    """
    Check if the given mesh is a closed surface or has boundary components
    :param mesh: str, mesh to check for boundary conditions
    :return: bool
    """

    check_mesh(mesh)

    sel = maya.cmds.ls(sl=True)
    maya.cmds.select(mesh)
    maya.cmds.polySelectConstraint(mode=3, type=1, where=1)
    boundary_sel = maya.cmds.ls(sl=True, fl=True)

    if sel:
        maya.cmds.select(sel)

    return bool(boundary_sel)


def get_mesh_fn(mesh):
    """
    Creates an MFnMesh class object from the given polygon mesh
    :param mesh: str, mesh to create function class for
    :return: MFnMesh
    """

    check_mesh(mesh)

    if maya.cmds.objectType(mesh) == 'transform':
        mesh = maya.cmds.listRelatives(mesh, s=True, ni=True, pa=True)[0]

    mesh_path = node.get_mdag_path(mesh)
    mesh_fn = maya.api.OpenMaya.MFnMesh(mesh_path)

    return mesh_fn


def get_mesh_vertex_iter(mesh, vtx_id=None):
    """
    Creates an MItMeshVertex class object from the given polygon mesh
    :param mesh: str, mesh to create function class for
    :param vtx_id: int, vertex ID to initialize iterator to
    :return: MItMeshVertex
    """

    check_mesh(mesh)

    if maya.cmds.objectType(mesh) == 'transform':
        mesh = maya.cmds.listRelatives(mesh, s=True, ni=True, pa=True)[0]

    mesh_path = node.get_mdag_path(mesh)
    mesh_vtx_it = maya.api.OpenMaya.MItMeshVertex(mesh_path)

    # Initialize vertexId
    if vtx_id is not None:
        mesh_vtx_it.setIndex(vtx_id)

    return mesh_vtx_it


def get_mesh_face_iter(mesh, face_id=None):
    """
    Creates an MItMeshPolygon class object from the given polygon mesh
    :param mesh: str, mesh to create function class for
    :param face_id: int, face ID to initialize iterator to
    :return: MItMeshPolygon
    """

    check_mesh(mesh)

    if maya.cmds.objectType(mesh) == 'transform':
        mesh = maya.cmds.listRelatives(mesh, s=True, ni=True, pa=True)[0]

    mesh_path = node.get_mdag_path(mesh)
    mesh_face_it = maya.api.OpenMaya.MItMeshPolygon(mesh_path)

    # Initialize faceId
    if face_id is not None:
        mesh_face_it.setIndex(face_id)

    return mesh_face_it


def get_mesh_edge_iter(mesh, edge_id=None):
    """
    Creates an MItMeshEdge class object from the given polygon mesh
    :param mesh: str, mesh to create function class for
    :param face_id: int, edge ID to initialize iterator to
    :return: MItMeshEdge
    """

    check_mesh(mesh)

    if maya.cmds.objectType(mesh) == 'transform':
        mesh = maya.cmds.listRelatives(mesh, s=True, ni=True, pa=True)[0]

    mesh_path = node.get_mdag_path(mesh)
    mesh_edge_it = maya.api.OpenMaya.MItMeshEdge(mesh_path)

    # Initialize faceId
    if edge_id is not None:
        mesh_edge_it.setIndex(edge_id)

    return mesh_edge_it


def get_raw_points(mesh):
    """
    Get mesh verices positions via the MFnMesh.getRawPoints() function
    :param mesh: str, mesh to get vertex positions for
    :return:
    """

    # get_raw_points function is dependant of MFnMesh.getRawPoints() function which is not available  in OpenMaya2

    check_mesh(mesh)

    mesh_fn = get_mesh_fn(mesh)
    mesh_pts = mesh_fn.getRawPoints()

    return mesh_pts


def get_points(mesh, flatten=False):
    """
    Get mesh vertex positions via the MFnMesh.getRawPoints() function
    :param mesh: str, mesh to get vertex positions for
    :param flatten: bool, Whether to force mesh points to be stored as sub lists instead of MFloatPoints
    :return: list
    """

    check_mesh(mesh)

    mesh_fn = get_mesh_fn(mesh)

    mesh_pt_array = list(mesh_fn.getFloatPoints())
    if flatten:
        mesh_pt_array = [list(pt) for pt in mesh_pt_array]

    return mesh_pt_array


def get_normal(mesh, vtx_id, world_space=False, angle_weighted=False):
    """
    Returns the vertex normal for the give nvertex of a given mesh
    :param mesh: str, mesh to query normal from
    :param vtx_id: int, vertex index to query normal from
    :param world_space: bool, sample the normal direction in world space
    :param angle_weighted: bool, If True, normal is computed taking in account the angle subtended by
        the face at the vertex
    """

    check_mesh(mesh)

    mesh_fn = get_mesh_fn(mesh)

    # Get sample space
    if world_space:
        sample_space = maya.api.OpenMaya.MSpace.kWorld
    else:
        sample_space = maya.api.OpenMaya.MSpace.kObject

    normal = mesh_fn.getVertexNormal(vtx_id, angle_weighted, sample_space)

    return normal


def get_normals(mesh, world_space=False, angle_weighted=False):
    """
    Returns all vertex normals for the given mesh
    :param mesh: str, mesh to query normals from
    :param world_space: bool, sample the normals direction in world space
    :param angle_weighted: bool, If True, normal is computed taking in account the angle subtended by
        the face at the vertex
    :return: list<float>
    """

    check_mesh(mesh)

    mesh_fn = get_mesh_fn(mesh)

    # Get sample space
    if world_space:
        sample_space = maya.api.OpenMaya.MSpace.kWorld
    else:
        sample_space = maya.api.OpenMaya.MSpace.kObject

    normals = mesh_fn.getVertexNormals(angle_weighted, sample_space)

    return normals


def get_uvs(mesh, uv_set=None):
    """
    Get mesh UV coordinates for the given mesh and in the given UV set
    :param mesh: str, mesh to get UV from
    :param uv_set: str, Mesh UV set to get UVs from. If None, current UV set is used
    :return: list, list
    """

    check_mesh(mesh)
    if uv_set and uv_set not in maya.cmds.polyUVSet(mesh, allUVSets=True):
        raise exceptions.MeshNoUVSetException(mesh, uv_set)

    mesh_fn = get_mesh_fn(mesh)

    if uv_set is not None:
        u_array, v_array = mesh_fn.getUVs(uv_set)
    else:
        u_array, v_array = mesh_fn.getUVs()

    return list(u_array), list(v_array)


def get_assigned_uvs(mesh, uv_set=None):
    """
    Get mesh UV assignments for the given mesh and in the given UV set
    :param mesh: str, mesh to get UV from
    :param uv_set: str, Mesh UV set to get UVs from. If None, current UV set is used
    :return: list, list
    """

    check_mesh(mesh)
    if uv_set and uv_set not in maya.cmds.polyUVSet(mesh, allUVSets=True):
        raise exceptions.MeshNoUVSetException(mesh, uv_set)

    mesh_fn = get_mesh_fn(mesh)

    if uv_set is not None:
        uv_count, uv_ids = mesh_fn.getAssignedUVs(uv_set)
    else:
        uv_count, uv_ids = mesh_fn.getAssignedUVs()

    return list(uv_count), list(uv_ids)


def get_connected_vertices(mesh, vertex_selection_set):
    """
    Get list of connected vertices in groups
    :param mesh: str, name of the mesh to get vertices from
    :param vertex_selection_set: list<str>, list with vertices indices to get connected vertices of
    :return:
    """

    # TODO: We need to rewrite this function to make it compatible with Maya API 1 and 2

    def get_neighbour_vertices(curr_vert_iter, vert_index):
        """
        Get neighbour of given vertex index
        :param curr_vert_iter: MItMeshVertex, iterator used to loop through all mesh vertices
        :param vert_index: int, current vertex index being processed
        :return: set<int>
        """

        curr_vert_iter.setIndex(vert_index, maya.api.OpenMaya.MScriptUtil().asIntPtr())
        int_array = maya.api.OpenMaya.MIntArray()
        curr_vert_iter.getConnectedVertices(int_array)

        return set(int(x) for x in int_array)

    # Set (non repeated elements) of already visited vertices
    visited_neighbours = set()
    district_dict = defaultdict(list)
    district_number = 0

    dep_node = node.depend_node(node_name=mesh)

    vert_iter = maya.api.OpenMaya.MItMeshVertex(dep_node)
    for index in vertex_selection_set:
        district_houses = set()
        if index not in visited_neighbours:
            district_houses.add(index)
            current_neighbours = get_neighbour_vertices(vert_iter, index)

            while current_neighbours:
                new_neighbours = set()
                for neighbour in current_neighbours:
                    if neighbour in vertex_selection_set and neighbour not in visited_neighbours:
                        visited_neighbours.add(neighbour)
                        district_houses.add(neighbour)
                        new_neighbours = new_neighbours.union(get_neighbour_vertices(vert_iter, neighbour))

                current_neighbours = new_neighbours

            district_dict[district_number] = district_houses
            district_number += 1

        vert_iter.setIndex(index, maya.api.OpenMaya.MScriptUtil().asIntPtr())
        vert_iter.next()

    return district_dict


def convert_to_vertices(obj):
    """
    Converts every poly selection to vertices
    :param obj: variant, can be the mesh transform, the mesh shape or component based selection
    """

    check_object = obj
    if isinstance(obj, list):
        check_object = obj[0]

    obj_type = maya.cmds.objectType(check_object)
    check_type = check_object
    if obj_type == 'transform':
        shapes = node.shape(node_name=obj)
        if shapes:
            if type(shapes) in [list, tuple]:
                check_type = shapes[0]
            else:
                check_type = shapes
        else:
            check_type = obj

    obj_type = maya.cmds.objectType(check_type)
    if obj_type == 'mesh':
        converted_vertices = maya.cmds.polyListComponentConversion(obj, toVertex=True)
        return maya.cmds.filterExpand(converted_vertices, selectionMask=maya_helpers.SelectionMasks.PolygonVertices)

    if obj_type == 'nurbsCurve' or obj_type == 'nurbsSurface':
        if isinstance(obj, list) and '.cv' in obj[0]:
            return maya.cmds.filterExpand(object, selectionMask=maya_helpers.SelectionMasks.CVs)
        elif '.cv' in obj:
            return maya.cmds.filterExpand(obj, selectionMask=maya_helpers.SelectionMasks.CVs)
        else:
            return maya.cmds.filterExpand('{}cv[*]'.format(obj[0], selectionMask=maya_helpers.SelectionMasks.CVs))

    if obj_type == 'lattice':
        if isinstance(obj, list) and '.pt' in obj[0]:
            return maya.cmds.filterExpand(obj, selectionMask=maya_helpers.SelectionMasks.LatticePoints)
        elif '.pt' in obj:
            return maya.cmds.filterExpand(obj, selectionMask=maya_helpers.SelectionMasks.LatticePoints)
        else:
            return maya.cmds.filterExpand(obj, selectionMask=maya_helpers.SelectionMasks.LatticePoints)


def convert_to_faces(obj):
    """
    Converts every poly selection to faces
    :param obj: variant, can be the mesh transform, the mesh shape or component based selection
    """

    converted_faces = maya.cmds.polyListComponentConversion(obj, toFace=True)
    return maya.cmds.filterExpand(converted_faces, selectionMask=maya_helpers.SelectionMasks.PolygonFace)


def convert_to_indices(vert_list):
    """
    Convert given flattened components list to vertices index list
    :param vert_list: list<str>, list of flattened vertices to convert
    # NOTE: Vertices list must follow Maya vertices list convention: ['{object_name}.v[0]', '{object_name}.v[1]' ...]
    :return: list<str>, [0, 1, 2, 3 ...]
    """

    indices = list()
    for i in vert_list:
        index = int(i.split('[')[-1].split(']')[0])
        indices.append(index)

    return indices


def convert_indices_to_vertices(index_list, mesh):
    """
    Convert given flattened index list to vertices list
    :param index_list: list<str>, list of flattened index to convert
    :param mesh: str: mesh vertices belong to
    :return: list<str>
    """

    vertices = list()
    for i in list(index_list):
        vertex = '{0}.vtx[{1}]'.format(mesh, i)
        vertices.append(vertex)

    return vertices


def convert_vertex_to_edge_indices(vtx):
    """
    Gets edges indices the  given vertex belongs to
    :param vtx: str, vertex in Maya format (vtx[index])
    :return: list<int>, edge indices the given vertex belongs to
    """

    to_edges = maya.cmds.polyListComponentConversion(vtx, toEdge=True)
    edges = maya.cmds.filterExpand(to_edges, selectionMask=maya_helpers.SelectionMasks.PolygonEdges)
    edge_numbers = list()
    for e in edges:
        edge_numbers.append(int(e.split('.e[').split(']')[0]))

    return edge_numbers


def check_edge_loop(mesh, vtx1, vtx2, first=True):
    """
    Check if the given vertices belongs to the same edge loop
    :param mesh: str
    :param vtx1: str
    :param vtx2: str
    :param first: bool
    :return: bool
    """

    edges1 = convert_vertex_to_edge_indices(vtx1)
    edges2 = convert_vertex_to_edge_indices(vtx2)
    for e1 in edges1:
        for e2 in edges2:
            edge_sel = maya.cmds.polySelect(mesh, edgeLoopPath=[e1, e2], noSelection=True)
            if edge_sel is None:
                continue
            if len(edge_sel) > 40 and first:
                continue

            return True

    return False


def edges_to_smooth(edges_list):
    """
    :param edges_list: str, list of flattened edges to convert
    # NOTE: Edges list must follow Maya edge list convention: ['{object_name}.e[0]', '{object_name}.e[1]' ...]
    """
    mesh = edges_list[0].split('.')[0]
    node.check_node(mesh)

    selected_vertices = convert_to_vertices(obj=edges_list)
    selected_indices = convert_to_indices(selected_vertices)

    selection_lists = get_connected_vertices(mesh=mesh, vertex_selection_set=selected_indices)
    list1 = convert_indices_to_vertices(index_list=selection_lists[0], mesh=mesh)
    list2 = convert_indices_to_vertices(index_list=selection_lists[1], mesh=mesh)

    base_list = list()
    fixed = list()
    for vert1 in list1:
        for vert2 in list2:
            if not check_edge_loop(mesh, vert1, vert2):
                continue
            base_list.append([vert1, vert2])
            fixed.extend([vert1, vert2])

    # Quick fix to avoid taking the longest loop first
    for vert1 in list1:
        for vert2 in list2:
            if vert1 in fixed or vert2 in fixed:
                continue
            if not check_edge_loop(mesh, vert1, vert2, False):
                continue
            base_list.append([vert1, vert2])

    return base_list


def get_closest_position_on_mesh(mesh, value_list):
    """
    Returns the closest position on a mesh from the given point
    :param mesh: str,l name of a mesh
    :param value_list: list(float, float, float), position to search from
    :return:list(float, float, float(, position on the mesh that's closest
    """

    mesh_fn = api.MeshFunction(mesh)
    position = mesh_fn.get_closest_position(value_list)

    return position


def get_closest_normal_on_mesh(mesh, value_list):
    """
    Returns the closest normal on the surface given vector
    :param mesh: str, name of the surface
    :param value_list:
    :return:
    """

    mesh_fn = api.MeshFunction(mesh)
    normal = mesh_fn.get_closest_normal(value_list)

    return normal


def get_closest_uv_on_mesh(mesh, value_list):
    """
    Returns the closest UV on a mesh given a vector
    :param mesh: str, name of a mesh wit UVs
    :param value_list: list(float, float, float), position vector from which to find the closest UV
    :return: list(int, int), UV that is closest to the given vector
    """

    mesh = api.MeshFunction(mesh)
    closest_uv = mesh.get_uv_at_point(value_list)

    return closest_uv


def find_shortest_vertices_path_between_vertices(vertices_list):

    start = vertices_list[0]
    end = vertices_list[-1]
    start = start[1:] if start.startswith('|') else start
    end = end[1:] if end.startswith('|') else end
    mesh = start.split('.')[0]

    obj_type = maya.cmds.objectType(mesh)
    if obj_type != 'mesh':
        return None

    first_extended_edges = maya.cmds.polyListComponentConversion(start, toEdge=True)
    first_extended = maya.cmds.filterExpand(first_extended_edges, selectionMask=maya_helpers.SelectionMasks.PolygonEdges)
    second_extended_edges = maya.cmds.polyListComponentConversion(end, toEdge=True)
    second_extended = maya.cmds.filterExpand(second_extended_edges, selectionMask=maya_helpers.SelectionMasks.PolygonEdges)

    found = list()
    for e1 in first_extended:
        for e2 in second_extended:
            e1_num = int(e1.split('.e[')[-1].split(']')[0])
            e2_num = int(e2.split('.e[')[-1].split(']')[0])
            edge_sel = maya.cmds.polySelect(mesh, edgeLoopPath=[e1_num, e2_num], noSelection=True)
            if edge_sel is None:
                continue
            found.append(edge_sel)

    total_found = len(found)
    if total_found != 0:
        edge_selection = found[0]
        if total_found != 1:
            for sep_list in found:
                if not len(sep_list) < len(edge_selection):
                    continue
                edge_selection = sep_list
    else:
        vtx_num1 = int(start.split('vtx[')[-1].split(']')[0])
        vtx_num2 = int(end.split('vtx[')[-1].split(']')[0])
        edge_selection = maya.cmds.polySelect(mesh, shortestEdgePath=[vtx_num1, vtx_num2])
        if edge_selection is None:
            logger.error('Selected vertices are not part of the same polyShell!')
            return None

    all_edges = list()
    new_vertex_selection = list()
    for edge in edge_selection:
        all_edges.append('{}.e[{}]'.format(mesh, edge))
        mid_expand = convert_to_vertices('{}.e[{}]'.format(mesh, edge))
        new_vertex_selection.append(mid_expand)

    reverse = False if start in new_vertex_selection[0] else True
    in_order = list()
    last_vertex = None
    for list_vertices in new_vertex_selection:
        if start in list_vertices:
            list_vertices.remove(start)
        if last_vertex is not None and last_vertex in list_vertices:
            list_vertices.remove(last_vertex)
        if end in list_vertices:
            list_vertices.remove(end)
        if len(list_vertices) != 0:
            last_vertex = list_vertices[0]
            in_order.append(last_vertex)

    if end not in in_order:
        in_order.insert(0, end)

    if reverse:
        in_order.reverse()

    return in_order


def fix_mesh_components_selection_visualization(mesh):
    """
    Cleanup selection details in Maya so given mesh selection components visualization is correct
    :param mesh: str, name of the mesh (shape or transform) components we want to visualize
    """

    object_type = maya.cmds.objectType(mesh)
    if object_type == 'transform':
        shape = maya.cmds.listRelatives(mesh, children=True, shapes=True)[0]
        object_type = maya.cmds.objectType(shape)

    maya.mel.eval('if( !`exists doMenuComponentSelection` ) eval( "source dagMenuProc" );')
    if object_type == "nurbsSurface" or object_type == "nurbsCurve":
        maya.mel.eval('doMenuNURBComponentSelection("%s", "controlVertex");' % mesh)
    elif object_type == "lattice":
        maya.mel.eval('doMenuLatticeComponentSelection("%s", "latticePoint");' % mesh)
    elif object_type == "mesh":
        maya.mel.eval('doMenuComponentSelection("%s", "vertex");' % mesh)
