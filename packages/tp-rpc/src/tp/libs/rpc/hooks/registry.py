from __future__ import annotations

# Central registry of supported DCCs with metadata
DCC_PLUGINS: dict[str, dict[str, str]] = {
    "maya": {
        "label": "Autodesk Maya",
        "module": "tp.libs.rpc.hooks.maya",
        "headless": "false",
    },
    "unreal": {
        "label": "Unreal Engine",
        "module": "tp.libs.rpc.hooks.unreal",
        "headless": "true",
    },
    "mobu": {
        "label": "MotionBuilder",
        "module": "tp.libs.rpc.hooks.mobu",
        "headless": "false",
    },
    "hou": {
        "label": "Houdini",
        "module": "tp.libs.rpc.hooks.hou",
        "headless": "true",
    },
    "blender": {
        "label": "Blender",
        "module": "tp.libs.rpc.hooks.blender",
        "headless": "true",
    },
}


def get_supported_dccs() -> dict[str, dict[str, str]]:
    """Return the dictionary of all supported DCC types and their metadata.

    Returns:
        Mapping of DCC type → metadata dictionary.
    """

    return DCC_PLUGINS
