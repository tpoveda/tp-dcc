"""tp.libs.templating.context - Context inheritance module.

This module provides hierarchical context management including:
- TemplateContext: Hierarchical context with inheritance
- ContextStack: Stack-based context management
"""

from __future__ import annotations

from tp.libs.templating.context.context import ContextStack, TemplateContext

__all__ = [
    "TemplateContext",
    "ContextStack",
]
