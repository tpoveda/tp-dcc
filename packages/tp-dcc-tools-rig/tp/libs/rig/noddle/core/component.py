from tp.core import dcc


if dcc.is_maya():
    from tp.libs.rig.noddle.maya.meta import component as component
    Component = component.Component
else:
    raise ImportError(f'Unable to import Component class for: {dcc.current_dcc()}')
