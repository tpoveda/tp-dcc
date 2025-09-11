from __future__ import annotations

from abc import ABC, abstractmethod


class ASkinningToolboxController(ABC):
    """Abstract class for skinning toolbox controller."""

    @abstractmethod
    def skin_transfer(self) -> None:
        """Transfers the skin weights from the first selected object to the
        rest of selected objects.
        """

        raise NotImplementedError

    @abstractmethod
    def skin_toggle(self) -> None:
        """Toggles the state of the first skin cluster on the selected meshes."""

        raise NotImplementedError
