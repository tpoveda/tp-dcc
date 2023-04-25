#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different types of timers
"""

import time

from tp.core import log

logger = log.tpLogger


class StopWatch(object):
    """
    Class that can be used to check how long a command takes to run
    """

    running = 0

    def __init__(self):
        self.time = None
        self.feedback = True

    def __del__(self):
        self.end()

    def start(self, description='', feedback=True):
        self.feedback = feedback
        if feedback:
            tabs = '\t' * self.running
            logger.debug('{}started timer: {}'.format(tabs, description))
        self.time = time.time()
        if feedback:
            self.__class__.running += 1

    def end(self):
        if not self.time:
            return 0.0, None

        seconds = time.time() - self.time
        self.time = None

        seconds = round(seconds, 2)
        minutes = None
        if seconds > 60:
            minutes, seconds = divmod(seconds, 60)
            seconds = round(seconds, 2)
            minutes = int(minutes)

        if self.feedback:
            tabs = '\t' * self.running
            if minutes is None:
                logger.debug('{}end timer: {} seconds'.format(tabs, seconds))
            else:
                if minutes > 1:
                    logger.debug('{} end timer: {}  minutes, {} seconds'.format(tabs, minutes, seconds))
                elif minutes == 1:
                    logger.debug('{} end timer: {} minute, {} seconds'.format(tabs, minutes, seconds))
            self.__class__.running -= 1

        return minutes, seconds

    def stop(self):
        return self.end()
