# !/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import

"""
Module that contains view functions related with 3ds Max
"""

import MaxPlus


def disable_redraw():
    """
    Disables redraw of 3ds Max viewports
    """

    MaxPlus.ViewportManager.DisableSceneRedraw()


def enable_redraw():
    """
    Enables redraw of 3ds Max viewports
    """

    MaxPlus.ViewportManager.EnableSceneRedraw()


def force_redraw():
    """
    Forces the redrawing of the viewports
    """

    # MaxPlus.ViewportManager.RedrawViewportsNow()
    MaxPlus.ViewportManager.RedrawViews(0)
