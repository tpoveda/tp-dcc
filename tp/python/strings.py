from __future__ import annotations

import re


def camel_case_to_string(camel_case_string: str) -> str:
    """
    Converts a camel case string to a normal one: testPath --> test Path.

    :param camel_case_string: string to convert to normal string.
    :return: normal string.
    """

    return re.sub("([a-z])([A-Z])", r"\g<1> \g<2>", camel_case_string)


def string_to_camel_case(string: str) -> str:
    """
    Converts a string to a camel case one: test path --> TestPath.

    :param string: string to convert to camel case.
    :return: camel case string.
    """

    return "".join(x for x in string.title() if not x.isspace())


def camel_case_to_snake_case(text: str) -> str:
    """
    Converts camel case string to underscore separate string.

    :param text: camel case string to convert.
    :return: snake case string.
    """

    words = []
    char_pos = 0
    for curr_char_pos, char in enumerate(text):
        if char.isupper() and char_pos < len(text):
            words.append(text[char_pos:curr_char_pos].lower())
            char_pos = curr_char_pos
    words.append(text[char_pos:].lower())
    return "_".join(words)


def camel_case_to_title(text: str) -> str:
    """
    Split string by upper case letters and return a nice name.

    :param text:  string to convert.
    :return: camel case string.
    """

    words = list()
    char_pos = 0
    for curr_char_pos, char in enumerate(text):
        if char.isupper() and char_pos < curr_char_pos:
            words.append(text[char_pos:curr_char_pos].title())
            char_pos = curr_char_pos
    words.append(text[char_pos:].title())
    return " ".join(words)


def lower_case_underscore_to_camel_case(text: str) -> str:
    """
    Converts string or unicode from lower case underscore to camel case.

    :param text: string to convert.
    :return: camel case string.
    """

    # NOTE: We use string's class to work on the string to keep its type
    split_string = text.split("_")
    class_ = text.__class__
    # noinspection PyTypeChecker
    return split_string[0] + class_.join("", map(class_.capitalize, split_string[1:]))


def snake_to_camel_case(snake_text):
    """
    Converts snake case text into camel case: test_path --> testPath.

    :param snake_text: snake case text.
    :return: camel case text.
    """

    components = snake_text.split("_")

    # We capitalize the first letter of each component except the first one with
    # the 'title' method and join them together.
    return components[0] + "".join(x.title() for x in components[1:])