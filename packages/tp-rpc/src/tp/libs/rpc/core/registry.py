from __future__ import annotations

import inspect
from typing import Any
from collections.abc import Callable


# Internal dictionary to hold all registered RPC-safe functions.
_registry: dict[str, Callable[..., Any]] = {}


def register_function(
    name: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator used to register a function into the global RPC registry.

    Functions registered via this decorator become callable remotely by name,
    assuming they are exposed via the server.

    Args:
        name: An optional name to register the function under. If not
        provided, the function's `__name__` will be used.

    Returns:
        Callable: The decorated function, unchanged.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Internal decorator that registers the function into the global RPC
        registry.

        Args:
            func: The function to register.

        Returns:
            Callable: The decorated function, unchanged.
        """

        func_name = name or func.__name__
        _registry[func_name] = func
        return func

    return decorator


def get_function(name: str) -> Callable[..., Any] | None:
    """Retrieve a registered function from the global registry.

    Args:
        name: The name of the function to retrieve.

    Returns:
        The function if found, otherwise None.
    """

    return _registry.get(name)


def list_functions(verbose: bool = False) -> list[str] | list[dict]:
    """Return all registered remote functions.

    Args:
        verbose (bool): If True, include signature and docstring.

    Returns:
        list: List of function names (if verbose=False),
              or dicts with name, signature, and doc (if verbose=True).
    """

    if not verbose:
        return sorted(_registry.keys())

    result: list[dict] = []
    for name, func in _registry.items():
        # noinspection PyBroadException
        try:
            sig = str(inspect.signature(func))
            doc = inspect.getdoc(func) or ""
            doc_line = doc.splitlines()[0] if doc else ""
        except Exception:
            sig = "(...)"
            doc_line = ""

        result.append(
            {
                "name": name,
                "signature": f"{name}{sig}",
                "doc": doc_line,
            }
        )

    return sorted(result, key=lambda f: f["name"])


def describe_function(name: str) -> dict:
    """Return signature and full docstring for a specific registered function.

    Args:
        name: The registered function name.

    Returns:
        Includes 'found', 'signature', and 'doc' keys.

    Raises:
        PermissionError: If remote function introspection is disabled.
    """

    func = _registry.get(name)
    if not func:
        return {"found": False, "signature": None, "doc": None}

    try:
        sig = inspect.signature(func)
        args = []

        for param in sig.parameters.values():
            args.append(
                {
                    "name": param.name,
                    "type": str(param.annotation)
                    if param.annotation != inspect._empty
                    else None,
                    "default": param.default
                    if param.default != inspect._empty
                    else None,
                }
            )
        return_type = (
            str(sig.return_annotation)
            if sig.return_annotation != inspect._empty
            else None
        )
        doc = inspect.getdoc(func)
        return {
            "found": True,
            "signature": f"{name}{sig}",
            "doc": doc,
            "args": args,
            "return_type": return_type,
        }
    except Exception as e:
        return {
            "found": True,
            "signature": "(unavailable)",
            "doc": f"(failed to introspect: {e})",
            "args": [],
            "return_type": None,
        }
