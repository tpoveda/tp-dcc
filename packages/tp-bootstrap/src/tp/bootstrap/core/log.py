from __future__ import annotations

import os
import sys

from loguru import logger

from . import constants


def setup_tp_dcc_logger():
    """Sets up the TP DCC logger using loguru."""

    # Remove existing handlers first.
    logger.remove()

    level = os.environ.get(constants.LOG_LEVEL_ENV_VAR, "INFO").upper()

    logger.add(
        sys.stderr,
        level=level,
        enqueue=True,
        backtrace=True,
        diagnose=True,
        colorize=True,
        format="{time:YYYY-MM-DD HH:mm:ss} [{level}] ({name}.{function}:{line}) > {message}",
    )

    logger.debug("TP DCC logger initialized with loguru.")
