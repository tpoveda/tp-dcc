from __future__ import annotations

import yaml
from loguru import logger

from tp.preferences.theme import Theme
from tp.bootstrap.core.manager import PackagesManager
from tp.preferences.interface import PreferenceInterface


class ThemeInterface(PreferenceInterface):
    id = "theme"
    _relative_path = "prefs/global/stylesheet.yaml"
    _preference_roots_path = "env/preference_roots.yaml"

    def current_theme(self) -> str:
        """Returns the name of the current theme.

        Returns:
            The name of the current theme, or an empty string if not set.
        """

        return self.settings(name="current_theme", fallback="")

    def stylesheet(self, theme_name: str | None = None) -> str:
        """Return the stylesheet of the specified theme.

        Args:
            theme_name: The name of the theme for which to retrieve the
                stylesheet. If `None`, the stylesheet for the current theme
                will be used.

        Returns:
            The stylesheet of the specified or current theme.
        """

        theme_name = theme_name or self.current_theme()
        theme = self.theme(theme_name)
        if not theme:
            raise ValueError(f"Theme with name {theme_name} does not exist!")

        return theme.stylesheet()

    def theme(self, theme_name: str | None = None) -> Theme | None:
        """Retrieve and return a theme object based on the provided theme name.

        This method looks up the available themes from the style settings and
        returns the theme that matches the given theme name. If no matching
        theme is found, or if the style settings or themes are missing, it
        logs appropriate warnings and returns `None`.

        Args:
            theme_name: The name of the theme to retrieve.

        Returns:
            A `Theme` object corresponding to the given theme name if found,
            otherwise `None`.
        """

        theme_name = theme_name or self.current_theme()

        style_prefs = self.settings()
        if not style_prefs:
            logger.warning("No style settings found.")
            return None

        themes = style_prefs.get("settings", {}).get("themes", {})
        if not themes:
            logger.warning("No themes found,")
            return None
        if theme_name not in themes:
            logger.warning(f"No themes found for theme: {theme_name}")
            return None

        theme_data = themes.get(theme_name)
        theme = Theme(theme_name, theme_data)

        return theme
