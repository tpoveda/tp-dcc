#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tp-dcc-tools-renamer tool
"""

from tp.core import tool
from tp.tools.renamer import view


class RenamerTool(tool.DccTool):
	def __init__(self):
		super(RenamerTool, self).__init__()

	def setup_ui(self):
		self.ui = view.RenamerView()
