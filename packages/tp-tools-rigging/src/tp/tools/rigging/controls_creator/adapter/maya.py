from __future__ import annotations

from .abstract import AbstractControlCreatorAdapter

from tp.libs.maya.curves import CURVE_FILE_EXTENSION


class MayaControlCreatorAdapter(AbstractControlCreatorAdapter):
    """Maya implementation of the `ControlCreatorAdapter`."""

    @classmethod
    def get_curve_file_extension(cls) -> str:
        """Returns the file extension for control curves.

        Returns:
            The file extension for control curve files.
        """

        return CURVE_FILE_EXTENSION
