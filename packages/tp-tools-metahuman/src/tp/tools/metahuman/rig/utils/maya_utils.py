"""Maya utility functions for rig building.

This module provides utility functions for common Maya operations used
throughout the MetaHuman rig building process. Uses tp.libs.maya.wrapper
for OpenMaya 2.0 operations.
"""

from __future__ import annotations

import logging
import math

import maya.cmds as cmds
from maya.api import OpenMaya as OpenMaya

from tp.libs.maya import wrapper

from ..data.skeleton_config import Color, ControlShapeConfig

logger = logging.getLogger(__name__)


# ============================================================================
# Node Access using Wrapper
# ============================================================================


def get_node(node_name: str) -> wrapper.DGNode | None:
    """Get a wrapper node from the given node name.

    Args:
        node_name: Name of the Maya node.

    Returns:
        Wrapper `DGNode/DagNode` or `None` if not found.
    """

    try:
        return wrapper.node_by_name(node_name)
    except (RuntimeError, ValueError):
        return None


def get_dag_node(node_name: str) -> wrapper.DagNode | None:
    """Get a wrapper DagNode from the given node name.

    Args:
        node_name: Name of the Maya DAG node.

    Returns:
        `DagNode` wrapper or `None` if not found.
    """

    node = get_node(node_name)
    return node if node and isinstance(node, wrapper.DagNode) else None


def get_joint(node_name: str) -> wrapper.Joint | None:
    """Get a wrapper `Joint` from the given node name.

    Args:
        node_name: Name of the Maya joint.

    Returns:
        Joint wrapper or None if not found.
    """

    node = get_node(node_name)
    return node if node and isinstance(node, wrapper.Joint) else None


# ============================================================================
# Plugin Management
# ============================================================================


def ensure_plugin_loaded(plugin_name: str) -> bool:
    """Ensure a Maya plugin is loaded.

    Args:
        plugin_name: Name of the plugin to load.

    Returns:
        `True` if the plugin is loaded; `False` otherwise.
    """

    if not cmds.pluginInfo(plugin_name, query=True, loaded=True):
        try:
            cmds.loadPlugin(plugin_name)
            logger.info(f"Loaded plugin: {plugin_name}")
            return True
        except RuntimeError as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return False

    return True


# ============================================================================
# Object Existence and Deletion
# ============================================================================


def object_exists(name: str) -> bool:
    """Check if a Maya object exists using wrapper.

    Args:
        name: Name of the object to check.

    Returns:
        `True` if the object with the given name exists in the current
            scene; `False` otherwise.
    """

    node = get_node(name)
    return node is not None and node.exists()


def delete_if_exists(name: str) -> bool:
    """Delete an object if it exists using wrapper.

    Args:
        name: Name of the object to delete.

    Returns:
        `True` if the object was deleted; `False` otherwise.
    """

    node = get_node(name)
    if node and node.exists():
        try:
            return node.delete()
        except RuntimeError:
            # Fall back to cmds
            try:
                cmds.delete(name)
                return True
            except RuntimeError:
                return False
    return False


# ============================================================================
# Group and Hierarchy Operations
# ============================================================================


def create_group(
    name: str, empty: bool = True, parent: str | None = None
) -> str:
    """Create a group node using wrapper.

    Args:
        name: Name for the group.
        empty: If True, create an empty group.
        parent: Optional parent for the group.

    Returns:
        Name of the created group.
    """

    parent_obj = None
    if parent:
        parent_node = get_dag_node(parent)
        if parent_node:
            parent_obj = parent_node.object()

    node = wrapper.DagNode()
    node.create(name, "transform", parent=parent_obj)
    return node.name()


def get_parent(node_name: str) -> str | None:
    """Get the parent of a node using wrapper.

    Args:
        node_name: Name of the node.

    Returns:
        Parent name or None.
    """

    node = get_dag_node(node_name)
    if node:
        parent = node.parent()
        if parent:
            return parent.name()

    return None


def get_children(node_name: str, all_descendants: bool = False) -> list[str]:
    """Get children of a node using wrapper.

    Args:
        node_name: Name of the node.
        all_descendants: If True, get all descendants.

    Returns:
        List of child names.
    """

    node = get_dag_node(node_name)
    if not node:
        return []

    if all_descendants:
        children = list(node.iterateChildren(recursive=True))
    else:
        children = node.children()

    return [child.name() for child in children]


