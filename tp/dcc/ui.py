from __future__ import annotations

from . import current_dcc, Maya

if current_dcc() == Maya:
    from .maya.ui import FnUi
else:
    raise ImportError(f'Unable to import UI Function Set for "{current_dcc()}"')
