from __future__ import annotations

from . import current_dcc, Maya, Standalone

if current_dcc() == Maya:
    from .maya.scene import FnScene  # noqa: F401
elif current_dcc() == Standalone:
    from .standalone.scene import FnScene  # noqa: F401
else:
    raise ImportError(f'Unable to import Scene Function Set for "{current_dcc()}"')
