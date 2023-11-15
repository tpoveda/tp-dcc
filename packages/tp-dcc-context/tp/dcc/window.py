from tp.core import dcc

if dcc.is_maya():
    from tp.dcc.maya.window import MayaWindow as Window
elif dcc.is_max():
    from tp.dcc.max.window import MaxWindow as Window
elif dcc.is_standalone():
    from tp.dcc.standalone.window import StandaloneWindow as Window
else:
    raise ImportError(f'Unable to import DCC Node class for: {dcc.current_dcc()}')
