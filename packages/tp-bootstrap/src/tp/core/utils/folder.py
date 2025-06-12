from __future__ import annotations

import errno
from pathlib import Path

from loguru import logger


def ensure_folder_exists(
    directory: str, permissions: int | None = None, placeholder: bool = False
) -> bool:
    """Ensure that a given folder exists, optionally setting permissions and
    creating a placeholder file.

    This function checks whether the specified directory exists. If it does
    not, it creates the directory, applies the given permissions (if any),
    and optionally adds a placeholder file to allow detection by version
    control systems that do not track empty folders.

    Args:
        directory: Absolute path of the folder to ensure exists.
        permissions: Unix-style permission bits to set on the created
            directory. Defaults to 0o775 if not provided.
        placeholder: If True, creates a 'placeholder' file in the new
            directory. Useful for ensuring version control systems detect
            the directory.

    Returns:
        True if the directory was created; False if it already existed.

    Raises:
        OSError: If directory creation fails for reasons other than it
        already existing.
    """

    path = Path(directory)
    if path.exists():
        return False

    permissions = permissions or 0o775

    try:
        path.mkdir(parents=True, mode=permissions)
        logger.debug(f"Created directory: {path} with permissions: {oct(permissions)}")

        if placeholder:
            placeholder_path = path / "placeholder"
            if not placeholder_path.exists():
                placeholder_path.write_text(
                    "Automatically generated placeholder file.\n"
                    "This file exists to allow source control systems to "
                    "track this directory.",
                    encoding="utf-8",
                )
                logger.debug(f"Created placeholder file at: {placeholder_path}")
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            logger.error(f"Failed to create directory '{path}': {exc}", exc_info=True)
            raise

    return True
