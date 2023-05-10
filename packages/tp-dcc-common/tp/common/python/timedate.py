#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utility functions related with time and date
"""

import time
from datetime import datetime


def convert_number_to_month(month_int):
    """
    Return a month as string given a month number.

    :param int month_int:
    :return:
    :rtype: str
    """

    months = ['January',
              'February',
              'March',
              'April',
              'May',
              'June',
              'July',
              'August',
              'September',
              'October',
              'November',
              'December']

    month_int -= 1
    if month_int < 0 or month_int > 11:
        return

    return months[month_int]


def get_current_time(date_and_time=True, reverse_date=False):
    """
    Returns current time.

    :param bool date_and_time: whether to return only the time or time and data.
    :param bool reverse_date: whether to return date with {year}-{month}-{day} format or {day}-{month}-{year} format.
    :return: current time as a string.
    :rtype: str
    """

    mtime = time.time()
    date_value = datetime.fromtimestamp(mtime)
    hour = str(date_value.hour)
    minute = str(date_value.minute)
    second = str(int(date_value.second))

    if len(hour) == 1:
        hour = '0' + hour
    if len(minute) == 1:
        minute = '0' + minute
    if len(second) == 1:
        second += '0'

    time_value = f'{hour}:{minute}:{second}'

    if not date_and_time:
        return time_value
    else:
        year = date_value.year
        month = date_value.month
        day = date_value.day

        if reverse_date:
            return f'{year}-{month}-{day} {time_value}'
        else:
            return f'{day}-{month}-{year} {time_value}'


def get_current_date(reverse_date=False, separator=None):
    """
    Returns current date
    :param reverse_date: bool, Whether to return date with {year}-{month}-{day} format or {day}-{month}-{year} format
    :param separator: str
    :return: str
    """

    separator = separator or '-'
    mtime = time.time()
    date_value = datetime.fromtimestamp(mtime)
    year = date_value.year
    month = date_value.month
    day = date_value.day

    if reverse_date:
        return f'{year}{separator}{month}{separator}{day}'
    else:
        return f'{day}{separator}{month}{separator}{year}'


def get_date_and_time(reverse_date=False, separator=None):
    """
    Returns current date and time
    :return:
    """

    separator = separator or '/'
    date_value = datetime.now()
    year = date_value.year
    month = date_value.month
    day = date_value.day
    hour = str(date_value.hour)
    minute = str(date_value.minute)
    second = str(int(date_value.second))

    if len(hour) == 1:
        hour = '0' + hour
    if len(minute) == 1:
        minute = '0' + minute
    if len(second) == 1:
        second = second + '0'

    if reverse_date:
        return f'{day}{separator}{month}{separator}{year} {hour}:{minute}:{second}'
    else:
        return f'{month}{separator}{day}{separator}{year} {hour}:{minute}:{second}'


def time_ago(timestamp):
    """
    Returns a pretty string for how long ago the given timestamp was
    Example:
        print timeAgo("2017-06-06 01:56:00")
        # 2 years ago
    :param str timestamp:
    :rtype: str
    """

    t1 = int(timestamp)
    t1 = datetime.fromtimestamp(t1)

    t2 = datetime.now()
    diff = t2 - t1

    day_diff = diff.days
    seconds_diff = diff.seconds

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if seconds_diff < 10:
            return 'just now'
        if seconds_diff < 60:
            return str(seconds_diff) + ' seconds ago'
        if seconds_diff < 120:
            return 'a minute ago'
        if seconds_diff < 3600:
            return str(seconds_diff / 60) + " minutes ago"
        if seconds_diff < 7200:
            return 'an hour ago'
        if seconds_diff < 86400:
            return str(seconds_diff / 3600) + ' hours ago'

    if day_diff == 1:
        return 'yesterday'

    if day_diff < 7:
        return str(day_diff) + ' days ago'

    if day_diff < 31:
        v = day_diff / 7
        if v == 1:
            return str(v) + ' week ago'
        return str(day_diff / 7) + ' weeks ago'

    if day_diff < 365:
        v = day_diff / 30
        if v == 1:
            return str(v) + ' month ago'
        return str(v) + ' months ago'

    v = day_diff / 365
    if v == 1:
        return str(v) + ' year ago'
    return str(v) + ' years ago'
