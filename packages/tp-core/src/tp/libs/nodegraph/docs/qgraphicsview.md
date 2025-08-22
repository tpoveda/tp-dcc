# Understanding QGraphicsView transforms (Qt)
This document explains how QGraphicsView uses 2D affine transforms to map between item, scene, and view coordinates. It covers how the transform matrix is represented, how translation, rotation, scaling, and shear work, and practical patterns for zooming, panning, rotating, and extracting values like the current zoom level.
## Quick overview
- QGraphicsView draws a QGraphicsScene using a view transform (a QTransform).
- A QTransform is a 3×3 affine matrix. In typical 2D usage, perspective terms are zero and m33 is 1.
- Transform operations compose in order: calling t.translate(...), then t.rotate(...), then t.scale(...) results in M = T * R * S.
- Coordinate mapping goes through: item space → scene space → view (widget) space → device (pixels).

## The matrix layout
Qt’s QTransform stores the 2D affine transform as:
- Linear (2×2) block: scale, rotate, shear
- Translation (2×1): dx, dy

Mathematically:
[ m11  m12  m13 ]
[ a  b  0 ]
[ m21  m22  m23 ] == [ c  d  0 ]
[ m31  m32  m33 ]    [ tx ty 1 ]
Key fields:
- m11, m22: scale along X and Y when there is no rotation or shear.
- m12, m21: shear terms; also non-zero when rotation is present.
- m31, m32: translation (also accessible as dx(), dy()).
- m13, m23: perspective (normally 0 in QGraphicsView).
- m33: typically 1.

Given a point p = (x, y, 1), the transformed point p' = (x', y', 1) is:
- x' = m11_x + m12_y + m31
- y' = m21_x + m22_y + m32

## Composition order (important!)
When you call QTransform operations, Qt appends the new transform to the right:
- After t.translate(tx, ty), then t.rotate(angle), the resulting matrix is M = T(tx,ty) * R(angle).

This means transforms are applied to points in the same order you called them. For example, to rotate around a specific pivot (px, py), do:
1. translate(+pivot), 2) rotate, 3) translate(-pivot).

## Coordinate systems and mappings
- QGraphicsItem has its own transform (item → scene).
- QGraphicsView has a view transform (scene → view/widget).
- QPainter may add a device transform (view → device/pixels).

Useful APIs:
- QGraphicsView.transform() / setTransform()
- mapToScene(), mapFromScene()
- QGraphicsItem.mapToScene(), mapFromScene()
- QTransform.inverted()

## Common operations
### Zoom (uniform scale)
- Uniform zoom means sx == sy.
- For interactive zoom under the mouse, set the anchor and scale.

```python
from Qt.QtWidgets import QGraphicsView

class ZoomView(QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._min_scale = 0.2
        self._max_scale = 3.0

    def wheelEvent(self, event):
        # Smooth, DPI-aware zoom factor
        angle = event.angleDelta().y()
        factor = 1.0015 ** angle  # >1 zoom in, <1 zoom out

        # Compute the scale that would result if we applied 'factor'
        t = self.transform()
        # Robust current scales even if rotated/sheared
        sx = (t.m11()**2 + t.m21()**2) ** 0.5
        sy = (t.m12()**2 + t.m22()**2) ** 0.5
        current = (sx + sy) * 0.5

        target = max(self._min_scale, min(self._max_scale, current * factor))
        step = target / current

        self.scale(step, step)
```

### Pan (translation)
- You can translate the view transform or use scroll bars.
- With a custom drag mode:

```python
from Qt.QtWidgets import QGraphicsView

class PanView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        # Or implement your own panning by tracking mouse press/move

# Or manually translate:

def pan(self, dx: float, dy: float):
    self.translate(dx, dy)
```

### Rotate
Rotate around the view center:

```python
def rotate_about_view_center(self, degrees: float):
    self.rotate(degrees)
```

Rotate around an arbitrary scene pivot (px, py):

```python
from Qt.QtCore import QPointF

def rotate_about_scene_point(self, degrees: float, pivot_scene: QPointF):
    pivot_view = self.mapFromScene(pivot_scene)
    self.translate(pivot_view.x(), pivot_view.y())
    self.rotate(degrees)
    self.translate(-pivot_view.x(), -pivot_view.y())
```

### Fit to view

```python
from Qt.QtCore import Qt, QRectF

def fit_rect(self, rect: QRectF, padding: float = 0.0):
    r = QRectF(rect)
    r.adjust(-padding, -padding, padding, padding)
    self.fitInView(r, Qt.AspectRatioMode.KeepAspectRatio)
```

## Extracting scale, rotation, translation, and shear

### Translation

```python
def translation_from_transform(t) -> tuple[float, float]:
    return t.m31(), t.m32()  # same as t.dx(), t.dy()
```

### Robust scale (works even after rotation/shear)
The scale magnitudes are the lengths of the transformed basis vectors (columns):
- scale_x = hypot(m11, m21)
- scale_y = hypot(m12, m22)

```python
import math

from Qt.QtGui import QTransform

def scales_from_transform(t: QTransform) -> tuple[float, float]:
    sx = math.hypot(t.m11(), t.m21())
    sy = math.hypot(t.m12(), t.m22())
    return sx, sy
```

If you know the transform is pure uniform scaling with no rotation/shear, 
m11() or m22() is sufficient and faster.

### Rotation angle
Using the first column as the rotated X basis:
- angle_rad = atan2(m21, m11)
- angle_deg = degrees(angle_rad)

```python
def rotation_degrees_from_transform(t: QTransform) -> float:
    import math
    return math.degrees(math.atan2(t.m21(), t.m11()))
```

Note: If the transform includes reflections (negative determinant), you may 
need to account for that when interpreting the angle.

