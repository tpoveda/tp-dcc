from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from tp.preferences.assets import BrowserPreference


class ThumbBrowserMixin:
    _browser_preference: BrowserPreference | None = None

    def __init__(self, *args, **kwargs):
        super().__init__()

    @property
    def browser_preference(self) -> BrowserPreference | None:
        """The current browser preferences."""

        return self._browser_preference

    def set_asset_preferences(self, preferences: BrowserPreference):
        """Set the asset preferences for the browser.

        Args:
            preferences: The browser preferences to set.
        """

        self._browser_preference = preferences
