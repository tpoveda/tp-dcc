from tp.core import dcc


if dcc.is_maya():
    from tp.libs.rig.noddle.maya.core.hook import Hook
else:
    raise ImportError(f'Unable to import Hook class for: {dcc.current_dcc()}')
