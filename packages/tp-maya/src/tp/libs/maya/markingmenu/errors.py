from __future__ import annotations


class InvalidMarkingMenuLayoutJsonFileFormatError(Exception):
    """
    Exception raised when a marking menu layout JSON file has an invalid format.
    """

    pass


class MissingMarkingMenu(Exception):
    """
    Exception raised when a marking menu is missing.
    """

    pass
