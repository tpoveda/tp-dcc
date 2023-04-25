#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool that shows a widget with changelog info
"""

import os
import json
from collections import OrderedDict

from Qt.QtCore import Qt
from Qt.QtWidgets import QSizePolicy, QWidget, QLabel, QPushButton, QScrollArea

from tp.common.qt.widgets import layouts, dialog, accordion


class Changelog(dialog.BaseDialog, object):
    def __init__(self):
        super(Changelog, self).__init__(
            name='ChangelogDialog',
            title='Changelog'
        )

        self.setWindowFlags(self.windowFlags() ^ Qt.FramelessWindowHint)

    def ui(self):
        super(Changelog, self).ui()
        self.set_logo('changelog_logo')

        self.main_layout.setAlignment(Qt.AlignTop)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.setFixedWidth(600)
        self.setMaximumHeight(800)

        scroll_layout = layouts.VerticalLayout(spacing=2, margins=(2, 2, 2, 2))
        scroll_layout.setAlignment(Qt.AlignTop)
        central_widget = QWidget()
        central_widget.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        scroll = QScrollArea()
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setFocusPolicy(Qt.NoFocus)
        ok_btn = QPushButton('OK')
        ok_btn.clicked.connect(self.close)
        self.main_layout.addWidget(scroll)
        self.main_layout.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(ok_btn)
        scroll.setWidget(central_widget)
        central_widget.setLayout(scroll_layout)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.main_layout = scroll_layout

        # ===========================================================================================

        self.version_accordion = accordion.AccordionWidget(parent=self)
        self.version_accordion.rollout_style = accordion.AccordionStyle.MAYA
        self.main_layout.addWidget(self.version_accordion)

        # ===========================================================================================

        changelog_json_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'changelog.json')
        if not os.path.isfile(changelog_json_file):
            return

        with open(changelog_json_file, 'r') as f:
            changelog_data = json.load(f, object_pairs_hook=OrderedDict)
        if not changelog_data:
            return

        changelog_data = OrderedDict(sorted(changelog_data.items(), reverse=True))

        for version, elements in changelog_data.items():
            self._create_version(version, elements)

        last_version_item = self.version_accordion.item_at(0)
        last_version_item.set_collapsed(False)

    def _create_version(self, version, elements):

        version_widget = QWidget()
        version_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        version_layout.setContentsMargins(0, 0, 0, 0)
        version_layout.setSpacing(0)
        version_layout.setAlignment(Qt.AlignTop)
        version_widget.setLayout(version_layout)
        self.version_accordion.add_item(version, version_widget, collapsed=True)

        version_label = QLabel()
        version_layout.addWidget(version_label)
        version_text = ''
        for item in elements:
            version_text += '- {}\n'.format(item)
        version_label.setText(version_text)

        self.main_layout.addSpacing(5)


def run():
    new_changelog = Changelog()
    new_changelog.exec_()
