import uuid
import webbrowser

from Qt.QtCore import Qt, Signal, QSize, QTimer
from Qt.QtWidgets import QApplication, QWidget, QFrame, QSizePolicy, QSplitter, QTabWidget, QSpacerItem
from Qt.QtGui import QCursor, QPainter

from tp.core import log, dcc
from tp.common.qt import consts, dpi, qtutils
from tp.common.qt.widgets import layouts, labels, buttons
from tp.common.resources import api as resources
from tp.preferences.interfaces import core as core_interfaces

if dcc.is_maya():
	import maya.cmds as cmds
	from tp.maya.cmds.ui import docking
	from tp.maya.cmds.ui import tooltips

logger = log.tpLogger


class SpawnerIcon(buttons.IconMenuButton):
	"""
	Custom button with a menu that can spawn docked widgets.
	"""

	docked = Signal(object)
	undocked = Signal()

	def __init__(self, window, parent=None):
		super(SpawnerIcon, self).__init__(parent=parent)

		self._docking_container = None
		self._docked = False
		self._start_pos = None
		self._workspace_control = None
		self._workspace_control_name = None
		self._window = window
		self._spawn_enabled = True
		self._init_dock = False

		self.set_logo_highlight(True)
		self._setup_logo_button()

	def mousePressEvent(self, event):
		if self._window.is_docked() or event.button() == Qt.RightButton:
			return

		if event.button() == Qt.LeftButton and self._spawn_enabled:
			self._init_dock = True
			self._start_pos = QCursor.pos()

		if self._tooltip_action:
			if dcc.is_maya():
				self._tooltip_action.setChecked(tooltips.tooltip_state())

	def mouseMoveEvent(self, event):
		if self._window.is_docked():
			return
		square_length = 0
		if self._start_pos:
			square_length = qtutils.get_squared_length(self._start_pos - QCursor.pos())
		if self._init_dock and square_length > 1:
			self._init_dock_container()
			self._init_dock = False
		if self._workspace_control_name is not None:
			self.move_to_mouse()

	def mouseReleaseEvent(self, event):
		if self._window.is_docked():
			return
		if not self._spawn_enabled or self._init_dock:
			super().mouseReleaseEvent(event)
			return
		if event.button() == Qt.RightButton:
			return
		if not self.is_workspace_floating():
			self.dockedEvent()
		else:
			self.delete_control()

	def dockedEvent(self, dock_to_main_window=None):
		if not dcc.is_maya():
			return

		frameless = self._window.parent_container
		self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
		width = self._window.width()
		height = self._window.height()
		if dock_to_main_window:
			cmds.workspaceControl(
				self._workspace_control_name, e=True, dtm=dock_to_main_window, initialWidth=width, initialHeight=height)
		else:
			cmds.workspaceControl(self._workspace_control_name, e=True, initialWidth=width, initialHeight=height)
		self._docking_container.set_widget(self._window)
		self.docked.emit(self._docking_container)
		self._arrange_splitters(width)
		self._docking_container = None
		self._docked = True
		frameless.close()

	def update_theme(self, event):
		"""
		Overrides base update_theme function to ignore it.
		"""

		pass

	def name(self):
		"""
		Returns frameless window name.

		:return: frameless window name.
		:rtype: str

		..note:: this should match frameless window name.
		"""

		return self._window.title or self._window.name or f'Window [{str(uuid.uuid4())[:4]}]'

	def set_logo_highlight(self, flag):
		"""
		Sets whether logo can be highlighted.

		:param bool flag: True to enable icon highlight; False otherwise.
		"""

		min_size = 0.55 if self._window.isMinimized() else 1
		size = consts.Sizes.TITLE_LOGO_ICON * min_size
		if flag:
			self.set_icon('tpdcc', colors=[None, None], size=size, scaling=[1], color_offset=40)
		else:
			self.set_icon(
				'tpdcc', colors=[None], tint_composition=QPainter.CompositionMode_Plus, size=size, scaling=[1],
				color_offset=40, grayscale=True)

	def move_to_mouse(self):
		"""
		Moves window to the mouse location.
		"""

		if not self._docking_container:
			return

		self._docking_container.move_to_mouse()

	def is_dock_locked(self):
		"""
		Returns whether dock functionality is locked.

		:return: True if dock functionality is locked; False otherwise.
		:rtype: bool
		"""

		if not dcc.is_maya():
			return False

		return docking.is_dock_locked()

	def is_workspace_floating(self):
		"""
		Returns whether workspace is floating.

		:return: True if workspace is floating; False otherwise.
		:rtype: bool
		"""

		if not dcc.is_maya() or not self._spawn_enabled:
			return False

		return docking.is_workspace_floating(self._workspace_control_name)

	def delete_control(self):
		"""
		Deletes workspace control.
		"""

		if not dcc.is_maya() or not self._workspace_control_name:
			return

		cmds.deleteUI(self._workspace_control_name)
		self._workspace_control = None
		self._workspace_control_name = None
		self._docking_container = None
		self._docked = False

	def _setup_logo_button(self):
		"""
		Internal function that initializes logo button.
		"""

		size = consts.Sizes.TITLE_LOGO_ICON
		self.setIconSize(QSize(size, size))
		self.setFixedSize(QSize(size + consts.Sizes().MARGIN / 2, size + consts.Sizes.MARGIN / 2))
		if dcc.is_maya():
			self._tooltip_action = self.addAction('Toggle Tooltips', checkable=True, connect=self._on_toggle_tooltips)
		self.menu_align = Qt.AlignLeft

	def _init_dock_container(self):
		"""
		Internal function that initializes dock container for current DCC.
		"""

		if not dcc.is_maya():
			logger.warning('Docking functionality is only available in Maya')
			return

		self._workspace_control_name, self._workspace_control, self._docking_container = docking.dock_to_container(
			workspace_name=self.name(), workspace_width=self._window.width(), workspace_height=self._window.height(),
			workspace_title=self.name(), size=35)

		self.move_to_mouse()

	def _splitter_ancestor(self, widget):
		"""
		Internal function that returns widgets splitter ancestors.

		:param QWidget widget: widget to get splitter ancestors of.
		:return: tuple of splitter ancestors.
		:rtype: tuple
		"""

		if widget is None:
			return None, None
		child = widget
		parent = child.parentWidget()
		if parent is None:
			return None, None
		while parent is not None:
			if isinstance(parent, QSplitter) and parent.orientation() == Qt.Horizontal:
				return child, parent
			child = parent
			parent = parent.parentWidget()

		return None, None

	def _arrange_splitters(self, width):
		"""
		Internal function that fixes splitter sizes, when docked into splitters.

		:param int width: width to set.
		"""

		docking_container = self._docking_container
		child, splitter = self._splitter_ancestor(docking_container)
		if child and isinstance(child, QTabWidget):
			return
		if child and splitter:
			pos = splitter.indexOf(child) + 1
			if pos == splitter.count():
				sizes = splitter.sizes()
				sizes[-2] = (sizes[-2] + sizes[-1]) - width
				sizes[-1] = width
				splitter.setSizes(sizes)
			else:
				splitter.moveSplitter(width, pos)

	def _on_toggle_tooltips(self, tagged_action):
		"""
		Internal callback function that is called when Tooltip action is toggled by the user.

		:param QAction tagged_action: toggled action.
		"""

		if not dcc.is_maya():
			return

		tooltips.set_tooltip_state(tagged_action.isChecked())


