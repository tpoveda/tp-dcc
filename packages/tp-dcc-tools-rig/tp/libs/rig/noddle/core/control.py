from tp.core import dcc


if dcc.is_maya():
    from tp.libs.rig.noddle.maya.core import control as maya_control
    Control = maya_control.Control
else:
    raise ImportError(f'Unable to import Control class for: {dcc.current_dcc()}')
