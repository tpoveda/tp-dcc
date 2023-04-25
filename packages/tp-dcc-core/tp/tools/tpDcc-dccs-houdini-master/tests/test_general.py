#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tests for tpDcc.dccs.houdini
"""

import pytest

from tpDcc.dccs.houdini import __version__


def test_version():
    assert __version__.get_version()
