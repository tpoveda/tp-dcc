"""Version token and utilities for version management."""

from __future__ import annotations

import re
from typing import Any

from tp.libs.templating.naming.token import KeyValue, Token


class VersionToken(Token):
    """Special token for version management with auto-increment support.

    This token handles version strings in various formats:
    - Simple numeric: "001", "002", "003"
    - Prefixed: "v001", "v002", "v003"
    - Semantic: "1.0.0", "1.0.1", "1.1.0"

    Example:
        >>> token = VersionToken(name="version", format_str="v{:03d}")
        >>> token.format_version(1)
        'v001'
        >>> token.parse_version("v042")
        42
        >>> token.next_version("v001")
        'v002'
    """

    # Common version patterns
    PATTERN_NUMERIC = re.compile(r"^(\d+)$")
    PATTERN_PREFIXED = re.compile(r"^([a-zA-Z]*)(\d+)$")
    PATTERN_SEMANTIC = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
    PATTERN_SEMANTIC_PREFIXED = re.compile(r"^([a-zA-Z]*)(\d+)\.(\d+)\.(\d+)$")

    def __init__(
        self,
        name: str = "version",
        description: str = "Version number",
        format_str: str = "{:03d}",
        prefix: str = "",
        semantic: bool = False,
        start_version: int = 1,
    ):
        """VersionToken constructor.

        Args:
            name: Token name (default: "version").
            description: Token description.
            format_str: Format string for version numbers (default: "{:03d}" for 001, 002, etc.).
            prefix: Version prefix (default: "" for no prefix, "v" for v001, etc.).
            semantic: If True, use semantic versioning (major.minor.patch).
            start_version: Starting version number (default: 1).
        """

        super().__init__(
            name=name,
            description=description,
            permissions=[],
            key_values=[],
        )

        self._format_str = format_str
        self._prefix = prefix
        self._semantic = semantic
        self._start_version = start_version

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}(name={self._name}, prefix={self._prefix!r}, "
            f"semantic={self._semantic}) object at {hex(id(self))}>"
        )

    @property
    def format_str(self) -> str:
        """Returns the format string for version numbers."""
        return self._format_str

    @property
    def prefix(self) -> str:
        """Returns the version prefix."""
        return self._prefix

    @property
    def semantic(self) -> bool:
        """Returns whether semantic versioning is used."""
        return self._semantic

    @property
    def start_version(self) -> int:
        """Returns the starting version number."""
        return self._start_version

    def format_version(self, version: int | tuple[int, ...]) -> str:
        """Format a version number into a string.

        Args:
            version: Version as integer (for simple) or tuple (for semantic).

        Returns:
            Formatted version string.

        Example:
            >>> token = VersionToken(prefix="v", format_str="{:03d}")
            >>> token.format_version(42)
            'v042'
            >>> semantic_token = VersionToken(semantic=True)
            >>> semantic_token.format_version((1, 2, 3))
            '1.2.3'
        """

        if self._semantic:
            if isinstance(version, int):
                version = (version, 0, 0)
            elif len(version) == 1:
                version = (version[0], 0, 0)
            elif len(version) == 2:
                version = (version[0], version[1], 0)
            return f"{self._prefix}{version[0]}.{version[1]}.{version[2]}"
        else:
            if isinstance(version, tuple):
                version = version[0]
            return f"{self._prefix}{self._format_str.format(version)}"

    def parse_version(self, version_str: str) -> int | tuple[int, ...]:
        """Parse a version string into numeric components.

        Args:
            version_str: Version string to parse.

        Returns:
            Integer for simple versions, tuple for semantic versions.

        Raises:
            ValueError: If version string cannot be parsed.

        Example:
            >>> token = VersionToken(prefix="v")
            >>> token.parse_version("v042")
            42
            >>> semantic_token = VersionToken(semantic=True)
            >>> semantic_token.parse_version("1.2.3")
            (1, 2, 3)
        """

        # Try semantic with prefix
        match = self.PATTERN_SEMANTIC_PREFIXED.match(version_str)
        if match:
            return (
                int(match.group(2)),
                int(match.group(3)),
                int(match.group(4)),
            )

        # Try semantic without prefix
        match = self.PATTERN_SEMANTIC.match(version_str)
        if match:
            return (
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
            )

        # Try prefixed numeric
        match = self.PATTERN_PREFIXED.match(version_str)
        if match:
            return int(match.group(2))

        # Try simple numeric
        match = self.PATTERN_NUMERIC.match(version_str)
        if match:
            return int(match.group(1))

        raise ValueError(f"Cannot parse version string: {version_str!r}")

    def next_version(
        self, current: str | None = None, increment: str = "patch"
    ) -> str:
        """Get the next version string.

        Args:
            current: Current version string. If None, returns start_version.
            increment: For semantic versions, which part to increment ("major", "minor", "patch").

        Returns:
            Next version string.

        Example:
            >>> token = VersionToken(prefix="v", format_str="{:03d}")
            >>> token.next_version("v001")
            'v002'
            >>> token.next_version(None)
            'v001'
            >>> semantic = VersionToken(semantic=True)
            >>> semantic.next_version("1.2.3", increment="minor")
            '1.3.0'
        """

        if current is None:
            if self._semantic:
                return self.format_version((self._start_version, 0, 0))
            return self.format_version(self._start_version)

        parsed = self.parse_version(current)

        if self._semantic:
            if isinstance(parsed, int):
                parsed = (parsed, 0, 0)
            major, minor, patch = parsed

            if increment == "major":
                return self.format_version((major + 1, 0, 0))
            elif increment == "minor":
                return self.format_version((major, minor + 1, 0))
            else:  # patch
                return self.format_version((major, minor, patch + 1))
        else:
            if isinstance(parsed, tuple):
                parsed = parsed[0]
            return self.format_version(parsed + 1)

    def compare(self, v1: str, v2: str) -> int:
        """Compare two version strings.

        Args:
            v1: First version string.
            v2: Second version string.

        Returns:
            -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2.

        Example:
            >>> token = VersionToken()
            >>> token.compare("v001", "v002")
            -1
            >>> token.compare("v002", "v001")
            1
            >>> token.compare("v001", "v001")
            0
        """

        parsed1 = self.parse_version(v1)
        parsed2 = self.parse_version(v2)

        # Normalize to tuples for comparison
        if isinstance(parsed1, int):
            parsed1 = (parsed1,)
        if isinstance(parsed2, int):
            parsed2 = (parsed2,)

        if parsed1 < parsed2:
            return -1
        elif parsed1 > parsed2:
            return 1
        return 0

    def is_valid_version(self, version_str: str) -> bool:
        """Check if a string is a valid version.

        Args:
            version_str: String to check.

        Returns:
            True if valid version string, False otherwise.
        """

        try:
            self.parse_version(version_str)
            return True
        except ValueError:
            return False

    def sort_versions(
        self, versions: list[str], reverse: bool = False
    ) -> list[str]:
        """Sort a list of version strings.

        Args:
            versions: List of version strings to sort.
            reverse: If True, sort in descending order.

        Returns:
            Sorted list of version strings.
        """

        def version_key(v: str):
            parsed = self.parse_version(v)
            if isinstance(parsed, int):
                return (parsed,)
            return parsed

        return sorted(versions, key=version_key, reverse=reverse)
