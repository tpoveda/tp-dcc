from __future__ import annotations

import logging

import unreal

logger = logging.getLogger(__name__)


def create_control_rig_blueprint(
    path: str,
    name: str,
    skeletal_mesh_path: str | None = None,
    modular_rig: bool = False,
) -> unreal.ControlRigBlueprint | None:
    """
    Creates a new Control Rig Blueprint asset.

    :param path: package path to the location where the new Control Rig asset will be
        created.
    :param name: name of the Control Rig asset.
    :param skeletal_mesh_path: path to the Skeletal Mesh asset that will be used as
        the Control Rig target.
    :param modular_rig: whether the Control Rig should be modular or not.
    :return: newly created Control Rig Blueprint asset.
    """

    # noinspection PyTypeChecker
    package_path = unreal.Paths.combine([path, name])

    if unreal.Paths.file_exists(package_path):
        package_path, name = (
            unreal.AssetToolsHelpers.get_asset_tools().create_unique_asset_name(path, name)
        )
        logger.error(f'Control Rig asset "{package_path}" already exists!')
        return None

    if skeletal_mesh_path:
        if not unreal.EditorAssetLibrary.does_asset_exist(skeletal_mesh_path):
            logger.error(f'Skeletal Mesh asset "{skeletal_mesh_path}" does not exist!')
            return None

    # Create Control Rig Blueprint from given Skeletal Mesh asset.
    factory = unreal.ControlRigBlueprintFactory
    if skeletal_mesh_path:
        skeletal_mesh_asset = unreal.load_asset(skeletal_mesh_path)
        blueprint = factory.create_control_rig_from_skeletal_mesh_or_skeleton(
            skeletal_mesh_asset, modular_rig=modular_rig
        )
        # Move newly created Control Rig Blueprint to the desired package path.
        moved_success = unreal.EditorAssetLibrary.rename_asset(
            blueprint.get_path_name(), package_path
        )
        if not moved_success:
            unreal.log_error(
                f"Failed to rename Control Rig Blueprint - {blueprint.get_path_name()}"
            )
            # Deletes invalid Control Rig Blueprint, which is now stale, and should not
            # exist in this location.
            unreal.EditorAssetLibrary.delete_asset(blueprint.get_path_name())
            return None
    else:
        blueprint = factory.create_new_control_rig_asset(
            package_path, modular_rig=modular_rig
        )
    if blueprint is None:
        logger.error(f"Failed to create Control Rig Blueprint: {package_path}!")
        return None

    return blueprint
