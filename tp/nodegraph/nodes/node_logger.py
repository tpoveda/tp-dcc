from __future__ import annotations

import logging

from ..core.node import Node
from ..core import datatypes as dt

logger = logging.getLogger(__name__)


class LoggerNode(Node):
    """
    Node that logs messages.
    """

    NODE_NAME = "Log"
    CATEGORY = "Utils"
    IS_EXEC = True
    AUTO_INIT_EXECS = True

    # noinspection PyAttributeOutsideInit
    def setup_ports(self):
        super().setup_ports()

        self.in_message = self.add_input(dt.String, "Message")
        self.in_info = self.add_input(dt.Boolean, "As Info", value=True)
        self.in_warning = self.add_input(dt.Boolean, "As Warning", value=False)
        self.in_error = self.add_input(dt.Boolean, "As Error", value=False)

    def execute(self):
        if self.in_info.value:
            logger.info(self.in_message.value)
        if self.in_warning.value:
            logger.warning(self.in_warning.value)
        if self.in_error.value:
            logger.error(self.in_error.value)
