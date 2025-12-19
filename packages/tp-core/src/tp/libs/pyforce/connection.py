from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Connection:
    """Perforce connection information."""

    """Perforce host and port (``P4PORT``)."""
    port: str

    """Helix server username (``P4USER``)."""
    user: str | None = None

    """Client workspace name (``P4CLIENT``)."""
    client: str | None = None
