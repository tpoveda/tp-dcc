from tp.core import dcc


if dcc.is_maya():
    from tp.libs.rig.noddle.maya.meta.components import spine
    SpineComponent = spine.SpineComponent
    FKIKSpineComponent = spine.FKIKSpineComponent

else:
    from tp.libs.rig.noddle.abstract.components import spine
    SpineComponent = spine.AbstractSpineComponent
    FKIKSpineComponent = spine.AbstractFKIKSpineComponent
