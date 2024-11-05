from __future__ import annotations

import sys
import platform
from pathlib import Path
from functools import lru_cache
from importlib.util import find_spec

Standalone = "standalone"
Maya = "maya"
# noinspection SpellCheckingInspection
Max = "3dsmax"
# noinspection SpellCheckingInspection
MotionBuilder = "mobu"
Houdini = "houdini"
Nuke = "nuke"
Unreal = "unreal"
Blender = "blender"
SubstancePainter = "painter"
SubstanceDesigner = "designer"
Fusion = "fusion"

ALL = [
    Maya,
    Max,
    MotionBuilder,
    Houdini,
    Nuke,
    Unreal,
    Blender,
    SubstancePainter,
    SubstanceDesigner,
    Fusion,
]

NiceNames = dict(
    [
        (Maya, "Maya"),
        (Max, "3ds Max"),
        (MotionBuilder, "MotionBuilder"),
        (Houdini, "Houdini"),
        (Nuke, "Nuke"),
        (Unreal, "Unreal"),
        (Blender, "Blender"),
        (SubstancePainter, "SubstancePainter"),
        (SubstanceDesigner, "SubstanceDesigner"),
        (Fusion, "Fusion"),
    ]
)

# noinspection SpellCheckingInspection
Packages = dict(
    [
        ("maya", Maya),
        ("pymxs", Max),
        ("MaxPlus", Max),
        ("pyfbsdk", MotionBuilder),
        ("hou", Houdini),
        ("nuke", Nuke),
        ("unreal", Unreal),
        ("bpy", Blender),
        ("substance_painter", SubstancePainter),
        ("sd", SubstanceDesigner),
        ("fusionscript", Fusion),
        ("PeyeonScript", Fusion),
    ]
)

# TODO: Add support for both MacOS and Linux
# noinspection SpellCheckingInspection
Executables = {
    Maya: {"windows": ["maya.exe", "mayabatch.exe"]},
    Max: {"windows": ["3dsmax.exe"]},
    MotionBuilder: {"windows": ["motionbuilder.exe"]},
    Houdini: {"windows": ["houdini"]},
    Nuke: {"windows": ["Nuke"]},
    Unreal: {"windows": ["UnrealEditor.exe"]},
    Blender: {"windows": ["blender.exe"]},
    SubstancePainter: {"windows": ["painter.exe"]},
    SubstanceDesigner: {"windows": ["designer.exe"]},
    Fusion: {"windows": ["Fusion.exe"]},
}


@lru_cache()
def current_dcc() -> str:
    """
    Returns name of the current DCC being used.

    :return: DCC being used.
    :rtype: str
    """

    found_dcc: str | None = None

    found_exec = False
    platform_name = platform.system().lower()
    for dcc_name, dcc_package in Packages.items():
        if found_exec:
            break
        try:
            is_importable = bool(find_spec(dcc_package))
            if is_importable:
                # sys.executable resolves to "standalone" for blender
                if dcc_name == Blender:
                    found_dcc = Blender
                    break
                else:
                    for exec_name in Executables.get(dcc_name, {}).get(
                        platform_name, []
                    ):
                        if exec_name in sys.executable:
                            found_exec = True
                            found_dcc = dcc_name
                            break
        except (TypeError, ValueError):
            # For some reason, find_spec in Unreal raises a ValueError (unreal.__spec__ is None)
            if dcc_name == Unreal:
                for exec_name in Executables.get(dcc_name, {}).get(platform_name, []):
                    if (
                        exec_name in sys.executable
                        or exec_name.split(".")[0] in sys.executable
                    ):
                        found_dcc = dcc_name
                        break
    if not found_dcc:
        try:
            current_exe = Path(sys.executable).stem
            if current_exe == "motionbuilder":
                found_dcc = MotionBuilder
            else:
                found_dcc = Standalone
        except ImportError:
            found_dcc = Standalone

    return found_dcc


def is_standalone() -> bool:
    """
    Check if current environment is standalone or not.

    :return: True if current environment is standalone; False otherwise.
    """

    return current_dcc() == Standalone


def is_maya() -> bool:
    """
    Checks if Maya is available or not.

    :return: True if current environment is Autodesk Maya; False otherwise.
    """

    return current_dcc() == Maya


def is_mayapy() -> bool:
    """
    Checks if MayaPy is available or not.

    :return: True if current environment is Autodesk MayaPy; False otherwise.
    :rtype: bool
    """

    return is_maya() and "mayapy" in sys.executable


def is_max() -> bool:
    """
    Checks if 3ds Max is available or not.

    :return: True if current environment is Autodesk 3ds Max; False otherwise.
    """

    return current_dcc() == Max


def is_mobu() -> bool:
    """
    Checks if MotionBuilder is available or not.

    :return: True if current environment is Autodesk MotionBuilder; False otherwise.
    """

    return current_dcc() == MotionBuilder


def is_houdini() -> bool:
    """
    Checks if Houdini is available or not.

    :return: True if current environment is SideFX Houdini; False otherwise.
    """

    return current_dcc() == Houdini


def is_unreal() -> bool:
    """
    Checks if Houdini is available or not.

    :return: True if current environment is Epic Games Unreal Engine; False otherwise.
    """

    return current_dcc() == Unreal


def is_nuke() -> bool:
    """
    Checks if Nuke is available or not.

    :return: True if current environment is Nuke; False otherwise.
    """

    return current_dcc() == Nuke


def is_blender() -> bool:
    """
    Checks if Blender is available or not.

    :return: True if current environment is Blender; False otherwise.
    """

    return current_dcc() == Blender


def is_substance_painter() -> bool:
    """
    Checks if Substance Painter is available or not.

    :return: True if current environment is Adobe Substance Painter; False otherwise.
    """

    return current_dcc() == SubstancePainter


def is_substance_designer() -> bool:
    """
    Checks if Substance Designer is available or not.

    :return: True if current environment is Adobe Substance Painter; False otherwise.
    """

    return current_dcc() == SubstancePainter


def is_fusion() -> bool:
    """
    Checks if Fusion is available or not.

    :return: True if current environment is Fusion; False otherwise.
    """

    return current_dcc() == Fusion
