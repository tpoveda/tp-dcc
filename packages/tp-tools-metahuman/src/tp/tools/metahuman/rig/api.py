"""MetaHuman Body Rig Builder API.

This module provides a high-level, typed API for building and managing MetaHuman
body rigs. It serves as the primary interface for external tools and scripts
to interact with the rig building system.

Example Usage:
    >>> from tp.tools.metahuman.rig.api import RigAPI, RigOptions
    >>>
    >>> # Create options
    >>> options = RigOptions(motion=True, use_space_switch=True)
    >>>
    >>> # Build the rig
    >>> result = RigAPI.build(options)
    >>> if result.success:
    ...     print(f"Rig built successfully: {result.message}")
    ...
    >>> # Or use the simplified builder
    >>> result = RigAPI.build_quick(motion=True)
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    Tuple,
    Union,
)

from .body_rig_builder import MetaHumanBodyRigBuilder, RigBuildResult
from .builders import (
    ControlBuilder,
    FingerControlBuilder,
    FKIKSwitchBuilder,
    ReverseFootBuilder,
    SkeletonBuilder,
    SpaceSwitchBuilder,
)
from .data.skeleton_config import (
    Color,
    RigColors,
    RigType,
    Side,
)

__all__ = [
    # Main API
    "RigAPI",
    # Options and configuration
    "RigOptions",
    "BuildMode",
    "ProgressInfo",
    # Results
    "RigBuildResult",
    "ValidationResult",
    # Types
    "ProgressCallback",
    # Re-exports for convenience
    "Side",
    "RigType",
    "RigColors",
    "Color",
]

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Type Definitions
# -----------------------------------------------------------------------------


class ProgressCallback(Protocol):
    """Protocol for progress callback functions.

    Progress callbacks receive the current progress percentage (0.0 to 100.0)
    and a descriptive message about the current operation.
    """

    def __call__(self, percent: float, message: str) -> None:
        """Called when progress is updated.

        Args:
            percent: Progress percentage from 0.0 to 100.0.
            message: Descriptive message about current operation.
        """
        ...


# -----------------------------------------------------------------------------
# Enumerations
# -----------------------------------------------------------------------------


class BuildMode(Enum):
    """Enumeration for rig build modes."""

    MOTION = auto()
    """Build motion skeleton with animation controls."""

    IN_PLACE = auto()
    """Build controls for existing skeleton without motion skeleton."""

    PREVIEW = auto()
    """Preview mode - validate and report but don't modify scene."""


# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------


@dataclass
class ProgressInfo:
    """Information about build progress.

    Attributes:
        percent: Progress percentage from 0.0 to 100.0.
        message: Descriptive message about current operation.
        stage: Current build stage name.
        is_complete: Whether the build is complete.
    """

    percent: float
    message: str
    stage: str = ""
    is_complete: bool = False

    def __post_init__(self) -> None:
        """Validate progress values."""
        self.percent = max(0.0, min(100.0, self.percent))


