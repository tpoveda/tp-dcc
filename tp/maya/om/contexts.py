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

    :param namespace: namespace name to set as active one.

    .note:: if the give namespace does not exist, it will be created automatically.
    """

    # some characters are illegal for namespaces
    namespace = namespace.replace(".", "_")

    current_namespace = OpenMaya.MNamespace.currentNamespace()
    existing_namespaces = OpenMaya.MNamespace.getNamespaces(current_namespace, True)
    valid_namespace = namespace if namespace.startswith(":") else f":{namespace}"

    if (
        current_namespace != valid_namespace
        and valid_namespace not in existing_namespaces
        and valid_namespace != OpenMaya.MNamespace.rootNamespace()
    ):
        try:
            OpenMaya.MNamespace.addNamespace(valid_namespace)
        except RuntimeError:
            logger.error(
                f"Failed to create namespace: {valid_namespace}, existing namespaces: {existing_namespaces}",
                exc_info=True,
            )
            OpenMaya.MNamespace.setCurrentNamespace(current_namespace)
            raise
    OpenMaya.MNamespace.setCurrentNamespace(valid_namespace)
    try:
        yield
    finally:
        OpenMaya.MNamespace.setCurrentNamespace(current_namespace)


@contextlib.contextmanager
def temp_namespace_context(namespace: str):
    """
    Python context that creates a temporary namespace and after yielding the function restores the previous namespace.

    :param namespace: namespace to create.
    """

    # some characters are illegal for namespaces
    namespace = namespace.replace(".", "_")

    current_namespace = OpenMaya.MNamespace.currentNamespace()
    existing_namespaces = OpenMaya.MNamespace.getNamespaces(current_namespace, True)
    valid_namespace = namespace if namespace.startswith(":") else f":{namespace}"

    if (
        current_namespace != valid_namespace
        and valid_namespace not in existing_namespaces
        and valid_namespace != OpenMaya.MNamespace.rootNamespace()
    ):
        try:
            OpenMaya.MNamespace.addNamespace(valid_namespace)
        except RuntimeError:
            logger.error(
                f"Failed to create namespace: {valid_namespace}, existing namespaces: {existing_namespaces}",
                exc_info=True,
            )
            OpenMaya.MNamespace.setCurrentNamespace(current_namespace)
            raise
    OpenMaya.MNamespace.setCurrentNamespace(valid_namespace)
    try:
        yield
    finally:
        OpenMaya.MNamespace.moveNamespace(
            valid_namespace, OpenMaya.MNamespace.rootNamespace(), True
        )
        OpenMaya.MNamespace.removeNamespace(valid_namespace)
