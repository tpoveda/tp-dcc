from __future__ import annotations

from enum import IntEnum
from typing import NamedTuple, Type, TypedDict, Unpack

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


class SliderSettings(TypedDict, total=False):
    """Settings dictionary for MouseDragSlider."""

    # Behavior.
    direction: Direction
    threshold: int
    step: int
    pixel_range: int | None

    # Mouse/keyboard.
    mouse_button: Qt.MouseButton
    slow_modifier: Qt.KeyboardModifier
    fast_modifier: Qt.KeyboardModifier

    # Value types & clamps.
    num_type: Type[int | float]
    min_value: float | None
    max_value: float | None
    min_value_xy: tuple[float | None, float | None]
    max_value_xy: tuple[float | None, float | None]

    # Speeds (scalar + per-axis overrides).
    speed: float
    slow_speed: float
    fast_speed: float
    speed_xy: tuple[float | None, float | None]
    slow_speed_xy: tuple[float | None, float | None]
    fast_speed_xy: tuple[float | None, float | None]


DEFAULT_SETTINGS: SliderSettings = {
    "direction": Direction.DirectionalClamp,
    "threshold": 3,
    "step": 10,
    "pixel_range": None,
    "mouse_button": Qt.MiddleButton,
    "slow_modifier": Qt.ControlModifier,
    "fast_modifier": Qt.ShiftModifier,
    "num_type": float,
    "min_value": None,
    "max_value": None,
    "min_value_xy": (None, None),
    "max_value_xy": (None, None),
    "slow_speed": 0.01,
    "speed": 0.1,
    "fast_speed": 1.0,
    "slow_speed_xy": (None, None),
    "speed_xy": (None, None),
    "fast_speed_xy": (None, None),
}


