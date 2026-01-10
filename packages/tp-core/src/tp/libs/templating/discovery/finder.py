"""Template-based asset discovery."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

from tp.libs.templating.discovery.glob import (
    glob_from_template,
    regex_from_template,
)

if TYPE_CHECKING:
    from tp.libs.templating.paths.resolver import PathResolver
    from tp.libs.templating.versioning.token import VersionToken


@dataclass
class DiscoveredAsset:
    """An asset discovered through pattern matching.

    Attributes:
        path: Full path to the discovered file.
        parsed_tokens: Token values extracted from the path.
        template_name: Name of the template that matched.
        asset_type: Detected or specified asset type.
        version: Extracted version string (if applicable).
        metadata: Additional metadata about the asset.
    """

    path: str
    parsed_tokens: dict[str, str] = field(default_factory=dict)
    template_name: str = ""
    asset_type: str | None = None
    version: str | None = None
    metadata: dict = field(default_factory=dict)

    @property
    def filename(self) -> str:
        """Returns the filename without path."""
        return os.path.basename(self.path)

    @property
    def directory(self) -> str:
        """Returns the directory containing the file."""
        return os.path.dirname(self.path)

    @property
    def extension(self) -> str:
        """Returns the file extension."""
        return os.path.splitext(self.path)[1]

    @property
    def name_without_extension(self) -> str:
        """Returns the filename without extension."""
        return os.path.splitext(os.path.basename(self.path))[0]

    def get_token(self, key: str, default: str = "") -> str:
        """Get a parsed token value.

        Args:
            key: Token key to retrieve.
            default: Default value if not found.

        Returns:
            Token value or default.
        """
        return self.parsed_tokens.get(key, default)


class TemplateDiscovery:
    """Discover files matching templates.

    This class provides utilities to scan directories and find files
    that match registered path templates.

    Example:
        >>> from tp.libs.templating.paths import PathResolver, Template
        >>> from tp.libs.templating.discovery import TemplateDiscovery
        >>>
        >>> # Set up resolver with templates
        >>> resolver = PathResolver()
        >>> resolver.register_template(Template(
        ...     name="character_model",
        ...     pattern="/content/characters/{name}/v{version}/{name}_v{version}.fbx"
        ... ))
        >>>
        >>> # Create discovery
        >>> discovery = TemplateDiscovery(resolver)
        >>>
        >>> # Find all character models
        >>> assets = discovery.find_matching("character_model", "/content")
        >>> for asset in assets:
        ...     print(f"{asset.parsed_tokens['name']} v{asset.version}")
    """

    def __init__(
        self,
        path_resolver: PathResolver,
        version_key: str = "version",
    ):
        """TemplateDiscovery constructor.

        Args:
            path_resolver: PathResolver with registered templates.
            version_key: Name of the version token in templates.
        """

        self._path_resolver = path_resolver
        self._version_key = version_key

    @property
    def path_resolver(self) -> PathResolver:
        """Returns the path resolver."""
        return self._path_resolver

    def find_matching(
        self,
        template_name: str,
        root_path: str,
        recursive: bool = True,
        file_extensions: list[str] | None = None,
        **partial_tokens,
    ) -> list[DiscoveredAsset]:
        """Find all files matching template with optional filters.

        Args:
            template_name: Name of the template to match.
            root_path: Root directory to search.
            recursive: If True, search subdirectories.
            file_extensions: Optional list of extensions to filter.
            **partial_tokens: Known token values to filter by.

        Returns:
            List of discovered assets.
        """

        template = self._path_resolver.get_template(template_name)
        if template is None:
            raise KeyError(f"Template '{template_name}' not found")

        # Generate regex for matching
        regex = regex_from_template(template, **partial_tokens)

        # Normalize extensions
        if file_extensions:
            file_extensions = [
                ext if ext.startswith(".") else f".{ext}"
                for ext in file_extensions
            ]

        discovered: list[DiscoveredAsset] = []
        root = Path(root_path)

        if not root.exists():
            return discovered

        # Choose iteration method
        if recursive:
            files = root.rglob("*")
        else:
            files = root.glob("*")

        for path in files:
            if not path.is_file():
                continue

            # Check extension filter
            if file_extensions:
                if path.suffix.lower() not in [
                    e.lower() for e in file_extensions
                ]:
                    continue

            # Try to match against template
            path_str = str(path).replace("\\", "/")
            match = regex.match(path_str)

            if match:
                parsed = match.groupdict()

                # Extract version if present
                version = parsed.get(self._version_key)

                discovered.append(
                    DiscoveredAsset(
                        path=str(path),
                        parsed_tokens=parsed,
                        template_name=template_name,
                        version=version,
                    )
                )

        return discovered

    def find_matching_iter(
        self,
        template_name: str,
        root_path: str,
        recursive: bool = True,
        **partial_tokens,
    ) -> Iterator[DiscoveredAsset]:
        """Iterate over files matching template (memory efficient).

        Args:
            template_name: Name of the template to match.
            root_path: Root directory to search.
            recursive: If True, search subdirectories.
            **partial_tokens: Known token values to filter by.

        Yields:
            Discovered assets.
        """

        template = self._path_resolver.get_template(template_name)
        if template is None:
            raise KeyError(f"Template '{template_name}' not found")

        regex = regex_from_template(template, **partial_tokens)
        root = Path(root_path)

        if not root.exists():
            return

        files = root.rglob("*") if recursive else root.glob("*")

        for path in files:
            if not path.is_file():
                continue

            path_str = str(path).replace("\\", "/")
            match = regex.match(path_str)

            if match:
                parsed = match.groupdict()
                version = parsed.get(self._version_key)

                yield DiscoveredAsset(
                    path=str(path),
                    parsed_tokens=parsed,
                    template_name=template_name,
                    version=version,
                )

    def find_latest_versions(
        self,
        template_name: str,
        root_path: str,
        version_token: VersionToken | None = None,
        **partial_tokens,
    ) -> list[DiscoveredAsset]:
        """Find latest version of each unique asset.

        Groups assets by all tokens except version, then returns
        only the latest version of each group.

        Args:
            template_name: Name of the template to match.
            root_path: Root directory to search.
            version_token: Optional VersionToken for version comparison.
            **partial_tokens: Known token values to filter by.

        Returns:
            List of latest version assets.
        """

        all_assets = self.find_matching(
            template_name,
            root_path,
            **partial_tokens,
        )

        if not all_assets:
            return []

        # Group by non-version tokens
        groups: dict[tuple, list[DiscoveredAsset]] = {}

        for asset in all_assets:
            # Create key from all tokens except version
            key_tokens = {
                k: v
                for k, v in asset.parsed_tokens.items()
                if k != self._version_key
            }
            key = tuple(sorted(key_tokens.items()))

            if key not in groups:
                groups[key] = []
            groups[key].append(asset)

        # Find latest in each group
        latest_assets: list[DiscoveredAsset] = []

        for group_assets in groups.values():
            if len(group_assets) == 1:
                latest_assets.append(group_assets[0])
            else:
                # Sort by version and take the last
                if version_token:
                    sorted_assets = sorted(
                        group_assets,
                        key=lambda a: version_token.parse_version(
                            a.version or "0"
                        )
                        if a.version
                        else (0,),
                    )
                else:
                    # Simple string sort
                    sorted_assets = sorted(
                        group_assets, key=lambda a: a.version or ""
                    )
                latest_assets.append(sorted_assets[-1])

        return latest_assets

    def find_by_name(
        self,
        name_token: str,
        name_value: str,
        root_path: str,
        template_names: list[str] | None = None,
    ) -> list[DiscoveredAsset]:
        """Find all assets with a specific name across templates.

        Args:
            name_token: Name of the token containing the asset name.
            name_value: Value to search for.
            root_path: Root directory to search.
            template_names: Optional list of templates to search.
                           If None, searches all registered templates.

        Returns:
            List of discovered assets.
        """

        if template_names is None:
            template_names = self._path_resolver.list_templates()

        all_assets: list[DiscoveredAsset] = []

        for template_name in template_names:
            try:
                assets = self.find_matching(
                    template_name, root_path, **{name_token: name_value}
                )
                all_assets.extend(assets)
            except KeyError:
                continue

        return all_assets

    def count_matching(
        self,
        template_name: str,
        root_path: str,
        **partial_tokens,
    ) -> int:
        """Count files matching template without loading all into memory.

        Args:
            template_name: Name of the template to match.
            root_path: Root directory to search.
            **partial_tokens: Known token values to filter by.

        Returns:
            Number of matching files.
        """

        count = 0
        for _ in self.find_matching_iter(
            template_name, root_path, **partial_tokens
        ):
            count += 1
        return count

    def group_by_token(
        self,
        assets: list[DiscoveredAsset],
        token_key: str,
    ) -> dict[str, list[DiscoveredAsset]]:
        """Group discovered assets by a token value.

        Args:
            assets: List of discovered assets.
            token_key: Token key to group by.

        Returns:
            Dictionary mapping token values to asset lists.
        """

        groups: dict[str, list[DiscoveredAsset]] = {}

        for asset in assets:
            value = asset.parsed_tokens.get(token_key, "__unknown__")
            if value not in groups:
                groups[value] = []
            groups[value].append(asset)

        return groups