def select_hierarchy(root: str) -> list[str]:
    """Select a node and its entire hierarchy.

    Args:
        root: Root node name.

    Returns:
        List of selected objects.
    """

    node = get_dag_node(root)
    if not node:
        return []

    result = [root]
    result.extend(get_children(root, all_descendants=True))

    # Also update Maya's selection.
    cmds.select(result, replace=True)
    return result


def reparent_node(
    child: str, parent: str, maintain_offset: bool = True
) -> bool:
    """Reparent a node to a new parent using wrapper.

    Args:
        child: Name of the child node.
        parent: Name of the new parent node.
        maintain_offset: Whether to maintain world-space position.

    Returns:
        `True` if successful; `False` otherwise.
    """

    child_node = get_dag_node(child)
    parent_node = get_dag_node(parent)

    if child_node and parent_node:
        child_node.setParent(parent_node, maintain_offset=maintain_offset)
        return True
    return False


# ============================================================================
# Transform Operations
# ============================================================================


def freeze_transforms(node_name: str) -> None:
    """Freeze all transforms on a node.

    Note: Using cmds as there's no direct wrapper equivalent.

    Args:
        node_name: Name of the node.
    """

    cmds.makeIdentity(
        node_name,
        apply=True,
        translate=True,
        rotate=True,
        scale=True,
        normal=False,
        preserveNormals=True,
    )


def delete_history(node_name: str) -> None:
    """Delete the construction history on a node.

    Args:
        node_name: Name of the node.
    """

    cmds.delete(node_name, constructionHistory=True)


def match_transform(
    source: str,
    target: str,
    translate: bool = True,
    rotate: bool = True,
    scale: bool = False,
) -> bool:
    """Match the transform of the source to the target.

    Args:
        source: Node to move.
        target: Node to match to.
        translate: Match translation.
        rotate: Match rotation.
        scale: Match scale.

    Returns:
        `True` if successful; `False` otherwise.
    """

    source_node = get_dag_node(source)
    target_node = get_dag_node(target)

    if not source_node or not target_node:
        return False

    if translate:
        world_pos = target_node.translation(space=OpenMaya.MSpace.kWorld)
        source_node.setTranslation(world_pos, space=OpenMaya.MSpace.kWorld)

    if rotate:
        world_rot = target_node.rotation(
            space=OpenMaya.MSpace.kWorld, as_quaternion=True
        )
        source_node.setRotation(world_rot, space=OpenMaya.MSpace.kWorld)

    if scale:
        target_scale = target_node.scale()
        source_node.setScale(target_scale)

    return True


def get_world_position(node_name: str) -> tuple[float, float, float]:
    """Get the world space position of a node.

    Args:
        node_name: Name of the node.

    Returns:
        Tuple of (x, y, z) position.
    """
    node = get_dag_node(node_name)
    if node:
        pos = node.translation(space=OpenMaya.MSpace.kWorld)
        return pos.x, pos.y, pos.z
    return 0.0, 0.0, 0.0


def set_world_position(
    node_name: str, position: tuple[float, float, float]
) -> bool:
    """Set the world space position of a node.

    Args:
        node_name: Name of the node.
        position: (x, y, z) position.

    Returns:
        True if successful.
    """
    node = get_dag_node(node_name)
    if node:
        node.setTranslation(position, space=OpenMaya.MSpace.kWorld)
        return True
    return False


def get_world_rotation(node_name: str) -> OpenMaya.MEulerRotation | None:
    """Get world space rotation of a node using wrapper.

    Args:
        node_name: Name of the node.

    Returns:
        `MEulerRotation` or None.
    """

    node = get_dag_node(node_name)
    if node:
        return node.rotation(space=OpenMaya.MSpace.kWorld, as_quaternion=False)
    return None


def set_world_rotation(
    node_name: str, rotation: OpenMaya.MEulerRotation | OpenMaya.MQuaternion
) -> bool:
    """Set the world space rotation of a node using wrapper.

    Args:
        node_name: Name of the node.
        rotation: Rotation to set.

    Returns:
        True if successful; False otherwise.
    """

    node = get_dag_node(node_name)
    if node:
        node.setRotation(rotation, space=OpenMaya.MSpace.kWorld)
        return True
    return False


# ============================================================================
# Curve Operations
# ============================================================================


