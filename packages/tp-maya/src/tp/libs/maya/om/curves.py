from __future__ import annotations

import copy
from typing import Iterator

from maya import cmds
from maya.api import OpenMaya

from tp.libs.math import scalar

from . import factory, nodes, plugs, mathlib

SHAPE_INFO = {
    "cvs": (),
    "degree": 3,
    "form": 1,
    "knots": (),
    "matrix": (
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
    ),
    "outlinerColor": (0.0, 0.0, 0.0),
    "overrideColorRGB": (0.0, 0.0, 0.0),
    "overrideEnabled": False,
    "overrideRGBColors": False,
    "useOutlinerColor": False,
}


# noinspection PyCallingNonCallable,PyArgumentList
class CurveCV(list):
    """Base class used to represent curve CVs"""

    # noinspection PyPep8Naming
    def ControlVWrapper(self):
        def wrapper(*args, **kwargs):
            f = self(
                *[a if isinstance(a, CurveCV) else CurveCV([a, a, a]) for a in args],
                **kwargs,
            )
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
            "None": CurveCV([1, 1, 1]),
            "XY": CurveCV([1, 1, -1]),
            "YZ": CurveCV([-1, 1, 1]),
            "ZX": CurveCV([1, -1, 1]),
        }

    def reorder(self, order):
        """With a given order sequence CVs will be reordered (for axis order purposes)
        :param order: list(int)
        """

        return CurveCV([self[i] for i in order])


def get_curve_data(
    curve_shape: str | OpenMaya.MObject | OpenMaya.MDagPath,
    space: OpenMaya.MSpace | None = None,
    color_data: bool = True,
    normalize: bool = True,
    parent: str | OpenMaya.MObject | None = None,
) -> dict:
    """Return the curve data from the given shape node.

    Args:
        curve_shape: name or MObject that represents nurbs curve shape
        space: MSpace, coordinate space to query the point data
        color_data: whether to include curve data.
        normalize: whether to normalize curve data, so it fits in first
            Maya grid-quadrant.
        parent: optional parent for the curve.

    Returns:
        Curve data as a dictionary.
    """

    if isinstance(curve_shape, str):
        curve_shape = nodes.mobject(curve_shape)
    if parent and isinstance(parent, str):
        parent = nodes.mobject(parent)

    space = space or OpenMaya.MSpace.kObject
    shape = OpenMaya.MFnDagNode(curve_shape).getPath()
    data = nodes.node_color_data(shape.node()) if color_data else dict()
    curve = OpenMaya.MFnNurbsCurve(shape)
    if parent:
        parent = OpenMaya.MFnDagNode(parent).getPath().partialPathName()

    curve_cvs = map(tuple, curve.cvPositions(space))
    curve_cvs = [
        cv[:-1] for cv in curve_cvs
    ]  # OpenMaya returns 4 elements in the cvs, ignore last one

    if normalize:
        mx = -1
        for cv in curve_cvs:
            for p in cv:
                if mx < abs(p):
                    mx = abs(p)
        curve_cvs = [[p / mx for p in pt] for pt in curve_cvs]

    # noinspection PyTypeChecker
    data.update(
        {
            "knots": tuple(curve.knots()),
            "cvs": curve_cvs,
            "degree": int(curve.degree),
            "form": int(curve.form),
            "matrix": tuple(nodes.world_matrix(curve.object())),
            "shape_parent": parent,
        }
    )

    return data


