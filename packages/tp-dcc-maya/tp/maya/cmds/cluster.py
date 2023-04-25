#!#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with Maya clusters
"""

import maya.cmds

from tp.core import log
from tp.common.math import vec3
from tp.maya.cmds import name as name_lib, shape as shape_utils

LOGGER = log.tpLogger


class ClusterObject(object):
    """
    Util class for clustering objects
    """

    def __init__(self, geometry, name):
        super(ClusterObject, self).__init__()

        self._geo = geometry
        self._join_ends = False
        self._name = name
        self._cvs = list()
        self._cv_count = 0
        self._clusters = list()
        self._handles = list()

    def create(self):
        """
        Creates the clusters
        """

        self._create()

    def get_cluster_list(self):
        """
        Returns the names of cluster deformers
        :return: list<str>
        """

        return self._clusters

    def get_cluster_handle_list(self):
        """
        Returns the name of cluster handles
        :return: list<str>
        """

        return self._handles

    def _create(self):
        """
        Internal function that creates the custer
        Override in child classes
        """

        return

    def _create_cluster(self, cvs):
        return create_cluster(cvs, self._name)


class ClusterSurface(ClusterObject, object):
    """
    Util class for clustering a surface
    """

    def __init__(self, geometry, name):
        super(ClusterSurface, self).__init__(geometry, name)

        self._join_ends = False
        self._join_both_ends = False
        self._first_cluster_pivot_at_start = True
        self._last_cluster_pivot_at_end = True
        self._maya_type = None

        if shape_utils.has_shape_of_type(self._geo, 'nurbsCurve'):
            self._maya_type = 'nurbsCurve'
        elif shape_utils.has_shape_of_type(self._geo, 'nurbsSurface'):
            self._maya_type = 'nurbsSurface'

        self._cluster_u = True

    def _create(self):
        self._cvs = maya.cmds.ls('{}.cv[*]'.format(self._geo, flatten=True))
        if self._maya_type == 'nurbsCurve':
            self._cv_count = len(self._cvs)
        elif self._maya_type == 'nurbsSurface':
            if self._cluster_u:
                index = '[0][*]'
            else:
                index = '[*][0]'

            self._cv_count = len(maya.cmds.ls('{}.cv{}'.format(self._geo, index), flatten=True))

        start_index = 0
        cv_count = self._cv_count
        if self._join_ends:
            if self._join_both_ends:
                self._create_start_and_end_joined_cluster()
            else:
                last_cluster, last_handle = self._create_start_and_end_clusters()
            cv_count = len(self._cvs[2:self._cv_count])
            start_index = 2

        for i in range(start_index, cv_count):
            if self._maya_type == 'nurbsCurve':
                cv = '{}.cv[{}]'.format(self._geo, i)
            elif self._maya_type == 'nurbsSurface':
                if self._cluster_u:
                    index = '[*][{}]'.format(i)
                else:
                    index = '[{}][*]'.format(i)
                cv = '{}.cv{}'.format(self._geo, index)
            else:
                LOGGER.warning('Given NURBS Maya type "{}" is not valid!'.format(self._maya_type))
                return

            cluster, handle = self._create_cluster(cv)
            self._clusters.append(cluster)
            self._handles.append(handle)

        if self._join_ends and not self._join_both_ends:
            self._clusters.append(last_cluster)
            self._handles.append(last_handle)

        return self._clusters

    def set_join_ends(self, flag):
        """
        Sets whether clusters on the end of the surface take up 2 CVs or 1 CV
        :param flag: bool
        """

        self._join_ends = flag

    def set_join_both_ends(self, flag):
        """
        Sets whether clusters on the ends of the surface are joined together or not
        :param flag: bool
        """

        self._join_both_ends = flag

    def set_last_cluster_pivot_at_end(self, flag):
        """
        Sets whether move the last cluster pivot to the end of the curve
        :param flag: bool
        """

        self._last_cluster_pivot_at_end = flag

    def set_first_cluster_pivot_at_start(self, flag):
        """
        Sets whether move the first cluster pivot to the start of the curve
        :param flag: bool
        """

        self._first_cluster_pivot_at_start = flag

    def set_cluster_u(self, flag):
        """
        Sets whether cluster u should be used
        :param flag: bool
        """

        self._cluster_u = flag

    def _create_start_and_end_clusters(self):
        """
        Internal function used to create start and end clusters
        """

        start_cvs = None
        end_cvs = None
        start_pos = None
        end_pos = None

        if self._maya_type == 'nurbsCurve':
            start_cvs = '{}.cv[0:1]'.format(self._geo)
            end_cvs = '{}.cv[{}:{}]'.format(self._geo, self._cv_count - 2, self._cv_count - 1)
            start_pos = maya.cmds.xform('{}.cv[0]'.format(self._geo), q=True, ws=True, t=True)
            end_pos = maya.cmds.xform('{}.cv[{}]'.format(self._geo, self._cv_count - 1), q=True, ws=True, t=True)
        elif self._maya_type == 'nurbsSurface':
            if self._cluster_u:
                cv_count_u = len(maya.cmds.ls('{}.cv[*][0]'.format(self._geo), flatten=True))
                index1 = '[0:*][0:1]'
                index2 = '[0:*][{}:{}]'.format(self._cv_count - 2, self._cv_count - 1)
                index3 = '[{}][0]'.format(cv_count_u - 1)
                index4 = '[0][{}]'.format(self._cv_count - 1)
                index5 = '[{}][{}]'.format(cv_count_u, self._cv_count - 1)
            else:
                cv_count_v = len(maya.cmds.ls('%s.cv[0][*]' % self._geo, flatten=True))
                index1 = '[0:1][0:*]'
                index2 = '[{}:{}][0:*]'.format(self._cv_count - 2, self._cv_count - 1)
                index3 = '[0][{}]'.format(cv_count_v - 1)
                index4 = '[{}][0]'.format(self._cv_count - 1)
                index5 = '[{}][{}]'.format(self._cv_count - 1, cv_count_v)

            start_cvs = '{}.cv{}'.format(self._geo, index1)
            end_cvs = '{}.cv{}'.format(self._geo, index2)

            p1 = maya.cmds.xform('{}.cv[0][0]'.format(self._geo), q=True, ws=True, t=True)
            p2 = maya.cmds.xform('{}.cv{}'.format(self._geo, index3), q=True, ws=True, t=True)
            start_pos = vec3.get_mid_point(p1, p2)

            p1 = maya.cmds.xform('{}.cv{}'.format(self._geo, index4), q=True, ws=True, t=True)
            p2 = maya.cmds.xform('{}.cv{}'.format(self._geo, index5), q=True, ws=True, t=True)
            end_pos = vec3.get_mid_point(p1, p2)

        cluster, handle = self._create_cluster(start_cvs)

        self._clusters.append(cluster)
        self._handles.append(handle)

        if self._first_cluster_pivot_at_start:
            maya.cmds.xform(handle, ws=True, rp=start_pos, sp=start_pos)

        last_cluster, last_handle = self._create_cluster(end_cvs)
        if self._last_cluster_pivot_at_end:
            maya.cmds.xform(last_handle, ws=True, rp=end_pos, sp=end_pos)

        return last_cluster, last_handle

    def _create_start_and_end_joined_cluster(self):
        start_cvs = None
        end_cvs = None

        if self._maya_type == 'nurbsCurve':
            start_cvs = '{}.cv[0:1]'.format(self._geo)
            end_cvs = '{}.cv[{}:{}]'.format(self._geo, self._cv_count - 2, self._cv_count - 1)
        elif self._maya_type == 'nurbsSurface':
            if self._cluster_u:
                index_1 = '[0:*][0]'
                index_2 = '[0:*][{}]'.format(self._cv_count - 1)
            else:
                index_1 = '[0][0:*}'
                index_2 = '[{}][0:*]'.format(self._cv_count - 1)

            start_cvs = '{}.cv{}'.format(self._geo, index_1)
            end_cvs = '{}.cv{}'.format(self._geo, index_2)

        maya.cmds.select([start_cvs, end_cvs])
        cvs = maya.cmds.ls(sl=True)

        cluster, handle = self._create_cluster(cvs)
        self._clusters.append(cluster)
        self._handles.append(handle)


class ClusterCurve(ClusterSurface, object):
    """
    Util class for clustering a curve
    """

    def _create(self):
        self._cvs = maya.cmds.ls('{}.cv[*]'.format(self._geo), flatten=True)
        self._cv_count = len(self._cvs)
        start_index = 0
        cv_count = self._cv_count

        if self._join_ends:
            last_cluster, last_handle = self._create_start_and_end_clusters()
            cv_count = len(self._cvs[2:self._cv_count])
            start_index = 2

        for i in range(start_index, cv_count):
            cluster, handle = self._create_cluster('{}.cv[{}]'.format(self._geo, i))
            self._clusters.append(cluster)
            self._handles.append(handle)

        if self._join_ends:
            self._clusters.append(last_cluster)
            self._handles.append(last_handle)

        return self._clusters

    def _create_start_and_end_clusters(self):
        cluster, handle = self._create_cluster('{}.cv[0:1]'.format(self._geo))

        self._clusters.append(cluster)
        self._handles.append(handle)

        pos = maya.cmds.xform('{}.cv[0]'.format(self._geo), q=True, ws=True, t=True)
        maya.cmds.xform(handle, ws=True, rp=pos, sp=pos)

        last_cluster, last_handle = self._create_cluster(
            '{}.cv[{}:{}]'.format(self._geo, self._cv_count - 2, self._cv_count - 1))
        pos = maya.cmds.xform('{}.cv[{}]'.format(self._geo, self._cv_count - 1), q=True, ws=True, t=True)
        maya.cmds.xform(last_handle, ws=True, rp=pos, sp=pos)

        return last_cluster, last_handle

    def set_cluster_u(self, flag):
        """
        Override because cluster u is not available on curves
        :param flag: bool
        """

        LOGGER.warning('Cannot set cluster U, there is only one direction for spans on a curve.')


def create_cluster(points, name, relative=False, front_of_chain=True, exclusive=False):
    """
    Creates a cluster on the given points
    :param points: list<str>, names of points to cluster
    :param name: str, name of the cluster
    :param relative: bool, sets whether or not cluster is created in relative mode. In this mode, only the
        transformations directly above the cluster are used by the cluster.
    :param front_of_chain: bool
    :param exclusive: bool, Whether or not cluster deformation set is put in a deform partition. If True, a vertex/CV
        only will be able to be deformed by one cluster.
    :return: list(str, str), [cluster, handle]
    """

    # NOTE: Bug detected in Maya 2019. If we pass exclusive argument, no matter if we pass True of False, exclusivity
    # will be enabled
    if exclusive:
        cluster, handle = maya.cmds.cluster(
            points, n=name_lib.find_unique_name(name), relative=relative, frontOfChain=front_of_chain, exclusive=True)
    else:
        cluster, handle = maya.cmds.cluster(

            points, n=name_lib.find_unique_name(name), relative=relative, frontOfChain=front_of_chain)
    return cluster, handle
