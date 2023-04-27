from Qt.QtCore import Qt, Signal, QObject, QPoint, QSize
from Qt.QtWidgets import QApplication, QWidget, QToolButton, QGridLayout, QMainWindow, QGraphicsDropShadowEffect
from Qt.QtGui import QCursor, QColor, QPainter

from tp.core import log, dcc
from tp.common.python import osplatform
from tp.common.qt import dpi, qtutils
from tp.common.qt.widgets import layouts, overlay
from tp.common.resources.core import icon

if dcc.is_maya():
	import maya.cmds as cmds
	from maya.app.general import mayaMixin

logger = log.tpLogger


class ContainerType(object):

	DOCKING = 1
	FRAMELESS_WINDOW = 2


class ContainerWidget(object):
	"""
	Abstract class used by custom container widgets.

	This class should never be instantiated directly.
	"""

	def is_docking_container(self):
		"""
		Returns whether current instance is a docking container widget.

		:return: True if current instance is a DockingContainer instance; False otherwise.
		:rtype: bool
		"""

		return isinstance(self, DockingContainer)

	def is_frameless_window(self):
		"""
		Returns whether current instance is a frameless window widget.

		:return: True if current instance is a FramelessWindow instance; False otherwise.
		:rtype: bool
		"""

		return isinstance(self, FramelessWindow)

	def get_container_type(self):
		"""
		Returns the type of container.

		:return: type container.
		:rtype: int
		"""

		return ContainerType.FRAMELESS_WINDOW if self.is_frameless_window() else ContainerType.DOCKING

	def set_widget(self, widget):
		"""
		Sets container widget.

		:param QWidget widget: container widget.
		"""

		self.setObjectName(widget.objectName())


class DockableMixin:
	pass


if dcc.is_maya():
	DockableMixin = mayaMixin.MayaQWidgetDockableMixin


class DockingContainer(DockableMixin, QWidget, ContainerWidget):
	"""
	Custom widget container that can be docked withing DCCs
	"""

	def __init__(self, parent=None, workspace_control_name=None, *args, **kwargs):
		super(DockingContainer, self).__init__(parent=parent, *args, **kwargs)

		self._prev_floating = True
		self._widget_flags = None
		self._detaching = False
		self._workspace_control = parent
		self._workspace_control_name = workspace_control_name
		self._detach_counter = 0
		self._logo_icon = QToolButton(parent=self)
		self._container_size = self.size()

		self._setup_ui()

	def enterEvent(self, event):
		"""
		Overrides base QWidget enterEvent function.

		:param QEvent event: Qt enter event event.
		"""

		if self._detaching:
			self.undock()

	def resizeEvent(self, event):
		"""
		Overrides base QWidget resizeEvent function.

		:param QEvent event: Qt resize event.
		"""

		if not self._detaching and not self.isFloating():
			self._container_size = self.size()

		return super().resizeEvent(event)

	def showEvent(self, event):
		"""
		Overrides base QWidget showEvent function.

		:param QEvent event: Qt show event.
		"""

		if not self.isFloating():
			self._logo_icon.hide()
		if not self._prev_floating and self.isFloating():
			self._detaching = True
		self._prev_floating = self.isFloating()

	def moveEvent(self, event):
		"""
		Overrides base QWidget moveEvent function.

		:param QEvent event: Qt move event.
		"""

		if not self._detaching:
			return

		self._detach_counter += 1
		new_size = QSize(self._container_size.width(), self._orig_widget_size.height())
		self.setFixedSize(new_size)
		if self._detach_counter == 2:
			self.undock()

	def set_widget(self, widget):
		"""
		Overrides base FramelessWindow set_widget function.

		:param QWidget widget: window central widget.
		"""

		self._main_widget = widget
		self._orig_widget_size = QSize(self._main_widget.size())
		self.layout().addWidget(widget)
		super(DockingContainer, self).set_widget(widget)
		self.setMinimumWidth(0)
		self.setMinimumHeight(0)

	def move_to_mouse(self):
		"""
		Moves current dock widget into current mouse cursor position.
		"""

		pos = QCursor.pos()
		window = self._win
		if self._win == dcc.get_main_window() and self._win is not None:
			logger.error('{}: Found Maya window instead of DockingContainer!'.format(
				self._workspace_control_name))
			return
		offset = qtutils.get_window_offset(window)
		half = qtutils.get_widget_center(window)
		pos += offset - half
		window.move(pos)
		window.setWindowOpacity(0.8)

	def undock(self):
		"""
		Undocks container widget.
		"""

		self._detach_counter = 0
		self._detaching = False

		if self.isFloating():
			frameless = self._main_widget.attach_to_frameless_window(save_window_pref=False)
			pos = self.mapToGlobal(QPoint())
			width = self._container_size.width()
			frameless.show()
			frameless.setGeometry(pos.x(), pos.y(), width, self._orig_widget_size.height())
			self._main_widget.title_bar.logo_button.delete_control()
			self._main_widget.undocked.emit()
			self._workspace_control = None

	def delete_control(self):
		"""
		Deletes workspace control.
		"""

		if not dcc.is_maya():
			return

		cmds.deleteUI(self._workspace_control_name)

	def _setup_ui(self):
		"""
		Internal function that initializes docking widget UI.
		"""

		size = 24
		ui_layout = layouts.vertical_layout(margins=(0, 0, 0, 0))
		ui_layout.addWidget(self._logo_icon)
		self.setLayout(ui_layout)
		self._logo_icon.setIcon(icon.colorize_icon('tpdcc', size=size))
		self._logo_icon.setIconSize(dpi.size_by_dpi(QSize(size, size)))
		self._logo_icon.clicked.connect(self.close)
		self._win = self.window()


