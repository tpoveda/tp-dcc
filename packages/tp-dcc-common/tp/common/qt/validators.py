from overrides import override
from Qt.QtGui import QValidator


class UpperCaseValidator(QValidator):
	"""
	Custom Qt validator taht keeps the text upper case.
	"""

	@override
	def validate(self, arg__1: str, arg__2: int) -> QValidator.State:
		return QValidator.Acceptable, arg__1.upper(), arg__2
