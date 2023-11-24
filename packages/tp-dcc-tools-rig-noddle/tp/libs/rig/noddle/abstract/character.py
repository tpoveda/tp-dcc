from __future__ import annotations

from typing import Any

from tp.common.python import decorators
from tp.libs.rig.noddle.abstract import component


class AbstractCharacter(component.AbstractComponent):
    """
    Abstract class definition for characters.
    """

    @decorators.abstractmethod
    def control_rig_group(self) -> Any:
        """
        Returns the node under rig controls should be placed within the scene hierarchy.

        :return: control rig group.
        :rtype: Any
        """

        raise NotImplementedError

    @decorators.abstractmethod
    def control_rig_group(self) -> Any:
        """
        Returns the node under rig controls should be placed within the scene hierarchy.

        :return: control rig group.
        :rtype: Any
        """

        raise NotImplementedError
