from typing import Type

from Qt.QtCore import Qt
from Qt.QtWidgets import QApplication


def cursor_mixin(cls):
	"""
	Mixin class that allows to change widget cursor.

	:param Type cls: mixed class
	"""

	old_enter_event = cls.enterEvent
	old_leave_event = cls.leaveEvent

	def _new_enter_event(self, *args, **kwargs):
		old_enter_event(self, *args, **kwargs)
		self.__dict__.update({'__tpdcc_enter': True})
		QApplication.setOverrideCursor(Qt.PointingHandCursor if self.isEnabled() else Qt.ForbiddenCursor)

		return super(cls, self).enterEvent(*args, **kwargs)

	def _new_leave_event(self, *args, **kwargs):
		old_leave_event(self, *args, **kwargs)
		if self.__dict__.get('__tpdcc_enter', False):
			QApplication.restoreOverrideCursor()
			self.__dict__.update({'__tpdcc_enter': False})

		return super(cls, self).leaveEvent(*args, **kwargs)

	def _new_hide_event(self, *args, **kwargs):
		old_leave_event(self, *args, **kwargs)
		if self.__dict__.get('__tpdcc_enter', False):
			QApplication.restoreOverrideCursor()
			self.__dict__.update({'__tpdcc_enter': False})

		return super(cls, self).hideEvent(*args, **kwargs)

	setattr(cls, 'enterEvent', _new_enter_event)
	setattr(cls, 'leaveEvent', _new_leave_event)
	setattr(cls, 'hideEvent', _new_hide_event)

	return cls
