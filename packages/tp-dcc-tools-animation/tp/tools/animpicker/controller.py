from __future__ import annotations

from tp.core import log
from tp.common.qt import api as qt

logger = log.modelLogger


class AnimPickerController(qt.QObject):

	def __init__(self):
		super().__init__()
