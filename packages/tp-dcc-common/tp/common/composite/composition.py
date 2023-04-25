#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base classes implementations for Composition mechanism
https://github.com/mikemalinowski/xcomposite
"""


class Composition(object):

    def __init__(self):

        self._components = list()

    def __repr__(self):

        if not self._components:
            return self.__class__.__name__

        return '[{} ({})]'.format(
            self.__class__.__name__, ';'.join(
                [component.__class__.__name__ for component in self._components if component != self]))

    def components(self):
        """
        Returns all components
        :return: list(instance)
        """

        return self._components

    def bind(self, component):
        """
        Adds a component to the class. At this point, all decorated class will incorporate this component
        :param component: class, component to add
        """

        self._components.append(component)

    def unbind(self, component_class):
        """
        Removes the component of given type from the list of components
        :param component_class: class, component class type to remove
        """

        for component in self._components[:]:
            if isinstance(component, component_class):
                self._components.remove(component)
