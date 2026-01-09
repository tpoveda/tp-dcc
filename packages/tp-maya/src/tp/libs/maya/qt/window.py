"""Maya-specific window implementation with docking support.

This module provides a Maya-specific window class that extends the base
Window class with Maya's workspace control docking functionality.
"""

from __future__ import annotations

from Qt.QtWidgets import QWidget

from tp.libs.qt.widgets.window import Window

from .docking import DockingContainer, SpawnerIcon


class MayaWindow(Window):
    """Window implementation with Maya docking support.

    This class extends the base Window class to add Maya-specific
    functionality like docking to Maya's workspace control system.
    """

    def __init__(
        self,
        name: str = "",
        title: str = "",
        width: int | None = None,
        height: int | None = None,
        resizable: bool = True,
        modal: bool = False,
        init_pos: tuple[int, int] | None = None,
        on_top: bool = False,
        save_window_pref: bool = False,
        minimize_enabled: bool = True,
        settings_path: str = "",
        parent: QWidget | None = None,
        enable_docking: bool = True,
        **kwargs,
    ) -> None:
        """Initialize a Maya window with docking support.

        Args:
            name: The internal name of the window.
            title: The title of the window.
            width: The width of the window.
            height: The height of the window.
            resizable: Whether the window is resizable.
            modal: Whether the window is modal.
            init_pos: Initial position (x, y).
            on_top: Whether the window should stay on top.
            save_window_pref: Whether to save window preferences.
            minimize_enabled: Whether minimization is enabled.
            settings_path: Path for storing settings.
            parent: The parent widget.
            enable_docking: Whether to enable Maya docking support.
        """

        self._enable_docking = enable_docking
        self._spawner_icon: SpawnerIcon | None = None

        super().__init__(
            name=name,
            title=title,
            width=width,
            height=height,
            resizable=resizable,
            modal=modal,
            init_pos=init_pos,
            on_top=on_top,
            save_window_pref=save_window_pref,
            minimize_enabled=minimize_enabled,
            settings_path=settings_path,
            parent=parent,
            **kwargs,
        )

        if enable_docking:
            self._setup_docking()

    @property
    def parent_container(self) -> DockingContainer | MayaWindow:
        """Get the parent container instance containing this window.

        Returns:
            The parent container (DockingContainer when docked, self otherwise).
        """

        return self._parent_container if self._parent_container else self

    def is_docked(self) -> bool:
        """Returns whether window is docked.

        Returns:
            True if window is docked; False otherwise.
        """

        return self._parent_container is not None and isinstance(
            self._parent_container, DockingContainer
        )

    def _setup_docking(self) -> None:
        """Set up the Maya docking functionality."""

        self._spawner_icon = SpawnerIcon(window=self, parent=self)
        self._spawner_icon.docked.connect(self._on_docked)
        self._spawner_icon.undocked.connect(self._on_undocked)
