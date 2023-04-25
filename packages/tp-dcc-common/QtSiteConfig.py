def update_misplaced_members(members):
	"""
	Called by Qt.py at run-time to modify the modules it makes available.
	:param dict members: The members considered by Qt.py
	"""

	# PySide
	members['PySide']['QtCore.QStandardPaths'] = 'QtCore.QStandardPaths'
	members['PySide']['QtGui.QEnterEvent'] = 'QtGui.QEnterEvent'
	members['PySide']['QtGui.QExposeEvent'] = 'QtGui.QExposeEvent'

	# PySide2
	members['PySide2']['QtCore.QStandardPaths'] = 'QtCore.QStandardPaths'
	members['PySide2']['QtGui.QEnterEvent'] = 'QtGui.QEnterEvent'
	members['PySide2']['QtGui.QExposeEvent'] = 'QtGui.QExposeEvent'

	# PyQt4
	members['PyQt4']['QtCore.QStandardPaths'] = 'QtCore.QStandardPaths'
	members['PyQt4']['QtGui.QEnterEvent'] = 'QtGui.QEnterEvent'
	members['PyQt4']['QtGui.QExposeEvent'] = 'QtGui.QExposeEvent'

	# PyQt5
	members['PyQt5']['QtCore.QStandardPaths'] = 'QtCore.QStandardPaths'
	members['PyQt5']['QtGui.QEnterEvent'] = 'QtGui.QEnterEvent'
	members['PyQt5']['QtGui.QExposeEvent'] = 'QtGui.QExposeEvent'
