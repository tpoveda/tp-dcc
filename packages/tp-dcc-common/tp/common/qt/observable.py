#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Qt observer pattern related functions and classes
"""

from uuid import uuid4
from functools import partial

from Qt.QtCore import Signal, QObject


class ObservableProxy(QObject):
    """
    Observer class that allows us to invoke callbacks in UI threads from non UI threads.
    """

    observerSignal = Signal(str, object)

    def __init__(self):
        super(ObservableProxy, self).__init__()

        self._mapping = dict()
        self.observerSignal.connect(self._on_call)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def add_mapping(self, callback):
        callback_uuid = str(uuid4())
        proxy_callback = partial(self.observerSignal.emit, callback_uuid)
        self._mapping[callback_uuid] = callback

        return proxy_callback

    # =================================================================================================================
    # CALLBACKS
    # =================================================================================================================

    def _on_call(self, uuid, *args, **kwargs):
        if uuid in self._mapping:
            self._mapping[uuid](args, kwargs)