def set_color_override(shape: str, color: Color, enable: bool = True) -> None:
    """Set the color override on a shape node using wrapper.

    Args:
        shape: Name of the shape node.
        color: Color to apply.
        enable: If True, enable the override.
    """

    node = get_node(shape)
    if not node:
        return

    # Use wrapper's plug system
    try:
        node.setAttribute("overrideEnabled", enable)
        node.setAttribute("overrideRGBColors", True)
        node.setAttribute("overrideColorR", color.r)
        node.setAttribute("overrideColorG", color.g)
        node.setAttribute("overrideColorB", color.b)
    except (RuntimeError, KeyError):
        # Fallback to cmds
        cmds.setAttr(f"{shape}.overrideEnabled", enable)
        cmds.setAttr(f"{shape}.overrideRGBColors", True)
        cmds.setAttr(f"{shape}.overrideColorRGB", color.r, color.g, color.b)


def create_nurbs_circle(
    name: str,
    config: ControlShapeConfig | None = None,
    normal: tuple[float, float, float] = (0, 0, 1),
    radius: float = 1.0,
) -> str:
    """Create a NURBS circle control curve.

    Note: Using cmds for curve creation as wrapper doesn't have direct support.

    Args:
        name: Name for the circle.
        config: Optional control shape configuration.
        normal: Normal direction for the circle.
        radius: Radius of the circle.

    Returns:
        Name of the created circle.
    """

    if config:
        normal = config.normal
        radius = config.radius

    circle = cmds.circle(
        name=name, normal=normal, center=(0, 0, 0), radius=radius, tolerance=0
    )[0]

    shape = f"{circle}Shape"
    if object_exists(shape):
        shape_node = get_node(shape)
        if shape_node:
            shape_node.setAttribute(
                "lineWidth", config.line_width if config else 2.0
            )

    # Apply degree and sections if specified
    if config and (config.degree == 1 or config.sections != 8):
        make_node = find_make_node(circle, "makeNurbCircle")
        if make_node:
            make_wrapper = get_node(make_node)
            if make_wrapper:
                if config.degree == 1:
                    make_wrapper.setAttribute("degree", 1)
                make_wrapper.setAttribute("sections", config.sections)

    return circle


def _rename_curve_shapes(curve: str, line_width: float = 2.0) -> None:
    """Rename curve shapes to match the curve name and set line width.

    Args:
        curve: Name of the curve transform.
        line_width: Line width to set on shapes.
    """
    shapes = cmds.listRelatives(curve, shapes=True) or []
    for i, shape in enumerate(shapes):
        new_name = f"{curve}Shape" if i == 0 else f"{curve}Shape{i}"
        if shape != new_name:
            cmds.rename(shape, new_name)
    # Re-get shapes after rename
    shapes = cmds.listRelatives(curve, shapes=True) or []
    for shape in shapes:
        cmds.setAttr(f"{shape}.lineWidth", line_width)


def create_cube_control(
    name: str, size: float = 1.0, line_width: float = 2.0
) -> str:
    """Create a cube-shaped control curve.

    Args:
        name: Name for the control.
        size: Size of the cube.
        line_width: Line width for the curve.

    Returns:
        Name of the created control.
    """
    s = size * 0.5
    points = [
        (-s, s, s),
        (s, s, s),
        (s, s, -s),
        (-s, s, -s),
        (-s, s, s),
        (-s, -s, s),
        (s, -s, s),
        (s, s, s),
        (s, -s, s),
        (s, -s, -s),
        (s, s, -s),
        (s, -s, -s),
        (-s, -s, -s),
        (-s, s, -s),
        (-s, -s, -s),
        (-s, -s, s),
    ]
    curve = cmds.curve(name=name, degree=1, point=points)
    _rename_curve_shapes(curve, line_width)
    return curve


def create_diamond_control(
    name: str, size: float = 1.0, line_width: float = 2.0
) -> str:
    """Create a diamond/octahedron-shaped control curve.

    Args:
        name: Name for the control.
        size: Size of the diamond.
        line_width: Line width for the curve.

    Returns:
        Name of the created control.
    """
    s = size
    points = [
        (0, s, 0),
        (s, 0, 0),
        (0, 0, s),
        (0, s, 0),
        (0, 0, -s),
        (s, 0, 0),
        (0, -s, 0),
        (0, 0, s),
        (-s, 0, 0),
        (0, s, 0),
        (0, 0, -s),
        (-s, 0, 0),
        (0, -s, 0),
    ]
    curve = cmds.curve(name=name, degree=1, point=points)
    _rename_curve_shapes(curve, line_width)
    return curve