def _pair2(
    v: tuple[float | None, float | None] | None,
    fallback: tuple[float | None, float | None],
) -> tuple[float | None, float | None]:
    """Normalize to a 2-tuple, falling back element-wise.

    Args:
        v: The input value.
        fallback: The fallback value.
    """

    if v is None:
        return fallback[0], fallback[1]
    x = v[0] if len(v) > 0 else None
    y = v[1] if len(v) > 1 else None
    return (
        x if x is not None else fallback[0],
        y if y is not None else fallback[1],
    )


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
        **settings: Unpack[SliderSettings],
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

        self._settings: SliderSettings = {}

        # Config
        self.set_settings(**settings)

    # region === Settings === #

    def set_settings(self, **settings: Unpack[SliderSettings]) -> None:
        """Apply settings. Safe to call at runtime."""

        self._settings = {**DEFAULT_SETTINGS, **settings}

    @property
    def direction(self) -> Direction:
        """The current direction mode."""

        return self._settings["direction"]

    @property
    def threshold(self) -> int:
        """The movement threshold in pixels before dragging starts."""

        return self._settings["threshold"]

    @property
    def step(self) -> int:
        """The pixel step for snapping."""

        return self._settings["step"]

    @property
    def pixel_range(self) -> int | None:
        """The pixel range for clamping the drag position."""

        return self._settings["pixel_range"]

    @property
    def mouse_button(self) -> Qt.MouseButton:
        """The mouse button to use for dragging."""

        return self._settings["mouse_button"]

    @property
    def slow_modifier(self) -> Qt.KeyboardModifier:
        """The keyboard modifier for slow speed."""

        return self._settings["slow_modifier"]

    @property
    def fast_modifier(self) -> Qt.KeyboardModifier:
        """The keyboard modifier for fast speed."""

        return self._settings["fast_modifier"]

    @property
    def num_type(self) -> Type[int | float]:
        """The numeric type for emitted values."""

        return self._settings["num_type"]

    @property
    def min_value(self) -> float | None:
        """The minimum value for both axes."""

        return self._settings["min_value"]

    @property
    def max_value(self) -> float | None:
        """The maximum value for both axes."""

        return self._settings["max_value"]

    @property
    def min_value_xy(self) -> tuple[float | None, float | None]:
        """The minimum values for X and Y."""

        return self._settings["min_value_xy"]

    @property
    def max_value_xy(self) -> tuple[float | None, float | None]:
        """The maximum values for X and Y."""

        return self._settings["max_value_xy"]

    @property
    def min_value_x(self) -> float | None:
        """The minimum X value."""

        return _pair2(
            self._settings["min_value_xy"], (self._settings["min_value"], None)
        )[0]

    @property
    def max_value_x(self) -> float | None:
        """The maximum X value."""

        return _pair2(
            self._settings["max_value_xy"], (self._settings["max_value"], None)
        )[0]

    @property
    def min_value_y(self) -> float | None:
        """The minimum Y value."""

        return _pair2(
            self._settings["min_value_xy"], (None, self._settings["min_value"])
        )[1]

    @property
    def max_value_y(self) -> float | None:
        """The maximum Y value."""

        return _pair2(
            self._settings["max_value_xy"], (None, self._settings["max_value"])
        )[1]

    @property
    def speed(self) -> float:
        """The normal speed scalar."""

        return self._settings["speed"]

    @property
    def speed_x(self) -> float:
        """The normal speed for X."""

        return _pair2(self._settings["speed_xy"], (self._settings["speed"], None))[0]

    @property
    def speed_y(self) -> float:
        """The normal speed for Y."""

        return _pair2(self._settings["speed_xy"], (None, self._settings["speed"]))[1]

    @property
    def slow_speed(self) -> float:
        """The slow speed scalar."""

        return self._settings["slow_speed"]

    @property
    def slow_speed_xy(self) -> tuple[float | None, float | None]:
        """The slow speed for X and Y."""

        return self._settings["slow_speed_xy"]

    @property
    def slow_speed_x(self) -> float:
        """The slow speed for X."""

        return _pair2(
            self._settings["slow_speed_xy"], (self._settings["slow_speed"], None)
        )[0]

    @property
    def slow_speed_y(self) -> float:
        """The slow speed for Y."""

        return _pair2(
            self._settings["slow_speed_xy"], (None, self._settings["slow_speed"])
        )[1]

    @property
    def fast_speed(self) -> float:
        """The fast speed scalar."""

        return self._settings["fast_speed"]

    @property
    def fast_speed_xy(self) -> tuple[float | None, float | None]:
        """The fast speed for X and Y."""

        return self._settings["fast_speed_xy"]

    @property
    def fast_speed_x(self) -> float:
        """The fast speed for X."""

        return _pair2(
            self._settings["fast_speed_xy"], (self._settings["fast_speed"], None)
        )[0]

    @property
    def fast_speed_y(self) -> float:
        """The fast speed for Y."""

        return _pair2(
            self._settings["fast_speed_xy"], (None, self._settings["fast_speed"])
        )[1]

    # endregion

    # region === Events === #

    def mouse_pressed(self, event: QMouseEvent) -> None:
        """Forward your widget's `mousePressEvent` here.

        Args:
            event: Forwarded mouse event.
        """

        if (event.button() & self.mouse_button) != self.mouse_button:
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
        if (event.button() & self.mouse_button) != self.mouse_button:
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
        self._fast = kb == self.fast_modifier
        self._slow = kb == self.slow_modifier
        self._modifiers = kb

    def _calculate_direction(self, delta: QPoint) -> Direction | None:
        """Calculate the current direction based on the delta and settings.

        Args:
            delta: The delta from the initial press position.

        Returns:
            The calculated direction or None if not enough movement.
        """

        if (
            self._rough_distance(delta) <= self.threshold
            or self._current_direction is not None
        ):
            return None

        abs_x = abs(delta.x())
        abs_y = abs(delta.y())

        if self.direction == Direction.DirectionalClamp:
            if abs_x >= abs_y:
                self.parent().setCursor(QtCore.Qt.SizeHorCursor)  # type: ignore[attr-defined]
                return Direction.Horizontal
            self.parent().setCursor(QtCore.Qt.SizeVerCursor)  # type: ignore[attr-defined]
            return Direction.Vertical

        if self.direction == Direction.Horizontal:
            self.parent().setCursor(QtCore.Qt.SizeHorCursor)  # type: ignore[attr-defined]
            return Direction.Horizontal

        if self.direction == Direction.Vertical:
            self.parent().setCursor(QtCore.Qt.SizeVerCursor)  # type: ignore[attr-defined]
            return Direction.Vertical

        if self.direction == Direction.Both:
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

        step = dpi.dpi_scale(self.step)
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
            value=(self.num_type(val_x), self.num_type(val_y)),
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

        if self.min_value_x is not None:
            x = max(self.min_value_x, x)
        if self.max_value_x is not None:
            x = min(self.max_value_x, x)
        return x

    def _clamp_value_y(self, y: float) -> float:
        """Clamp the Y value if min/max are set.

        Args:
            y: The Y value to clamp.

        Returns:
            The clamped Y value.
        """

        if self.min_value_y is not None:
            y = max(self.min_value_y, y)
        if self.max_value_y is not None:
            y = min(self.max_value_y, y)
        return y

    def _clamp_pos(self, pos: int) -> int:
        """Clamp the position by pixelRange if set.

        Args:
            pos: The position to clamp.

        Returns:
            The clamped position.
        """

        if self.pixel_range is not None:
            pr = dpi.dpi_scale(self.pixel_range)
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

        step = dpi.dpi_scale(self.step)

        if direction in (Direction.Horizontal, Direction.Both):
            speed = (
                self.fast_speed_x
                if self._fast
                else (self.slow_speed_x if self._slow else self.speed_x)
            )
        else:
            speed = (
                self.fast_speed_y
                if self._fast
                else (self.slow_speed_y if self._slow else self.speed_y)
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
