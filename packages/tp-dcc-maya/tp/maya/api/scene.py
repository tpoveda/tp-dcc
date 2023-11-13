from __future__ import annotations

from tp.common.python import patterns
from tp.maya.api import plugins


class MayaScene(patterns.ProxyFactory):
    """
    Overload of ProxyFactory that interfaces with Maya scenes.
    """

    __slots__ = ('__plugins__', '__extensions__', '__properties__')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__plugins__ = dict(self.iterate_packages(plugins, class_attr='__plugin__'))
        self._extensions = {}
        self.__properties__ = {}