def create_arrow_control(
    name: str, size: float = 1.0, line_width: float = 2.0
) -> str:
    """Create an arrow-shaped control curve.

    Args:
        name: Name for the control.
        size: Size of the arrow.
        line_width: Line width for the curve.

    Returns:
        Name of the created control.
    """
    s = size
    points = [
        (0, 0, s * 2),
        (s, 0, 0),
        (s * 0.5, 0, 0),
        (s * 0.5, 0, -s * 2),
        (-s * 0.5, 0, -s * 2),
        (-s * 0.5, 0, 0),
        (-s, 0, 0),
        (0, 0, s * 2),
    ]
    curve = cmds.curve(name=name, degree=1, point=points)
    _rename_curve_shapes(curve, line_width)
    return curve


def create_four_arrow_control(
    name: str, size: float = 1.0, line_width: float = 2.0
) -> str:
    """Create a four-directional arrow control (move-style) in XZ plane (Y-up).

    Args:
        name: Name for the control.
        size: Size of the control.
        line_width: Line width for the curve.

    Returns:
        Name of the created control.
    """
    s = size
    a = s * 0.2  # Arrow head size
    b = s * 0.1  # Arrow body width

    points = [
        # Forward arrow (positive Z)
        (0, 0, s),
        (-a, 0, s - a),
        (-b, 0, s - a),
        (-b, 0, b),
        # Left arrow (negative X)
        (-s + a, 0, b),
        (-s + a, 0, a),
        (-s, 0, 0),
        (-s + a, 0, -a),
        (-s + a, 0, -b),
        (-b, 0, -b),
        # Back arrow (negative Z)
        (-b, 0, -s + a),
        (-a, 0, -s + a),
        (0, 0, -s),
        (a, 0, -s + a),
        (b, 0, -s + a),
        (b, 0, -b),
        # Right arrow (positive X)
        (s - a, 0, -b),
        (s - a, 0, -a),
        (s, 0, 0),
        (s - a, 0, a),
        (s - a, 0, b),
        (b, 0, b),
        # Back to forward arrow
        (b, 0, s - a),
        (a, 0, s - a),
        (0, 0, s),
    ]
    curve = cmds.curve(name=name, degree=1, point=points)
    _rename_curve_shapes(curve, line_width)
    return curve


def create_cog_control(
    name: str, size: float = 1.0, teeth: int = 8, line_width: float = 2.0
) -> str:
    """Create a cog/gear-shaped control curve in XZ plane (Y-up).

    Args:
        name: Name for the control.
        size: Size of the cog.
        teeth: Number of teeth on the cog.
        line_width: Line width for the curve.

    Returns:
        Name of the created control.
    """
    import math

    points = []
    inner_radius = size * 0.75
    outer_radius = size

    for i in range(teeth * 2):
        angle = (i / (teeth * 2)) * 2 * math.pi
        if i % 2 == 0:
            r = outer_radius
        else:
            r = inner_radius
        x = math.cos(angle) * r
        z = math.sin(angle) * r
        points.append((x, 0, z))

    # Close the shape
    points.append(points[0])

    curve = cmds.curve(name=name, degree=1, point=points)
    _rename_curve_shapes(curve, line_width)
    return curve


def create_sphere_control(
    name: str, size: float = 1.0, line_width: float = 2.0
) -> str:
    """Create a sphere-shaped control with three circles.

    Args:
        name: Name for the control.
        size: Size of the sphere.
        line_width: Line width for the curves.

    Returns:
        Name of the created control.
    """
    # Create three circles in different orientations
    circle_x = cmds.circle(
        name=f"{name}_temp_x",
        normal=(1, 0, 0),
        radius=size,
        constructionHistory=False,
    )[0]
    circle_y = cmds.circle(
        name=f"{name}_temp_y",
        normal=(0, 1, 0),
        radius=size,
        constructionHistory=False,
    )[0]
    circle_z = cmds.circle(
        name=f"{name}_temp_z",
        normal=(0, 0, 1),
        radius=size,
        constructionHistory=False,
    )[0]

    # Create main transform
    main_ctrl = cmds.group(empty=True, name=name)

    # Parent all shapes to main transform and rename them
    for i, temp_circle in enumerate([circle_x, circle_y, circle_z]):
        shape = cmds.listRelatives(temp_circle, shapes=True)[0]
        cmds.parent(shape, main_ctrl, shape=True, relative=True)
        cmds.delete(temp_circle)

    # Rename shapes and set line width
    shapes = cmds.listRelatives(main_ctrl, shapes=True) or []
    for i, shape in enumerate(shapes):
        new_name = f"{main_ctrl}Shape" if i == 0 else f"{main_ctrl}Shape{i}"
        if shape != new_name:
            cmds.rename(shape, new_name)

    shapes = cmds.listRelatives(main_ctrl, shapes=True) or []
    for shape in shapes:
        cmds.setAttr(f"{shape}.lineWidth", line_width)

    return main_ctrl


