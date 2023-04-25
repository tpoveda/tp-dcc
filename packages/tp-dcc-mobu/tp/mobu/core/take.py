#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with MotionBuilder takes
"""

import pyfbsdk


def get_current_anim_take_name():
    """
    Returns the name of the current take
    :return: str, name of the current take
    """

    current_take = pyfbsdk.FBSystem().CurrentTake
    take_name = None
    if current_take:
        take_name = pyfbsdk.FBSystem().CurrentTake.Name

    return take_name
