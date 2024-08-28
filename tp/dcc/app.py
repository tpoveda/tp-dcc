from __future__ import annotations

from . import current_dcc, Maya, Standalone

if current_dcc() == Maya:
    from .maya.app import FnApp  # noqa: F401
elif current_dcc() == Standalone:
    from .standalone.app import FnApp  # noqa: F401
else:
    raise ImportError(f'Unable to import App Function Set for "{current_dcc()}"')