### Full 2D affine decomposition (scale, shear, rotation, translation)

This decomposes the 2×2 linear part A into: A = R · S, where R is rotation 
and S encodes scale and shear. It’s stable for non-singular transforms.

```python
import math
from typing import NamedTuple
from PySide6.QtGui import QTransform

class Decomposition(NamedTuple):
    tx: float
    ty: float
    rotation_deg: float
    scale_x: float
    scale_y: float
    shear: float  # dimensionless shear factor (x-shear along y)

def decompose_qtransform(t: QTransform) -> Decomposition:
    # Translation
    tx, ty = t.m31(), t.m32()

    # Columns of the 2x2 linear block
    a, c = t.m11(), t.m21()  # first column
    b, d = t.m12(), t.m22()  # second column

    # Scale X is length of first column
    scale_x = math.hypot(a, c)
    if scale_x == 0.0:
        # Singular; fallback
        rotation_deg = 0.0
        shear = 0.0
        scale_y = math.hypot(b, d)
        return Decomposition(tx, ty, rotation_deg, scale_x, scale_y, shear)

    # Normalize first column to get first rotation basis vector
    r0x, r0y = a / scale_x, c / scale_x

    # Shear is projection of second column onto r0
    shear = r0x * b + r0y * d

    # Remove shear from second column, remaining length is scale_y
    u1x = b - shear * r0x
    u1y = d - shear * r0y
    scale_y = math.hypot(u1x, u1y)

    # Build second rotation basis vector
    if scale_y != 0.0:
        r1x, r1y = u1x / scale_y, u1y / scale_y
    else:
        # Degenerate Y
        r1x, r1y = -r0y, r0x  # orthogonal fallback

    # Rotation angle from r0 (x-axis direction)
    rotation_deg = math.degrees(math.atan2(r0y, r0x))

    return Decomposition(tx, ty, rotation_deg, scale_x, scale_y, shear)
```

Interpretation:
- scale_x, scale_y are magnitudes of scaling along rotated axes.
- shear is the amount of x-shear along y after removing rotation (0 means no shear).
- rotation_deg is the rotation of the x-axis basis

## Building transforms

### In code (Python)

```python
from Qt.QtGui import QTransform

t = QTransform()
t.translate(100, 50)   # move right 100, down 50
t.rotate(30)           # rotate by 30 degrees
t.scale(2.0, 1.5)      # scale

# Apply to a view
view.setTransform(t)
```

### Around a pivot

```python
def scale_about_scene_point(view, factor: float, pivot_scene):
    pivot_view = view.mapFromScene(pivot_scene)
    view.translate(pivot_view.x(), pivot_view.y())
    view.scale(factor, factor)
    view.translate(-pivot_view.x(), -pivot_view.y())
```

## Mapping coordinates

- View/widget → scene:
    - mapToScene(QPoint/QRect/QPolygon)
    - mapFromScene(...)

```python
from Qt.QtCore import QPoint, QRect

p_view = QPoint(10, 20)
p_scene = view.mapToScene(p_view)

r_view = QRect(0, 0, 640, 480)
r_scene = view.mapToScene(r_view).boundingRect()
```

- Inverting a transform:

```python
t = view.transform()
inv_t, invertible = t.inverted()
if invertible:
    # map from view to scene manually if needed
    pass
```

## Practical tips and pitfalls
- Clamp zoom to a sensible min/max to avoid precision issues and over-zoom.
- Anchor under mouse for natural zooming: setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
- Order matters. To rotate/scale around a pivot: translate(+pivot), then rotate/scale, then translate(-pivot).
- Rotations and shears make m11/m22 unreliable as “scale” on their own—use hypot formulas instead.
- Negative scales mirror axes; check the determinant sign if that matters: det = m11_m22 - m12_m21.
- fitInView() resets the transform; if you mix custom zoom with fitInView, reapply your constraints afterward.
- High-DPI: QPainter/device pixel ratio may affect crispness, but view transforms work the same.

## Cheat sheet
- Current uniform zoom (robust): sqrt(m11^2 + m21^2) or sqrt(m12^2 + m22^2)
- Rotation angle (degrees): atan2(m21, m11) * 180 / pi
- Translation: (m31, m32) or (dx(), dy())
- Compose transforms in this order: t.translate(...); t.rotate(...); t.scale(...); # M = T * R * S

## Minimal end-to-end example

```python
import math
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem
from PySide6.QtCore import Qt, QRectF

class DemoView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(self.renderer().Antialiasing, True)  # optional
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Add a simple item
        self.scene().addEllipse(QRectF(-50, -50, 100, 100))

        # Start centered
        self.setSceneRect(QRectF(-200, -200, 400, 400))
        self.fitInView(QRectF(-100, -100, 200, 200), Qt.KeepAspectRatio)

    def wheelEvent(self, event):
        factor = 1.0015 ** event.angleDelta().y()
        self.scale(factor, factor)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self.rotate(15)
        elif event.key() == Qt.Key_T:
            # Print current transform decomposition
            t = self.transform()
            sx = math.hypot(t.m11(), t.m21())
            sy = math.hypot(t.m12(), t.m22())
            rot = math.degrees(math.atan2(t.m21(), t.m11()))
            tx, ty = t.m31(), t.m32()
            print(f"tx={tx:.2f}, ty={ty:.2f}, rot={rot:.2f}°, sx={sx:.2f}, sy={sy:.2f}")
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication([])
    v = DemoView()
    v.resize(800, 600)
    v.show()
    app.exec()
```

This example:
- Draws a circle in scene space centered at the origin.
- Supports mouse-wheel zoom under the cursor.
- Press R to rotate the view by 15°.
- Press T to print current translation, rotation, and scale.