@dataclass
class RigOptions:
    """Configuration options for building a MetaHuman body rig.

    This dataclass contains all configurable options for the rig building
    process. It can be serialized to/from JSON for persistent configuration.

    Attributes:
        motion: If True, create motion skeleton for animation.
        build_mode: The build mode to use (MOTION, IN_PLACE, or PREVIEW).
        use_space_switch: If True, create space switch systems.
        create_finger_controls: If True, create finger curl controls.
        create_reverse_foot: If True, create reverse foot setup.
        create_fkik_switches: If True, create FK/IK switching systems.
        colors: Color configuration for controls.
        namespace: Optional namespace for rig elements.
        scale: Global scale factor for controls.
        left_side_color: Override color for left side controls.
        right_side_color: Override color for right side controls.
        center_color: Override color for center controls.
        global_color: Override color for global control.
        custom_data: Dictionary for storing custom user data.
    """

    # Core options
    motion: bool = True
    build_mode: BuildMode = BuildMode.MOTION
    use_space_switch: bool = True
    create_finger_controls: bool = True
    create_reverse_foot: bool = True
    create_fkik_switches: bool = True

    # Appearance options
    namespace: str = ""
    scale: float = 1.0

    # Color overrides (None means use default)
    left_side_color: Optional[Color] = None
    right_side_color: Optional[Color] = None
    center_color: Optional[Color] = None
    global_color: Optional[Color] = None

    # Custom data for extensions
    custom_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate options after initialization."""
        if self.scale <= 0:
            raise ValueError("scale must be a positive number")
        if self.build_mode == BuildMode.MOTION:
            self.motion = True
        elif self.build_mode == BuildMode.IN_PLACE:
            self.motion = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert options to a JSON-serializable dictionary.

        Returns:
            Dictionary representation of the options.
        """
        data = asdict(self)

        # Convert enums to their names
        data["build_mode"] = self.build_mode.name

        # Convert Color objects to dict
        for color_key in [
            "left_side_color",
            "right_side_color",
            "center_color",
            "global_color",
        ]:
            if data[color_key] is not None:
                color = getattr(self, color_key)
                data[color_key] = {"r": color.r, "g": color.g, "b": color.b}

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RigOptions":
        """Create RigOptions from a dictionary.

        Args:
            data: Dictionary with option values.

        Returns:
            New RigOptions instance.
        """
        # Handle build_mode enum
        build_mode = data.get("build_mode", "MOTION")
        if isinstance(build_mode, str):
            build_mode = BuildMode[build_mode]

        # Handle color conversions
        color_fields = [
            "left_side_color",
            "right_side_color",
            "center_color",
            "global_color",
        ]
        colors: Dict[str, Optional[Color]] = {}
        for color_key in color_fields:
            color_data = data.get(color_key)
            if color_data is not None and isinstance(color_data, dict):
                colors[color_key] = Color(
                    r=color_data["r"], g=color_data["g"], b=color_data["b"]
                )
            else:
                colors[color_key] = None

        return cls(
            motion=bool(data.get("motion", True)),
            build_mode=build_mode,
            use_space_switch=bool(data.get("use_space_switch", True)),
            create_finger_controls=bool(
                data.get("create_finger_controls", True)
            ),
            create_reverse_foot=bool(data.get("create_reverse_foot", True)),
            create_fkik_switches=bool(data.get("create_fkik_switches", True)),
            namespace=str(data.get("namespace", "")),
            scale=float(data.get("scale", 1.0)),
            left_side_color=colors["left_side_color"],
            right_side_color=colors["right_side_color"],
            center_color=colors["center_color"],
            global_color=colors["global_color"],
            custom_data=dict(data.get("custom_data", {})),
        )

    def copy(self, **overrides: Any) -> "RigOptions":
        """Create a copy of these options with optional overrides.

        Args:
            **overrides: Values to override in the copy.

        Returns:
            New RigOptions instance with overrides applied.
        """
        data = self.to_dict()
        data.update(overrides)
        return RigOptions.from_dict(data)


@dataclass
class ValidationResult:
    """Result of options validation.

    Attributes:
        is_valid: Whether the options are valid.
        errors: List of validation error messages.
        warnings: List of validation warning messages.
    """

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        """Return True if validation passed."""
        return self.is_valid


# -----------------------------------------------------------------------------
# Main API Class
# -----------------------------------------------------------------------------


