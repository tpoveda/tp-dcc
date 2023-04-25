# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Max Python functions related with 3ds Max scenes
"""

from pymxs import runtime as rt


def delete_selected_animation():
    """
    Deletes the animation of the selected objects
    """

    rt.macros.run('Animation Tools', 'DeleteSelectedAnimation')
