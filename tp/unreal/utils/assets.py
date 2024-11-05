from __future__ import annotations

import unreal


def asset_exists(asset_path: str) -> bool:
    """
    Returns whether given asset path exists.

    :param str asset_path: asset path of the asset.
    :return: Whether given asset path exists or not.
    """

    return unreal.EditorAssetLibrary.does_asset_exist(asset_path)
