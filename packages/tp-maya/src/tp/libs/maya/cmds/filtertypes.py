from __future__ import annotations

from maya import cmds
from loguru import logger

from .cameras.cameras import get_startup_camera_transforms, get_startup_camera_shapes


ALL_FILTER_TYPE = "All Node Types"
GROUP_FILTER_TYPE = "Group"
GEOMETRY_FILTER_TYPE = "Geometry"
POLYGON_FILTER_TYPE = "Polygon"
SPHERE_FILTER_TYPE = "Sphere"
BOX_FILTER_TYPE = "Box"
CYLINDER_FILTER_TYPE = "Cylinder"
CAPSULE_FILTER_TYPE = "Capsule"
NURBS_FILTER_TYPE = "Nurbs"
JOINT_FILTER_TYPE = "Joint"
CURVE_FILTER_TYPE = "Curve"
CIRCLE_FILTER_TYPE = "Circle"
LOCATOR_FILTER_TYPE = "Locator"
LIGHT_FILTER_TYPE = "Light"
CAMERA_FILTER_TYPE = "Camera"
CLUSTER_FILTER_TYPE = "Cluster"
FOLLICLE_FILTER_TYPE = "Follicle"
DEFORMER_FILTER_TYPE = "Deformer"
TRANSFORM_FILTER_TYPE = "Transform"
CONTROLLER_FILTER_TYPE = "Controller"
PARTICLE_FILTER_TYPE = "Particle"
NETWORK_FILTER_TYPE = "Network"

# Dictionary containing that maps all filters nice names with their types.
ALL_SPECIAL = "ALL"
GROUP_SPECIAL = "GROUP"
TYPE_FILTERS = {
    ALL_FILTER_TYPE: [ALL_SPECIAL],
    GROUP_FILTER_TYPE: [GROUP_SPECIAL],
    GEOMETRY_FILTER_TYPE: ["mesh", "nurbsSurface"],
    POLYGON_FILTER_TYPE: ["polygon"],
    SPHERE_FILTER_TYPE: ["sphere"],
    BOX_FILTER_TYPE: ["box"],
    CYLINDER_FILTER_TYPE: ["cylinder"],
    CAPSULE_FILTER_TYPE: ["capsule"],
    NURBS_FILTER_TYPE: ["nurbsSurface"],
    JOINT_FILTER_TYPE: ["joint"],
    CURVE_FILTER_TYPE: ["nurbsCurve"],
    CIRCLE_FILTER_TYPE: ["circle"],
    LOCATOR_FILTER_TYPE: ["locator"],
    LIGHT_FILTER_TYPE: ["light"],
    CAMERA_FILTER_TYPE: ["camera"],
    CLUSTER_FILTER_TYPE: ["cluster"],
    FOLLICLE_FILTER_TYPE: ["follicle"],
    DEFORMER_FILTER_TYPE: [
        "clusterHandle",
        "baseLattice",
        "lattice",
        "softMod",
        "deformBend",
        "sculpt",
        "deformTwist",
        "deformWave",
        "deformFlare",
    ],
    TRANSFORM_FILTER_TYPE: ["transform"],
    CONTROLLER_FILTER_TYPE: ["control"],
    PARTICLE_FILTER_TYPE: ["particle"],
    NETWORK_FILTER_TYPE: ["network"],
}

GEO_SUFFIX = "geo"
JOINT_SUFFIX = "jnt"
CONTROLLER_SUFFIX = "ctrl"
CONSTRAINT_SUFFIX = "cnstr"
GROUP_SUFFIX = "grp"
SRT_SUFFIX = "srt"
LEFT_SUFFIX = "L"
LEFT2_SUFFIX = "lft"
RIGHT_SUFFIX = "R"
RIGHT2_SUFFIX = "rgt"
CENTER_SUFFIX = "M"
CENTER2_SUFFIX = "cntr"
CENTER3_SUFFIX = "mid"
LOW = "low"
HIGH = "high"
LORES = "lores"
HIRES = "hires"
CURVE_SUFFIX = "crv"
CLUSTER_SUFFIX = "cstr"
FOLLICLE_SUFFIX = "foli"
NURBS_SUFFIX = "geo"
IMAGE_PLANE_SUFFIX = "imgp"
LOCATOR_SUFFIX = "loc"
LIGHT_SUFFIX = "lgt"
SHADER_SUFFIX = "shdr"
SHADING_GROUP_SUFFIX = "shdg"
CAMERA_SUFFIX = "cam"

