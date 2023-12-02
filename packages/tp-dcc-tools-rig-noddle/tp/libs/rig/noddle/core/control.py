from tp.core import dcc


if dcc.is_maya():
    from tp.libs.rig.noddle.maya.core.control import Control
else:
    raise ImportError(f'Unable to import Control class for: {dcc.current_dcc()}')
