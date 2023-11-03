from __future__ import annotations

import collections.abc
from collections import deque
from typing import Iterator, Any


def flatten(*args, **kwargs) -> Iterator[Any]:
    """
    Returns a generator that flattens the given items and yields them.

    :return: flatten iterated items.
    :rtype: Iterator[Any]
    """

    queue = deque(args)
    while len(queue) > 0:
        item = queue.popleft()

        if isinstance(item, collections.abc.Sequence) and not isinstance(item, str):

            queue.extendleft(reversed(item))
        elif isinstance(item, collections.abc.Iterator) and not isinstance(item, str):
            queue.extendleft(reversed(list(item)))
        else:
            yield item
