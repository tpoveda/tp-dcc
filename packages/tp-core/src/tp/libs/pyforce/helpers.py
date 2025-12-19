from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    from enum import Enum

    class StrEnum(str, Enum):
        pass
else:
    from enum import StrEnum
