from tp.common.qt import api as qt

from tp.common.qt.widgets import menus


class FacileMenuExample(qt.MainWindow):

	def ui(self):
		super(FacileMenuExample, self).ui()

		facile_menu_bar = menus.FacileMenuBar(parent=self)
		self.main_layout.addWidget(facile_menu_bar)

		file_menu = menus.FacileMenu(parent=self)
		file_menu.addAction('New')

		facile_menu_bar.add_menu('Document')