class FramelessWindow(QMainWindow, ContainerWidget):
	"""
	Frameless window implementation.
	"""

	closed = Signal()

	def __init__(self, width=None, height=None, save_window_pref=True, on_top=False, parent=None):

		self._on_top = on_top
		if dcc.is_blender():
			self._on_top = True

		super().__init__(parent=parent)

		if osplatform.is_mac():
			# macOs needs it the saveWindowPref all the time otherwise it will be behind the other windows.
			self.save_window_pref()
			qtutils.single_shot_timer(lambda: self._setup_size(width, height))
		else:
			if save_window_pref:
				self.save_window_pref()
			self._setup_size(width, height)

		self._shadow_effect = None
		self._default_window_flags = self.windowFlags()

		self._setup_ui()

	def closeEvent(self, event):
		super(FramelessWindow, self).closeEvent(event)

		self.closed.emit()

	def set_widget(self, widget):
		"""
		Overrides base FramelessWindow set_widget function.

		:param QWidget widget: window central widget.
		"""

		self.setCentralWidget(widget)
		self.set_shadow_effect_enabled(True)

		if not osplatform.is_mac():
			self._set_new_object_name(widget)

	def set_shadow_effect_enabled(self, flag):
		"""
		Sets whether frameless window shadow effect is enabled.

		:param bool flag: True to enable shadow effect; False otherwise.
		"""

		if flag:
			self._shadow_effect = QGraphicsDropShadowEffect(self)
			self._shadow_effect.setBlurRadius(dpi.dpi_scale(8))
			self._shadow_effect.setColor(QColor(0, 0, 0, 150))
			self._shadow_effect.setOffset(dpi.dpi_scale(2))
			self.setGraphicsEffect(self._shadow_effect)
		else:
			self.setGraphicsEffect(None)
			self._shadow_effect = None

	def set_transparency(self, flag):
		"""
		Sets whether window transparency effect is enabled.

		:param bool flag: True to enable window transparency effect; False otherwise.
		"""

		if flag:
			self.window().setAutoFillBackground(False)
		else:
			self.window().setAttribute(Qt.WA_NoSystemBackground, False)

		self.window().setAttribute(Qt.WA_TranslucentBackground, flag)
		self.window().repaint()

	def save_window_pref(self):
		"""
		Function that forces the window to automatically be parented to DCC main window and also to force the saving
		of the window size and position.

		..note:: this functionality is only supported in Maya
		"""

		if not dcc.is_maya():
			return

		self.setProperty('saveWindowPref', True)

	def _setup_size(self, width, height):
		"""
		Internal function that initializes frameless window size.

		:param int width: initial width in pixels.
		:param int height: initial height in pixels.
		"""

		if not (width is None and height is None):
			if width is None:
				width = dpi.dpi_scale(self.size().width())
			elif height is None:
				height = dpi.dpi_scale(self.size().height())

			self.resize(width, height)

	def _setup_ui(self):
		"""
		Internal function that initializes frameless window UI.
		:return:
		"""

		self.setAttribute(Qt.WA_TranslucentBackground)
		if qtutils.is_pyside2() or qtutils.is_pyqt5():
			window_flags = self.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint
		else:
			window_flags = self.windowFlags() | Qt.FramelessWindowHint
		if self._on_top:
			window_flags = window_flags | Qt.WindowStaysOnTopHint
		self._default_window_flags = window_flags ^ Qt.WindowMinMaxButtonsHint
		self.setWindowFlags(self._default_window_flags)
		self.layout().setContentsMargins(0, 0, 0, 0)

	def _set_new_object_name(self, widget):
		"""
		Internal function that updates this instance object name based on the given widget.

		:param QWidget widget: frameless window central widget.
		"""

		self.setObjectName(widget.objectName() + 'Frameless')


