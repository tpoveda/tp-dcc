from __future__ import annotations

from tp.libs import dcc
from tp.preferences.interface import PreferenceInterface


class GeneralInterface(PreferenceInterface):
    id = "general"
    _relative_path = f"prefs/{dcc.current_dcc()}/general.yaml"
