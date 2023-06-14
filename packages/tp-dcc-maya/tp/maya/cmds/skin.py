#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with skins
"""

import traceback

try:
    import cStringIO as StringIO
except ImportError:
    import io as StringIO

import maya.cmds
import maya.mel
import maya.api.OpenMaya
import maya.api.OpenMayaAnim

from tp.core import log, dcc
from tp.common.python import helpers
from tp.common.math import vec3, kdtree
from tp.maya import api
from tp.maya.om import mathlib as api_mathlib, skin as api_skin
from tp.maya.cmds import decorators, exceptions, deformer, attribute, node as node_utils, mesh as mesh_utils
from tp.maya.cmds import joint as jnt_utils, transform as xform_utils, shape as shape_utils, name as name_utils

logger = log.tpLogger


class ShowJointInfluence(object):
    """
    Displays affected vertices for selected joint
    """

    def __init__(self, joint):
        """
        Constructor
        :param joint: str, name of the joint we want to show vertex skin influences of
        """

        self.joint = None
        self.select_vertices = True
        self.show_weights = True
        self.delete_later = list()

        if jnt_utils.is_joint(joint) or xform_utils.is_transform(joint):
            self.joint = joint

        if jnt_utils.is_joint(joint) or xform_utils.is_transform(joint):
            self.joint = joint
            self.enable()

    @decorators.undo
    def enable(self):
        """
        Enables show vertex skin influences of the wrapped joint
        """

        self._cleanup()
        self._display_weighted_verts()

    @decorators.undo
    def disable(self):
        """
        Internal function used to unshow the weighted vertices of the wrapped joint
        """

        self._cleanup()
        maya.cmds.select(clear=True)

    def set_select_vertices(self, select_vertices):
        """
        Set if the influenced vertices should be selected or not
        :param select_vertices: bool
        """

        self.select_vertices = select_vertices

    def set_show_weights(self, show_weights):
        """
        Set if the weights of the influenced weights should be showed or not
        :param show_weights: bool
        """

        self.show_weights = show_weights

    @decorators.ShowMayaProgress('Showing influences')
    def _display_weighted_verts(self):
        """
        Internal function used to show the weighted vertices of the wrapped joint
        """

        affected_verts = list()
        affected_value = list()

        connections = list(set(maya.cmds.listConnections(self.joint, type='skinCluster')))
        if len(connections) <= 0:
            logger.warning('Wrapped joint "{}" has no skinCluster!'.format(self.joint))
            return

        for skin_cluster in connections:
            skin_cluster_set = None
            tree_connections = maya.cmds.listConnections(
                skin_cluster, destination=True, source=False, plugs=False, connections=False)
            for branch in tree_connections:
                node_type = maya.cmds.nodeType(branch)
                if node_type == 'objectSet':
                    skin_cluster_set = branch
                    break

            if skin_cluster_set <= 0:
                logger.warning(
                    'Wrapped joint "{}" with skinCluster "{}" has no valid SkinClusterSet'.format(
                        self.joint, skin_cluster))
                return

            obj = maya.cmds.listConnections(
                skin_cluster_set, destination=True, source=False, plugs=False, connections=False)
            vertex_num = maya.cmds.polyEvaluate(obj, vertex=True)
            for vtx in range(vertex_num):
                self._display_weighted_verts.step()
                vtx_name = '{0}.vtx[{1}]'.format(obj[0], str(vtx))
                weights = maya.cmds.skinPercent(skin_cluster, vtx_name, query=True, value=True)
                influences = maya.cmds.skinPercent(skin_cluster, vtx_name, query=True, transform=None)
                for i in range(len(influences)):
                    if influences[i] == self.joint and weights[i] > 0:
                        affected_verts.append(vtx_name)
                        affected_value.append(weights[i])
                        break

        if self.show_weights:
            maya.cmds.select(clear=True)
            grp = maya.cmds.group(empty=True, n='annotations_{}'.format(self.joint))
            for i in range(len(affected_verts)):
                pos = maya.cmds.pointPosition(affected_verts[i], world=True)
                loc = maya.cmds.spaceLocator()[0]
                maya.cmds.setAttr('{}.t'.format(loc), pos[0], pos[1], pos[2])
                maya.cmds.setAttr('{}.v'.format(loc), 0)
                maya.cmds.select(loc, replace=True)
                annotation_node = maya.cmds.annotate(loc, text=str(affected_value[i]), point=(pos[0], pos[1], pos[2]))
                annotation_xform = maya.cmds.listRelatives(annotation_node, parent=True, fullPath=True)
                maya.cmds.parent(annotation_xform, grp)
                maya.cmds.parent(loc, grp)
                self.delete_later.append(annotation_node)
                self.delete_later.append(loc)
            self.delete_later.append(grp)

        if self.select_vertices:
            maya.cmds.select(affected_verts, replace=True)

    def _cleanup(self):
        """
        Cleans objects created by the class
        """

        for obj in self.delete_later:
            maya.cmds.delete(obj)
        self.delete_later = list()

        if maya.cmds.objExists('annotations_{}'.format(self.joint)):
            maya.cmds.delete('annotations_{}'.format(self.joint))


class StoreSkinWeight(object):

    def __init__(self):
        self._do_run = False

    def run_store(self):
        self._do_run = True
        self._dag_skin_id_dict = dict()
        self.get_all_mesh_vertices()
        self.get_skin_weight()

    def get_mesh_node_list(self):
        """
        Returns list of meshes that belongs to the stored skin info
        :return: list(str)
        """

        if not self._do_run:
            return

        return self._mesh_node_list

    def get_all_influences(self):
        """
        Returns a list with all the influences that belongs to the stored skin info
        :return: list(str)
        """

        if not self._do_run:
            return

        return self._all_influences

    def get_all_skin_clusters(self):
        """
        Returns a list of all skin clusters that belongs to the stored skin info
        :return: dict(str, str)
        """

        if not self._do_run:
            return

        return self._all_skin_clusters

    def get_influences_dict(self):
        """
        Returns dictionary of influences that belongs to the stored skin info
        :return: dict
        """

        if not self._do_run:
            return

        return self._influences_dict

    def get_node_vertices_dict(self):
        """
        Returns dictionary of vertices that belongs to the stored skin info
        :return: dict
        """

        if not self._do_run:
            return

        return self._node_vertices_dict

    def get_node_weight_dict(self):
        """
        Returns dictionary of weights that belongs to the stored skin info
        :return: dict
        """

        if not self._do_run:
            return

        return self._node_weight_dict

    def get_node_skinfn_dict(self):
        """
        Returns dictionary of skinfn objects that belongs to the stored skin info
        :return: dict
        """

        if not self._do_run:
            return

        return self._node_skinfn_dict

    def get_show_dict(self):
        """
        Returns dictionary of weights that can be useful to show info of
        :return: dict
        """

        return self._show_dict

    def get_all_mesh_vertices(self):
        """
        Returns a dictionary containing all vertex IDs list and information of the meshes
        :return: list
        """

        selection_list = api.get_active_selection_list()
        selection_list_iter = api.SelectionListIterator(selection_list)

        loop = 0
        add_nodes = list()

        while not selection_list_iter.is_done():
            loop += 1
            if loop >= 10000:
                logger.warning('Too many loops while retrieving vertices from mesh node!')
                return list()

            try:
                mesh_dag = selection_list_iter.get_dag_path()
            except Exception as e:
                logger.error('Get Dag Path error : {}'.format(e.message))
                selection_list_iter.next()
                continue

            mesh_path_name = mesh_dag.full_path_name()
            add_nodes += [mesh_path_name]
            selection_list_iter.next()

        add_nodes = [maya.cmds.listRelatives(
            node, p=True, f=True)[0] if maya.cmds.nodeType(node) == 'mesh' else node for node in add_nodes]

        if maya.cmds.selectMode(query=True, component=True):
            self._hilite_nodes = maya.cmds.ls(hilite=True, long=True)
            self._hilite_nodes = mesh_utils.get_meshes_from_nodes(
                nodes=self._hilite_nodes, full_path=True, search_child_node=True)
            add_node = mesh_utils.get_meshes_from_nodes(
                maya.cmds.ls(sl=True, long=True, tr=True), full_path=True, search_child_node=True)
            if add_node:
                self._hilite_nodes += add_node
            if add_nodes:
                self._hilite_nodes += add_nodes
        else:
            self._hilite_nodes = maya.cmds.ls(
                sl=True, long=True, tr=True) + maya.cmds.ls(hlong=True, long=True, tr=True)
            self._hilite_nodes = mesh_utils.get_meshes_from_nodes(
                nodes=self._hilite_nodes, full_path=True, search_child_node=True)
            if add_nodes:
                self._hilite_nodes += add_nodes

        self._hilite_nodes = list(set(self._hilite_nodes))

        for n in self._hilite_nodes[:]:
            sel_list = api.SelectionList()
            sel_list.add(n)

            try:
                mesh_dag, component = selection_list.get_component(0)
            except Exception as e:
                logger.erro('Get Dag Path error : {}'.format(e.message))
                continue

            skin_fn, vertex_array, skin_name = self._adjust_to_vertex_list(mesh_dag, component)
            if skin_fn is None:
                continue

            self._dag_skin_id_dict[mesh_dag.full_path_name()] = [
                skin_fn.get_api_object(), vertex_array.get_api_object(), skin_name, mesh_dag.get_api_object()
            ]

    def get_selected_mesh_vertices(self, node):
        """
        Returns selected vertices on the given mesh node
        :param node:
        :return:
        """

        selection_list = api.get_active_selection_list()
        selection_list_iter = api.SelectionListIterator(selection_list)

        selected_objs = dict()
        loop = 0
        vertex_arrays = list()

        while not selection_list_iter.is_done():
            loop += 1
            if loop >= 10000:
                logger.warning('Too many loops while retrieving vertices from mesh node!')
                return vertex_arrays
            try:
                mesh_dag, component = selection_list_iter.get_component()
            except Exception as e:
                logger.error('Get current vertex error : {}'.format(e.message))
                selection_list_iter.next()
                continue

            mesh_path_name = mesh_dag.full_path_name()
            if maya.cmds.nodeType(mesh_path_name) == 'mesh':
                mesh_path_name = maya.cmds.listRelatives(mesh_path_name, p=True, f=True)[0]
            if node != mesh_path_name:
                selection_list_iter.next()
                continue

            skin_fn, vertex_array, skin_name = self._adjust_to_vertex_list(mesh_dag, component, force=True)
            vertex_arrays += sorted(vertex_array)
            selection_list_iter.next()

        return vertex_arrays

    def get_skin_cluster(self, dag_path=None):
        """
        Loops through the DAG hierarchy of the given DAG path finding a skin cluster
        :param dag_path: variant, api.DagPath
        :return:
        """

        if not dag_path:
            return None, None

        skin_cluster = maya.cmds.ls(maya.cmds.listHistory(dag_path.full_path_name()), type='skinCluster')
        if not skin_cluster:
            return None, None

        skin_name = skin_cluster[0]
        selection_list = api.SelectionList()
        selection_list.create_by_name(skin_name)

        skin_node = selection_list.depend_node(0)
        skin_fn = api.SkinCluster(skin_node)

        return skin_fn, skin_name

    def get_skin_weight(self):

        self._node_weight_dict = dict()
        self._node_vertices_dict = dict()
        self._influences_id_list = list()
        self._influences_dict = dict()
        self._all_influences = list()
        self._all_skin_clusters = dict()
        self._mesh_node_list = list()
        self._show_dict = dict()
        self._node_skinfn_dict = dict()

        for mesh_path_name, skin_vtx in self._dag_skin_id_dict.items():
            skin_fn = skin_vtx[0]
            vertex_array = skin_vtx[1]
            skin_name = skin_vtx[2]
            mesh_path = skin_vtx[3]

            self._node_skinfn_dict[mesh_path_name] = skin_fn
            if maya.cmds.nodeType(mesh_path_name) == 'mesh':
                mesh_path_name = maya.cmds.listRelatives(mesh_path_name, p=True, f=True)[0]

            single_id_comp = api.SingleIndexedComponent()
            vertex_component = single_id_comp.create(maya.api.OpenMaya.MFn.kMeshVertComponent)
            single_id_comp.add_elements(vertex_array)

            api_skin_fn = api.SkinCluster(skin_fn)
            influence_dags = api_skin_fn.influence_objects()
            influence_indices = api.IntArray(len(influence_dags), 0)
            for i in range(len(influence_dags)):
                influence_indices[i] = int(api_skin_fn.index_for_influence_object(influence_dags[i]))

            try:
                weights = api_skin_fn.get_weights(mesh_path, vertex_component)
            except Exception as e:
                logger.error('Get Skin Weight error : {}'.format(e.message))
                continue

            weights = self._convert_shape_weights(len(influence_indices), weights)

            influence_list = [api.DagPath(influence_dags[i]).full_path_name() for i in range(len(influence_indices))]

            self._node_vertices_dict[mesh_path_name] = vertex_array
            self._all_skin_clusters[mesh_path_name] = skin_name
            self._mesh_node_list.append(mesh_path_name)
            self._influences_id_list.append(influence_indices)
            self._node_weight_dict[mesh_path_name] = weights
            self._influences_dict[mesh_path_name] = influence_list
            self._all_influences += influence_list
            self._show_dict[mesh_path_name] = vertex_array

        self._all_influences = sorted(list(set(self._all_influences)))

    def _adjust_to_vertex_list(self, mesh_dag, component, force=False):

        skin_fn, skin_name = self.get_skin_cluster(mesh_dag)

        if not force:
            if not skin_fn or not skin_name:
                return None, None, None
            if not mesh_dag.hasFn(maya.api.OpenMaya.MFn.kMesh) or skin_name == '':
                return None, None, None

        sel_id = dict()
        component_type = None

        if component.hasFn(maya.api.OpenMaya.MFn.kMeshVertComponent):
            component_type = 'vtx'
        elif component.hasFn(maya.api.OpenMaya.MFn.kMeshEdgeComponent):
            component_type = 'edge'
        elif component.hasFn(maya.api.OpenMaya.MFn.kMeshPolygonComponent):
            component_type = 'face'
        if component_type:
            component_fn = api.SingleIndexedComponent(component)

        mesh_fn = api.MeshFunction(mesh_dag)

        if 'vtx' == component_type:
            pass
        elif 'edge' == component_type:
            pass
        elif 'face' == component_type:
            pass
        else:
            vertex_ids = range(mesh_fn.get_number_of_vertices())
            vertex_array = api.IntArray()
            vertex_array.set(vertex_ids)

        return skin_fn, vertex_array, skin_name

    def _convert_shape_weights(self, shape, weights):
        """
        Converts given shape weights into a 2D array of vertices
        :param shape:
        :param weights:
        :return:
        """

        return [[weights[i + j * shape] for i in range(shape)] for j in range(int(len(weights) / shape))]


class SkinJointObject(object):
    """
    Class to manage skinning objects easily
    """

    def __init__(self, geometry, name, joint_radius=1.0):
        self._geometry = geometry
        self._name = name
        self._joint_radius = joint_radius
        self._join_ends = False
        self._cvs = list()
        self._cvs_count = 0
        self._skin_cluster = None
        self._joints = list()
        self._cvs_dict = dict()

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def create(self):
        """
        Function that creates skinning
        :return:
        """

        self._create()

    def get_joints_list(self):
        """
        Returns the names of the joints in the skinning
        :return: list(str)
        """

        return self._joints

    def get_skin(self):
        """
        Returns skin deformer name
        :return: str
        """

        return self._skin_cluster

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _create(self):
        """
        Internal function that MUST be override for custom skinning
        """

        raise NotImplementedError()

    def _create_joint(self, cvs):
        """
        Internal function that creates a new joint in the given CV
        :param cvs: list(str)
        :return:  str, name of the created joint
        """

        joint = jnt_utils.create_joint_at_points(cvs, self._name, joint_radius=self._joint_radius)
        cvs = helpers.force_list(cvs)
        self._cvs_dict.setdefault(joint, list()).append(cvs)

        return joint


class SkinJointSurface(SkinJointObject, object):
    """
    Class to manage skinning for surfaces
    """

    def __init__(self, geometry, name, joint_radius=1.0):
        super(SkinJointSurface, self).__init__(geometry, name, joint_radius)

        self._join_ends = False
        self._join_both_ends = False
        self._first_joint_pivot_at_start = True
        self._last_joint_pivot_at_end = True
        self._maya_type = None
        self._joint_u = True
        self._create_mid_joint = False
        self._orient_start_to = None
        self._orient_end_to = None

        if shape_utils.has_shape_of_type(self._geometry, 'nurbsCurve'):
            self._maya_type = 'nurbsCurve'
        elif shape_utils.has_shape_of_type(self._geometry, 'nurbsSurface'):
            self._maya_type = 'nurbsSurface'

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def _create(self):
        self._cvs = maya.cmds.ls('{}.cv[*]'.format(self._geometry), flatten=True)
        if self._maya_type == 'nurbsCurve':
            self._cvs_count = len(self._cvs)
        elif self._maya_type == 'nurbsSurface':
            index = '[0][*]' if self._joint_u else '[*][0]'
            self._cvs_count = len(maya.cmds.ls('{}.cv{}'.format(self._geometry, index), flatten=True))

        start_index = 0
        cvs_count = self._cvs_count

        if self._join_ends:
            if self._join_both_ends:
                self._create_start_and_end_joined_joints()
            else:
                last_joint = self._create_start_and_end_joints()
            cvs_count = len(self._cvs[2:self._cvs_count])
            start_index = 2

        for i in range(start_index, cvs_count):
            if self._maya_type == 'nurbsCurve':
                cv = '{}.cv[{}]'.format(self._geometry, i)
            elif self._maya_type == 'nurbsSurface':
                index = '[*][{}]'.format(i) if self._joint_u else '[{}][*]'.format(i)
                cv = '{}.cv{}'.format(self._geometry, index)

            joint = self._create_joint(cv)
            self._joints.append(joint)

        if self._join_ends and not self._join_both_ends:
            self._joints.append(last_joint)

        self._skin()

        return self._joints

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def set_join_ends(self, flag):
        """
        Sets whether the skin ends of the surfaces take up 2 CVs or not
        :param flag: bool, Whether 2 CVs at the start have one joint, and 2 CVs on the end have one joint
        """

        self._join_ends = flag

    def set_join_both_ends(self, flag):
        """
        Sets whether the skin ends of the surface are joined together
        :param flag: bool, Whether to join or not the ends of the surface
        """

        self._join_both_ends = flag

    def set_last_joint_pivot_at_end(self, flag):
        """
        Sets whether or not the last joint pivot should be moved to the end of the curve
        :param flag: bool
        """

        self._last_joint_pivot_at_end = flag

    def set_first_joint_pivot_at_start(self, flag):
        """
        Sets whether or not the start joint pivot should be moved to the start of the curve
        :param flag: bool
        """

        self._first_joint_pivot_at_start = flag

    def set_joint_u(self, flag):
        """
        Sets whether to skin the U instead of the V spans
        :param flag: bool
        """

        self._joint_u = flag

    def set_create_mid_joint(self, flag):
        """
        Sets whether or not a mid joint should be created
        :param flag: bool
        """

        self._create_mid_joint = flag

    def set_orient_start(self, node):
        """
        Sets which node start joint should be oriented to
        :param node: str
        """

        self._orient_start_to = node

    def set_orient_end(self, node):
        """
        Sets which node end joint should be oriented to
        :param node: str
        """

        self._orient_end_to = node

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _create_start_and_end_joints(self):
        start_cvs = None
        end_cvs = None
        start_position = None
        end_position = None

        if self._maya_type == 'nurbsCurve':
            start_cvs = '{}.cv[0:1]'.format(self._geometry)
            end_cvs = '{}.cv[{}:{}]'.format(self._geometry, self._cvs_count - 2, self._cvs_count - 1)
            start_position = maya.cmds.xform('{}.cv[0]'.format(self._geometry), q=True, ws=True, t=True)
            end_position = maya.cmds.xform(
                '{}.cv[{}]'.format(self._geometry, self._cvs_count - 1), q=True, ws=True, t=True)
        elif self._maya_type == 'nurbsSurface':
            if self._joint_u:
                cv_count_u = len(maya.cmds.ls('{}.cv[*][0]'.format(self._geometry), flatten=True))
                index1 = '[0:*][0:1]'
                index2 = '[0:*][{}:{}]'.format(self._cvs_count - 2, self._cvs_count - 1)
                index3 = '[{}][0]'.format(cv_count_u - 1)
                index4 = '[0][{}]'.format(self._cvs_count - 1)
                index5 = '[{}][{}]'.format(cv_count_u, self._cvs_count - 1)
            else:
                cv_count_v = len(maya.cmds.ls('{}.cv[0][*]'.format(self._geometry), flatten=True))
                index1 = '[0:1][0:*]'
                index2 = '[{}:{}][0:*]'.format(self._cvs_count - 2, self._cvs_count - 1)
                index3 = '[0][{}]'.format(cv_count_v - 1)
                index4 = '[{}][0]'.format(self._cvs_count - 1)
                index5 = '[{}][{}]'.format(self._cvs_count - 1, cv_count_v)

            start_cvs = '{}.cv{}'.format(self._geometry, index1)
            end_cvs = '{}.cv{}'.format(self._geometry, index2)
            p1 = maya.cmds.xform('{}.cv[0][0]'.format(self._geometry), q=True, ws=True, t=True)
            p2 = maya.cmds.xform('{}.cv{}'.format(self._geometry, index3), q=True, ws=True, t=True)
            start_position = vec3.get_mid_point(p1, p2)
            p1 = maya.cmds.xform('{}.cv{}'.format(self._geometry, index4), q=True, ws=True, t=True)
            p2 = maya.cmds.xform('{}.cv{}'.format(self._geometry, index5), q=True, ws=True, t=True)
            end_position = vec3.get_mid_point(p1, p2)

        start_joint = self._create_joint(start_cvs)
        self._joints.append(start_joint)
        if self._first_joint_pivot_at_start:
            maya.cmds.xform(start_joint, ws=True, rp=start_position, sp=start_position)

        end_joint = self._create_joint(end_cvs)
        if self._last_joint_pivot_at_end:
            maya.cmds.xform(end_joint, ws=True, rp=end_position, sp=end_position)

        return end_joint

    def _create_start_and_end_joined_joints(self):
        start_cvs = None
        end_cvs = None

        if self._maya_type == 'nurbsCurve':
            start_cvs = '{}.cv[0:1]'.format(self._geometry)
            end_cvs = '{}.cv[{}:{}]'.format(self._geometry, self._cvs_count - 2, self._cvs_count - 1)
        elif self._maya_type == 'nurbsSurface':
            if self._joint_u:
                index1 = '[0:*][0]'
                index2 = '[0:*][{}]'.format(self._cvs_count - 1)
            else:
                index1 = '[0][0:*]'
                index2 = '[{}][0:*]'.format(self._cvs_count - 1)
            start_cvs = '{}.cv{}'.format(self._geometry, index1)
            end_cvs = '{}.cv{}'.format(self._geometry, index2)

        cvs = start_cvs + end_cvs
        joint = self._create_joint(cvs)
        self._joints.append(joint)

        return joint

    def _skin(self):
        self._skin_cluster = maya.cmds.skinCluster(self._joints, self._geometry, tsb=True)[0]
        if not self._create_mid_joint:
            for joint, cvs in self._cvs_dict.items():
                for cv in cvs:
                    maya.cmds.skinPercent(self._skin_cluster, cv, transformValue=[(joint, 1)])
            maya.cmds.setAttr('{}.skinningMethod'.format(self._skin_cluster), 1)


class SkinJointCurve(SkinJointSurface, object):
    def __init__(self, geometry, name, joint_radius=1.0):
        super(SkinJointCurve, self).__init__(geometry, name, joint_radius)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def set_joint_u(self, flag):
        logger.warning('Cannot set joint U, curves only have one direction for spans')

    def _create(self):
        self._cvs = maya.cmds.ls('{}.cv[*]'.format(self._geometry), flatten=True)
        self._cvs_count = len(self._cvs)
        start_index = 0
        cvs_count = self._cvs_count

        if self._join_ends:
            last_joint = self._create_start_and_end_joints()
            cvs_count = len(self._cvs[2:self._cvs_count])
            start_index = 2

        if not self._create_mid_joint:
            for i in range(start_index, cvs_count):
                joint = self._create_joint('{}.cv[{}]'.format(self._geometry, i))
                self._joints.append(joint)

        if self._orient_start_to:
            maya.cmds.delete(maya.cmds.orientConstraint(self._orient_start_to, self._joints[0]))
        if self._orient_end_to and self._join_ends:
            maya.cmds.delete(maya.cmds.orientConstraint(self._orient_end_to, last_joint))

        if self._join_ends:
            if self._create_mid_joint:
                start_joint = self._joints[0]
                maya.cmds.select(clear=True)
                mid_joint = maya.cmds.joint(n=name_utils.find_unique_name('joint_mid'), radius=self._joint_radius)
                maya.cmds.delete(maya.cmds.pointConstraint(start_joint, last_joint, mid_joint))
                maya.cmds.delete(maya.cmds.orientConstraint(start_joint, last_joint, mid_joint))
                self._joints.append(mid_joint)

            self._joints.append(last_joint)

        self._skin()

        return self._joints

    def _create_start_and_end_joints(self):
        joint = self._create_joint('{}.cv[0:1]'.format(self._geometry))
        self._joints.append(joint)
        position = maya.cmds.xform('{}.cv[0]'.format(self._geometry), query=True, ws=True, t=True)
        # maya.cmds.xform(joint, ws=True, rp=position, sp=position)
        maya.cmds.xform(joint, ws=True, t=position)
        last_joint = self._create_joint('{}.cv[{}:{}]'.format(self._geometry, self._cvs_count - 2, self._cvs_count - 1))
        position = maya.cmds.xform('{}.cv[{}]'.format(self._geometry, self._cvs_count), q=True, ws=True, t=True)
        # maya.cmds.xform(last_joint, ws=True, rp=position, sp=position)
        maya.cmds.xform(last_joint, ws=True, t=position)

        return last_joint


def check_skin(skin_cluster):
    """
    Checks if a node is valid skin cluster and raise and exception if the node is not valid
    :param skin_cluster: str, name of the node to be checked
    :return: bool, True if the given node is a skin cluster node
    """

    if not is_skin_cluster(skin_cluster):
        raise exceptions.SkinClusterException(skin_cluster)


def is_skin_cluster(skin_cluster):
    """
    Checks if the given node is a valid skinCluster
    :param skin_cluster:  str, name of the node to be checked
    :return: bool, True if the given node is a skin cluster node
    """

    if not maya.cmds.objExists(skin_cluster):
        logger.error('SkinCluster "{}" does not exists!'.format(skin_cluster))
        return False
    if maya.cmds.objectType(skin_cluster) != 'skinCluster':
        logger.error('Object "{}" is not a valid skinCluster node!'.format(skin_cluster))
        return False

    return True


def find_related_skin_cluster(geo):
    """
    Returns the skinCluster node attached to the specified geometry
    :param geo: str, geometry
    :return: variant, None || str
    """

    node_utils.check_node(node=geo)

    shape_node = node_utils.shape(node_name=geo)
    if not shape_node:
        return None

    skin_cluster = maya.mel.eval('findRelatedSkinCluster("{}")'.format(shape_node))
    if not skin_cluster:
        skin_cluster = maya.cmds.ls(maya.cmds.listHistory(shape_node), type='skinCluster')
        if skin_cluster:
            skin_cluster = skin_cluster[0]
    if not skin_cluster:
        return None

    return skin_cluster


def compare_influences_in_meshes_skin_clusters(skinned_meshes, query=False):
    """
    Returns whether or not given skin clusters have the same influencing joints
    :param skinned_meshes: list(str), list of skinned meshes we want to compare
    :param query: bool
    :return: bool
    """

    compares_list = list()

    for skinned_mesh in skinned_meshes:
        skin_cluster_name = find_related_skin_cluster(skinned_mesh)
        if not skin_cluster_name:
            continue
        joints = maya.cmds.skinCluster(skin_cluster_name, query=True, inf=True)
        compares_list.append([skinned_mesh, joints])

    if len(compares_list) < 2:
        logger.error('At least 2 skinned geometries are needed to compare skin clusters.')
        return False

    total_compares = len(compares_list)
    missing_joints_list = list()

    for i in range(total_compares):
        for compare_list in compares_list:
            if compare_list == compares_list[i]:
                continue
            missed_joints = list()
            for match in compare_list[1]:
                if not any(match in value for value in compares_list[i][1]):
                    missed_joints.append(match)
            missing_joints_list.append([compares_list[i][0], missed_joints])

    if query:
        joints = list()
        for missing_list in missing_joints_list:
            for joint in missing_list[1]:
                joints.append(joint)
        if not joints:
            return None
        return True
    else:
        for missing_joints in missing_joints_list:
            skin_cluster_name = find_related_skin_cluster(missing_joints[0])
            if not skin_cluster_name:
                continue
            for joint in missing_joints[1]:
                try:
                    maya.cmds.skinCluster(
                        skin_cluster_name, query=True, lockWeights=False, weight=0.0, addInfluence=joint)
                except Exception:
                    pass

    return True


@decorators.undo
def restore_to_bind_pose(skinned_mesh=None):
    """
    Reset the given skinned meshes back to bind pose without the need of the bind pose node
    It uses the prebind matrix of the joints to calculate the bind pose
    :param skinned_mesh: list(str), list of skinned meshes to reset to bind pose
    :return: bool
    """

    skinned_meshes = skinned_mesh or dcc.selected_nodes_of_type('transform')
    skinned_meshes = helpers.force_list(skinned_meshes)
    if not skinned_meshes:
        skinned_meshes = list()
        meshes = dcc.list_nodes(node_type='mesh')
        for mesh in meshes:
            skinned_meshes.append(maya.cmds.listRelatives(mesh, parent=True)[0])
    if not skinned_meshes:
        return False

    for skin_mesh in skinned_meshes:
        if maya.cmds.objectType(skin_mesh) == 'joint':
            continue
        mesh_shapes = maya.cmds.listRelatives(shapes=True)
        if not mesh_shapes:
            continue
        if maya.cmds.objectType(mesh_shapes[0]) != 'mesh':
            continue

        skin_cluster_name = find_related_skin_cluster(skin_mesh)
        if not skin_cluster_name:
            continue

        influence_joints = maya.cmds.skinCluster(skin_cluster_name, query=True, influence=True)
        if not influence_joints:
            continue
        bind_pose_node = maya.cmds.dagPose(influence_joints[0], query=True, bindPose=True)
        if bind_pose_node:
            maya.cmds.select(skin_mesh)
            maya.mel.eval('gotoBindPose;')
        else:
            for i, joint in enumerate(influence_joints):
                prebind_matrix = maya.cmds.getAttr('{}.bindPreMatrix[{}]'.format(skin_cluster_name, i))
                api_matrix = api.Matrix(prebind_matrix).inverse()
                matrix_list = api_matrix.to_list()
                maya.cmds.xform(joint, ws=True, m=matrix_list)

    return True


@decorators.undo
def remove_all_bind_poses_in_scene():
    """
    Deletes all bind poses nodes from current scene
    :return: bool
    """

    dag_poses = maya.cmds.ls(type='dagPose') or list()
    for dag_pose in dag_poses:
        if not maya.cmds.getAttr('{}.bindPose'.format(dag_pose)):
            continue
        maya.cmds.delete(dag_pose)

    return True


@decorators.undo
def average_vertices_weights(selection, use_distance):
    """
    Generates an average weight from all selected vertices to apply to the last selected vertex
    :param selection: list<Vertex>, list of vertices to average
    :param use_distance:
    :return:
    """

    total_vertices = len(selection)
    if total_vertices < 2:
        logger.warning('Not enough vertices selected! Select a minimum of 2 vertices')
        return

    obj = selection[0]
    if '.' in selection[0]:
        obj = selection[0].split('.')[0]

    is_edge_selection = False
    if '.e[' in selection[0]:
        is_edge_selection = True

    skin_cluster_name = find_related_skin_cluster(obj)
    maya.cmds.setAttr('{0}.envelope'.format(skin_cluster_name), 0)
    succeeded = True

    # TODO: Support for multiple geometry types
    poly = True
    added = 0.0

    try:
        maya.cmds.skinCluster(obj, edit=True, normalizeWeights=True)
        if total_vertices == 2 or is_edge_selection:
            base_list = [selection]
            if is_edge_selection:
                base_list = mesh_utils.edges_to_smooth(edges_list=selection)

            percentage = 99.0 / len(base_list)
            for i, vert_list in enumerate(base_list):
                start = vert_list[0]
                end = vert_list[-1]
                order = mesh_utils.find_shortest_vertices_path_between_vertices(vert_list)
                if order:
                    order = order[:-1]      # we are not interested in the last vertex
                    amount = len(order) + 1
                    total_distance = api_mathlib.distance_between_nodes(order[-1], end)
                    list_bone_influences = maya.cmds.skinCluster(obj, query=True, inf=True)
                    weights_start = maya.cmds.skinPercent(skin_cluster_name, start, query=True, v=True)
                    weights_end = maya.cmds.skinPercent(skin_cluster_name, end, query=True, v=True)

                    lengths = list()
                    if use_distance:
                        for j, vertex in enumerate(order):
                            if j == 0:
                                length = api_mathlib.distance_between_nodes(start, vertex)
                            else:
                                length = api_mathlib.distance_between_nodes(order[j - 1], vertex)
                            if poly:
                                total_distance += length
                            lengths.append(length)

            percentage = float(1.0) / (amount + added)
            current_length = 0.0

            for i, vertex in enumerate(order):
                if use_distance:
                    current_length += lengths[i]
                    current_percentage = (current_length / total_distance)
                else:
                    current_percentage = i * percentage
                    if poly:
                        current_percentage = (i + 1) * percentage

                new_weight_list = list()
                for j, weight in enumerate(weights_start):
                    value1 = weights_end[j] * current_percentage
                    value2 = weights_end[j] * (1 - current_percentage)
                    new_weight_list.append((list_bone_influences[j], value1 + value2))

                maya.cmds.skinPercent(skin_cluster_name, vertex, transformValue=new_weight_list)

        else:
            last_selected = selection[-1]
            point_list = [x for x in selection if x != last_selected]
            mesh_name = last_selected.split('.')[0]

            list_joint_influences = maya.cmds.skinCluster(mesh_name, query=True, weightedInfluence=True)
            influence_size = len(list_joint_influences)

            temp_vertex_joints = list()
            temp_vertex_weights = list()
            for pnt in point_list:
                for jnt in range(influence_size):
                    point_weights = maya.cmds.skinPercent(
                        skin_cluster_name, pnt, transform=list_joint_influences[jnt], query=True, value=True)
                    if point_weights < 0.000001:
                        continue
                    temp_vertex_joints.append(list_joint_influences[jnt])
                    temp_vertex_weights.append(point_weights)

            total_values = 0.0
            average_values = list()
            clean_list = list()
            for i in temp_vertex_joints:
                if i not in clean_list:
                    clean_list.append(i)

            for i in range(len(clean_list)):
                working_value = 0.0
                for j in range(len(temp_vertex_joints)):
                    if not temp_vertex_joints[j] == clean_list[i]:
                        continue
                    working_value += temp_vertex_weights[j]
                num_points = len(point_list)
                average_values.append(working_value / num_points)
                total_values += average_values[i]

            summary = 0
            for value in range(len(average_values)):
                temp_value = average_values[value] / total_values
                average_values[value] = temp_value
                summary += average_values[value]

            cmd = StringIO.StringIO()
            cmd.write('maya.cmds.skinPercent("%s","%s", transformValue=[' % (skin_cluster_name, last_selected))

            for count, skin_joint in enumerate(clean_list):
                cmd.write('("%s", %s)' % (skin_joint, average_values[count]))
                if not count == len(clean_list) - 1:
                    cmd.write(', ')
            cmd.write('])')
            eval(cmd.getvalue())
    except Exception:
        logger.warning(str(traceback.format_exc()))
        succeeded = False
    finally:
        maya.cmds.setAttr('{0}.envelope'.format(skin_cluster_name), 1)

    return succeeded


@decorators.undo
def apply_smooth_bind(geo=None, show_options=False):
    """
    Applies smooth bind to given nodes
    :param geo: str or list(str) or None
    :param show_options: bool
    :return: bool
    """

    geo = geo or maya.cmds.ls(sl=True)
    if not geo:
        return False
    geo = helpers.force_list(geo)

    if show_options:
        maya.cmds.SmoothBindSkinOptions()
    else:
        raise NotImplementedError('Apply Smooth Bind Skin without options is not implemented yet!')

    return True


@decorators.undo
def apply_rigid_skin(geo=None, show_options=False):
    """
    Applies smooth bind to given nodes
    :param geo: str or list(str) or None
    :param show_options: bool
    :return: bool
    """

    geo = geo or maya.cmds.ls(sl=True)
    if not geo:
        return False
    geo = helpers.force_list(geo)

    if show_options:
        maya.cmds.RigidBindSkinOptions()
    else:
        raise NotImplementedError('Apply Rigid Bind Skin without options is not implemented yet!')

    return True


@decorators.undo
def detach_bind_skin(geo=None, show_options=False):
    """
    Detaches bind skin of the given nodes
    :param geo: str or list(str) or None
    :param show_options: bool
    :return: bool
    """

    geo = geo or maya.cmds.ls(sl=True)
    geo = helpers.force_list(geo)

    if show_options:
        maya.cmds.DetachSkinOptions()
    else:
        if not geo:
            return False
        maya.cmds.DetachSkin()

    return True


def open_pain_skin_weights_tool(show_options=True):
    """
    Opens Maya Paint Skin Weights Tool
    :param show_options: bool
    :return: bool
    """

    if show_options:
        maya.cmds.ArtPaintSkinWeightsToolOptions()
    else:
        maya.cmds.ArtPaintSkinWeightsTool()

    return True


def reset_skinned_joints(skinned_joints, skin_cluster_name=None):
    """
    Reset skin deformation for given joints by recomputing all prebind matrices in current pose
    Similar to Move Skinned Joints tool but works even with constrained joints.
    Call this function after moving/rotating a skinned joint to reset the mesh deformation to its non-deformed state
    while maintaining the transformed joint in its new position/rotation
    http://leftbulb.blogspot.com/2012/09/resetting-skin-deformation-for-joint.html
    :param skinned_joints: list(str), list of skinned joints to reset
    :param skin_cluster_name: str, name of the skin cluster joint is skinned to
    """

    for joint in skinned_joints:
        skin_cluster_plugs = maya.cmds.listConnections(
            '{}.worldMatrix[0]'.format(joint), type='skinCluster', plugs=True)
        if skin_cluster_name and skin_cluster_plugs:
            for skin_cluster_plug in skin_cluster_plugs:
                if skin_cluster_name in skin_cluster_plug:
                    skin_cluster_plugs = [skin_cluster_plug]

        if skin_cluster_plugs:
            for skin_cluster_plug in skin_cluster_plugs:
                index = skin_cluster_plug[skin_cluster_plug.index('[') + 1:-1]
                skin_cluster = skin_cluster_plug[:skin_cluster_plug.index('.')]
                inverse_matrix = maya.cmds.getAttr('{}.worldInverseMatrix'.format(joint))
                maya.cmds.setAttr('{}.bindPreMatrix[{}]'.format(skin_cluster, index), type='matrix', *inverse_matrix)
                if dcc.version() >= 2016:
                    maya.cmds.skinCluster(skin_cluster, edit=True, recacheBindMatrices=True)
                    maya.cmds.dgdirty(skin_cluster)
        else:
            logger.warning(
                'Impossible to reset skinned joint "{}" bind matrix because no skin cluster found!'.format(joint))
            continue

    return True


@decorators.undo
def move_skin_weights(source_joint=None, target_joint=None, mesh=None):
    """
    Transfers skin weights from source joint to target joint
    :param source_joint: str
    :param target_joint: str
    :param mesh: str
    """

    selection = dcc.selected_nodes()
    source_joint = source_joint or (selection[0] if helpers.index_exists_in_list(selection, 0) else None)
    target_joint = target_joint or (selection[1] if helpers.index_exists_in_list(selection, 1) else None)
    mesh = mesh or (selection[2] if helpers.index_exists_in_list(selection, 2) else None)

    skin_cluster_name = find_related_skin_cluster(mesh)
    if not skin_cluster_name:
        logger.warning('Given mesh "{}" has no skin cluster attached to it!'.format(mesh))
        return False

    source_joint_short = dcc.node_short_name(source_joint)
    target_joint_short = dcc.node_short_name(target_joint)

    if source_joint_short == target_joint_short:
        return True

    # Make sure that given joints are influences of the skin cluster
    influence_joints = maya.cmds.skinCluster(skin_cluster_name, query=True, inf=True)
    if source_joint_short not in influence_joints:
        maya.cmds.skinCluster(skin_cluster_name, edit=True, lockWeights=False, weight=0.0, addInfluence=source_joint)
    if target_joint_short not in influence_joints:
        maya.cmds.skinCluster(skin_cluster_name, edit=True, lockWeights=False, weight=0.0, addInfluence=target_joint)
    total_infs = len(influence_joints)

    mesh_shape_name = shape_utils.get_shapes(mesh)[0]
    out_wgts_array = api_skin.get_skin_weights(skin_cluster_name, mesh_shape_name)
    total_weights = len(out_wgts_array)

    src_jnt_index = 0
    tgt_jnt_index = 0
    for i in range(total_infs):
        if influence_joints[i] == source_joint_short:
            src_jnt_index = i
        if influence_joints[i] == target_joint_short:
            tgt_jnt_index = i

    amount_to_loop = int(total_weights / total_infs)

    for i in range(amount_to_loop):
        new_value = out_wgts_array[(i * total_infs) + tgt_jnt_index] + out_wgts_array[(i * total_infs) + src_jnt_index]
        out_wgts_array[(i * total_infs) + tgt_jnt_index] = new_value
        out_wgts_array[(i * total_infs) + src_jnt_index] = 0.0

    api_skin.set_skin_weights(skin_cluster_name, mesh_shape_name, out_wgts_array)

    return True


@decorators.undo
def swap_skin_weights(source_joint=None, target_joint=None, mesh=None):
    """
    Swaps skin weights from source joint to target joint by reconnecting matrices in given mesh skin cluster node
    NOTE: Due to matrix reconnection, this swapping is only applicable in bind pose (but its fast)
    :param source_joint: str
    :param target_joint: str
    :param mesh: str
    """

    # TODO: Implement another function (a slower one) that allow us to the the swapping in non bind pose

    selection = dcc.selected_nodes()
    source_joint = source_joint or (selection[0] if helpers.index_exists_in_list(selection, 0) else None)
    target_joint = target_joint or (selection[1] if helpers.index_exists_in_list(selection, 1) else None)
    mesh = mesh or (selection[2] if helpers.index_exists_in_list(selection, 2) else None)

    skin_cluster_name = find_related_skin_cluster(mesh)
    if not skin_cluster_name:
        logger.warning('Given mesh "{}" has no skin cluster attached to it!'.format(mesh))
        return False

    source_connections = maya.cmds.listConnections(
        '{}.worldMatrix'.format(source_joint), source=False, destination=True,
        connections=True, plugs=True, type='skinCluster')
    target_connections = maya.cmds.listConnections(
        '{}.worldMatrix'.format(target_joint), source=False, destination=True,
        connections=True, plugs=True, type='skinCluster')

    source_same_skin_cluster = False
    target_same_skin_cluster = False
    source_current_connection = ''
    target_current_connection = ''

    for source_connection in source_connections:
        if source_connection.split('.')[0] == skin_cluster_name:
            source_same_skin_cluster = True
            source_current_connection = source_connection
    for target_connection in target_connections:
        if target_connection.split('.')[0] == skin_cluster_name:
            target_same_skin_cluster = True
            target_current_connection = target_connection

    if not source_same_skin_cluster:
        logger.warning(
            'Joint "{}" is not part of the given skin cluster node "{}"'.format(source_joint, skin_cluster_name))
        return False
    if not target_same_skin_cluster:
        logger.warning(
            'Joint "{}" is not part of the given skin cluster node "{}"'.format(target_joint, skin_cluster_name))
        return False

    try:
        source_orig_connection = source_current_connection.split('matrix')[-1]
        target_orig_connection = target_current_connection.split('matrix')[-1]

        maya.cmds.disconnectAttr('{}.worldMatrix'.format(source_joint), source_current_connection)
        maya.cmds.disconnectAttr('{}.worldMatrix'.format(target_joint), target_current_connection)
        maya.cmds.disconnectAttr(
            '{}.lockInfluenceWeights'.format(source_joint),
            '{}.lockWeights{}'.format(skin_cluster_name, source_orig_connection))
        maya.cmds.disconnectAttr(
            '{}.lockInfluenceWeights'.format(target_joint),
            '{}.lockWeights{}'.format(skin_cluster_name, target_orig_connection))

        maya.cmds.connectAttr('{}.worldMatrix'.format(source_joint), target_current_connection, force=True)
        maya.cmds.connectAttr('{}.worldMatrix'.format(target_joint), source_current_connection, force=True)
        maya.cmds.connectAttr(
            '{}.lockInfluenceWeights'.format(source_joint),
            '{}.lockWeights{}'.format(skin_cluster_name, target_orig_connection), force=True)
        maya.cmds.connectAttr(
            '{}.lockInfluenceWeights'.format(target_joint),
            '{}.lockWeights{}'.format(skin_cluster_name, source_orig_connection), force=True)

        reset_skinned_joints([source_joint, target_joint], skin_cluster_name=skin_cluster_name)

    except Exception as exc:
        logger.exception('Error while swapping joints: "{}"'.format(exc))
        return False

    return True


@decorators.undo
def mirror_skin_weights(mesh=None, show_options=False, **kwargs):
    """
    Mirrors skin weights
    :param mesh: str
    :param show_options: bool
    """

    transforms = mesh or dcc.selected_nodes_of_type('transform')
    transforms = helpers.force_list(transforms)
    if not transforms:
        return False

    if kwargs.pop('auto_assign_labels', False):
        jnt_utils.auto_assign_labels_to_mesh_influences(
            transforms, input_left=kwargs.pop('left_side_label', None),
            input_right=kwargs.pop('right_side_label', None), check_labels=True)

    if show_options:
        maya.cmds.optionVar(stringValue=("mirrorSkinAxis", "YZ"))
        maya.cmds.optionVar(intValue=("mirrorSkinWeightsSurfaceAssociationOption", 3))
        maya.cmds.optionVar(intValue=("mirrorSkinWeightsInfluenceAssociationOption1", 3))
        maya.cmds.optionVar(intValue=("mirrorSkinWeightsInfluenceAssociationOption2", 2))
        maya.cmds.optionVar(intValue=("mirrorSkinWeightsInfluenceAssociationOption3", 1))
        maya.cmds.optionVar(intValue=("mirrorSkinNormalize", 1))
        maya.cmds.MirrorSkinWeightsOptions()
    else:
        raise NotImplementedError('Mirror Skin Weights with no options not implemented yet!')

    return True


@decorators.undo
def copy_skin_weights(
        source_mesh=None, target_mesh=None, show_options=False, **kwargs):
    """
    Copy skin weights
    :param source_mesh: str, name of the mesh we want to copy skin weights from
    :param target_mesh: str, name of the mesh we want to paste skin weights to
    :param show_options: bool
    """

    selection = dcc.selected_nodes_of_type('transform')
    source_transform = source_mesh or (selection[0] if helpers.index_exists_in_list(selection, 1) else None)
    target_transform = target_mesh or (selection[1] if helpers.index_exists_in_list(selection, 1) else None)
    if not source_transform or not target_transform:
        logger.warning('Select source mesh and target mesh before executing Copy Skin Weights')
        return False

    if kwargs.pop('auto_assign_labels', False):
        jnt_utils.auto_assign_labels_to_mesh_influences(
            [source_transform, target_transform], input_left=kwargs.pop('left_side_label', None),
            input_right=kwargs.pop('right_side_label', None))

    if show_options:
        maya.cmds.optionVar(intValue=("copySkinWeightsSurfaceAssociationOption", 3))
        maya.cmds.optionVar(intValue=("copySkinWeightsInfluenceAssociationOption1", 4))
        maya.cmds.optionVar(intValue=("copySkinWeightsInfluenceAssociationOption2", 4))
        maya.cmds.optionVar(intValue=("copySkinWeightsInfluenceAssociationOption3", 6))
        maya.cmds.optionVar(intValue=("copySkinWeightsNormalize", 1))
        maya.cmds.CopySkinWeightsOptions()
    else:
        raise NotImplementedError('Copy Skin Weights with no options not implemented yet!')

    return True


@decorators.undo
@decorators.repeat_static_command(__name__, skip_arguments=True)
def transfer_skinning(source_mesh, target_meshes, in_place=True, component_association=True, uv_space=False):
    """
    Transfers skinning from one skinned mesh to other meshes using native Maya copySkinWweights command
    :param source_mesh: str, mesh to copy skinning information from
    :param target_meshes: list(str), list of messes that will gather weight skin cluster information from source mesh
    :param in_place: bool, If True, will make sure to cleanup the mesh and apply the skinning; Ohterwise it assumes
        that skinning is already applied to target meshes and just copies the the weights
    :param component_association: bool, Whether closesCompnent association is used or closestPoint
    :param uv_space: bool, Whether UV space is used to transfer the skinning data
    :return: bool
    """

    source_skin_cluster = find_related_skin_cluster(source_mesh)
    if not source_skin_cluster:
        return False

    surface_association = 'closestComponent' if component_association else 'closestPoint'

    for target_mesh in target_meshes:
        if in_place:
            maya.cmds.delete(target_mesh, ch=True)
        else:
            target_skin_cluster = find_related_skin_cluster(target_mesh)
            if not target_skin_cluster:
                continue
            maya.cmds.skinCluster(target_skin_cluster, edit=True, unbind=True)

        join_influences = maya.cmds.skinCluster(source_skin_cluster, query=True, influence=True)
        max_influences = maya.cmds.skinCluster(source_skin_cluster, query=True, maximumInfluences=True)
        remove_all_bind_poses_in_scene()
        new_skin_cluster = maya.cmds.skinCluster(join_influences, target_mesh, maximumInfluences=max_influences)[0]
        if uv_space:
            maya.cmds.copySkinWeights(
                sourceSkin=source_skin_cluster, destinationSkin=new_skin_cluster, noMirror=True,
                surfaceAssociation=surface_association, uv=['map1', 'map1'],
                influenceAssociation=['label', 'oneToOne', 'name'], normalize=True)
        else:
            maya.cmds.copySkinWeights(
                sourceSkin=source_skin_cluster, destinationSkin=new_skin_cluster, noMirror=True,
                surfaceAssociation=surface_association, influenceAssociation=['label', 'oneToOne', 'name'],
                normalize=True)

        return True


@decorators.undo
def prune_skin_weights(geo=None, show_options=False):
    geo = geo or maya.cmds.ls(sl=True)
    geo = helpers.force_list(geo)

    if show_options:
        maya.cmds.PruneSmallWeightsOptions()
    else:
        if not geo:
            return False
        raise NotImplementedError('Prune Weights with no options not implemented yet!')

    return True


@decorators.undo
def transfer_uvs_to_skinned_geometry(source_mesh=None, target_mesh=None, use_intermediate_shape=False, **kwargs):
    """
    Transfer UVs from one skinned mesh to another one
    :param source_mesh: str, name of the mesh we want to copy skin weights from
    :param target_mesh: str, name of the mesh we want to paste skin weights to
    :param use_intermediate_shape: bool, Whether to use intermediate shape instead of final shapes. In some scenarios,
        this can give cleaner transfers and no deformation with bind movement
    """

    selection = dcc.selected_nodes_of_type('transform')
    source_transform = source_mesh or (selection[0] if helpers.index_exists_in_list(selection, 0) else None)
    target_transform = target_mesh or (selection[1] if helpers.index_exists_in_list(selection, 1) else None)
    if not source_transform or not target_transform:
        logger.warning('Select source mesh and target mesh before executing Copy Skin Weights')
        return False

    if kwargs.pop('auto_assign_labels', False):
        jnt_utils.auto_assign_labels_to_mesh_influences(
            [source_mesh, target_mesh], input_left=kwargs.pop('left_side_label', None),
            input_right=kwargs.pop('right_side_label', None))

    if dcc.node_type(source_transform) == 'transform':
        source_shapes = dcc.list_shapes_of_type(source_transform, shape_type='mesh', intermediate_shapes=False)
    else:
        source_shapes = maya.cmds.listRelatives(source_mesh, ad=True, type='mesh')
    if not source_shapes:
        logger.error(
            'Impossible to transfer skin UVs from "{}" to "{}" because source object has no shapes!'.format(
                source_transform, target_transform))
        return False
    source_shape = source_shapes[0]

    if dcc.node_type(target_transform) == 'transform':
        target_shapes = dcc.list_shapes_of_type(
            target_transform, shape_type='mesh', intermediate_shapes=use_intermediate_shape)
    else:
        target_shapes = maya.cmds.listRelatives(target_mesh, ad=True, type='mesh')
    if not target_shapes:
        logger.error(
            'Impossible to transfer skin UVs from "{}" to "{}" because target object has no shapes!'.format(
                source_transform, target_transform))
        return False

    if use_intermediate_shape:
        target_mesh = None
        target_mesh_orig = None
        for target_shape in target_shapes:
            if maya.cmds.getAttr('{}.intermediateObject'.format(target_shape)) == 0:
                continue
            target_mesh = target_shape
            target_mesh_orig = target_shape
        if not target_mesh_orig:
            logger.error(
                'Impossible to transfer skin UVs from "{}" to "{}" because no intermediate shape '
                'found in target shape!'.format(source_transform, target_transform))
            return False

        maya.cmds.setAttr('{}.intermediateObject'.format(target_mesh), 0)
        maya.cmds.transferAttributes(
            source_shape, target_mesh_orig, transferPositions=False, transferNormals=False, transferUVs=2,
            transferColors=2, sampleSpace=4, sourceUvSpace='map1', targetUvSpace='map1', searchMethod=3, flipUVs=False,
            colorBorders=True)
        maya.cmds.setAttr('{}.intermediateObject'.format(target_mesh), 1)
        maya.cmds.delete(target_mesh_orig, ch=True)
    else:
        maya.cmds.transferAttributes(
            source_shape, target_shapes[0], transferPositions=False, transferNormals=False, transferUVs=2,
            transferColors=2, sampleSpace=4, sourceUvSpace='map1', targetUvSpace='map1', searchMethod=3, flipUVs=False,
            colorBorders=True)

    return True


@decorators.undo
@decorators.repeat_static_command(__name__, skip_arguments=True)
def freeze_skinned_mesh(skinned_mesh, **kwargs):
    """
    Freezes the transformations and deletes the history of the given skinned meshes
    :param skinned_mesh: str or list(str)
    :return: bool
    """

    meshes = skinned_mesh or dcc.selected_nodes_of_type('transform')
    meshes = helpers.force_list(meshes)
    if not meshes:
        return False

    if kwargs.pop('auto_assign_labels', False):
        jnt_utils.auto_assign_labels_to_mesh_influences(
            meshes, input_left=kwargs.pop('left_side_label', None),
            input_right=kwargs.pop('right_side_label', None), check_labels=True)

    try:
        for i, mesh in enumerate(meshes):
            skin_cluster_name = find_related_skin_cluster(mesh)
            if not skin_cluster_name:
                continue
            attached_joints = maya.cmds.skinCluster(skin_cluster_name, query=True, inf=True)
            mesh_shape_name = maya.cmds.listRelatives(mesh, shapes=True)[0]
            out_influences_array = api_skin.get_skin_weights(skin_cluster_name, mesh_shape_name)
            maya.cmds.skinCluster(mesh_shape_name, edit=True, unbind=True)
            maya.cmds.delete(mesh, ch=True)
            maya.cmds.makeIdentity(mesh, apply=True)
            new_skin_cluster_name = maya.cmds.skinCluster(
                attached_joints, mesh, toSelectedBones=True, bindMethod=0, normalizeWeights=True)[0]
            api_skin.set_skin_weights(new_skin_cluster_name, mesh_shape_name, out_influences_array)

        dcc.select_node(meshes)

    except Exception:
        logger.error('Error while freezing skinned mesh "{}" : {}'.format(mesh, traceback.format_exc()))
        return False

    return True


def get_influencing_joints(mesh_node):
    """
    Returns all the joints that influence the mesh
    :param mesh_node: str, mesh to retrieve influenced joints of
    :return: list(str)
    """

    skin_cluster_name = find_related_skin_cluster(mesh_node)
    if not skin_cluster_name:
        return list()

    influencing_joints = maya.cmds.skinCluster(skin_cluster_name, query=True, inf=True)

    return influencing_joints


@decorators.undo
def select_influencing_joints(mesh_node=None):
    """
    Selects all the joints that are influencing the given mesh
    :param mesh_node: str, mesh to retrieve influenced joints of
    """

    if not mesh_node:
        selected_transforms = dcc.selected_nodes_of_type(node_type='transform')
        mesh_node = selected_transforms[0] if selected_transforms else None
    if not mesh_node:
        return False

    influencing_joints = get_influencing_joints(mesh_node)
    if not influencing_joints:
        return False

    maya.cmds.select(influencing_joints, replace=True)

    return True


def get_influence_vertices(joint_nodes, mesh_name):
    """
    Returns the vertices of the given mesh that are skinned to the given influence of the mesh skin cluster
    :param joint_nodes: str or list(str), name of the joint we want o retrieve influencing vertices of
    :param mesh_name: str, name of the mesh that has the skin cluster attached
    :return: list(str)
    """

    selected_transforms = dcc.selected_nodes_of_type('transform')
    selected_joints = dcc.selected_nodes_of_type('joint')
    joint_nodes = joint_nodes or selected_joints
    if not mesh_name:
        mesh_names = [xform for xform in selected_transforms if xform not in selected_joints]
        mesh_name = mesh_names[0] if mesh_names else None
    if not joint_nodes or not mesh_name:
        return False
    joint_nodes = helpers.force_list(joint_nodes)
    joint_nodes_short = [dcc.node_short_name(joint_node) for joint_node in joint_nodes]

    skin_cluster_name = find_related_skin_cluster(mesh_name)
    if not skin_cluster_name:
        logger.warning('Given mesh "{}" has no skin cluster attached to it!'.format(mesh_name))
        return False

    selection = list()
    percentage = 100.0 / len(joint_nodes)
    progress_value = 0.0

    for i, joint in enumerate(joint_nodes):
        # PyMEL implementation
        # from pymel.core.general import PyNode
        # joints_attached = maya.cmds.skinCluster(skin_cluster_name, query=True, inf=True)
        # if joint_nodes_short[i] not in joints_attached:
        #     continue
        # skin_node = PyNode(skin_cluster_name)
        # vertices_list, values = skin_node.getPointsAffectedByInfluence(joint)
        # found_vertices = vertices_list.getSelectionStrings()
        # if len(found_vertices) == 0:
        #     continue
        # selected_vertices = mesh_utils.convert_to_vertices(found_vertices)
        maya.cmds.select(clear=True)
        maya.cmds.skinCluster(mesh_name, edit=True, normalizeWeights=True)
        maya.cmds.select(joint, deselect=True)
        mesh_utils.fix_mesh_components_selection_visualization(mesh_name)
        maya.cmds.select(clear=True)
        maya.cmds.skinCluster(skin_cluster_name, edit=True, selectInfluenceVerts=True)
        selected_vertices = maya.cmds.ls(sl=True, flatten=True)

        if not selected_vertices:
            continue

        for selected_vertex in selected_vertices:
            if '.' not in selected_vertex:
                continue
            selection.append(selected_vertex)

        progress_value += (percentage * i)

    mesh_utils.fix_mesh_components_selection_visualization(mesh_name)

    return selection


@decorators.undo
def select_influence_vertices(joint_nodes=None, mesh_name=None):
    """
    Selects the vertices of the given mesh that are skinned to the given influence of the mesh skin cluster
    :param joint_nodes: str or list(str), name of the joint we want o retrieve influencing vertices of
    :param mesh_name: str, name of the mesh that has the skin cluster attached
    """

    selected_influence_vertices = get_influence_vertices(joint_nodes=joint_nodes, mesh_name=mesh_name)
    if not selected_influence_vertices:
        return False

    maya.cmds.select(selected_influence_vertices, replace=True)

    return True


@decorators.undo
def unbind_influences_quick(skinned_objects=None, influences_to_unbind=None, delete=False):
    """
    Unbind given influences from given meshes and stores the unbind influences weights into other influences
    The weights reassignation is handled by Maya
    :param skinned_objects: list(str), meshes which joints need to be removed
    :param influences_to_unbind: list(str), list of joints that need to be unbind
    :param delete: bool, Whether or not to delete unbind influences after unbind process is completed
    :return: bool
    """

    selected_transforms = dcc.selected_nodes_of_type('transform')
    selected_joints = dcc.selected_nodes_of_type('joint')
    influences_to_unbind = influences_to_unbind or selected_joints
    if not skinned_objects:
        skinned_objects = [xform for xform in selected_transforms if xform not in selected_joints]
    if not skinned_objects or not influences_to_unbind:
        return False
    skinned_objects = helpers.force_list(skinned_objects)
    influences_to_unbind = helpers.force_list(influences_to_unbind)
    influences_to_unbind_short = [dcc.node_short_name(joint_node) for joint_node in influences_to_unbind]

    skin_clusters = list()
    skin_percentage = 100.0 / len(skinned_objects)
    progress_value = 0.0

    for i, skin_object in enumerate(skinned_objects):
        skin_cluster_name = find_related_skin_cluster(skin_object)
        if not skin_cluster_name:
            continue
        joints_attached = maya.cmds.skinCluster(skin_cluster_name, query=True, inf=True)

        influence_verts = get_influence_vertices(influences_to_unbind, skin_object)
        if not influence_verts:
            continue

        joints = list()
        for joint_to_remove in influences_to_unbind_short:
            if joint_to_remove not in joints_attached:
                continue
            joints.append((joint_to_remove, 0.0))

        maya.cmds.select(influence_verts, replace=True)
        maya.cmds.skinPercent(skin_cluster_name, transformValue=joints, normalize=True)

        progress_value += (i * skin_percentage)

        skin_clusters.append(skin_cluster_name)

    for skin_cluster in skin_clusters:
        joints_attached = maya.cmds.skinCluster(skin_cluster, query=True, inf=True)
        for jnt in influences_to_unbind_short:
            if jnt not in joints_attached:
                continue
            maya.cmds.skinCluster(skin_cluster, edit=True, removeInfluence=jnt)

    if delete:
        for joint_to_remove in influences_to_unbind:
            child_joints = maya.cmds.listRelatives(joint_to_remove, children=True)
            parent = maya.cmds.listRelatives(joint_to_remove, parent=True)
            if not child_joints:
                continue
            if not parent:
                maya.cmds.parent(child_joints, world=True)
                continue
            maya.cmds.parent(child_joints, parent)
        maya.cmds.delete(influences_to_unbind)

    progress_value = 100.0

    return True


@decorators.undo
def unbind_influences(skinned_objects=None, influences_to_unbind=None, delete=False, use_parent=True):
    """
    Unbind given influences from given meshes and stores the unbind influences weights into other influences

    :param skinned_objects: list(str), meshes which joints need to be removed
    :param influences_to_unbind: list(str), list of joints that need to be unbind
    :param delete: bool, Whether or not to delete unbind influences after unbind process is completed
    :param use_parent: bool, If True, removed influences weights will be stored on its parent; if False it will look
        for the closest joint using a point cloud system
    :return: bool
    """

    selected_transforms = dcc.selected_nodes_of_type('transform')
    selected_joints = dcc.selected_nodes_of_type('joint')
    influences_to_unbind = influences_to_unbind or selected_joints
    if not skinned_objects:
        skinned_objects = [xform for xform in selected_transforms if xform not in selected_joints]
    if not skinned_objects or not influences_to_unbind:
        return False
    skinned_objects = helpers.force_list(skinned_objects)
    influences_to_unbind = helpers.force_list(influences_to_unbind)
    influences_to_unbind_short = [dcc.node_short_name(joint_node) for joint_node in influences_to_unbind]

    skin_clusters = list()
    skin_percentage = 100.0 / len(skinned_objects)
    progress_value = 0.0

    for skin_index, skin_object in enumerate(skinned_objects):
        skin_cluster_name = find_related_skin_cluster(skin_object)
        if not skin_cluster_name:
            continue
        joints_attached = maya.cmds.skinCluster(skin_cluster_name, query=True, inf=True)

        if not use_parent:
            for joint_to_remove in influences_to_unbind_short:
                if joint_to_remove in joints_attached:
                    joints_attached.remove(joint_to_remove)

        source_positions = list()
        source_joints = list()
        for joint_attached in joints_attached:
            pos = maya.cmds.xform(joint_attached, query=True, worldSpace=True, t=True)
            source_positions.append(pos)
            source_joints.append([joint_attached, pos])

        source_kdtree = kdtree.KDTree.construct_from_data(source_positions)

        joint_percentage = skin_percentage / len(influences_to_unbind)
        for joint_index, jnt in enumerate(influences_to_unbind):
            jnt1 = jnt
            if use_parent:
                jnt2 = maya.cmds.listRelatives(jnt, parent=True)
                jnt2 = jnt2[0] if jnt2 else None
                if jnt2 is None:
                    remove_pos = maya.cmds.xform(jnt, query=True, worldSpace=True, t=True)
                    points = source_kdtree.query(query_point=remove_pos, t=1)
                    for index, position in enumerate(source_joints):
                        if position[1] != points[0]:
                            continue
                        jnt2 = position[0]
            else:
                remove_pos = maya.cmds.xform(jnt, query=True, worldSpace=True, t=True)
                points = source_kdtree.query(query_point=remove_pos, t=True)
                for index, position in enumerate(source_joints):
                    if position[1] != points[0]:
                        continue
                    jnt2 = position[0]

            move_skin_weights(jnt1, jnt2, skin_object)

            progress_value += ((joint_index + 1) * joint_percentage) + (skin_index * skin_percentage)

        skin_clusters.append(skin_cluster_name)

    for skin_cluster in skin_clusters:
        joints_attached = maya.cmds.skinCluster(skin_cluster, query=True, inf=True)
        for jnt in influences_to_unbind_short:
            if jnt not in joints_attached:
                continue
            maya.cmds.skinCluster(skin_cluster, edit=True, removeInfluence=jnt)

    if delete:
        for joint_to_remove in influences_to_unbind:
            child_joints = maya.cmds.listRelatives(joint_to_remove, children=True)
            parent = maya.cmds.listRelatives(joint_to_remove, parent=True)
            if not child_joints:
                continue
            if not parent:
                maya.cmds.parent(child_joints, world=True)
                continue
            maya.cmds.parent(child_joints, parent)
        maya.cmds.delete(influences_to_unbind)

    progress_value = 100.0

    return True


@decorators.undo
@decorators.repeat_static_command(__name__, skip_arguments=True)
def delete_influences(skinned_objects=None, influences_to_remove=None, fast=True):
    """
    Deletes given influences from given meshes and stores the unbind influences weights into other influences
    :param skinned_objects: list(str), meshes which joints need to be removed
    :param influences_to_remove: list(str), list of joints that need to be removed
    :param fast: list(str), bool, Whether to do the deletion using quick unbind method or not
    :return: bool
    """

    if fast:
        valid_deletion = unbind_influences_quick(
            skinned_objects=skinned_objects, influences_to_unbind=influences_to_remove, delete=True)
    else:
        valid_deletion = unbind_influences(
            skinned_objects=skinned_objects, influences_to_unbind=influences_to_remove, delete=True
        )

    return valid_deletion


@decorators.undo
@decorators.repeat_static_command(__name__, skip_arguments=True)
def delete_unused_influences(skinned_objects=None):
    """
    Deletes all unused influences of the given skinned meshes
    :param skinned_objects: list(str), lisf of skinned meshes to remove unused influences of
    :return: bool
    """

    skinned_objects = skinned_objects or dcc.selected_nodes()

    for i, mesh in enumerate(skinned_objects):
        skin_cluster_name = find_related_skin_cluster(mesh)
        if not skin_cluster_name:
            shape = maya.cmds.listRelatives(mesh, shapes=True) or None
            if shape:
                logger.warning(
                    'Impossible to delete unused influences because mesh "{}" '
                    'has no skin cluster attached to it!'.format(mesh))
            continue

        attached_joints = maya.cmds.skinCluster(skin_cluster_name, query=True, influence=True)
        weighted_joints = maya.cmds.skinCluster(skin_cluster_name, query=True, weightedInfluence=True)

        non_influenced = list()
        for attached in attached_joints:
            if attached in weighted_joints:
                continue
            non_influenced.append(attached)

        for joint in non_influenced:
            maya.cmds.skinCluster(skin_cluster_name, edit=True, removeInfluence=joint)

    return True


@decorators.undo
def combine_skinned_meshes(meshes=None):
    """
    Combine given meshes and keeps skin cluster weights information intact
    :param meshes: list(str), list of meshes to combine
    :return: bool
    """

    meshes = meshes or dcc.selected_nodes_of_type('transform')
    if not meshes:
        return False

    if dcc.version() < 2015:
        logger.warning('Combine Skinned meshes functionality is only available in Maya 2015 or higher')
        return False

    maya.cmds.polyUniteSkinned(meshes, ch=False, mergeUVSets=True)
    return True


@decorators.undo
def extract_skinned_selected_components(selected_components=None, **kwargs):
    """
    Extracts selected components as a new mesh but keeping all the skin cluster information
    If no skin cluster is found, only the mesh is extracted
    :param selected_components: list(str), list of components to extract
    """

    components = selected_components or dcc.selected_nodes(flatten=True)
    components = helpers.force_list(components)
    if not components:
        return False

    mesh = components[0]
    if '.' in mesh:
        mesh = mesh.split('.')[0]

    if kwargs.pop('auto_assign_labels', False):
        jnt_utils.auto_assign_labels_to_mesh_influences(
            mesh, input_left=kwargs.pop('left_side_label', None),
            input_right=kwargs.pop('right_side_label', None), check_labels=True)

    faces = mesh_utils.convert_to_faces(components)
    duplicated_mesh = maya.cmds.duplicate(mesh)[0]
    all_faces = mesh_utils.convert_to_faces(duplicated_mesh)

    new_selection = list()
    for face in faces:
        new_selection.append('{}.{}'.format(duplicated_mesh, face.split('.')[-1]))

    maya.cmds.delete(list(set(all_faces) ^ set(new_selection)))
    maya.cmds.delete(duplicated_mesh, ch=True)
    if find_related_skin_cluster(mesh):
        transfer_skinning(mesh, [duplicated_mesh], in_place=True)

    for xform in 'trs':
        for axis in 'xyz':
            dcc.unlock_attribute(duplicated_mesh, '{}{}'.format(xform, axis))

    dcc.select_node(duplicated_mesh)

    return duplicated_mesh


@decorators.undo
def hammer_vertices(vertices_to_hammer=None, return_as_list=True):
    """
    Hammer given vertices and returns a list with the ones that have been hammered
    :param vertices_to_hammer: list(str), list of vertices to hammer weights of
    :param return_as_list: bool
    :return: bool or list(str)
    """

    components = vertices_to_hammer or dcc.selected_nodes(flatten=True)
    components = helpers.force_list(components)
    if not components:
        return False

    maya.cmds.select(components)
    maya.mel.eval('weightHammerVerts;')

    if return_as_list:
        return mesh_utils.convert_to_vertices(components)

    return True


def get_skin_weights(skin_deformer, vertices_ids=None):
    """
    Get the skin weights of the given skinCluster deformer
    :param skin_deformer: str, name of a skin deformer
    :param vertices_ids:
    :return: dict<int, list<float>, returns a dictionary where the key is the influence id and the
    value is the list of weights of the influence
    """

    mobj = node_utils.get_mobject(skin_deformer)

    mf_skin = maya.api.OpenMayaAnim.MFnSkinCluster(mobj)

    weight_list_plug = mf_skin.findPlug('weightList', 0)
    weights_plug = mf_skin.findPlug('weights', 0)
    weight_list_attr = weight_list_plug.attribute()
    weights_attr = weights_plug.attribute()

    weights = dict()

    vertices_count = weight_list_plug.numElements()
    if not vertices_ids:
        vertices_ids = list(range(vertices_count))

    for vertex_id in vertices_ids:
        weights_plug.selectAncestorLogicalIndex(vertex_id, weight_list_attr)

        weight_influence_ids = weights_plug.getExistingArrayAttributeIndices()

        influence_plug = maya.api.OpenMaya.MPlug(weights_plug)
        for influence_id in weight_influence_ids:
            influence_plug.selectAncestorLogicalIndex(influence_id, weights_attr)
            if influence_id not in weights:
                weights[influence_id] = [0] * vertices_count

            try:
                value = influence_plug.asDouble()
                weights[influence_id][vertex_id] = value
            except KeyError:
                # Assumes a removed influence
                pass

    return weights


def get_skin_envelope(geo_obj):
    """
    Returns envelope value of the skinCluster in the given geometry object
    :param geo_obj: str, name of the geometry
    :return: float
    """

    skin_deformer = deformer.find_deformer_by_type(geo_obj, 'skinCluster')
    if skin_deformer:
        return maya.cmds.getAttr('{}.envelope'.format(skin_deformer))

    return None


def set_skin_envelope(geo_obj, envelope_value):
    """
    Sets the envelope value of teh skinCluster in the given geometry object
    :param geo_obj: str, name of the geometry
    :param envelope_value: float. envelope value
    """

    skin_deformer = deformer.find_deformer_by_type(geo_obj, 'skinCluster')
    if skin_deformer:
        return maya.cmds.setAttr('{}.envelope'.format(skin_deformer), envelope_value)


def get_skin_influence_weights(influence_name, skin_deformer):
    """
    Returns weights of the influence in the given skinCluster deformer
    :param influence_name: str, name of the influence
    :param skin_deformer: str, skinCluster deformer name
    :return: list<float>, influences values
    """

    influence_index = get_index_at_skin_influence(influence_name, skin_deformer)
    if influence_index is None:
        return

    weights_dict = get_skin_weights(skin_deformer)
    if influence_index in weights_dict:
        weights = weights_dict[influence_index]
    else:
        indices = attribute.indices('{}.weightList'.format(skin_deformer))
        index_count = len(indices)
        weights = [0] * index_count

    return weights


def get_index_at_skin_influence(influence, skin_deformer):
    """
    Given an influence name, find at what index it connects to the skinCluster
    This corresponds to the matrix attribute.
    For example, skin_deformer.matrix[0] is the connection of the first influence
    :param influence: str, name of an influence
    :param skin_deformer: str, name of a skinCluster affected by the influence
    :return: int, index of the influence
    """

    connections = maya.cmds.listConnections('{}.worldMatrix'.format(influence), p=True, s=True)
    if not connections:
        return

    good_connection = None
    for cnt in connections:
        if cnt.startswith(skin_deformer):
            good_connection = cnt
            break

    if good_connection is None:
        return

    search = name_utils.search_last_number(good_connection)
    found_string = search.group()

    index = None
    if found_string:
        index = int(found_string)

    return index


def get_skin_influence_at_index(index, skin_deformer):
    """
    Returns which influence connect to the skinCluster at the given index
    :param index: int, index of an influence
    :param skin_deformer: str, name of the skinCluster to check the index
    :return: str, name of the influence at the given index
    """

    influence_slot = '{}.matrix[{}]'.format(skin_deformer, index)
    connection = attribute.attribute_input(influence_slot)
    if connection:
        connection = connection.split('.')
        return connection[0]

    return None


def get_skin_influence_names(skin_deformer, short_name=False):
    """
    Returns the names of the connected influences in the given skinCluster
    :param skin_deformer: str, name of the skinCluster
    :param short_name: bool, Whether to return full name of the influence or not
    :return: list<str>
    """

    mobj = node_utils.get_mobject(skin_deformer)
    mf_skin = maya.api.OpenMayaAnim.MFnSkinCluster(mobj)
    influence_dag_paths = mf_skin.influenceObjects()

    influence_names = list()
    for i in range(len(influence_dag_paths)):
        if not short_name:
            influence_path_name = influence_dag_paths[i].fullPathName()
        else:
            influence_path_name = influence_dag_paths[i].partialPathName()
        influence_names.append(influence_path_name)

    return influence_names


def get_skin_influence_indices(skin_deformer):
    """
    Returns the indices of the connected influences in the given skinCluster
    This corresponds to the matrix attribute.
    For example, skin_deformer.matrix[0] is the connection of the first influence
    :param skin_deformer: str, name of a skinCluster
    :return: list<int>, list of indices
    """

    mobj = node_utils.get_mobject(skin_deformer)
    mf_skin = maya.api.OpenMayaAnim.MFnSkinCluster(mobj)
    influence_dag_paths = mf_skin.influenceObjects()

    influence_ids = list()
    for i in range(len(influence_dag_paths)):
        influence_id = int(mf_skin.indexForInfluenceObject(influence_dag_paths[i]))
        influence_ids.append(influence_id)

    return influence_ids


def get_skin_influences(skin_deformer, short_name=True, return_dict=False):
    """
    Returns the influences connected to the skin cluster
    Returns a dictionary with the keys being the name of the influences being the value at the
    key index where the influence connects to the skinCluster
    :param skin_deformer: str, name of a skinCluster
    :param short_name: bool, Whether to return full name of the influence or not
    :param return_dict: bool, Whether to return a dictionary or not
    :return: variant<dict, list>
    """

    mobj = node_utils.get_mobject(skin_deformer)
    mf_skin = maya.api.OpenMayaAnim.MFnSkinCluster(mobj)

    influence_dag_paths = mf_skin.influenceObjects()
    total_paths = len(influence_dag_paths)

    influence_ids = dict()
    influence_names = list()
    for i in range(total_paths):
        influence_path = influence_dag_paths[i]
        if not short_name:
            influence_path_name = influence_dag_paths[i].fullPathName()
        else:
            influence_path_name = influence_dag_paths[i].partialPathName()
        influence_id = int(mf_skin.indexForInfluenceObject(influence_path))
        influence_ids[influence_path_name] = influence_id
        influence_names.append(influence_path_name)

    if return_dict:
        return influence_ids
    else:
        return influence_names


def get_non_zero_influences(skin_deformer):
    """
    Returns influences that have non zero weights in the skinCluster
    :param skin_deformer: str, name of a skinCluster deformer
    :return: list<str>, list of influences found in the skinCluster that have influence
    """

    influences = maya.cmds.skinCluster(skin_deformer, query=True, weightedInfluence=True)

    return influences


def add_missing_influences(skin_deformer1, skin_deformer2):
    """
    Make sure used influences in skin1 are added to skin2
    :param skin_deformer1: str, name of skinCluster
    :param skin_deformer2: str, name of skinCluster
    """

    influences1 = get_non_zero_influences(skin_deformer1)
    influences2 = get_non_zero_influences(skin_deformer2)

    for influence1 in influences1:
        if influence1 not in influences2:
            maya.cmds.skinCluster(skin_deformer2, edit=True, addInfluence=True, weight=0.0, normalizeWeights=1)


def get_skin_blend_weights(skin_deformer):
    """
    Returns the blendWeight values on the given skinCluster
    :param skin_deformer: str, name of a skinCluster deformer
    :return: list<float>, blend weight values corresponding to point order
    """

    indices = attribute.indices('{}.weightList'.format(skin_deformer))
    blend_weights = attribute.indices('{}.blendWeights'.format(skin_deformer))
    blend_weights_dict = dict()

    if blend_weights:
        for blend_weight in blend_weights:
            blend_weights_dict[blend_weight] = maya.cmds.getAttr(
                '{}.blendWeights[{}]'.format(skin_deformer, blend_weight))

    values = list()
    for i in range(len(indices)):
        if i in blend_weights_dict:
            value = blend_weights_dict[i]
            if type(value) < 0.000001:
                value = 0.0
            if isinstance(value, float):
                value = 0.0
            if value != value:
                value = 0.0

            values.append(value)
            continue
        else:
            values.append(0.0)
            continue

    return values


def set_skin_blend_weights(skin_deformer, weights):
    """
    Sets the blendWeights on the skinCluster given a list of weights
    :param skin_deformer: str, name of a skinCluster deformer
    :param weights: list<float>, list of weight values corresponding to point order
    """

    indices = attribute.indices('{}.weightList'.format(skin_deformer))

    new_weights = list()
    for weight in weights:
        if weight != weight:
            weight = 0.0
        new_weights.append(weight)

    for i in range(len(indices)):
        if maya.cmds.objExists('{}.blendWeights[{}]'.format(skin_deformer, i)):
            try:
                maya.cmds.setAttr('{}.blendWeights[{}]'.format(skin_deformer, i), weights[i])
            except Exception:
                pass


def set_skin_weights_to_zero(skin_deformer):
    """
    Sets all the weights on the given skinCluster to zero
    :param skin_deformer: str, name of a skinCluster deformer
    """

    weights = maya.cmds.ls('{}.weightList[*]'.format(skin_deformer))
    for weight in weights:
        weight_attrs = maya.cmds.listAttr('{}.weights'.format(weight), multi=True)
        if not weight_attrs:
            continue
        for weight_attr in weight_attrs:
            attr = '{}.{}'.format(skin_deformer, weight_attr)
            maya.cmds.setAttr(attr, 0)


@decorators.undo_chunk
def skin_mesh_from_mesh(source_mesh, target_mesh, exclude_joints=None, include_joints=None, uv_space=False):
    """
    Skins a mesh based on the skinning of another mesh
    Source mesh must be skinned and the target mesh will be skinned with the joints in the source mesh
    The skinning from the source mesh will be projected onto the target mesh
    :param source_mesh: str, name of a mesh
    :param target_mesh: str, name of a mesh
    :param exclude_joints: list<str>, exclude the named joint from the skinCluster
    :param include_joints: list<str>, include the named joints from the skinCluster
    :param uv_space: bool, Whether to copy the skin weights in UV space rather than point space
    """

    logger.debug('Skinning {} using weights from {}'.format(target_mesh, source_mesh))

    skin = deformer.find_deformer_by_type(source_mesh, 'skinCluster')
    if not skin:
        logger.warning('{} has no skin. No skinning to copy!'.format(source_mesh))
        return

    target_skin = deformer.find_deformer_by_type(target_mesh, 'skinCluster')
    if target_skin:
        logger.warning('{} already has a skinCluster. Deleting existing one ...'.format(target_mesh))
        maya.cmds.delete(target_skin)
        target_skin = None

    influences = get_non_zero_influences(skin)

    if exclude_joints:
        for exclude in exclude_joints:
            if exclude in influences:
                influences.remove(exclude)
    if include_joints:
        found = list()
        for include in include_joints:
            if include in influences:
                found.append(include)
        influences = found

    # TODO: skinCluster should be renamed using NameIt lib
    if target_skin:
        if uv_space:
            maya.cmds.copySkinWeights(
                sourceSkin=skin,
                destinationSkin=target_skin,
                noMirror=True,
                surfaceAssociation='closestPoint',
                influenceAssociation=['name'],
                uvSpace=['map1', 'map1'],
                normalize=True
            )
        else:
            maya.cmds.copySkinWeights(
                sourceSkin=skin,
                destinationSkin=target_skin,
                noMirror=True,
                surfaceAssociation='closestPoint',
                influenceAssociation=['name'],
                normalize=True
            )
        skinned = maya.cmds.skinCluster(target_skin, query=True, weightedInfluence=True)
        unskinned = set(influences) ^ set(skinned)
        for jnt in unskinned:
            maya.cmds.skinCluster(target_skin, edit=True, removeInfluence=jnt)
    else:
        skin_name = name_utils.get_basename(target_mesh)
        target_skin = maya.cmds.skinCluster(
            influences, target_mesh, tsb=True, n=name_utils.find_unique_name('skin_{}'.format(skin_name)))[0]

    return target_skin
