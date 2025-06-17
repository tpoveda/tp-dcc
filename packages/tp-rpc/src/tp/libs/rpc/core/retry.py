from __future__ import annotations

import time
import random
from typing import TypeVar, Callable, Any
from functools import wraps

import Pyro5.errors
from loguru import logger

T = TypeVar("T")


def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 0.5,
    max_delay: float = 5.0,
    backoff_factor: float = 2.0,
    jitter: float = 0.1,
    exceptions: tuple = (
        Pyro5.errors.CommunicationError,
        Pyro5.errors.TimeoutError,
    ),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that adds retry logic with exponential backoff to a function.

    Args:
        max_attempts: Maximum number of attempts before giving up.
        initial_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.
        backoff_factor: Multiplier for the delay after each retry.
        jitter: Random factor to add to the delay to prevent synchronized
            retries.
        exceptions: Tuple of exceptions that should trigger a retry.

    Returns:
        Decorated function with retry logic.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            attempt = 1
            delay = initial_delay

            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt >= max_attempts:
                        logger.error(
                            f"[tp-rpc][retry] Failed after {attempt} attempts: {e}"
                        )
                        raise

                    # Calculate the next delay with jitter.
                    jitter_amount = random.uniform(-jitter, jitter) * delay
                    actual_delay = min(delay + jitter_amount, max_delay)

                    logger.warning(
                        f"[tp-rpc][retry] Attempt {attempt}/{max_attempts} "
                        f"failed: {e}. Retrying in {actual_delay:.2f}s"
                    )

                    time.sleep(actual_delay)
                    delay = min(delay * backoff_factor, max_delay)
                    attempt += 1

        return wrapper

    return decorator
