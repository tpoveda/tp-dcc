#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes and functions related with names
"""

import os
import re
import sys
import string

from tp.common.python import helpers, strings


class FindUniqueString(object):
    """
    Utility class to get unique strings
    """

    def __init__(self, test_string):
        self.test_string = test_string
        self.increment_string = None
        self.padding = 0

    # region Public Functions
    def set_padding(self, padding):
        self.padding = padding

    def get(self):
        return self._search()
    # endregion

    # region Private Functions
    def _get_scope_list(self):
        return []

    def _format_string(self, number):
        if number == 0:
            number = 1

        exp = search_last_number(self.test_string)

        if self.padding:
            number = str(number).zfill(self.padding)

        if exp:
            self.increment_string = '{0}{1}{2}'.format(
                self.test_string[:exp.start()], number, self.test_string[exp.end():])
        else:
            split_dot = self.test_string.split('.')
            if len(split_dot) > 1:
                split_dot[-2] += str(number)
                self.increment_string = string.join(split_dot, '.')
            elif len(split_dot) == 1:
                self.increment_string = '{0}{1}'.format(self.test_string, number)

    def _get_number(self):
        return get_end_number(self.test_string)

    def _search(self):
        number = self._get_number()
        self.increment_string = self.test_string
        unique = False

        while not unique:
            scope = self._get_scope_list()
            if not scope:
                unique = True
                continue
            if self.increment_string not in scope:
                unique = True
                continue
            if self.increment_string in scope:
                if not number:
                    number = 0
                self._format_string(number)
                number += 1
                unique = False
                continue

        return self.increment_string


def strip_name(name):
    """
    Method that strips any |Path and :Namespaces: from a given object DAG path
    Ns:Rig|Ns:Leg|Ns:Test == Test
    :param name: str
    :return: str
    """

    return name.split('|')[-1].split(':')[-1]


def remove_suffix(name):
    """
    Remove suffix from given name string
    @param name: string, given name string to process
    @return: string, name without suffix
    """

    # By convention, we split the names when we find a _ character
    edits = name.split('_')

    # If there is not a _ it means that there is not an underscore and we return the full name
    if len(edits) < 2:
        return name

    # The suffix will be _ + the last split string and the name will be the complete name without the suffix
    suffix = '_' + edits[-1]
    name_no_suffix = name[:-len(suffix)]

    return name_no_suffix


def get_numeric_name(text, names):

    if text in names:
        text = re.sub('\\d*$', '', text)
        names = [n for n in names if n.startswith(text)]
        int_list = list()
        for name in names:
            m = re.match('^%s(\\d+)' % text, name)
            if m:
                int_list.append(int(m.group(1)))
            else:
                int_list.append(0)

                int_list.sort()
        missing_int = helpers.find_missing_items(int_list)
        if missing_int:
            _id = str(missing_int[0])
        else:
            _id = str(int_list[-1] + 1)
    else:
        _id = ''
    text += _id
    return text


def get_first_number(input_string, as_string=False):
    """
    Returns the first number of the given string
    :param input_string: str
    :param as_string: bool, Whether the found number should be returned as integer or as string
    :return: variant, str || int
    """

    found = re.search('[0-9]+', input_string)
    if not found:
        return None

    number_str = found.group()
    if not number_str:
        return None

    if as_string:
        return number_str
    number = int(number_str)

    return number


def get_last_number(input_string, as_string=False):
    """
    Returns the last number of the given string
    :param input_string: str, string to search for a number
    :param as_string: bool, Whether the found number should be returned as integer or as string
    :return: variant, str || int
    """

    found = search_last_number(input_string)
    if not found:
        return None

    number_str = found.group()
    if not number_str:
        return None

    if as_string:
        return number_str
    number = int(number_str)

    return number


def get_end_number(input_string, as_string=False):
    """
    Get the number at the end of a string
    :param input_string: bool, string to search for a number
    :param as_string: bool, Whether the found number should be returned as integer or as string
    :return: variant, str || int,  number at the end of te string
    """

    found = re.findall(r'\d+', input_string)
    if not found:
        return None

    if type(found) == list:
        found = found[0]

    if as_string:
        return found
    else:
        return int(found)


def get_trailing_number(input_string, as_string=False, number_count=-1):
    """
    Returns the number at the very end of a string. If number not at the end of the string, returns None
    :param input_string: str, string to get trailing number of
    :param as_string: bool, Whether to return the trailing number as an string or an integer
    :param number_count: int, padding trailing count
    :return: variant, str || int
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

    return None


def get_trailing_number_data(input_string):
    """
    Returns the trailing number of a string, the name with the number removed and the padding of the number
    :param input_string: str
    :return: tuple(str, str, int)
    """

    m = re.search(r'\d+$', input_string)
    if m:
        num_as_string = m.group()
        name_without_number = input_string[:-len(num_as_string)]
        padding = len(num_as_string)
        return name_without_number, int(num_as_string), padding

    return input_string, None, 0


