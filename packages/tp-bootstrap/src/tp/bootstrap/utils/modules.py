from __future__ import annotations

from typing import Any
from collections.abc import Callable

from loguru import logger


def run_script_function(
    file_path: str, func_name: str, message: str, *args: Any
) -> Any:
    """Run a function from a Python script file.

    Args:
        file_path: Full path to the Python script.
        func_name: Name of the function to execute inside the script.
        message: The debug message to log before running the function.
        *args: Positional arguments to pass to the function.

    Returns:
        The return value from the function if found and executed; None
        otherwise.
    """

    try:
        scope: dict[str, Callable] = {}
        with open(file_path, "r", encoding="utf-8") as f:
            exec(compile(f.read(), file_path, "exec"), scope)

        func = scope.get(func_name)
        if func is None:
            logger.error(f"Function '{func_name}' not found in {file_path}.")
            return None

        logger.debug(message)
        return func(*args)

    except Exception as e:
        logger.error(f"Problem loading {file_path}: {e}", exc_info=True)
        return None
