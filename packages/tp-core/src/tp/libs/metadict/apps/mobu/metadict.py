from __future__ import annotations

import json
from typing import Any

# pyfbsdk is only available within MotionBuilder.
from pyfbsdk import (  # type: ignore[import-not-found]
    FBNote,
    FBProperty,
    FBSystem,
)

from tp.bootstrap.utils import dcc
from tp.libs.metadict import MetadataDictionary


class MobuMetadataDictionary(MetadataDictionary):
    """Metadata dictionary class for MotionBuilder application.

    This implementation stores metadata as a StaticComment property within
    an FBNote node in the MotionBuilder scene.

    Attributes:
        priority: Higher priority ensures MotionBuilder implementation is used when available.
    """

    priority = 2

    @classmethod
    def usable(cls) -> bool:
        """Return whether this MetadataDictionary is usable in MotionBuilder.

        Returns:
            True if running inside MotionBuilder, False otherwise.
        """

        return dcc.is_mobu()

    @staticmethod
    def get_static_comment_property(note: FBNote) -> FBProperty | None:
        """Return the StaticComment property from the given note.

        Args:
            note: FBNote to get the StaticComment property from.

        Returns:
            StaticComment property from the given note, or None if not found.
        """

        for prop in note.PropertyList:
            if prop.Name == "StaticComment":
                return prop
        return None

    def _load_data(self) -> dict[str, Any]:
        """Load raw data from the MotionBuilder scene.

        Returns:
            Dictionary of loaded data.
        """

        note = self._find_note()
        if not note:
            return {}

        try:
            prop = self.get_static_comment_property(note)
            if prop and prop.Data:
                return json.loads(prop.Data)
        except (json.JSONDecodeError, AttributeError):
            # No existing data or invalid JSON.
            pass
        return {}

    def _save_data(self, data: dict[str, Any]) -> None:
        """Save raw data to the MotionBuilder scene.

        Args:
            data: Dictionary data to save.

        Raises:
            ValueError: If the dictionary data cannot be serialized to JSON.
            RuntimeError: If the StaticComment property could not be accessed.
        """

        note = self._find_note()
        if not note:
            note = FBNote(self._note_name)

        prop = self.get_static_comment_property(note)
        if not prop:
            raise RuntimeError(
                f"Could not access StaticComment property on note '{self._note_name}'"
            )

        try:
            prop.Data = json.dumps(data)
        except (TypeError, ValueError) as err:
            raise ValueError(
                f"Could not serialize MetadataDictionary to JSON: {err}. "
                "Ensure all stored data is JSON serializable."
            ) from err

    def delete(self) -> bool:
        """Delete the metadata note from the MotionBuilder scene.

        Returns:
            True if the note was deleted, False if it didn't exist.
        """

        note = self._find_note()
        if note:
            note.FBDelete()
            return True
        return False

    @property
    def _note_name(self) -> str:
        """Return the name of the FBNote used for storing metadata.

        Returns:
            Name of the FBNote.
        """

        return f"tp_metadata_{self.id}"

    def _find_note(self) -> FBNote | None:
        """Find and return the FBNote storing metadata for this dictionary.

        Returns:
            FBNote if found, None otherwise.
        """

        for note in FBSystem().Scene.Notes:
            if note.Name == self._note_name:
                return note
        return None
