from __future__ import annotations

from Qt.QtCore import QPointF, QLineF, QRectF
from Qt.QtWidgets import QWidget, QGraphicsScene, QGraphicsView
from Qt.QtGui import QColor, QPen, QBrush, QPainter

from tp.libs.math.scalar import lerp_value, range_percentage
from tp.preferences.interfaces import core as core_interfaces


class CanvasBase(QGraphicsView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)

        self._prefs = core_interfaces.nodegraph_interface()

        self._minimum_scale = 0.2
        self._maximum_scale = 3.0

        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)

        self.setScene(self._create_scene())
        self.centerOn(
            QPointF(self.sceneRect().width() / 2, self.sceneRect().height() / 2)
        )

    # === LOD === #

    @property
    def minimum_scale(self) -> float:
        """The minimum scale value for the view."""

        return self._minimum_scale

    @property
    def maximum_scale(self) -> float:
        """The maximum scale value for the view."""

        return self._maximum_scale

    def current_view_scale(self) -> float:
        """Returns the current scale of the view.

        Returns:
            The current scale of the view.
        """

        # `transform()` returns the current transformation matrix of the view,
        # and then we extract the scale factor from it.
        # The `m22()` method returns the scale factor in the Y direction, which
        # is the same as the scale factor in the X direction (m11) for uniform
        # scaling.

        return self.transform().m22()

    def reset_scale(self) -> None:
        """Resets the scale of the view to the default value."""

        self.resetMatrix()

    def get_lod_value_from_scale(self, num_lods: int = 5, scale: float = 1.0):
        """Calculates the level of detail (LOD) value based on the current
        scale.

        Args:
            num_lods: The number of LODs to calculate.
            scale: The current scale of the view.

        Returns:
            The calculated LOD value.
        """

        # Normalize (0 to 1) the scale between the minimum and maximum scale
        # values.
        normalized_scale = range_percentage(
            self.minimum_scale, self.maximum_scale, scale
        )

        # We use linear interpolation to determine the LOD value based on the
        # number of LODs and the current scale of the view.
        lod = lerp_value(num_lods, 1, normalized_scale)

        # Round the LOD value to the nearest whole number.
        return int(round(lod))

    def get_lod_value_from_current_scale(self, num_lods: int = 5):
        """Calculates the level of detail (LOD) value based on the current
        scale of the view.

        Args:
            num_lods: The number of LODs to calculate.

        Returns:
            The calculated LOD value.
        """

        return self.get_lod_value_from_scale(
            num_lods=num_lods, scale=self.current_view_scale()
        )

    def get_canvas_lod_value_from_current_scale(self) -> int:
        """Calculates the level of detail (LOD) value for the canvas based on
        the current scale of the view.

        Returns:
            The calculated LOD value for the canvas.
        """

        return self.get_lod_value_from_current_scale(num_lods=self._prefs.canvas_lods)

    # === Scene === #

    def _create_scene(self) -> QGraphicsScene:
        """Creates the graphics scene for the canvas.

        Returns:
            A new `QGraphicsScene` instance.
        """

        scene = QGraphicsScene(self)
        scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        scene.setSceneRect(QRectF(0, 0, 10, 10))

        return scene

    # === Rendering === #

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """Draws the background of the canvas.

        Args:
            painter: The `QPainter` used to draw the background.
            rect: The rectangle area to draw the background in.
        """

        super().drawBackground(painter, rect)

        lod = self.get_canvas_lod_value_from_current_scale()
        lod_switch = self._prefs.canvas_lod_switch
        background_color = QColor(self._prefs.canvas_background_color)
        grid_color = QColor(self._prefs.canvas_grid_color)
        grid_color_darker = QColor(self._prefs.canvas_grid_color_darker)
        grid_size_small = self._prefs.canvas_grid_size_small
        grid_size_large = self._prefs.canvas_grid_size_large
        draw_grid = self._prefs.canvas_draw_grid
        draw_numbers = self._prefs.canvas_draw_numbers

        painter.save()
        try:
            painter.fillRect(rect, QBrush(background_color))

            left = int(rect.left()) - (int(rect.left()) % grid_size_small)
            top = int(rect.top()) - (int(rect.top()) % grid_size_small)

            if draw_grid:
                # Render detailed grid lines for small LODs.
                if lod < lod_switch:
                    horizontal_grid_lines: list[QLineF] = []
                    y = float(top)
                    while y < float(rect.bottom()):
                        horizontal_grid_lines.append(
                            QLineF(rect.left(), y, rect.right(), y)
                        )
                        y += grid_size_small
                    painter.setPen(QPen(grid_color, 1))
                    painter.drawLines(horizontal_grid_lines)

                    vertical_grid_lines = []
                    x = float(left)
                    while x < float(rect.right()):
                        vertical_grid_lines.append(
                            QLineF(x, rect.top(), x, rect.bottom())
                        )
                        x += grid_size_small
                    painter.setPen(QPen(grid_color, 1))
                    painter.drawLines(vertical_grid_lines)

                # Draw larger grid lines.
                left = int(rect.left()) - (int(rect.left()) % grid_size_large)
                top = int(rect.top()) - (int(rect.top()) % grid_size_large)

                vertical_grid_lines = []
                painter.setPen(QPen(grid_color_darker, 1.5))
                x = left
                while x < rect.right():
                    vertical_grid_lines.append(QLineF(x, rect.top(), x, rect.bottom()))
                    x += grid_size_large
                painter.drawLines(vertical_grid_lines)

                # Draw horizontal thick lines
                horizontal_grid_lines = []
                painter.setPen(QPen(grid_color_darker, 1.5))
                y = top
                while y < rect.bottom():
                    horizontal_grid_lines.append(
                        QLineF(rect.left(), y, rect.right(), y)
                    )
                    y += grid_size_large
                painter.drawLines(horizontal_grid_lines)

            if draw_numbers:
                scale = self.current_view_scale()
                f = painter.font()
                f.setPointSize(int(6 / min(scale, 1)))
                f.setFamily("Consolas")
                painter.setFont(f)
                y = float(top)

                while y < float(rect.bottom()):
                    y += grid_size_large
                    if y > top + 30:
                        painter.setPen(QPen(grid_color_darker.lighter(300)))
                        painter.drawText(int(rect.left()), int(y - 1.0), str(int(y)))

                x = float(left)
                while x < rect.right():
                    x += grid_size_large
                    intx = int(x)
                    if x > left + 30:
                        painter.setPen(QPen(grid_color_darker.lighter(300)))
                        painter.drawText(
                            x, rect.top() + painter.font().pointSize(), str(intx)
                        )

        finally:
            painter.restore()
