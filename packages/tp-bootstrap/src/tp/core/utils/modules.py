from __future__ import annotations

import os
import sys
import uuid
import pathlib
import inspect
import importlib
import traceback
import importlib.util
from typing import Any
from types import ModuleType
from collections.abc import Callable, Sequence, Iterator

from loguru import logger


MODULE_EXCLUDE_PREFIXES = (
    "__init__.py",
    ".__init__",
    "._",
)


def is_valid_module_path(
    path: str, exclude: Sequence[str] | set[str] | None = None
) -> bool:
    """Returns whether the given path is a valid module path.

    Args:
        path: Path to check.
        exclude: Names to exclude from the check.

    Returns:
        Whether the given path is a valid module path.
    """

    exclude = exclude or []
    base_name = os.path.basename(path)
    if not base_name.startswith(MODULE_EXCLUDE_PREFIXES) and base_name not in exclude:
        return pathlib.Path(path).suffix in (".py", ".pyc")

    return False


def convert_to_dotted_path(path: str) -> str:
    """Returns a dotted path relative to the given path.

    Args:
        path: Python file path to convert (eg. myPath/folder/test.py).

    Returns:
        dotted path (e.g. folder.test)
    """

    directory, file_path = os.path.split(path)
    file_name = os.path.splitext(file_path)[0]
    package_path = [file_name]

    # Normalize sys.path entries to POSIX style for consistent comparison
    sys_path = set(pathlib.Path(p).resolve().as_posix() for p in sys.path if p)

    # Get the absolute resolved directory in POSIX format
    directory = pathlib.Path(directory).resolve().as_posix()

    # We ignore current working directory. Useful if we want to execute tools
    # directly inside PyCharm.
    current_work_dir = pathlib.Path(os.getcwd()).as_posix()
    if current_work_dir in sys_path:
        sys_path.remove(current_work_dir)

    drive_root = pathlib.Path(directory).drive

    # Iterate up the directory tree.
    while True:
        if directory in sys_path:
            break
        parent, name = os.path.split(directory)
        if not name or parent == drive_root:
            return ""
        package_path.append(name)
        directory = parent

    return ".".join(reversed(package_path))


def is_dotted_path(path: str) -> bool:
    """Returns whether the given path is dotted (tp.utils).

    Args:
        path: path to check.

    Returns:
        True if the given path is dotted; False otherwise.
    """

    return len(path.split(".")) > 2


def safe_import_module(module_path: str, name: str | None = None) -> ModuleType | None:
    """Imports the given module path safely.

    Args:
        module_path: module dotted path (tp.utils) or an absolute one.
        name: name for the imported module which will be used if the module
            path is an absolute path. If not given, then `module_path`
            basename without the extension will be used.

    Returns:
        imported module object
    """

    # noinspection PyBroadException
    try:
        return import_module(
            module_path, name=name, skip_errors=True, skip_warnings=True
        )
    except Exception:
        return None


def import_module(
    module_path: str,
    name: str | None = None,
    skip_warnings: bool = True,
    skip_errors: bool = False,
) -> ModuleType | None:
    """Imports the given module path. If the given module path is a dotted
        one, import lib will be used. Otherwise, it's expected that given
        module path is the absolute path to the source file.

    Args:
        module_path: module dotted path (tp.utils) or an absolute one.
        name: name for the imported module which will be used if the module
            path is an absolute path. If not given, then `module_path`
            basename without the extension will be used.
        skip_warnings: whether warnings should be skipped.
        skip_errors: whether errors should be skipped.

    Returns:
        imported module object

    Raises:
        ImportError: if an error occurs while importing module.
    """

    if is_dotted_path(module_path) and not os.path.exists(module_path):
        try:
            return importlib.import_module(module_path)
        except (NameError, KeyError, AttributeError) as exc:
            if "__init__" in str(exc) or "__path__" in str(exc):
                pass
            else:
                msg = 'Failed to load module: "{}"'.format(module_path)
                logger.error(msg, exc_info=True) if not skip_errors else logger.debug(
                    "{} | {}".format(msg, traceback.format_exc())
                )
        except (ImportError, ModuleNotFoundError):
            msg = 'Failed to import module: "{}"'.format(module_path)
            logger.error(msg, exc_info=True) if not skip_errors else logger.debug(
                "{} | {}".format(msg, traceback.format_exc())
            )
            return None
        except SyntaxError:
            msg = 'Module contains syntax errors: "{}"'.format(module_path)
            logger.error(msg, exc_info=True) if not skip_errors else logger.debug(
                "{} | {}".format(msg, traceback.format_exc())
            )
            return None

    if os.path.exists(module_path):
        name = name or os.path.splitext(os.path.basename(module_path))[0]
        if name in sys.modules:
            return sys.modules[name]

    if not name:
        if not skip_warnings:
            logger.warning(
                f"Impossible to load module because module "
                f"path: {module_path} was not found!"
            )
        return None

    if os.path.isdir(module_path):
        module_path = os.path.join(module_path, "__init__.py")
        if not os.path.isfile(module_path):
            raise ValueError(f'Cannot find module path: "{module_path}"')

    try:
        spec = importlib.util.spec_from_file_location(
            name, os.path.realpath(module_path)
        )
        mod = importlib.util.module_from_spec(spec)  # type: ignore
        spec.loader.exec_module(mod)  # type: ignore
        sys.modules[name] = mod
    except ImportError:
        msg = 'Failed to import module: "{}"'.format(module_path)
        logger.error(msg, exc_info=True) if not skip_errors else logger.debug(
            "{} | {}".format(msg, traceback.format_exc())
        )
        raise

    return mod


def load_module_from_source(
    file_path: str, unique_namespace: bool = False
) -> ModuleType | None:
    """Loads a Python from given source file.

    Args:
        file_path: absolute path pointing to a Python file.
        unique_namespace: whether to load module within a unique namespace.

    Returns:
        ModuleType or None: loaded module.
    """

    file_name = os.path.splitext(os.path.basename(file_path))[0]

    module_name = f"{file_name}{str(uuid.uuid4())}" if unique_namespace else file_name

    # noinspection PyBroadException
    try:
        spec = importlib.util.spec_from_file_location(
            module_name, os.path.realpath(file_path)
        )
        mod = importlib.util.module_from_spec(spec)  # type: ignore
        spec.loader.exec_module(mod)  # type: ignore
        sys.modules[module_name] = mod
        return mod
    except Exception:
        logger.error(f"Failed trying to direct load : {file_path}", exc_info=True)
        return None


def iterate_package_modules(
    path: str, exclude: Sequence[str] | None = None
) -> Iterator[str]:
    """Iterates over the modules found in the given path.

    Args:
        path: path to iterate over.
        exclude: names to exclude from the iteration.

    Yields:
        module path.
    """

    exclude_set = set(exclude) if exclude else set()
    resolved_path = pathlib.Path(path).resolve()
    for root, _, files in os.walk(resolved_path):
        root_path = pathlib.Path(root)
        is_package = any(file.endswith(".py") for file in files)
        if not is_package:
            continue
        for file_name in files:
            module_path = root_path / file_name
            if is_valid_module_path(str(module_path), exclude=exclude_set):
                yield module_path.as_posix()


def iterate_module_members(
    module: ModuleType, predicate: Callable[[Any], bool] | None = None
) -> Iterator[tuple[str, object]]:
    """Iterates over the members of the given module.

    Args:
        module: module to iterate over.
        predicate: predicate to filter members.

    Yields:
        member name and object.
    """

    yield from inspect.getmembers(module, predicate=predicate)