def serialize_transform_curve(
    node: OpenMaya.MObject,
    space: OpenMaya.MSpace | None = None,
    color_data: bool = True,
    normalize: bool = True,
) -> dict:
    """Serializes given transform shapes curve data and returns a dictionary with that data.

    :param node: object that represents the transform above the nurbsCurve shapes we want to serialize.
    :param space: coordinate space to query the point data.
    :param color_data: whether to include or not color curve related data.
    :param normalize: whether to normalize curve data, so it fits in first Maya grid quadrant.
    :return: curve shape data.
    """

    space = space or OpenMaya.MSpace.kObject
    shapes = nodes.shapes(
        OpenMaya.MFnDagNode(node).getPath(), filter_types=OpenMaya.MFn.kNurbsCurve
    )
    data = {}
    for shape in shapes:
        shape_dag = OpenMaya.MFnDagNode(shape.node())
        is_intermediate = shape_dag.isIntermediateObject
        if not is_intermediate:
            curve_data = get_curve_data(
                shape, space=space, color_data=color_data, normalize=normalize
            )
            curve_data["outlinerColor"] = tuple(curve_data.get("outlinerColor", ()))
            if len(curve_data["outlinerColor"]) > 3:
                curve_data["outlinerColor"] = curve_data["outlinerColor"][:-1]
            curve_data["overrideColorRGB"] = tuple(
                curve_data.get("overrideColorRGB", ())
            )
            if len(curve_data["overrideColorRGB"]) > 3:
                curve_data["overrideColorRGB"] = curve_data["overrideColorRGB"][:-1]
            data[OpenMaya.MNamespace.stripNamespaceFromName(shape_dag.name())] = (
                curve_data
            )

    return data


# noinspection PyTypeChecker
def create_curve_shape(
    curve_data: dict,
    parent: OpenMaya.MObject | None = None,
    space: int | OpenMaya.MSpace | None = None,
    curve_size: float = 1.0,
    translate_offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
    scale_offset: tuple[float, float, float] = (1.0, 1.0, 1.0),
    axis_order: str = "XYZ",
    color: tuple[float, float, float] | None = None,
    mirror: bool | None = None,
    mod: OpenMaya.MDGModifier | None = None,
) -> tuple[OpenMaya.MObject, list[OpenMaya.MObject]]:
    """Create a NURBS curve based on the given curve data.

    Args:
        curve_data: data, {"shapeName": {"cvs": [], "knots":[], "degree": int, "form": int, "matrix": []}}
        parent: Transform that takes ownership of the curve shapes.
            If no parent is given, a new transform will be created.
        space: Coordinate space to set the point data.
        curve_size: Global curve size offset.
        translate_offset: Translate offset for the curve.
        scale_offset: Scale offset for the curve.
        axis_order: Axis order for the curve.
        color: Curve color.
        mirror: Whether the curve should be mirrored.
        mod: optional DGModifier to use to create the nodes.

    Returns:
        Tuple containing the parent MObject and the list of MObject shapes
    """

    parent_inverse_matrix = OpenMaya.MMatrix()
    if parent is None:
        parent = OpenMaya.MObject.kNullObj
    else:
        if isinstance(parent, str):
            parent = nodes.mobject(parent)
        if parent != OpenMaya.MObject.kNullObj:
            parent_inverse_matrix = nodes.world_inverse_matrix(parent)

    translate_offset = CurveCV(translate_offset)
    scale = CurveCV(scale_offset)
    order = [{"X": 0, "Y": 1, "Z": 2}[x] for x in axis_order]

    curves_to_create: dict[str, str] = {}
    for shape_name, shape_data in curve_data.items():
        if not isinstance(shape_data, dict):
            continue
        curves_to_create[shape_name] = []
        shape_parent = shape_data.get("shape_parent", None)
        if shape_parent:
            if shape_parent in curves_to_create:
                curves_to_create[shape_parent].append(shape_name)

    created_curves: list[str] = []
    all_shapes: list[OpenMaya.MObject] = []
    created_parents: dict[str, OpenMaya.MObject] = {}

    # If parent already has a shape with the same name we delete it
    # TODO: We should compare the bounding boxes of the parent shape and the
    #  new one and scale it to fit new bounding box to the old one.
    parent_shapes = []
    if parent and parent != OpenMaya.MObject.kNullObj:
        parent_shapes = nodes.shapes(OpenMaya.MFnDagNode(parent).getPath())

    for shape_name, shape_children in curves_to_create.items():
        for parent_shape in parent_shapes:
            if parent_shape.partialPathName() == shape_name:
                if not nodes.is_valid_mobject(parent_shape.node()):
                    continue
                cmds.delete(parent_shape.fullPathName())
                break

        if shape_name not in created_curves:
            shape_name, parent, new_shapes, new_curve = _create_curve(
                shape_name,
                curve_data[shape_name],
                space,
                curve_size,
                translate_offset,
                scale,
                order,
                color,
                mirror,
                parent,
                parent_inverse_matrix,
            )
            created_curves.append(shape_name)
            all_shapes.extend(new_shapes)
            created_parents[shape_name] = parent

        for child_name in shape_children:
            if child_name not in created_curves:
                to_parent = (
                    created_parents[shape_name]
                    if shape_name in created_parents
                    else parent
                )
                child_name, child_parent, new_shapes, new_curve = _create_curve(
                    child_name,
                    curve_data[child_name],
                    space,
                    curve_size,
                    translate_offset,
                    scale,
                    order,
                    color,
                    mirror,
                    OpenMaya.MObject.kNullObj,
                    parent_inverse_matrix,
                )
                created_curves.append(child_name)
                all_shapes.extend(new_shapes)
                created_parents[child_name] = child_parent
                nodes.set_parent(new_curve.parent(0), to_parent)

    return parent, all_shapes


