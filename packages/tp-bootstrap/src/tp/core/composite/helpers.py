from __future__ import annotations

from collections.abc import Callable

from .composition import Composition, Ignore


def composition_methods(
    composition_instance: Composition, method_name: str
) -> list[Callable]:
    """Retrieves a list of all the methods which require calling.

    Args:
        composition_instance: The composition instance to check for methods.
        method_name: The name of the method to check.

    Returns:
        A list of methods that match the given name.
    """

    return [
        getattr(component, method_name)
        for component in composition_instance.components()
        if hasattr(component, method_name)
    ]


def composition_results(
    composition_instance: Composition, method_name: str, *args, **kwargs
) -> list[Composition]:
    """Returns all teh results for the methods with the given name on the
    class.

    Args:
        composition_instance: The composition instance to check for methods.
        method_name: The name of the method to check.
        *args: Positional arguments to pass to the methods.
        **kwargs: Keyword arguments to pass to the methods.

    Returns:
        A list of results from the methods.
    """

    results: list[Composition] = []

    for method in composition_methods(composition_instance, method_name):
        result = method(*args[1:], **kwargs)

        if isinstance(result, Ignore):
            continue

        results.append(result)

    return results
