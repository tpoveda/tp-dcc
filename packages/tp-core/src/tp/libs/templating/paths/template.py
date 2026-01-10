"""Template class for path patterns."""

from __future__ import annotations

import abc
from typing import Any

from tp.libs.templating import consts
from tp.libs.templating.paths.pattern import (
    expand_pattern,
    keys_from_pattern,
    parse_path_by_pattern,
    path_from_parsed_data,
    regular_expression_from_pattern,
)


class Template:
    """Class that defines a path template by a name and a path pattern.

    A template anchor determines how the pattern is anchored during the parse process:
        - Start anchor (1): Default anchor that will match the pattern against the start of a path.
        - End anchor (2): Will match the pattern against the end of a path.
        - Both anchors (3): Will match the pattern against the start and end (full path match).
        - None: Will try to match the pattern once anywhere in the path.

    If a template resolver is given, it will be used to resolve any template referenced in the pattern
    during operations.

    Example:
        >>> template = Template(
        ...     name="asset_texture",
        ...     pattern="/content/textures/{asset}/{texture_type}/T_{asset}_{texture_type}.png"
        ... )
        >>> template.parse("/content/textures/hero/diffuse/T_hero_diffuse.png")
        {'asset': 'hero', 'texture_type': 'diffuse'}
        >>> template.format({'asset': 'villain', 'texture_type': 'normal'})
        '/content/textures/villain/normal/T_villain_normal.png'
    """

    def __init__(
        self,
        name: str,
        pattern: str,
        anchor: int = consts.START_ANCHOR,
        duplicate_placeholder_mode: int = consts.RELAXED_PARSE,
        template_resolver: Resolver | None = None,
    ):
        """Template constructor.

        Args:
            name: Name to identify this template.
            pattern: Path pattern with placeholders (e.g., "/jobs/{job}/assets/{asset_name}").
            anchor: Anchor mode for pattern matching.
            duplicate_placeholder_mode: Mode for handling duplicate placeholders.
            template_resolver: Optional resolver for template references.
        """

        super().__init__()

        self._name = name
        self._pattern = pattern
        self._anchor = anchor
        self._duplicate_placeholder_mode = duplicate_placeholder_mode
        self._template_resolver = template_resolver

        # Check that supplied pattern is valid and able to be compiled.
        regular_expression_from_pattern(pattern)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self._name}, pattern={self._pattern})"

    @property
    def name(self) -> str:
        """Returns the name for this template.

        Returns:
            Template name used for identification.
        """

        return self._name

    @property
    def pattern(self) -> str:
        """Returns the pattern for this template.

        Returns:
            Template pattern string.
        """

        return self._pattern

    @property
    def anchor(self) -> int:
        """Returns the anchor mode for this template.

        Returns:
            Anchor mode (START_ANCHOR, END_ANCHOR, BOTH_ANCHOR, or None).
        """

        return self._anchor

    @property
    def template_resolver(self) -> Resolver | None:
        """Returns the template resolver for this template.

        Returns:
            Template resolver or None.
        """

        return self._template_resolver

    @template_resolver.setter
    def template_resolver(self, value: Resolver | None):
        """Sets the template resolver for this template.

        Args:
            value: Template resolver or None.
        """

        self._template_resolver = value

    def expanded_pattern(self) -> str:
        """Returns pattern with all referenced templates expanded recursively.

        Returns:
            Expanded pattern.
        """

        return expand_pattern(self._pattern, self._template_resolver)

    def keys(self) -> set[str]:
        """Returns unique set of placeholders in pattern.

        Returns:
            Set of placeholder keys.
        """

        return keys_from_pattern(self._pattern, self._template_resolver)

    def parse(self, path: str) -> dict:
        """Returns a dictionary of data extracted from given path using the pattern.

        Args:
            path: Path to parse.

        Returns:
            Dictionary of parsed data.

        Raises:
            ParseError: If given path is not parsable by this template.
        """

        return parse_path_by_pattern(
            path,
            self._pattern,
            self._duplicate_placeholder_mode,
            self._template_resolver,
        )

    def format(self, data: dict) -> str:
        """Returns a path formatted by given data.

        Args:
            data: Dictionary of data to format into the pattern.

        Returns:
            Formatted path string.

        Raises:
            FormatError: If data is missing required keys.
        """

        return path_from_parsed_data(
            self._pattern, data, self._template_resolver
        )


class Resolver(abc.ABC):
    """Abstract base class for template resolvers.

    A resolver is used to look up templates by name, enabling template references
    in patterns (e.g., "{@other_template}/subfolder").

    Example:
        >>> class DictResolver(Resolver):
        ...     def __init__(self, templates):
        ...         self._templates = templates
        ...     def get(self, template_name, default=None):
        ...         return self._templates.get(template_name, default)
        ...
        >>> resolver = DictResolver({"base": "/content/{project}"})
        >>> template = Template("asset", "{@base}/assets/{asset}", template_resolver=resolver)
    """

    @abc.abstractmethod
    def get(self, template_name: str, default: Any = None) -> Any:
        """Returns template that matches given template name.

        Args:
            template_name: Name of the template to retrieve.
            default: Value to return if no template is found.

        Returns:
            Found template or default value.
        """

        return default

    @classmethod
    def __subclasshook__(cls, subclass: type):
        """Returns whether given subclass supports this interface.

        Args:
            subclass: Class to check.
        """

        if cls is Resolver:
            return callable(getattr(subclass, "get", None))

        return NotImplemented
