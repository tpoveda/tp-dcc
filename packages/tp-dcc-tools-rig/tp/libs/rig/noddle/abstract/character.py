from __future__ import annotations

import abc

from typing import Any


class AbstractCharacter(abc.ABC):
    """
    Abstract class definition for characters.
    """

    @abc.abstractmethod
    def control_rig_group(self) -> Any:
        """
        Returns the node under rig controls should be placed within the scene hierarchy.

        :return: control rig group.
        :rtype: Any
        """

        pass

