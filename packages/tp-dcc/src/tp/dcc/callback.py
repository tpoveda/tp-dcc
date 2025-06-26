from __future__ import annotations

from . import is_maya, is_max, is_standalone, current_dcc


if is_maya():
    # noinspection PyUnresolvedReferences
    from tp.dcc.maya.callback import FnCallback
elif is_max():
    # noinspection PyUnresolvedReferences
    from tp.dcc.max.callback import FnCallback
elif is_standalone():
    # noinspection PyUnresolvedReferences
    from tp.dcc.standalone.callback import FnCallback
else:
    raise ImportError(f"Unable to import DCC Mesh class for: {current_dcc()}")
