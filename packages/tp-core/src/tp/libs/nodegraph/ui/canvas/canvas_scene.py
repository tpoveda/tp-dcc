from __future__ import annotations

import math
import typing
from enum import IntEnum

from Qt.QtCore import Qt, QObject, QPointF, QLineF, QRectF
from Qt.QtWidgets import QGraphicsScene
from Qt.QtGui import QFontMetricsF, QColor, QPen, QBrush, QPainter, QFontDatabase

from tp.libs.math.scalar import lerp_smooth, clamp
from tp.preferences.interfaces import core as core_interfaces

if typing.TYPE_CHECKING:
    from .canvas_base import CanvasBase


class GridMode(IntEnum):
    """Enumeration for grid modes in the canvas scene."""

    NoGrid = 0
    Dots = 1
    Lines = 2


class CanvasScene(QGraphicsScene):
    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)

        self._prefs = core_interfaces.nodegraph_interface()

        self._background_color = QColor(self._prefs.canvas_background_color)
        self._grid_color = QColor(self._prefs.canvas_grid_color)
        self._grid_color_darker = QColor(self._prefs.canvas_grid_color_darker)
        self._grid_size_small = self._prefs.canvas_grid_size_small
        self._grid_size_large = self._prefs.canvas_grid_size_large
        self._draw_grid = self._prefs.canvas_draw_grid
        self._draw_numbers = self._prefs.canvas_draw_numbers
        self._grid_mode = GridMode(self._prefs.canvas_grid_mode)

        self.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.setSceneRect(QRectF(0, 0, 10, 10))
        self.setBackgroundBrush(self._background_color)

    @property
    def background_color(self) -> QColor:
        """The background color of the canvas scene."""

        return self._background_color

    @background_color.setter
    def background_color(self, color: QColor | tuple[float, float, float]) -> None:
        """Sets the background color of the canvas scene."""

        if isinstance(color, tuple):
            color = QColor(*color)

        self._background_color = color
        self.setBackgroundBrush(self._background_color)

    def __repr__(self) -> str:
        """Returns a string representation of the canvas scene.

        Returns:
            A string representation of the canvas scene, including its
            class name,
        """

        return (
            f'<{self.__class__.__name__}("{self.viewer()}") object at {hex(id(self))}>'
        )

    def viewer(self) -> CanvasBase | None:
        """Returns the first viewer in the scene.

        Returns:
            The first `CanvasBase` viewer in the scene, or `None` if no viewers
            are present.
        """

        return self.views()[0] if self.views() else None

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """Draws the background of the canvas.

        Args:
            painter: The `QPainter` used to draw the background.
            rect: The rectangle area to draw the background in.
        """

        super().drawBackground(painter, rect)

        view = self.viewer()
        if not view:
            return

        painter.save()
        try:
            painter.fillRect(rect, QBrush(self._background_color))

            if self._grid_mode == GridMode.Dots:
                self._draw_dots(painter, rect, view)
            elif self._grid_mode == GridMode.Lines:
                self._draw_grids(painter, rect, view)

        finally:
            painter.restore()

    def _draw_dots(self, painter: QPainter, rect: QRectF, view: CanvasBase) -> None:
        """Draws a dotted grid (small + large) with zoom-aware fading.

        Args:
            painter: The `QPainter` used to draw the grid.
            rect: The rectangle area to draw the grid in.
            view: The `CanvasBase` viewer associated with the scene.
        """

        if not self._draw_grid:
            return

        scale = float(view.current_view_scale())
        half_px_in_scene = 0.5 / max(scale, 1e-6)

        # Pixels per cell.
        ppu_small = self._grid_size_small * scale
        ppu_large = self._grid_size_large * scale

        # Fade in earlier than lines; clamp to a tiny floor so dots never fully disappear.
        small_alpha = clamp(lerp_smooth(0.75, 6.0, ppu_small), 0.0, 1.0)
        large_alpha = clamp(lerp_smooth(0.40, 3.5, ppu_large), 0.0, 1.0)

        # Adaptive dot sizes in *pixels* (cosmetic pen). Kept modest for density.
        # Feel free to tweak the multipliers/limits to taste.
        small_px = clamp(ppu_small * 0.16, 1.5, 2.4)  # ~1.5–2.4 px

        # Don’t bother if the cell is sub-pixel.
        draw_small = (ppu_small >= 0.5) and (small_alpha > 0.02)
        draw_large = (ppu_large >= 0.5) and (large_alpha > 0.02)
        if not (draw_small or draw_large):
            return

        # Snap starts to grid.
        left_points = (
            math.floor(rect.left() / self._grid_size_small) * self._grid_size_small
        )
        top_points = (
            math.floor(rect.top() / self._grid_size_small) * self._grid_size_small
        )

        painter.setRenderHint(QPainter.Antialiasing, True)

        if draw_small:
            pts_small: list[QPointF] = []
            y = float(top_points)
            end_y = float(rect.bottom())
            while y <= end_y:
                x = float(left_points)
                while x <= rect.right():
                    pts_small.append(
                        QPointF(x + half_px_in_scene, y + half_px_in_scene)
                    )
                    x += self._grid_size_small
                y += self._grid_size_small

            if pts_small:
                pen_small = QPen(self._grid_color)
                pen_small.setCosmetic(True)
                pen_small.setWidthF(float(small_px))
                pen_small.setCapStyle(Qt.RoundCap)
                pen_small.setJoinStyle(Qt.RoundJoin)
                c = QColor(self._grid_color)
                c.setAlphaF(clamp(max(small_alpha, 0.18), 0.0, 1.0))
                pen_small.setColor(c)
                painter.setPen(pen_small)
                painter.drawPoints(pts_small)

    def _draw_grids(self, painter: QPainter, rect: QRectF, view: CanvasBase) -> None:
        """Draws the grid on the canvas.

        Args:
            painter: The `QPainter` used to draw the grid.
            rect: The rectangle area to draw the grid in.
            view: The `CanvasBase` viewer associated with the scene.
        """

        # Current zoom scale in scene-units-to-device-pixels.
        scale = float(view.current_view_scale())

        # Device-pixel-aware 0.5 offset to align cosmetic 1 px hairlines.
        half_px_in_scene = 0.5 / max(scale, 1e-6)

        # Pixel density of each grid step at this zoom.
        ppu_small = self._grid_size_small * scale  # pixels per small cell.
        ppu_large = self._grid_size_large * scale  # pixels per large cell.

        # Fade the small grid progressively:
        # - fully off when a small cell is sub-pixel
        # - fully on when a small cell is comfortably large (e.g. >= 8px)
        small_alpha = lerp_smooth(1.25, 8.0, ppu_small)

        # Fade the large grid as well (ensures it doesn’t dominate when it’s sub-pixel)
        large_alpha = lerp_smooth(0.75, 4.0, ppu_large)

        # Pens.
        small_pen = QPen(self._grid_color)
        small_pen.setCosmetic(True)
        small_pen.setWidthF(1.0)
        small_pen.setCapStyle(Qt.FlatCap)
        small_pen.setJoinStyle(Qt.MiterJoin)

        large_pen = QPen(self._grid_color_darker)
        large_pen.setCosmetic(True)
        large_pen.setWidthF(1.0)
        large_pen.setCapStyle(Qt.FlatCap)
        large_pen.setJoinStyle(Qt.MiterJoin)

        # Disable AA for axis-aligned hairlines (crisper and faster).
        painter.setRenderHint(QPainter.Antialiasing, False)

        if self._draw_grid:
            # Compute start coordinates snapped to the grid
            left_small = (
                math.floor(rect.left() / self._grid_size_small) * self._grid_size_small
            )
            top_small = (
                math.floor(rect.top() / self._grid_size_small) * self._grid_size_small
            )

            left_large = (
                math.floor(rect.left() / self._grid_size_large) * self._grid_size_large
            )
            top_large = (
                math.floor(rect.top() / self._grid_size_large) * self._grid_size_large
            )

            # Draw the small grid if it has any visible alpha and is not
            # sub-pixel.
            if small_alpha > 0.0 and ppu_small >= 0.5:
                color = QColor(self._grid_color)
                color.setAlphaF(clamp(small_alpha, 0.0, 1.0))
                small_pen.setColor(color)
                painter.setPen(small_pen)

                # Build line lists
                h_lines: list[QLineF] = []
                v_lines: list[QLineF] = []

                # Horizontal
                y = float(top_small)
                end_y = float(rect.bottom())
                while y <= end_y:
                    y_aligned = y + half_px_in_scene
                    h_lines.append(
                        QLineF(rect.left(), y_aligned, rect.right(), y_aligned)
                    )
                    y += self._grid_size_small

                # Vertical
                x = float(left_small)
                end_x = float(rect.right())
                while x <= end_x:
                    x_aligned = x + half_px_in_scene
                    v_lines.append(
                        QLineF(x_aligned, rect.top(), x_aligned, rect.bottom())
                    )
                    x += self._grid_size_small

                if h_lines:
                    painter.drawLines(h_lines)
                if v_lines:
                    painter.drawLines(v_lines)

            # Draw the large grid if it has any visible alpha and is not
            # sub-pixel.
            if large_alpha > 0.0 and ppu_large >= 0.5:
                color_d = QColor(self._grid_color_darker)
                color_d.setAlphaF(clamp(large_alpha, 0.0, 1.0))
                large_pen.setColor(color_d)
                painter.setPen(large_pen)

                h_lines: list[QLineF] = []
                v_lines: list[QLineF] = []

                # Vertical.
                x = float(left_large)
                end_x = float(rect.right())
                while x <= end_x:
                    x_aligned = x + half_px_in_scene
                    v_lines.append(
                        QLineF(x_aligned, rect.top(), x_aligned, rect.bottom())
                    )
                    x += self._grid_size_large

                # Horizontal.
                y = float(top_large)
                end_y = float(rect.bottom())
                while y <= end_y:
                    y_aligned = y + half_px_in_scene
                    h_lines.append(
                        QLineF(rect.left(), y_aligned, rect.right(), y_aligned)
                    )
                    y += self._grid_size_large

                if v_lines:
                    painter.drawLines(v_lines)
                if h_lines:
                    painter.drawLines(h_lines)

    def _draw_numbers(self, painter: QPainter, rect: QRectF, view: CanvasBase) -> None:
        """Draws the grid labels (numbers) on the canvas.

        Args:
            painter: The `QPainter` used to draw the labels.
            rect: The rectangle area to draw the labels in.
            view: The `CanvasBase` viewer associated with the scene.
        """

        if not self._draw_numbers:
            return

        # Current zoom scale in scene-units-to-device-pixels.
        scale = float(view.current_view_scale())

        # Device-pixel-aware 0.5 offset to align cosmetic 1 px hairlines.
        half_px_in_scene = 0.5 / max(scale, 1e-6)

        # Pixel density of each grid step at this zoom.
        ppu_large = self._grid_size_large * scale  # pixels per large cell.

        # Enable only text AA for clean labels.
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        # Fade labels in as large cells get bigger, off when tiny.
        text_alpha = lerp_smooth(8.0, 20.0, ppu_large)
        if text_alpha <= 0.0:
            return

        label_color = QColor(self._grid_color_darker)
        label_color.setAlphaF(text_alpha)
        painter.setPen(QPen(label_color))

        # Font sized relative to zoom (clamped)
        f = painter.font()
        # Keep size stable on-screen; larger when zoomed out to
        # remain readable.
        # 6pt-11pt feels reasonable for a utility overlay.
        f.setPointSizeF(clamp(6.0 / max(min(scale, 1.0), 0.1), 6.0, 11.0))
        # Prefer a monospaced font; fall back if unavailable.
        # noinspection PyBroadException
        try:
            f.setFamily(QFontDatabase.systemFont(QFontDatabase.FixedFont).family())
        except Exception:
            f.setFamily("Consolas")
        painter.setFont(f)

        fm = QFontMetricsF(f)

        # Horizontal labels (Y-axis ticks) — draw at large-grid
        # intersections
        y = float(
            math.floor(rect.top() / self._grid_size_large) * self._grid_size_large
        )
        end_y = float(rect.bottom())
        baseline_offset = fm.ascent()  # for top-left placement.
        while y <= end_y:
            if y >= rect.top():
                painter.drawText(
                    int(rect.left()),
                    int(y - half_px_in_scene) + int(baseline_offset),
                    str(int(y)),
                )
            y += self._grid_size_large

        # Vertical labels (X-axis ticks).
        x = float(
            math.floor(rect.left() / self._grid_size_large) * self._grid_size_large
        )
        end_x = float(rect.right())
        while x <= end_x:
            if x >= rect.left():
                painter.drawText(
                    int(x - half_px_in_scene),
                    int(rect.top()) + int(baseline_offset),
                    str(int(x)),
                )
            x += self._grid_size_large