# noinspection PyTypeChecker
def create_curve_from_points(
    name: str,
    points: list[list[float] | OpenMaya.MVector],
    shape_dict: dict | None = None,
    parent: OpenMaya.MObject | None = None,
) -> tuple[OpenMaya.MObject, tuple[OpenMaya.MObject]]:
    """Creates a new curve from the given points and the given data curve info
    :param str name: name of the curve to create.
    :param points: list of points for the curve.
    :param shape_dict: optional shape data.
    :param parent: optional parent.
    :return: the newly created curve transform and their shapes.
    """

    shape_dict = shape_dict or copy.deepcopy(SHAPE_INFO)

    name = f"{name}Shape" if not name.lower().endswith("shape") else name
    degree = shape_dict.get("degree", 3)

    deg = shape_dict["degree"]
    shape_dict["cvs"] = points
    knots = shape_dict.get("knots")
    if not knots:
        # linear curve
        if degree == 1:
            shape_dict["knots"] = tuple(range(len(points)))
        elif deg == 3:
            total_cvs = len(points)
            # append two zeros to the front of the knot count, so it lines up with maya specs
            # (ncvs - deg) + 2 * deg - 1
            knots = [0, 0] + list(range(total_cvs))
            # remap the last two indices to match the third from last
            knots[-2] = knots[len(knots) - degree]
            knots[-1] = knots[len(knots) - degree]
            shape_dict["knots"] = knots

    return create_curve_shape({name: shape_dict}, parent)


def iterate_curve_params(
    nurbs_curve_dag_path: OpenMaya.MDagPath, count: int, initial_offset: float = 0.1
) -> Iterator[float]:
    """Generator function that iterates the curve CVs and attaches transform nodes to
    the curve using a motion path.

    :param nurbs_curve_dag_path: path to the curve to attach the transforms to.
    :param count: number of transforms to create.
    :param initial_offset: param offset from the start of the curve.
    :return: generator with the created transform de and the motion path node.
    """

    curve = OpenMaya.MFnNurbsCurve(nurbs_curve_dag_path)
    length = curve.length()
    distance = length / float(count - 1)
    current = initial_offset
    for i in range(count):
        yield curve.findParamFromLength(current)
        current += distance


def attach_node_to_curve_at_param(
    nurbs_curve: OpenMaya.MObject,
    node: OpenMaya.MObject,
    param: float,
    name: str,
    rotate: bool = True,
    fraction_mode: bool = False,
) -> OpenMaya.MObject:
    """Attaches the given node to the curve using a motion path node.

    :param nurbs_curve: curve to attach the node to.
    :param node: node to attach to the curve.
    :param param: param value to attach the node to.
    :param name: name for the motion path node.
    :param rotate: whether to connect rotation from the motion path to the SRT.
    :param fraction_mode: whether the motion path should use fraction mode.
    :return: the created motion path node.
    """

    node_fn = OpenMaya.MFnDependencyNode(node)
    curve_fn = OpenMaya.MFnDependencyNode(nurbs_curve)
    motion_path = factory.create_dg_node(name, "motionPath")
    motion_path_fn = OpenMaya.MFnDependencyNode(motion_path)

    if rotate:
        plugs.connect_vector_plugs(
            motion_path_fn.findPlug("rotate", False),
            node_fn.findPlug("rotate", False),
            (True, True, True),
        )
    plugs.connect_vector_plugs(
        motion_path_fn.findPlug("allCoordinates", False),
        node_fn.findPlug("translate", False),
        (True, True, True),
    )

    plugs.connect_plugs(
        curve_fn.findPlug("worldSpace", False).elementByLogicalIndex(0),
        motion_path_fn.findPlug("geometryPath", False),
    )
    motion_path_fn.findPlug("uValue", False).setFloat(param)
    motion_path_fn.findPlug("frontAxis", False).setInt(0)
    motion_path_fn.findPlug("upAxis", False).setInt(1)
    motion_path_fn.findPlug("fractionMode", False).setBool(fraction_mode)

    return motion_path


