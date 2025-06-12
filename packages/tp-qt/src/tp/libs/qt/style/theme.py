from __future__ import annotations

import os
import enum

from loguru import logger
from Qt.QtCore import QResource
from Qt.QtWidgets import QWidget

from tp.libs.python import helpers

from . import setup, style_file_path
from ...qt import dpi


def instance() -> Theme:
    """Returns global TNN theme instance.

    Returns:
        The global Theme instance.
    """

    return Theme.instance()


class Theme:
    """Class that defines the default theme, which loads a QSS and optionally
    can modify it on runtime.

    This class manages theme colors, sizes, and styles used throughout the application.
    It provides a singleton instance for global access.
    """

    _INSTANCE: Theme | None = None

    # noinspection SpellCheckingInspection
    class Colors:
        """Class that defines available theme colors.

        This class contains color constants used throughout the application.
        Colors are defined as hexadecimal values.
        """

        MatteBlack = "#151515"
        DynamicBlack = "#1e1e1e"
        VerifiedBlack = "#242424"
        TricornBlack = "#2f2f2f"
        Jet = "#353535"
        DeadPixel = "#3a3a3a"
        PigIron = "#494949"
        BlackOak = "#4f4f4f"
        StoneColor = "#555555"
        ShadowMountain = "#575757"
        IndustrialRevolution = "#737373"
        SilverSnippet = "#8f8f8f"
        GrayWhite = "#c0c0c0"
        Quicksilver = "#a6a6a6"
        Silver = "#c0c0c0"
        Orochimaru = "#d9d9d9"
        White = "#ffffff"
        BlueDiamond = "#0664c3"
        BlueRuin = "#0070e0"
        ClearChill = "#1890ff"
        SagatPurple = "#722ed1"
        CalaBenirrasBlue = "#13c2c2"
        Luigi = "#52c41a"
        Pinkinity = "#eb2f96"
        MediumPink = "#ef5b97"
        RougeSarde = "#f5222d"
        LadduOrange = "#fa8c16"
        IsleOfSand = "#fa8c16"
        TomateConcasse = "#fa541c"
        VeteranysDayBlue = "#2f54eb"
        MootGreen = "#a0d911"
        DesertMoss = "#bd9f63"
        Beer = "#faad14"

    class Sizes(enum.Enum):
        """Enumerator that defines available theme sizes.

        These sizes are used to maintain consistent UI element dimensions
        across the application.
        """

        Default = "default"
        Tiny = "tiny"
        Small = "small"
        Medium = "medium"
        Large = "large"
        Huge = "huge"

    def __init__(self):
        super().__init__()

        self._default_qss: str = ""
        self._custom_qss: str = ""
        self._registered_rcc_resources: list[str] = []

        qss_style = style_file_path()
        if not qss_style:
            logger.warning(f'QSS file path does not exist: "{qss_style}"')
            raise RuntimeError("No QSS file found")

        setup()
        with open(qss_style, "r") as f:
            self._default_qss = f.read()

        scale_factor = dpi.dpi_multiplier()
        self._sizes: helpers.AttributeDict[str, int] = helpers.AttributeDict()
        self._sizes.update(
            {
                Theme.Sizes.Default.value: int(32 * scale_factor),
                Theme.Sizes.Tiny.value: int(18 * scale_factor),
                Theme.Sizes.Small.value: int(24 * scale_factor),
                Theme.Sizes.Medium.value: int(32 * scale_factor),
                Theme.Sizes.Large.value: int(40 * scale_factor),
                Theme.Sizes.Huge.value: int(48 * scale_factor),
            }
        )

        self._primary_color = Theme.Colors.DesertMoss
        self._info_color = Theme.Colors.ClearChill
        self._success_color = Theme.Colors.Luigi
        self._warning_color = Theme.Colors.Beer
        self._error_color = Theme.Colors.RougeSarde
        self._hyperlink_style = """
        <style>
         a {{
            text-decoration: none;
            color: {0};
        }}
        </style>""".format(self._primary_color)

    @classmethod
    def instance(cls) -> Theme:
        """Returns global theme instance.

        This is a singleton implementation that ensures only one theme
        instance exists throughout the application.

        Returns:
            The global Theme instance.
        """

        if cls._INSTANCE is None:
            cls._INSTANCE = cls()

        return cls._INSTANCE

    @property
    def sizes(self) -> helpers.AttributeDict:
        """Getter method that returns available sizes.

        Returns:
            Dictionary of available theme sizes.
        """

        return self._sizes

    @property
    def primary_color(self) -> str:
        """Getter method that returns primary theme color as a string.

        Returns:
            Primary theme color as a hexadecimal string.
        """

        return self._primary_color

    @property
    def info_color(self) -> str:
        """Getter method that returns info theme color as a string.

        Returns:
            Info theme color as a hexadecimal string.
        """

        return self._info_color

    @property
    def success_color(self) -> str:
        """Getter method that returns success theme color as a string.

        Returns:
            Success theme color as a hexadecimal string.
        """

        return self._success_color

    @property
    def warning_color(self) -> str:
        """Getter method that returns warning theme color as a string.

        Returns:
            Warning theme color as a hexadecimal string.
        """

        return self._warning_color

    @property
    def error_color(self) -> str:
        """Getter method that returns error theme color as a string.

        Returns:
            Error theme color as a hexadecimal string.
        """

        return self._error_color

    @property
    def hyperlink_style(self) -> str:
        """Getter method that returns hyperlink style as a string.

        Returns:
            HTML style for hyperlinks using the primary color.
        """

        return self._hyperlink_style

    def update_from_qss_file_path(
        self, qss_file_path: str, resources_rcc_file_path: str | None = None
    ):
        """Updates current theme with the contents of the given QSS file.

        Args:
            qss_file_path: Absolute file path pointing to a valid QSS file.
            resources_rcc_file_path: Optional RCC file to register within Qt resource system.
        """

        if not qss_file_path or not os.path.isfile(qss_file_path):
            logger.warning(
                f"Was not possible to update theme. QSS file path is not valid: {qss_file_path}"
            )
            return

        with open(qss_file_path, "r") as f:
            self._custom_qss += f.read()

        if resources_rcc_file_path:
            self.register_resources_rcc_file_path(resources_rcc_file_path)

    def register_resources_rcc_file_path(self, resources_rcc_file_path: str) -> bool:
        """Registers given RCC resources file path within Qt resources system.

        Args:
            resources_rcc_file_path: Absolute file path pointing to a valid RCC file.

        Returns:
            True if RCC file was registered successfully; False otherwise.
        """

        if not resources_rcc_file_path or not os.path.isfile(resources_rcc_file_path):
            return False
        if resources_rcc_file_path in self._registered_rcc_resources:
            return False

        QResource.registerResource(resources_rcc_file_path)
        self._registered_rcc_resources.append(resources_rcc_file_path)

        return True

    def apply(self, widget: QWidget):
        """Applies theme stylesheet to given widget.

        Args:
            widget: Widget to apply stylesheet to.
        """

        stylesheet_to_apply: str = self._default_qss
        if self._custom_qss:
            stylesheet_to_apply += f"\n{self._custom_qss}"

        widget.setStyleSheet(stylesheet_to_apply)