def get_last_letter(input_string):
    """
    Returns the last letter of the given string
    :param input_string: str, string to search for a letter
    :return: str, last letter in the string
    """

    search = search_last_letter(input_string)
    if not search:
        return None

    found_str = search.group()
    return found_str


def convert_side_name(name):
    """
    Convert a string with underscore to proper side name
    :param name: str, string to convert
    :return: tuple of integer
    """

    if name == "L":
        return "R"
    elif name == "R":
        return "L"
    if name == 'l':
        return 'r'
    if name == 'r':
        return 'l'

    re_pattern = re.compile("_[RLrl][0-9]+_|^[RLrl][0-9]+_|_[RLrl][0-9]+$|_[RLrl]_|^[RLrl]_|_[RLrl]$")

    re_match = re.search(re_pattern, name)
    if re_match:
        instance = re_match.group(0)
        rep = None
        if instance.find("R") != -1:
            rep = instance.replace("R", "L")
        else:
            rep = instance.replace("L", "R")
        if not rep:
            if instance.find('r') != -1:
                rep = instance.replace('r', 'l')
            else:
                rep = instance.replace('l', 'r')

        name = re.sub(re_pattern, rep, name)

    return name


def replace_string(string_value, replace_string, start, end):
    """
    Replaces one string by another
    :param string_value: str, string to replace
    :param replace_string: str, string to replace with
    :param start: int, string index to start replacing from
    :param end: int, string index to end replacing
    :return: str, new string after replacing
    """

    first_part = string_value[:start]
    second_part = string_value[end:]

    return first_part + replace_string + second_part


def replace_string_at_start(line, string_to_replace, replace_string):
    """
    Replaces string at the start of the given line
    :param line: str
    :param string_to_replace: str
    :param replace_string: str
    :return:
    """

    m = re.search('^%s' % string_to_replace, line)
    if not m:
        return

    start = m.start(0)
    end = m.end(0)
    new_line = line[:start] + replace_string + line[end:]

    return new_line


def replace_string_at_end(line, string_to_replace, replace_string):
    """
    Replaces string at the end of the given line
    :param line: str
    :param string_to_replace: str
    :param replace_string: str
    :return:
    """

    m = re.search('%s$' % string_to_replace, line)
    if not m:
        return

    start = m.start(0)
    end = m.end(0)
    new_line = line[:start] + replace_string + line[end:]

    return new_line


def clean_file_string(string):
    """
    Replaces all / and \\ characters by _
    :param string: str, string to clean
    :return: str, cleaned string
    """

    if string == '/':
        return '_'

    string = string.replace('\\', '_')

    return string


def clean_name_string(string_value, clean_chars='_', remove_chars='_'):
    """
    Clean given string by cleaning given clean_char and removing given remove_chars.

    :param str string_value: str
    :param str clean_chars: str
    :param str remove_chars: str
    :return: cleaned name
    :rtype: str
    """

    string_value = re.sub('^[^A-Za-z0-9%s]+' % clean_chars, '', string_value)
    string_value = re.sub('[^A-Za-z0-9%s]+$' % clean_chars, '', string_value)
    string_value = re.sub('[^A-Za-z0-9]', remove_chars, string_value)

    if not string_value:
        string_value = remove_chars

    return string_value


def search_first_number(input_string):
    """
    Get the first number in a string
    :param input_string:  string to search for its first number
    :return: int, last number in the string
    """

    regex = re.compile('[0-9]+')
    return regex.search(input_string)


def search_last_number(input_string):
    """
    Get the last number in a string
    :param input_string:  string to search for its lsat number
    :return: int, last number in the string
    """

    regex = re.compile(r'(\d+)(?=(\D+)?$)')
    return regex.search(input_string)


def replace_last_number(input_string, replace_string):
    """
    Replace the last number with the given replace_string
    :param input_string: str, string to search for the last number
    :param replace_string: str, string to replace the last number with
    :return: str, new string after replacing
    """

    replace_string = str(replace_string)
    regex = re.compile(r'(\d+)(?=(\D+)?$)')
    search = regex.search(input_string)
    if not search:
        return input_string + replace_string

    return input_string[:search.start()] + replace_string + input_string[search.end():]


def increment_first_number(input_string, value=1):
    """
    Up the value of the first number by the given value (by default is 1)
    :param input_string: str, string to search for increment its first number
    :return: str, new string after the first number is replaced
    """

    search = search_first_number(input_string)
    if search:
        new_string = '{0}{1}{2}'.format(
            input_string[0:search.start()], int(search.group()) + value, input_string[search.end():])
    else:
        new_string = input_string + '_{}'.format(value)

    return new_string


