from __future__ import annotations

from collections.abc import MutableMapping

import maya.api.OpenMaya as OpenMaya

from tp.maya.om import dagpath


class UserProperties(MutableMapping):
    """
    Overload of MutableMapping that interfaces with user properties.
    """

    __slots__ = ('__handle__', '__buffer__', '__properties__')

    def __init__(self, obj: str | OpenMaya.MObject | OpenMaya.MDagPath, **kwargs):
        super().__init__()

        self.__handle__ = dagpath.mobject_handle(obj)
        self.__buffer__ = ''
        self.__properties__ = {}
