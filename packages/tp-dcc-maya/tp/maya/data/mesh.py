#! /usr/bin/env python

"""
This module include base class for mesh data object
"""

# import maya.cmds
#
# import tpRigToolkit.maya as maya
# from tpRigToolkit.maya.data import base
# from tpRigToolkit.maya.lib import mesh, exceptions


# class MeshData(base.AbstractMeshData, object):
#     """
#     Base class for mesh data objects
#     This class contains functions to save, load and rebuild Maya mesh data
#     """
#
#     def __init__(self, mesh=''):
#         super(MeshData, self).__init__()
#
#         # Class Defaults
#         self.max_distance = 9999999.9
#
#         # Common Mesh Data
#         self._data['name'] = ''
#         self._data['vertexList'] = list()
#         self._data['polyCount'] = list()
#         self._data['polyConnects'] = list()
#
#         # UV Data
#         self._data['uvCount'] = list()
#         self._data['uvIds'] = list()
#         self._data['uArray'] = list()
#         self._data['vArray'] = list()
#
#         self._mesh = mesh
#         if mesh:
#             self.build_data()
#
#     def build_data(self):
#         """
#         Builds mesh data
#         """
#
#         if not self._mesh:
#             return
#
#         if not mesh.is_mesh(self._mesh):
#             exceptions.MeshException(self._mesh)
#
#         timer = cmds.timerX()
#
#         self._data['name'] = self._mesh
#
#         # Get Polygon Data
#         mesh_fn = mesh.get_mesh_fn(self._mesh)
#         if dcclib.app.is_new_api():
#             poly_count, poly_connects = mesh_fn.getVertices()
#         else:
#             poly_count = dcclib.app.OpenMaya.MIntArray()
#             poly_connects = dcclib.app.OpenMaya.MIntArray()
#             mesh_fn.getVertices(poly_count, poly_connects)
#         self._data['polyCount'] = list(poly_count)
#         self._data['polyConnects'] = list(poly_connects)
#
#         # Get Vertex Data
#         self._data['vertexList'] = meshutils.get_points(mesh=self._mesh, flatten=True)
#
#         # Get UVs Data
#         uv_count, uv_ids = meshutils.get_assigned_uvs(mesh=self._mesh)
#         self._data['uvCount'] = list(uv_count)
#         self._data['uvIds'] = list(uv_ids)
#
#         u_array, v_array = meshutils.get_uvs(mesh=self._mesh)
#         self._data['uArray'] = list(u_array)
#         self._data['vArray'] = list(v_array)
#
#         build_time = cmds.timerX(st=timer)
#         dcclib.debug('MayaMeshData: Data build time for mesh "{}" : {}'.format(self._mesh, str(build_time)))
#
#         return self._data['name']
#
#     def rebuild(self):
#         """
#         Rebuilds the mesh data from the stored data
#         """
#
#         timer = cmds.timerX()
#
#         # Rebuild Mesh Data
#         if dcclib.app.is_new_api():
#             poly_count = dcclib.app.OpenMaya.MIntArray(self._data['polyCount'])
#             poly_connects = dcclib.app.OpenMaya.MIntArray(self._data['polyConnects'])
#         else:
#             mesh_util = dcclib.app.OpenMaya.MScriptUtil()
#             poly_count = dcclib.app.OpenMaya.MIntArray()
#             poly_connects = dcclib.app.OpenMaya.MIntArray()
#             mesh_util.createIntArrayFromList(self._data['polyCount'], poly_count)
#             mesh_util.createIntArrayFromList(self._data['polyConnects'], poly_connects)
#
#         # Rebuild UV Data
#         if dcclib.app.is_new_api():
#             uv_count = dcclib.app.OpenMaya.MIntArray(self._data['uvCount'])
#             uv_ids = dcclib.app.OpenMaya.MIntArray(self._data['uvIds'])
#             u_array = dcclib.app.OpenMaya.MIntArray(self._data['uArray'])
#             v_array = dcclib.app.OpenMaya.MIntArray(self._data['vArray'])
#         else:
#             mesh_util = dcclib.app.OpenMaya.MScriptUtil()
#             uv_count = dcclib.app.OpenMaya.MIntArray()
#             uv_ids = dcclib.app.OpenMaya.MIntArray()
#             u_array = dcclib.app.OpenMaya.MFloatArray()
#             v_array = dcclib.app.OpenMaya.MFloatArray()
#             mesh_util.createIntArrayFromList(self._data['uvCount'], uv_count)
#             mesh_util.createIntArrayFromList(self._data['uvIds'], uv_ids)
#             mesh_util.createFloatArrayFromList(self._data['uArray'], u_array)
#             mesh_util.createFloatArrayFromList(self._data['vArray'], v_array)
#
#         # Rebuild Vertex Array
#         num_vertices = len(self._data['vertexList'])
#         num_polygons = len(self._data['polyCount'])
#
#         if dcclib.app.is_new_api():
#             vertex_array = dcclib.app.OpenMaya.MFloatPointArray(num_vertices, dcclib.app.OpenMaya.MFloatPoint.kOrigin)
#             for i in range(num_vertices):
#                 vertex_array.append(self._data['vertexList'][i])
#             mesh_fn = dcclib.app.OpenMaya.MFnMesh()
#             mesh_obj = mesh_fn.create(
#                 vertex_array,
#                 poly_count,
#                 poly_connects,
#                 u_array,
#                 v_array
#             )
#         else:
#             vertex_array = dcclib.app.OpenMaya.MFloatPointArray(num_vertices, dcclib.app.OpenMaya.MFloatPoint.origin)
#             for i in range(num_vertices):
#                 vertex_array.set(
#                 i, self._data['vertexList'][i][0], self._data['vertexList'][i][1],
#                 self._data['vertexList'][i][2], self._data['vertexList'][i][3])
#
#             mesh_fn = dcclib.app.OpenMaya.MFnMesh()
#             mesh_data = dcclib.app.OpenMaya.MFnMeshData().create()
#             mesh_obj = mesh_fn.create(
#                 num_vertices,
#                 num_polygons,
#                 vertex_array,
#                 poly_count,
#                 poly_connects,
#                 u_array,
#                 v_array,
#                 mesh_data
#             )
#
#         mesh_fn.assignUVs(uv_count, uv_ids)
#         mesh_obj_handle = dcclib.app.OpenMaya.MObjectHandle(mesh_obj)
#
#         build_time = cmds.timerX(st=timer)
#         dcclib.debug('MayaMeshData: Data rebuild time for mesh "{}" : {}'.format(self._mesh, str(build_time)))
#
#         return mesh_obj_handle
#
#     def rebuild_mesh(self):
#         """
#         Rebuilds the mesh from the stored data
#         """
#
#         timer = cmds.timerX()
#
#         # Rebuild Mesh Data
#         mesh_data = dcclib.app.OpenMaya.MObject()
#         if dcclib.app.is_new_api():
#             poly_count = dcclib.app.OpenMaya.MIntArray(self._data['polyCount'])
#             poly_connects = dcclib.app.OpenMaya.MIntArray(self._data['polyConnects'])
#         else:
#             mesh_util = dcclib.app.OpenMaya.MScriptUtil()
#             poly_count = dcclib.app.OpenMaya.MIntArray()
#             poly_connects = dcclib.app.OpenMaya.MIntArray()
#             mesh_util.createIntArrayFromList(self._data['polyCount'], poly_count)
#             mesh_util.createIntArrayFromList(self._data['polyConnects'], poly_connects)
#
#         # Rebuild UV Data
#         if dcclib.app.is_new_api():
#             uv_count = dcclib.app.OpenMaya.MIntArray(self._data['uvCount'])
#             uv_ids = dcclib.app.OpenMaya.MIntArray(self._data['uvIds'])
#             u_array = dcclib.app.OpenMaya.MIntArray(self._data['uArray'])
#             v_array = dcclib.app.OpenMaya.MIntArray(self._data['vArray'])
#         else:
#             mesh_util = dcclib.app.OpenMaya.MScriptUtil()
#             uv_count = dcclib.app.OpenMaya.MIntArray()
#             uv_ids = dcclib.app.OpenMaya.MIntArray()
#             u_array = dcclib.app.OpenMaya.MFloatArray()
#             v_array = dcclib.app.OpenMaya.MFloatArray()
#             mesh_util.createIntArrayFromList(self._data['uvCount'], uv_count)
#             mesh_util.createIntArrayFromList(self._data['uvIds'], uv_ids)
#             mesh_util.createFloatArrayFromList(self._data['uArray'], u_array)
#             mesh_util.createFloatArrayFromList(self._data['vArray'], v_array)
#
#         # Rebuild Vertex Array
#         num_vertices = len(self._data['vertexList'])
#         num_polygons = len(self._data['polyCount'])
#
#         if dcclib.app.is_new_api():
#             vertex_array = dcclib.app.OpenMaya.MFloatPointArray(num_vertices, dcclib.app.OpenMaya.MFloatPoint.kOrigin)
#             for i in range(num_vertices):
#                 vertex_array[i] = dcclib.app.OpenMaya.MFloatPoint(self._data['vertexList'][i])
#
#             mesh_fn = dcclib.app.OpenMaya.MFnMesh()
#             mesh_obj = mesh_fn.create(
#                 vertex_array,
#                 poly_count,
#                 poly_connects,
#                 u_array,
#                 v_array
#             )
#         else:
#             vertex_array = dcclib.app.OpenMaya.MFloatPointArray(num_vertices, dcclib.app.OpenMaya.MFloatPoint.origin)
#             for i in range(num_vertices):
#                 vertex_array.set(i, self._data['vertexList'][i][0], self._data['vertexList'][i][1],
#                                  self._data['vertexList'][i][2], self._data['vertexList'][i][3])
#
#             mesh_fn = dcclib.app.OpenMaya.MFnMesh()
#             mesh_obj = mesh_fn.create(
#                 num_vertices,
#                 num_polygons,
#                 vertex_array,
#                 poly_count,
#                 poly_connects,
#                 u_array,
#                 v_array,
#                 mesh_data
#             )
#
#         mesh_fn.assignUVs(uv_count, uv_ids)
#
#         mesh = dcclib.app.OpenMaya.MFnDependencyNode(mesh_obj).setName(self._data['name'])
#         mesh_shape = cmds.listRelatives(mesh, s=True, ni=True, pa=True)[0]
#         cmds.sets(mesh_shape, fe='initialShadingGroup')
#
#         build_time = cmds.timerX(st=timer)
#         dcclib.debug('MayaMeshData: Geometry rebuild time for mesh "{}" : {}'.format(self._mesh, str(build_time)))
#
#         return mesh