def create_square_control(
    name: str, size: float = 1.0, line_width: float = 2.0
) -> str:
    """Create a square-shaped control curve.

    Args:
        name: Name for the control.
        size: Size of the square.
        line_width: Line width for the curve.

    Returns:
        Name of the created control.
    """
    s = size * 0.5
    points = [(-s, 0, s), (s, 0, s), (s, 0, -s), (-s, 0, -s), (-s, 0, s)]
    curve = cmds.curve(name=name, degree=1, point=points)
    _rename_curve_shapes(curve, line_width)
    return curve


def create_locator_control(
    name: str, size: float = 1.0, line_width: float = 2.0
) -> str:
    """Create a locator-style cross control curve.

    Args:
        name: Name for the control.
        size: Size of the locator.
        line_width: Line width for the curve.

    Returns:
        Name of the created control.
    """
    s = size
    # Create three lines for X, Y, Z axes
    points = [
        (-s, 0, 0),
        (s, 0, 0),
        (0, 0, 0),
        (0, -s, 0),
        (0, s, 0),
        (0, 0, 0),
        (0, 0, -s),
        (0, 0, s),
    ]
    curve = cmds.curve(name=name, degree=1, point=points)
    _rename_curve_shapes(curve, line_width)
    return curve


def create_direction_arrow_control(
    name: str, size: float = 1.0, line_width: float = 2.0
) -> str:
    """Create a directional arrow control indicating forward direction.

    This creates a stylized arrow pointing forward (positive Z in XZ plane)
    with a sleek, modern design suitable for root controls. Y-up world.

    Args:
        name: Name for the control.
        size: Size of the arrow.
        line_width: Line width for the curve.

    Returns:
        Name of the created control.
    """
    s = size
    # Create a stylized forward-facing arrow in XZ plane (Y=0)
    # Arrow tip at front (positive Z), base at back
    points = [
        # Arrow tip
        (0, 0, s * 1.5),
        # Right side of arrow head
        (s * 0.6, 0, s * 0.5),
        (s * 0.3, 0, s * 0.5),
        # Right side of body
        (s * 0.3, 0, -s),
        # Back of arrow
        (-s * 0.3, 0, -s),
        # Left side of body
        (-s * 0.3, 0, s * 0.5),
        (-s * 0.6, 0, s * 0.5),
        # Back to tip
        (0, 0, s * 1.5),
    ]
    curve = cmds.curve(name=name, degree=1, point=points)
    _rename_curve_shapes(curve, line_width)
    return curve


def create_hand_control(
    name: str, size: float = 1.0, line_width: float = 2.0
) -> str:
    """Create a stylized hand/fingers control curve in XZ plane (Y-up).

    This creates a modern-looking control with curved fingers silhouette,
    perfect for finger curl/spread controls.

    Args:
        name: Name for the control.
        size: Size of the control.
        line_width: Line width for the curve.

    Returns:
        Name of the created control.
    """
    s = size

    # Create a stylized hand shape with 5 finger-like prongs
    # Palm base at back, fingers pointing forward (positive Z)
    points = [
        # Start at palm left
        (-s * 0.8, 0, -s * 0.3),
        # Pinky finger
        (-s * 0.8, 0, s * 0.6),
        (-s * 0.65, 0, s * 0.8),
        (-s * 0.5, 0, s * 0.6),
        # Ring finger
        (-s * 0.5, 0, s * 0.8),
        (-s * 0.35, 0, s * 1.0),
        (-s * 0.2, 0, s * 0.8),
        # Middle finger
        (-s * 0.2, 0, s * 0.9),
        (0, 0, s * 1.2),
        (s * 0.2, 0, s * 0.9),
        # Index finger
        (s * 0.2, 0, s * 0.8),
        (s * 0.35, 0, s * 1.0),
        (s * 0.5, 0, s * 0.8),
        # Thumb
        (s * 0.5, 0, s * 0.5),
        (s * 0.8, 0, s * 0.7),
        (s * 0.9, 0, s * 0.4),
        (s * 0.6, 0, s * 0.2),
        # Palm right and back to start
        (s * 0.6, 0, -s * 0.3),
        (-s * 0.8, 0, -s * 0.3),
    ]

    curve = cmds.curve(name=name, degree=1, point=points)
    _rename_curve_shapes(curve, line_width)
    return curve


