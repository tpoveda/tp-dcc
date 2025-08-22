from __future__ import annotations

import math
from enum import IntEnum

from Qt.QtCore import (
    Qt,
    QPoint,
    QPointF,
    QLineF,
    QRectF,
    QTimerEvent,
    QTimer,
    QElapsedTimer,
)
from Qt.QtWidgets import QWidget, QGraphicsScene, QGraphicsView
from Qt.QtGui import (
    QCursor,
    QFontMetricsF,
    QColor,
    QPen,
    QBrush,
    QMouseEvent,
    QPainter,
    QWheelEvent,
    QFontDatabase,
)

from tp.libs.math.scalar import lerp_value, range_percentage, lerp_smooth, clamp
from tp.preferences.interfaces import core as core_interfaces

from ...core.input import InputAction, InputActionType, manager as input_manager


class CanvasManipulationMode(IntEnum):
    """Enum representing the different manipulation modes for the canvas."""

    Undefined = 0
    Select = 1
    Pan = 2
    Move = 3
    Zoom = 4
    Copy = 5


class CanvasBase(QGraphicsView):
    """Base class for the node graph canvas."""

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)

        self._prefs = core_interfaces.nodegraph_interface()

        self._minimum_scale = 0.2
        self._maximum_scale = 3.0
        self._manipulation_mode = CanvasManipulationMode.Undefined
        self._mouse_press_pos = QPoint()
        self._mouse_pos = QPoint()
        self._last_mouse_pos = QPoint()
        self._mouse_release_pos = QPoint()

        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setAttribute(Qt.WA_AlwaysShowToolTips)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)

        self.setScene(self._create_scene())
        self.centerOn(
            QPointF(self.sceneRect().width() / 2, self.sceneRect().height() / 2)
        )

        self._initialize_smooth_interaction()

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
            scale = float(self.current_view_scale())

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

    # === Manipulation (Zoom, Pan) === #

    @property
    def manipulation_mode(self) -> CanvasManipulationMode:
        """The current manipulation mode of the canvas."""

        return self._manipulation_mode

    @manipulation_mode.setter
    def manipulation_mode(self, mode: CanvasManipulationMode) -> None:
        """Sets the manipulation mode of the canvas."""

        self._manipulation_mode = mode

        # Update the cursor based on the new manipulation mode.
        if mode == CanvasManipulationMode.Undefined:
            self.viewport().setCursor(Qt.ArrowCursor)
        elif mode == CanvasManipulationMode.Select:
            self.viewport().setCursor(Qt.ArrowCursor)
        elif mode == CanvasManipulationMode.Pan:
            self.viewport().setCursor(Qt.OpenHandCursor)
        elif mode == CanvasManipulationMode.Move:
            self.viewport().setCursor(Qt.ArrowCursor)
        elif mode == CanvasManipulationMode.Zoom:
            self.viewport().setCursor(Qt.SizeHorCursor)
        elif mode == CanvasManipulationMode.Copy:
            self.viewport().setCursor(Qt.ArrowCursor)

    def zoom(self, scale_factor: float) -> None:
        """Zooms the canvas by a given scale factor.

        Args:
            scale_factor: The factor by which to scale the view. A value
                greater than 1.0 zooms in, while a value less than 1.0 zooms
                out.
        """

        # Guard against invalid scale factors.
        if scale_factor <= 0.0:
            return

        current_scale = self.current_view_scale()
        # If the current scale is zero or negative, do not zoom.
        # This prevents division by zero or negative scaling.
        if current_scale <= 0.0:
            return

        # Calculate the requested scale based on the current scale and the
        # scale factor.
        requested_scale = current_scale * scale_factor

        # Clamp the absolute scale to the allowed range.
        min_scale = self._minimum_scale
        max_scale = self._maximum_scale
        if min_scale > max_scale:
            # If the configuration is inverted, swap to ensure a valid range.
            min_scale, max_scale = max_scale, min_scale
        clamped_scale = max(min_scale, min(max_scale, requested_scale))

        # Convert the clamped absolute scale back into a relative factor
        # to apply.
        effective_factor = clamped_scale / current_scale
        # Avoid applying a transform if the effective factor is effectively 1.0.
        if abs(effective_factor - 1.0) <= 1e-6:
            return

        # Apply uniform scaling on both axes.
        self.scale(effective_factor, effective_factor)

    def pan(self, delta: QPoint) -> None:
        """Pan the canvas by a screen-space delta, adjusted by the current zoom.

        Args:
            delta: Delta in view/screen coordinates (e.g., mouse drag in pixels).
                   Positive values move the visual content in the opposite
                   direction so the scene appears to follow the cursor.
        """

        # Extract raw delta components and skip if there is no movement.
        dx = int(delta.x())
        dy = int(delta.y())
        if dx == 0.0 and dy == 0.0:
            return

        # Guard against invalid/degenerate scales (prevents division by zero).
        scale = self.current_view_scale()
        if scale <= 0.0:
            return

        # Convert view-space delta to scene-space translation.
        # Note: translation is inverted, so dragging right moves the scene left,
        # making the content appear to follow the cursor.
        inv_scale = 1.0 / scale
        tx = -dx * inv_scale
        ty = -dy * inv_scale

        # Avoid performing an update for an effective no-op translation.
        if abs(tx) <= 1e-6 and abs(ty) <= 1e-6:
            return

        # Apply translation to the scene rect and update the view.
        rect = self.sceneRect()
        new_rect = rect.translated(tx, ty)
        self.setSceneRect(new_rect)
        self.update()

    # noinspection PyAttributeOutsideInit
    def smooth_zoom_to(
        self, absolute_scale: float, anchor_view_pos: QPoint | None = None
    ) -> None:
        """Ease the view toward an absolute scale, anchored at the given view
        position.
        """

        # Establish an anchor (defaults to the current cursor position if not
        # provided).
        if anchor_view_pos is None:
            anchor_view_pos = self.mapFromGlobal(QCursor.pos())
        self._smooth_anchor_view = anchor_view_pos
        self._smooth_anchor_scene = self.mapToScene(anchor_view_pos)

        # Update the target scale and start animating.
        self._smooth_zoom_target_scale = self._clamp_scale(float(absolute_scale))
        self._ensure_smooth_animating()

    def smooth_pan_by_view(self, delta_view: QPoint) -> None:
        """Queue a view-space pan delta that will be eased over several frames.

        Args:
            delta_view: The delta in view-space pixels to pan the canvas.
                        Positive values move the visual content in the opposite
                        direction so the scene appears to follow the cursor.
        """

        self._smooth_pan_remaining_view += delta_view
        self._ensure_smooth_animating()

    # noinspection PyAttributeOutsideInit
    def set_inertial_pan_velocity(self, velocity_view: QPoint) -> None:
        """Set an inertial pan velocity (view-space pixels/tick) and start decaying.

        Args:
            velocity_view: The initial velocity in view-space pixels per tick.
                           Positive values move the visual content in the opposite
                           direction so the scene appears to follow the cursor.
        """

        self._smooth_inertia_vel_view = velocity_view
        self._ensure_smooth_animating()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handles the mouse press event for the canvas.

        Args:
            event: The `QMouseEvent` containing the mouse position and buttons.
        """

        modifiers = event.modifiers()
        self._mouse_press_pos = event.pos()
        current_input_action = InputAction(
            "temp",
            InputActionType.Mouse,
            "temp",
            event.button(),
            modifiers=modifiers,
        )

        if current_input_action in input_manager["Canvas.Pan"]:
            self._cancel_zoom_animation()
            self.manipulation_mode = CanvasManipulationMode.Pan

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handles the mouse move event for the canvas.

        Args:
            event: The `QMouseEvent` containing the mouse position and buttons.
        """

        modifiers = event.modifiers()
        self._mouse_pos = event.pos()
        mouse_delta = QPointF(self._mouse_pos) - self._last_mouse_pos

        if self._manipulation_mode == CanvasManipulationMode.Pan:
            self.pan(mouse_delta)
        else:
            super().mouseMoveEvent(event)

        self._last_mouse_pos = self._mouse_pos

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handles the mouse release event for the canvas.

        Args:
            event: The `QMouseEvent` containing the mouse position and buttons.
        """

        super().mouseReleaseEvent(event)

        modifiers = event.modifiers()
        self._mouse_release_pos = event.pos()

        # Reset the manipulation mode to undefined after releasing the mouse.
        self.manipulation_mode = CanvasManipulationMode.Undefined

        super().mouseReleaseEvent(event)

    # noinspection PyAttributeOutsideInit
    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handles the mouse wheel event for zooming in and out of the canvas.

        Args:
            The `QWheelEvent` containing the mouse wheel movement information.
        """

        # Get the cursor position in view coordinates from the event.
        cursor_pos_view = event.position().toPoint()

        # Compute the zoom factor from wheel delta.
        angle_delta_y = event.angleDelta().y()
        pixel_delta_y = event.pixelDelta().y()
        if angle_delta_y != 0:
            steps = angle_delta_y / 120.0
        elif pixel_delta_y != 0:
            # Map pixel delta to fractional steps.
            # The scale factor here keeps sensitivity reasonable.
            steps = pixel_delta_y / 120.0
        else:
            # No vertical wheel delta; nothing to do.
            event.accept()
            return

        # Derive a per-step base and clamp an instantaneous factor for
        # responsiveness.
        base = 1.0 + max(self._mouse_wheel_zoom_rate, 1e-4)
        raw_factor = base**steps

        # Clamp extreme spikes from high-resolution devices to keep it
        # stylish, not jumpy.
        step_factor = max(
            1.0 / self._smooth_max_step_zoom_factor,
            min(self._smooth_max_step_zoom_factor, raw_factor),
        )

        # Set anchor and target absolute scale, then animate toward it.
        current_scale = self.current_view_scale()
        target_scale = self._clamp_scale(current_scale * step_factor)
        self._smooth_anchor_view = cursor_pos_view
        self._smooth_anchor_scene = self.mapToScene(cursor_pos_view)
        self._smooth_zoom_target_scale = target_scale

        # Kick the animation; zoom easing and anchor correction happen in
        # the timer tick.
        self._ensure_smooth_animating()
        event.accept()

    def timerEvent(self, event: QTimerEvent) -> None:
        """Handles the timer event for smooth animations.

        Args:
            event: The `QTimerEvent` that triggered the timer.
        """

        if (
            self._smooth_timer_id is not None
            and event.timerId() == self._smooth_timer_id
        ):
            self._tick_smooth_animation()
            event.accept()
            return

        super().timerEvent(event)

    def _initialize_smooth_interaction(self) -> None:
        """Initializes the smooth interaction settings for the canvas."""

        # Configuration.
        self._mouse_wheel_zoom_rate = self._prefs.canvas_mouse_wheel_zoom_rate
        self._smooth_smoothing = float(
            max(0.0, min(1.0, self._prefs.canvas_smooth_smoothing))
        )
        self._smooth_friction = float(
            max(0.0, min(1.0, self._prefs.canvas_smooth_friction))
        )
        self._smooth_max_step_zoom_factor = float(
            max(1.01, self._prefs.canvas_smooth_max_step_zoom_factor)
        )
        self._smooth_tick_ms = max(4, int(self._prefs.canvas_smooth_tick_ms))

        # State.
        self._smooth_timer_id: int | None = None
        current_scale = self.current_view_scale()
        self._smooth_zoom_target_scale: float = (
            current_scale if current_scale > 0.0 else 1.0
        )

        # Pan easing buffer and inertial velocity (in view/screen space
        # pixels per tick).
        self._smooth_pan_remaining_view = QPoint()
        self._smooth_inertia_vel_view = QPoint()

        # Zoom anchoring state.
        self._smooth_anchor_view: QPoint | None = (
            None  # view-space point under the cursor.
        )
        self._smooth_anchor_scene: QPoint | None = (
            None  # scene-space point under the cursor.
        )

    def _clamp_scale(self, value: float) -> float:
        """Clamps the given scale value to the minimum and maximum scale values
        defined for the canvas.

        Args:
            value: The scale value to clamp.

        Returns:
            The clamped scale value, ensuring it is within the defined range.
        """

        min_scale = self._minimum_scale
        max_scale = self._maximum_scale

        if min_scale > max_scale:
            min_scale, max_scale = max_scale, min_scale

        return max(min_scale, min(max_scale, value))

    def _ensure_smooth_animating(self) -> None:
        """Ensures that the smooth animation timer is running."""

        if self._smooth_timer_id is None:
            self._smooth_timer_id = self.startTimer(self._smooth_tick_ms)

    def _tick_smooth_animation(self) -> None:
        """Advance easing for zoom/pan; stop the timer automatically when idle."""

        changed = False

        # Ease zoom (absolute scale) toward the target.
        current_scale = self.current_view_scale()
        target_scale = float(self._smooth_zoom_target_scale)
        if current_scale > 0.0 and abs(current_scale - target_scale) > 1e-6:
            new_scale = lerp_value(current_scale, target_scale, self._smooth_smoothing)
            new_scale = self._clamp_scale(new_scale)
            if new_scale <= 0.0:
                new_scale = current_scale  # guard

            step_factor = new_scale / current_scale
            if abs(step_factor - 1.0) > 1e-6:
                self._apply_zoom_step_with_anchor(step_factor)
                changed = True

        # 2) Ease queued pan deltas (view space).
        pr = self._smooth_pan_remaining_view
        px, py = pr.x(), pr.y()
        if abs(px) > 0.1 or abs(py) > 0.1:
            step_x = px * self._smooth_smoothing
            step_y = py * self._smooth_smoothing
            step = QPoint(int(round(step_x)), int(round(step_y)))
            if step.x() != 0 or step.y() != 0:
                self.pan(step)
                self._smooth_pan_remaining_view -= step
                changed = True
            else:
                # Snap to done if the step is too small to matter.
                self._smooth_pan_remaining_view = QPoint(0, 0)

        # 3) Apply inertial pan velocity (decays each frame).
        vel = self._smooth_inertia_vel_view
        vx, vy = vel.x(), vel.y()
        if abs(vx) > 0.05 or abs(vy) > 0.05:
            step = QPoint(int(round(vx)), int(round(vy)))
            if step.x() != 0 or step.y() != 0:
                self.pan(step)
                changed = True
            # Decay velocity.
            vx *= self._smooth_friction
            vy *= self._smooth_friction
            # Dead zone threshold to stop.
            if abs(vx) < 0.05:
                vx = 0.0
            if abs(vy) < 0.05:
                vy = 0.0
            self._smooth_inertia_vel_view = QPoint(vx, vy)

        # Stop animation if nothing changed.
        if not changed:
            self._stop_smooth_animating()

    def _apply_zoom_step_with_anchor(self, factor: float) -> None:
        """Apply a relative zoom step and pan to keep the anchor fixed under
        the cursor.

        Args:
            factor: The relative zoom factor to apply. A value greater than 1.0
                zooms in, while a value less than 1.0 zooms out.
        """

        if factor <= 0.0 or abs(factor - 1.0) < 1e-9:
            return

        # Apply the partial zoom step.
        self.zoom(factor)

        # If we have a valid anchor, pan to keep it visually pinned.
        if (
            self._smooth_anchor_scene is not None
            and self._smooth_anchor_view is not None
        ):
            new_pos_view = self.mapFromScene(self._smooth_anchor_scene)
            # Compute view-space delta needed to restore the anchor under the
            # cursor.
            delta = new_pos_view - self._smooth_anchor_view
            # Pan expects a view-space delta; move in the opposite direction.
            self.pan(-delta)

    def _stop_smooth_animating(self) -> None:
        """Stops the smooth animation timer if it is running."""

        if self._smooth_timer_id is not None:
            self.killTimer(self._smooth_timer_id)
            self._smooth_timer_id = None

    def _cancel_zoom_animation(self) -> None:
        """Cancel any ongoing smooth zoom animation and reset the anchor."""

        cur = self.current_view_scale()
        if cur > 0.0:
            self._smooth_zoom_target_scale = cur
        self._smooth_anchor_view = None
        self._smooth_anchor_scene = None
