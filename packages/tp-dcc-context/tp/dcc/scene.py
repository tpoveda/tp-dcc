from tp.core import dcc

if dcc.is_maya():
    from tp.dcc.maya.scene import MayaScene as Scene
elif dcc.is_max():
    from tp.dcc.max.scene import MaxScene as Scene
elif dcc.is_standalone():
    from tp.dcc.standalone.scene import StandaloneScene as Scene
else:
    raise ImportError(f'Unable to import DCC Scene class for: {dcc.current_dcc()}')