def generate_transforms_along_curve(
    nurbs_curve_dag_path: OpenMaya.MDagPath,
    count: int,
    name: str,
    rotate: bool = True,
    fraction_mode: bool = False,
    node_type: str = "transform",
    initial_offset: float = 0.1,
) -> Iterator[tuple[OpenMaya.MObject, OpenMaya.MObject]]:
    """Generator function that iterates the curve CVs and attaches transform nodes to
    the curve using a motion path.

    :param nurbs_curve_dag_path: path to the curve to attach the transforms to.
    :param count: number of transforms to create.
    :param name: base name for the transforms to create.
    :param rotate: whether to connect rotation from the motion path to the SRT.
    :param fraction_mode: whether the motion path should use fraction mode.
    :param node_type: transform onde type to create ('transform' or 'joint').
    :param initial_offset: param offset from the start of the curve.
    :return: generator with the created transform de and the motion path node.
    """

    curve_node = nurbs_curve_dag_path.node()
    iterator = (
        scalar.generate_linear_steps(0, 1, count)
        if fraction_mode
        else iterate_curve_params(
            nurbs_curve_dag_path, count, initial_offset=initial_offset
        )
    )
    for param in iterator:
        transform = factory.create_dag_node(name, node_type)
        motion_path = attach_node_to_curve_at_param(
            curve_node,
            transform,
            param,
            "_".join((name, "mp")),
            rotate=rotate,
            fraction_mode=fraction_mode,
        )
        yield transform, motion_path


def iterate_curve_points(
    curve_shape_dag_path: OpenMaya.MDagPath,
    count: int,
    space: OpenMaya.MSpace = OpenMaya.MSpace.kObject,
) -> Iterator[tuple[OpenMaya.MVector, OpenMaya.MVector, OpenMaya.MVector]]:
    """Generator function that iterates the position, normal and tangent for the curve
    with the given point count.

    :param curve_shape_dag_path: Nurbs curve DAG path to use.
    :param count: the point count to generate points info from.
    :param space: coordinate space to query the point data.
    :return: generator with the position, normal and tangent for each point.
    """

    curve_fn = OpenMaya.MFnNurbsCurve(curve_shape_dag_path)
    length = curve_fn.length()
    distance = length / float(count - 1)
    current = 0.001
    max_param = curve_fn.findParamFromLength(length)
    default_normal = [1.0, 0.0, 0.0]
    default_tangent = [0.0, 1.0, 0.0]
    for i in range(count):
        param = curve_fn.findParamFromLength(current)
        # Maya fails to calculate the normal when the para is the max param, so we
        # sample with a slightly smaller value.
        if param == max_param:
            param = max_param - 0.0001
        point = OpenMaya.MVector(curve_fn.getPointAtParam(param, space=space))
        # When the curve if flat (like pointing directly up to +Y) an exception is
        # raised, so we catch it and return a default normal and tangent vector instead.
        try:
            yield (
                point,
                curve_fn.normal(param, space=space),
                curve_fn.tangent(param, space=space),
            )
        except RuntimeError:
            yield point, default_normal, default_tangent
        current += distance


