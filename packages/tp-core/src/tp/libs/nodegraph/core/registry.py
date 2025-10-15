from __future__ import annotations

import importlib
import importlib.util
import inspect
import logging
import os
import pkgutil
import sys
from typing import Any, Generic, TypeVar

from .node import Node
from .dtype import DType

# Type variable for generic registry
T = TypeVar("T")


class Registry(Generic[T]):
    """A generic registry for storing and retrieving items by name.

    This class provides a way to register and retrieve items by name,
    with support for categories and metadata. It also supports lazy loading
    of items, which are loaded only when requested.
    """

    def __init__(self, name: str):
        super().__init__()

        self._name = name
        self._items: dict[str, T] = {}
        self._lazy_items: dict[str, dict[str, Any]] = {}
        self._categories: dict[str, set[str]] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
        self._use_lazy_loading = True
        self._logger = logging.getLogger(f"pipegraph.registry.{name}")

    def __contains__(self, name: str) -> bool:
        """Check if an item is in the registry."""

        return name in self.items or name in self.lazy_items

    def __getitem__(self, name: str) -> T:
        """Get an item from the registry by name."""

        item = self.get(name)
        if item is None:
            raise KeyError(f"Item '{name}' not found in registry '{self.name}'")
        return item

    def __iter__(self):
        """Iterate over items in the registry."""

        return iter(self.items.items())

    def __len__(self) -> int:
        """Get the number of items in the registry."""

        return len(self.items) + len(self.lazy_items)

    @property
    def name(self) -> str:
        """The name of the registry."""

        return self._name

    @property
    def items(self) -> dict[str, T]:
        """The items in the registry."""

        return self._items

    @property
    def lazy_items(self) -> dict[str, dict[str, Any]]:
        """The lazy items in the registry."""

        return self._lazy_items

    @property
    def categories(self) -> dict[str, set[str]]:
        """The categories in the registry."""

        return self._categories

    @property
    def metadata(self) -> dict[str, dict[str, Any]]:
        """The metadata for the items in the registry."""

        return self._metadata

    @property
    def use_lazy_loading(self) -> bool:
        """Whether lazy loading is enabled for this registry."""

        return self._use_lazy_loading

    @use_lazy_loading.setter
    def use_lazy_loading(self, flag: bool) -> None:
        """Set whether lazy loading is enabled for this registry."""

        self._use_lazy_loading = flag

    def register(
        self,
        name: str,
        item: T,
        category: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> T:
        """Register an item with the registry.

        Args:
            name: The name to register the item under
            item: The item to register
            category: An optional category to group the item under
            metadata: Optional metadata to associate with the item

        Returns:
            The registered item
        """
        if name in self._items:
            self._logger.warning(
                f"Overwriting existing item '{name}' in registry '{self.name}'"
            )

        # Remove from lazy_items if it exists there.
        if name in self._lazy_items:
            del self._lazy_items[name]

        self._items[name] = item

        metadata = metadata or {}

        if category:
            if category not in self._categories:
                self._categories[category] = set()
            self._categories[category].add(name)

            # Register the category in metadata.
            metadata["category"] = category

        if metadata:
            self._metadata[name] = metadata

        self._logger.debug(f"Registered item '{name}' in registry '{self.name}'")

        return item

    def register_lazy(
        self,
        name: str,
        module_name: str,
        class_name: str,
        category: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a lazy-loadable item with the registry.

        The item will be loaded only when it is requested.

        Args:
            name: The name to register the item under
            module_name: The name of the module containing the item
            class_name: The name of the class to load
            category: An optional category to group the item under
            metadata: Optional metadata to associate with the item
        """
        if name in self._items:
            self._logger.warning(
                f"Overwriting existing item '{name}' in registry '{self.name}'"
            )
            del self._items[name]

        self._lazy_items[name] = {
            "module_name": module_name,
            "class_name": class_name,
        }

        if category:
            if category not in self._categories:
                self._categories[category] = set()
            self._categories[category].add(name)

        if metadata:
            self._metadata[name] = metadata

        self._logger.debug(f"Registered lazy item '{name}' in registry '{self._name}'")

    def _load_lazy_item(self, name: str) -> T | None:
        """Load a lazy-loadable item.

        Args:
            name: The name of the item to load

        Returns:
            The loaded item, or None if loading failed
        """

        if name not in self._lazy_items:
            return None

        info = self.lazy_items[name]
        module_name = info["module_name"]
        class_name = info["class_name"]

        try:
            module = importlib.import_module(module_name)
            item = getattr(module, class_name)

            # Register the loaded item.
            self.items[name] = item
            del self.lazy_items[name]

            self._logger.debug(
                f"Lazy-loaded item '{name}' from {module_name}.{class_name}"
            )

            return item
        except (ImportError, AttributeError) as e:
            self._logger.error(f"Error lazy-loading item '{name}': {e}")
            return None

    def get(self, name: str) -> T | None:
        """Get an item from the registry by name.

        If the item is lazy-loadable and not yet loaded, it will be loaded.

        Args:
            name: The name of the item to get

        Returns:
            The item, or None if not found
        """

        # Check if the item is already loaded.
        if name in self._items:
            return self._items.get(name)

        # Check if the item is lazy-loadable
        if self._use_lazy_loading and name in self._lazy_items:
            return self._load_lazy_item(name)

        return None

    def get_all(self) -> dict[str, T]:
        """Get all items in the registry.

        Notes:
            This does not load lazy-loadable items.

        Returns:
            A dictionary mapping names to items
        """

        return self.items.copy()

    def get_all_names(self) -> list[str]:
        """Get all item names in the registry, including lazy-loadable items.

        Returns:
            A list of all item names
        """

        return list(set(self.items.keys()) | set(self.lazy_items.keys()))

    def get_by_category(self, category: str) -> dict[str, T]:
        """Get all items in a category.

        Notes:
            This loads lazy-loadable items in the category.

        Args:
            category: The category to get items from

        Returns:
            A dictionary mapping names to items
        """

        if category not in self.categories:
            return {}

        result = {}
        for name in self.categories[category]:
            item = self.get(name)  # This will load lazy items
            if item is not None:
                result[name] = item

        return result

    def get_metadata(self, name: str) -> dict[str, Any] | None:
        """Get metadata for an item.

        Args:
            name: The name of the item to get metadata for

        Returns:
            The metadata, or None if not found
        """

        return self.metadata.get(name)


# === Global Registries ===
node_registry = Registry[type[Node]]("nodes")
data_type_registry = Registry[DType]("data_types")


def register_node(
    name: str | None = None,
    category: str | None = None,
    metadata: dict[str, Any] | None = None,
):
    """Decorator to register a node class with the node registry.

    Args:
        name: The name to register the node under. If None, the class name will be used.
        category: An optional category to group the node under
        metadata: Optional metadata to associate with the node

    Returns:
        A decorator function
    """

    def decorator(cls: type[Node]) -> type[Node]:
        node_name = name or cls.__name__
        node_registry.register(node_name, cls, category, metadata)
        return cls

    return decorator


def register_data_type(
    name: str | None = None,
    category: str | None = None,
    metadata: dict[str, Any] | None = None,
):
    """Decorator to register a data type with the data type registry.

    Args:
        name: The name to register the data type under. If None, the class name will be used.
        category: An optional category to group the data type under
        metadata: Optional metadata to associate with the data type

    Returns:
        A decorator function
    """

    def decorator(cls: type) -> type:
        type_name = name or cls.__name__
        data_type_registry.register(type_name, cls, category, metadata)
        return cls

    return decorator


def discover_plugins(package_name: str, lazy_load: bool = True):
    """Discover and import all plugins in a package.

    This function recursively imports all modules in a package.
    If lazy_load is `True`, it registers plugins for lazy loading.
    Otherwise, it imports modules immediately, which will trigger any
        registration decorators.

    Args:
        package_name: The name of the package to discover plugins in
        lazy_load: Whether to use lazy loading for discovered plugins
    """

    package = importlib.import_module(package_name)

    if not hasattr(package, "__path__"):
        return

    for _, name, is_pkg in pkgutil.iter_modules(
        package.__path__, package.__name__ + "."
    ):
        if is_pkg:
            discover_plugins(name, lazy_load)
        else:
            if lazy_load:
                # Register for lazy loading.
                _register_module_for_lazy_loading(name)
            else:
                # Import immediately.
                try:
                    importlib.import_module(name)
                except ImportError as e:
                    logging.warning(f"Error importing plugin module {name}: {e}")


def discover_plugins_from_directory(directory: str, lazy_load: bool = True):
    """Discover and import all plugins in a directory.

    This function recursively imports all Python modules in a directory.
    If lazy_load is True, it registers plugins for lazy loading.
    Otherwise, it imports modules immediately, which will trigger any
        registration decorators.

    Args:
        directory: The directory to discover plugins in
        lazy_load: Whether to use lazy loading for discovered plugins
    """

    if not os.path.isdir(directory):
        logging.warning(f"Plugin directory {directory} does not exist")
        return

    # Add the directory to the Python path
    sys.path.insert(0, os.path.abspath(os.path.dirname(directory)))

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                module_path = os.path.join(root, file)
                module_name = os.path.splitext(os.path.relpath(module_path, directory))[
                    0
                ]
                module_name = module_name.replace(os.path.sep, ".")

                if lazy_load:
                    # Register for lazy loading.
                    _register_file_for_lazy_loading(module_name, module_path)
                else:
                    # Import immediately.
                    try:
                        spec = importlib.util.spec_from_file_location(
                            module_name, module_path
                        )
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            sys.modules[module_name] = module
                    except ImportError as e:
                        logging.warning(
                            f"Error importing plugin module {module_name}: {e}"
                        )

    # Remove the directory from the Python path.
    sys.path.pop(0)


def _register_module_for_lazy_loading(module_name: str):
    """Register all Node subclasses in a module for lazy loading.

    Args:
        module_name: The name of the module to register
    """

    try:
        # Import the module to inspect it.
        module = importlib.import_module(module_name)

        # Find all `Node` subclasses in the module.
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, Node)
                and obj.__module__ == module_name
                and obj != Node
            ):
                # Get the category from the class.
                category = None
                for decorator_name in ["register_node", "node"]:
                    if hasattr(obj, f"_{decorator_name}_category"):
                        category = getattr(obj, f"_{decorator_name}_category")
                        break

                # Get the metadata from the class.
                metadata = None
                for decorator_name in ["register_node", "node"]:
                    if hasattr(obj, f"_{decorator_name}_metadata"):
                        metadata = getattr(obj, f"_{decorator_name}_metadata")
                        break

                # Register the class for lazy loading.
                node_registry.register_lazy(
                    name=obj.__name__,
                    module_name=module_name,
                    class_name=name,
                    category=category,
                    metadata=metadata,
                )
    except ImportError as e:
        logging.warning(f"Error inspecting module {module_name} for lazy loading: {e}")


def _register_file_for_lazy_loading(module_name: str, module_path: str):
    """Register all Node subclasses in a file for lazy loading.

    Args:
        module_name: The name of the module to register
        module_path: The path to the module file
    """

    try:
        # Import the module to inspect it.
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find all `Node` subclasses in the module.
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, Node)
                    and obj.__module__ == module_name
                    and obj != Node
                ):
                    # Get the category from the class.
                    category = None
                    for decorator_name in ["register_node", "node"]:
                        if hasattr(obj, f"_{decorator_name}_category"):
                            category = getattr(obj, f"_{decorator_name}_category")
                            break

                    # Get the metadata from the class.
                    metadata = None
                    for decorator_name in ["register_node", "node"]:
                        if hasattr(obj, f"_{decorator_name}_metadata"):
                            metadata = getattr(obj, f"_{decorator_name}_metadata")
                            break

                    # Register the class for lazy loading.
                    node_registry.register_lazy(
                        name=obj.__name__,
                        module_name=module_name,
                        class_name=name,
                        category=category,
                        metadata=metadata,
                    )
    except ImportError as e:
        logging.warning(f"Error inspecting file {module_path} for lazy loading: {e}")