SUFFIXES = [
    "Select...",
    f"Mesh: '{GEO_SUFFIX}'",
    f"Joint: '{JOINT_SUFFIX}'",
    f"Control: '{CONTROLLER_SUFFIX}'",
    f"Constraint: '{CONSTRAINT_SUFFIX}'",
    f"Group: '{GROUP_SUFFIX}'",
    f"Rot Trans Scl: '{SRT_SUFFIX}'",
    f"Left: '{LEFT_SUFFIX}'",
    f"Left: '{LEFT2_SUFFIX}'",
    f"Right: '{RIGHT_SUFFIX}'",
    f"Right: '{RIGHT2_SUFFIX}'",
    f"Center: '{CENTER_SUFFIX}'",
    f"Center: '{CENTER2_SUFFIX}'",
    "Center: '{CENTER3_SUFFIX}'",
    f"Low: '{LOW}'",
    f"High: '{HIGH}'",
    f"Lores: '{LORES}'",
    f"Hires: '{HIRES}'",
    f"Camera: '{CAMERA_SUFFIX}'",
    f"Curve: '{CURVE_SUFFIX}'",
    f"Cluster: '{CLUSTER_SUFFIX}'",
    f"Follicle: '{FOLLICLE_SUFFIX}'",
    f"Nurbs: '{NURBS_SUFFIX}'",
    f"Image Planes: '{IMAGE_PLANE_SUFFIX}'",
    f"Locators: '{LOCATOR_SUFFIX}'",
    f"Shader: '{SHADER_SUFFIX}'",
    f"Lights: '{LIGHT_SUFFIX}'",
    f"Shading Group: '{SHADING_GROUP_SUFFIX}'",
]

AUTO_SUFFIX_DICT = {
    "mesh": GEO_SUFFIX,
    "joint": JOINT_SUFFIX,
    "nurbsCurve": CURVE_SUFFIX,
    "group": GROUP_SUFFIX,
    "follicle": FOLLICLE_SUFFIX,
    "nurbsSurface": GEO_SUFFIX,
    "imagePlane": IMAGE_PLANE_SUFFIX,
    "aiAreaLight": LIGHT_SUFFIX,
    "rsPhysicalLight": LIGHT_SUFFIX,
    "PxrRectLight": LIGHT_SUFFIX,
    "PxrSphereLight": LIGHT_SUFFIX,
    "PxrDiskLight": LIGHT_SUFFIX,
    "PxrDistantLight": LIGHT_SUFFIX,
    "PxrDomeLight": LIGHT_SUFFIX,
    "VRayLightRectShape": LIGHT_SUFFIX,
    "VRaySunShape": LIGHT_SUFFIX,
    "VRayLightDomeShape": LIGHT_SUFFIX,
    "locator": LOCATOR_SUFFIX,
    "light": LIGHT_SUFFIX,
    "lambert": SHADER_SUFFIX,
    "blinn": SHADER_SUFFIX,
    "phong": SHADER_SUFFIX,
    "rampShader": SHADER_SUFFIX,
    "phongE": SHADER_SUFFIX,
    "surfaceShader": SHADER_SUFFIX,
    "useBackground": SHADER_SUFFIX,
    "shadingGroup": SHADING_GROUP_SUFFIX,
    "aiStandardSurface": SHADER_SUFFIX,
    "RedshiftMaterial": SHADER_SUFFIX,
    "VRayMtl": SHADER_SUFFIX,
    "PxrSurface": SHADER_SUFFIX,
    "controller": CONTROLLER_SUFFIX,
    "camera": CAMERA_SUFFIX,
    "clusterHandle": CLUSTER_SUFFIX,
    "parentConstraint": CONSTRAINT_SUFFIX,
    "pointConstraint": CONSTRAINT_SUFFIX,
    "orientConstraint": CONSTRAINT_SUFFIX,
    "aimConstraint": CONSTRAINT_SUFFIX,
    "matrixConstraint": CONSTRAINT_SUFFIX,
}

PROTECTED_NODES = [
    "layerManager",
    "renderLayerManager",
    "poseInterpolatorManager",
    "defaultRenderLayer",
    "defaultLayer",
    "lightLinker1",
    "shapeEditorManager",
]


