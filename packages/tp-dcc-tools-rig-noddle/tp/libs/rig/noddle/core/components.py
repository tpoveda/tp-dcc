from __future__ import annotations

from tp.core import dcc


if dcc.is_maya():
    from tp.libs.rig.noddle.maya.meta.components import fk, head, fkik, foot, spine, stretch, twist
    FKComponent = fk.FKComponent
    HeadComponent = head.HeadComponent
    FKIKComponent = fkik.FKIKComponent
    FootComponent = foot.ReverseFootComponent
    SpineComponent = spine.SpineComponent
    FKIKSpineComponent = spine.FKIKSpineComponent
    IKSplineStretchComponent = stretch.IKSplineStretchComponent
    TwistComponent = twist.TwistComponent
else:
    from tp.libs.rig.noddle.abstract import components
    FKComponent = components.AbstractFKComponent
    HeadComponent = components.AbstractHeadComponent
    FKIKComponent = components.AbstractFKIKComponent
    FootComponent = components.AbstractReverseFootComponent
    SpineComponent = components.AbstractSpineComponent
    FKIKSpineComponent = components.AbstractFKIKSpineComponent
    IKSplineStretchComponent = components.AbstractIKSplineStretchComponent
    TwistComponent = components.AbstractTwistComponent