class FramelessOverlay(overlay.OverlayWidget):

	MOVED_BUTTON = Qt.MiddleButton
	RESIZE_BUTTON = Qt.RightButton

	def __init__(
			self, parent, title_bar, top_left=None, top_right=None, bottom_left=None, bottom_right=None, resizable=True):
		super().__init__(parent=parent)

		self._pressed_at = None
		self._resize_direction = 0
		self._resizable = resizable
		self._title_bar = title_bar
		self._top_left = top_left
		self._top_right = top_right
		self._bottom_left = bottom_left
		self._bottom_right = bottom_right

	@classmethod
	def is_modifier(cls):
		modifiers = QApplication.keyboardModifiers()
		return modifiers == Qt.AltModifier

	# =================================================================================================================
	# OVERRIDES
	# =================================================================================================================

	def mousePressEvent(self, event):
		"""
		Overrides base QWidget mousePressEvent function.
		Alt + Middle click to move window.

		:param QEvent event: Qt mouse press event.
		"""

		self._pressed_at = QCursor.pos()
		if not self.isEnabled():
			event.ignore()
			super().mousePressEvent(event)
			return

		if self.is_modifier() and event.buttons() & self.MOVED_BUTTON:
			self._title_bar.start_move()
			self.setCursor(Qt.CursorShape.ClosedHandCursor)
		if self.is_modifier() and event.buttons() & self.RESIZE_BUTTON and self._resizable:
			self._resize_direction = self._get_quadrant()
			if self._resize_direction == ResizerDirection.Top | ResizerDirection.Right:
				self._top_right.window_resize_start()
				self.setCurosr(Qt.CursorShape.SizeBDiagCursor)
			elif self._resize_direction == ResizerDirection.Top | ResizerDirection.Left:
				self._top_left.window_resize_start()
				self.setCurosr(Qt.CursorShape.SizeFDiagCursor)
			elif self._resize_direction == ResizerDirection.Bottom | ResizerDirection.Left:
				self._bottom_left.window_resize_start()
				self.setCurosr(Qt.CursorShape.SizeBDiagCursor)
			elif self._resize_direction == ResizerDirection.Bottom | ResizerDirection.Right:
				self._bottom_right.window_resize_start()
				self.setCurosr(Qt.CursorShape.SizeFDiagCursor)

		if (not self.is_modifier() and event.buttons() & self.MOVED_BUTTON) or \
				(not self.is_modifier() and event.buttons() & self.RESIZE_BUTTON):
			self.hide()

		event.ignore()
		return super().mousePressEvent(event)

	def mouseMoveEvent(self, event):
		if not self.isEnabled():
			event.ignore()
			super().mouseMoveEvent(event)
			return

		if not self.is_modifier():
			self.hide()
			return

		self._title_bar.mouseMoveEvent(event)

		if self._resize_direction != 0:
			if self._resize_direction == ResizerDirection.Top | ResizerDirection.Right:
				self._top_right.windowResized.emit()
			elif self._resize_direction == ResizerDirection.Top | ResizerDirection.Left:
				self._top_left.windowResized.emit()
			elif self._resize_direction == ResizerDirection.Bottom | ResizerDirection.Left:
				self._bottom_left.windowResized.emit()
			elif self._resize_direction == ResizerDirection.Bottom | ResizerDirection.Right:
				self._bottom_right.windowResized.emit()

		event.ignore()

		super().mouseMoveEvent(event)

	def mouseReleaseEvent(self, event):
		if not self.isEnabled():
			event.ignore()
			super().mouseReleaseEvent(event)
			return

		self._title_bar.end_move()
		self._top_left.resizedFinished.emit()
		self._top_right.resizedFinished.emit()
		self._bottom_left.resizedFinished()
		self._bottom_right.resizedFinished()
		self._resize_direction = 0
		event.ignore()

		if self._pressed_at - QCursor.pos() == QPoint(0, 0):
			qtutils.click_under(QCursor.pos(), 1, modifier=Qt.AltModifier)

		super().mouseReleaseEvent(event)

	def setEnabled(self, enabled):
		self.set_debug_mode(not enabled)
		self.setVisible(enabled)
		super().setEnabled(enabled)

	def show(self):
		self.update_stylesheet()
		if self.isEnabled():
			super().show()
		else:
			logger.warning('FramelessOverlay.show() was called when it is disabled')

	def update_stylesheet(self):
		"""
		Updates style sheet.
		"""

		self.set_debug_mode(self._debug)

	def _get_quadrant(self):
		"""
		Internal function that returns the quadrant of where the mouse is located and returns the resizer direction.

		:return: resizer direction.
		:rtype: ResizerDirection
		"""

		mid_x = self.geometry().width() / 2
		mid_y = self.geometry().height() / 2
		result = 0

		pos = self.mapFromGlobal(QCursor.pos())

		if pos.x() < mid_x:
			result = result | ResizerDirection.Left
		elif pos.x() > mid_x:
			result = result | ResizerDirection.Right

		if pos.y() < mid_y:
			result = result | ResizerDirection.Top
		elif pos.y() > mid_y:
			result = result | ResizerDirection.Bottom

		return result


