from __future__ import annotations

import timeit
import logging
from typing import Callable

logger = logging.getLogger(__name__)


def fn_timer(fn: Callable):
    def function_timer(*args, **kwargs):
        t0 = timeit.default_timer()
        result = fn(*args, **kwargs)
        t1 = timeit.default_timer()
        # noinspection PyUnresolvedReferences
        logger.debug(
            "Total time running {}: {} seconds".format(
                ".".join((fn.__module__, fn.__name__)), str(t1 - t0)
            )
        )
        return result

    return function_timer
