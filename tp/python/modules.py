from __future__ import annotations

import os
import sys
import uuid
import pathlib
import logging
import inspect
import pkgutil
import importlib
import traceback
import importlib.util
from types import ModuleType
from typing import Iterator, Iterable, Type, Any

from . import helpers

logger = logging.getLogger(__name__)

# File prefixes to exclude for determining a valid python module
# include Operating System meta files and hidden files to ignore
MODULE_EXCLUDE_PREFIXES = (
    "__init__.py",
    ".__init__",
    # OSX related metaFiles
    ".DS_Store",
    ".Spotlight-V100",
    ".Trashes",
    ".fseventsd",
    "._",
)


def is_dotted_module_path(module_path: str) -> bool:
    """
    Checks if the given module path is a dotted module path.

    This function determines whether a module path is in the dotted notation,
    which is typically used to represent nested module paths in Python.

    :param module_path: The module path to check.
    :return: True if the module path is in dotted notation, False otherwise.
    """

    return len(module_path.split(".")) > 2


def convert_to_dotted_path(path: str) -> str:
    """
    Converts a filesystem path to a dotted module path.

    This function takes a filesystem path and converts it to a dotted module path,
    which is used to represent the module in Python's import system.

    :param path: The filesystem path to convert.
    :return: The dotted module path.
    """

    directory, file_path = os.path.split(path)
    directory = pathlib.Path(directory).as_posix()
    file_name = os.path.splitext(file_path)[0]
    package_path = [file_name]
    sys_path = list(set([pathlib.Path(p).as_posix() for p in sys.path]))

    # We ignore current working directory. Useful if we want to execute tools directly inside PyCharm
    current_work_dir = pathlib.Path(os.getcwd()).as_posix()
    if current_work_dir in sys_path:
        sys_path.remove(current_work_dir)

    drive_letter = os.path.splitdrive(path)[0] + "\\"
    while directory not in sys_path:
        directory, name = os.path.split(directory)
        directory = pathlib.Path(directory).as_posix()
        if directory == drive_letter or name == "":
            return ""
        package_path.append(name)

    return ".".join(reversed(package_path))


def file_path_to_module_path(file_path: str) -> str:
    """
    Converts a filesystem path to a module path.

    This function takes a filesystem path and converts it to a module path suitable for importing.
    For example, it transforms a file path like 'path/to/module.py' to 'path.to.module'.

    :param file_path: The filesystem path to convert.
    :return: The module path derived from the filesystem path.
    """

    directory, file_path = os.path.split(file_path)
    directory = pathlib.Path(directory).as_posix()
    file_name = os.path.splitext(file_path)[0]
    package_path = [file_name]
    sys_path = list(set([pathlib.Path(p).as_posix() for p in sys.path]))

    # We ignore current working directory. Useful if we want to execute tools directly inside PyCharm
    current_work_dir = pathlib.Path(os.getcwd()).as_posix()
    if current_work_dir in sys_path:
        sys_path.remove(current_work_dir)

    drive_letter = os.path.splitdrive(file_path)[0] + "\\"
    while directory not in sys_path:
        directory, name = os.path.split(directory)
        directory = pathlib.Path(directory).as_posix()
        if directory == drive_letter or name == "":
            return ""
        package_path.append(name)

    return ".".join(reversed(package_path))


def valid_module_path(path: str, exclude: Iterable[str] | None = None) -> bool:
    """
    Checks if a given module path is valid.

    This function verifies if a given module path is valid by checking if it exists and is not in the exclusion list.

    :param path: The module path to validate.
    :param exclude: An iterable of module paths to exclude.
    :return: True if the module path is valid, False otherwise.
    """

    exclude = exclude or []
    basename = os.path.basename(path)
    if not basename.startswith(MODULE_EXCLUDE_PREFIXES) and basename not in exclude:
        return path.endswith(".py") or path.endswith(".pyc")
    return False


