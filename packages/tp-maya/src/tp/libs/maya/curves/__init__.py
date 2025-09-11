from __future__ import annotations

import os
import glob
import pathlib
from typing import Any
from enum import IntEnum, auto
from collections.abc import Generator

from loguru import logger
import maya.api.OpenMaya as OpenMaya

from tp.libs.python import helpers, jsonio, paths
from tp.libs.maya.om import scene, nodes, curves

CURVE_FILE_EXTENSION = "curve"
CURVES_ENV_VAR = "TP_DCC_CURVES_PATHS"
_PATHS_CACHE: dict[str, dict] = {}


class ShapeType(IntEnum):
    """Enumeration of shape types."""

    Curve = auto()
    Surface = auto()


class MissingCurveFromLibrary(Exception):
    """Exception that is raised when a curve is not found in the library."""

    pass


def update_cache(force: bool = False) -> None:
    """Handle the update of cached curves.

    Args:
        force: Whether to force the update of the cache event if the cache is
            already initialized.
    """

    global _PATHS_CACHE

    if _PATHS_CACHE and not force:
        return

    for root in iterate_root_paths():
        for shape_path in glob.glob(
            pathlib.Path(root, "*.{}".format(CURVE_FILE_EXTENSION)).as_posix()
        ):
            _PATHS_CACHE[os.path.splitext(os.path.basename(shape_path))[0]] = {
                "path": shape_path
            }


def clear_cache() -> None:
    """Clears the cache of available curves."""

    global _PATHS_CACHE

    _PATHS_CACHE.clear()


def default_curves_library_path() -> str:
    """Return the default curves library path.

    Returns:
        The default curves library path.
    """

    return paths.canonical_path("./library")


def iterate_root_paths() -> Generator[str]:
    """Iterate over all root locations defined by `TP_DCC_CURVES_PATHS`
    environment variable.

    Yields:
        Root paths.
    """

    for root in [default_curves_library_path()] + os.environ.get(
        CURVES_ENV_VAR, ""
    ).split(os.pathsep):
        if not root or not os.path.exists(root):
            continue
        yield root


def root_paths() -> list[str]:
    """Returns a list of all root locations defined by `TP_DCC_CURVES_PATHS`
    environment variable.

    Returns:
        List of root paths.
    """

    return list(iterate_root_paths())


def iterate_curve_paths() -> Generator[str]:
    """Iterate over all curve paths.

    Yields:
        Curve paths.
    """

    update_cache()
    for curve_info in _PATHS_CACHE.values():
        yield curve_info["path"]


def curve_paths() -> list[str]:
    """Returns a list of all curve paths.

    Returns:
        List of curve paths.
    """

    return list(iterate_curve_paths())


def iterate_names() -> Generator[str]:
    """Iterate over all available curve names.

    Notes:
        - Curves are sourced from all the root locations specified by the
            CURVES_ENV_VAR environment variable.

    Yields:
        Curve names.
    """

    update_cache()
    for curve_name in _PATHS_CACHE.keys():
        yield curve_name


def names() -> list[str]:
    """Returns a list of all available curve names.

    Notes:
        - Curves are sourced from all the root locations specified by the
            CURVES_ENV_VAR environment variable.

    Returns:
        List of curve names.
    """

    return list(iterate_names())


def find_curve_path_by_name(curve_name: str) -> str | None:
    """Return the curve path of the curve with the given name.

    Args:
        curve_name: Name of the curve we want to retrieve path of.

    Returns:
        Curve path.
    """

    update_cache()

    if not _PATHS_CACHE:
        return None

    return _PATHS_CACHE.get(curve_name, dict()).get("path", "")


def load_curve(curve_name: str, folder_path: str) -> dict:
    """Load the curve with the given name and located in the given directory.

    Args:
        curve_name: Name of the curve to load.
        folder_path: Absolute directory where the curve file is located.

    Returns:
        Loaded curve data.
    """

    curve_path = pathlib.Path(
        folder_path, ".".join([curve_name, CURVE_FILE_EXTENSION])
    ).as_posix()
    return jsonio.read_file(curve_path)


def load_from_lib(curve_name: str) -> dict[str, Any]:
    """Load the data from the given curve name in the library.

    Args:
        curve_name: Name of the curve to load data of.

    Returns:
        Curve data.

    Raises:
        MissingCurveFromLibrary: If the given curve name does not exist in the
            library of curves.
    """

    update_cache()

    curve_data = _PATHS_CACHE.get(curve_name)
    if not curve_data:
        raise MissingCurveFromLibrary(
            f"Curve name {curve_name} does not exist in the library"
        )

    data = curve_data.get("data")
    if not data:
        data = jsonio.read_file(curve_data["path"])
        curve_data["data"] = data

    return data


def load_and_create_from_lib(
    curve_name: str,
    parent: OpenMaya.MObject | None = None,
    shape_type: ShapeType = ShapeType.Curve,
    mod: OpenMaya.MDGModifier | None = None,
) -> tuple[OpenMaya.MObject, list[OpenMaya.MObject]]:
    """Load and create the curve from the curve library. If a parent is
    given, the shape node will be parented under it.

    Args:
        curve_name: Curve library name to load and create.
        parent: Optional curve parent.
        shape_type: Type of shape to create.
        mod: Optional MDGModifier to use to create the curve.

    Returns:
        Tuple with the MObject of the parent and a list representing the
            MObjects of the created shapes.
    """

    new_data = load_from_lib(curve_name)

    if shape_type == ShapeType.Curve:
        return curves.create_curve_shape(new_data, parent=parent, mod=mod)

    return curves.create_curve_surface(new_data, parent=parent, mod=mod)