def increment_last_number(input_string, value=1):
    """
    Up the value of the last number by the given value (by default is 1)
    :param input_string: str, string to search for increment its last number
    :return: str, new string after the last number is replaced
    """

    search = search_last_number(input_string)
    if search:
        new_string = '{0}{1}{2}'.format(
            input_string[0:search.start()], int(search.group()) + value, input_string[search.end():])
    else:
        new_string = input_string + '{}'.format(value)

    return new_string


def search_last_letter(input_string):
    """
    Returns the last letter in a string
    :param input_string: str, string to search for a letter
    :return: str, last letter in the string
    """

    match = re.findall('[_a-zA-Z]+', input_string)
    if match:
        return match[-1][-1]


def format_path(path):
    """
    Takes a path and format it to forward slashes
    :param path: str
    :return: str
    """

    return os.path.normpath(path).replace('\\', '/').replace('\t', '/t').replace('\n', '/n').replace('\a', '/a')


def add_unique_postfix(fn):
    if not os.path.exists(fn):
        return fn

    path, name = os.path.split(fn)
    name, ext = os.path.splitext(name)

    def make_fn(i):
        return os.path.join(path, '%s_%d%s' % (name, i, ext))

    for i in range(2, sys.maxint):
        uni_fn = make_fn(i)
        if not os.path.exists(uni_fn):
            return uni_fn

    return None


def find_unique_name(name, names, inc_format='{name}{count:03}', sanity_count=9999999):
    """
    Finds a unique name in a given set of names
    :param name: str, name to search for in the scene
    :param names: list<str>, set of strings to check for a unique name
    :param inc_format: str, used to increment the name
    :param sanity_count: int, used to prevent infinite search loop. Increment if needed (default=9999999)
    """

    count = 0
    ret = name
    while ret in names:
        count += 1
        ret = inc_format.format(name=name, count=count)
        if sanity_count and count > sanity_count:
            raise Exception('Unable to find a unique name in {} tries, try a different format.'.format(sanity_count))

    return ret


def find_special(pattern, string_value, position_string):
    """
    Searchs given regular expressin pattern in the given string
    :param pattern: str, regular expression pattern to search for
    :param string_value: str, string to search in
    :param position_string: str, 'start', 'end', 'first', 'last', 'inside', where the pattern should search
    :return: tuple(int, int): start and end indexes of the found pattern. Returns (None, None) if pattern is not found
    """

    char_count = len(string_value)
    found_iter = re.finditer(pattern, string_value)
    found = list()
    index_start = None
    index_end = None

    for item in found_iter:
        found.append(item)
    if not found:
        return None, None

    if position_string == 'end':
        index_start = found[-1].start()
        index_end = found[-1].end()

        if index_end > char_count or index_end < char_count:
            return None, None

        return index_start, index_end
    elif position_string == 'start':
        index_start = found[0].start()
        index_end = found[0].end()

        if index_start != 0:
            return None, None
        return index_start, index_end
    elif position_string == 'first':
        index_start = found[0].start()
        index_end = found[0].end()

        return index_start, index_end
    elif position_string == 'last':
        index_start = found[-1].start()
        index_end = found[-1].end()

        return index_start, index_end
    elif position_string == 'inside':
        start_index = None
        end_index = None
        for match in found:
            start_index = match.start()
            end_index = match.end()

            if start_index == 0:
                continue
            if end_index > char_count:
                continue

            break

        index_start = start_index
        index_end = end_index

    return index_start, index_end


def pad_number(name):
    """
    Add a number to a name
    :param name: str, name to pad
    :return: str
    """

    number = get_last_number(name)
    if number is None:
        number = 0
    number_string = str(number)
    index = name.rfind(number_string)
    if number < 10:
        number_string = number_string.zfill(2)

    new_name = name[0:index] + number_string + name[index + 1:]

    return new_name


def find_unique_id(ids):
    """
    Returns a unique int ID from given ids iterable, starting from 1
    :param ids: iterable (list, set, tuple)
    :return: int
    """

    if not ids or len(ids) == 0:
        return 1

    ids = sorted(set(ids))
    last_id = min(ids)

    if last_id > 1:
        return 1

    for uid in ids:
        diff = uid - last_id
        if diff > 1:
            return last_id + 1
        last_id = uid
    else:
        return uid + 1


def get_unique_name_from_list(existing_names, name):
    """
    Creates a unique name by iterating over existing_names and extracts the end digits to find a new unique name
    :param existing_names: list(str), list of strings where to search for existing indexes
    :param name: str, name to obtain a unique version from
    :return: str
    """

    if name not in existing_names:
        return name

    ids = set()

    for existing_name in existing_names:
        digits = strings.extract_digits_from_end_of_string(existing_name)
        if digits:
            ids.add(digits)
    idx = find_unique_id(ids)
    name_no_digits = strings.remove_digits_from_end_of_string(name)

    return name_no_digits + str(idx)
