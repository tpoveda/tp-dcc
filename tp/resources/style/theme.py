from __future__ import annotations

import os
import enum
import logging

from Qt.QtCore import QResource
from Qt.QtWidgets import QWidget

from . import setup, style_file_path
from ...qt import dpi
from ...python import helpers


logger = logging.getLogger(__name__)


def instance() -> Theme:
    """
    Returns global TNN theme instance.
    """

    return Theme.instance()


class Theme:
    """
    Class that defines default theme, which loads a QSS and optionally can modify it on runtime.
    """

    _INSTANCE: Theme | None = None

    # noinspection SpellCheckingInspection
    class Colors:
        """
        Class that defines available theme colors.
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
        """
        Enumerator that defines available theme sizes.
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
        """
        Returns global theme instance.
        """

        if cls._INSTANCE is None:
            cls._INSTANCE = cls()

        return cls._INSTANCE

    @property
    def sizes(self) -> helpers.AttributeDict:
        """
        Getter method that returns available sizes.

        :return: available sizes.
        """

        return self._sizes

    @property
    def primary_color(self) -> str:
        """
        Getter method that returns primary theme color as a string.

        :return: primary theme color.
        """

        return self._primary_color

    @property
    def info_color(self) -> str:
        """
        Getter method that returns info theme color as a string.

        :return: info theme color.
        """

        return self._info_color

    @property
    def success_color(self) -> str:
        """
        Getter method that returns success theme color as a string.

        :return: success theme color.
        """

        return self._success_color

    @property
    def warning_color(self) -> str:
        """
        Getter method that returns warning theme color as a string.

        :return: warning theme color.
        """

        return self._warning_color

    @property
    def error_color(self) -> str:
        """
        Getter method that returns error theme color as a string.

        :return: error color.
        """

        return self._error_color

    @property
    def hyperlink_style(self) -> str:
        """
        Getter method that returns error hyperlink color as a string.

        :return: hyperlink color.
        """

        return self._hyperlink_style

    def update_from_qss_file_path(
        self, qss_file_path: str, resources_rcc_file_path: str | None = None
    ):
        """
        Updates current theme with the contents of the given QSS file.

        :param qss_file_path: absolute file path pointing to a valid QSS file.
        :param resources_rcc_file_path: optional RCC file to register within Qt resource system.
        """

        if not qss_file_path or not os.path.isfile(qss_file_path):
            logger.warning(
                f"Was not possible to update TNM theme. QSS file path is not valid: {qss_file_path}"
            )
            return

        with open(qss_file_path, "r") as f:
            self._custom_qss += f.read()

        if resources_rcc_file_path:
            self.register_resources_rcc_file_path(resources_rcc_file_path)

    def register_resources_rcc_file_path(self, resources_rcc_file_path: str) -> bool:
        """
        Registers given RCC resources file path within Qt resources system.

        :param resources_rcc_file_path: absolute file path pointing to a valid RCC file.
        :return: True if RCC file was registered successfully; False otherwise.
        """

        if not resources_rcc_file_path or not os.path.isfile(resources_rcc_file_path):
            return False
        if resources_rcc_file_path in self._registered_rcc_resources:
            return False

        QResource.registerResource(resources_rcc_file_path)
        self._registered_rcc_resources.append(resources_rcc_file_path)

        return True

    def apply(self, widget: QWidget):
        """
        Applies theme stylesheet to given widget.

        :param QWidget widget: widget to apply stylesheet to.
        """

        stylesheet_to_apply: str = self._default_qss
        if self._custom_qss:
            stylesheet_to_apply += f"\n{self._custom_qss}"

        widget.setStyleSheet(stylesheet_to_apply)
