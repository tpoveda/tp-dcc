#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains observer pattern related functions and classes
"""

import time

from tp.core import log


logger = log.tpLogger


class Observable(object):
    """
    Basic observable/observer pattern implementation
    """

    def __init__(self):

        # Dictionary that maps instance references with dictionaries where the key is the event id and its value
        # it is the callback that should be called
        self._connected = dict()

    def connect(self, instance, callback, event_id):
        """
        Connects instance to an event
        :param instance: object
        :param callback: function, function that will be called when teh event happens
        :param event_id: id, unique identifier for the event
        """

        self._connected.setdefault(instance, dict())
        self._connected[instance][event_id] = callback

    def disconnect(self, instance, event_id=None):
        """
        Disconnects instance from an event
        :param instance: object
        :param event_id: id, unique identifier of the event
        """

        if instance not in self._connected:
            return
        if event_id is None:
            self._connected[instance] = dict()
        else:
            del self._connected[instance][event_id]

    def emit(self, event_id, arg=None):
        """
        Emits event and all connected instances will be notified
        :param event_id: int
        :param arg:
        """

        if not self._connected:
            return
        start = time.perf_counter()
        for k in self._connected:
            if event_id in self._connected[k]:
                self._connected[k][event_id](arg)
        stop = time.perf_counter()
        if (stop - start) > 0.100:
            logger.warning('*** SLOW *** {}.broadcast(event_id={}'.format(self.__class__.__name__, event_id) + (
                ',{}'.format(arg) if arg else '') + ') took %.2f' % (stop - start))
