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
