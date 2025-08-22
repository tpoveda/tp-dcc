from __future__ import annotations

from tp.preferences.interface import PreferenceInterface


class NodeGraphPreferenceInterface(PreferenceInterface):
    id = "nodegraph"
    _relative_path = "prefs/nodegraph.yaml"

    # === Canvas === #

    @property
    def canvas_lods(self) -> int:
        """The number of levels of detail to use for the node graph canvas."""

        return self.settings(name="canvas", fallback={}).get("number_lods", 4)

    @property
    def canvas_lod_switch(self) -> int:
        """The lod number at which to switch between levels of detail in the
        node graph canvas.
        """

        return self.settings(name="canvas", fallback={}).get("lod_switch", 3)

    @property
    def canvas_background_color(self) -> str:
        """The background color of the node graph canvas."""

        return self.settings(name="canvas", fallback={}).get(
            "background_color", "#232323"
        )

    @property
    def canvas_grid_color(self) -> str:
        """The grid color of the node graph canvas."""

        return self.settings(name="canvas", fallback={}).get("grid_color", "#14141466")

    @property
    def canvas_grid_color_darker(self) -> str:
        """The darker grid color of the node graph canvas."""

        return self.settings(name="canvas", fallback={}).get(
            "grid_color_darker", "#141414"
        )

    @property
    def canvas_draw_grid(self) -> bool:
        """Whether to draw the grid on the node graph canvas."""

        return self.settings(name="canvas", fallback={}).get("draw_grid", True)

    @property
    def canvas_grid_size_small(self) -> int:
        """The size of the small grid in the node graph canvas."""

        return self.settings(name="canvas", fallback={}).get("grid_size_small", 10)

    @property
    def canvas_grid_size_large(self) -> int:
        """The size of the large grid in the node graph canvas."""

        return self.settings(name="canvas", fallback={}).get("grid_size_large", 100)

    @property
    def canvas_draw_numbers(self) -> bool:
        """Whether to draw numbers on the node graph canvas."""

        return self.settings(name="canvas", fallback={}).get("draw_numbers", False)

    @property
    def canvas_mouse_wheel_zoom_rate(self) -> float:
        """The zoom rate when using the mouse wheel on the node graph canvas."""

        # Mouse wheel zoom rate for the canvas.
        # This value determines how much the view will zoom in or out when the
        # mouse wheel is scrolled. A smaller value results in finer control over
        # zooming.
        # A value of 0.0005 means that for every 120 units of wheel movement
        # (which is the standard amount for a single notch on most mice), the view
        # will zoom by a factor of 0.05.
        # This results in a very gradual zoom effect, allowing for precise
        # adjustments. Adjust this value to make zooming faster or slower
        # depending on user preference.

        return self.settings(name="canvas", fallback={}).get(
            "mouse_wheel_zoom_rate", 0.5
        )

    @property
    def canvas_smooth_smoothing(self) -> float:
        """The smoothing factor for the node graph canvas."""

        return self.settings(name="canvas", fallback={}).get("smoothing", 0.15)

    @property
    def canvas_smooth_friction(self) -> float:
        """The friction factor for the node graph canvas."""

        return self.settings(name="canvas", fallback={}).get("friction", 0.92)

    @property
    def canvas_smooth_max_step_zoom_factor(self) -> float:
        """The maximum step zoom factor for the node graph canvas."""

        return self.settings(name="canvas", fallback={}).get(
            "max_step_zoom_factor", 1.35
        )

    @property
    def canvas_smooth_tick_ms(self) -> int:
        """The tick interval in milliseconds for the node graph canvas."""

        return self.settings(name="canvas", fallback={}).get("tick_ms", 8)
