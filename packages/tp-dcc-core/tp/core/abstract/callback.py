# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that base classes used by the callback system
"""

from traceback import format_exc

from tp.core import log
from tp.common.python import decorators

logger = log.tpLogger


class ICallback(object):
    """
    Class that defines basic callback interface functions
    """

    @classmethod
    @decorators.abstractmethod
    def register(cls, fn, owner=None):
        """
        Register the given Python function
        :param fn: function, python function to register
        :param owner: class, class owner of the function
        :return: token of non defined type to later unregister the function
        """

        raise None

    @classmethod
    @decorators.abstractmethod
    def unregister(cls, token):
        """
        Unregister the given Python function
        :param token: token, token provided by register method
        """

        return None

    @classmethod
    @decorators.abstractmethod
    def filter(cls, *args):
        """
        Function used to process the arguments during an execution of a callback
        :param args: variable list of arguments pass from the callback function to be evaluated
        """

        return False, None


class AbstractCallback(object):
    """
    Class that defines basic callback interface functions
    This class manages a pair of notifier and listener objects
    """

    def __init__(self, notifier, shutdown_notifier, owner=None):
        super(AbstractCallback, self).__init__()

        self._notifier = notifier
        self._enabled_stack = list()
        self._registry = list()

        self._shutdown_notifier = None
        self._shutdown_token = None
        if shutdown_notifier and notifier != shutdown_notifier:
            self._shutdown_notifier = shutdown_notifier
            self._shutdown_token = self._shutdown_notifier.register(self._shutdown)

    # def __del__(self):
    #     if self._notifier:
    #         self._shutdown([])

    def _connect(self, fn):
        """
        Internal callback registration function
        :param fn: Python function to register as a listener to the Sender
        :return:
        """

        return self._notifier.register(fn)

    def _disconnect(self, token):
        """
        Internal callback unregistration function
        :param token: valid token returned from a previuous _connect() call
        :return: None if unregistration was successfull or the unchanged value from token otherwise
        """

        if token:
            return self._notifier.unregister(token)

        return None

    def _filter(self, *args):
        """
        Internal function to evaluate if the callback from the notifier is valid.
            Test the validity of the message with the custom function.
        @param *args A variable list of arguments receivied from the notifier.
        @return      A tuple of indeterminant length (bool, object, ...) that is (True, Valid Data, ...) if callback
            should be passed to the listners; (False, None) otherwise.
        """

        return self._notifier.filter(*args)

    def _shutdown(self, *args):
        """
        Forces an unregistering and disconnection from the sender. This method should be overriden by subclasse
        """

        if self._shutdown_token and self._shutdown_notifier:
            self._shutdown_notifier.unregister(self._shutdown_token)
        self._shutdown_notifier = None
        self._notifier = None

    def _push(self, state):
        """
        Function to set the enable state while maintaining a history of previous enabled states
        :param state: bool, the enable state of the callback
        """

        if self.valid:
            self._enabled_stack.append(self.enabled)
            self.enabled = state

    def _pop(self):
        """
        Function to restore the enable state to a previous enabled state
        :return: True if the callback is enabled as a result of the restoration or False otherwise
        """

        if self.valid and self._enabled_stack:
            self.enabled = self._enabled_stack.pop()

        return self.enabled

    @property
    def valid(self):
        """!
        Convenience property to query the validity of this callback.
        @return True if the callback has a notifier; False otherwise.
        """

        return bool(self._notifier)

    @property
    def empty(self):
        """
        Convenience property to query the existence of listeners to this callback.
        @return True if the callback has listeners registered; False otherwise.
        @warning This method must be overriden by subclasses.
        """

        return True

    @property
    def connected(self):
        """
        Convenience property to query the 'connected' state of the callback.
        @return True if the callback has connected itself with the INotifier implementation.
        @warning This method must be overriden by subclasses.
        """

        return False

    @property
    def enabled(self):
        """
        Convenience property to query the 'not empty' and 'connected' state of the callback.
        @return True if the callback has listeners and is connected the to the INotifier implementation.
        @warning This method must be overriden by subclasses.
        """

        return False

    @property
    def registry(self):
        """
        Convenience property to query all registerd functions of a callback
        :return: list<fn>
        """

        return None

    @enabled.setter
    def enabled(self, value):
        """
        Convenience property to set the 'enable' state of the callback.  Modifying the enable state either toggles
            the 'connected' state of the callback but maintains the list of listeners.
        @param value The enable state of the callback.
        @warning This method must be overriden by subclasses.
        """
        pass

    def suspend(self):
        """
        Method to the suspend the callback connection.
        """

        self._push(False)

    def resume(self):
        """
        Method to resume the nofitication connection.
        @return True if the callback connection has been resumed succesfully; False otherwise.
        """

        return self._pop()

    def unregister(self, fn):
        """
        Removes a listener from this inestance.
        @param fn A valid python function with a variable number of arguments (i.e. *args).
        @warning This method must be overriden by subclasses.
        """

        pass

    def register(self, fn, owner=None):
        """
        Adds a listener to this instance.

        @param fn A valid python function with a variable number of arguments (i.e. *args).
        @param owner: class, owner of the callback
        @warning This method must be overriden by subclasses.
        """

        pass

    def unregister_owner_callbacks(self, owner):
        """
        Removes all notifiers registered by a certain owner
        :param owner: class
        """

        pass

    def cleanup(self):
        """
        Method to terminate the callback
        """

        return self._shutdown()


class SimpleCallback(AbstractCallback):
    """
    Simple implementation of Abstractcallback interface
    It maintains a one-to-one relationship between listener and notifiers whitout any event filtering
    """

    class RegistryEntry(object):
        def __init__(self, callback, token, owner=None):
            self.callback = callback
            self.token = token
            self.owner = owner

    def __init__(self, notifier, shutdown_notifier, owner=None):
        super(SimpleCallback, self).__init__(notifier=notifier, shutdown_notifier=shutdown_notifier, owner=owner)

    def _shutdown(self, *args):
        """
        Forces an unregistering from the notifier
        """

        logger.debug('Started: ({}) {} Shutdown'.format(str(self._notifier), self.__class__.__name__))
        for entry in self._registry:
            logger.debug(
                '{}._shutdown - Disconnecting ({})'.format(str(self._notifier), self.__class__.__name__, str(entry)))
            entry.token = self._disconnect(entry.token)
        del self._registry[:]

        super(self.__class__, self)._shutdown(*args)
        logger.debug('Complete: ({}) {} Shutdown'.format(str(self._notifier), self.__class__.__name__))

    @property
    def empty(self):
        """
        Convenience property to query the existence of listeners to this callback.
        @return True if the callback has listeners registered; False otherwise.
        """

        return not bool(self._registry)

    @property
    def connected(self):
        """
        Convenience property to query the 'connected' state of the callback.
        @return True if the callback has connected itself with the INotifier implementation.
        """

        return all(e.token for e in self._registry)

    @property
    def enabled(self):
        """
        Convenience property to query the 'not empty' and 'connected' state of the callback.
        @return True if the callback has listeners and is connected the to the INotifier implementation.
        """

        return not self.empty and bool(self.connected)

    def invoke_callbacks(self):
        """
        Manually invoke all the callbacks registered to the callback
        """

        for entry in self._registry:
            try:
                entry.callback()
            except Exception:
                from traceback import format_exc
                logger.error(format_exc())

    @enabled.setter
    def enabled(self, value):
        """!
        Convenience property to set the 'enable' state of the callback.  Modifying the enable state either toggles
            the 'connected' state of the callback but maintains the list of listeners.

        @param value The enable state of the callback.
        """

        for entry in self._registry:
            if not value and entry.token:
                entry.token = self._disconnect(entry.token)
            elif value and not entry.token:
                entry.token = self._connect(entry.callback)

    def register(self, fn, owner=None):
        """
        Adds a listener to this instance
        @param fn: a valid Python function with a varaible number of arguments (exp. *args)
        @param owner: class, owner of the callback
        """

        entry = next((e for e in self._registry if e.callback == fn), None)
        logger.debug(
            'Started: ({}) {} Register - fn:"{}", owner:"{}", entry:"{}"'.format(
                str(self._notifier), self.__class__.__name__, str(fn), owner, str(entry)))
        if not entry:
            token = self._connect(fn) if self.connected else None
            logger.debug(
                '({}) {} Register - token:"{}"'.format(str(self._notifier), self.__class__.__name__, str(token)))
            self._registry.append(SimpleCallback.RegistryEntry(fn, token, owner=owner))
        logger.debug('Completed: ({}) {} Register'.format(str(self._notifier), self.__class__.__name__))

    def unregister(self, fn):
        """
        Removes a listener from this instance
        :param fn: a valid Python function with a varaible number of arguments (exp. *args)
        """

        entry = next((e for e in self._registry if e.callback == fn), None)
        logger.debug(
            'Started: ({}) {} Unregister - fn:"{}", entry:"{}"'.format(
                str(self._notifier), self.__class__.__name__, str(fn), str(entry)))
        if entry:
            self._disconnect(entry.token)
            self._registry.remove(entry)
        logger.debug('Completed: ({}) {} Unregister'.format(str(self._notifier), self.__class__.__name__))

    def unregister_owner_callbacks(self, owner):
        """
        Removes all notifiers registered by a certain owner
        :param owner: class
        """

        entry = next((e for e in self._registry if e.owner == owner), None)
        logger.debug(
            'Started: ({}) {} Unregister - owner:"{}", entry:"{}"'.format(
                str(self._notifier), self.__class__.__name__, str(owner), str(entry)))
        if entry:
            self._disconnect(entry.token)
            self._registry.remove(entry)
        logger.debug('Completed: ({}) {} Unregister'.format(str(self._notifier), self.__class__.__name__))


class FilterCallback(AbstractCallback, object):
    """
    Provides a implementation of an Abstractcallback interface that allows the filtering of the callback
    generated from the notifier. It maintains a many-to-one relationship between listeners and notifier
    """

    class RegistryEntry(object):
        def __init__(self, callback, owner=None):
            self.callback = callback
            self.owner = owner

    def __init__(self, notifier, shutdown_notifier, owner=None):
        super(FilterCallback, self).__init__(notifier=notifier, shutdown_notifier=shutdown_notifier, owner=owner)

        self._token = None

    def _shutdown(self, *args):
        """
        Forces an unregistering from the notifier
        """

        logger.debug('Started: ({}) {} Shutdown'.format(str(self._notifier), self.__class__.__name__))
        if self._token:
            self._token = self._disconnect(self._token)
            self._token = None
        del self._registry[:]

        super(self.__class__, self)._shutdown(*args)
        logger.debug('Complete: ({}) {} Shutdown'.format(str(self._notifier), self.__class__.__name__))

    def _notify(self, *args):
        """
        Internal function registered with the notifier. Evaluates the condition with _filter during the callback.
        If its valid, it will broadcast the callback to the listener via _execute().
        All notifier data is passed on to the user via _execute().
        :param args: A variable list of arguments received from the notifier
        :return:
        """

        fargs = self._filter(*args)
        if fargs[0]:
            self._execute(*fargs[1:])

    def _execute(self, *args):
        """
        Internal function to notify all listeners registered to the current instance of the class
        :param args: A variable list of arguments received from the notifier
        """

        for entry in self._registry:
            try:
                entry.callback(*args)
            except Exception:
                logger.error(format_exc())

    @property
    def empty(self):
        """
        Convenience property to query the existence of listeners to this callback.
        @return True if the callback has listeners registered; False otherwise.
        """

        return not bool(self._registry)

    @property
    def connected(self):
        """
        Convenience property to query the 'connected' state of the callback.
        @return True if the callback has connected itself with the INotifier implementation.
        """

        return bool(self._token)

    @property
    def enabled(self):
        """
        Convenience property to query the 'not empty' and 'connected' state of the callback.
        @return True if the callback has listeners and is connected the to the INotifier implementation.
        """

        return not self.empty and bool(self.connected)

    @enabled.setter
    def enabled(self, value):
        """!
        Convenience property to set the 'enable' state of the callback.  Modifying the enable state either toggles
            the 'connected' state of the callback but maintains the list of listeners.

        @param value The enable state of the callback.
        """

        if not value and self._token:
            self._token = self._disconnect(self._token)
        elif value and not self._token:
            self._token = self._connect(self._notify)

    def register(self, fn, owner=None):
        """
        Adds a listener to this instance
        @param fn: a valid Python function with a variable number of arguments (exp. *args)
        @param owner: class, owner of the callback
        """

        logger.debug(
            'Started: ({}) {} Register - fn:"{}", owner:"{}", IsEmpty:"{}"'.format(
                str(self._notifier), self.__class__.__name__, str(fn), owner, bool(self.empty)))
        if self.empty:
            self._token = self._connect(self._notify)
            logger.debug(
                '({}) {} Register - token:"{}"'.format(str(self._notifier), self.__class__.__name__, str(self._token)))
        self._registry.append(FilterCallback.RegistryEntry(fn, owner=owner))
        logger.debug('Completed: ({}) {} Register'.format(str(self._notifier), self.__class__.__name__))

    def unregister(self, fn):
        """
        Removes a listener from this instance
        :param fn: a valid Python function with a varaible number of arguments (exp. *args)
        """

        entry = next((e for e in self._registry if e.callback == fn), None)
        logger.debug(
            'Started: ({}) {} Unregister - fn:"{}", IsEmpty:"{}"'.format(
                str(self._notifier), self.__class__.__name__, str(fn), bool(self.empty)))

        if entry:
            self._registry.remove(entry)
        # else:
        #     dcclib.logger.warning('({}) {} Unregister - fn:"{}" not in list - perhaps already removed?'.format(
        #     str(self._notifier), self.__class__.__name__, str(fn)))

        if self.empty and self.connected:
            logger.debug(
                '({}) {} Unregister token:"{}"'.format(str(self._notifier), self.__class__.__name__, str(self._token)))
            self._token = self._disconnect(self._token)
        logger.debug('Completed: ({}) {} Unregister'.format(str(self._notifier), self.__class__.__name__))

    def unregister_owner_callbacks(self, owner):
        """
        Removes all notifiers registered by a certain owner
        :param owner: class
        """

        entry = next((e for e in self._registry if e.owner == owner), None)
        logger.debug(
            'Started: ({}) {} Unregister - owner:"{}", entry:"{}"'.format(
                str(self._notifier), self.__class__.__name__, str(owner), str(entry)))
        if entry:
            self._registry.remove(entry)
        # else:
        #     dcclib.logger.warning('({}) {} Unregister - fn:"{}" not in list - perhaps already removed?'.format(
        #     str(self._notifier), self.__class__.__name__, str(owner)))

        if self.empty and self.connected:
            logger.debug(
                '({}) {} Unregister token:"{}"'.format(str(self._notifier), self.__class__.__name__, str(self._token)))
            self._token = self._disconnect(self._token)
        logger.debug('Completed: ({}) {} Unregister'.format(str(self._notifier), self.__class__.__name__))


class CallbackInstance(object):
    """
    Utility class to sync callback registration to the lifetime of an object instance
    """

    def __init__(self, callback, fn):
        """
        Constructor
        :param callback: Abstractcallback, instance
        :param fn: Python function to register and unregister withing the scope
        """

        super(CallbackInstance, self).__init__()

        self._notify = fn
        self._callback = callback
        if self._callback:
            self._callback.register(self._notify)

    # def __del__(self):
    #     """
    #     Destructor
    #     """
    #
    #     if self._callback:
    #         self._callback.unregister(self._notify)
    #     self._callback = None
    #     self._notify = None

    @property
    def callback(self):
        """
        Convenience property to access the callback implementation associated with this callbackInstance
        """

        return self._callback


class PythonTickCallback(ICallback, object):
    """
    This notifier implements a Tick notifier
    """

    interval = 0.05         # Tick interval (seconds)
    tick_threads = dict()   # Collection of token pairs

    @classmethod
    def register(cls, fn):
        """
        Register the given Python function
        :param fn: function, python function to register
        :return: token of non defined type to later unregister the function
        """

        fn_id = id(fn)
        if cls.tick_threads.get(fn_id, None) is not None:
            logger.warning('{} already registered with PythonTickNotifier'.format(str(fn)))
            return None

        repeater = cls._tick(fn_id)
        cls.tick_threads[fn_id] = (fn, repeater)

        return fn_id

    @classmethod
    def unregister(cls, token):
        """
        Unregister the given Python function
        :param token: token, token provided by register method
        """

        pair = cls.tick_threads.get(token, None)
        if pair:
            pair[1].stop()
            del cls.tick_threads[token]

        return None

    @classmethod
    @decorators.repeater(interval)
    def _tick(cls, token):
        """
        Internal function to handl the tick event
        :param token: token, token provided by register function
        """

        pair = cls.tick_threads.get(token, None)
        if pair:
            pair[0]()
