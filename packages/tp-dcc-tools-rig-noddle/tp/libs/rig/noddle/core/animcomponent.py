from tp.core import dcc


if dcc.is_maya():
    from tp.libs.rig.noddle.maya.meta import animcomponent as anim_component
    AnimComponent = anim_component.AnimComponent
else:
    raise ImportError(f'Unable to import AnimComponent class for: {dcc.current_dcc()}')