def create_control_shape(
    name: str,
    config: ControlShapeConfig,
) -> str:
    """Create a control curve based on the shape type in config.

    Args:
        name: Name for the control.
        config: Control shape configuration.

    Returns:
        Name of the created control.
    """
    from ..data.skeleton_config import ShapeType

    shape_type = config.shape_type
    size = config.radius
    line_width = config.line_width

    if shape_type == ShapeType.CUBE:
        return create_cube_control(name, size, line_width)
    elif shape_type == ShapeType.DIAMOND:
        return create_diamond_control(name, size, line_width)
    elif shape_type == ShapeType.ARROW:
        return create_arrow_control(name, size, line_width)
    elif shape_type == ShapeType.FOUR_ARROW:
        return create_four_arrow_control(name, size, line_width)
    elif shape_type == ShapeType.COG:
        return create_cog_control(name, size, line_width=line_width)
    elif shape_type == ShapeType.SPHERE:
        return create_sphere_control(name, size, line_width)
    elif shape_type == ShapeType.SQUARE:
        return create_square_control(name, size, line_width)
    elif shape_type == ShapeType.LOCATOR:
        return create_locator_control(name, size, line_width)
    elif shape_type == ShapeType.DIRECTION_ARROW:
        return create_direction_arrow_control(name, size, line_width)
    elif shape_type == ShapeType.HAND:
        return create_hand_control(name, size, line_width)
    else:
        # Default to circle
        return create_nurbs_circle(name, config)


def find_make_node(node_name: str, node_type: str) -> str | None:
    """Find a specific type of construction node in a node's history.

    Uses wrapper's connection iteration.

    Args:
        node_name: Node to search history for.
        node_type: Type of node to find.

    Returns:
        Name of the found node or None.
    """

    node = get_node(node_name)
    if not node:
        return None

    # Iterate through sources (upstream connections).
    for source_plug, _ in node.iterateConnections(
        source=True, destination=False
    ):
        source_node = source_plug.node()
        if source_node and node_type in source_node.name():
            return source_node.name()

    # Fallback to cmds `listHistory`.
    history = cmds.listHistory(node_name) or []
    for hist_node in history:
        if node_type in hist_node:
            return hist_node

    return None


def create_offset_group(source_object: str, offset_name: str) -> str:
    """Create an offset group for a control or joint.

    Args:
        source_object: Object to create offset for.
        offset_name: Name for the offset group.

    Returns:
        Name of the created offset group.
    """

    node = get_node(source_object)
    if not node:
        return offset_name

    is_joint = isinstance(node, wrapper.Joint)

    if not is_joint:
        # For non-joints, duplicate and remove shape.
        cmds.duplicate(source_object, name=offset_name)
        shapes = cmds.listRelatives(offset_name, shapes=True)
        if shapes:
            cmds.delete(shapes[0])
        cmds.parent(source_object, offset_name)
    else:
        # For joints, create an empty group.
        offset_name = create_group(offset_name)

        # Match transform using wrapper.
        match_transform(offset_name, source_object)

        parent = get_parent(source_object)
        if parent:
            reparent_node(offset_name, parent)
        reparent_node(source_object, offset_name, maintain_offset=False)

    return offset_name


# ============================================================================
# Pole Vector Calculations
# ============================================================================


