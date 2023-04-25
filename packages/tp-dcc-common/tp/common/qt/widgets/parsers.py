#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for custom PySide/PyQt windows
"""

from html.parser import HTMLParser

from Qt.QtWidgets import QLabel
from Qt.QtGui import QFont

from tp.common.qt.widgets import gif


class WidgetsFromTextParser(HTMLParser, object):
    def __init__(self, text, root_tag):
        super(WidgetsFromTextParser, self).__init__()

        self._widgets = list()
        self._root_tag = root_tag

        self._constructed = ''
        self._font = QFont('sans')

        self.feed(text)

    @property
    def widgets(self):
        return self._widgets

    def feed(self, data):
        super(WidgetsFromTextParser, self).feed(data)

        self.add_label_from_constructed()

    def handle_starttag(self, tag, attrs):
        starttag = self.get_starttag_text()
        self._constructed += starttag

        if tag == self._root_tag:
            if attrs[0][0] == 'gig':
                rem = len(starttag)
                self._constructed = self._constructed[:-rem]
                self.add_label_from_constructed()
                self.add_gif_widget(attrs[0][1])

    def handle_endtag(self, tag):
        if tag == self._root_tag:
            return

        self._constructed += "</{}>".format(tag)

    def handle_data(self, data):
        self._constructed += data

    def add_gif_widget(self, gif_file):
        gif_widget = gif.GifLabel(gif_file)
        self._widgets.append(gif_widget)

    def add_label_from_constructed(self):
        label = QLabel(self._constructed)
        label.setOpenExternalLinks(True)
        label.setWordWrap(True)
        label.setFont(self._font)
        self._constructed = ''

        self._widgets.append(label)
