from __future__ import annotations

import logging
from typing import Iterator, Any

from ...python import helpers

logger = logging.getLogger(__name__)


class MarkingMenuLayout(dict):
    """
    Class that defines a marking menu layout dictionary.
    """

    def __init__(self, **kwargs):
        kwargs["sortOrder"] = kwargs.get("sortOrder", 0)
        super().__init__(**kwargs)
        self._solved = False

    def __getitem__(self, key: str) -> list | dict | str:
        """
        Returns the value for the given key.

        :param key:
        :return: a dictionary in cases of marking menu regions (N, S, W, ...) being a
            nested after a layout has been solved; a list will be returned for the
            generic  region; a string will be returned when the layout has not been
            solved but  references another layout.
        """

        value = self.get(key)
        return self.get("items", {})[key] if value is None else value

    def __iter__(self) -> Iterator[str, dict]:
        """
        Returns an iterator for the layout.

        :return: iterator for the layout.
        """

        for name, data in iter(self["items"].items()):
            yield name, data

    def items(self) -> Iterator[str, dict]:
        """
        Returns an iterator for the layout. Example:

            {
                "N": {},
                "NW": {},
                "W": {},
                "SW": {},
                "S": {},
                "SE": {},
                "E": {},
                "NE": {},
                "generic": [
                    {
                        "type": "menu",
                        "name": "Testmenu",
                        "children": [{"type": "command", "id": ""}]
                    }
                ]
            }

        :return: iterator for the layout.
        """

        return self.get("items", {}).items()

    def merge(self, layout: MarkingMenuLayout | None = None):
        """
        Merges the given layout into this layout.

        :param layout: layout to merge into this layout.
        """

        helpers.merge_dictionaries(self, layout["items"])

    def validate(self, layout: MarkingMenuLayout | None = None) -> list[Any]:
        """
        Recursively validates the marking menu layout, returning all failed items.
        If an item references another marking menu layout, that layout will be
            validated too.
        :param layout: marking menu layout instance to solve.
        :return: list of failed items.
        """

        # Avoiding circular import by importing the manager here instead of at the top.
        from .manager import MarkingMenusManager

        layout = layout or self
        failed: list[Any] = []
        for item, data in iter(layout["items"].items()):
            if not data:
                continue
            elif isinstance(data, MarkingMenuLayout):
                failed.extend(self.validate(data))
            elif item == "generic":
                failed.extend(self._validate_generic(data))
            elif data.get("type", "") == "command":
                command = MarkingMenusManager().command_factory.get_plugin_by_id(
                    data["id"]
                )
                if not command:
                    failed.append(data)
            else:
                failed.append(data)

        return failed

    def solve(self) -> bool:
        """
        Recursively solves the marking menu layout by expanding any @layout.id
        references, which will compose a single dictionary representing the marking
        menu layout.

        A marking menu layout can contain deeply nested layouts, which is referenced by
        the syntax @layout.id, in the case where there is a reference, then that layout
        will be solved first.

        :return: whether tha layout was solved or not.
        """

        # Avoiding circular import by importing the manager here instead of at the top.
        from .manager import MarkingMenusManager

        manager = MarkingMenusManager()
        solved: bool = False
        for item, data in self.get("items", {}).items():
            if not data:
                continue
            elif item == "generic":
                solved = True
                continue
            elif data["type"] == "layout":
                sub_layout = manager.marking_menu_layouts.get(data["id"])
                if not sub_layout:
                    logger.warning(f"Layout {data['id']} not found! Skipping {data}")
                    continue
                sub_layout.solve()
                self["items"][item] = sub_layout
                solved = True

        self._solved = solved

        return solved

    def _validate_generic(self, data: list[Any]) -> list[Any]:
        """
        Internal function that validates the generic items to ensure that all commands
        are valid within the executor.

        :param data: generic items list from the marking menu layout.
        :return: list of invalid items.
        """

        # Avoiding circular import by importing the manager here instead of at the top.
        from .manager import MarkingMenusManager

        failed: list[Any] = []
        for item in iter(data):
            command_type = item["type"]
            if command_type == "menu":
                failed.extend(self._validate_generic(item["children"]))
            elif command_type == "command":
                command = MarkingMenusManager().command_factory.get_plugin_by_id(
                    item["id"]
                )
                if not command:
                    failed.append(item)
            else:
                failed.append(item)

        return failed
