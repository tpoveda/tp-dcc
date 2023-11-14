from __future__ import annotations

from tp.core import dcc


if dcc.is_maya():
    from tp.libs.rig.noddle.maya.meta.components import stretch
    IKSplineStretchComponent = stretch.IKSplineStretchComponent
else:
    from tp.libs.rig.noddle.abstract.components import stretch
    IKSplineStretchComponent = stretch.AbstractIKSplineStretchComponent
