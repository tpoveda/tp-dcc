"""Dependent node pattern for the metadata network.

This module provides the DependentMeta class which enables automatic
creation of parent dependency chains. When a DependentMeta node is created,
it automatically ensures its required parent nodes exist.

This pattern is useful for building hierarchical metadata structures where
certain nodes must always exist within a specific hierarchy.

Example:
    >>> from tp.libs.maya.meta.dependent import DependentMeta
    >>> from tp.libs.maya.meta.base import MetaBase
    >>>
    >>> class RigCore(MetaBase):
    ...     ID = "rigCore"
    ...
    >>> class SkeletonLayer(DependentMeta):
    ...     ID = "skeletonLayer"
    ...     dependent_node = RigCore  # Requires RigCore parent
    ...
    >>> # Creating SkeletonLayer auto-creates RigCore if needed
    >>> skeleton = SkeletonLayer(name="my_skeleton")
    >>> assert skeleton.meta_parent() is not None
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from maya.api import OpenMaya

from .base import MetaBase, MetaRegistry

if TYPE_CHECKING:
    from ..wrapper import DagNode, DGNode


class DependentMeta(MetaBase):
    """Meta node that requires a parent meta node to exist.

    When instantiated, this class automatically ensures that its required
    parent node (specified by `dependent_node`) exists. If the parent
    doesn't exist, it will be auto-created.

    This enables building hierarchical metadata structures where certain
    nodes must always exist within a specific context.

    Class Attributes:
        dependent_node: The parent meta class that this node depends on.
            If None, behaves like a regular MetaBase.
        auto_create_parent: If True (default), automatically creates the
            parent node if it doesn't exist.

    Example:
        >>> class CharacterCore(MetaBase):
        ...     ID = "characterCore"
        ...
        >>> class RigLayer(DependentMeta):
        ...     ID = "rigLayer"
        ...     dependent_node = CharacterCore
        ...
        >>> # This will auto-create CharacterCore if needed
        >>> rig = RigLayer(name="main_rig")
    """

    # The parent meta class that this node depends on
    dependent_node: type[MetaBase] | None = None

    # Whether to automatically create the parent if missing
    auto_create_parent: bool = True

    def __init__(
        self,
        node: DGNode | DagNode | OpenMaya.MObject | None = None,
        name: str | None = None,
        parent: MetaBase | None = None,
        namespace: str | None = None,
        init_defaults: bool = True,
        lock: bool = False,
        mod: OpenMaya.MDGModifier | None = None,
        *args,
        **kwargs,
    ):
        """Initialize the dependent meta node.

        Args:
            node: Existing node to wrap, or None to create new.
            name: Name for new node.
            parent: Explicit parent meta node. If None and dependent_node
                is set, the parent will be auto-created or found.
            namespace: Namespace for new node.
            init_defaults: Whether to initialize default attributes.
            lock: Whether to lock the node after creation.
            mod: Optional modifier for batched operations.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """

        # Store parent for post-initialization
        self._pending_parent = parent

        # Initialize the base node first
        super().__init__(
            node=node,
            name=name,
            namespace=namespace,
            init_defaults=init_defaults,
            lock=lock,
            mod=mod,
            *args,
            **kwargs,
        )

        # Handle parent dependency after node creation
        if node is None and init_defaults:
            self._ensure_parent_dependency(mod=mod)

    def _ensure_parent_dependency(
        self, mod: OpenMaya.MDGModifier | None = None
    ):
        """Ensure the parent dependency is satisfied.

        This method checks if a parent is required and creates or connects
        to one as needed.

        Args:
            mod: Optional modifier for batched operations.
        """

        # If no dependent_node defined, nothing to do
        if self.dependent_node is None:
            return

        # Check if we already have a parent of the correct type
        existing_parent = self._find_existing_parent()
        if existing_parent is not None:
            return

        # Use explicitly provided parent
        if self._pending_parent is not None:
            if isinstance(self._pending_parent, self.dependent_node):
                self.add_meta_parent(self._pending_parent, mod=mod)
                logger.debug(
                    f"Connected {self.name()} to provided parent "
                    f"{self._pending_parent.name()}"
                )
            else:
                logger.warning(
                    f"Provided parent {self._pending_parent} is not of "
                    f"expected type {self.dependent_node.__name__}"
                )
            return

        # Auto-create parent if enabled
        if self.auto_create_parent:
            parent = self._create_or_find_parent(mod=mod)
            if parent is not None:
                self.add_meta_parent(parent, mod=mod)
                logger.debug(
                    f"Auto-connected {self.name()} to parent {parent.name()}"
                )

    def _find_existing_parent(self) -> MetaBase | None:
        """Find an existing parent of the required type.

        Returns:
            The parent if found and of correct type, None otherwise.
        """

        if self.dependent_node is None:
            return None

        for parent in self.iterate_meta_parents():
            if isinstance(parent, self.dependent_node):
                return parent
            # Also check by class name for dynamic resolution
            if parent.metaclass_type() == MetaRegistry.registry_name_for_class(
                self.dependent_node
            ):
                return parent

        return None

    def _create_or_find_parent(
        self, mod: OpenMaya.MDGModifier | None = None
    ) -> MetaBase | None:
        """Create or find a parent node of the required type.

        First attempts to find an existing node of the required type
        in the scene. If none exists, creates a new one.

        Args:
            mod: Optional modifier for batched operations.

        Returns:
            The parent meta node, or None if creation failed.
        """

        if self.dependent_node is None:
            return None

        # Try to find an existing node of the required type
        from .base import find_meta_nodes_by_class_type

        existing_nodes = find_meta_nodes_by_class_type(self.dependent_node)
        if existing_nodes:
            logger.debug(
                f"Found existing {self.dependent_node.__name__}: "
                f"{existing_nodes[0].name()}"
            )
            return existing_nodes[0]

        # Create a new parent node
        try:
            parent = self.dependent_node(mod=mod)
            logger.debug(
                f"Created new parent {self.dependent_node.__name__}: "
                f"{parent.name()}"
            )
            return parent
        except Exception as e:
            logger.error(
                f"Failed to create parent {self.dependent_node.__name__}: {e}"
            )
            return None

    def get_dependency_parent(self) -> MetaBase | None:
        """Get the parent that satisfies the dependency requirement.

        This returns the first parent that matches the `dependent_node` type.

        Returns:
            The dependency parent, or None if not connected.
        """

        return self._find_existing_parent()

    def ensure_dependency_chain(
        self, mod: OpenMaya.MDGModifier | None = None
    ) -> bool:
        """Ensure the entire dependency chain is satisfied.

        This method walks up the dependency chain and ensures all
        required parent nodes exist and are connected.

        Args:
            mod: Optional modifier for batched operations.

        Returns:
            True if the chain is complete, False if there were issues.
        """

        # First ensure our immediate parent
        self._ensure_parent_dependency(mod=mod)

        # Then check if our parent also has dependencies
        parent = self.get_dependency_parent()
        if parent is not None and isinstance(parent, DependentMeta):
            return parent.ensure_dependency_chain(mod=mod)

        return self.get_dependency_parent() is not None

    @classmethod
    def get_dependency_chain(cls) -> list[type[MetaBase]]:
        """Get the full dependency chain for this class.

        Returns:
            List of meta classes in the dependency chain, starting from
            the root (most independent) to this class.
        """

        chain: list[type[MetaBase]] = []
        current: type[MetaBase] | None = cls

        while current is not None:
            chain.insert(0, current)
            if hasattr(current, "dependent_node"):
                current = getattr(current, "dependent_node", None)
            else:
                break

        return chain


def create_dependency_chain(
    leaf_type: type[DependentMeta],
    mod: OpenMaya.MDGModifier | None = None,
    **kwargs,
) -> DependentMeta:
    """Create a complete dependency chain ending with the specified type.

    This utility function creates all required parent nodes in the
    dependency chain before creating the final leaf node.

    Args:
        leaf_type: The dependent meta class to create.
        mod: Optional modifier for batched operations.
        **kwargs: Additional arguments passed to the leaf node constructor.

    Returns:
        The created leaf node with its complete dependency chain.

    Example:
        >>> class Core(MetaBase):
        ...     ID = "core"
        ...
        >>> class Layer(DependentMeta):
        ...     ID = "layer"
        ...     dependent_node = Core
        ...
        >>> class SubLayer(DependentMeta):
        ...     ID = "subLayer"
        ...     dependent_node = Layer
        ...
        >>> # Creates Core -> Layer -> SubLayer
        >>> sub = create_dependency_chain(SubLayer, name="my_sublayer")
    """

    return leaf_type(mod=mod, **kwargs)


def get_or_create_parent(
    node: DependentMeta,
    parent_type: type[MetaBase] | None = None,
    mod: OpenMaya.MDGModifier | None = None,
) -> MetaBase | None:
    """Get or create a parent node for the given dependent node.

    Args:
        node: The dependent meta node.
        parent_type: The parent type to get/create. If None, uses
            the node's dependent_node attribute.
        mod: Optional modifier for batched operations.

    Returns:
        The parent meta node, or None if not applicable.
    """

    target_type = parent_type or node.dependent_node
    if target_type is None:
        return None

    # Check for existing parent
    for parent in node.iterate_meta_parents():
        if isinstance(parent, target_type):
            return parent

    # Create new parent
    return target_type(mod=mod)
