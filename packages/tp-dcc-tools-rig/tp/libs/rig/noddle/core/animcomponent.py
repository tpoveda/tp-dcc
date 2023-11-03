from tp.core import dcc
from tp.libs.rig.noddle.abstract import animcomponent


if dcc.is_maya():
    from tp.libs.rig.noddle.maya.meta import animcomponent as maya_anim_component
    AnimComponent = maya_anim_component.AnimComponent
else:
    AnimComponent = animcomponent.AbstractAnimComponent
