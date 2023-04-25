#!#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains common definitions for tpDcc.dccs.maya
"""

from __future__ import print_function, division, absolute_import


PIVOT_ARGS = dict(rp=['rp', 'r', 'rotate', 'rotatePivot', 'pivot'], sp=['scale', 's', 'scalePivot'],
                  local=['l', 'translate'], boundingBox=['bb', 'bbCenter'], axisBox=['ab'],
                  closestPoint=['cpos', 'closest', 'closestPoint'])

SPACE_ARGS = {'object': ['os', 'objectSpace', 'o'], 'world': ['w', 'worldSpace', 'ws'], 'local': ['l', 'translate']}
