"""Built-in node library for PipeGraph.

This package provides a comprehensive library of pre-built nodes for
common operations including math, logic, control flow, variables,
debugging, and type conversion.

Usage:
    # Import specific nodes
    from tp.libs.pipegraph.nodes import AddNode, SubtractNode, BranchNode

    # Import all nodes from a category
    from tp.libs.pipegraph.nodes.math import *

    # Register all built-in nodes with the registry
    from tp.libs.pipegraph.nodes import register_all_nodes
    register_all_nodes()
"""

from __future__ import annotations


def register_all_nodes() -> int:
    """Register all built-in nodes with the global registry.

    Returns:
        The number of nodes registered.

    Example:
        >>> from tp.libs.pipegraph.nodes import register_all_nodes
        >>> count = register_all_nodes()
        >>> print(f"Registered {count} built-in nodes")
    """
