from __future__ import annotations

from tp.common.python import folder


class Rig:

	def __init__(self, name: str | None):
		super().__init__()

		self._name = name
		self._directory = folder.current_working_directory()