def import_module(
    module_path: str,
    name: str | None = None,
    skip_warnings: bool = True,
    skip_errors: bool = False,
    force_reload: bool = False,
) -> ModuleType | None:
    """
    Imports a module from a given module path.

    This function imports a module from the specified module path, with options to skip warnings, skip errors,
    and force reload the module. An optional name can be provided for the imported module.

    :param module_path: The filesystem path or dotted path of the module to import.
    :param name: An optional name to assign to the imported module. Defaults to None.
    :param skip_warnings: If True, skips warnings during import. Defaults to True.
    :param skip_errors: If True, skips errors during import. Defaults to False.
    :param force_reload: If True, forces reloading of the module. Defaults to False.
    :return: The imported module.
    """

    if is_dotted_module_path(module_path) and not os.path.exists(module_path):
        try:
            return importlib.import_module(module_path)
        except (NameError, KeyError, AttributeError) as exc:
            if "__init__" in str(exc) or "__path__" in str(exc):
                pass
            else:
                msg = f'Failed to load module: "{module_path}"'
                logger.error(msg, exc_info=True) if not skip_errors else logger.debug(
                    f"{msg} | {traceback.format_exc()}"
                )
        except (ImportError, ModuleNotFoundError):
            msg = f'Failed to import module: "{module_path}"'
            logger.error(msg, exc_info=True) if not skip_errors else logger.debug(
                f"{msg} | {traceback.format_exc()}"
            )
            return None
        except SyntaxError:
            msg = f'Module contains syntax errors: "{module_path}"'
            logger.error(msg, exc_info=True) if not skip_errors else logger.debug(
                f"{msg} | {traceback.format_exc()}"
            )
            return None
    try:
        if os.path.exists(module_path):
            if not name:
                name = os.path.splitext(os.path.basename(module_path))[0]
            if name in sys.modules:
                if force_reload:
                    pass
                    # logger.info(f'Force module reloading: {name}')
                    # sys.modules.pop(name)
                return sys.modules[name]
        if not name:
            if not skip_warnings:
                logger.warning(
                    f"Impossible to load module because module path: {module_path} was not found!"
                )
            return None
        if os.path.isdir(module_path):
            module_path = os.path.join(module_path, "__init__.py")
            if not os.path.isfile(module_path):
                raise ValueError(f'Cannot find module path: "{module_path}"')
        spec = importlib.util.spec_from_file_location(
            name, os.path.realpath(module_path)
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        sys.modules[name] = mod
        return mod
    except ImportError:
        logger.error(f'Failed to load module: "{module_path}"')
        raise


def resolve_module(name: str, log_error: bool = False):
    """
    Resolves a module by name.

    This function attempts to resolve and import a module by its name.
    It includes an option to log errors if the module cannot be resolved.

    :param name: The name of the module to resolve.
    :param log_error: If True, logs errors if the module cannot be resolved. Defaults to False.
    :return: The resolved module, or None if the module cannot be resolved.
    """

    name = name.split(".")
    used = name.pop(0)
    found = __import__(used)
    for n in name:
        used = used + "." + n
        try:
            found = getattr(found, n)
        except AttributeError:
            try:
                __import__(used)
            except ImportError:
                if log_error:
                    logger.error(traceback.format_exc())
                return None
            found = getattr(found, n)

    return found


def iterate_module(
    module: ModuleType, include_abstract: bool = False, class_filter: type = object
) -> Iterator[tuple[str, type]]:
    """
    Iterates over the classes in a given module.

    This function traverses the specified module and yields the names and types of classes found within it.
    It supports filtering out abstract classes and restricting the iteration to subclasses of a specified type.

    :param module: The module to iterate over.
    :param include_abstract: If True, includes abstract classes in the iteration. Defaults to False.
    :param class_filter: Only include classes that are subclasses of this type. Defaults to object.
    :return: An iterator of tuples, each containing the class name and class type.
    """

    for key, item in module.__dict__.items():
        if not inspect.isclass(item):
            continue
        if inspect.isabstract(item) and not include_abstract:
            continue
        if issubclass(item, class_filter) or item in class_filter:
            yield key, item
        else:
            logger.debug(f"Skipping {key} class")


def iterate_modules(
    path: str,
    exclude: list[str] | None = None,
    skip_inits: bool = True,
    recursive: bool = True,
    return_pyc: bool = False,
) -> list[str]:
    """
    Iterates over modules in the given directory path.

    This function traverses the specified directory and yields modules found within it.
    It supports excluding certain files or directories, skipping `__init__.py` files,
    and recursive traversal.

    :param path: The directory path to search for modules.
    :param exclude: A list of file or directory names to exclude from the search. Defaults to None.
    :param skip_inits: If True, skips `__init__.py` files. Defaults to True.
    :param recursive: If True, searches directories recursively. Defaults to True.
    :param return_pyc: If True, includes `.pyc` files in the results. Defaults to False.
    :return: A list of module paths found in the specified directory.
    """

    exclude = helpers.force_list(exclude)
    _exclude = ["__init__.py", "__init__.pyc"] if skip_inits else list()

    modules_found = dict()

    extension_to_skip = ".pyc" if not return_pyc else ".py"

    if recursive:
        for root, dirs, files in os.walk(path):
            if "__init__.py" not in files:
                continue
            for f in files:
                base_name = os.path.splitext(f)[0]
                if f not in exclude and base_name not in exclude:
                    module_path = pathlib.Path(root, f).as_posix()
                    if f.endswith(".py") or f.endswith(".pyc") and base_name:
                        if base_name in modules_found:
                            if base_name.endswith(extension_to_skip):
                                continue
                            else:
                                if (
                                    base_name.endswith(extension_to_skip)
                                    and base_name not in modules_found
                                ):
                                    modules_found[base_name] = module_path
                        else:
                            modules_found[base_name] = module_path
    else:
        files = os.listdir(path)
        if "__init__.py" not in files:
            return list(modules_found.values())
        for file_name in files:
            base_name = os.path.splitext(file_name)[0]
            if file_name not in exclude and base_name not in exclude:
                module_path = pathlib.Path(path, file_name).as_posix()
                if (
                    file_name.endswith(".py")
                    or file_name.endswith(".pyc")
                    and base_name
                ):
                    if base_name in modules_found:
                        if base_name.endswith(extension_to_skip):
                            continue
                        else:
                            if (
                                base_name.endswith(extension_to_skip)
                                and base_name not in modules_found
                            ):
                                modules_found[base_name] = module_path
                    else:
                        modules_found[base_name] = module_path

    return list(modules_found.values())


def iterate_package(
    package_path: str, force_reload: bool = False
) -> Iterator[ModuleType]:
    """
    Iterates over all modules in a given package.

    This function traverses the specified package path and yields the modules found within it.
    It supports an option to force reload the modules.

    :param package_path: The filesystem path of the package to iterate over.
    :param force_reload: If True, forces reloading of the modules. Defaults to False.
    :return: An iterator of the modules found in the package.
    :raises TypeError: if the given package path does not exist.
    """

    if not os.path.exists(package_path):
        raise TypeError(f"iterate_package() cannot locate package: {package_path}")

    if os.path.isfile(package_path):
        package_path = os.path.dirname(package_path)

    for file_name in os.listdir(package_path):
        module_name, extension = os.path.splitext(file_name)
        if module_name == "__init__" or extension != ".py":
            continue

        # Try and import module
        file_path = os.path.join(package_path, f"{module_name}.py")
        module_path = file_path_to_module_path(file_path)
        logger.info(f'Attempting to import: "{module_path}" module, from: {file_path}')
        try:
            # Import module and check if it should be reloaded
            module = __import__(
                module_path,
                locals=locals(),
                globals=globals(),
                fromlist=[file_path],
                level=0,
            )
            if force_reload:
                logger.info("Reloading module...")
                importlib.reload(module)
            yield module
        except ImportError as exception:
            logger.warning(exception)
            continue


def iterate_module_members(
    module_to_iterate: ModuleType, predicate: Any = None
) -> Iterator[Any]:
    """
    Iterates over the members of a given module.

    This function traverses the specified module and yields its members.
    Optionally, a predicate can be provided to filter the members.

    :param module_to_iterate: The module whose members are to be iterated.
    :param predicate: An optional type to filter the members. Only members that match the predicate will be yielded.
        Defaults to None.
    :return: An iterator of tuples, each containing the member name and member type.
    :rtype: Iterator[ModuleType]
    """

    for mod in inspect.getmembers(module_to_iterate, predicate=predicate):
        yield mod


def iterate_module_subclasses(module: ModuleType, class_type: Type):
    """
    Iterates over all subclasses of a given type in a module.

    This function traverses the specified module and yields all classes that are subclasses of the specified type.

    :param module: The module to iterate over.
    :param class_type: The type to match subclasses against.
    :return: An iterator of tuples, each containing the subclass name and subclass type.
    """

    for member in iterate_module_members(module, predicate=inspect.isclass):
        if issubclass(member, class_type):
            yield member


def get_package_children(module_path: str) -> list[str]:
    """
    Retrieves the names of all child modules in a package.

    This function takes a module path and returns a list of names of all child modules contained in that package.

    :param module_path: The module path of the package.
    :return: A list of names of child modules in the package.
    """

    return [name for _, name, _ in pkgutil.iter_modules([module_path])]


def load_module_from_source(
    file_path: str, unique_namespace=False
) -> ModuleType | None:
    """
    Loads a module from a source file.

    This function loads a module from the specified file path. Optionally, a unique namespace can be used to avoid
    conflicts.

    :param file_path: The filesystem path to the module source file.
    :param unique_namespace: If True, loads the module into a unique namespace to avoid conflicts. Defaults to False.
    :return: The loaded module, or None if the module could not be loaded.
    """

    file_name = os.path.splitext(os.path.basename(file_path))[0]

    module_name = f"{file_name}{str(uuid.uuid4())}" if unique_namespace else file_name

    # noinspection PyBroadException
    try:
        spec = importlib.util.spec_from_file_location(
            module_name, os.path.realpath(file_path)
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        sys.modules[module_name] = mod
        return mod
    except Exception:
        logger.info(
            f"Failed trying to direct load : {file_path} | {traceback.format_exc()}"
        )
        return None


def find_class(
    class_name: str,
    module_path: str,
    __locals__: dict | None = None,
    __globals__: dict | None = None,
) -> type | None:
    """
    Finds and returns a class by its name from a specified module path.

    This function searches for a class with the given name within the specified module path.
    Optionally, local and global dictionaries can be provided for the search context.

    :param class_name: The name of the class to find.
    :param module_path: The path of the module to search in.
    :param __locals__: Optional dictionary of local variables to use in the search context. Defaults to None.
    :param __globals__: Optional dictionary of global variables to use in the search context. Defaults to None.
    :return: The found class, or None if the class could not be found.
    """

    if helpers.is_null_or_empty(class_name):
        return None

    from_list = module_path.split(".", 1)
    module = __import__(
        module_path, locals=__locals__, globals=__globals__, fromlist=from_list, level=0
    )

    return getattr(module, class_name)


def try_import(
    path: str,
    default: Any = None,
    __locals__: dict | None = None,
    __globals__: dict | None = None,
) -> Any:
    """
    Attempts to import a module from the given path.

    This function tries to import a module from the specified path. If the import fails,
    it returns a default value. Optionally, local and global dictionaries can be provided
    for the import context.

    :param path: The path of the module to import.
    :param default: The default value to return if the import fails. Defaults to None.
    :param __locals__: Optional dictionary of local variables to use in the import context. Defaults to None.
    :param __globals__: Optional dictionary of global variables to use in the import context. Defaults to None.
    :return: The imported module, or the default value if the import fails.
    """

    try:
        from_list = path.split(".", 1)
        return __import__(
            path, locals=__locals__, globals=__globals__, fromlist=from_list, level=0
        )
    except ImportError as exception:
        logger.info(exception)
        return default
