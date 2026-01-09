from __future__ import annotations

import logging

from . import consts

logger = logging.getLogger(__name__)


def can_be_serialized(class_name: str, data: dict) -> bool:
    """Function that checks whether the given class can be serialized.

    Args:
        class_name: name of the class to check.
        data: data to check.

    Returns:
        Whether the class can be serialized or not.
    """

    serializable_class_name = data.get(consts.CLASS_NAME_ATTR)
    if (
        serializable_class_name is not None
        and serializable_class_name != class_name
    ):
        logger.debug(
            f'Cannot deserialize "{class_name}" from serialized data of class "{serializable_class_name}"'
        )
        return False

    data.pop(consts.CLASS_NAME_ATTR, None)
    data.pop(consts.CLASS_VERSION_ATTR, None)

    return True
