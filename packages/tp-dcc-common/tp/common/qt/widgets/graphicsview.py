#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different graphic views
"""

import os
import math
import logging

from Qt.QtCore import Qt, Signal, QPoint, QRectF, QLineF
from Qt.QtWidgets import QGraphicsRectItem, QGraphicsView, QGraphicsItem
from Qt.QtGui import QColor, QPen, QBrush, QPainter, QImage, QVector2D

from tpDcc.libs.math.core import scalar

LOGGER = logging.getLogger('tpDcc-libs-qt')

try:
    from Qt import QtOpenGL
except ImportError:
    try:
        from PySide import QtOpenGL
    except ImportError:
        # Max 2018 does not support QtOpenGL?
        LOGGER.warning('QtOpenGL is not available! QtOpenGL functionality will not be available!')


class ViewportModes(object):
    Full = 'full'
    Smart = 'smart'
    Minimal = 'minimal'
    Bounding = 'bounding'


class AutoPanController(object):
    def __init__(self, amount=10.0):
        super(AutoPanController, self).__init__()

        self._enabled = False
        self._amount = amount
        self._auto_pan_delta = QVector2D(0.0, 0.0)
        self._been_outside = False

    def get_amount(self):
        return self._amount

    def set_amount(self, amount):
        self._amount = amount

    def get_auto_pan_delta(self):
        return self._auto_pan_delta

    def get_enabled(self):
        return self._enabled

    amount = property(get_amount, set_amount)
    auto_pan_delta = property(get_auto_pan_delta)
    enabled = property(get_enabled)

    def start(self):
        self._enabled = True

    def update(self, rect, pos):
        if self._enabled:
            if pos.x() < 0:
                self._auto_pan_delta = QVector2D(-self._amount, 0.0)
                self._been_outside = True
                self._amount = scalar.clamp(abs(pos.x()) * 0.3, 0.0, 25.0)
            if pos.x() > rect.width():
                self._auto_pan_delta = QVector2D(self._amount, 0.0)
                self._been_outside = True
                self._amount = scalar.clamp(abs(rect.width() - pos.x()) * 0.3, 0.0, 25.0)
            if pos.y() < 0:
                self._auto_pan_delta = QVector2D(0.0, -self._amount)
                self._been_outside = True
                self._amount = scalar.clamp(abs(pos.y()) * 0.3, 0.0, 25.0)
            if pos.y() > rect.height():
                self._auto_pan_delta = QVector2D(0.0, self._amount)
                self._been_outside = True
                self._amount = scalar.clamp(abs(rect.height() - pos.y()) * 0.3, 0.0, 25.0)
            if self._been_outside and rect.contains(pos):
                self.reset()

    def stop(self):
        self._enabled = False
        self.reset()

    def reset(self):
        self._been_outside = False
        self._auto_pan_delta = QVector2D(0.0, 0.0)


class RubberRect(QGraphicsRectItem, object):

    DEFAULT_RUBBER_RECT_COLOR = QColor(255, 255, 255, 50)

    def __init__(self, name):
        super(RubberRect, self).__init__()
        self._name = name
        self.setZValue(2)
        self.setPen(QPen(self.DEFAULT_RUBBER_RECT_COLOR, 0.5, Qt.SolidLine))
        self.setBrush(QBrush(self.DEFAULT_RUBBER_RECT_COLOR))

    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = name

    name = property(get_name, set_name)


class BaseGraphicsView(QGraphicsView, object):
    """
    QGraphicsView with custom functionality:
        - Zoom in/Zoom out
        - Panning/Auto Panning
        - Custom Rubber Rect Selection
    """

    selectionChanged = Signal()

    def __init__(self, min_scale=0.5, max_scale=2.0, parent=None, **kwargs):
        super(BaseGraphicsView, self).__init__(parent=parent)

        self._min_scale = min_scale
        self._max_scale = max_scale
        self._factor = 1.0
        self._factor_diff = 0.0
        self._scale = 1.0
        self._pan_speed = 1.0
        self._is_panning = False
        self._init_scrollbars_pos = QVector2D(self.horizontalScrollBar().value(), self.verticalScrollBar().value())
        self._is_rubber_rect_selection = False
        self._use_opengl = kwargs.get('use_opengl', False)
        self.log = kwargs.get('log', LOGGER)

        self._mouse_pressed = False
        self._pressed_item = None
        self._released_item = None
        self._mouse_pressed_pos = QPoint(0, 0)
        self._mouse_release_pos = QPoint(0, 0)
        self._mouse_pos = QPoint(0, 0)
        self._last_mouse_pos = QPoint(0, 0)

        self._auto_pan_controller = AutoPanController()
        self._rubber_rect = RubberRect(name='RubberRect')

        self.initialize_scene_view()

        self.setInteractive(True)
        self.setMouseTracking(True)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.TextAntialiasing, True)
        self.setRenderHint(QPainter.HighQualityAntialiasing, True)
        self.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.setRenderHint(QPainter.NonCosmeticDefaultPen, True)
        self.setAttribute(Qt.WA_AlwaysShowToolTips)
        self.setRubberBandSelectionMode(Qt.IntersectsItemShape)

    # region Properties
    def get_viewport_mode(self):
        mode = self.viewportUpdateMode()
        if mode == QGraphicsView.FullViewportUpdate:
            return ViewportModes.Full
        if mode == QGraphicsView.SmartViewportUpdate:
            return ViewportModes.Smart
        if mode == QGraphicsView.MinimalViewport:
            return ViewportModes.Minimal
        if mode == QGraphicsView.BoundingRectViewportUpdate:
            return ViewportModes.Bounding

        return None

    def set_viewport_mode(self, mode):
        if mode == ViewportModes.Full:
            mode = QGraphicsView.FullViewportUpdate
        if mode == ViewportModes.Smart:
            mode = QGraphicsView.SmartViewportUpdate
        if mode == ViewportModes.Minimal:
            mode = QGraphicsView.MinimalViewportUpdate
        if mode == ViewportModes.Bounding:
            mode = QGraphicsView.BoundingRectViewportUpdate

        self.setViewportUpdateMode(mode)
    # endregion

    # region Override Functions
    def mousePressEvent(self, event):
        super(BaseGraphicsView, self).mousePressEvent(event)

        self._pressed_item = self.itemAt(event.pos())
        self._mouse_pressed_pos = event.pos()

        modifiers = event.modifiers()

        if self._pressed_item and isinstance(self._pressed_item, QGraphicsItem):
            self._auto_pan_controller.start()

        if not self._pressed_item:
            if event.button() == Qt.LeftButton:
                self._is_rubber_rect_selection = True
            if event.button() == Qt.RightButton and modifiers == Qt.NoModifier:
                self._is_panning = True
            self._init_scrollbars_pos = QVector2D(self.horizontalScrollBar().value(), self.verticalScrollBar().value())

    def mouseMoveEvent(self, event):
        super(BaseGraphicsView, self).mouseMoveEvent(event)

        self._mouse_pos = event.pos()

        if self._is_panning:
            delta = self.mapToScene(event.pos()) - self.mapToScene(self._last_mouse_pos)
            self._pan(delta)

        if self._rubber_rect and self.scene():
            if self._is_rubber_rect_selection:
                current_pos = self.mapToScene(self._mouse_pos)
                press_pos = self.mapToScene(self._mouse_pressed_pos)
                if self._rubber_rect not in self.scene().items():
                    self.scene().addItem(self._rubber_rect)
                if not self._rubber_rect.isVisible():
                    self._rubber_rect.setVisible(True)
                r = QRectF(
                    press_pos.x(), press_pos.y(), current_pos.x() - press_pos.x(), current_pos.y() - press_pos.y())
                self._rubber_rect.setRect(r.normalized())

        self._auto_pan_controller.update(self.viewport().rect(), event.pos())

        self._last_mouse_pos = event.pos()

    def mouseReleaseEvent(self, event):
        super(BaseGraphicsView, self).mouseReleaseEvent(event)

        self._auto_pan_controller.stop()
        self._mouse_release_pos = event.pos()
        self._released_item = self.itemAt(event.pos())
        self._is_panning = False

        if self._rubber_rect and self.scene():
            if self._is_rubber_rect_selection:
                self._is_rubber_rect_selection = False
                self.setDragMode(QGraphicsView.NoDrag)
                self._select_rubber_rect_items()
                self.remove_item_by_name(self._rubber_rect.name)

    def keyPressEvent(self, event):
        modifiers = event.modifiers()

        # Zoom In
        if all([event.key() == Qt.Key_Equal, modifiers == Qt.ControlModifier]):
            # TODO: Check why is not working
            self.zoom_delta(True)

        # Zoom Out
        if all([event.key() == Qt.Key_Minus, modifiers == Qt.ControlModifier]):
            self.zoom_delta(False)

        # Rest Graph Zoom
        if all([event.key() == Qt.Key_R, modifiers == Qt.ControlModifier]):
            self.reset_scale()

        super(BaseGraphicsView, self).keyPressEvent(event)

    def wheelEvent(self, event):
        self._zoom(math.pow(2.0, event.delta() / 240.0))
    # endregion

    # region Public Functions
    def initialize_scene_view(self):
        """
        Instantiates the proper Scene and enables OpenGL if necessary
        Scene instantiation must be override in child classes
        """

        if self._use_opengl:
            self.setViewport(QtOpenGL.QGLWidget(QtOpenGL.QGLFormat(QtOpenGL.QGL.SampleBuffers)))
            self.log.info('Initializing OpenGL renderer')

    def get_contents_size(self):
        """
        Returns the view contents size (pyshical size)
        :return: tuple, content size
        """

        content_rect = self.contentsRect()
        return (content_rect.width(), content_rect.height())

    def get_center(self):
        """
        Returns the correct center point of the current view
        :return: QPointF, current view center point
        """

        return self.mapToScene(self.viewport().rect().center())

    def set_center(self, pos):
        """
        Sets the current scene center point
        :param pos: tuple, x and y coordinates
        """

        self.centerOn(pos[0], pos[1])

    def get_scene_coordinates(self):
        """
        Returns the scene size
        :return: tuple, coordinates of current scene (-x, -y, x, y)
        """

        if self.scene():
            return self.scene().sceneRect().getCoords()
        return (0, 0, 0, 0)

    def get_translation(self):
        """
        Returns the current scrollbar positions
        :return: tuple, scroll bar coordinates (h, v)
        """

        return [self.horizontalScrollBar().value(), self.verticalScrollBar().value()]

    def get_scale_factor(self):
        """
        Returns the current scale factor
        """

        return [self.transform().m11(), self.transform().m22()]

    def get_scene_attributes(self):
        """
        Returns a dictionary of scene attributes
        :return: dict, view position, scale, size
        """

        scene_attributes = dict()
        scene_attributes.update(view_scale=self.get_scale_factor())
        scene_attributes.update(view_center=self.get_center())
        scene_attributes.update(view_size=self.get_contents_size())
        scene_attributes.update(scene_size=self.get_scene_coordinates())

        return scene_attributes

    def update_scene_attributes(self):
        """
        Updates scene attributes
        """

        scene_attributes = self.get_scene_attributes()
        return scene_attributes

    def remove_item_by_name(self, name):
        """
        Remove graph item by its name (can be any kind of QGraphicsItem)
        :param name: str, name of the item to delete
        """

        if self.scene():
            [self.scene().removeItem(i) for i in self.scene().items() if hasattr(i, 'name') and i.name == name]

    def move_scrollbar(self, delta):
        """
        Move the scrollbar of the view by a given delta
        :param delta: QPointF
        """

        x = self.horizontalScrollBar().value() + delta.x()
        y = self.verticalScrollBar().value() + delta.y()
        self.horizontalScrollBar().setValue(x)
        self.verticalScrollBar().setValue(y)

    def set_scrollbars_positions(self, horizontal, vertical):
        """
        Set the position of the view scrollbars
        :param horizontal: float, position of the horizontal scrollbar
        :param vertical: float, position of the vertical scrollbar
        :return:
        """

        try:
            self.horizontalScrollBar().setValue(horizontal)
            self.verticalScrollBar().setValue(vertical)
        except Exception as e:
            LOGGER.debug(str(e))

    def reset_scale(self):
        self.resetMatrix()

    def zoom_delta(self, direction):
        if direction:
            self._zoom(1 + 0.1)
        else:
            self._zoom(1 - 0.1)

    def fit_scene_content(self):
        """
        Fits scene content to view, by scaling it
        """

        if self.scene():
            scene_rect = self.scene().get_bounding_rect(margin=0)
            self.fitInView(scene_rect, Qt.KeepAspectRatio)
    # endregion

    # region Private Functions
    def _pan(self, delta):
        delta *= self._scale * -1
        delta *= self._pan_speed
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + delta.x())
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() + delta.y())

    def _zoom(self, scale_factor):
        self._factor = round(self.matrix().scale(scale_factor, scale_factor).mapRect(QRectF(0, 0, 1, 1)).width(), 1)

        if hasattr(self.scene(), 'grid_size'):
            if self._factor < (self._min_scale + 0.4):
                self.scene().grid_size = 20
            else:
                self.scene().grid_size = 10

        if self._factor < self._min_scale or self._factor > self._max_scale:
            return
        self.scale(scale_factor, scale_factor)
        self._scale *= scale_factor

    def _select_rubber_rect_items(self):
        self.scene().blockSignals(True)
        items = [i for i in self._rubber_rect.collidingItems()]
        for item in items[:-1]:
            item.setSelected(True)
        self.scene().blockSignals(False)
        if len(items) > 0:
            items[-1].setSelected(True)


class GridView(BaseGraphicsView, object):
    """
    View with grid drawing support
    """

    def __init__(self, parent=None):
        super(GridView, self).__init__(parent=parent)

        self._grid_spacing = 100
        self._grid_size = 10
        self._draw_grid_size = self._grid_size * 2
        self._show_grid = True

        self.setRenderHint(QPainter.Antialiasing)

        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setAttribute(Qt.WA_AlwaysShowToolTips)

    def drawBackground(self, painter, rect):
        super(GridView, self).drawBackground(painter, rect)

        if self._show_grid:
            scene_rect = self.sceneRect()
            left = int(scene_rect.left()) - (int(scene_rect.left()) % self._draw_grid_size)
            top = int(scene_rect.top()) - (int(scene_rect.top()) % self._draw_grid_size)
            scale_mult = 1.0

            lines = list()
            left_line = rect.left() - rect.left() % self._grid_size
            top_line = rect.top() - rect.top() % self._grid_size
            i = int(left_line)
            while i < int(rect.right()):
                lines.append(QLineF(i, rect.top(), i, rect.bottom()))
                i += self._grid_size
            u = int(top_line)
            while u < int(rect.bottom()):
                lines.append(QLineF(rect.left(), u, rect.right(), u))
                u += self._grid_size
            # TODO: Change pen to a class variable (avoid to create a pen each drawing frame)
            pen = QPen()
            pen.setWidth(0)
            pen.setColor(QColor(20, 20, 20))
            painter.setPen(pen)
            painter.drawLines(lines)


class GridBackgroundImageView(GridView, object):
    """
    View with image background drawing support
    """

    def __init__(self, parent=None):
        super(GridBackgroundImageView, self).__init__(parent=parent)

        self._background_image = None
        self._background_image_path = None
        self._fit_image_to_window = False

        self.setBackgroundBrush(QBrush(QColor(70, 70, 70, 255)))

    def get_background_image(self):
        return self._background_image

    def set_background_image(self, value, fit_to_window=False, mirror_x=False, mirror_y=False):
        if not value:
            return
        value = str(value)
        if not (value and os.path.exists(value)):
            print('background image not found: {}'.format(value))
            return

        self._background_image_path = value
        self._fit_image_to_window = fit_to_window

        # Load image and mirror it vertically
        self._background_image = QImage(value).mirrored(mirror_x, mirror_y)

        if not fit_to_window:
            width = self._background_image.width()
            height = self._background_image.height()
            self.scene().set_size(width, height)
            self.fit_scene_content()

    background_image = property(get_background_image, set_background_image)

    # def resizeEvent(self, event):
    # TODO: tpoveda: This is not working when an image is not loaded
    #     if self._fit_image_to_window:
    #         self.scene().set_size(self.rect().width(), self.rect().height())
    #     else:
    #         self.fit_scene_content()
    #     super(GridBackgroundImageView, self).resizeEvent(event)

    def drawBackground(self, painter, rect):
        """
        Override method to draw view custom background image
        """

        if not self.background_image:
            return super(GridBackgroundImageView, self).drawBackground(painter, rect)
        super(GridBackgroundImageView, self).drawBackground(painter, rect)
        painter.drawImage(self.sceneRect(), self.background_image, QRectF(self.background_image.rect()))
