import contextlib

import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMayaAnim as OpenMayaAnim

from tp.core import log

logger = log.tpLogger


@contextlib.contextmanager
def maintain_time():
	"""
	Context manager that preserves the time after the context.
	"""

	current_time = OpenMayaAnim.MAnimControl.currentTime()
	try:
		yield
	finally:
		OpenMayaAnim.MAnimControl.setCurrentTime(current_time)


@contextlib.contextmanager
def namespace_context(namespace):
	"""
	Python context that sets the given namespace as the active namespace and after yielding the function restores
	the previous namespace.

	:param str namespace: namespace name to set as active one.

	..note:: if the give namespace does not exists, it will be created automatically.
	"""

	# some characters are illegal for namespaces
	namespace = namespace.replace('.', '_')

	current_namespace = OpenMaya.MNamespace.currentNamespace()
	existing_namespaces = OpenMaya.MNamespace.getNamespaces(current_namespace, True)
	if current_namespace != namespace and namespace not in existing_namespaces and \
			namespace != OpenMaya.MNamespace.rootNamespace():
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
