"""Pattern parsing and formatting utilities for path templates."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from functools import partial
from typing import TYPE_CHECKING

from tp.libs.templating import consts, errors

if TYPE_CHECKING:
    from tp.libs.templating.paths.template import Resolver

# Regex patterns
STRIP_EXPRESSION_REGEX = re.compile(r"{(.+?)(:(\\}|.)+?)}")
PLAIN_PLACEHOLDER_REGEX = re.compile(r"{(.+?)}")
TEMPLATE_REFERENCE_REGEX = re.compile(r"{@(?P<reference>.+?)}")


def regular_expression_from_pattern(
    pattern: str,
    anchor: int = consts.START_ANCHOR,
) -> re.Pattern[str]:
    """Returns a regular expression that represents a pattern.

    Args:
        pattern: Template pattern, e.g.:
            '/jobs/{job}/assets/{asset_name}/model/{lod}/{asset_name}_{lod}_v{version}.{filetype}'
        anchor: Anchor that determines how the pattern is anchored during the parse process.

    Returns:
        Regular expression representing given pattern.
    """

    def _escape(_match: re.Match) -> str:
        """Internal function that escapes matched "other" group value."""
        _groups = _match.groupdict()
        if _groups["other"] is not None:
            return re.escape(_groups["other"])
        return _groups["placeholder"]

    def _convert(
        _match: re.Match, _placeholder_count: defaultdict[str, int]
    ) -> str:
        """Internal function that returns a regular expression to represent a match."""
        _placeholder_name = _match.group("placeholder")

        # Support at symbol (@) as referenced template indicator.
        _placeholder_name = _placeholder_name.replace("@", consts.AT_CODE)

        # Support period (.) as nested key indicator.
        _placeholder_name = _placeholder_name.replace(".", consts.PERIOD_CODE)

        # Add unique count to support duplicate placeholder names.
        _placeholder_count[_placeholder_name] += 1
        _placeholder_name += "{0:03d}".format(
            _placeholder_count[_placeholder_name]
        )

        _expression = _match.group("expression")
        _expression = _expression or r"[\w_.\-]+"

        # Un-escape potentially escaped characters in expression.
        _expression = _expression.replace("\\{", "{").replace("\\}", "}")

        return r"(?P<{0}>{1})".format(_placeholder_name, _expression)

    # Escape non-placeholder components
    expression = re.sub(
        r"(?P<placeholder>{(.+?)(:(\\}|.)+?)?})|(?P<other>.+?)",
        _escape,
        pattern,
    )

    # Replace placeholders with regex pattern.
    expression = re.sub(
        r"{(?P<placeholder>.+?)(:(?P<expression>(\\}|.)+?))?}",
        partial(_convert, _placeholder_count=defaultdict(int)),
        expression,
    )

    # Add anchor if necessary.
    if anchor is not None:
        if bool(anchor & consts.START_ANCHOR):
            expression = f"^{expression}"
        if bool(anchor & consts.END_ANCHOR):
            expression = f"{expression}$"

    # Compile expression.
    try:
        compiled = re.compile(expression)
    except re.error as error:
        if any(
            [
                "bad group name" in str(error),
                "bad character in group name" in str(error),
            ]
        ):
            raise ValueError("Placeholder name contains invalid characters.")
        else:
            _, value, traceback = sys.exc_info()
            raise ValueError(f"Invalid pattern: {value}| {traceback}")

    return compiled


def expand_pattern(
    pattern: str,
    template_resolver: Resolver | None = None,
) -> str:
    """Returns pattern with all referenced templates expanded recursively.

    Args:
        pattern: Pattern to expand.
        template_resolver: Optional template resolver for resolving template references.

    Returns:
        Expanded pattern.
    """

    def _expand_reference(_match: re.Match) -> str:
        """Internal function that expands a reference represented by a regex match object."""
        _reference = _match.group("reference")

        if template_resolver is None:
            raise errors.ResolveError(
                f"Failed to resolve reference {_reference!r} as no template resolver set."
            )

        _template = template_resolver.get(_reference)
        if _template is None:
            raise errors.ResolveError(
                f"Failed to resolve reference {_reference!r} using template resolver."
            )

        return expand_pattern(_template, template_resolver)

    return TEMPLATE_REFERENCE_REGEX.sub(_expand_reference, pattern)


def format_specification_from_pattern(pattern: str) -> str:
    """Returns format specification for given pattern.

    Args:
        pattern: Pattern to get format specification of.

    Returns:
        Format specification.
    """

    return STRIP_EXPRESSION_REGEX.sub(r"{\g<1>}", pattern)


def keys_from_pattern(
    pattern: str,
    template_resolver: Resolver | None = None,
) -> set[str]:
    """Returns unique set of placeholders in pattern.

    Args:
        pattern: Pattern to get placeholder keys of.
        template_resolver: Optional template resolver for resolving template references.

    Returns:
        Pattern placeholder keys.
    """

    format_specification = format_specification_from_pattern(
        expand_pattern(pattern, template_resolver)
    )
    return set(PLAIN_PLACEHOLDER_REGEX.findall(format_specification))


def parse_path_by_pattern(
    path: str,
    pattern: str,
    duplicate_placeholder_mode: int = consts.RELAXED_PARSE,
    template_resolver: Resolver | None = None,
) -> dict:
    """Parses a path using the given pattern and returns extracted data.

    Args:
        path: Path to parse.
        pattern: Pattern to use for parsing.
        duplicate_placeholder_mode: Mode for handling duplicate placeholders.
        template_resolver: Optional template resolver for resolving template references.

    Returns:
        Dictionary of parsed data.

    Raises:
        ParseError: If path does not match the template pattern.
    """

    # Construct regular expression for expanded pattern.
    regex = regular_expression_from_pattern(
        expand_pattern(pattern, template_resolver)
    )

    # Parse.
    parsed = {}

    match = regex.search(path)
    if match:
        data = {}
        for key, value in sorted(match.groupdict().items()):
            # Strip number that was added to make group name unique.
            key = key[:-3]

            # If strict mode enabled for duplicate placeholders, ensure that
            # all duplicate placeholders extract the same value.
            if duplicate_placeholder_mode == consts.STRICT_PARSE:
                if key in parsed:
                    if parsed[key] != value:
                        raise errors.ParseError(
                            f"Different extracted values for placeholder {key!r} detected. "
                            f"Values were {parsed[key]!r} and {value!r}."
                        )
                else:
                    parsed[key] = value

            # Expand dot notation keys into nested dictionaries.
            target = data

            parts = key.split(consts.PERIOD_CODE)
            for part in parts[:-1]:
                target = target.setdefault(part, {})

            target[parts[-1]] = value
        return data

    else:
        raise errors.ParseError(
            f"Path {path!r} did not match template pattern."
        )


def path_from_parsed_data(
    pattern: str,
    data: dict,
    template_resolver: Resolver | None = None,
) -> str:
    """Returns a path formatted by given data.

    Args:
        pattern: Pattern used to format data.
        data: Parsed pattern data.
        template_resolver: Optional template resolver for resolving template references.

    Returns:
        Formatted path string.
    """

    def _format(_match: re.Match, _data: dict) -> str:
        """Internal function that returns value from data for given match object."""
        placeholder = _match.group(1)
        parts = placeholder.split(".")
        try:
            value = _data
            for part in parts:
                value = value[part]
        except (TypeError, KeyError):
            raise errors.FormatError(
                f"Could not format data {_data!r} due to missing key {placeholder!r}."
            )
        else:
            return value

    format_specification = format_specification_from_pattern(
        expand_pattern(pattern, template_resolver)
    )

    return PLAIN_PLACEHOLDER_REGEX.sub(
        partial(_format, _data=data), format_specification
    )