class RigAPI:
    """High-level API for building and managing MetaHuman body rigs.

    This class provides static methods for all rig-related operations,
    including building, validation, serialization, and querying.

    Example:
        >>> from tp.tools.metahuman.rig.api import RigAPI, RigOptions
        >>>
        >>> # Quick build with defaults
        >>> result = RigAPI.build_quick()
        >>>
        >>> # Build with custom options
        >>> options = RigOptions(motion=True, scale=1.5)
        >>> result = RigAPI.build(options)
        >>>
        >>> # Build with progress callback
        >>> def on_progress(percent: float, message: str) -> None:
        ...     print(f"{percent:.0f}% - {message}")
        ...
        >>> result = RigAPI.build(options, progress=on_progress)
    """

    # Default option presets
    PRESET_ANIMATION = RigOptions(motion=True, build_mode=BuildMode.MOTION)
    PRESET_LAYOUT = RigOptions(motion=False, build_mode=BuildMode.IN_PLACE)

    # -------------------------------------------------------------------------
    # Build Methods
    # -------------------------------------------------------------------------

    @staticmethod
    def build(
        options: Optional[RigOptions] = None,
        progress: Optional[ProgressCallback] = None,
    ) -> RigBuildResult:
        """Build a MetaHuman body rig with the specified options.

        This is the main entry point for building rigs. It creates a complete
        animation rig including controls, constraints, and systems.

        Args:
            options: Build options. Uses defaults if None.
            progress: Optional callback for progress updates.

        Returns:
            RigBuildResult with build status and information.

        Raises:
            ValueError: If options validation fails.
            RuntimeError: If build fails due to scene issues.

        Example:
            >>> options = RigOptions(motion=True)
            >>> result = RigAPI.build(options)
            >>> if result.success:
            ...     print(f"Created {len(result.controls_created)} controls")
        """
        if options is None:
            options = RigOptions()

        # Validate options first.
        validation = RigAPI.validate_options(options)
        if not validation.is_valid:
            error_msg = "; ".join(validation.errors)
            raise ValueError(f"Invalid RigOptions: {error_msg}")

        # Log warnings.
        for warning in validation.warnings:
            logger.warning(warning)

        # Handle preview mode.
        if options.build_mode == BuildMode.PREVIEW:
            logger.info("Preview mode: validating without building")
            return RigBuildResult(
                success=True,
                message="Preview validation passed. No changes made.",
            )

        # Report initial progress.
        if progress:
            progress(0.0, "Initializing rig builder...")

        logger.debug("Starting rig build with options: %s", options)

        try:
            # Create and configure builder.
            builder = MetaHumanBodyRigBuilder(motion=options.motion)

            # Execute build.
            if progress:
                progress(10.0, "Building rig structure...")

            result = builder.build()

            if progress:
                progress(100.0, "Build complete!")

            logger.info("Rig build completed: %s", result.message)
            return result

        except Exception as e:
            logger.exception("Rig build failed")
            return RigBuildResult(
                success=False,
                message=f"Build failed: {e}",
            )

    @staticmethod
    def build_quick(
        motion: bool = True,
        progress: Optional[ProgressCallback] = None,
    ) -> RigBuildResult:
        """Build a rig with default options.

        This is a convenience method for quick rig building without
        explicitly creating RigOptions.

        Args:
            motion: If True, create motion skeleton. Default True.
            progress: Optional callback for progress updates.

        Returns:
            RigBuildResult with build status and information.

        Example:
            >>> # Quick build for animation
            >>> result = RigAPI.build_quick()
            >>>
            >>> # Quick build for layout
            >>> result = RigAPI.build_quick(motion=False)
        """

        options = RigOptions(
            motion=motion,
            build_mode=BuildMode.MOTION if motion else BuildMode.IN_PLACE,
        )
        return RigAPI.build(options, progress=progress)

    # -------------------------------------------------------------------------
    # Validation Methods
    # -------------------------------------------------------------------------

    @staticmethod
    def validate_options(options: RigOptions) -> ValidationResult:
        """Validate rig build options.

        Checks that all option values are valid and consistent.

        Args:
            options: Options to validate.

        Returns:
            ValidationResult with validation status and messages.

        Example:
            >>> options = RigOptions(scale=-1)  # Invalid
            >>> result = RigAPI.validate_options(options)
            >>> if not result.is_valid:
            ...     print(result.errors)
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Validate scale
        if not isinstance(options.scale, (int, float)):
            errors.append("scale must be a number")
        elif options.scale <= 0:
            errors.append("scale must be a positive number")

        # Validate namespace
        if options.namespace and not isinstance(options.namespace, str):
            errors.append("namespace must be a string")
        elif options.namespace and " " in options.namespace:
            errors.append("namespace cannot contain spaces")

        # Validate build_mode
        if not isinstance(options.build_mode, BuildMode):
            errors.append("build_mode must be a BuildMode enum value")

        # Check for mode/motion consistency
        if options.build_mode == BuildMode.MOTION and not options.motion:
            warnings.append(
                "build_mode is MOTION but motion=False; motion will be enabled"
            )
        elif options.build_mode == BuildMode.IN_PLACE and options.motion:
            warnings.append(
                "build_mode is IN_PLACE but motion=True; motion will be disabled"
            )

        # Validate colors
        for color_name in [
            "left_side_color",
            "right_side_color",
            "center_color",
            "global_color",
        ]:
            color = getattr(options, color_name)
            if color is not None and not isinstance(color, Color):
                errors.append(f"{color_name} must be a Color instance or None")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    @staticmethod
    def validate_scene() -> ValidationResult:
        """Validate the current Maya scene for rig building.

        Checks that a valid MetaHuman skeleton exists and the scene
        is ready for rig building.

        Returns:
            ValidationResult with validation status and messages.

        Example:
            >>> result = RigAPI.validate_scene()
            >>> if not result.is_valid:
            ...     print("Scene is not ready:", result.errors)
        """
        errors: List[str] = []
        warnings: List[str] = []

        try:
            # Try to detect skeleton
            builder = SkeletonBuilder()
            root, suffix = builder.detect_skeleton_type()

            if not root:
                errors.append(
                    "No valid MetaHuman skeleton found in scene. "
                    "Please ensure a MetaHuman character is loaded."
                )
            else:
                logger.debug(
                    "Found skeleton root: %s (suffix: %s)", root, suffix
                )

        except Exception as e:
            errors.append(f"Error validating scene: {e}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    # -------------------------------------------------------------------------
    # Query Methods
    # -------------------------------------------------------------------------

    @staticmethod
    def list_build_modes() -> List[str]:
        """Return available build mode names.

        Returns:
            List of build mode names.

        Example:
            >>> modes = RigAPI.list_build_modes()
            >>> print(modes)  # ['MOTION', 'IN_PLACE', 'PREVIEW']
        """
        return [mode.name for mode in BuildMode]

    @staticmethod
    def list_rig_types() -> List[str]:
        """Return available rig type names (FK/IK).

        Returns:
            List of rig type names.
        """
        return [rt.name for rt in RigType]

    @staticmethod
    def list_sides() -> List[str]:
        """Return available side names.

        Returns:
            List of side names.
        """
        return [side.name for side in Side]

    @staticmethod
    def get_default_colors() -> Dict[str, Tuple[float, float, float]]:
        """Return default rig colors.

        Returns:
            Dictionary mapping color names to RGB tuples.

        Example:
            >>> colors = RigAPI.get_default_colors()
            >>> print(colors['LEFT'])  # (0.0, 0.0, 0.5)
        """
        return {
            "LEFT": RigColors.LEFT.as_tuple(),
            "LEFT_BRIGHT": RigColors.LEFT_BRIGHT.as_tuple(),
            "RIGHT": RigColors.RIGHT.as_tuple(),
            "RIGHT_BRIGHT": RigColors.RIGHT_BRIGHT.as_tuple(),
            "CENTER": RigColors.CENTER.as_tuple(),
            "GLOBAL": RigColors.GLOBAL.as_tuple(),
            "BODY": RigColors.BODY.as_tuple(),
        }

    @staticmethod
    def get_preset(name: str) -> RigOptions:
        """Get a named options preset.

        Args:
            name: Name of the preset ('animation' or 'layout').

        Returns:
            RigOptions with preset values.

        Raises:
            ValueError: If preset name is not recognized.

        Example:
            >>> options = RigAPI.get_preset('animation')
        """
        presets = {
            "animation": RigAPI.PRESET_ANIMATION,
            "layout": RigAPI.PRESET_LAYOUT,
        }

        name_lower = name.lower()
        if name_lower not in presets:
            valid = ", ".join(presets.keys())
            raise ValueError(
                f"Unknown preset '{name}'. Valid presets are: {valid}"
            )

        # Return a copy to avoid mutating the preset
        return presets[name_lower].copy()

    @staticmethod
    def list_presets() -> List[str]:
        """Return available preset names.

        Returns:
            List of preset names.
        """
        return ["animation", "layout"]

    # -------------------------------------------------------------------------
    # Serialization Methods
    # -------------------------------------------------------------------------

    @staticmethod
    def save_options(options: RigOptions, path: Union[str, Path]) -> None:
        """Save rig options to a JSON file.

        Args:
            options: Options to save.
            path: File path for the JSON file.

        Example:
            >>> options = RigOptions(motion=True, scale=1.5)
            >>> RigAPI.save_options(options, "my_rig_options.json")
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as fh:
            json.dump(options.to_dict(), fh, indent=2)

        logger.debug("Saved RigOptions to %s", path)

    @staticmethod
    def load_options(path: Union[str, Path]) -> RigOptions:
        """Load rig options from a JSON file.

        Args:
            path: Path to the JSON file.

        Returns:
            Loaded RigOptions.

        Raises:
            FileNotFoundError: If file doesn't exist.
            json.JSONDecodeError: If file is not valid JSON.

        Example:
            >>> options = RigAPI.load_options("my_rig_options.json")
            >>> result = RigAPI.build(options)
        """
        path = Path(path)

        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        options = RigOptions.from_dict(data)
        logger.debug("Loaded RigOptions from %s", path)

        return options

    @staticmethod
    def options_to_json(options: RigOptions) -> str:
        """Convert options to a JSON string.

        Args:
            options: Options to convert.

        Returns:
            JSON string representation.

        Example:
            >>> options = RigOptions(motion=True)
            >>> json_str = RigAPI.options_to_json(options)
        """
        return json.dumps(options.to_dict(), indent=2)

    @staticmethod
    def options_from_json(json_str: str) -> RigOptions:
        """Create options from a JSON string.

        Args:
            json_str: JSON string representation.

        Returns:
            RigOptions instance.

        Example:
            >>> json_str = '{"motion": true, "scale": 1.5}'
            >>> options = RigAPI.options_from_json(json_str)
        """
        data = json.loads(json_str)
        return RigOptions.from_dict(data)

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    @staticmethod
    def get_version() -> str:
        """Return the API version.

        Returns:
            Version string in semver format.
        """
        return "1.0.0"

    @staticmethod
    def get_builders() -> Dict[str, type]:
        """Return available builder classes.

        Returns:
            Dictionary mapping builder names to classes.

        Example:
            >>> builders = RigAPI.get_builders()
            >>> for name, cls in builders.items():
            ...     print(f"{name}: {cls.__name__}")
        """
        return {
            "control": ControlBuilder,
            "skeleton": SkeletonBuilder,
            "reverse_foot": ReverseFootBuilder,
            "space_switch": SpaceSwitchBuilder,
            "finger": FingerControlBuilder,
            "fkik_switch": FKIKSwitchBuilder,
        }
