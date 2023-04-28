#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Dcc callback classes
"""

from tp.core import dcc
from tp.core.abstract import callback as abstract_callback
from tp.common.python import decorators


class _MetaCallback(type):
    def __call__(cls, *args, **kwargs):
        if dcc.is_maya():
            from tp.maya.cmds import callback as maya_callback
            return maya_callback.MayaCallback
        else:
            return None


@decorators.add_metaclass(_MetaCallback)
class Callback(abstract_callback.AbstractCallback):
    pass
