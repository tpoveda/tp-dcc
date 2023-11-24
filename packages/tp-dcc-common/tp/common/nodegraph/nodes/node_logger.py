from __future__ import annotations

from typing import Any, Callable

from overrides import override

from tp.core import log
from tp.tools.rig.noddle.builder import api

logger = log.tpLogger


class LoggerNode(api.NoddleNode):
    ID = 11
    IS_EXEC = True
    ICON = 'func.png'
    AUTO_INIT_EXECS = True
    DEFAULT_TITLE = 'Log'
    CATEGORY = 'Utils'

    @override
    def setup_sockets(self):
        super().setup_sockets()

        self.in_message = self.add_input(api.dt.String, 'Message')
        self.in_info = self.add_input(api.dt.Boolean, 'As Info', value=True)
        self.in_warning = self.add_input(api.dt.Boolean, 'As Warning', value=False)
        self.in_error = self.add_input(api.dt.Boolean, 'As Error', value=False)
        self.update_title()

    @override
    def execute(self) -> Any:
        if self.in_info.value():
            logger.info(self.in_message.value())
        if self.in_warning.value():
            logger.warning(self.in_message.value())
        if self.in_error.value():
            logger.error(self.in_message.value())

    @override
    def _setup_signals(self):
        super()._setup_signals()
        self.in_message.signals.valueChanged.connect(self.update_title)

    def update_title(self):
        """
        Updates node title.
        """

        self.title = f'{self.DEFAULT_TITLE}: {self.in_message.value()}'


def register_plugin(register_node: Callable, register_function: Callable, register_data_type: Callable):
    register_node(LoggerNode.ID, LoggerNode)
