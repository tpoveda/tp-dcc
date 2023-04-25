#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains abstract definition of DCC nodes
"""

from tp.core import dcc, exceptions


class Node(object):

    @classmethod
    def ls(cls, objects=None, selection=False):
        if objects is None and not selection:
            objects = dcc.all_scene_nodes(full_path=False)
        else:
            objects = objects or list()
            if selection:
                objects.extend(dcc.selected_nodes(full_path=False) or [])

        return [cls(name) for name in objects]

    def __init__(self, name, attributes=None):
        try:
            self._name = name.encode('ascii')
        except UnicodeEncodeError:
            raise UnicodeEncodeError('Not a valid ASCII name "{}".'.format(name))

        self._short_name = None
        self._namespace = None
        self._mirror_axis = None
        self._attributes = attributes

    def __str__(self):
        return self.name()

    def name(self):
        return self._name

    def attributes(self):
        return self._attributes

    def short_name(self):
        if self._short_name is None:
            self._short_name = self.name().split('|')[-1]
        return self._short_name

    def to_short_name(self):
        names = dcc.list_nodes(node_name=self.short_name())
        if len(names) == 1:
            return Node(names[0])
        elif len(names) > 1:
            raise exceptions.MoreThanOneObjectFoundError('More than one object found {}'.format(str(names)))
        else:
            raise exceptions.NoObjectFoundError('No object found {}'.format(self.short_name()))

    def namespace(self):
        if self._namespace is None:
            self._namespace = ':'.join(self.short_name().split(':')[:-1])
        return self._namespace

    def strip_first_pipe(self):
        if self.name().startswith('|'):
            self._name = self.name()[1:]

    def exists(self):
        return dcc.node_exists(self.name())

    def is_long(self):
        return '|' in self.name()

    def is_referenced(self):
        return dcc.node_is_referenced(self.name())

    def set_mirror_axis(self, mirror_axis):
        """
        Sets node mirror axis
        :param mirror_axis: list(int)
        """

        self._mirror_axis = mirror_axis

    def set_namespace(self, namespace):
        """
        Sets namespace for current node
        :param namespace: str
        """

        new_name = self.name()
        old_name = self.name()

        new_namespace = namespace
        old_namespace = self.namespace()

        if new_namespace == old_namespace:
            return self.name()

        if old_namespace and new_namespace:
            new_name = old_name.replace(old_namespace + ":", new_namespace + ":")
        elif old_namespace and not new_namespace:
            new_name = old_name.replace(old_namespace + ":", "")
        elif not old_namespace and new_namespace:
            new_name = old_name.replace("|", "|" + new_namespace + ":")
            if new_namespace and not new_name.startswith("|"):
                new_name = new_namespace + ":" + new_name

        self._name = new_name

        self._short_name = None
        self._namespace = None

        return self.name()


def group_objects(objects):
    """
    Group objects as Nodes
    :param objects: list(str)
    :return: dict
    """

    results = dict()
    for name in objects:
        node = Node(name)
        results.setdefault(node.namespace(), list())
        results[node.namespace()].append(name)

    return results


def get_reference_paths(objects, without_copy_number=False):
    """
    Retursn the reference paths for the given objects
    :param objects: list(str)
    :param without_copy_number: bool
    :return: list(str)
    """

    paths = list()
    for obj in objects:
        if dcc.node_is_referenced(obj):
            paths.append(dcc.node_reference_path(obj, without_copy_number=without_copy_number))

    return list(set(paths))


def get_reference_data(objects):
    """
    Retruns the reference paths for the given objects
    :param objects: list(str)
    :return: list(dict)
    """

    data = list()
    paths = get_reference_paths(objects)
    for path in paths:
        data.append({
            'filename': path,
            'unresolved': dcc.node_reference_path(path, without_copy_number=True),
            'namespace': dcc.node_namespace(path),
            'node': dcc.node_is_referenced(path)
        })

    return data
