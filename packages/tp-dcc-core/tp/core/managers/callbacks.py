#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base callbackManager class
"""

from tp.core import log, dcc
from tp.core.api import callback as dcc_callback
from tp.core.abstract import callback
from tp.common.python import decorators

logger = log.tpLogger


@decorators.add_metaclass(decorators.Singleton)
class CallbacksManager:
    """
    Static class used to manage all callbacks instances
    """

    _initialized = False
    _callbacks = dict()

    @classmethod
    def initialize(cls):
        """
        Initializes all module callbacks
        """

        if cls._initialized:
            return

        default_callbacks = {'Tick': callback.PythonTickCallback}

        try:
            shutdown_type = getattr(dcc_callback.Callback(), 'ShutdownCallback')
        except AttributeError:
            shutdown_type = None

        for callback_name in dcc.callbacks():

            # Get callback type from tpDcc.DccCallbacks
            n_type = getattr(dcc.DccCallbacks, callback_name)[1]['type']
            if n_type == 'simple':
                callback_type = callback.SimpleCallback
            elif n_type == 'filter':
                callback_type = callback.FilterCallback
            else:
                logger.warning(f'Callback Type "{n_type}" is not valid! Using Simplecallback instead ...')
                callback_type = callback.SimpleCallback

            # We extract callback types from the specific registered callbacks module
            if not dcc_callback.Callback():
                logger.warning(f'DCC {dcc.name()} has no callbacks registered!')
                return

            callback_class = getattr(dcc_callback.Callback(), f'{callback_name}Callback', None)
            if not callback_class:
                callback_class = default_callbacks.get(callback_name, callback.ICallback)
                logger.debug(
                    f'Dcc {dcc.name()} does not provides an ICallback'
                    f' for {callback_name}Callback. Using {callback_class.__name__} instead')
            new_callback = CallbacksManager._callbacks.get(callback_name, None)
            if new_callback:
                new_callback.cleanup()

            CallbacksManager._callbacks[callback_name] = callback_type(callback_class, shutdown_type)

            logger.debug(f'Creating Callback "{callback_name}" of type "{callback_class}" ...')

        cls._initialized = True

    @classmethod
    def register(cls, callback_type, fn, owner=None):
        """
        Registers, is callback exists, a new callback.

        :param str callback_type: type of callback.
        :param callablce fn: Python function to be called when callback is emitted.
        :param type or None owner: optional callback owner.
        """

        if type(callback_type) in [list, tuple]:
            callback_type = callback_type[0]

        if callback_type in CallbacksManager._callbacks:
            CallbacksManager._callbacks[callback_type].register(fn, owner)

    @classmethod
    def unregister(cls, callback_type, fn):
        """
        Unregisters, is callback exists, a new callback.

        :param str callback_type: type of callback.
        :param callable fn: Python function we want to unregister.
        """

        if type(callback_type) in [list, tuple]:
            callback_type = callback_type[0]

        if callback_type in CallbacksManager._callbacks:
            CallbacksManager._callbacks[callback_type].unregister(fn)

    @classmethod
    def unregister_owner_callbacks(cls, owner):
        """
        Unregister all the callbacks from all registered callbacks that belongs to a specific owner.

        :param type owner: callback owner.
        """

        if not cls._initialized:
            return

        for callback_name, register_callback in CallbacksManager._callbacks.items():
            register_callback.unregister_owner_callbacks(owner=owner)

    @classmethod
    def cleanup(cls):
        """
        Cleanup all module callbacks.
        """

        # if not cls._initialized:
        #     return

        callbacks_to_clean = list()
        for callback_name, register_callback in CallbacksManager._callbacks.items():
            register_callback.cleanup()
            callbacks_to_clean.append(callback_name)
        for callback_name in callbacks_to_clean:
            CallbacksManager._callbacks.pop(callback_name)

        cls._initialized = False
