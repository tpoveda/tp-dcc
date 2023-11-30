from __future__ import annotations

from tp.core import dcc


if dcc.is_maya():
    from tp.libs.rig.frag.hooks.maya.metadata import decode_metadata, encode_metadata, metadata, set_metadata
elif dcc.is_standalone():
    from tp.libs.rig.frag.hooks.standalone.metadata import decode_metadata, encode_metadata, metadata, set_metadata
else:
    raise ImportError(f'Unable to import DCC MetaData functions for: {dcc.current_dcc()}')