class ResizerDirection:
	"""
	Class that defines all the available resize directions
	"""

	Left = 1
	Top = 2
	Right = 4
	Bottom = 8


class Resizers:
	"""
	Class that defines all the different resizer types
	"""

	Vertical = 1
	Horizontal = 2
	Corners = 4
	All = Vertical | Horizontal | Corners


class WindowResizer(QObject):

	resizeFinished = Signal()

	def __init__(self, parent, install_to_layout=None):
		super().__init__(parent=parent)

		self._frameless_parent = parent
		self._layout = None
		self._is_visible = True

		self._install_to_layout(install_to_layout, parent)
		self._setup_signals()

	@property
	def top_left_resizer(self):
		return self._top_left_resizer

	@property
	def top_right_resizer(self):
		return self._top_right_resizer

	@property
	def bottom_left_resizer(self):
		return self._bottom_left_resizer

	@property
	def bottom_right_resizer(self):
		return self._bottom_right_resizer

	def show(self):
		"""
		Shows the resizers.
		"""

		self._is_visible = True
		for resizer in self._resizers:
			resizer.show()

	def hide(self):
		"""
		Hides the resizers.
		"""

		self._is_visible = False
		for resizer in self._resizers:
			resizer.hide()

	def is_visible(self):
		"""
		Returns whether resizers are visible.

		:return: True if resizers are visible; False otherwise.
		:rtype: bool
		"""

		return self._is_visible

	def resizer_height(self):
		"""
		Calculates the total height of the resizers.

		:return: resizer height.
		:rtype: int
		"""

		resizers = [self._top_resizer, self._bottom_resizer]
		result = 0
		for r in resizers:
			if not r.isHidden():
				result += r.minimumSize().height()

		return result

	def resizer_width(self):
		"""
		Calculates the total widht of the resizers.

		:return: resizer width.
		:rtype: int
		"""

		resizers = [self._left_resizer, self._right_resizer]
		ret = 0
		for r in resizers:
			if not r.isHidden():
				ret += r.minimumSize().width()

		return ret

	def set_resize_directions(self):
		"""
		Sets the resize directions for the window resizer widgets.
		"""

		self._top_resizer.set_resize_direction(ResizerDirection.Top)
		self._bottom_resizer.set_resize_direction(ResizerDirection.Bottom)
		self._right_resizer.set_resize_direction(ResizerDirection.Right)
		self._left_resizer.set_resize_direction(ResizerDirection.Left)
		self._top_left_resizer.set_resize_direction(ResizerDirection.Left | ResizerDirection.Top)
		self._top_right_resizer.set_resize_direction(ResizerDirection.Right | ResizerDirection.Top)
		self._bottom_left_resizer.set_resize_direction(ResizerDirection.Left | ResizerDirection.Bottom)
		self._bottom_right_resizer.set_resize_direction(ResizerDirection.Right | ResizerDirection.Bottom)

	def set_resizer_active(self, flag):
		"""
		Sets whether resizers are active.

		:param bool flag: True to activate resizers; False otherwise.
		"""

		self.show() if flag else self.hide()

	def set_enabled(self, flag):
		"""
		Sets whether resizers are enabled.

		:param bool flag: True to enable resizers; False otherwise.
		"""

		[resizer.setEnabled(flag) for resizer in self._resizers]

	def _install_to_layout(self, grid_layout, parent):
		"""
		Internal function that install resizers into the given grid layout.

		:param QGridLayout layout: grid layout to install resizers into.
		"""

		if not isinstance(grid_layout, QGridLayout):
			logger.error('Resizers only can be installed on grid layouts (QGridLayout)!')
			return

		self._layout = grid_layout

		self._top_resizer = VerticalResizer(ResizerDirection.Top, parent=parent)
		self._bottom_resizer = VerticalResizer(ResizerDirection.Bottom, parent=parent)
		self._right_resizer = HorizontalResizer(ResizerDirection.Right, parent=parent)
		self._left_resizer = HorizontalResizer(ResizerDirection.Left, parent=parent)
		self._top_left_resizer = CornerResizer(ResizerDirection.Left | ResizerDirection.Top, parent=parent)
		self._top_right_resizer = CornerResizer(ResizerDirection.Right | ResizerDirection.Top, parent=parent)
		self._bottom_left_resizer = CornerResizer(ResizerDirection.Left | ResizerDirection.Bottom, parent=parent)
		self._bottom_right_resizer = CornerResizer(ResizerDirection.Right | ResizerDirection.Bottom, parent=parent)

		self._resizers = [
			self._top_resizer, self._top_right_resizer, self._right_resizer, self._bottom_right_resizer,
			self._bottom_resizer, self._bottom_left_resizer, self._left_resizer, self._top_left_resizer
		]

		grid_layout.addWidget(self._top_left_resizer, 0, 0, 1, 1)
		grid_layout.addWidget(self._top_resizer, 0, 1, 1, 1)
		grid_layout.addWidget(self._top_right_resizer, 0, 2, 1, 1)
		grid_layout.addWidget(self._left_resizer, 1, 0, 2, 1)
		grid_layout.addWidget(self._right_resizer, 1, 2, 2, 1)
		grid_layout.addWidget(self._bottom_left_resizer, 3, 0, 1, 1)
		grid_layout.addWidget(self._bottom_resizer, 3, 1, 1, 1)
		grid_layout.addWidget(self._bottom_right_resizer, 3, 2, 1, 1)

		self.set_resize_directions()

	def _setup_signals(self):
		"""
		Internal function that setup resizer signals.
		"""

		for resizer in self._resizers:
			resizer.windowResizedFinished.connect(self.resizeFinished.emit)


