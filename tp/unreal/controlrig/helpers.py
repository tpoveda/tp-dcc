from __future__ import annotations

import string

import unreal

from . import consts


def trs_from_list_matrix(
    matrix: list[list[float, float, float, float]],
) -> tuple[unreal.Vector, unreal.Rotator, unreal.Vector]:
    """
    Converts given matrix list to translation, rotation and scale.

    :param matrix: list of floats representing a matrix.
    :return: tuple with translation, rotation and scale.
    """

    matrix = unreal.Matrix(*matrix)
    translation = matrix.get_origin()
    rotation = matrix.get_rotator()
    scale = matrix.get_scale_vector()

    return translation, rotation, scale


def string_between_quotes(string: str) -> str:
    """
    Returns the string inside quotes.

    :param string: source string.
    :return: string without quotes.
    """

    splits = string.split("'")
    return splits[1].split(".")[-1]


def get_letter(index: int, lower: bool = False) -> str:
    """
    Returns a letter from the given index.

    :param index: index of the letter.
    :param lower: whether the letter should be lowercase or not.
    :return: letter from the given index.
    """

    letter = string.ascii_lowercase[index]
    return letter if lower else letter.upper()


def get_first_letter_uppercase(text: str) -> str:
    """
    Returns the first letter of the given text in uppercase.

    :param text: text to get the first letter from.
    :return: first letter of the given text in uppercase.
    """

    if not text:
        return ''
    elif len(text) == 1:
        return text.upper()
    else:
        return f'{text[0].upper()}{text[1:]}'


# noinspection PyShadowingBuiltins
def get_element_key(name: str, type: str) -> unreal.RigElementKey:
    """
    Returns a RigElementKey from the given name and type.

    :param name: name of the element.
    :param type: type of the element.
    :return: found rig element key.
    """

    # noinspection PyTypeChecker
    return unreal.RigElementKey(type=consts.ELEMENT_TYPES[type], name=name)
