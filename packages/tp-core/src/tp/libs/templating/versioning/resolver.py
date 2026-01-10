"""Version resolver for filesystem-based version discovery."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

from tp.libs.templating.versioning.token import VersionToken

if TYPE_CHECKING:
    from tp.libs.templating.paths.resolver import PathResolver


class VersionResolver:
    """Resolve versions from filesystem.

    This class provides utilities to discover, list, and manage versions
    of files in a filesystem based on path templates.

    Example:
        >>> from tp.libs.templating.paths import PathResolver, Template
        >>> from tp.libs.templating.versioning import VersionResolver, VersionToken
        >>>
        >>> # Set up path resolver with versioned template
        >>> resolver = PathResolver()
        >>> resolver.register_template(Template(
        ...     name="asset_version",
        ...     pattern="/content/assets/{asset_name}/v{version}/{asset_name}_v{version}.fbx"
        ... ))
        >>>
        >>> # Create version resolver
        >>> version_resolver = VersionResolver(resolver)
        >>>
        >>> # Find all versions of an asset
        >>> versions = version_resolver.all_versions(
        ...     "asset_version",
        ...     root_path="/content/assets",
        ...     asset_name="hero"
        ... )
        >>> print(versions)  # ['001', '002', '003']
        >>>
        >>> # Get next available version
        >>> next_ver = version_resolver.next_available_version(
        ...     "asset_version",
        ...     root_path="/content/assets",
        ...     asset_name="hero"
        ... )
        >>> print(next_ver)  # '004'
    """

    def __init__(
        self,
        path_resolver: PathResolver,
        version_token: VersionToken | None = None,
        version_key: str = "version",
    ):
        """VersionResolver constructor.

        Args:
            path_resolver: PathResolver instance for path template resolution.
            version_token: VersionToken for parsing/formatting versions.
                          If None, a default VersionToken is created.
            version_key: Name of the version placeholder in templates.
        """

        self._path_resolver = path_resolver
        self._version_token = version_token or VersionToken()
        self._version_key = version_key

    @property
    def path_resolver(self) -> PathResolver:
        """Returns the path resolver."""
        return self._path_resolver

    @property
    def version_token(self) -> VersionToken:
        """Returns the version token."""
        return self._version_token

    @property
    def version_key(self) -> str:
        """Returns the version key name."""
        return self._version_key

    def all_versions(
        self,
        template_name: str,
        root_path: str,
        **tokens,
    ) -> list[str]:
        """List all existing versions matching the template.

        Args:
            template_name: Name of the path template.
            root_path: Root directory to search in.
            **tokens: Known token values (excluding version).

        Returns:
            Sorted list of version strings found.
        """

        template = self._path_resolver.get_template(template_name)
        if template is None:
            raise KeyError(f"Template '{template_name}' not found")

        # Get all template keys
        template_keys = template.keys()

        # Check if version key exists in template
        if self._version_key not in template_keys:
            raise ValueError(
                f"Template '{template_name}' does not contain version key '{self._version_key}'"
            )

        # Build a glob-like pattern by replacing unknown tokens with wildcards
        pattern = template.pattern

        # Create regex pattern from template
        # Replace known tokens with their values
        for key, value in tokens.items():
            pattern = pattern.replace(f"{{{key}}}", re.escape(str(value)))

        # Replace version token with a capture group
        version_pattern = r"(\d+(?:\.\d+)*)"
        pattern = re.sub(
            r"\{" + self._version_key + r"(?::[^}]+)?\}",
            version_pattern,
            pattern,
        )

        # Replace any remaining tokens with wildcards
        pattern = re.sub(r"\{[^}]+\}", r"[^/\\\\]+", pattern)

        # Compile the regex
        try:
            regex = re.compile(pattern)
        except re.error:
            return []

        # Search filesystem
        versions: set[str] = set()
        root = Path(root_path)

        if not root.exists():
            return []

        # Walk the directory tree
        for path in root.rglob("*"):
            if path.is_file():
                # Try to match the path
                path_str = str(path).replace("\\", "/")
                match = regex.search(path_str)
                if match:
                    # Extract version from the match
                    version_str = match.group(1)
                    if self._version_token.is_valid_version(version_str):
                        versions.add(version_str)

        # Sort versions
        return self._version_token.sort_versions(list(versions))

    def latest_version(
        self,
        template_name: str,
        root_path: str,
        **tokens,
    ) -> str | None:
        """Find the latest version matching the template.

        Args:
            template_name: Name of the path template.
            root_path: Root directory to search in.
            **tokens: Known token values (excluding version).

        Returns:
            Latest version string, or None if no versions found.
        """

        versions = self.all_versions(template_name, root_path, **tokens)
        if not versions:
            return None

        # Return the last (highest) version
        return versions[-1]

    def next_available_version(
        self,
        template_name: str,
        root_path: str,
        **tokens,
    ) -> str:
        """Get the next available version number.

        Args:
            template_name: Name of the path template.
            root_path: Root directory to search in.
            **tokens: Known token values (excluding version).

        Returns:
            Next version string (incremented from latest, or start version if none exist).
        """

        latest = self.latest_version(template_name, root_path, **tokens)
        return self._version_token.next_version(latest)

    def version_exists(
        self,
        template_name: str,
        root_path: str,
        version: str,
        **tokens,
    ) -> bool:
        """Check if a specific version exists.

        Args:
            template_name: Name of the path template.
            root_path: Root directory to search in.
            version: Version string to check.
            **tokens: Known token values (excluding version).

        Returns:
            True if the version exists, False otherwise.
        """

        versions = self.all_versions(template_name, root_path, **tokens)
        return version in versions

    def resolve_latest(
        self,
        template_name: str,
        root_path: str,
        **tokens,
    ) -> str | None:
        """Resolve the full path to the latest version.

        Args:
            template_name: Name of the path template.
            root_path: Root directory to search in.
            **tokens: Known token values (excluding version).

        Returns:
            Full path to the latest version, or None if no versions found.
        """

        latest = self.latest_version(template_name, root_path, **tokens)
        if latest is None:
            return None

        # Add version to tokens and resolve
        tokens[self._version_key] = latest
        return self._path_resolver.resolve_path(template_name, **tokens)

    def resolve_version(
        self,
        template_name: str,
        version: str,
        **tokens,
    ) -> str:
        """Resolve the full path for a specific version.

        Args:
            template_name: Name of the path template.
            version: Version string.
            **tokens: Known token values (excluding version).

        Returns:
            Full path for the specified version.
        """

        tokens[self._version_key] = version
        return self._path_resolver.resolve_path(template_name, **tokens)

    def version_count(
        self,
        template_name: str,
        root_path: str,
        **tokens,
    ) -> int:
        """Count the number of versions.

        Args:
            template_name: Name of the path template.
            root_path: Root directory to search in.
            **tokens: Known token values (excluding version).

        Returns:
            Number of versions found.
        """

        return len(self.all_versions(template_name, root_path, **tokens))
