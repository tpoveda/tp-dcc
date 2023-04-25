#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Python contexts related with OpenMaya
"""

from contextlib import contextmanager

import maya.api.OpenMaya as OpenMaya

from tp.core import log

logger = log.tpLogger


@contextmanager
def namespace_context(namespace):
	"""
	Python context that sets the given namespace as the active namespace and after yielding the function restores
	the previous namespace.

	:param str namespace: namespace name to set as active one.

	..note:: if the give namespace does not exist, it will be created automatically.
	"""

	current_namespace = OpenMaya.MNamespace.currentNamespace()
	existing_namespaces = OpenMaya.MNamespace.getNamespaces(current_namespace, True)
	valid_namespace = namespace if namespace.startswith(':') else ':{}'.format(namespace)
	if current_namespace != valid_namespace and valid_namespace not in existing_namespaces and \
			valid_namespace != OpenMaya.MNamespace.rootNamespace():
		try:
			OpenMaya.MNamespace.addNamespace(namespace)
		except RuntimeError:
			logger.error('Failed to create namespace: {}, existing namespaces: {}'.format(
				namespace, existing_namespaces), exc_info=True)
			OpenMaya.MNamespace.setCurrentNamespace(current_namespace)
			raise
	OpenMaya.MNamespace.setCurrentNamespace(namespace)
	try:
		yield
	finally:
		OpenMaya.MNamespace.setCurrentNamespace(current_namespace)