def load_and_create_from_path(
    curve_name: str, folder_path: str, parent: OpenMaya.MObject | None = None
) -> tuple[OpenMaya.MObject | None, list[OpenMaya.MObject]]:
    """Load and create the NURBS curve from the file located in the given path.

    Args:
        curve_name: Name of the curve to load and create.
        folder_path: Absolute directory where the curve file is located.
        parent: Optional parent for the NURBS curve to parent under.

    Returns:
        Tuple containing the MObject of the parent and a list of MObjects
            representing the created shapes.
    """

    curve_data = load_curve(curve_name, folder_path)
    shape_type = ShapeType(curve_data.get("shapeType", ShapeType.Curve))
    if shape_type == ShapeType.Curve:
        return curves.create_curve_shape(curve_data, parent=parent)

    return curves.create_curve_surface(curve_data, parent=parent)


def save_to_directory(
    node: OpenMaya.MObject,
    directory: str,
    name: str | None,
    override: bool = True,
    save_matrix: bool = False,
    normalize: bool = True,
    shape_type: ShapeType = ShapeType.Curve,
) -> tuple[dict, str]:
    """Save the given transform node into the given directory.

    Args:
        node: Maya object representing the transform node to save curves of.
        directory: absolute path where curve file will be saved.
        name: name of the file to create. If not given, the name of the node
            will be used.
        override: whether to force override the library shape if it already
            exists.
        save_matrix: whether to save matrix information.
        normalize: whether to normalize curve data, so it fits in first Maya
            grid-quadrant.
        shape_type: Type of shape to save.

    Returns:
        Tuple containing the save curve data and the save path.

    Raises:
        ValueError: if we try to save a curve that already exists and override
            argument is `False`
    """

    name = name or nodes.name(node, partial_name=True, include_namespace=False)
    name = (
        name
        if name.endswith(f".{CURVE_FILE_EXTENSION}")
        else ".".join([name, CURVE_FILE_EXTENSION])
    )
    if not override and name in names():
        raise ValueError(
            f'Curve with name "{name}" already exists in the curves library!'
        )

    if shape_type == ShapeType.Curve:
        data = curves.serialize_transform_curve(node, normalize=normalize)
    else:
        data = curves.serialize_transform_surface(node, normalize=normalize)

    if not save_matrix:
        for curves_shape in data:
            data[curves_shape].pop("matrix", None)

    save_path = pathlib.Path(directory, name).as_posix()

    jsonio.write_to_file(data, save_path)
    _PATHS_CACHE[os.path.splitext(name)[0]] = {"path": save_path, "data": data}

    return data, save_path


def save_to_lib(
    node: OpenMaya.MObject | None = None,
    name: str | None = None,
    override: bool = True,
    save_matrix: bool = False,
    normalize: bool = True,
    shape_type: ShapeType = ShapeType.Curve,
) -> tuple[dict, str]:
    """Save the given transform node shapes into the curve library, using the
    first library directory defined within the `CURVES_ENV_VAR` environment
    variable.

    Args:
        node: Maya object representing the transform node to save curves of.
        name: name of the file to create. If not given, the name of the node
            will be used.
        override: whether to force override the library shape if it already
            exists.
        save_matrix: whether to save matrix information.
        normalize: whether to normalize curve data, so it fits in first Maya
            grid-quadrant.
        shape_type: Type of shape to save.

    Returns:
        Tuple containing the save curve data and the save path.

    Raises:
        ValueError: if no node to save curves from is given.
    """

    node = node or helpers.first_in_list(
        scene.selected_nodes(filter_to_apply=[OpenMaya.MFn.kTransform])
    )
    if not node:
        raise ValueError("No node to save curves")
    directory = os.environ.get(CURVES_ENV_VAR, "").split(os.pathsep)[0]
    directory = directory or default_curves_library_path()
    return save_to_directory(
        node,
        directory,
        name,
        override=override,
        save_matrix=save_matrix,
        normalize=normalize,
        shape_type=shape_type,
    )


def rename_curve(curve_name: str, new_name: str) -> str:
    """Rename a shape from the library, using the first library directory
    defined within the `CURVES_ENV_VAR` environment variable.

    Args:
        curve_name: name of the curve to rename.
        new_name: new curve name.

    Returns:
        New curve path.
    """

    curve_path = find_curve_path_by_name(curve_name)
    if not curve_path or not os.path.exists(curve_path):
        logger.warning(f'Curve file not found: "{curve_path}"')
        return ""

    new_path = pathlib.Path(
        os.path.dirname(curve_path), ".".join([new_name, CURVE_FILE_EXTENSION])
    ).as_posix()
    if os.path.isdir(new_path):
        logger.warning(
            f'Cannot rename curve, because filename already exists: "{new_path}"'
        )
        return ""

    os.rename(curve_path, new_path)
    old_data = _PATHS_CACHE.get(curve_name)
    old_data["path"] = new_path
    _PATHS_CACHE[new_name] = old_data
    del _PATHS_CACHE[curve_name]

    logger.info(f'Successfully renamed curve "{curve_path}" to "{new_path}"')

    return new_path


def delete_curve(curve_name: str) -> bool:
    """Delete the curve with given name from the library, using the first
    library directory defined within the `CURVES_ENV_VAR` environment variable.

    Args:
        curve_name: name of the curve to delete.

    Returns:
        `True` if the delete curve operation was successful; `False` otherwise.
    """

    curve_path = find_curve_path_by_name(curve_name)
    if not curve_path:
        logger.warning(f'Curve file not found: "{curve_path}"')
        return False

    os.remove(curve_path)

    if curve_name in _PATHS_CACHE:
        del _PATHS_CACHE[curve_name]

    return True
