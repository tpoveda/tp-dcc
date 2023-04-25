import os

from Qt.QtWidgets import QMessageBox, QFileDialog


_current_user_directory = os.path.expanduser('~')


def set_dir(file):
	global _current_user_directory
	if os.path.isdir(file):
		_current_user_directory = file
	elif os.path.isfile(file):
		_current_user_directory = os.path.split(file)[0]


def message_dialog(text='', title='Message'):
	dlg = QMessageBox()
	dlg.setWindowTitle(title)
	dlg.setInformativeText(text)
	dlg.setStandardButtons(QMessageBox.Ok)
	return dlg.exec()


def question_dialog(text='', title='Are you sure?'):
	dlg = QMessageBox()
	dlg.setWindowTitle(title)
	dlg.setInformativeText(text)
	dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
	result = dlg.exec()
	return bool(result == QMessageBox.Yes)


def get_save_filename(parent=None, title='Save File', file_dir=None, ext_filter='*'):
	if not file_dir:
		file_dir = _current_user_directory
	file_dlg = QFileDialog.getSaveFileName(parent, title, file_dir, ext_filter)
	file = file_dlg[0] or None
	if file:
		set_dir(file)
	return file_dlg


def get_open_filename(parent=None, title='Open File', file_dir=None, ext_filter='*'):
	if not file_dir:
		file_dir = _current_user_directory
	file_dlg = QFileDialog.getOpenFileName(parent, title, file_dir, ext_filter)
	file = file_dlg[0] or None
	if file:
		set_dir(file)
	return file_dlg
