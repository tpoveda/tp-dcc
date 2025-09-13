from __future__ import annotations

from tp.libs.qt.mvc import Model, UiProperty


class AssetsModel(Model):
    """Model class that stores all the data for the tool."""

    def __init__(self):
        super().__init__()

    def initialize_properties(self) -> list[UiProperty]:
        """Initialize the properties associated with the instance.

        Returns:
            A list of initialized UI properties.
        """

        return []