def calculate_pole_vector_position(
    bone_a: str,
    bone_b: str,
    bone_c: str,
    distance: float = 50.0,
    flip: bool = False,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Calculate the optimal pole vector position for a 3-joint chain.

    Uses wrapper for getting positions.
    Based on Craig Miller's algorithm: https://vimeo.com/66262994

    The pole vector is placed in the plane formed by the three joints,
    extended outward from the mid-joint in the direction of the bend.

    Args:
        bone_a: First joint (e.g., shoulder/hip).
        bone_b: Middle joint (e.g., elbow/knee).
        bone_c: End joint (e.g., wrist/ankle).
        distance: Distance from the mid-joint to place the pole vector.
        flip: If True, flip the pole vector direction (useful for arms).

    Returns:
        Tuple of (position, rotation) for the pole vector.
    """

    # Get world positions using wrapper.
    node_a = get_dag_node(bone_a)
    node_b = get_dag_node(bone_b)
    node_c = get_dag_node(bone_c)

    if not all([node_a, node_b, node_c]):
        return (0, 0, 0), (0, 0, 0)

    start = node_a.translation(space=OpenMaya.MSpace.kWorld)
    mid = node_b.translation(space=OpenMaya.MSpace.kWorld)
    end = node_c.translation(space=OpenMaya.MSpace.kWorld)

    # Calculate direction vectors.
    start_end = end - start
    start_mid = mid - start

    # Project the mid-point onto the start-end line to find the closest point.
    start_end_len_sq = start_end * start_end
    if start_end_len_sq < 0.0001:
        # Degenerate case: start and end are at same position.
        return (mid.x, mid.y, mid.z), (0, 0, 0)

    dot_product = start_mid * start_end
    t = dot_product / start_end_len_sq
    proj_point = start + (start_end * t)

    # Calculate the pole vector direction (from projected point to mid-joint).
    # This is the direction the mid-joint is "bending" away from the line.
    pole_dir = mid - proj_point
    pole_dir_len = pole_dir.length()

    if pole_dir_len < 0.0001:
        # Limb is straight - use a default direction perpendicular to the limb.
        # Try to use the joint's local X or Z axis as a fallback.
        up_vector = OpenMaya.MVector(0, 1, 0)
        pole_dir = start_end ^ up_vector
        if pole_dir.length() < 0.0001:
            pole_dir = OpenMaya.MVector(1, 0, 0)
        pole_dir.normalize()
    else:
        pole_dir.normalize()

    # Flip the direction if requested (for arms where the default might be wrong).
    if flip:
        pole_dir = pole_dir * -1

    # Place pole vector at the specified distance from the mid-joint.
    final_pos = mid + (pole_dir * distance)

    # Calculate rotation to aim at the mid-joint.
    cross1 = start_end ^ pole_dir
    cross1.normalize()

    cross2 = cross1 ^ pole_dir
    cross2.normalize()

    # Build matrix from vectors.
    matrix_list = [
        pole_dir.x,
        pole_dir.y,
        pole_dir.z,
        0,
        cross1.x,
        cross1.y,
        cross1.z,
        0,
        cross2.x,
        cross2.y,
        cross2.z,
        0,
        0,
        0,
        0,
        1,
    ]

    matrix = OpenMaya.MMatrix(matrix_list)
    transform_matrix = OpenMaya.MTransformationMatrix(matrix)
    rot = transform_matrix.rotation(asQuaternion=False)

    position = (final_pos.x, final_pos.y, final_pos.z)
    rotation = (math.degrees(rot.x), math.degrees(rot.y), math.degrees(rot.z))

    return position, rotation


def create_pole_vector_locator(
    bone_a: str,
    bone_b: str,
    bone_c: str,
    name: str | None = None,
    flip: bool = False,
) -> str:
    """Create a locator at the optimal pole vector position.

    Args:
        bone_a: First joint.
        bone_b: Middle joint.
        bone_c: End joint.
        name: Optional name for the locator.
        flip: If True, flip the pole vector direction.

    Returns:
        Name of the created locator.
    """

    position, rotation = calculate_pole_vector_position(
        bone_a, bone_b, bone_c, flip=flip
    )

    loc_name = name or f"{bone_b}_pole_vector_loc"
    locator = cmds.spaceLocator(name=loc_name)[0]

    # Set position.
    set_world_position(locator, position)

    # Set rotation
    rot_euler = OpenMaya.MEulerRotation(
        math.radians(rotation[0]),
        math.radians(rotation[1]),
        math.radians(rotation[2]),
    )
    set_world_rotation(locator, rot_euler)

    return locator


# ============================================================================
# Scene Settings
# ============================================================================


def current_up_axis() -> str:
    """Get the current scene up axis."""

    return cmds.upAxis(q=True, axis=True)


def set_up_axis(axis: str = "z", rotate_view: bool = True) -> None:
    """Set the scene up axis.

    Args:
        axis: Axis to set as up ("y" or "z").
        rotate_view: If True, rotate the view to match.
    """

    if current_up_axis() == axis:
        return

    cmds.upAxis(axis=axis, rotateView=rotate_view)

    # Reset viewport camera behavior after changing up axis.
    # The tumble tool and camera pivot can become misaligned causing
    # weird rotation behavior and incorrect pivot points.
    _reset_viewport_after_up_axis_change()


def _reset_viewport_after_up_axis_change() -> None:
    """Reset viewport camera and tumble behavior after up axis change.

    This fixes issues where the camera rotation becomes "broken" after
    changing and restoring the up axis, including:
    - Tumble tool rotating in wrong directions
    - Camera pivot point being incorrect
    """

    try:
        # Reset tumble tool settings.
        # localTumble=0: Use world up for tumble reference (not camera local).
        # orthoLock=True: Lock orthographic views properly.
        cmds.tumbleCtx("tumbleContext", edit=True, localTumble=0)
        cmds.tumbleCtx("tumbleContext", edit=True, orthoLock=True)
    except RuntimeError:
        # tumbleContext may not exist in batch mode.
        pass

    # Reset tumble pivot on each camera and fix persp camera orientation.
    try:
        model_panels = cmds.getPanel(type="modelPanel") or []
        for panel in model_panels:
            try:
                # Get the camera and reset its tumble pivot attribute.
                camera = cmds.modelPanel(panel, query=True, camera=True)
                if not camera:
                    continue
                camera_shapes = cmds.listRelatives(
                    camera, shapes=True, type="camera"
                )
                if not camera_shapes:
                    continue
                camera_shape = camera_shapes[0]

                # Reset tumble pivot to origin - this is critical for fixing
                # the rotation point after up axis change.
                cmds.setAttr(
                    f"{camera_shape}.tumblePivot", 0, 0, 0, type="double3"
                )

                # For perspective cameras, reset the view to fix orientation.
                # This uses `viewSet` which properly recalculates the camera's
                # up vector based on the new scene up axis.
                if "persp" in camera.lower():
                    cmds.viewSet(camera, home=True)
                    # Frame all objects in view (equivalent to pressing 'F').
                    cmds.viewFit(camera, allObjects=True)

            except RuntimeError:
                continue

    except RuntimeError:
        pass

    # Refresh the viewport to apply changes.
    try:
        cmds.refresh(force=True)
    except RuntimeError:
        pass


def view_along_axis(axis: str) -> None:
    """Set the active viewport's camera to view along the specified axis.

    Args:
        axis: The axis to view along ('x', '-x', 'y', '-y', 'z', '-z').
    """

    active_panel = cmds.getPanel(withFocus=True)
    if not active_panel:
        logger.warning("No viewport focused.")
        return

    # noinspection PyBroadException
    try:
        camera = cmds.modelPanel(active_panel, query=True, camera=True)

        rotations = {
            "x": (0, 90, 0),
            "-x": (0, -90, 0),
            "y": (-90, 0, 0),
            "-y": (90, 0, 0),
            "z": (0, 0, 0),
            "-z": (0, 180, 0),
        }

        if axis in rotations:
            rotate_x, rotate_y, rotate_z = rotations[axis]
            cmds.rotate(
                rotate_x,
                rotate_y,
                rotate_z,
                camera,
                relative=True,
                objectSpace=True,
            )
        else:
            logger.warning(
                f"Invalid axis: {axis}. Use 'x', '-x', 'y', '-y', 'z', or '-z'."
            )
    except Exception:
        logger.debug("Skipped view along axis adjustment.")


def show_confirm_dialog(
    title: str,
    message: str,
    buttons: list[str] = None,
    default_button: str = "Yes",
    cancel_button: str = "No",
) -> str:
    """Show a confirmation dialog.

    Args:
        title: Dialog title.
        message: Dialog message.
        buttons: List of button labels.
        default_button: Default button.
        cancel_button: Cancel button.

    Returns:
        The selected button label.
    """
    if buttons is None:
        buttons = ["Yes", "No"]

    return cmds.confirmDialog(
        title=title,
        message=message,
        button=buttons,
        defaultButton=default_button,
        cancelButton=cancel_button,
        dismissString=cancel_button,
    )
