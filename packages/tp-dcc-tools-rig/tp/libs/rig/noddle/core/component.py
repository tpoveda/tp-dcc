from tp.core import dcc


if dcc.is_maya():
    from tp.libs.rig.noddle.maya.meta import component as component
    from tp.libs.rig.noddle.maya.meta import animcomponent as animcomponent
    Component = component.Component
    AnimComponent = animcomponent.AnimComponent
else:
    from tp.libs.rig.noddle.abstract import component
    from tp.libs.rig.noddle.abstract import animcomponent
    Component = component.AbstractComponent
    AnimComponent = animcomponent.AbstractAnimComponent
