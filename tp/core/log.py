from __future__ import annotations

import os
import logging
from typing import Iterator
from logging.handlers import RotatingFileHandler

from .. import dcc
from .consts import (
    LOGGER_NAME,
    LOG_LEVEL_ENV_VAR,
    LOG_LEVEL_DEFAULT,
    ENV_VAR,
    EnvironmentMode,
)

_LOGGER_STATES = {}


def setup_logger(remove_handlers: bool = True):
    """
    Setup root logger for tp package.
    """

    global _LOGGER_STATES
    _LOGGER_STATES.clear()

    logger = logging.getLogger(LOGGER_NAME)

    log_level = os.getenv(LOG_LEVEL_ENV_VAR, LOG_LEVEL_DEFAULT).upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    if remove_handlers:
        for handler in logger.handlers[:]:  # Copy of handlers list
            logger.removeHandler(handler)

    if logger.handlers:
        return logger

    # Console handler.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logger.level)
    # noinspection SpellCheckingInspection
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(module)s.%(funcName)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (only in production environment).
    env = os.getenv(ENV_VAR, EnvironmentMode.Production.value)
    log_path = os.path.join(
        os.path.expanduser("~"), f"tp_{dcc.current_dcc()}_{env}_{os.getpid()}.log"
    )
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
    )
    file_handler.setLevel(logger.level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def iterate_child_loggers() -> Iterator[logging.Logger]:
    """
    Iterate over all loggers that are children of the root logger.
    """

    for name, logger in logging.Logger.manager.loggerDict.items():
        if name.startswith(f"{LOGGER_NAME}.") and isinstance(logger, logging.Logger):
            yield logger


def child_loggers() -> list[logging.Logger]:
    """
    Return all loggers that are children of the root logger.
    """

    return list(iterate_child_loggers())


def disable_all_child_loggers():
    """
    Disable all loggers that are children of the root logger.
    """

    global _LOGGER_STATES
    _LOGGER_STATES.clear()

    for logger in iterate_child_loggers():
        _LOGGER_STATES[logger.name] = {
            "level": logger.level,
            "propagate": logger.propagate,
        }
        logger.setLevel(logging.CRITICAL + 1)
        logger.propagate = False


def restore_all_child_loggers():
    """
    Restore all loggers that are children of the root logger.
    """

    global _LOGGER_STATES

    root_logger = logging.getLogger(LOGGER_NAME)

    restored_loggers: list[logging.Logger] = []
    for name, state in _LOGGER_STATES.items():
        logger = logging.getLogger(name)
        logger.setLevel(state["level"])
        logger.propagate = state["propagate"]
        restored_loggers.append(logger)

    for logger in iterate_child_loggers():
        if logger in restored_loggers:
            continue
        logger.setLevel(root_logger.level)
        logger.propagate = True

    _LOGGER_STATES.clear()


def disable_specific_logger(logger_name: str):
    """
    Disable a specific logger by saving its original state and setting its level to an extremely high level.

    :param logger_name: Name of the logger to disable.
    """

    global _LOGGER_STATES
    logger = logging.getLogger(logger_name)

    # Store the original state if it's not already stored.
    if logger_name not in _LOGGER_STATES:
        _LOGGER_STATES[logger_name] = {
            "level": logger.level,
            "propagate": logger.propagate,
        }

    # Disable the logger by setting level high and turning off propagation.
    logger.setLevel(logging.CRITICAL + 1)
    logger.propagate = False


def enable_specific_logger(logger_name: str):
    """
    Enable a specific logger by restoring its original state.

    :param logger_name: Name of the logger to enable.
    """

    global _LOGGER_STATES

    if logger_name in _LOGGER_STATES:
        logger = logging.getLogger(logger_name)
        settings = _LOGGER_STATES[logger_name]
        logger.setLevel(settings["level"])
        logger.propagate = settings["propagate"]

        # Remove the restored logger from the stored states.
        del _LOGGER_STATES[logger_name]


def disable_loggers_with_prefix(prefix):
    """
    Disable all loggers whose names start with the given prefix.
    This function saves the original level and propagate settings for restoration.
    """

    global _LOGGER_STATES
    _LOGGER_STATES.clear()

    for name, logger in logging.Logger.manager.loggerDict.items():
        if name.startswith(prefix) and isinstance(logger, logging.Logger):
            _LOGGER_STATES[name] = {
                "level": logger.level,
                "propagate": logger.propagate,
            }
            logger.setLevel(logging.CRITICAL + 1)
            logger.propagate = False


def enable_loggers_with_prefix(prefix):
    """
    Enable all loggers whose names start with the given prefix by restoring their original states.
    """
    global _LOGGER_STATES

    # root_logger = logging.getLogger(LOGGER_NAME)

    restored_loggers: list[logging.Logger] = []
    for name, settings in _LOGGER_STATES.items():
        if name.startswith(prefix):
            logger = logging.getLogger(name)
            logger.setLevel(settings["level"])
            logger.propagate = settings["propagate"]
            restored_loggers.append(logger)

    # for logger in iterate_child_loggers():
    #     if logger in restored_loggers or not logger.name.startswith(prefix):
    #         continue
    #     logger.setLevel(root_logger.level)
    #     logger.propagate = True

    # Clear the stored states after restoring
    _LOGGER_STATES.clear()
