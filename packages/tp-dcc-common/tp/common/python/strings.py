#!#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utility functions related with strings
"""

from __future__ import annotations

import re
import os
import random
from typing import Tuple, Any
from string import ascii_letters
from distutils.util import strtobool

from tp.core import log

iters = [list, tuple, set, frozenset]


class _hack(tuple):
    pass


iters = _hack(iters)
iters.__doc__ = """
A list of iterable items (like lists, but not strings). Includes whichever
of lists, tuples, sets, and Sets are available in this version of Python.
"""

logger = log.tpLogger


def _strips(direction, text, remove):
    """
    Strips characters on a certain direction
    :param direction: str, strip direction ("r", "R", "l" or "L")
    :param text: str, text so strip
    :param remove: variant<iter>, elements to remove
    :return:
    """
    if isinstance(remove, iters):
        for subr in remove:
            text = _strips(direction, text, subr)
        return text

    if direction == 'l' or direction == 'L':
        if text.startswith(remove):
            return text[len(remove):]
    elif direction == 'r' or direction == 'R':
        if text.endswith(remove):
            return text[:-len(remove)]
    else:
        raise ValueError("Direction needs to be r or l.")
    return text


def rstrips(text, remove):
    """
    Removes the string `remove` from the right of `text`
    >>> rstrips("foobar", "bar")
    'foo'
    """
    return _strips('r', text, remove)


def lstrips(text, remove):
    """
    Removes the string `remove` from the left of `text`
    >>> lstrips("foobar", "foo")
    'bar'
    >>> lstrips('http://foo.org/', ['http://', 'https://'])
    'foo.org/'
    >>> lstrips('FOOBARBAZ', ['FOO', 'BAR'])
    'BAZ'
    >>> lstrips('FOOBARBAZ', ['BAR', 'FOO'])
    'BARBAZ'
    """
    return _strips('l', text, remove)


def strips(text, remove):
    """
    removes the string `remove` from the both sides of `text`
    >>> strips("foobarfoo", "foo")
    'bar'
    """
    return rstrips(lstrips(text, remove), remove)


def normalize(string):
    """
    Replace all invalid characters with "_"
    :param string: str, string to normalize
    :return: str, normalize string
    """

    string = str(string)

    if re.match('^[0-9]', string):
        string = '_' + string

    return re.sub("[^A-Za-z0-9_-]", "_", str(string))


def remove_invalid_character(string, regex="[^A-Za-z0-9]"):
    """
    Remove all invalid character
    :param string: str, string to normalize
    :return: str, valid string
    """

    return re.sub(regex, "", str(string))


def clean_string(text):
    """
    Returns a cleaned version of a string - removes everything but alphanumeric and characters and dots
    :param text:  str, string to clean
    :return: str, cleaned string
    """

    return re.sub(r'[^a-zA-Z0-9\n\.]', '_', text)


def replace_sharp_with_padding(string, index):
    """
    Replace a list of # symbol with properly padded index (i.e, count_### > count_001)
    :param string: str, string set. Should include '#'
    :param index: int, index to replace
    :return: str, normalized string
    """

    if string.count("#") == 0:
        string += "#"

    digit = str(index)
    while len(digit) < string.count("#"):
        digit = "0" + digit

    return re.sub("#+", digit, string)


def extract(string, start='(', stop=')'):
    """
    Extract the string that is contained between start and stop strings
    :param string: str, string to process
    :param start: str, start string
    :param stop: str, stop string
    :return: str, extracted string
    """

    try:
        return string[string.index(start) + 1:string.index(stop)]
    except Exception:
        return string


def format_path(path):
    """
    Takes a path and format it to forward slashes
    :param path: str
    :return: str
    """

    return os.path.normpath(path).replace('\\', '/').replace('\t', '/t').replace('\n', '/n').replace('\a', '/a')


def format_path_join(path, *paths):
    """
    os.path.join wrapper that returns always a valid Python path
    :param path:  str
    :param paths: str
    :return: str
    """

    return format_path(os.path.join(path, *paths))


def strip_prefix(name, split='_'):
    """
    Strips prefix
    :param name: str, name to strip prefix of
    :param split: str, split character
    :return: str
    """

    if not name.count(split):
        return name

    return split.join(name.split(split)[1:])


def strip_suffix(name, split='_'):
    """
    Returns the portion of name minus the last element separated by the splitter character
    :param name: str, name to strip the suffix from
    :param split: str, split character
    :return: str
    """

    if not name.count(split):
        return name

    return name.replace(split + name.split(split)[-1], '')


def add_prefix(prefix, split, string):
    """
    Adds a prefix to the given string
    :param prefix: str, prefix to add to the string
    :param split: str, split character
    :param string: str, string to add prefix to
    :return: str
    """
    return split.join([prefix, string])


def get_prefix(string, split):
    """
    Returns the prefix of the given string
    :param string: str, string to get prefix of
    :param split: str, split character
    :return: str
    """
    return string.split(split)[0]


def camel_case_to_string(camel_case_string):
    """
    Converts a camel case string to a normal one
    testPath --> test Path
    :param camel_case_string: str
    :return: str
    """

    return re.sub("([a-z])([A-Z])", r"\g<1> \g<2>", camel_case_string)


def string_to_camel_case(string):
    """
    Converts a string to a camel case one
    test path --> TestPath
    :param string: str
    :return: str
    """

    return ''.join(x for x in string.title() if not x.isspace())


def camel_case_to_snake_case(text: str) -> str:
    """
    Converts camel case string to underscore separate string.

    :param str text: camel case string to convert.
    :return: snake case string.
    :rtype: str
    """

    words = []
    char_pos = 0
    for curr_char_pos, char in enumerate(text):
        if char.isupper() and char_pos < len(text):
            words.append(text[char_pos:curr_char_pos].lower())
            char_pos = curr_char_pos
    words.append(text[char_pos:].lower())
    return '_'.join(words)


def camel_case_to_title(text):
    """
    Split string by upper case letters and return a nice name
    :param text: str, string to convert
    :return: str
    """

    words = list()
    char_pos = 0
    for curr_char_pos, char in enumerate(text):
        if char.isupper() and char_pos < curr_char_pos:
            words.append(text[char_pos:curr_char_pos].title())
            char_pos = curr_char_pos
    words.append(text[char_pos:].title())
    return ' '.join(words)


def lower_case_underscore_to_camel_case(text):
    """
    Converts string or unicdoe from lower case underscore to camel case
    :param text: str, string to convert
    :return: str
    """

    # NOTE: We use string's class to work on the string to keep its type
    split_string = text.split('_')
    class_ = text.__class__
    return split_string[0] + class_.join('', map(class_.capitalize, split_string[1:]))


def snake_to_camel_case(snake_text):
    """
    Converts snake case text into camel case
    test_path --> testPath
    :param snake_text:str
    :return: str
    """

    components = snake_text.split('_')

    # We capitalize the first letter of each component except the first one with
    # the 'title' method and join them together.
    return components[0] + ''.join(x.title() for x in components[1:])


def trailing_number(input_string: str, as_string: bool = False, number_count: int = -1) -> str | int | None:
    """
    Returns the number at the very end of a string. If number not at the end of the string return None.

    :param str input_string: string to trail.
    :param bool as_string: whether to return trailing number as an integer or as an string.
    :param int number_count: number count.
    :return: trailing string.
    :rtype: str or int or None
    """

    if not input_string:
        return None

    number = r'\d+'
    if number_count > 0:
        number = r'\d' * number_count

    group = re.match('([a-zA-Z_0-9]+)(%s$)' % number, input_string)
    if group:
        number = group.group(2)
        if as_string:
            return number
        else:
            return int(number)


def trailing_number_tuple(input_string: str) -> Tuple[str, int | None, int]:
    """
    Returns the trailing number of a string, the name with the number removed and the padding of the number.

    :param str input_string: string to trail.
    :return: tuple with the number of a string, the name without the number and the padding of the number.
    :rtype: Tuple[str, int | None, int]
    """

    m = re.search(r'\d+$', input_string)
    if m:
        number_as_string = m.group()
        name_numberless = input_string[:-len(number_as_string)]
        padding = len(number_as_string)
        return name_numberless, int(number_as_string), padding

    return input_string, None, 0


def get_string_index(index, padding=2):
    """
    Returns the string equivalent for the given integer index
    :param index: int, the index to get the string equivalent for
    :param padding: int, number of characters for the index string
    :return: str
    """

    str_ind = str(index)
    for i in range(padding - len(str_ind)):
        str_ind = '0' + str_ind

    return str_ind


def get_alpha(value, capital=False):
    """
    Convert an integer value to a character. a-z then double, aa-zz etc.
    @param value: int, Value to get an alphabetic character from
    @param capital: boolean: True if you want to get capital character
    @return: str, Character from an integer
    """

    # Calculate number of characters required
    base_power = base_start = base_end = 0
    while value >= base_end:
        base_power += 1
        base_start = base_end
        base_end += pow(26, base_power)
    base_index = value - base_start

    # Create alpha representation
    alphas = ['a'] * base_power
    for index in range(base_power - 1, -1, -1):
        alphas[index] = chr(97 + (base_index % 26))
        base_index /= 26

    if capital:
        return ''.join(alphas).upper()

    return ''.join(alphas)


def extract_digits_from_end_of_string(input_string):
    """
    Gets digits at the end of a string
    :param input_string: str
    :return: int
    """

    result = re.search(r'(\d+)$', input_string)
    if result is not None:
        return int(result.group(0))


def remove_digits_from_end_of_string(input_string):
    """
    Deletes the numbers at the end of a string
    :param input_string: str
    :return: str
    """

    return re.sub(r'\d+$', '', input_string)


def num_pad(num, length):
    """
    Returns given number with zero's at prefix to match given length
    :param num: int
    :param length: int
    :return: str
    """

    num_str = str(num)
    length_str = str(length)
    num_chars = len(num_str)
    length_chars = len(length_str)
    if num_chars < length_chars:
        diff = length_chars - num_chars
        return '{}{}'.format('0' * diff, num_str)

    return num_str


def rst_to_html(rst):
    """
    Converts given RST (reestructured text) string to HTML
    :param rst: str
    :return:
    """

    if not rst:
        return ''

    try:
        from docutils import core
    except Exception:
        logger.warning('docutils module is not available. Impossible to convert RST to HTML ...')
        return rst

    return core.publish_string(rst, writer_name='html').decode('utf-8')


def generate_random_string(num_symbols=5):
    """
    Generates a random string with the given number of characters
    :param num_symbols: int
    :return: str
    """

    result = ''
    for i in range(num_symbols):
        letter = random.choice(ascii_letters)
        result += letter

    return result


def first_letter_lower(input_string):
    """
    Returns a new string with the first letter as lowercase
    :param input_string: str
    :return: str
    """

    return input_string[:1].lower() + input_string[1:]


def first_letter_upper(input_string):
    """
    Returns a new string with the first letter as uppercase
    :param input_string: str
    :return: str
    """

    return input_string[:1].capitalize() + input_string[1:]


def to_boolean(input_string):
    """
    Returns given string as a boolean
    :param input_string: str
    :return: bool
    """

    return bool(strtobool(input_string))


def elided_text(text, width, char='.', repeat=3):
    """
    Returns elided version of the given text
    :param text: str
    :param width: int
    :param char: str
    :param repeat: int
    :return: str
    """

    return text if len(str(text)) < width else text[:width - repeat] + (char * repeat)


def get_spaces_count_at_beginning(text):
    """
    Returns the total number of spaces at the beginning of the given text
    :param text: str
    :return: int
    """

    return len(text) - len(text.lstrip())


def flatten_array_space(array):
    """
    Flatten a given list of strings into a single string, separated by spaces
    :param array: list(str)
    :return: str
    """

    from tp.common.python import helpers

    out_array = ''
    array = helpers.force_list(array)
    for obj in array:
        if type(obj).__name__ != 'str':
            obj = obj.__str__()
        if out_array == '':
            out_array = out_array + obj
        else:
            out_array = out_array + ' ' + obj

    return out_array


def flatten_array(array):
    """
    Flattens a given list into a single string, separated by commas
    :param array: list(str)
    :return: str
    """

    # import here to avoid cyclic imports
    from tp.common.python import helpers

    out_array = ''
    array = helpers.force_list(array)
    for obj in array:
        if type(obj).__name__ != 'str':
            obj = obj.__str__()
        if out_array == '':
            out_array = out_array + obj
        else:
            out_array = out_array + ', ' + obj

    return out_array


def flatten_array_colon(array):
    """
    Flattens a given list into a single string, separated by colons
    :param array: list(str)
    :return: str
    """

    # import here to avoid cyclic imports
    from tp.common.python import helpers

    out_array = ''
    array = helpers.force_list(array)
    for obj in array:
        if type(obj).__name__ != 'str':
            obj = obj.__str__()
        if out_array == '':
            out_array = out_array + obj
        else:
            out_array = out_array + ':' + obj

    return out_array


def append_extension(input_string, extension):
    """
    Adds the given extension at the end of the string if the input string does not already end with that extension

    :param str input_string: string to append extension.
    :param str extension: extension to append into the input string.
    :return: string with the extension appended.
    :rtype: str
    """

    if not extension.startswith('.'):
        extension = '.{}'.format(extension)
    if input_string.endswith('.'):
        input_string = input_string[:-1]
    if not input_string.endswith(extension):
        input_string = '{}{}'.format(input_string, extension)

    return input_string


def new_lines(text: str) -> int:
    """
    Returns the total count of new lines in given text.

    :param str text: text to get new lines count from.
    :return: total new lines.
    :rtype: int
    """

    return text.count('\n')


def title_case(input_string: str) -> str:
    """
    Returns given string as title case.

    :param str input_string: input string.
    :return: title case string.
    :rtype: str
    """

    if not input_string:
        return ''

    splitted = re.sub('(?!^)([A-Z][a-z]+)', r' \1', input_string).split()
    result = ' '.join(splitted)

    return result.replace('_', ' ').title()


def file_safe_name(text: str, space_to: str = ' ', keep: Tuple[str] = (' ', '_', '-')) -> str:
    """
    Returns a file safe name from the given string.

    :param str text: string to convert to a valid file name.
    :param str space_to: convert spaces to given character.
    :param Tuple[str] keep: characters to keep in the name.
    :return: file safe name.
    :rtype: str
    """

    return ''.join([c for c in text if c.isalnum() or c in keep]).rstrip().replace(' ', space_to)