def iterate_rotations_along_curve(
    curve_shape_dag_path: OpenMaya.MDagPath,
    count: int,
    aim_vector: OpenMaya.MVector,
    up_vector: OpenMaya.MVector,
    world_up_vector: OpenMaya.MVector,
) -> Iterator[tuple[OpenMaya.MVector, OpenMaya.MQuaternion]]:
    """Generator function that iterates the position and rotation along the curve
    incrementally based on the given joint count.

    :param curve_shape_dag_path: Nurbs curve DAG path to use.
    :param count: number of points along the curve to use.
    :param aim_vector: primary axis to align the curve.
    :param up_vector: up vector axis to use.
    :param world_up_vector: secondary world up vector to use.
    :return: generator with the position and rotation for each joint.
    """

    positions = [
        point
        for point, _, __ in iterate_curve_points(
            curve_shape_dag_path, count, space=OpenMaya.MSpace.kWorld
        )
    ]
    last_index = count - 1
    previous_rotation = OpenMaya.MQuaternion()
    for i, position in enumerate(positions):
        if i == last_index:
            rotation = previous_rotation
        else:
            rotation = mathlib.look_at(
                position,
                positions[i + 1],
                aim_vector=aim_vector,
                up_vector=up_vector,
                world_up_vector=world_up_vector,
            )
        previous_rotation = rotation
        yield position, rotation


def _create_curve(
    shape_name: str,
    shape_data: dict,
    space: OpenMaya.MSpace,
    curve_size: float,
    translate_offset: CurveCV,
    scale: CurveCV,
    order: list[int],
    color: tuple[float, float, float] | None,
    mirror: bool | None,
    parent: OpenMaya.MObject,
    parent_inverse_matrix: OpenMaya.MMatrix,
) -> tuple[str, OpenMaya.MObject, list[OpenMaya.MObject], OpenMaya.MFnNurbsCurve]:
    """Creates a curve shape based on the given data.

    Args:
        shape_name: Name of the shape to create.
        shape_data: Dictionary with the shape data.
        space: which space to use for the curve.
        curve_size: Size of the curve.
        translate_offset: Offset to apply to the curve.
        scale: Scale to apply to the curve.
        order: Axis order for the curve.
        color: Color to apply to the curve.
        mirror: Whether to mirror the curve.
        parent: Parent object for the curve.
        parent_inverse_matrix: Parent inverse matrix.

    Returns:
        Tuple with the shape name, parent, new shapes, and the curve object.
    """

    new_curve = OpenMaya.MFnNurbsCurve()
    new_shapes = []

    # transform cvs
    curve_cvs = shape_data["cvs"]
    transformed_cvs = []
    cvs = [CurveCV(pt) for pt in copy.copy(curve_cvs)]
    for i, cv in enumerate(cvs):
        cv *= curve_size * scale.reorder(order)
        cv += translate_offset.reorder(order)
        cv *= CurveCV.mirror_vector()[mirror]
        cv = cv.reorder(order)
        transformed_cvs.append(cv)

    cvs = OpenMaya.MPointArray()
    for cv in transformed_cvs:
        cvs.append(cv)
    degree = shape_data["degree"]
    form = shape_data["form"]
    knots = shape_data.get("knots", None)
    if not knots:
        knots = tuple([float(i) for i in range(-degree + 1, len(cvs))])

    enabled = shape_data.get("overrideEnabled", False) or color is not None
    if space == OpenMaya.MSpace.kWorld and parent != OpenMaya.MObject.kNullObj:
        for i in range(len(cvs)):
            cvs[i] *= parent_inverse_matrix
    shape = new_curve.create(cvs, knots, degree, form, False, False, parent)
    nodes.rename(shape, shape_name)
    new_shapes.append(shape)
    if (
        parent == OpenMaya.MObject.kNullObj
        and shape.apiType() == OpenMaya.MFn.kTransform
    ):
        parent = shape
    if enabled:
        plugs.set_plug_value(
            new_curve.findPlug("overrideEnabled", False),
            int(shape_data.get("overrideEnabled", bool(color))),
        )
        colors = color or shape_data["overrideColorRGB"]
        outliner_color = shape_data.get("outlinerColor", None)
        use_outliner_color = shape_data.get("useOutlinerColor", False)
        nodes.set_node_color(
            new_curve.object(),
            colors,
            outliner_color=outliner_color,
            use_outliner_color=use_outliner_color,
        )

    return shape_name, parent, new_shapes, new_curve
