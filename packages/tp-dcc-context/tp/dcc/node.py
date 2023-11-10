from tp.core import dcc

if dcc.is_maya():
    from tp.dcc.maya.node import MayaNode as Node
elif dcc.is_max():
    from tp.dcc.max.node import MaxNode as Node
elif dcc.is_standalone():
    from tp.dcc.standalone.node import StandaloneNode as Node
else:
    raise ImportError(f'Unable to import DCC Node class for: {dcc.current_dcc()}')
