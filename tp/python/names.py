from __future__ import annotations

import re


def get_end_number(input_string: str, as_string: bool = False) -> int | None:
    """
    Get the number at the end of a string.

    :param input_string: string to search for a number.
    :param as_string: whether the found number should be returned as integer or as string.
    :return: number at the end of te string.
    """

    found = re.findall(r"\d+", input_string)
    if not found:
        return None

    if isinstance(found, list):
        found = found[0]

    if as_string:
        return found
    else:
        return int(found)


class FindUniqueString:
    """
    Class that allows to find a unique string in a given scope.
    """

    def __init__(self, test_string: str):
        super().__init__()

        self._test_string: str = test_string
        self._increment_string: str | None = None
        self._padding: int = 0

    @property
    def padding(self) -> int:
        """
        Getter method that returns the padding value.

        :return: padding value.
        """

        return self._padding

    @padding.setter
    def padding(self, padding: int):
        """
        Setter method that sets the padding value.

        :param padding: new padding value.
        """

        self._padding = padding

    def get(self) -> str:
        """
        Returns a unique string.

        :return: unique string.
        """

        return self._search()

    # noinspection PyMethodMayBeStatic
    def _get_scope_list(self) -> list[str]:
        """
        Internal function that returns optional list of files and folders to take into account when looking for unique
        names.

        :return: list of files and folders.
        """

        return []

    def _format_string(self, number: int):
        """
        Internal function that formats the string with the given number.

        :param number: number to format the string with.
        """

        if number == 0:
            number = 1

        exp = re.compile(r"(\d+)(?=(\D+)?$)").search(self._test_string)
        if self._padding:
            number = str(number).zfill(self._padding)

        if exp:
            self._increment_string = f"{self._test_string[: exp.start()]}{number}{self._test_string[exp.end() :]}"
        else:
            split_dot = self._test_string.split(".")
            if len(split_dot) > 1:
                split_dot[-2] += str(number)
                self._increment_string = ".".join(split_dot)
            elif len(split_dot) == 1:
                self._increment_string = f"{self._test_string}{number}"

    def _get_number(self):
        """
        Internal function that returns the number at the end of the string.

        :return: number at the end of the string.
        """

        return get_end_number(self._test_string)

    def _search(self) -> str:
        """
        Internal function that generates the unique string.

        :return: unique string.
        """

        number = self._get_number()
        self._increment_string = self._test_string
        unique = False

        while not unique:
            scope = self._get_scope_list()
            if not scope:
                unique = True
                continue
            if self._increment_string not in scope:
                unique = True
                continue
            if self._increment_string in scope:
                if not number:
                    number = 0
                self._format_string(number)
                number += 1
                unique = False
                continue

        return self._increment_string
