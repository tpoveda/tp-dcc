#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with curve nodes
"""

from copy import copy
from collections import OrderedDict

from pymxs import runtime as rt

from tp.max.core import transform, node as node_utils


class CurveCV(list):
    """
    Base class used to represent curve CVs
    """

    def ControlVWrapper(self):
        def wrapper(*args, **kwargs):
            f = self(*[a if isinstance(a, CurveCV) else CurveCV([a, a, a]) for a in args], **kwargs)
            return f
        return wrapper

    @ControlVWrapper
    def __mul__(self, other):
        return CurveCV([self[i] * other[i] for i in range(3)])

    @ControlVWrapper
    def __sub__(self, other):
        return CurveCV([self[i] - other[i] for i in range(3)])

    @ControlVWrapper
    def __add__(self, other):
        return CurveCV([self[i] + other[i] for i in range(3)])

    def __imul__(self, other):
        return self * other

    def __rmul__(self, other):
        return self * other

    def __isub__(self, other):
        return self - other

    def __rsub__(self, other):
        return self - other

    def __iadd__(self, other):
        return self + other

    def __radd__(self, other):
        return self + other

    @staticmethod
    def mirror_vector():
        return {
            None: CurveCV([1, 1, 1]),
            'None': CurveCV([1, 1, 1]),
            'XY': CurveCV([1, 1, -1]),
            'YZ': CurveCV([-1, 1, 1]),
            'ZX': CurveCV([1, -1, 1])
        }

    def reorder(self, order):
        """
        With a given order sequence CVs will be reordered (for axis order purposes)
        :param order: list(int)
        """

        return CurveCV([self[i] for i in order])


def create_curve_shape(
        curve_data, curve_size=1.0, translate_offset=(0.0, 0.0, 0.0),
        scale=(1.0, 1.0, 1.0), axis_order='XYZ', color=None, mirror=None):
    """
    Creates a NURBS curve based on the given curve data
    :param curve_data: dict, data, {"shapeName": {"cvs": [], "knots":[], "degree": int, "form": int, "matrix": []}}
    will be created
    :return: tuple(MObject, list(MObject)), tuple containing the parent MObject and the list of MObject shapes
    """

    translate_offset = CurveCV(translate_offset)
    scale = CurveCV(scale)
    order = [{'X': 0, 'Y': 1, 'Z': 2}[x] for x in axis_order]

    curves_to_create = OrderedDict()
    for shape_name, shape_data in curve_data.items():
        curves_to_create[shape_name] = list()
        shape_parent = shape_data.get('shape_parent', None)
        if shape_parent:
            if shape_parent in curves_to_create:
                curves_to_create[shape_parent].append(shape_name)

    created_curves = list()

    nurbs_set = rt.NURBSSet()
    for shape_name, shape_children in curves_to_create.items():
        if shape_name not in created_curves:
            _, new_shapes = _create_curve(shape_name, curve_data[shape_name], curve_size, translate_offset, scale,
                                          order, mirror, nurbs_set=nurbs_set)
    n = rt.NURBSNode(nurbs_set, name='nurbs01')

    # TODO: Here we need to support both colors between 1.0 and 255, this is hacky way. Find a better solution.
    if color:
        if all(i > 1.0 for i in color):
            n.wirecolor = rt.Color(*color)
        else:
            color = [i * 255 for i in color]
            n.wirecolor = rt.Color(*color)

    return n


def _create_curve(
        shape_name, shape_data, curve_size, translate_offset, scale, order, mirror, nurbs_set=None):

    nurbs_set = nurbs_set or rt.NURBSSet()
    new_shapes = list()

    curve_cvs = shape_data['cvs']
    degree = shape_data['degree']
    curve_order = degree + 1
    total_knots = curve_order + len(curve_cvs)

    transformed_cvs = list()
    cvs = [CurveCV(pt) for pt in copy(curve_cvs)]
    for i, cv in enumerate(cvs):
        cv *= curve_size * scale.reorder(order)
        cv += translate_offset.reorder(order)
        cv *= CurveCV.mirror_vector()[mirror]
        cv = cv.reorder(order)
        transformed_cvs.append(cv)

    knots = shape_data.get('knots', None)
    if not knots:
        # TODO: Check is this is valid
        knots = tuple([float(i) for i in range(total_knots)])

    curve = rt.NURBSCVCurve(name=shape_name, order=curve_order, numCVs=len(cvs), numKnots=len(knots))
    for i, knot in enumerate(knots):
        rt.setKnot(curve, i + 1, knot)
    for i, cv in enumerate(cvs):
        new_cv = rt.NURBSControlVertex(rt.Point3(*cv))
        rt.setCV(curve, i + 1, new_cv)
    rt.appendObject(nurbs_set, curve)
    new_shapes.append(curve)

    return nurbs_set, new_shapes


def add_shape(curve_spline1, curve_spline2):
    """
    Combines given two curve splines
    :param curve_spline1:
    :param curve_spline2:
    :return:
    """

    curve_spline1 = node_utils.get_pymxs_node(curve_spline1)
    curve_spline2 = node_utils.get_pymxs_node(curve_spline2)

    if not curve_spline1 or not curve_spline2:
        return
    if not rt.isKindOf(curve_spline1, rt.SplineShape) or not rt.isKindOf(curve_spline2, rt.SplineShape):
        return
    rt.convertToSplineShape(curve_spline1)
    rt.convertToSplineShape(curve_spline2)
    rt.addAndWeld(curve_spline1, curve_spline2, -1)

    return curve_spline1


def draw_line_between_two_points(point_a, point_b):
    """
    Draws a spline curve where point_a is its starting point and point_b its end point
    :param point_a: list(float, float, float) or rt.Point3
    :param point_b: list(float, float, float) or rt.Point3
    :return: str, name of the new spline
    """

    if rt.classOf(point_a) != rt.Point3:
        point_a = rt.Point3(*point_a)
    if rt.classOf(point_b) != rt.Point3:
        point_b = rt.Point3(*point_b)

    spline = rt.SplineShape(pos=point_a)
    rt.addNewSpline(spline)
    rt.addKnot(spline, 1, rt.Name('corner'), rt.Name('line'), point_a)
    rt.addKnot(spline, 1, rt.Name('corner'), rt.Name('line'), point_b)
    rt.updateShape(spline)

    return spline


def draw_line_between_three_points(point_a, point_b, point_c):
    """
    Draws a spline curve where point_a is its starting point and point_b its end point and point_c its mid point
    :param point_a: list(float, float, float) or rt.Point3
    :param point_b: list(float, float, float) or rt.Point3
    :param point_c: list(float, float, float) or rt.Point3
    :return: str, name of the new spline
    """

    if rt.classOf(point_a) != rt.Point3:
        point_a = rt.Point3(*point_a)
    if rt.classOf(point_b) != rt.Point3:
        point_b = rt.Point3(*point_b)
    if rt.classOf(point_c) != rt.Point3:
        point_c = rt.Point3(*point_c)

    spline = rt.SplineShape(pos=point_a)
    rt.addNewSpline(spline)
    rt.addKnot(spline, 1, rt.Name('corner'), rt.Name('line'), point_a)
    rt.addKnot(spline, 1, rt.Name('corner'), rt.Name('line'), point_b)
    rt.addKnot(spline, 1, rt.Name('corner'), rt.Name('line'), point_c)
    rt.updateShape(spline)

    return spline


def create_circle_control(name, init_pos=None, radius=10, color=None, axis='z'):
    """
    Creates a circle control
    :param name: str
    :param init_pos: list(float, float, float) or None
    :param radius: float
    :param color: list(float, float, float) or rt.Point3
    :param axis: str
    """

    pos = init_pos or [0, 0, 0]
    if rt.classOf(pos) != rt.Point3:
        pos = rt.Point3(*pos)
    if color and rt.classOf(color) != rt.color:
        color = rt.color(*color)
    if not color:
        color = rt.yellow

    rt.setCommandPanelTaskMode(rt.Name('modify'))
    ctrl_name = rt.uniquename(name)
    base_circle = rt.circle(name=ctrl_name, radius=radius, steps=6, pos=pos)
    if str(axis).lower() == 'x':
        xform_mod = rt.xform()
        rt.addModifier(base_circle, xform_mod)
        rt.setProperty(xform_mod.gizmo, 'rotation', rt.eulerAngles(0, 90, 0))
    elif str(axis).lower() == 'y':
        xform_mod = rt.xform()
        rt.addModifier(base_circle, xform_mod)
        rt.setProperty(xform_mod.gizmo, 'rotation', rt.eulerAngles(90, 0, 0))
    base_circle.wirecolor = color
    rt.convertTo(base_circle, rt.SplineShape)

    return base_circle


def create_rectangle_control(name, init_pos=None, length=10.0, width=10.0, corner_radius=0.0, color=None, axis='z'):
    """
    Creates a rectangle control
    :param name: str
    :param init_pos:
    :param length:
    :param width:
    :param corner_radius:
    :param color:
    :param axis:
    :return:
    """

    pos = init_pos or [0, 0, 0]
    if rt.classOf(pos) != rt.Point3:
        pos = rt.Point3(*pos)
    if color and rt.classOf(color) != rt.color:
        color = rt.color(*color)
    if not color:
        color = rt.yellow

    rt.setCommandPanelTaskMode(rt.Name('modify'))
    ctrl_name = rt.uniquename(name)
    base_rectangle = rt.rectangle(name=ctrl_name, length=length, width=width, cornerRadius=corner_radius, pos=pos)
    base_rectangle.wirecolor = color
    if str(axis).lower() == 'x':
        xform_mod = rt.xform()
        rt.addModifier(base_rectangle, xform_mod)
        rt.setProperty(xform_mod.gizmo, 'rotation', rt.eulerAngles(0, 90, 0))
    elif str(axis).lower() == 'y':
        xform_mod = rt.xform()
        rt.addModifier(base_rectangle, xform_mod)
        rt.setProperty(xform_mod.gizmo, 'rotation', rt.eulerAngles(90, 0, 0))
    rt.convertTo(base_rectangle, rt.SplineShape)

    return base_rectangle


def create_gizmo_control(name, init_pos=None, radius=10, color=None):
    """
    Creates a gizmo control
    :param name: str
    :param init_pos:
    :param radius:
    :param color:
    :return:
    """

    pos = init_pos or [0, 0, 0]
    if rt.classOf(pos) != rt.Point3:
        pos = rt.Point3(*pos)
    if color and rt.classOf(color) != rt.color:
        color = rt.color(*color)
    if not color:
        color = rt.yellow

    circle_a = create_circle_control(name=name, radius=radius, color=color, init_pos=pos, axis='x')
    circle_b = create_circle_control(name=name, radius=radius, color=color, init_pos=pos, axis='y')
    circle_c = create_circle_control(name=name, radius=radius, color=color, init_pos=pos, axis='z')
    gizmo_ctrl = add_shape(circle_a, circle_b)
    gizmo_ctrl = add_shape(gizmo_ctrl, circle_c)

    return gizmo_ctrl


def create_box_control(name, init_pos=None, length=10, width=10, height=10, color=None):
    """
    Creates a box control
    :param name: str
    :param init_pos:
    :param length:
    :param width:
    :param height:
    :param color:
    :return:
    """

    pos = init_pos or [0, 0, 0]
    if rt.classOf(pos) != rt.Point3:
        pos = rt.Point3(*pos)
    if color and rt.classOf(color) != rt.color:
        color = rt.color(*color)
    if not color:
        color = rt.yellow

    rt.setCommandPanelTaskMode(rt.Name('modify'))
    base_box = rt.Box(
        lengthsegs=1, widthsegs=1, heightsegs=1, length=length, width=width, height=height,
        mapcoords=True, pos=pos, isSelected=True)
    rt.select(base_box)
    rt.convertTo(base_box, rt.PolyMeshObject)
    rt.subobjectLevel = 2
    edge_bitarray = rt.BitArray()
    edge_indices = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    edge_bitarray.count = len(edge_indices)
    for i, index in enumerate(edge_indices):
        edge_bitarray[i] = index
    base_box.EditablePoly.SetSelection(rt.Name('Edge'), edge_bitarray)
    ctrl_name = rt.uniquename(name)
    base_box.EditablePoly.createShape(ctrl_name, False, base_box)
    rt.subobjectLevel = 0
    rt.delete(base_box)
    box_ctrl = rt.getNodeByName(ctrl_name)
    rt.convertTo(box_ctrl, rt.SplineShape)
    box_ctrl.wirecolor = color
    rt.CenterPivot(box_ctrl)
    transform.reset_xform_and_collapse(box_ctrl, freeze=True)

    return box_ctrl


def create_circle_with_triangle_control(name, init_pos=None, radius=10, corner_radius=0, color=None, axis='z'):
    """
    Creates a circle with a triangle inside control
    :param name: str
    :param init_pos:
    :param radius:
    :param corner_radius:
    :param color:
    :param axis:
    :return:
    """

    pos = init_pos or [0, 0, 0]
    if rt.classOf(pos) != rt.Point3:
        pos = rt.Point3(*pos)
    if color and rt.classOf(color) != rt.color:
        color = rt.color(*color)
    if not color:
        color = rt.yellow

    circle_ctrl = create_circle_control(name, init_pos=pos, radius=radius, color=color, axis=axis)
    triangle_ctrl = rt.Ngon(
        radius=radius, cornerRadius=corner_radius, nsides=3, circular=False, scribe=1, pos=pos, isSelected=True)
    xform_mod = rt.xform()
    rt.addModifier(triangle_ctrl, xform_mod)
    rt.setProperty(xform_mod.gizmo, 'rotation', rt.eulerAngles(0, 0, -90))
    if str(axis).lower() == 'x':
        xform_mod = rt.xform()
        rt.addModifier(triangle_ctrl, xform_mod)
        rt.setProperty(xform_mod.gizmo, 'rotation', rt.eulerAngles(0, -90, 0))
    elif str(axis).lower() == 'y':
        xform_mod = rt.xform()
        rt.addModifier(triangle_ctrl, xform_mod)
        rt.setProperty(xform_mod.gizmo, 'rotation', rt.eulerAngles(-90, 0, 0))

    final_ctrl = add_shape(circle_ctrl, triangle_ctrl)

    return final_ctrl
