#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Implementation of an octree data structure
"""

from tp.common.math import bbox


class Octree(object):
    """
    An octree data structure partitions 3D space into octants
    """

    def __init__(self, bbox_min, bbox_max):
        """
        Constructor
        :param bbox_min: tuple, contains the minimum X,Y,Z values of the mesh bounding box
        :param bbox_max: tuple, contains the maximum X,Y,Z values of the mesh bounding box
        """

        self._bbox_min = bbox_min
        self._bbox_max = bbox_max
        self._root = OctreeNode(self._bbox_min, self._bbox_max, divisions=0, parent=self)

    @property
    def root(self):
        return self._root


class OctreeNode(object):
    """
    Octant representation
    """

    def __init__(self, bbox_min, bbox_max, divisions=0, parent=None):
        """
        Constructor
        :param bbox_min: tuple, contains the minimum X,Y,Z values of the mesh bounding box
        :param bbox_max: tuple, contains the maximum X,Y,Z values of the mesh bounding box
        :param divisions: int, division level of this octant node (ejp: this node is 2**divisions times smaller than
                               than the original Octree bounding box size
        :param parent: Octree, octree parent for this node
        """

        self._bbox_min = bbox_min
        self._bbox_max = bbox_max
        self._parent = parent
        self._divisions = divisions
        self._children = list()
        self._half_values = bbox.bounding_box_half_values(bbox_min=bbox_min, bbox_max=bbox_max)

    def get_divisions(self):
        return self._divisions

    def get_children(self):
        return self._children

    def get_half_values(self):
        return self._half_values

    divisions = property(get_divisions)
    children = property(get_children)
    half_values = property(get_half_values)

    def child_containing(self, point):
        """
        Returns the child node containing the given point
        :param point: tuple(X, Y, Z), tuple containing (X,Y,Z) positions of a point
        :return: OctreeNode
        """

        x, y, z = point
        half_x, half_y, half_z = self._half_values

        # Get octant the point is in
        greater_half_x = int(x >= half_x)
        greater_half_y = int(y >= half_y)
        greater_half_z = int(z >= half_z)

        child_index = 4 * greater_half_z + 2 * greater_half_y + greater_half_x
        return self._children[child_index]

    def is_inside(self, point):
        """
        Returns True if the given points lies inside this OctreeNode, False otherwise
        :param point: tuple(X, Y, Z), tuple containing (X,Y,Z) positions of a point
        :return: bool
        """

        x, y, z = point

        in_x = self._bbox_min[0] <= x < self._bbox_max[0]
        in_y = self._bbox_min[1] <= y < self._bbox_max[1]
        in_z = self._bbox_min[2] <= z < self._bbox_max[2]

        return all(in_x, in_y, in_z)

    def subdivide(self):
        """
        Divides an OctreeNode into 8 octants. The subdivided node replaced in node list by the octants
        :return: OctreeNode, octree node we want to divide
        """

        octant_list = list()
        divs = self._divisions + 1
        min_x, min_y, min_z = self._bbox_min
        max_x, max_y, max_z = self._bbox_max
        half_x, half_y, half_z = self._half_values

        oct_0_min = self._bbox_min  # 000
        oct_0_max = (half_x, half_y, half_z)
        octant_list.append(OctreeNode(oct_0_min, oct_0_max, divisions=divs, parent=self))

        oct_1_min = (half_x, min_y, min_z)  # 001
        oct_1_max = (max_x, half_y, half_z)
        octant_list.append(OctreeNode(oct_1_min, oct_1_max, divisions=divs, parent=self))

        oct_2_min = (min_x, half_y, min_z)  # 010
        oct_2_max = (half_x, max_y, half_z)
        octant_list.append(OctreeNode(oct_2_min, oct_2_max, divisions=divs, parent=self))

        oct_3_min = (half_x, half_y, min_z)  # 011
        oct_3_max = (max_x, max_y, half_z)
        octant_list.append(OctreeNode(oct_3_min, oct_3_max, divisions=divs, parent=self))

        oct_4_min = (min_x, min_y, half_z)  # 100
        oct_4_max = (half_x, half_y, max_z)
        octant_list.append(OctreeNode(oct_4_min, oct_4_max, divisions=divs, parent=self))

        oct_5_min = (half_x, min_y, half_z)  # 101
        oct_5_max = (max_x, half_y, max_z)
        octant_list.append(OctreeNode(oct_5_min, oct_5_max, divisions=divs, parent=self))

        oct_6_min = (min_x, half_y, half_z)  # 110
        oct_6_max = (half_x, max_y, max_z)
        octant_list.append(OctreeNode(oct_6_min, oct_6_max, divisions=divs, parent=self))

        oct_7_min = (half_x, half_y, half_z)  # 111
        oct_7_max = self._bbox_max
        octant_list.append(OctreeNode(oct_7_min, oct_7_max, divisions=divs, parent=self))

        # Remove the original node and add the octants
        self._children = octant_list
