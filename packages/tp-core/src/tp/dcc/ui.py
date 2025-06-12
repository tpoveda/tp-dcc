from __future__ import annotations

from . import current_dcc, Maya, Unreal, Standalone

if current_dcc() == Maya:
    from .maya.ui import FnUi  # noqa: F401
elif current_dcc() == Unreal:
    from .unreal.ui import FnUi  # noqa: F401
elif current_dcc() == Standalone:
    from .standalone.ui import FnUi  # noqa: F401
else:
    raise ImportError(f'Unable to import UI Function Set for "{current_dcc()}"')
