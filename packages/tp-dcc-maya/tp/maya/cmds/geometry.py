#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with geometry
"""

import re

import maya.cmds
import maya.api.OpenMaya

from tp.core import log
from tp.common.python import helpers
from tp.common.math import vec3, octree, dijkstra
from tp.maya import api
from tp.maya.cmds import helpers, exceptions, shape, scene, transform as xform_utils, name as name_utils
from tp.maya.cmds import joint as joint_utils, component as cmp_utils, shape as shape_utils

logger = log.tpLogger


class MeshTopologyCheck(object):
    def __init__(self, mesh1, mesh2):

        self.mesh1 = None
        self.mesh1_function = None
        self.mesh1_vert_count = None
        self.mesh1_edge_count = None
        self.mesh1_face_count = None

        self.mesh2 = None
        self.mesh2_function = None
        self.mesh2_vert_count = None
        self.mesh2_edge_count = None
        self.mesh2_face_count = None

        self.set_first_mesh(mesh1)
        self.set_second_mesh(mesh2)

    # region Public Functions
    def set_first_mesh(self, mesh):
        """
        Sets the first mesh to compare
        :param mesh: str, name of  the mesh
        """

        self.mesh1 = get_mesh_shape(mesh, 0)
        self.mesh1_function = api.MeshFunction(self.mesh1)
        self.mesh1_vert_count = self.mesh1_function.get_number_of_vertices()
        self.mesh1_edge_count = self.mesh1_function.get_number_of_edges()
        self.mesh1_face_count = self.mesh1_function.get_number_of_faces()

    def set_second_mesh(self, mesh):
        """
        Sets the second mesh to compare
        :param mesh: str, name of  the mesh
        """

        self.mesh2 = get_mesh_shape(mesh, 0)
        self.mesh2_function = api.MeshFunction(self.mesh2)
        self.mesh2_vert_count = self.mesh2_function.get_number_of_vertices()
        self.mesh2_edge_count = self.mesh2_function.get_number_of_edges()
        self.mesh2_face_count = self.mesh2_function.get_number_of_faces()

    def check_vert_count(self):
        """
        Returns whether both meshes have same number of vertices
        :return: bool
        """

        return self.mesh1_vert_count == self.mesh2_vert_count

    def check_edge_count(self):
        """
        Returns whether both meshes have same number of edges
        :return: bool
        """

        return self.mesh1_edge_count == self.mesh2_edge_count

    def check_face_count(self):
        """
        Returns whether both meshes have same number of faces
        :return: bool
        """

        return self.mesh1_face_count == self.mesh2_face_count

    def check_vert_face_count(self):
        """
        Returns whether both meshes have same number of faces and vertices
        :return: bool
        """

        if not self.check_face_count():
            return False

        if not self.check_vert_count():
            return False

        return True

    def check_vert_edge_face_count(self):
        """
        Returns whether both meshes have same number of faces, vertices and edges
        :return: bool
        """

        if not self.check_face_count():
            return False

        if not self.check_vert_count():
            return False

        if not self.check_edge_count():
            return False

        return True

    def check_first_face_verts(self):
        """
        Returns whether both meshes have the same first face index
        :return: bool
        """

        face1 = cmp_utils.faces_to_vertices('%s.f[0]' % self.mesh1)
        face2 = cmp_utils.faces_to_vertices('%s.f[0]' % self.mesh2)

        vertex_indices1 = get_vertex_indices(face1)
        vertex_indices2 = get_vertex_indices(face2)

        return vertex_indices1 == vertex_indices2
    # endregion


def check_geometry(geometry):
    """
    Checks if a node is valid geometry node and raise and exception if the node is not valid
    :param geometry: str, name of the node to be checked
    :return: bool, True if the give node is a geometry node
    """

    if not is_geometry(geometry):
        raise exceptions.GeometryException(geometry)


def is_a_surface(geometry):
    """
    Returns whether given nodo is a surface one or not
    :param geometry: str
    :return: bopol
    """

    return maya.cmds.objExists('{}.cv[0][0]'.format(geometry))


def is_geometry(geometry):
    """
    Check if the given node is a valid geometry shape node
    :param geometry: str, node object to query as geometry
    :return: bool
    """

    if not maya.cmds.objExists(geometry):
        return False

    if 'transform' in maya.cmds.nodeType(geometry, i=True):
        geo_shape = maya.cmds.ls(maya.cmds.listRelatives(geometry, s=True, ni=True, pa=True) or [], geometry=True)
        if not geo_shape:
            return False
        geometry = geo_shape[0]

    if 'geometryShape' in maya.cmds.nodeType(geometry, i=True):
        return True

    return False


def geometry_type(geometry):
    """
    Returns the geometry type of the first shape under the given geometry object
    :param geometry: str, geometry object to query
    :return: str
    """

    if not maya.cmds.objExists(geometry):
        raise exceptions.GeometryExistsException(geometry)

    shapes_list = shape.get_shapes(node=geometry, intermediates=False)
    if not shapes_list:
        shapes_list = shape.get_shapes(node=geometry, intermediates=True)
    if not shapes_list:
        raise exceptions.NoShapeChildren(geometry)

    geometry_type = maya.cmds.objectType(shapes_list[0])

    return geometry_type


def component_type(geometry):
    """
    Rreturns the geometry component type string, used for building component selection lists
    :param geometry: str, geometry object to query
    :return: str
    """

    check_geometry(geometry)

    geo_type = geometry_type(geometry=geometry)
    com_type = {
        'mesh': 'vtx',
        'nurbsSurface': 'cv',
        'nurbsCurve': 'cv',
        'lattice': 'pt',
        'particle': 'pt'
    }

    return com_type[geo_type]


def is_mesh_compatible(mesh1, mesh2):
    """
    Checks whether two meshes to see if they have the same vertices, edge and face count
    :param mesh1: str
    :param mesh2: str
    :return: bool
    """

    check = MeshTopologyCheck(mesh1, mesh2)

    check_value = check.check_vert_edge_face_count()
    if not check_value:
        return False

    check_value = check.check_first_face_verts()

    return bool(check_value)


def replace(source_geometry, target_geometry):
    """
    Replaces the geometry of one object with another
    :param source_geometry: str, object that will provide the replacement geometry
    :param target_geometry: str, object whose geometry will be replaced
    """

    check_geometry(source_geometry)
    check_geometry(target_geometry)

    source_shape = source_geometry
    source_geo_type = geometry_type(source_geometry)
    if maya.cmds.objectType(source_shape) == 'transform':
        source_shapes = shape.get_shapes(source_geometry, intermediates=False)
        source_int_shapes = shape.get_shapes(source_geometry, intermediates=True)
        source_shape = source_shapes[0]
        if source_int_shapes:
            if source_geo_type == 'mesh':
                if maya.cmds.listConnections(source_shapes[0] + '.inMesh', s=True, d=False):
                    for int_shape in source_int_shapes:
                        if maya.cmds.listConnections(int_shape + '.outMesh', s=False, d=True):
                            source_shape = int_shape
                            break
            elif (source_geo_type == 'nurbsSurface') or (source_geo_type == 'nurbsCurve'):
                if maya.cmds.listConnections(source_shapes[0] + '.create', s=True, d=False):
                    for int_shape in source_int_shapes:
                        if maya.cmds.listConnections(int_shape + '.local', s=False, d=True):
                            source_shape = int_shape
                            break
            else:
                raise exceptions.UnknownGeometryType(source_geo_type)

    target_shape = target_geometry
    target_geo_type = geometry_type(target_geometry)
    if maya.cmds.objectType(target_shape) == 'transform':
        target_shapes = shape.get_shapes(target_geometry, intermediates=False)
        target_int_shapes = shape.get_shapes(target_geometry, intermediates=True)
        if not target_int_shapes:
            target_shape = target_shapes[0]
        else:
            if target_geo_type == 'mesh':
                if maya.cmds.listConnections(target_shapes[0] + '.inMesh', s=True, d=False):
                    for int_shape in target_int_shapes:
                        if maya.cmds.listConnections(int_shape + '.outMesh', s=False, d=True):
                            target_shape = int_shape
                            break
            elif (target_geo_type == 'nurbsSurface') or (target_geo_type == 'nurbsCurve'):
                if maya.cmds.listConnections(target_shapes[0] + '.create', s=True, d=False):
                    for int_shape in target_int_shapes:
                        if maya.cmds.listConnections(int_shape + '.local', s=False, d=True):
                            target_shape = int_shape
                            break
            else:
                raise exceptions.UnknownGeometryType(target_geo_type)

    if target_geo_type != source_geo_type:
        raise Exception('Target and Source geometry types do not match! Aborting ...')

    # We replace the geometry
    if target_geo_type == 'mesh':
        maya.cmds.connectAttr(source_shape + '.outMesh', target_shape + '.inMesh', force=True)
        maya.cmds.evalDeferred('maya.cmds.disconnectAttr("{}.outMesh", "{}.inMesh")'.format(source_shape, target_shape))
    elif (target_geo_type == 'nurbsSurface') or (target_geo_type == 'nurbsCurve'):
        maya.cmds.connectAttr(source_shape + '.local', target_shape + '.create', force=True)
        maya.cmds.evalDeferred('maya.cmds.disconnectAttr("{}.local", "{}.create")'.format(source_shape, target_shape))
    else:
        raise exceptions.UnknownGeometryType(target_geo_type)


def get_mpoint_array(geometry, world_space=True):
    """
    Returns an MPointArray containing the component positions for the given geometry
    :param geometry: str, geometry to return MPointArray for
    :param world_space: bool, Whether to return point positions in world or object space
    :return: MPointArray
    """

    from tp.maya.cmds import node

    check_geometry(geometry)

    if node.get_mobject(geometry).hasFn(maya.api.OpenMaya.MFn.kTransform):
        try:
            geometry = maya.cmds.listRelatives(geometry, s=True, ni=True, pa=True)[0]
        except Exception:
            raise exceptions.GeometryException(geometry)

    if world_space:
        shape_obj = node.get_mdag_path(geometry)
        space = maya.api.OpenMaya.MSpace.kWorld
    else:
        shape_obj = node.get_mobject(geometry)
        space = maya.api.OpenMaya.MSpace.kObject

    # Check shape type
    shape_type = maya.cmds.objectType(geometry)

    point_list = maya.api.OpenMaya.MPointArray()
    if shape_type == 'mesh':
        mesh_fn = maya.api.OpenMaya.MFnMesh(shape_obj)
        point_list = mesh_fn.getPoints(space)
    if shape_type == 'nurbsCurve':
        curve_fn = maya.api.OpenMaya.MFnNurbsCurve(shape_obj)
        point_list = curve_fn.getCVs(space)
    if shape_type == 'nurbsSurface':
        surface_fn = maya.api.OpenMaya.MFnNurbsSurface(shape_obj)
        point_list = surface_fn.getCVs(space)

    return point_list


def get_point_array(geometry, world_space=True):
    """
    Returns a point array containing the component positions for the given geometry
    :param geometry: str, geometry to return point array for
    :param world_space: bool, Whether to return point positions in world or object space
    :return: list
    """

    point_array = list()
    mpoint_array = get_mpoint_array(geometry=geometry, world_space=world_space)

    mpoint_array_length = mpoint_array.length() if hasattr(mpoint_array, 'length') else len(mpoint_array)
    for i in range(mpoint_array_length):
        point_array.append([mpoint_array[i][0], mpoint_array[i][1], mpoint_array[i][2]])

    return point_array


def set_mpoint_array(geometry, points, world_space=False):
    """
    Set the points positions of a geometry node
    :param geometry: str, geometry to set points array to
    :param points: MPointArray, point array of points
    :param world_space:
    :return: bool, Whether to set point positions in world or object space
    """

    from tp.maya.cmds import node

    check_geometry(geometry)

    if world_space:
        shape_obj = node.get_mdag_path(geometry)
        space = maya.api.OpenMaya.MSpace.kWorld
    else:
        shape_obj = node.get_mobject(geometry)
        space = maya.api.OpenMaya.MSpace.kObject

    it_geo = maya.api.OpenMaya.MItGeometry(shape_obj)
    it_geo.setAllPositions(points, space)


def get_mbounding_box(geometry, world_space=True):
    """
    Returns an MBoundingBox for the given geometry
    :param geometry: str, geometry to return MBoundingBox for
    :param world_space: bool, Whether to calculate MBoundingBox in world or object space
    :return: MBoundingBox
    """

    from tp.maya.cmds import node

    check_geometry(geometry)

    geo_path = node.get_mdag_path(geometry)
    geo_node_fn = maya.api.OpenMaya.MFnDagNode(geo_path)
    geo_bbox = geo_node_fn.boundingBox()

    # Transform to world space or local space
    if world_space:
        geo_bbox.transformUsing(geo_path.exclusiveMatrix())
    else:
        logger.warning('Local space Bounding Bosx is not fully reliable ...')
        geo_bbox.transformUsing(geo_node_fn.transformationMatrix().inverse())

    return geo_bbox


def voxelize_mesh(mesh_node, divisions=2):
    """
    Voxelizes a mesh using an octree data structure
    :param mesh_node: str
    :param divisions: int
    :return:
    """

    def _flatten_vertices_list(mesh_name, vertices_list):
        """
        Given a list containing vertices, which may appear as ranges, return a list containing without ranges
        NOTE: Maya returns ranges with inclusive vertices on both ends
        :param mesh_name: str, name of the mesh to get vertices from
        :param vertices_list: list, list of mesh vertices to flatten
        :return: list
        """

        flattened_verts = list()
        for vert in vertices_list:
            match = re.compile(r".*\[(\d*):(\d*)\]").match(vert)
            if not match:
                continue
            for v_index in match.groups():
                flattened_verts.append('{0}.vtx[{1}]'.format(mesh_name, v_index))

        return flattened_verts

    mesh_node = mesh_node or maya.cmds.ls(sl=True)
    mesh_nodes = helpers.force_list(mesh_node)
    if not mesh_nodes:
        return

    for mesh_name in mesh_nodes:
        try:
            shape_node = maya.cmds.listRelatives(mesh_name, children=True, shapes=True)[0]
            node_type = maya.cmds.nodeType(shape_node)
            if not node_type == 'mesh':
                continue
        except IndexError:
            continue

        min_x, min_y, min_z, max_x, max_y, max_z = maya.cmds.exactWorldBoundingBox(mesh_name)
        ot = octree.Octree((min_x, min_y, min_z), (max_x, max_y, max_z))
        ot_nodes = [ot.root]

        # Subdivide the octree to desired division level
        while ot_nodes:
            tree_node = ot_nodes.pop(0)
            if tree_node.divisions < divisions:
                tree_node.subdivide()
                ot_nodes.append(tree_node.children)
            break

        voxel_locations = set()
        # For each face in the mesh, find the node(s) containing that face
        for face_index in range(maya.cmds.polyEvaluate(mesh_name, f=True)):
            verts = maya.cmds.polyListComponentConversion('%s.f[%d]' % (mesh_name, face_index), ff=True, tv=True)

            # Flatten vertices list
            vert_list = _flatten_vertices_list(mesh_name, verts)

            # Find the leaf node containing these vertices
            for v in vert_list:
                node = ot.root
                while node.children:
                    v_pos = maya.cmds.xform(v, query=True, ws=True, t=True)
                    node = node.child_containing(v_pos)

                # Add the midpoint of the leaf node to the voxel set
                voxel_locations.add(node.half_values)

        # Create a cube at each of the voxel locations
        for i, (lx, ly, lz) in enumerate(voxel_locations):
            voxel_name = '%s_vox_%d' % (mesh_name, i)
            maya.cmds.polyCube(name=voxel_name)
            maya.cmds.xform(voxel_name, translation=[lx, ly, lz])


def smooth_preview(geometry, smooth_flag=True):
    """
    Turns on/off smooth preview of the given geometry node
    :param geometry: str, name of the geometry to set smooth preview
    :param smooth_flag: bool
    """

    if smooth_flag:
        maya.cmds.setAttr('{}.displaySmoothMesh'.format(geometry), 2)
    else:
        maya.cmds.setAttr('{}.displaySmoothMesh'.format(geometry), 0)


def smooth_preview_all(smooth_flag=True):
    """
    Turns on/off smooth preview of all the meshes in the current scene
    :param smooth_flag: bool
    """

    if scene.is_batch():
        return

    meshes = maya.cmds.ls(type='mesh')
    for mesh in meshes:
        intermediate = maya.cmds.getAttr('{}.intermediateObject'.format(mesh))
        if not intermediate:
            smooth_preview(mesh, smooth_flag)


def transforms_to_nurbs_surface(transforms, name='from_transforms', spans=-1, offset_axis='Y', offset_amount=1):
    """
    Creates a NURBS surface from a list of transforms
    Useful for creating a NURBS surface that follows a spine or tail
    :param transforms: list<str>, list of transforms
    :param name: str, name of the surface
    :param spans: int, number of spans to given to the final surface.
    If -1, the surface will have spans based on the number of transforms
    :param offset_axis: str, axis to offset the surface relative to the transform ('X', 'Y' or 'Z')
    :param offset_amount: int, amount the surface offsets from the transform
    :return: str, name of the NURBS surface
    """

    transform_positions_1 = list()
    transform_positions_2 = list()

    if offset_axis == 0:
        offset_axis = 'X'
    elif offset_axis == 1:
        offset_axis = 'Y'
    elif offset_axis == 2:
        offset_axis = 'Z'

    for xform in transforms:
        xform_1 = maya.cmds.group(empty=True)
        xform_2 = maya.cmds.group(empty=True)
        xform_utils.MatchTransform(xform, xform_1).translation_rotation()
        xform_utils.MatchTransform(xform, xform_2).translation_rotation()
        vct = vec3.get_axis_vector(offset_axis)
        maya.cmds.move(
            vct[0] * offset_amount, vct[1] * offset_amount, vct[2] * offset_amount, xform_1, relative=True, os=True)
        maya.cmds.move(
            vct[0] * -offset_amount, vct[1] * -offset_amount, vct[2] * -offset_amount, xform_2, relative=True, os=True)
        pos_1 = maya.cmds.xform(xform_1, q=True, ws=True, t=True)
        pos_2 = maya.cmds.xform(xform_2, q=True, ws=True, t=True)
        transform_positions_1.append(pos_1)
        transform_positions_2.append(pos_2)
        maya.cmds.delete(xform_1, xform_2)

    crv_1 = maya.cmds.curve(p=transform_positions_1, degree=1)
    crv_2 = maya.cmds.curve(p=transform_positions_2, degree=1)
    curves = [crv_1, crv_2]
    if not spans == -1:
        for crv in curves:
            maya.cmds.rebuildCurve(
                crv, ch=False, rpo=True, rt=0, end=1, kr=False, kcp=False, kep=True, kt=False,
                spans=spans, degree=3, tol=0.01)

    loft = maya.cmds.loft(crv_1, crv_2, n=name_utils.find_unique_name(name), ss=1, degree=1, ch=False)
    # maya.cmds.rebuildSurface(
    # loft, ch=True, rpo=1, rt=0, end=1, kr=0, kcp=0, kc=0, su=1, du=1, sv=spans, dv=3, fr=0, dir=2)

    maya.cmds.delete(crv_1, crv_2)

    return loft[0]


def curve_to_nurbs_surface(curve, description='', spans=-1, offset_axis='X', offset_amount=5):
    """
    Creates a new NURBS surface from the given curve
    :param curve: str, name of the curve
    :param description: str, name of the generate NURBS surface
    :param spans: int, surface spans
    :param offset_axis: str, offset axis
    :param offset_amount: float, offset amount
    :return: str, name of the newly created NURBS surface
    """

    description = description or curve
    curve_1 = maya.cmds.duplicate(curve)[0]
    curve_2 = maya.cmds.duplicate(curve)[0]
    offset_axis = offset_axis.upper()
    positive_move = vec3.get_axis_vector(offset_axis, offset_amount)
    negative_move = vec3.get_axis_vector(offset_axis, -offset_amount)
    maya.cmds.move(positive_move[0], positive_move[1], positive_move[2], curve_1)
    maya.cmds.move(negative_move[0], negative_move[1], negative_move[2], curve_2)

    curves = [curve_1, curve_2]
    if not spans == -1:
        for curve in curves:
            maya.cmds.rebuildCurve(
                curve, ch=False, rpo=True, rt=0, end=1, kr=False, kcp=False,
                kep=True, kt=False, spans=spans, degree=3, tol=0.01)

    loft = maya.cmds.loft(
        curve_1, curve_2,
        n=name_utils.find_unique_name('nurbsSurface_{}'.format(description)), ss=1, degree=1, ch=False)

    spans = maya.cmds.getAttr('{}.spans'.format(curve_1))
    maya.cmds.rebuildSurface(
        loft, ch=False, rpo=1, rt=0, end=1, kr=0, kcp=0, kc=0, su=1, du=1, sv=spans, dv=3, tol=0.01, fr=0, dir=2)
    maya.cmds.delete(curve_1, curve_2)

    return loft[0]


def nurbs_surface_u_to_transforms(surface, description='', count=4, value=0.5):
    """
    Creates joints along the U axis of the given surface
    :param surface: str
    :param description: str
    :param count: int
    :param value: float
    :return: list(str)
    """

    joints = list()
    last_joint = None
    section_value = 0
    description = description or surface

    max_value_u = maya.cmds.getAttr('{}.maxValueU'.format(surface))
    max_value_v = maya.cmds.getAttr('{}.maxValueV'.format(surface))
    mid_value = float(max_value_v * value)
    section = float(max_value_u / count)

    for i in range(count + 1):
        pos = maya.cmds.pointPosition('{}.uv[{}][{}]'.format(surface, section_value, mid_value))
        joint = maya.cmds.createNode('joint', n='joint_{}_{}'.format(i + 1, description))
        maya.cmds.xform(joint, ws=True, t=pos)

        if last_joint:
            maya.cmds.parent(joint, last_joint)
            joint_utils.orient_x_to_child(last_joint)

        joints.append(joint)
        section_value += section
        last_joint = joint
        if i == count:
            maya.cmds.makeIdentity(joint, apply=True, jo=True)

    return joints


def nurbs_surface_v_to_transforms(surface, description='', count=4, value=0.5):
    """
    Creates joints along the V axis of the given surface
    :param surface: str
    :param description: str
    :param count: int
    :param value: float
    :return: list(str)
    """

    joints = list()
    last_joint = None
    section_value = 0
    description = description or surface

    max_value_u = maya.cmds.getAttr('{}.maxValueU'.format(surface))
    max_value_v = maya.cmds.getAttr('{}.maxValueV'.format(surface))
    mid_value = float(max_value_u * value)
    section = float(max_value_v / count)

    for i in range(count + 1):
        pos = maya.cmds.pointPosition('{}.uv[{}][{}]'.format(surface, mid_value, section_value))
        joint = maya.cmds.createNode('joint', n='joint_{}_{}'.format(i + 1, description))
        maya.cmds.xform(joint, ws=True, t=pos)

        if last_joint:
            maya.cmds.parent(joint, last_joint)
            joint_utils.orient_x_to_child(last_joint)

        joints.append(joint)
        section_value += section
        last_joint = joint
        if i == count:
            maya.cmds.makeIdentity(joint, apply=True, jo=True)

    return joints


def transform_to_polygon_plane(transform, size=1, axis='Y'):
    """
    Creates a single polygon face from the position and orientation of a transform
    :param transform: str, name of the transform where the plane should be created
    :param size: float, size of the plane
    :param axis: str, axis plane should point at
    :return: str, name of the new plane
    """

    axis = axis.upper()
    if axis == 'X':
        axis_vector = [1, 0, 0]
    elif axis == 'Y':
        axis_vector = [0, 1, 0]
    elif axis == 'Z':
        axis_vector = [0, 0, 1]

    plane = maya.cmds.polyPlane(w=size, h=size, sx=1, sy=1, ax=axis_vector, ch=False)
    plane = maya.cmds.rename(plane, name_utils.find_unique_name('{}_plane'.format(transform)))
    xform_utils.MatchTransform(transform, plane).translation_rotation()

    return plane


def transforms_to_polygon(transforms, name, size=1, merge=True, axis='Y'):
    """
    Creates polygons on each given transform.
    Useful to create mesh for rivets and then deform.
    :param transforms: list(str)
    :param name: str
    :param size: float
    :param merge: bool
    :param axis: str
    :return: list(str)
    """

    new_mesh = None
    meshes = list()
    transforms = helpers.force_list(transforms)

    for transform in transforms:
        mesh = transform_to_polygon_plane(transform, size, axis=axis)
        meshes.append(mesh)

    if merge:
        if len(transforms) > 1:
            new_mesh = maya.cmds.polyUnite(meshes, ch=False, mergeUVSets=True, name=name)
            new_mesh = new_mesh[0]
        elif len(transforms) == 1:
            new_mesh = maya.cmds.rename(meshes[0], name)
        maya.cmds.polyLayoutUV(new_mesh, lm=1)

    return new_mesh


def get_mesh_shape(mesh, shape_index=0):
    """
    Returns the first mesh shape or one based in the index
    :param mesh: str, name of a mesh
    :param shape_index: int, index of shape to retrieve (usually is 0)
    :return: str, name of the shape. If no mesh shapes found then returns None
    """

    if mesh.find('.vtx'):
        mesh = mesh.split('.')[0]
    if maya.cmds.nodeType(mesh) == 'mesh':
        mesh = maya.cmds.listRelatives(mesh, p=True, f=True)[0]

    shapes = shape.get_shapes_of_type(mesh)
    if not shapes:
        return

    if not maya.cmds.nodeType(shapes[0]) == 'mesh':
        return

    shape_count = len(shapes)
    if shape_index < shape_count:
        return shapes[0]
    if shape_index > shape_count:
        logger.warning('{} does not have a shape count up to {}'.format(mesh, shape_index))
        return None

    return shapes[shape_index]


def get_surface_shape(surface, shape_index=0):
    """
    Returns the shape of a surface transform
    :param surface: str
    :param shape_index: int
    :return: str or None
    """

    if surface.find('.vtx'):
        surface = surface.split('.')[0]
    if maya.cmds.nodeType(surface) == 'nurbsSurface':
        surface = maya.cmds.listRelatives(surface, p=True)

    shapes = shape_utils.get_shapes(surface)
    if not shapes:
        return
    if not maya.cmds.nodeType(shapes[0]) == 'nurbsSurface':
        return

    shape_count = len(shapes)
    if shape_index < shape_count:
        return shapes[0]
    elif shape_index >= shape_count:
        logger.warning(
            'Surface {} does not have a shape count up to {}. Returning last shape'.format(surface, shape_index))
        return shapes[-1]

    return shapes[shape_index]


def get_vertices(geo_obj):
    """
    Returns list of vertices of the given geometry
    :param geo_obj: str, name of the geometry
    :return: list<str>
    """

    mesh = get_mesh_shape(geo_obj)
    meshes = shape.get_shapes_of_type(mesh, 'mesh', no_intermediate=True)

    found = list()
    for mesh in meshes:
        verts = maya.cmds.ls('{}.vtx[*]'.format(mesh), flatten=True)
        if verts:
            found += verts

    return found


def get_vertex_indices(list_of_vertex_names):
    """
    Returns list of indices of the given vertices
    :param list_of_vertex_names: list<str>
    :return: list<int>
    """

    list_of_vertex_names = helpers.force_list(list_of_vertex_names)
    vertex_indices = list()
    for vertex in list_of_vertex_names:
        index = int(vertex[vertex.find('[') + 1:vertex.find(']')])
        vertex_indices.append(index)

    return vertex_indices


def get_faces(geo_obj):
    """
    Returns list of faces of the given geometry
    :param geo_obj: str, name of the geometry
    :return: list<str>
    """

    mesh = get_mesh_shape(geo_obj)
    meshes = shape.get_shapes_of_type(mesh, 'mesh', no_intermediate=True)

    found = list()
    for mesh in meshes:
        faces = maya.cmds.ls('{}.f[*]'.format(mesh), flatten=True)
        if faces:
            found += faces

    return found


def get_closest_parameter_on_surface(surface, vector):
    """
    Returns the closest parameter value on the surface given vector
    :param surface: str, name of the surface
    :param vector: list(float, float, float(, position from which to check for closes parameter on surface
    :return: list(int, int), parameter coordinates (UV) of the closest point on the surface
    """

    shapes = shape.get_shapes(surface)
    surface = shapes[0] if shapes else surface
    surface = api.NurbsSurfaceFunction(surface)
    uv = surface.get_closest_parameter(vector)
    uv = list(uv)
    if uv[0] == 0:
        uv[0] = 0.001

    if uv[1] == 0:
        uv[1] = 0.001

    return uv


def get_closest_normal_on_surface(surface, vector):
    """
    Returns the closest normal on the surface given vector
    :param surface: str, name of the surface
    :param vector:
    :return:
    """

    shapes = shape.get_shapes(surface)
    surface = shapes[0] if shapes else surface
    surface = api.NurbsSurfaceFunction(surface)

    return surface.get_closest_normal(vector)


def get_point_from_surface_parameter(surface, u_value, v_value):
    """
    Returns surface point in given UV values
    :param surface: str, name of a surface
    :param u_value: int, u value
    :param v_value: int, v value
    :return: float(list, list, list)
    """

    surface_fn = api.NurbsSurfaceFunction(surface)
    position = surface_fn.get_position_from_parameter(u_value, v_value)

    return position


def get_triangles(mesh):
    """
    Returns the triangles of a mesh
    :param mesh: str
    :return: list(str)
    """

    found_faces = list()

    mesh = get_mesh_shape(mesh)
    meshes = shape_utils.get_shapes_of_type(mesh, 'mesh', no_intermediate=True)
    for mesh in meshes:
        mesh_fn = api.MeshFunction(mesh)
        triangles = mesh_fn.get_triangle_ids()
        faces = cmp_utils.get_face_names_from_indices(mesh, triangles)
        if faces:
            found_faces.extend(faces)

    return found_faces


def get_non_triangle_non_quad(mesh):
    """
    Returns faces that are neither quad or triangles
    :param mesh: str
    :return: list(str)
    """

    found_faces = list()

    mesh = get_mesh_shape(mesh)
    meshes = shape_utils.get_shapes_of_type(mesh, 'mesh')
    for mesh in meshes:
        mesh_fn = api.MeshFunction(mesh)
        ids = mesh_fn.get_non_tri_quad_ids()
        faces = cmp_utils.get_face_names_from_indices(mesh, ids)
        if faces:
            found_faces.extend(faces)

    return found_faces


def get_face_center(mesh, face_id):
    """
    Returns the center position of a face
    :param mesh: str, name of a mesh
    :param face_id: int, index of a face component
    :return: list(float, float, float), vector of the center of the face
    """

    mesh = get_mesh_shape(mesh)
    face_iter = api.IteratePolygonFaces(mesh)

    return face_iter.get_center(face_id)


def get_face_centers(mesh):
    """
    Returns all face centers of the given mesh
    :param mesh: str, name of a mesh
    :return: list(list(float, float, float)), list containing all vector centers of the mesh
    """

    mesh = get_mesh_shape(mesh)
    face_iter = api.IteratePolygonFaces(mesh)

    return face_iter.get_face_center_vectors()


def get_meshes_in_list(dg_nodes_list):
    """
    Given a list of DG nodes, returns any transform that has a mesh shape node
    :param dg_nodes_list: list(str)
    :return: list(str)
    """

    found_meshes = list()

    if not dg_nodes_list:
        return found_meshes

    for dg_node in dg_nodes_list:
        if maya.cmds.nodeType(dg_node) == 'mesh':
            found_mesh = maya.cmds.listRelatives(dg_node, p=True)
            if not found_mesh:
                continue
            found_meshes.append(found_mesh[0])
        if maya.cmds.nodeType(dg_node) == 'transform':
            shapes = get_mesh_shape(dg_node)
            if not shapes:
                continue
            found_meshes.append(dg_node)

    return found_meshes


def get_surfaces_in_list(dg_nodes_list):
    """
    Given a list of DG nodes, returns any transform that has a surface shape node
    :param dg_nodes_list: list(str)
    :return: list(str)
    """

    found_surfaces = list()

    for dg_node in dg_nodes_list:
        if maya.cmds.nodeType(dg_node) == 'nurbsSurface':
            found_surface = maya.cmds.listRelatives(dg_node, p=True)
            found_surfaces.append(found_surface)
        if maya.cmds.nodeType(dg_node) == 'transform':
            shapes = get_surface_shape(dg_node)
            if shapes:
                found_surfaces.append(dg_node)

    return found_surfaces


def get_selected_meshes():
    """
    Returns all selected meshes from current selection
    :return: list(str)
    """

    selection = maya.cmds.ls(sl=True)

    return get_meshes_in_list(selection)


def get_selected_surfaces():
    """
    Returns all selected surfaces from current selection
    :return: list(str)
    """

    selection = maya.cmds.ls(sl=True)

    return get_surfaces_in_list(selection)


def add_poly_smooth(mesh, divisions=1):
    """
    Creates a new polySmooth node on the given mesh
    :param mesh: str, name of a mesh
    :param divisions: int, smooth divisions
    :return: str, name of the poly smooth node
    """

    if helpers.maya_version() < 2017:
        poly_smooth = maya.cmds.polySmooth(
            mesh, mth=0, dv=divisions, bnr=1, c=1, kb=0, khe=0, kt=1,
            kmb=1, suv=1, peh=0, sl=1, dpe=1, ps=0.1, ro=1, ch=1)[0]
    else:
        poly_smooth = maya.cmds.polySmooth(
            mesh, sdt=2, mth=0, dv=divisions, bnr=1, c=1, kb=0, khe=0, kt=1,
            kmb=1, suv=1, peh=0, sl=1, dpe=1, ps=0.1, ro=1, ch=1)[0]

    return poly_smooth


# TODO: Finish implementation
def polygon_plane_to_curves(plane, count=5, u=True, description=''):
    description = description or plane
    if count == 0:
        return

    dup_curve = maya.cmds.duplicate(plane)[0]


def grow_lattice_points(points):
    """
    Returns grow selection of the given lattice points
    :param points: lsit(str)
    :return: list(str)
    """

    base = points[0].split('.')[0]
    all_points = maya.cmds.filterExpand('{}.pt[*]'.format(base), helpers.SelectionMasks.LatticePoints)
    extras = list()
    for point in points:
        extras.append(point)
        a = int(point.split('[')[1].split(']')[0])
        b = int(point.split('[')[2].split(']')[0])
        c = int(point.split('[')[3].split(']')[0])
        for i in [-1, 1]:
            grow_a = '{}.pt[{}][{}][{}]'.format(base, a + i, b, c)
            grow_b = '{}.pt[{}][{}][{}]'.format(base, a, b + i, c)
            grow_c = '{}.pt[{}][{}][{}]'.format(base, a, b, c + i)
            if grow_a in all_points:
                extras.append(grow_a)
            if grow_b in all_points:
                extras.append(grow_b)
            if grow_c in all_points:
                extras.append(grow_c)

    return extras


def find_shortest_path_between_surface_cvs(cvs_list, diagonal=False, return_total_distance=False):

    start = cvs_list[0]
    end = cvs_list[-1]
    start = start[1:] if start.startswith('|') else start
    end = end[1:] if end.startswith('|') else end
    surface = start.split('.')[0]

    obj_type = maya.cmds.objectType(surface)
    if obj_type == 'transform':
        shape = maya.cmds.listRelatives(surface, shapes=True)
        if shape:
            obj_type = maya.cmds.objectType(shape[0])
    if obj_type != 'nurbsSurface':
        return None

    all_cvs = maya.cmds.filterExpand(
        '{}.cv[*][*]'.format(surface), selectionMask=helpers.SelectionMasks.ControlVertices)
    graph = dijkstra.Graph()
    recompute_dict = dict()
    for cv in all_cvs:
        base = (cv)
        graph.add_node(base)
        recompute_dict[base] = cv

    for cv in all_cvs:
        maya.cmds.select(clear=True)
        maya.cmds.nurbsSelect(cv, growSelection=True)
        grow_selection = maya.cmds.ls(sl=True)[0]
        if not diagonal:
            work_string = cv.split('][')
            grow_string = grow_selection.split('][')
            grow_selection = [
                "%s][%s" % (work_string[0], grow_string[-1]), "%s][%s" % (grow_string[0], work_string[-1])]
        grow_selection = maya.cmds.filterExpand(grow_selection, selectionMask=helpers.SelectionMasks.ControlVertices)
        grow_selection.remove(cv)

        base_pos = maya.api.OpenMaya.MVector(*maya.cmds.xform(cv, q=True, ws=True, t=True))
        for grow_cv in grow_selection:
            cv_pos = maya.api.OpenMaya.MVector(*maya.cmds.xform(grow_cv, q=True, ws=True, t=True))
            cvs_length = (cv_pos - base_pos).length()
            graph.add_edge((cv), (grow_cv), cvs_length)

    shortest = dijkstra.shortest_path(graph, (start), (end))

    in_order = list()
    for found in shortest[-1]:
        in_order.append(recompute_dict[found])

    if return_total_distance:
        total_distance = shortest[0]
        return in_order, total_distance

    return in_order


def find_shortest_path_between_lattice_cvs(cvs_list, return_total_distance=False):
    start = cvs_list[0]
    end = cvs_list[-1]
    surface = start.split('.')[0]

    obj_type = maya.cmds.objectType(surface)
    if obj_type == 'transform':
        shape = maya.cmds.listRelatives(surface, shapes=True)
        if shape:
            obj_type = maya.cmds.objectType(shape[0])
    if obj_type != 'lattice':
        return None

    all_cvs = maya.cmds.filterExpand(
        '{}.cv[*][*]'.format(surface), selectionMask=helpers.SelectionMasks.ControlVertices)
    graph = dijkstra.Graph()
    recompute_dict = dict()
    for cv in all_cvs:
        base = (cv)
        graph.add_node(cv)
        recompute_dict[base] = cv

    for cv in all_cvs:
        grow_selection = grow_lattice_points([cv])
        grow_selection.remove(cv)
        base_pos = maya.api.OpenMaya.MVector(*maya.cmds.xform(cv, q=True, ws=True, t=True))
        for grow_cv in grow_selection:
            cv_pos = maya.api.OpenMaya.MVector(*maya.cmds.xform(grow_cv, q=True, ws=True, t=True))
            cvs_length = (cv_pos - base_pos).length()
            graph.add_edge((cv), (grow_cv), cvs_length)

    shortest = dijkstra.shortest_path(graph, (start), (end))

    in_order = list()
    for found in shortest[-1]:
        in_order.append(recompute_dict[found])

    if return_total_distance:
        total_distance = shortest[0]
        return in_order, total_distance

    return in_order
