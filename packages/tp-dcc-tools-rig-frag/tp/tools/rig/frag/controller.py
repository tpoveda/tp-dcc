from __future__ import annotations

from tp.core import dcc

if dcc.is_maya():
    from tp.tools.rig.frag.controllers.maya import MayaFragController as FragController
elif dcc.is_standalone():
    from tp.tools.rig.frag.controllers.standalone import StandaloneFragController as FragController
else:
    raise ImportError(f'Unable to import DCC FragController class for: {dcc.current_dcc()}')
