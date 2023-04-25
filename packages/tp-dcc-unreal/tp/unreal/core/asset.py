#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with Unreal assets
"""

import unreal


def asset_exists(asset_path):
    """
    Returns whet her or not given asset path exists
    :param asset_path: str
    :return: bool
    """

    return unreal.EditorAssetLibrary.does_asset_exist(asset_path)


def get_unique_name(asset_path, suffix=''):
    """
    Returns a unique name for the asset in the given path
    :param asset_path: str
    :param suffix: str
    :return: tuple(str, str), tuple containing asset path and name
    """

    return unreal.AssetToolsHelpers.get_asset_tools().create_unique_asset_name(
        base_package_name=asset_path, suffix=suffix)


def get_assets(assets_path, recursive=False, only_on_disk=False):
    """
    Returns all assets located in the given path
    :param assets_path: str
    :param recursive: bool
    :param only_on_disk: bool
    :return: list(unreal.AssetData)
    """

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

    return asset_registry.get_assets_by_path(assets_path, recursive=recursive, include_only_on_disk_assets=only_on_disk)


def get_asset_data(asset_path, only_on_disk=False):
    """
    Returns AssetData of the asset located in the given path
    :param asset_path: str
    :param only_on_disk: bool
    :return: unreal.AssetData or None
    """

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

    return asset_registry.get_asset_by_object_path(asset_path, include_only_on_disk_assets=only_on_disk)


def get_asset(asset_path, only_on_disk=False):
    """
    Returns instance of an existent asset
    :param asset_path: str
    :param only_on_disk: bool), if True, in-memory objects will be ignored. The call will be faster.
    :return: unreal.AssetData or None
    """

    asset_data = get_asset_data(asset_path, only_on_disk=only_on_disk)
    if not asset_data:
        return None

    full_name = asset_data.get_full_name()
    path = full_name.split(' ')[-1]

    return unreal.load_asset(path)


def create_asset(asset_path='', unique_name=True, asset_class=None, asset_factory=None, **kwargs):
    """
    Creates a a new Unreal asset
    :param asset_path: str
    :param unique_name: str
    :param asset_class: cls
    :param asset_factory: cls
    :param kwargs: dict
    :return:
    """

    if unique_name:
        asset_path, asset_name = get_unique_name(asset_path)
    if not asset_exists(asset_path):
        path = asset_path.rsplit('/', 1)[0]
        name = asset_path.rsplit('/', 1)[1]
        return unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            asset_name=name, package_path=path, asset_class=asset_class, factory=asset_factory, **kwargs)

    return unreal.load_asset(asset_path)
