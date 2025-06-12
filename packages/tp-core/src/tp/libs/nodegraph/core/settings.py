from __future__ import annotations


from ...python import paths, settings


class NodeGraphSettings(settings.JsonSettings):
    """
    Class that defines node graph settings.
    """

    def __init__(self):
        super().__init__(paths.canonical_path("../settings.json"))

    @property
    def node_title_font(self) -> tuple[str, int]:
        """
        Getter method that returns the node title font and size.

        :return: str
        """

        return self.get("node_title_font", ("Roboto", 10))
