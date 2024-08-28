from __future__ import annotations

from Qt.QtGui import QColor
from Qt.QtCore import QRegularExpression


_NUMERALS = "0123456789abcdefABCDEF"
# noinspection SpellCheckingInspection
_HEXDEC = {v: int(v, 16) for v in (x + y for x in _NUMERALS for y in _NUMERALS)}


def string_is_hex(color_str: str) -> bool:
    """
    Returns whether given string is a valid hexadecimal color

    :param color_str: color hexadecimal string.
    :return: True if the given string corresponds to a hexadecimal color; False otherwise.
    """

    if color_str.startswith("#"):
        color_str = color_str[1:]
    hex_regex1 = QRegularExpression(
        "^[0-9A-F]{3}$", QRegularExpression.CaseInsensitiveOption
    )
    hex_regex2 = QRegularExpression(
        "^[0-9A-F]{6}$", QRegularExpression.CaseInsensitiveOption
    )
    hex_regex3 = QRegularExpression(
        "^[0-9A-F]{8}$", QRegularExpression.CaseInsensitiveOption
    )
    if any(
        [
            hex_regex1.match(color_str).hasMatch(),
            hex_regex2.match(color_str).hasMatch(),
            hex_regex3.match(color_str).hasMatch(),
        ]
    ):
        return True

    return False


def rgb_from_hex(triplet: str):
    """
    Returns an RGB triplet from given hexadecimal value.

    :param triplet: r,g,b Hexadecimal Color tuple
    """

    if triplet.startswith("#"):
        triplet = triplet[1:]

    if len(triplet) == 3:
        r, g, b = triplet[0] * 2, triplet[1] * 2, triplet[2] * 2
        return tuple([float(int(v, 16)) for v in (r, g, b)])

    return _HEXDEC[triplet[0:2]], _HEXDEC[triplet[2:4]], _HEXDEC[triplet[4:6]]


def from_string(text_color: str) -> QColor:
    """
    Returns a `QColor` from the given string.

    :param text_color: string format color to parse
    :return: color instance.
    """

    a = 255
    if string_is_hex(text_color):
        r, g, b = rgb_from_hex(text_color)
    else:
        try:
            if text_color.startswith("rgba"):
                r, g, b, a = text_color.replace("rgba(", "").replace(")", "").split(",")
            else:
                r, g, b, a = text_color.replace("rgb(", "").replace(")", "").split(",")
        except ValueError:
            if text_color.startswith("rgba"):
                r, g, b = text_color.replace("rgba(", "").replace(")", "").split(",")
            else:
                r, g, b = text_color.replace("rgb(", "").replace(")", "").split(",")

    return QColor(int(r), int(g), int(b), int(a))
