from tp.common.qt.widgets.examples import standard, menus


def show_standard_widgets(example_name='main'):
	widgets_window = None
	if example_name.lower() == 'main':
		widgets_window = standard.StandardWidgetsMainWindow()
	elif example_name.lower() == 'editor':
		widgets_window = standard.StandardWidgetsEditorWindow()
	elif example_name.lower() == 'tree':
		widgets_window = standard.StandardWidgetsTreeWindow()
	elif example_name.lower() == 'progress':
		widgets_window = standard.StandardWidgetsProgressWindow()

	if widgets_window:
		widgets_window.show()

	return widgets_window


def show_custom_widgets(custom_name):
	custom_window = None

	if custom_name.lower() == 'facile_menu':
		custom_window = menus.FacileMenuExample()
	if custom_window:
		custom_window.show()

	return custom_window
