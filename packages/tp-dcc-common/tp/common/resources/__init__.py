#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for tp-common-resources
"""

import os
import sys

from Qt.QtWidgets import QApplication

from tp.core.managers import resources

app = QApplication.instance() or QApplication(sys.argv)
resources_path = os.path.dirname(os.path.abspath(__file__))
resources.register_resource(resources_path, key='tp-common-resources')
