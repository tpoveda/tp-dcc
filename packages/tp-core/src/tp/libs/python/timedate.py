from __future__ import annotations

from datetime import datetime


def get_date_and_time(reverse_date: bool = False, separator: str | None = None):
    """
    Returns current date and time in a formatted string.

    :param reverse_date: whether to return date in reverse order.
    :param separator: separator to use between date and time values.
    :return: formatted date and time string.
    """

    separator = separator or "/"
    date_value = datetime.now()
    year = date_value.year
    month = date_value.month
    day = date_value.day
    hour = str(date_value.hour)
    minute = str(date_value.minute)
    second = str(int(date_value.second))

    if len(hour) == 1:
        hour = "0" + hour
    if len(minute) == 1:
        minute = "0" + minute
    if len(second) == 1:
        second = second + "0"

    if reverse_date:
        return f"{day}{separator}{month}{separator}{year} {hour}:{minute}:{second}"
    else:
        return f"{month}{separator}{day}{separator}{year} {hour}:{minute}:{second}"
