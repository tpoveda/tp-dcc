"""Glob pattern generation from templates."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tp.libs.templating.paths.template import Template


def glob_from_template(
    template: Template,
    **known_tokens,
) -> str:
    """Generate glob pattern from template.

    Known tokens are substituted with their values, unknown tokens
    become wildcards (*).

    Args:
        template: Template to convert.
        **known_tokens: Token values to substitute.

    Returns:
        Glob pattern string.

    Example:
        >>> template = Template(name="asset", pattern="/content/{type}/{name}/v{version}")
        >>> glob_from_template(template, type="characters")
        '/content/characters/*/v*'
    """

    pattern = template.pattern

    # Get all template keys
    keys = template.keys()

    # Replace known tokens with their values
    for key, value in known_tokens.items():
        # Handle both simple {key} and {key:regex} patterns
        pattern = re.sub(
            r"\{" + re.escape(key) + r"(?::[^}]+)?\}", str(value), pattern
        )

    # Replace remaining unknown tokens with wildcards
    for key in keys:
        if key not in known_tokens:
            pattern = re.sub(
                r"\{" + re.escape(key) + r"(?::[^}]+)?\}", "*", pattern
            )

    # Also handle any template references that might remain
    pattern = re.sub(r"\{@[^}]+\}", "*", pattern)

    return pattern


def regex_from_template(
    template: Template,
    **known_tokens,
) -> re.Pattern:
    """Generate regex pattern from template.

    Known tokens are substituted with their escaped values, unknown tokens
    become capture groups.

    Args:
        template: Template to convert.
        **known_tokens: Token values to substitute.

    Returns:
        Compiled regex pattern with named capture groups.

    Example:
        >>> template = Template(name="asset", pattern="/content/{type}/{name}")
        >>> regex = regex_from_template(template, type="characters")
        >>> match = regex.match("/content/characters/hero")
        >>> match.group("name")
        'hero'
    """

    pattern = template.pattern

    # Escape special regex characters except our placeholders
    # First, temporarily replace placeholders
    placeholder_pattern = re.compile(r"\{([^}]+)\}")
    placeholders = []

    def save_placeholder(match):
        placeholders.append(match.group(0))
        return f"__PLACEHOLDER_{len(placeholders) - 1}__"

    pattern = placeholder_pattern.sub(save_placeholder, pattern)

    # Escape the rest
    pattern = re.escape(pattern)

    # Track which keys we've already created named groups for
    seen_keys: set[str] = set()

    # Restore and convert placeholders
    for i, placeholder in enumerate(placeholders):
        placeholder_marker = f"__PLACEHOLDER_{i}__"

        # Parse the placeholder content
        inner = placeholder[1:-1]  # Remove { and }

        # Check if it's a template reference
        if inner.startswith("@"):
            # Template references become wildcards
            pattern = pattern.replace(placeholder_marker, r".*?")
            continue

        # Check for regex expression
        if ":" in inner:
            key, expr = inner.split(":", 1)
        else:
            key = inner
            expr = r"[\w_.\-]+"

        # Check if this is a known token
        if key in known_tokens:
            # Substitute with escaped value
            pattern = pattern.replace(
                placeholder_marker, re.escape(str(known_tokens[key]))
            )
        else:
            # Create capture group - only use named group for first occurrence
            if key not in seen_keys:
                pattern = pattern.replace(
                    placeholder_marker, f"(?P<{key}>{expr})"
                )
                seen_keys.add(key)
            else:
                # Use non-capturing group for duplicates
                pattern = pattern.replace(placeholder_marker, f"(?:{expr})")

    return re.compile("^" + pattern + "$")


def partial_regex_from_template(
    template: Template,
    **known_tokens,
) -> re.Pattern:
    """Generate partial regex pattern (without anchors) from template.

    This allows matching anywhere in a string, useful for searching.

    Args:
        template: Template to convert.
        **known_tokens: Token values to substitute.

    Returns:
        Compiled regex pattern without start/end anchors.
    """

    full_pattern = regex_from_template(template, **known_tokens)
    # Remove anchors
    pattern_str = full_pattern.pattern
    if pattern_str.startswith("^"):
        pattern_str = pattern_str[1:]
    if pattern_str.endswith("$"):
        pattern_str = pattern_str[:-1]

    return re.compile(pattern_str)
