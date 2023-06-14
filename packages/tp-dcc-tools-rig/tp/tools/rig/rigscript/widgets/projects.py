from __future__ import annotations

from tp.common.qt import api as qt


class ProjectWidget(qt.QWidget):
	def __init__(self, projects_path: str | None = None, parent: qt.QWidget | None = None):
		super().__init__(parent)

		self._projects_path = projects_path
		self._history = None

		self.set_projects_path(projects_path)

	def set_projects_path(self):