class Resizer(QWidget):
	"""
	Base class that defines resizer widget functionality
	Those resizers can be used in windows and dialogs
	"""

	windowResized = Signal()                  # signal emitted when a resize operation is being done
	windowResizedStarted = Signal()           # signal emitted when a resize operation starts
	windowResizedFinished = Signal()          # signal emitted when a resize operation ends

	def __init__(self, direction, parent, debug=False):
		super().__init__(parent)

		self._direction = direction         # resize direction
		self._widget_mouse_pos = None       # caches the position of the mouse
		self._widget_geometry = None        # caches the geometry of the resized widget

		if not debug:
			self.setStyleSheet('background-color: transparent;')
		else:
			self.setStyleSheet('background-color: #88990000')

		self.set_resize_direction(direction)

		# # make sure that resizers are invisible
		# self.setAttribute(Qt.WA_TranslucentBackground)

		self.windowResized.connect(self._on_window_resized)
		self.windowResizedStarted.connect(self._on_window_resize_started)

	def paintEvent(self, event):
		"""
		Overrides base QFrame paintEvent function
		Override to make mouse events work in transparent widgets.

		:param QPaintEvente event: Qt paint event
		"""

		painter = QPainter(self)
		painter.fillRect(self.rect(), QColor(255, 0, 0, 0))
		painter.end()

	def mousePressEvent(self, event):
		"""
		Overrides base QFrame mousePressEvent function

		:param QEvent event: Qt mouse event
		"""

		self.windowResizedStarted.emit()

	def mouseMoveEvent(self, event):
		"""
		Overrides base QFrame mouseMoveEvent function

		:param QEvent event: Qt mouse event
		"""

		self.windowResized.emit()

	def mouseReleaseEvent(self, event):
		"""
		Overrides base QFrame mouseReleaseEvent function

		:param QEvent event: Qt mouse event
		"""

		self.windowResizedFinished.emit()

	def set_resize_direction(self, direction):
		"""
		Sets the resize direction

		.. code-block:: python
			setResizeDirection(ResizeDirection.Left | ResizeDireciton.Top)

		:param ResizerDirection direction: resize direction.
		:return: resizer direction
		:rtype: int
		"""

		self._direction = direction

	def window_resize_start(self):
		"""
		Start resize operation.
		"""

		self._widget_mouse_pos = self.mapFromGlobal(QCursor.pos())
		self._widget_geometry = self.window().frameGeometry()

	def _on_window_resized(self):
		"""
		Internal function that resizes the frame based on the mouse position and the current direction
		"""

		pos = QCursor.pos()
		new_geo = self.window().frameGeometry()

		min_width = self.window().minimumSize().width()
		min_height = self.window().minimumSize().height()

		if self._direction & ResizerDirection.Left == ResizerDirection.Left:
			left = new_geo.left()
			new_geo.setLeft(pos.x() - self._widget_mouse_pos.x())
			if new_geo.width() <= min_width:
				new_geo.setLeft(left)
		if self._direction & ResizerDirection.Top == ResizerDirection.Top:
			top = new_geo.top()
			new_geo.setTop(pos.y() - self._widget_mouse_pos.y())
			if new_geo.height() <= min_height:
				new_geo.setTop(top)
		if self._direction & ResizerDirection.Right == ResizerDirection.Right:
			new_geo.setRight(pos.x() + (self.minimumSize().width() - self._widget_mouse_pos.x()))
		if self._direction & ResizerDirection.Bottom == ResizerDirection.Bottom:
			new_geo.setBottom(pos.y() + (self.minimumSize().height() - self._widget_mouse_pos.y()))

		x = new_geo.x()
		y = new_geo.y()
		w = max(new_geo.width(), min_width)
		h = max(new_geo.height(), min_height)

		self.window().setGeometry(x, y, w, h)

	def _on_window_resize_started(self):
		"""
		Internal callback function that is called when resize operation starts
		"""

		self.window_resize_start()