def filter_shapes(
    objs_list: list[str],
    allow_joints: bool = True,
    allow_constraints: bool = True,
    allow_dg: bool = True,
) -> list[str]:
    """If a shape node is found in given objects, it will be replaced with
    its transform parent. Otherwise, will leave the node in the list.

    Args:
        objs_list: List of Maya object names to filter.
        allow_joints: Whether to include joints in the returned list or not.
            They will be treated as transform nodes.
        allow_constraints: Whether to include constraints in the returned
            list or not. They will be treated as transform nodes.
        allow_dg: Whether to return DG nodes in the returned list or not.

    Returns:
        List of Maya object names with only transform nodes.

    Raises:
        ValueError: If the parent of a shape node cannot be found.
    """

    found_transforms: list[str] = []

    for obj in objs_list:
        if cmds.objectType(obj, isType="transform"):
            found_transforms.append(obj)
        elif allow_joints and cmds.objectType(obj, isType="joint"):
            found_transforms.append(obj)
        elif allow_constraints and cmds.objectType(obj, isType="constraint"):
            found_transforms.append(obj)
        else:
            # If the object is not a shape node, we return it.
            if not cmds.ls(obj, shapes=True):
                found_transforms.append(obj)
            # If the object is a DAG node, we return its transform parent.
            elif "dagNode" in cmds.nodeType(obj, inherited=True):
                found_dag_parents = cmds.listRelatives(obj, parent=True, fullPath=True)
                if found_dag_parents:
                    found_transforms.append(found_dag_parents[0])
                else:
                    raise ValueError(f"Could not find parent for object: {obj}")
            elif allow_dg:
                # Not DAG nodes do not have transform nodes, we add them directly.
                found_transforms.append(obj)

    # Remove duplicates by keeping its order.
    seen = set()
    seen_add = seen.add
    return [x for x in found_transforms if not (x in seen or seen_add(x))]


def filter_all_node_types(
    selection_only: bool = True,
    dag: bool = False,
    transforms_only: bool = False,
    remove_maya_defaults: bool = True,
):
    """Filter nodes with no restrictions of node types.

    Args:
        selection_only: Whether to search all scene objects or only selected ones in the scene.
        dag: Whether to return only DAG nodes.
        remove_maya_defaults: Whether to ignore Maya default nodes.
        transforms_only: Whether to return only transform nodes.

    Returns:
        List of node names in Maya that matches the given criteria.
    """

    if not selection_only:
        all_objs = cmds.ls(long=True, dagObjects=dag)
        if not remove_maya_defaults:
            protected = cmds.ls(defaultNodes=True) + PROTECTED_NODES
            scene_filtered = list(set(all_objs) - set(protected))
            if not transforms_only:
                return scene_filtered
            else:
                return filter_shapes(scene_filtered)

        default_cameras = get_startup_camera_transforms() + get_startup_camera_shapes()
        maya_defaults = default_cameras + cmds.ls(defaultNodes=True) + PROTECTED_NODES
        scene_filtered = list(set(all_objs) - set(maya_defaults))
        if not transforms_only:
            return scene_filtered
        else:
            return filter_shapes(scene_filtered)

    all_selected_objs = cmds.ls(selection=True, long=True, dagObjects=dag)
    if not all_selected_objs:
        logger.warning("No objects selected, select at least one please!")
        return []

    return (
        all_selected_objs if not transforms_only else filter_shapes(all_selected_objs)
    )


def filter_nodes_by_type(
    filter_types: list[str],
    objs_list: list[str] | None = None,
    search_scene: bool = False,
    dag: bool = False,
):
    """Return a list of objects that match the given node type.

    Args:
        filter_types: List of node types to filter by. This should match a
            string from the TYPE_FILTERS keys.
        objs_list: List of Maya nodes to filter. If None, will search all
            scene objects.
        search_scene: Whether to search all scene objects or only the
            given objs_list.
        dag: Whether to return only DAG nodes.

    Returns:
        List of filtered objects that match the filter criteria.
    """

    filtered_objs: list[str] = []
    if not search_scene:
        for filter_type in filter_types:
            filtered_objs += cmds.ls(type=filter_type, long=True, dagObjects=dag)
    else:
        for filter_type in filter_types:
            filtered_objs += cmds.ls(
                objs_list,
                type=filter_type,
                long=True,
                dagObjects=dag,
            )

    return list(set(filtered_objs))


def filter_by_group(selection_only: bool, dag: bool) -> list[str]:
    """Return nodes that are groups (empty transform nodes with no shape nodes).

    Args:
        selection_only: whether to search all scene objects or only selected ones
        dag: whether to only return DAG nodes or not

    Returns:
        List of group nodes (empty transform nodes) in the scene.
    """

    objs_list: list[str] = []
    group_list: list[str] = []

    if selection_only:
        objs_list = cmds.ls(selection=True, long=True)
        if not objs_list:
            logger.warning("Nothing is selected, please select at least one object!")
            return []

    obj_transforms = filter_nodes_by_type(
        filter_types=TYPE_FILTERS[TRANSFORM_FILTER_TYPE],
        objs_list=objs_list,
        search_scene=not selection_only,
        dag=dag,
    )
    if not obj_transforms:
        logger.warning("No groups found!")
        return []

    # We check again to avoid not wanted transforms (such as joints, or shape nodes).
    for obj in obj_transforms:
        if not cmds.listRelatives(obj, shapes=True) and cmds.objectType(
            obj, isType="transform"
        ):
            group_list.append(obj)

    return group_list


