from __future__ import annotations

import queue
import time
from typing import Any
from collections.abc import Callable

# Queue for executing functions on the DCC's main thread.
EXECUTION_QUEUE = queue.Queue()

# Dictionary to hold result or error of the current call.
CALL_STATE: dict[str, Any] = {}

# Keys for shared result tracking.
RETURN_VALUE_NAME = "RPC_SERVER_RETURN_VALUE"
ERROR_VALUE_NAME = "RPC_SERVER_ERROR_VALUE"


def run_in_main_thread(func: Callable, *args) -> Any:
    """Enqueue a function to be executed on the main thread and wait for
    its result.

    This function is used by the @main_thread decorator to safely execute
    UI-sensitive code (e.g., Maya cmds) that must run in the main thread.

    Args:
        func: The function to be executed.
        *args: Positional arguments to pass to the function.

    Returns:
        Any: The return value from the function if successful.

    Raises:
        Exception: Re-raises any exception raised by the function.
        TimeoutError: If execution doesn't complete within the timeout window.
    """

    timeout = 90  # seconds

    CALL_STATE.pop(RETURN_VALUE_NAME, None)
    CALL_STATE.pop(ERROR_VALUE_NAME, None)
    EXECUTION_QUEUE.put((func, args))

    for _ in range(timeout * 10):
        if RETURN_VALUE_NAME in CALL_STATE:
            return CALL_STATE.pop(RETURN_VALUE_NAME)
        elif ERROR_VALUE_NAME in CALL_STATE:
            raise CALL_STATE.pop(ERROR_VALUE_NAME)
        time.sleep(0.1)

    raise TimeoutError(f"Call to '{func.__name__}' timed out after {timeout} seconds.")


def process_main_thread_queue(*args):
    """Run all queued calls in EXECUTION_QUEUE.

    This should be scheduled periodically by the DCC (e.g., via Maya
    evalDeferred or idle event).

    Args:
        *args: Extra arguments (ignored, supports flexible binding).
    """

    while not EXECUTION_QUEUE.empty():
        func, call_args = EXECUTION_QUEUE.get()
        try:
            CALL_STATE[RETURN_VALUE_NAME] = func(*call_args)
        except Exception as e:
            CALL_STATE[ERROR_VALUE_NAME] = e
            raise