class CornerResizer(Resizer, object):
	"""
	Resizer implementation for window corners
	"""

	def __init__(self, direction, parent=None):
		super().__init__(direction=direction, parent=parent)

		self.setFixedSize(dpi.size_by_dpi(QSize(10, 10)))

	def set_resize_direction(self, direction):
		super().set_resize_direction(direction)


		if direction == ResizerDirection.Left | ResizerDirection.Top or \
				direction == ResizerDirection.Right | ResizerDirection.Bottom:
			self.setCursor(Qt.SizeFDiagCursor)
		elif direction == ResizerDirection.Right | ResizerDirection.Top or \
				direction == ResizerDirection.Left | ResizerDirection.Bottom:
			self.setCursor(Qt.SizeBDiagCursor)


class VerticalResizer(Resizer, object):
	"""
	Resizer implementation for top and bottom sides of the window
	"""

	def __init__(self, direction=Qt.SizeVerCursor, parent=None):
		super().__init__(direction=direction, parent=parent)

		self.setFixedHeight(dpi.dpi_scale(8))

	def set_resize_direction(self, direction):
		super().set_resize_direction(direction)

		self.setCursor(Qt.SizeVerCursor)


class HorizontalResizer(Resizer, object):
	"""
	Resizer implementation for left and right sides of the window
	"""

	def __init__(self, direction=Qt.SizeHorCursor, parent=None):
		super().__init__(direction=direction, parent=parent)

		self.setFixedHeight(dpi.dpi_scale(8))

	def set_resize_direction(self, direction):
		super().set_resize_direction(direction)

		self.setCursor(Qt.SizeHorCursor)
