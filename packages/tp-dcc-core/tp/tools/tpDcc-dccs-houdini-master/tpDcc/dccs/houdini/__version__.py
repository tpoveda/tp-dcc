#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Version module for tpDcc-dccs-houdini
"""

from __future__ import print_function, division, absolute_import

__version__ = None


def get_version():
    global __version__
    if __version__:
        return __version__

    from ._version import get_versions
    __version__ = get_versions()['version']
    del get_versions

    return __version__
