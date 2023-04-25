# #! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya progress bar implementation
"""

import maya.cmds

from tp.core import log, progressbar
from tp.maya.cmds import gui

logger = log.tpLogger


class MayaProgressBar(progressbar.BaseProgressBar, object):
    """
    Util class to manipulate Maya progress bar
    """

    def __init__(self, title='', count=None, begin=True):
        super(MayaProgressBar, self).__init__(title=title, count=count, begin=begin)

        if maya.cmds.about(batch=True):
            self.title = title
            self.count = count
            msg = '{} count: {}'.format(title, count)
            self.status_string = ''
            logger.debug(msg)
            return
        else:
            self.progress_ui = gui.progress_bar()
            if begin:
                self.__class__.inc_value = 0
                self.end()
            if not title:
                title = maya.cmds.progressBar(self.progress_ui, query=True, status=True)
            if not count:
                count = maya.cmds.progressBar(self.progress_ui, query=True, maxValue=True)

            maya.cmds.progressBar(
                self.progress_ui, edit=True, beginProgress=begin, isInterruptable=True, status=title, maxValue=count)

    def set_count(self, count_number):
        maya.cmds.progressBar(self.progress_ui, edit=True, maxValue=int(count_number))

    def get_count(self):
        return maya.cmds.progressBar(self.progress_ui, query=True, maxValue=True)

    def set_progress(self, value):
        """
        Set progress bar progress value
        :param value: int
        """

        return maya.cmds.progressBar(self.progress_ui, edit=True, progress=value)

    def inc(self, inc=1):
        """
        Set the current increment
        :param inc: int, increment value
        """

        if maya.cmds.about(batch=True):
            return

        super(MayaProgressBar, self).inc(inc)

        maya.cmds.progressBar(self.progress_ui, edit=True, step=inc)

    def step(self):
        """
        Increments current progress value by one
        """

        if maya.cmds.about(batch=True):
            return

        self.__class__.inc_value += 1
        maya.cmds.progressBar(self.progress_ui, edit=True, step=1)

    def status(self, status_str):
        """
        Set the status string of the progress bar
        :param status_str: str
        """

        if maya.cmds.about(batch=True):
            self.status_string = status_str
            return

        maya.cmds.progressBar(self.progress_ui, edit=True, status=status_str)

    def end(self):
        """
        Ends progress bar
        """

        if maya.cmds.about(batch=True):
            return

        if maya.cmds.progressBar(self.progress_ui, query=True, isCancelled=True):
            maya.cmds.progressBar(self.progress_ui, edit=True, beginProgress=True)

        maya.cmds.progressBar(self.progress_ui, edit=True, ep=True)

    def break_signaled(self):
        """
        Breaks the progress bar loop so that it stop and disappears
        """

        if maya.cmds.about(batch=True):
            return False

        break_progress = maya.cmds.progressBar(self.progress_ui, query=True, isCancelled=True)
        if break_progress:
            self.end()
            return True

        return False
