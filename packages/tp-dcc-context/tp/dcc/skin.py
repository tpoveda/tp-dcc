from tp.core import dcc

if dcc.is_maya():
    from tp.dcc.maya.skin import MayaSkin as Skin
elif dcc.is_max():
    from tp.dcc.max.skin import MaxSkin as Skin
elif dcc.is_standalone():
    from tp.dcc.standalone.skin import StandaloneSkin as Skin
else:
    raise ImportError(f'Unable to import DCC Skin class for: {dcc.current_dcc()}')