class TitleLabel(labels.ClippedLabel):
	"""
	Custom label implementation with elided functionality used for the title bar title
	Used for CSS purposes.
	"""

	def __init__(self, text='', width=0, elide=True, always_show_all=False, parent=None):
		super().__init__(
			text=text, width=width, elide=elide, always_show_all=always_show_all, parent=parent)

		self.setAttribute(Qt.WA_TransparentForMouseEvents)


class TitleBar(QFrame):

	doubleClicked = Signal()
	moving = Signal(object, object)

	class TitleStyle:
		DEFAULT = 'DEFAULT'
		THIN = 'THIN'

	def __init__(self, show_title=True, always_show_all=False, parent=None):
		super().__init__(parent)

		self._title_bar_height = 40
		self._pressed_at = None
		self._window = parent
		self._mouse_pos = None
		self._widget_mouse_pos = None
		self._mouse_press_pos = None
		self._theme_preference = core_interfaces.theme_preference_interface()
		self._toggle = True
		self._icon_size = 13
		self._move_enabled = True
		self._move_threshold = 5

		self._main_layout = layouts.horizontal_layout(parent=self)
		self._left_contents = QFrame(parent=self)
		self._right_contents = QWidget(parent=self)

		self._main_right_layout = layouts.horizontal_layout()
		self._contents_layout = layouts.horizontal_layout()
		self._corner_contents_layout = layouts.horizontal_layout()
		self._title_layout = layouts.horizontal_layout()
		self._title_style = self.TitleStyle.DEFAULT
		self._window_buttons_layout = layouts.horizontal_layout()
		self._split_layout = layouts.horizontal_layout()

		self._logo_button = SpawnerIcon(window=parent, parent=self)
		self._close_button = buttons.BaseButton(theme_updates=False, parent=self)
		self._minimize_button = buttons.BaseButton(theme_updates=False, parent=self)
		self._maximize_button = buttons.BaseButton(theme_updates=False, parent=self)
		self._help_button = buttons.BaseButton(theme_updates=False, parent=self)
		self._title_label = TitleLabel(always_show_all=always_show_all, parent=self)

		if not show_title:
			self._title_label.hide()

		self.setup_ui()
		self.setup_signals()

	@property
	def move_enabled(self):
		return self._move_enabled

	@move_enabled.setter
	def move_enabled(self, flag):
		self._move_enabled = bool(flag)

	@property
	def logo_button(self):
		return self._logo_button

	@property
	def title_label(self):
		return self._title_label

	@property
	def close_button(self):
		return self._close_button

	@property
	def right_contents(self):
		return self._right_contents

	@property
	def left_contents(self):
		return self._left_contents

	@property
	def title_layout(self):
		return self._title_layout

	@property
	def contents_layout(self):
		return self._contents_layout

	@property
	def main_right_layout(self):
		return self._main_right_layout

	@property
	def corner_contents_layout(self):
		return self._corner_contents_layout

	def setup_ui(self):
		"""
		Initializes title UI.
		"""

		self.setFixedHeight(dpi.dpi_scale(self._title_bar_height))
		self.setLayout(self._main_layout)

		color = self._theme_preference.FRAMELESS_TITLE_COLOR
		self._close_button.set_icon(resources.icon(
			'close', theme='window'), colors=color, size=self._icon_size, color_offset=80)
		self._minimize_button.set_icon(resources.icon(
			'minimize', theme='window'), colors=color, size=self._icon_size, color_offset=80)
		self._maximize_button.set_icon(resources.icon(
			'maximize', theme='window'), colors=color, size=self._icon_size, color_offset=80)
		self._help_button.set_icon(resources.icon('question'), colors=color, size=self._icon_size, color_offset=80)

		# Button Setup
		for button in [self._help_button, self._close_button, self._minimize_button, self._maximize_button]:
			button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
			button.double_click_enabled = False

		# Layout setup
		self._main_right_layout.setContentsMargins(*dpi.margins_dpi_scale(0, 5, 6 ,0))
		self._contents_layout.setContentsMargins(0, 0, 0, 0)
		self._corner_contents_layout.setContentsMargins(0, 0, 0, 0)
		self._right_contents.setLayout(self._corner_contents_layout)

		# Window buttons
		self._window_buttons_layout.setContentsMargins(0, 0, 0, 0)
		self._window_buttons_layout.addWidget(self._help_button)
		self._window_buttons_layout.addWidget(self._minimize_button)
		self._window_buttons_layout.addWidget(self._maximize_button)
		self._window_buttons_layout.addWidget(self._close_button)

		# Split Layout
		self._split_layout.addWidget(self._left_contents)
		self._split_layout.addLayout(self._title_layout, 1)
		self._split_layout.addWidget(self._right_contents)

		# Title Layout
		self._left_contents.setLayout(self._contents_layout)
		self._contents_layout.setSpacing(0)
		self._title_layout.addWidget(self._title_label)
		self._title_layout.setSpacing(0)
		self._title_layout.setContentsMargins(*dpi.margins_dpi_scale(0, 8, 0, 7))
		self._title_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
		self._title_label.setMidLineWidth(1)

		# Main Title Layout (Logo and Main Right Layout)
		self._main_layout.setContentsMargins(*dpi.margins_dpi_scale(4, 0, 0, 0))
		self._main_layout.setSpacing(0)
		self._spacing_item = QSpacerItem(8, 8)
		self._spacing_item_2 = QSpacerItem(6, 6)
		self._main_layout.addSpacerItem(self._spacing_item)
		self._main_layout.addWidget(self._logo_button)
		self._main_layout.addSpacerItem(self._spacing_item_2)
		self._main_layout.addLayout(self._main_right_layout)
		self._main_right_layout.addLayout(self._split_layout)
		self._main_right_layout.addLayout(self._window_buttons_layout)
		self._main_right_layout.setAlignment(Qt.AlignVCenter)
		self._window_buttons_layout.setAlignment(Qt.AlignVCenter)
		self._main_right_layout.setStretch(0, 1)

		QTimer.singleShot(0, self.refresh)

		self.set_title_spacing(False)

		if not self._window.HELP_URL:
			self._help_button.hide()

	def mousePressEvent(self, event):
		"""
		Overrides base mousePressEvent function to cache the drag positions.

		:param QEvent event: Qt mouse event.
		"""

		if event.buttons() & Qt.LeftButton:
			self._mouse_press_pos = event.globalPos()
			self.start_move()

		event.ignore()

	def mouseDoubleClickEvent(self, event):
		"""
		Overrides mouseDoubleClickEvent function to maximize/minimize window (if possible).

		:param QEvent event: Qt mouse event.
		"""

		super().mouseDoubleClickEvent(event)
		self.doubleClicked.emit()

	def mouseMoveEvent(self, event):
		"""
		Overrides base mouseMoveEvent function to cache the drag positions.

		:param QEvent event: Qt mouse event.
		"""

		if self._widget_mouse_pos is None or not self._move_enabled:
			return

		moved = event.globalPos() - self._mouse_press_pos
		if moved.manhattanLength() < self._move_threshold:
			return

		pos = QCursor.pos()
		new_pos = pos
		new_pos.setX(pos.x() - self._widget_mouse_pos.x())
		new_pos.setY(pos.y() - self._widget_mouse_pos.y())
		delta = new_pos - self.window().pos()
		self.moving.emit(new_pos, delta)
		self.window().move(new_pos)

	def mouseReleaseEvent(self, event):
		"""
		Overrides base mouseReleaseEvent function to cache the drag positions.

		:param QEvent event: Qt mouse event.
		"""

		if self._mouse_press_pos is not None:
			moved = event.globalPos() - self._mouse_press_pos
			if moved.manhattanLength() > self._move_threshold:
				event.ignore()
			self._mouse_press_pos = None
			self.end_move()

	def start_move(self):
		"""
		Starts the movement of the title bar parent window.
		"""

		if self._move_enabled:
			self._widget_mouse_pos = self._window.mapFromGlobal(QCursor.pos())

	def end_move(self):
		"""
		Ends the movement of the title bar parent window.
		"""

		if self._move_enabled:
			self._widget_mouse_pos = None

	def refresh(self):
		"""
		Refreshes title bar.
		"""

		QApplication.processEvents()
		self.updateGeometry()
		self.update()

	def set_title_text(self, title):
		"""
		Sets the title of the title bar.

		:param str title: title
		"""

		self._title_label.setText(title.upper())

	def set_title_spacing(self, spacing):
		"""
		Set title spacing.

		:param bool spacing: whether spacing should be applied.
		"""

		_spacing = consts.Sizes.INDICATOR_WIDTH * 2
		if spacing:
			self._spacing_item.changeSize(_spacing, _spacing)
			self._spacing_item_2.changeSize(_spacing - 2, _spacing - 2)
		else:
			self._spacing_item.changeSize(0, 0)
			self._spacing_item_2.changeSize(0, 0)
			self._split_layout.setSpacing(0)

	def set_title_align(self, align):
		"""
		Sets title align.

		:param Qt.Align align: alignment.
		"""

		if align == Qt.AlignCenter:
			self._split_layout.setStretch(1, 0)
		else:
			self._split_layout.setStretch(1, 1)

	def title_style(self):
		"""
		Returns title style.

		:return: title style.
		:rtype: int
		"""

		return self._title_style

	def set_title_style(self, style):
		"""
		Sets the title style.

		:param int style: title style.
		"""

		self._title_style = style

		if style == self.TitleStyle.DEFAULT:
			qtutils.set_stylesheet_object_name(self._title_label, '')
			self.setFixedHeight(dpi.dpi_scale(self._title_bar_height))
			self._title_layout.setContentsMargins(*dpi.margins_dpi_scale(0, 5, 0, 7))
			self._main_right_layout.setContentsMargins(*dpi.margins_dpi_scale(0, 5, 6, 0))
			self._logo_button.setIconSize(QSize(24, 24))
			self._logo_button.setFixedSize(QSize(30, 24))
			self._minimize_button.setFixedSize(QSize(28, 24))
			self._minimize_button.setIconSize(QSize(24, 24))
			self._maximize_button.setFixedSize(QSize(28, 24))
			self._maximize_button.setIconSize(QSize(24, 24))
			self._close_button.setFixedSize(QSize(28, 24))
			self._close_button.setIconSize(QSize(16, 16))
			self._window_buttons_layout.setSpacing(6)
			if self._window.HELP_URL:
				self._help_button.show()
			self._window_buttons_layout.setSpacing(dpi.dpi_scale(6))
		elif style == self.TitleStyle.THIN:
			self.setFixedHeight(dpi.dpi_scale(int(self._title_bar_height / 2)))
			self._title_layout.setContentsMargins(*dpi.margins_dpi_scale(0, 3, 15, 7))
			self._main_right_layout.setContentsMargins(*dpi.margins_dpi_scale(0, 0, 6, 0))
			self._logo_button.setIconSize(QSize(12, 12))
			self._logo_button.setFixedSize(QSize(10, 12))
			self._minimize_button.setFixedSize(QSize(10, 18))
			self._maximize_button.setFixedSize(QSize(10, 18))
			self._maximize_button.setFixedSize(QSize(12, 12))
			self._close_button.setFixedSize(QSize(10, 18))
			self._close_button.setFixedSize(QSize(12, 12))
			self._title_label.setFixedHeight(dpi.dpi_scale(20))
			self._window_buttons_layout.setSpacing(dpi.dpi_scale(6))
			self._help_button.hide()
			qtutils.set_stylesheet_object_name(self._title_label, 'Minimized')
		else:
			logger.error('{} style does not exists for {}!'.format(style, self._window.__class__.__name__))

	def set_minimize_button_visible(self, flag):
		"""
		Sets whether dragger shows minimize button or not.

		:param bool flag: True to enable minimize; False otherwise.
		"""

		self._minimize_button.setVisible(flag)

	def set_maximize_button_visible(self, flag):
		"""
		Sets whether dragger shows maximize button or not.

		:param bool flag: True to enable maximize; False otherwise.
		"""

		self._maximize_button.setVisible(flag)

	def close_window(self):
		"""
		Closes title bar parent window.
		"""

		self._window.close()

	def open_help(self):
		"""
		Opens help URL
		"""

		if self._window.HELP_URL:
			webbrowser.open(self._window.HELP_URL)

	def setup_signals(self):
		"""
		Creates title signals.
		"""

		self._close_button.leftClicked.connect(self._on_close_button_clicked)
		self._minimize_button.leftClicked.connect(self._on_minimize_button_clicked)
		self._maximize_button.leftClicked.connect(self._on_maximize_button_clicked)
		self._help_button.leftClicked.connect(self._on_help_button_clicked)

	def _on_close_button_clicked(self):
		"""
		Internal callback function that is called when close button is left-clicked by the user.
		"""

		self.close_window()

	def _on_maximize_button_clicked(self):
		"""
		Internal callback function that is called when maximize button is left-clicked by the user.
		"""

		self._window.maximize()

	def _on_minimize_button_clicked(self):
		"""
		Internal callback function that is called when minimize button is left-clicked by the user.
		"""

		self._window.minimize()

	def _on_help_button_clicked(self):
		"""
		Internal callback function that is called when help button is left-clicked by the user.
		"""

		self.open_help()
