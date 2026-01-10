"""PathResolver that links path templates to naming conventions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tp.libs.templating.paths.template import Resolver, Template

if TYPE_CHECKING:
    from tp.libs.templating.naming.convention import NamingConvention


class PathResolver(Resolver):
    """Resolver that links path templates to naming conventions.

    This allows deriving file paths from naming convention tokens, enabling
    a unified system where naming conventions and path structures work together.

    Example:
        >>> from tp.libs.templating.naming.convention import NamingConvention
        >>> from tp.libs.templating.paths.resolver import PathResolver
        >>> from tp.libs.templating.paths.template import Template
        >>>
        >>> # Create a naming convention with tokens
        >>> convention = NamingConvention(naming_data={"name": "project"})
        >>> convention.add_token("asset_type", character="CHR", prop="PRP")
        >>> convention.add_token("side", left="L", right="R")
        >>>
        >>> # Create a path resolver linked to the naming convention
        >>> resolver = PathResolver(naming_convention=convention)
        >>>
        >>> # Register path templates
        >>> resolver.register_template(Template(
        ...     name="asset_root",
        ...     pattern="/content/assets/{asset_type}/{asset_name}"
        ... ))
        >>> resolver.register_template(Template(
        ...     name="asset_texture",
        ...     pattern="{@asset_root}/textures/T_{asset_name}_{texture_type}.png",
        ...     template_resolver=resolver
        ... ))
        >>>
        >>> # Resolve a path using naming convention tokens
        >>> path = resolver.resolve_path(
        ...     "asset_texture",
        ...     asset_type="character",  # Will be resolved to "CHR" via naming convention
        ...     asset_name="hero",
        ...     texture_type="diffuse"
        ... )
        >>> print(path)
        '/content/assets/CHR/hero/textures/T_hero_diffuse.png'
    """

    def __init__(
        self,
        naming_convention: NamingConvention | None = None,
        templates: dict[str, Template] | None = None,
    ):
        """PathResolver constructor.

        Args:
            naming_convention: Optional naming convention to use for token resolution.
            templates: Optional dictionary of templates to register.
        """

        super().__init__()

        self._naming_convention = naming_convention
        self._templates: dict[str, Template] = templates or {}

    @property
    def naming_convention(self) -> NamingConvention | None:
        """Returns the naming convention used for token resolution.

        Returns:
            NamingConvention or None.
        """

        return self._naming_convention

    @naming_convention.setter
    def naming_convention(self, value: NamingConvention | None):
        """Sets the naming convention used for token resolution.

        Args:
            value: NamingConvention or None.
        """

        self._naming_convention = value

    @property
    def templates(self) -> dict[str, Template]:
        """Returns all registered templates.

        Returns:
            Dictionary mapping template names to Template instances.
        """

        return self._templates.copy()

    def register_template(self, template: Template):
        """Register a path template.

        Args:
            template: Template instance to register.
        """

        self._templates[template.name] = template
        # Set this resolver as the template's resolver for reference resolution
        template.template_resolver = self

    def unregister_template(self, template_name: str) -> bool:
        """Unregister a path template by name.

        Args:
            template_name: Name of the template to unregister.

        Returns:
            True if template was unregistered, False if not found.
        """

        if template_name in self._templates:
            del self._templates[template_name]
            return True
        return False

    def get(self, template_name: str, default=None) -> str | None:
        """Get a template pattern by name.

        This method is used by Template instances to resolve template references.

        Args:
            template_name: Name of the template to retrieve.
            default: Value to return if template is not found.

        Returns:
            Template pattern string or default value.
        """

        template = self._templates.get(template_name)
        if template is not None:
            return template.pattern
        return default

    def get_template(self, template_name: str) -> Template | None:
        """Get a Template instance by name.

        Args:
            template_name: Name of the template to retrieve.

        Returns:
            Template instance or None if not found.
        """

        return self._templates.get(template_name)

    def resolve_path(
        self,
        template_name: str,
        resolve_tokens: bool = True,
        **token_values,
    ) -> str:
        """Resolve a path using naming convention tokens.

        Args:
            template_name: Name of the path template to use.
            resolve_tokens: If True, resolve token values through naming convention.
            **token_values: Token values to use in the path.

        Returns:
            Resolved path string.

        Raises:
            KeyError: If template is not found.
        """

        template = self.get_template(template_name)
        if template is None:
            raise KeyError(f"Template '{template_name}' not found")

        # Resolve tokens through naming convention if available
        resolved_data = {}
        if self._naming_convention and resolve_tokens:
            for key, value in token_values.items():
                token = self._naming_convention.token(key)
                if token:
                    resolved_data[key] = token.solve(
                        value, default_value=value
                    )
                else:
                    resolved_data[key] = value
        else:
            resolved_data = token_values

        return template.format(resolved_data)

    def parse_path(
        self,
        template_name: str,
        path: str,
        reverse_tokens: bool = True,
    ) -> dict:
        """Parse a path and return token values.

        Args:
            template_name: Name of the path template to use.
            path: Path string to parse.
            reverse_tokens: If True, reverse-resolve token values through naming convention
                            (e.g., "CHR" -> "character").

        Returns:
            Dictionary of parsed token values.

        Raises:
            KeyError: If template is not found.
            ParseError: If path does not match the template pattern.
        """

        template = self.get_template(template_name)
        if template is None:
            raise KeyError(f"Template '{template_name}' not found")

        parsed = template.parse(path)

        # Reverse-resolve tokens through naming convention if available
        if self._naming_convention and reverse_tokens:
            resolved_data = {}
            for key, value in parsed.items():
                if isinstance(value, dict):
                    # Handle nested dictionaries
                    resolved_data[key] = value
                    continue
                token = self._naming_convention.token(key)
                if token:
                    # Try to find the key for this value
                    token_key = token.parse(value)
                    resolved_data[key] = token_key if token_key else value
                else:
                    resolved_data[key] = value
            return resolved_data

        return parsed

    def list_templates(self) -> list[str]:
        """Returns a list of all registered template names.

        Returns:
            List of template names.
        """

        return list(self._templates.keys())

    def clear_templates(self):
        """Removes all registered templates."""

        self._templates.clear()
