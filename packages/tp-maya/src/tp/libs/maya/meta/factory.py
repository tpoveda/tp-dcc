"""Meta Factory metaclass for dynamic metanode instantiation.

This module provides the MetaFactory metaclass which enables dynamic
instantiation of the correct metanode subclass based on the node's
stored class type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from maya.api import OpenMaya

if TYPE_CHECKING:
    from ..wrapper import DagNode, DGNode
    from .base import MetaBase


class MetaFactory(type):
    """Metaclass to manage dynamic instantiation and registration of classes.

    This metaclass overrides the default `__call__` method to allow dynamic
    instantiation  of classes or their appropriate subclasses.

    It evaluates whether a node or specific class type is provided and
    determines the correct class to instantiate based on a  registration
    mechanism.

    It enables seamless integration with a class registry for the dynamic
    management of instantiable classes.
    """

    def __call__(cls: type[MetaBase], *args, **kwargs):
        """Override the default `__call__` behavior of a class to introduce
        customized instantiation logic.

        It primarily checks whether the provided class is registered,
        registers it if needed, and determines the appropriate class type for
        the instantiation based on the provided `node`. If a specific type is
        resolved from the registry, it delegates the instantiation to that
        type.

        Args:
            cls: The class being called, of type `MetaBase` or its subclass.
            *args: Positional arguments for the class instantiation.
                The first argument can optionally be the `node`.
            **kwargs: Keyword arguments for the class instantiation.
                Contains `node`, which can be an instance of `DGNode`,
                `DagNode`, `MetaBase`, `OpenMaya.MObject`, or `None`.

        Returns:
            An instance of the determined class type. If no specific type is
            resolved, it defaults to instantiating the given `cls`.

        """

        from .base import MetaBase
        from .registry import MetaRegistry

        node: DGNode | DagNode | MetaBase | OpenMaya.MObject | None = (
            kwargs.get("node")
        )
        if args:
            node = args[0]

        register = MetaRegistry

        # If the given class is not registered, we register it.
        registry_name = MetaRegistry.registry_name_for_class(cls)

        if not register.is_in_registry(registry_name):
            register.register_meta_class(cls)

        if not node:
            return type.__call__(cls, *args, **kwargs)

        class_type = MetaBase.class_name_from_plug(node)
        if class_type == registry_name:
            return type.__call__(cls, *args, **kwargs)

        # Check MetaRegistry first
        # noinspection PyUnresolvedReferences
        registered_type = MetaRegistry().get_type(class_type)

        # If not found, check PropertyRegistry
        if registered_type is None:
            try:
                from .properties import PropertyRegistry

                registered_type = PropertyRegistry.get_type(class_type)
                if registered_type is None:
                    registered_type = PropertyRegistry.get_hidden(class_type)
            except ImportError:
                pass

        if registered_type is None:
            return type.__call__(cls, *args, **kwargs)

        return type.__call__(registered_type, *args, **kwargs)
