from __future__ import annotations

from enum import IntEnum
from typing import NamedTuple, Type

from Qt.QtCore import Qt, Signal, QObject, QPoint, QModelIndex
from Qt.QtWidgets import QApplication
from Qt.QtGui import QMouseEvent

from tp.libs.qt import dpi


class Direction(IntEnum):
    """Axis mode for drag-based sliding."""

    DirectionalClamp = 1  # Decide H/V after passing a threshold by dominant axis.
    Horizontal = 2
    Vertical = 3
    Both = 4  # Allows either axis; dominant axis is chosen after a threshold.


class MouseSlideEvent(NamedTuple):
    """Payload emitted on slide updates/releases."""

    value: tuple[float, float]
    direction: Direction
    x: int
    y: int
    dx: int
    dy: int
    index: QModelIndex
    modifiers: Qt.KeyboardModifier | Qt.KeyboardModifiers


class MouseDragSlider(QObject):
    """Drag-to-slide helper that turns mouse movement into 1D/2D numeric deltas.

    Attach it to a view-like widget (e.g., a thumbnail view) and forward
    your widget's mousePress/Move/Release events to `mouse_pressed`,
    `mouse_moved`, and `mouse_released`.

    Modes:
        - Horizontal: only X is active.
        - Vertical: only Y is active.
        - DirectionClamp: picks H or V after the threshold by dominant axis.
        - Both: allows either; dominant axis is chosen after threshold.

    Speeds:
        - `speed` is the base scalar per step (pixel step).
        - `slowSpeed` and `fastSpeed` override base with modifiers.
        - Per-axis overrides (speedXY/slowSpeedXY/fastSpeedXY) take precedence
          when provided (use `None` to fallback to the scalar variant).

    Position clamping:
        - `pixelRange` limits the drag cursor displacement to [-range, +range].
        - `minValue*`/`maxValue*` clamp the emitted numeric values.

    Usage:

        def mousePressEvent(self, e):
            self.slider.mouse_pressed(e)

        def mouseMoveEvent(self, e):
            if not self.slider.mouse_moved(e):
                super().mouseMoveEvent(e)

        def mouseReleaseEvent(self, e):
            self.slider.mouse_released(e)

    Signals:
        - scrolled(MouseSlideEvent)
        - pressed()
        - released(MouseSlideEvent)
    """

    scrolled = Signal(object)  # MouseSlideEvent
    pressed = Signal()
    released = Signal(object)  # MouseSlideEvent

    def __init__(
        self,
        parent: QObject,
        directions: Direction = Direction.DirectionalClamp,
        *,
        min_value: float | None = None,
        max_value: float | None = None,
        num_type: Type[int | float] = float,
        step: int = 10,
        pixel_range: int | None = None,
        slow_speed: float = 0.01,
        speed: float = 0.1,
        fast_speed: float = 1.0,
        slow_speed_xy: tuple[float | None, float | None] = (None, None),
        speed_xy: tuple[float | None, float | None] = (None, None),
        fast_speed_xy: tuple[float | None, float | None] = (None, None),
        min_value_xy: tuple[float | None, float | None] = (None, None),
        max_value_xy: tuple[float | None, float | None] = (None, None),
        mouse_button: Qt.MouseButton = Qt.MiddleButton,
        threshold: int = 3,
        slow_modifier: Qt.KeyboardModifier = Qt.ControlModifier,
        fast_modifier: Qt.KeyboardModifier = Qt.ShiftModifier,
    ) -> None:
        super().__init__(parent=parent)

        # Runtime state
        self._pressed_pos: QPoint | None = None
        self._current_direction: Direction | None = None
        self._last_x: int = 0
        self._last_y: int = 0
        self._fast: bool = False
        self._slow: bool = False
        self._modifiers: Qt.KeyboardModifier | Qt.KeyboardModifiers = Qt.NoModifier
        self._index: QModelIndex | None = None

        # Config
        self.set_settings(
            directions=directions,
            min_value=min_value,
            max_value=max_value,
            num_type=num_type,
            step=step,
            pixel_range=pixel_range,
            slow_speed=slow_speed,
            speed=speed,
            fast_speed=fast_speed,
            slow_speed_xy=slow_speed_xy,
            speed_xy=speed_xy,
            fast_speed_xy=fast_speed_xy,
            min_value_xy=min_value_xy,
            max_value_xy=max_value_xy,
            mouse_button=mouse_button,
            threshold=threshold,
            slow_modifier=slow_modifier,
            fast_modifier=fast_modifier,
        )

    # region === Settings === #

    # noinspection PyAttributeOutsideInit
    def set_settings(
        self,
        *,
        directions: Direction = Direction.DirectionalClamp,
        min_value: float | None = None,
        max_value: float | None = None,
        num_type=float,
        step: int = 10,
        pixel_range: int | None = None,
        threshold: int = 3,
        mouse_button: Qt.MouseButton = Qt.MiddleButton,
        slow_modifier: Qt.KeyboardModifier = Qt.ControlModifier,
        fast_modifier: Qt.KeyboardModifier = Qt.ShiftModifier,
        slow_speed: float = 0.01,
        speed: float = 0.1,
        fast_speed: float = 1.0,
        slow_speed_xy: tuple[float | None, float | None] = (None, None),
        speed_xy: tuple[float | None, float | None] = (None, None),
        fast_speed_xy: tuple[float | None, float | None] = (None, None),
        min_value_xy: tuple[float | None, float | None] = (None, None),
        max_value_xy: tuple[float | None, float | None] = (None, None),
    ) -> None:
        """Apply settings. Safe to call at runtime."""
        self._threshold = threshold
        self._min_value = min_value
        self._max_value = max_value
        self._min_value_x = (
            min_value_xy[0] if min_value_xy[0] is not None else min_value
        )
        self._max_value_x = (
            max_value_xy[0] if max_value_xy[0] is not None else max_value
        )
        self._min_value_y = (
            min_value_xy[1] if min_value_xy[1] is not None else min_value
        )
        self._max_value_y = (
            max_value_xy[1] if max_value_xy[1] is not None else max_value
        )
        self._direction = directions
        self._mouse_button = mouse_button
        self._pixel_range = pixel_range
        self._step = step
        self._num_type = num_type

        # Speeds (XY overrides fall back to scalar variants).
        self._slow_speed_x = (
            slow_speed_xy[0] if slow_speed_xy[0] is not None else slow_speed
        )
        self._normal_speed_x = speed_xy[0] if speed_xy[0] is not None else speed
        self._fast_speed_x = (
            fast_speed_xy[0] if fast_speed_xy[0] is not None else fast_speed
        )

        self._slow_speed_y = (
            slow_speed_xy[1] if slow_speed_xy[1] is not None else slow_speed
        )
        self._normal_speed_y = speed_xy[1] if speed_xy[1] is not None else speed
        self._fast_speed_y = (
            fast_speed_xy[1] if fast_speed_xy[1] is not None else fast_speed
        )

        self._fast_modifier = fast_modifier
        self._slow_modifier = slow_modifier

    # endregion

    # region === Events === #

    def mouse_pressed(self, event: QMouseEvent) -> None:
        """Forward your widget's `mousePressEvent` here.

        Args:
            event: Forwarded mouse event.
        """

        if (event.button() & self._mouse_button) != self._mouse_button:
            return

        index = self.parent().indexAt(event.pos())  # type: ignore[attr-defined]
        if getattr(index, "row", lambda: -1)() >= 0:
            self.pressed.emit()
            self._pressed_pos = event.pos()
            self._index = index

    def mouse_moved(self, event: QMouseEvent) -> bool:
        """Forward your widget's `mouseMoveEvent` here. Returns `True` if
        consumed.

        Args:
            event: Forwarded mouse event.
        """
        self._update_modifiers()

        if self._pressed_pos is None:
            return False

        delta = event.pos() - self._pressed_pos

        # Choose working axis after a threshold.
        new_dir = self._calculate_direction(delta)
        if new_dir is not None:
            self._current_direction = new_dir

        if self._current_direction is None:
            return False

        self._calculate_and_emit(delta)
        return True

    def mouse_released(self, event: QMouseEvent) -> None:
        """Forward your widget's `mouseReleaseEvent` here.

        Args:
            event: Forwarded mouse event.
        .
        """
        if (event.button() & self._mouse_button) != self._mouse_button:
            return

        if self._pressed_pos is not None:
            delta = event.pos() - self._pressed_pos
            self._calculate_and_emit(delta, emit_signal=self.released, force_emit=True)

        self._pressed_pos = None
        self._current_direction = None
        self._index = None
        self.parent().unsetCursor()  # type: ignore[attr-defined]

    # endregion

    # === region === Internals === #

    def _update_modifiers(self) -> None:
        """Update the current keyboard modifiers state."""

        kb = QApplication.keyboardModifiers()
        self._fast = kb == self._fast_modifier
        self._slow = kb == self._slow_modifier
        self._modifiers = kb

    def _calculate_direction(self, delta: QPoint) -> Direction | None:
        """Calculate the current direction based on the delta and settings.

        Args:
            delta: The delta from the initial press position.

        Returns:
            The calculated direction or None if not enough movement.
        """

        if (
            self._rough_distance(delta) <= self._threshold
            or self._current_direction is not None
        ):
            return None

        abs_x = abs(delta.x())
        abs_y = abs(delta.y())

        if self._direction == Direction.DirectionalClamp:
            if abs_x >= abs_y:
                self.parent().setCursor(QtCore.Qt.SizeHorCursor)  # type: ignore[attr-defined]
                return Direction.Horizontal
            self.parent().setCursor(QtCore.Qt.SizeVerCursor)  # type: ignore[attr-defined]
            return Direction.Vertical

        if self._direction == Direction.Horizontal:
            self.parent().setCursor(QtCore.Qt.SizeHorCursor)  # type: ignore[attr-defined]
            return Direction.Horizontal

        if self._direction == Direction.Vertical:
            self.parent().setCursor(QtCore.Qt.SizeVerCursor)  # type: ignore[attr-defined]
            return Direction.Vertical

        if self._direction == Direction.Both:
            self.parent().setCursor(QtCore.Qt.SizeAllCursor)  # type: ignore[attr-defined]
            return Direction.Horizontal if abs_x >= abs_y else Direction.Vertical

        return None

    def _calculate_and_emit(
        self,
        delta: QPoint,
        *,
        emit_signal: Signal | None = None,
        force_emit: bool = False,
    ) -> None:
        signal = emit_signal or self.scrolled

        if self._current_direction is None:
            return

        step = dpi.dpi_scale(self._step)
        # Snap to step and clamp by pixelRange.
        pos_x = self._clamp_pos(int(delta.x() * (1.0 / step)) * step)
        # Convert from Qt to Cartesian Y (invert), then snap/clamp.
        pos_y = self._clamp_pos(-int(delta.y() * (1.0 / step)) * step)

        should_emit = force_emit or (pos_x != self._last_x or pos_y != self._last_y)
        if not should_emit:
            return

        # Convert positions to numeric values with speed and step applied.
        val_x = self._value_from_pos(pos_x, self._current_direction)
        val_y = self._value_from_pos(pos_y, self._current_direction)

        val_x = self._clamp_value_x(val_x)
        val_y = self._clamp_value_y(val_y)

        payload = MouseSlideEvent(
            value=(self._num_type(val_x), self._num_type(val_y)),
            direction=self._current_direction,
            x=pos_x,
            y=pos_y,
            dx=pos_x - self._last_x,
            dy=pos_y - self._last_y,
            index=self._index,  # type: ignore[arg-type]
            modifiers=self._modifiers,
        )

        signal.emit(payload)
        self._last_x, self._last_y = pos_x, pos_y

    def _clamp_value_x(self, x: float) -> float:
        """Clamp the X value if min/max are set.

        Args:
            x: The X value to clamp.

        Returns:
            The clamped X value.
        """

        if self._min_value_x is not None:
            x = max(self._min_value_x, x)
        if self._max_value_x is not None:
            x = min(self._max_value_x, x)
        return x

    def _clamp_value_y(self, y: float) -> float:
        """Clamp the Y value if min/max are set.

        Args:
            y: The Y value to clamp.

        Returns:
            The clamped Y value.
        """

        if self._min_value_y is not None:
            y = max(self._min_value_y, y)
        if self._max_value_y is not None:
            y = min(self._max_value_y, y)
        return y

    def _clamp_pos(self, pos: int) -> int:
        """Clamp the position by pixelRange if set.

        Args:
            pos: The position to clamp.

        Returns:
            The clamped position.
        """

        if self._pixel_range is not None:
            pr = dpi.dpi_scale(self._pixel_range)
            pos = min(max(-pr, pos), pr)
        return pos

    def _value_from_pos(self, pos: int, direction: Direction) -> float:
        """Convert a position to a numeric value based on speed and step.

        Args:
            pos: The position to convert.
            direction: The current direction.

        Returns:
            The converted numeric value.
        """

        step = dpi.dpi_scale(self._step)

        if direction in (Direction.Horizontal, Direction.Both):
            speed = (
                self._fast_speed_x
                if self._fast
                else (self._slow_speed_x if self._slow else self._normal_speed_x)
            )
        else:
            speed = (
                self._fast_speed_y
                if self._fast
                else (self._slow_speed_y if self._slow else self._normal_speed_y)
            )

        # keep value invariant w.r.t. `step` choice.
        return pos * speed * (1.0 / step)

    @staticmethod
    def _rough_distance(p: QPoint) -> int:
        """Rough distance metric (L1 norm) for thresholding.

        Args:
            p: The point to calculate the distance for.

        Returns:
            The rough distance.
        """

        return abs(p.x()) + abs(p.y())

    # endregion
