from __future__ import annotations

from abc import ABC, abstractmethod


class AbstractControlCreatorAdapter(ABC):
    """Abstract base class for control creator adapters."""

    @classmethod
    @abstractmethod
    def get_curve_file_extension(cls) -> str:
        """Returns the file extension for control curves.

        Returns:
            The file extension for control curve files.
        """

        raise NotImplementedError
