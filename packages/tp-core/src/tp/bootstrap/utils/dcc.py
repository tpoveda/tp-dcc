from __future__ import annotations

import sys
import importlib.util
from typing import Any
from pathlib import Path
from dataclasses import dataclass, field

from functools import lru_cache

from loguru import logger


class DccRegistry(type):
    """Custom metaclass for DCC classes that auto-registers DCC classes."""

    registry = {}

    def __new__(cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any]):
        """Create a new DCC class and register it in the registry.

        This method is called when a new class is created. It checks if the
        class is not the base class and if it has a 'name' attribute. If so,
        it registers the class in the registry dictionary with the name as
        the key and the class itself as the value.

        Args:
            name: Name of the class being created.
            bases: Tuple of base classes for the new class.
            namespace: Dictionary of attributes and methods for the new class.
        """

        new_cls = super().__new__(cls, name, bases, namespace)
        if name != "DccBase" and hasattr(new_cls, "name"):
            cls.registry[new_cls.name] = new_cls

        return new_cls


@dataclass
class DccBase(metaclass=DccRegistry):
    """Base class for DCC implementations."""

    name: str = field(init=False)
    display_name: str = field(init=False)
    package: str = field(init=False)
    executables: list[str] = field(init=False)

    @classmethod
    def get_default_executable(cls):
        """Returns the default executable for the DCC.

        Returns:
            Default executable for the DCC.
        """

        # noinspection PyTypeChecker
        return cls.executables[0] if cls.executables else None


class DccBlender(DccBase):
    """Blender DCC implementation."""

    name = "blender"
    display_name = "Blender"
    package = "bpy"
    executables = ["blender"]


class DccHoudini(DccBase):
    """Houdini DCC implementation."""

    name = "houdini"
    display_name = "Houdini"
    package = "hou"
    executables = ["houdini"]


class DccMaya(DccBase):
    """Maya DCC implementation."""

    name = "maya"
    display_name = "Maya"
    package = "maya"
    executables = ["maya", "mayabatch", "mayapy"]


class DccMotionBuilder(DccBase):
    """MotionBuilder DCC implementation."""

    name = "mobu"
    display_name = "MotionBuilder"
    package = "pyfbsdk"
    executables = ["motionbuilder"]


class DccSubstanceDesigner(DccBase):
    """Substance Designer DCC implementation."""

    name = "designer"
    display_name = "Substance Designer"
    package = "sd"
    executables = ["designer", "Adobe Substance 3D Designer.exe"]


class DccSubstancePainter(DccBase):
    """Substance Painter DCC implementation."""

    name = "painter"
    display_name = "Substance Painter"
    package = "substance_painter"
    executables = ["painter", "Adobe Substance 3D Painter.exe"]


class DccUnreal(DccBase):
    """Unreal implementation."""

    name = "unreal"
    display_name = "Unreal"
    package = "unreal"
    executables = ["UnrealEditor.exe", "UnrealEditor"]


class DccStandalone(DccBase):
    """Standalone implementation."""

    name = "standalone"
    display_name = "Standalone"
    package = "standalone"
    executables = []


Standalone = DccStandalone.name
Maya = DccMaya.name
MotionBuilder = DccMotionBuilder.name
Houdini = DccHoudini.name
Unreal = DccUnreal.name
SubstancePainter = DccSubstancePainter.name
SubstanceDesigner = DccSubstanceDesigner.name
Blender = DccBlender.name


@lru_cache(maxsize=1)
def current_dcc() -> str:
    """Returns the name of the current DCC being used.

    Returns:
        DCC being used.
    """

    # Detect DCC from executable.
    for dcc_name, dcc_cls in DccRegistry.registry.items():
        current_executable = Path(sys.executable).stem.lower()
        matches = any(exe.lower() == current_executable for exe in dcc_cls.executables)
        if matches:
            logger.debug(f"Detected DCC from executable: {dcc_name}")
            return dcc_name

    # Detect DCC from the package.
    for dcc_name, dcc_cls in DccRegistry.registry.items():
        try:
            if dcc_cls.package and importlib.util.find_spec(dcc_cls.package):
                logger.debug(f"Detected DCC from package: {dcc_name}")
                return dcc_name
        except (ImportError, ValueError) as e:
            logger.debug(f"Could not find spec for {dcc_cls.package}: {e}")
            continue

    return Standalone


def is_standalone() -> bool:
    """Checks if the current environment is standalone or not.

    Returns:
        True if the current environment is standalone; False otherwise.
    """

    return current_dcc() == Standalone


def is_maya() -> bool:
    """Checks if Maya is available or not.

    Returns:
        True if the current environment is Autodesk Maya; False otherwise.
    """

    return current_dcc() == Maya


def is_mayapy() -> bool:
    """Checks if MayaPy is available or not.

    Returns:
        True if the current environment is Autodesk MayaPy; False otherwise.
    """

    return is_maya() and "mayapy" in Path(sys.executable).stem.lower()


def is_mobu() -> bool:
    """Checks if MotionBuilder is available or not.

    Returns:
        True if the current environment is Autodesk MotionBuilder; False otherwise.
    """

    return current_dcc() == MotionBuilder


def is_houdini() -> bool:
    """Checks if Houdini is available or not.

    Returns:
        True if the current environment is SideFX Houdini; False otherwise.
    """

    return current_dcc() == Houdini


def is_unreal() -> bool:
    """Checks if Houdini is available or not.

    Returns:
        True if the current environment is Epic Games Unreal Engine; False
        otherwise.
    """

    return current_dcc() == Unreal


def is_substance_painter() -> bool:
    """Checks if Substance Painter is available or not.

    Returns:
        True if the current environment is Adobe Substance Painter; False
        otherwise.
    """

    return current_dcc() == SubstancePainter


def is_substance_designer() -> bool:
    """Checks if Substance Designer is available or not.

    Returns:
        True if the current environment is Adobe Substance Designer; False
        otherwise.
    """

    return current_dcc() == SubstanceDesigner


def is_blender() -> bool:
    """Checks if Blender is available or not.

    Returns:
        True if the current environment is Blender; False otherwise.
    """

    return current_dcc() == Blender
