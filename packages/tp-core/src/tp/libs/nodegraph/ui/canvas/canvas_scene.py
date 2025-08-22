from __future__ import annotations

import math
import typing

from Qt.QtCore import Qt, QObject, QLineF, QRectF
from Qt.QtWidgets import QGraphicsScene
from Qt.QtGui import QFontMetricsF, QColor, QPen, QBrush, QPainter, QFontDatabase

from tp.libs.math.scalar import lerp_smooth, clamp
from tp.preferences.interfaces import core as core_interfaces

if typing.TYPE_CHECKING:
    from .canvas_base import CanvasBase


class CanvasScene(QGraphicsScene):
    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)

        self._prefs = core_interfaces.nodegraph_interface()

        self.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.setSceneRect(QRectF(0, 0, 10, 10))


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

        background_color = QColor(self._prefs.canvas_background_color)
        grid_color = QColor(self._prefs.canvas_grid_color)
        grid_color_darker = QColor(self._prefs.canvas_grid_color_darker)
        grid_size_small = self._prefs.canvas_grid_size_small
        grid_size_large = self._prefs.canvas_grid_size_large
        draw_grid = self._prefs.canvas_draw_grid
        draw_numbers = self._prefs.canvas_draw_numbers

        painter.save()
        try:
            # Draw background.
            painter.fillRect(rect, QBrush(background_color))

            # Current zoom scale in scene-units-to-device-pixels.
            scale = float(view.current_view_scale())

            # Device-pixel-aware 0.5 offset to align cosmetic 1 px hairlines.
            half_px_in_scene = 0.5 / max(scale, 1e-6)

            # Pixel density of each grid step at this zoom.
            ppu_small = grid_size_small * scale  # pixels per small cell.
            ppu_large = grid_size_large * scale  # pixels per large cell.

            # Fade the small grid progressively:
            # - fully off when a small cell is sub-pixel
            # - fully on when a small cell is comfortably large (e.g. >= 8px)
            small_alpha = lerp_smooth(1.25, 8.0, ppu_small)

            # Fade the large grid as well (ensures it doesn’t dominate when it’s sub-pixel)
            large_alpha = lerp_smooth(0.75, 4.0, ppu_large)

            # Pens.
            small_pen = QPen(grid_color)
            small_pen.setCosmetic(True)
            small_pen.setWidthF(1.0)
            small_pen.setCapStyle(Qt.FlatCap)
            small_pen.setJoinStyle(Qt.MiterJoin)

            large_pen = QPen(grid_color_darker)
            large_pen.setCosmetic(True)
            large_pen.setWidthF(1.0)
            large_pen.setCapStyle(Qt.FlatCap)
            large_pen.setJoinStyle(Qt.MiterJoin)

            # Disable AA for axis-aligned hairlines (crisper and faster).
            painter.setRenderHint(QPainter.Antialiasing, False)

            if draw_grid:
                # Compute start coordinates snapped to the grid
                left_small = math.floor(rect.left() / grid_size_small) * grid_size_small
                top_small = math.floor(rect.top() / grid_size_small) * grid_size_small

                left_large = math.floor(rect.left() / grid_size_large) * grid_size_large
                top_large = math.floor(rect.top() / grid_size_large) * grid_size_large

                # Draw small grid if it has any visible alpha and is not sub-pixel
                if small_alpha > 0.0 and ppu_small >= 0.5:
                    color = QColor(grid_color)
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
                        y += grid_size_small

                    # Vertical
                    x = float(left_small)
                    end_x = float(rect.right())
                    while x <= end_x:
                        x_aligned = x + half_px_in_scene
                        v_lines.append(
                            QLineF(x_aligned, rect.top(), x_aligned, rect.bottom())
                        )
                        x += grid_size_small

                    if h_lines:
                        painter.drawLines(h_lines)
                    if v_lines:
                        painter.drawLines(v_lines)

                # Draw the large grid if it has any visible alpha and is not
                # sub-pixel.
                if large_alpha > 0.0 and ppu_large >= 0.5:
                    color_d = QColor(grid_color_darker)
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
                        x += grid_size_large

                    # Horizontal.
                    y = float(top_large)
                    end_y = float(rect.bottom())
                    while y <= end_y:
                        y_aligned = y + half_px_in_scene
                        h_lines.append(
                            QLineF(rect.left(), y_aligned, rect.right(), y_aligned)
                        )
                        y += grid_size_large

                    if v_lines:
                        painter.drawLines(v_lines)
                    if h_lines:
                        painter.drawLines(h_lines)

            # Labels (numbers) — fade based on large-cell size so they
            # don’t clutter.
            if draw_numbers:
                # Enable only text AA for clean labels.
                painter.setRenderHint(QPainter.TextAntialiasing, True)

                # Fade labels in as large cells get bigger, off when tiny.
                text_alpha = lerp_smooth(8.0, 20.0, ppu_large)
                if text_alpha > 0.0:
                    label_color = QColor(grid_color_darker)
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
                        f.setFamily(
                            QFontDatabase.systemFont(QFontDatabase.FixedFont).family()
                        )
                    except Exception:
                        f.setFamily("Consolas")
                    painter.setFont(f)

                    fm = QFontMetricsF(f)

                    # Horizontal labels (Y-axis ticks) — draw at large-grid
                    # intersections
                    y = float(
                        math.floor(rect.top() / grid_size_large) * grid_size_large
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
                        y += grid_size_large

                    # Vertical labels (X-axis ticks).
                    x = float(
                        math.floor(rect.left() / grid_size_large) * grid_size_large
                    )
                    end_x = float(rect.right())
                    while x <= end_x:
                        if x >= rect.left():
                            painter.drawText(
                                int(x - half_px_in_scene),
                                int(rect.top()) + int(baseline_offset),
                                str(int(x)),
                            )
                        x += grid_size_large

        finally:
            painter.restore()
