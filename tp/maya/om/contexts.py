from __future__ import annotations

import logging
import contextlib

from maya.api import OpenMaya

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def namespace_context(namespace):
    """
    Python context that sets the given namespace as the active namespace and after yielding the function restores
    the previous namespace.

    :param str namespace: namespace name to set as active one.

    ..note:: if the give namespace does not exist, it will be created automatically.
    """

    # some characters are illegal for namespaces
    namespace = namespace.replace(".", "_")

    current_namespace = OpenMaya.MNamespace.currentNamespace()
    existing_namespaces = OpenMaya.MNamespace.getNamespaces(current_namespace, True)
    if (
        current_namespace != namespace
        and namespace not in existing_namespaces
        and namespace != OpenMaya.MNamespace.rootNamespace()
    ):
        try:
            OpenMaya.MNamespace.addNamespace(namespace)
        except RuntimeError:
            logger.error(
                "Failed to create namespace: {}, existing namespaces: {}".format(
                    namespace, existing_namespaces
                ),
                exc_info=True,
            )
            OpenMaya.MNamespace.setCurrentNamespace(current_namespace)
            raise
    OpenMaya.MNamespace.setCurrentNamespace(namespace)
    try:
        yield
    finally:
        OpenMaya.MNamespace.setCurrentNamespace(current_namespace)
