from __future__ import annotations

import sys
import weakref
import traceback
from typing import Any
from loguru import logger
from dataclasses import dataclass
from abc import ABC, abstractmethod

from Qt.QtCore import Signal, QObject
from Qt.QtWidgets import QWidget

from tp.libs.plugin import Plugin, PluginExecutionStats


@dataclass
class ModRigToolUiData:
    label: str = ""
    icon: str = "tpdcc"
    icon_color: tuple[int, int, int] = (192, 192, 192)
    icon_color_toggled: tuple[int, int, int] = (192, 192, 192)
    tooltip: str = ""


class ModRigToolSignals(QObject):
    refreshRequested = Signal(bool)


class ModRigTool(Plugin, ABC):
    id: str = ""
    creator: str = ""
    ui_data = ModRigToolUiData()

    def __init__(self):
        super().__init__()

        self._view: weakref.ReferenceType[QWidget] | None = None
        self._signals = ModRigToolSignals()

    @property
    def view(self) -> QWidget | None:
        """The view this tool is associated with, if any."""

        return self._view() if self._view else None

    @view.setter
    def view(self, widget: QWidget | None):
        """Sets the view this tool is associated with.

        Args:
            widget: The widget to set as the view.
        """

        self._view = weakref.ref(widget) if widget else None

    # noinspection PyMethodMayBeStatic
    def variants(self) -> list[dict[str, Any]]:
        """Returns the list of variants available for this tool.

        Returns:
            A list of tool variants available for this tool.
        """

        return []

    def variant_by_id(self, variant_id: str | None) -> dict[str, Any]:
        """Returns the variant dictionary for the given variant ID.

        Args:
            variant_id: The ID of the variant to retrieve.

        Returns:
            The variant dictionary if found; `None` otherwise.
        """

        if not variant_id:
            return {}

        try:
            ret = [x for x in self.variants() if x["id"] == variant_id][0]
        except:
            raise Exception(f"VariantID: '{variant_id}' not found for '{self.id}'")

        return ret

    def process(
        self, variant_id: str | None = None, args: dict[str, Any] | None = None
    ) -> Any:
        args = args or {}
        stats = PluginExecutionStats(self)
        exc_type, exc_value, exc_tb = None, None, None

        try:
            stats.start()
            logger.debug(f"Executing tool: {self.id} ...")
            variant = self.variant_by_id(variant_id)
            if variant:
                execution_args = variant["args"]
                execution_args.update(args)
                return self.execute(**execution_args)
            return self.execute(**args)
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            stats.finish(traceback.format_exception(exc_type, exc_value, exc_tb))
            raise
        finally:
            if not exc_type:
                stats.finish()
            logger.debug(
                f"Finished executing tool: {self.id}, "
                f"execution time: {stats.execution_time}"
            )

    @abstractmethod
    def execute(self, **kwargs: dict[str, Any]):
        """Executes the tool logic.

        Args:
            **kwargs: Arbitrary keyword arguments.
        """

        pass

    # noinspection PyPep8Naming
    @property
    def refreshRequested(self) -> Signal:
        """The signal emitted when a refresh is requested."""

        return self._signals.refreshRequested

    def request_refresh(self, force: bool = False):
        """Request a refresh, so UIs can be updated.

        Args:
            force: Whether to force the refresh even if not needed.
        """

        logger.debug(f"Tool {self.id} requested a refresh (force={force})")
        self._signals.refreshRequested.emit(force)
