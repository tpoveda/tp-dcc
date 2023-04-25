#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module to define background workers
"""

import uuid
from threading import Lock, Condition

from Qt.QtCore import Signal, QThread


class Worker(QThread, object):
    workCompleted = Signal(str, object)
    workFailure = Signal(str, str)

    def __init__(self, app, parent=None):
        super(Worker, self).__init__(parent=parent)

        self._execute_tasks = True
        self._app = app

        self._queue_mutex = Lock()

        self._queue = list()
        self._receivers = dict()

        self._wait_condition = Condition(self._queue_mutex)

    def stop(self, wait_for_completion=True):
        """
        Stops the worker, run this before shutdown
        """

        with self._queue_mutex:
            self._execute_tasks = False
            self._wait_condition.notify_all()

        if wait_for_completion:
            self.wait()

    def clear(self):
        """
        Empties the queue
        """

        with self._queue_mutex:
            self._queue = list()

    def queue_work(self, worker_fn, params, asap=False):
        """
        Queues up some work returning a unique id to identify this worker
        :param worker_fn:
        :param params:
        :param asap:
        :return:
        """

        uid = uuid.uuid4().hex
        work = {'id': uid, 'fn': worker_fn, 'params': params}
        with self._queue_mutex:
            if asap:
                self._queue.insert(0, work)
            else:
                self._queue.append(work)

            self._wait_condition.notify_all()

        return uid

    def run(self):
        while self._execute_tasks:
            with self._queue_mutex:
                if len(self._queue) == 0:
                    self._wait_condition.wait()
                    if len(self._queue) == 0:
                        continue
                item_to_process = self._queue.pop()

            if not self._execute_tasks:
                break

            data = None
            try:
                data = item_to_process['fn'](item_to_process['params'])
            except Exception as e:
                if self._execute_tasks:
                    self.workFailure.emit(item_to_process['id'], 'An error ocurred: {}'.format(str(e)))
                else:
                    self.workCompleted.emit(item_to_process['id'], data)