def filter_dag_transforms(
    filter_types: list[str],
    selection_only: bool = True,
    dag: bool = False,
    transforms_only: bool = True,
):
    """Returns a list of Maya nodes that match filter type and returns only
    transform parent of shape nodes.

    Args:
        filter_types: list of node types to filter by.
        selection_only: whether to search all scene objects or only selected ones.
        dag: whether to return only DAG nodes.
        transforms_only: whether to return only transform nodes or not.

    Returns:
        List of filtered DAG transform nodes.
    """

    if selection_only:
        sel_objs = cmds.ls(selection=True, long=True)
        if not sel_objs:
            logger.warning("No objects selected. Please select at least one!")
            return []
        found_shape_names = cmds.listRelatives(sel_objs, shapes=True, fullPath=True)
        if found_shape_names:
            sel_objs += found_shape_names
        filtered_shapes = filter_nodes_by_type(
            filter_types=filter_types,
            objs_list=sel_objs,
            dag=dag,
        )
    else:
        filtered_shapes = filter_nodes_by_type(
            filter_types=filter_types,
            search_scene=True,
            dag=dag,
        )

    return filtered_shapes if not transforms_only else filter_shapes(filtered_shapes)


def filter_by_type(
    filter_type: str,
    search_hierarchy: bool = False,
    selection_only: bool = True,
    dag: bool = False,
    remove_maya_defaults: bool = True,
    transforms_only: bool = True,
    include_constraints: bool = True,
    keep_order: bool = False,
):
    """Returns a list of objects that match the given node type.
    This function allows:
        - Filter by a list of node types.
        - Filter by special node types (such as "groups", which does not have
            a node type name).
        - Can limit the filter to an object list or override to search
            the whole scene.
        - Can include the hierarchy of the objects to search.
        - Can limit the returned list to transforms that will replace
            any shape nodes.
        - Can ignore Maya default nodes, such as lambert1 and persp.

    Notes:
        - Filter types include types that are not Maya object types such
            as "Groups" and "All types'.
        - Some types are multiple object types, "Light" for example will
            find many node types.

    Args:
        filter_type: Type that describes a node type in Maya. This should
            match a string from the TYPE_FILTERS keys.
        search_hierarchy: Whether to search objects in hierarchies.
        selection_only: Whether to search all scene objects or only selected
            ones in the scene.
        dag: Whether to return only DAG nodes.
        remove_maya_defaults: Whether to ignore Maya default nodes.
        transforms_only: Whether to return only transform nodes.
        include_constraints: Whether to include constraints in the
            returned list.
        keep_order: Whether to take into account the order of selection
            and hierarchy.

    Returns:
        List of node names in Maya that matches the given criteria.

    Raises:
        ValueError: If the filter type is not found in the TYPE_FILTERS
            dictionary.
    """

    search_hierarchy = search_hierarchy if selection_only else False

    obj_type_list = TYPE_FILTERS.get(filter_type, None)
    if obj_type_list is None:
        raise ValueError(f"Unknown filter type: {filter_type}")

    if keep_order:
        if selection_only:
            sel_objs = cmds.ls(selection=True, long=True, dagObjects=search_hierarchy)
            filtered_result = filter_by_type(
                filter_type=filter_type,
                search_hierarchy=search_hierarchy,
                selection_only=selection_only,
                dag=dag,
                remove_maya_defaults=remove_maya_defaults,
                transforms_only=transforms_only,
                include_constraints=include_constraints,
                keep_order=False,
            )
            remove_result = [obj for obj in sel_objs if obj not in filtered_result]
            return [obj for obj in sel_objs if obj not in remove_result]
        else:
            return filter_by_type(
                filter_type=filter_type,
                search_hierarchy=search_hierarchy,
                selection_only=selection_only,
                dag=dag,
                remove_maya_defaults=remove_maya_defaults,
                transforms_only=transforms_only,
                keep_order=False,
            )
    else:
        if obj_type_list[0] == ALL_SPECIAL:
            return filter_all_node_types(
                selection_only=selection_only,
                transforms_only=transforms_only,
                dag=dag,
                remove_maya_defaults=remove_maya_defaults,
            )
        elif obj_type_list[0] == GROUP_SPECIAL:
            return filter_by_group(
                selection_only=selection_only,
                dag=dag,
            )
        else:
            return filter_dag_transforms(
                filter_types=obj_type_list,
                selection_only=selection_only,
                dag=dag,
            )
