#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different graphic scenes
"""

import logging

from Qt.QtCore import Qt, Signal, QPointF, QRectF
from Qt.QtWidgets import QGraphicsScene, QGraphicsLineItem, QGraphicsRectItem
from Qt.QtGui import QPixmap, QColor, QPainter, QPen, QBrush

from tpDcc.libs.python import decorators

LOGGER = logging.getLogger('tpDcc-libs-qt')


class BaseScene(QGraphicsScene, object):
    """
    Base scene for graphics scenes that add support for z index
    """

    scene_changed = Signal()

    _DEFAULT_SCENE_WIDTH = 100
    _DEFAULT_SCENE_HEIGHT = 200

    def __init__(self, auto_z=False, parent=None):
        super(BaseScene, self).__init__(parent=parent)

        self._auto_z = auto_z
        self._z_index = 0
        self._root = None
        self.setParent(parent)

    def get_root(self):
        """
        Returns root scene object
        :return: QSceneObject
        """

        return self._root

    def set_root(self, value):
        """
        Set the root scene object
        :param value: QSceneObject
        """

        self._root = value
        self._root.setParent(self)

    def get_auto_z(self):
        """
        Returns whether auto Z is enabled or not
        :return: bool
        """

        return self._auto_z

    def set_auto_z(self, auto_z):
        """
        Sets whether auto z is enabled or not
        :param auto_z: bool
        """

        self._auto_z = auto_z

    def set_default_size(self):
        """
        Resets the view to its default values
        """

        return self.set_size(self._DEFAULT_SCENE_WIDTH, self._DEFAULT_SCENE_HEIGHT)

    def set_size(self, width, height):
        """
        Sets the size of the scene
        :param width: int, new width of the scene
        :param height: int, new height of the scene
        """

        self.setSceneRect(0, 0, width, height)

    def get_items_by_z_value_order(self, classes_tuple=None, rect=QRectF()):
        """
        Returns the items of the passed class
        :param classes_tuple:
        :param rect:
        :return:
        """

        def cmp_zvalue(x, y):
            x_val = x.zValue()
            y_val = y.zValue()
            if x_val > y_val:
                return 1
            elif x_val < y_val:
                return -1
            else:
                return 0

        if classes_tuple is not None:
            items = filter(lambda x: isinstance(x, classes_tuple), rect.isValid() and self.items(rect) or self.items())
        else:
            items = self.items()
        if items:
            items.sort(key=lambda x: x.zValue())
        return items

    def get_top_item(self):
        """
        Get top Z value item of the scene
        :return:
        """

        items = self.get_items_by_z_value_order()
        if items:
            return items[-1]
        else:
            return None

    def primary_view(self):
        """
        Returns the first view of the scene
        """

        views = self.views()
        if views:
            return views[0]

    def window(self):
        """
        Returns the view window
        """

        view = self.primary_view()
        if view:
            return view.window()
        else:
            return ''

    def clear(self):
        """
        Reset default Z index on clear
        """

        super(BaseScene, self).clear()
        self._z_index = 0

    def addItem(self, item):
        super(BaseScene, self).addItem(item)

        if self._auto_z:
            self._set_z_value(item)

    def _set_z_value(self, control):

        """
        Sets a proper Z idnex for the control
        """

        control.setZValue(self._z_index)
        self._z_index += 1


class GridColors(object):
    """
    Class that stores predefined colors for grids
    """

    BaseColor = QColor(60, 60, 60, 100)
    DarkerColor = QColor(20, 20, 20, 100)


class BackgroundImageScene(BaseScene, object):
    """
    Scene with image background drawing support
    """

    def __init__(self, parent=None):
        super(BackgroundImageScene, self).__init__(parent=parent)

        self._image_path = ''
        self._use_bg_image = True
        self._pixmap = QPixmap()

    @decorators.accepts(QPixmap)
    def get_pixmap(self):
        return self._pixmap

    @decorators.returns(QPixmap)
    def set_pixmap(self, value):
        self._pixmap = value

    @decorators.returns(bool)
    def get_use_bg_image(self):
        return self._use_bg_image

    @decorators.accepts(bool)
    def set_use_bg_image(self, value):
        self._use_bg_image = value
        self.update()

    pixmap = property(get_pixmap, set_pixmap)
    use_bg_image = property(get_use_bg_image, set_use_bg_image)

    def set_background_pixmap(self, pixmap_path):
        """
        Sets the background of the scene
        :param pixmap_path: str, path to the pixmap
        """

        pixmap = QPixmap(pixmap_path)
        if not pixmap.isNull():
            self._image_path = pixmap_path
            self._pixmap = pixmap
        else:
            self._image_path = ''
            self._pixmap = QPixmap()
        self.use_bg_image = True

    def clear_background_image(self):
        """
        Clears the background image
        """

        self._pixmap = QPixmap()
        self._image_path = ''
        self.use_bg_image = False

    def drawBackground(self, painter, rect):
        """
        Override draw background method to write out image as background
        """

        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(rect, self._color)
        painter.setPen(QPen(Qt.black, 0.5, Qt.DashLine))
        painter.setBrush(QColor(67, 255, 163))
        if self._use_bg_image and not self._pixmap.isNull():
            painter.drawPixmap(QPointF(0, 0), self._pixmap)


class GridScene(BaseScene, object):
    """
    Scene with grid background drawing support
    """

    def __init__(self,
                 grid_main_spacing=8,
                 grid_secondary_spacing=8,
                 grid_main_pen_color=GridColors.BaseColor,
                 grid_secondary_pen_color=GridColors.DarkerColor,
                 grid_main_width=1,
                 grid_secondary_width=1,
                 grid_main_style=Qt.SolidLine,
                 grid_secondary_style=Qt.SolidLine,
                 draw_main_grid=True,
                 draw_secondary_grid=True,
                 fit_grid=False,
                 fit_grid_main_divisions=10,
                 fit_grid_secondary_divisions=4,
                 parent=None):
        super(GridScene, self).__init__(parent=parent)

        self._grid_main_pen = QPen()
        self._grid_secondary_pen = QPen()
        self._grid_main_spacing = grid_main_spacing
        self._grid_secondary_spacing = grid_secondary_spacing
        self._grid_main_pen.setColor(grid_main_pen_color)
        self._grid_secondary_pen.setColor(grid_secondary_pen_color)
        self._grid_main_pen.setWidth(grid_main_width)
        self._grid_secondary_pen.setWidth(grid_secondary_width)
        self._grid_main_style = grid_main_style
        self._grid_secondary_style = grid_secondary_style
        self._draw_main_grid = draw_main_grid
        self._draw_secondary_grid = draw_secondary_grid
        self._fit_grid = fit_grid
        self._fit_grid_main_divisions = fit_grid_main_divisions
        self._fit_grid_secondary_divisions = fit_grid_secondary_divisions

        self._grid_main_pen.setStyle(self._grid_main_style)
        self._grid_secondary_pen.setStyle(self._grid_secondary_style)
        self._fit_grid_draw = False

    @decorators.accepts(int)
    def set_grid_main_spacing(self, value):
        """
        Set the size of the main grid (define the gap between grid lines)
        """

        self._grid_main_spacing = value

    @decorators.accepts(int)
    def set_grid_secondary_spacing(self, value):
        """
        Set the size of the secondary grid
        """

        self._grid_secondary_spacing = value

    @decorators.returns(int)
    def get_grid_main_spacing(self):
        """
        Returns the size of the main grid
        :return: int, size of the main grid
        """

        return self._grid_main_spacing

    @decorators.returns(int)
    def get_grid_secondary_spacing(self):
        """
        Returns the size of the secondary grid
        :return: int, size of the secondary grid
        """

        return self._grid_secondary_spacing

    @decorators.accepts(QColor)
    def set_main_pen_color(self, value):
        self._grid_main_pen.setColor(value)

    @decorators.returns(QColor)
    def get_main_pen_color(self):
        return self._grid_main_pen.color()

    @decorators.accepts(QColor)
    def set_secondary_pen_color(self, value):
        self._grid_secondary_pen.setColor(value)

    @decorators.returns(QColor)
    def get_secondary_pen_color(self):
        return self._grid_secondary_pen.color()

    @decorators.accepts(float)
    def set_grid_width(self, value):
        self._grid_main_pen.setWidth(value)
        self._grid_secondary_pen.setWidth(value)

    @decorators.returns(float)
    def get_grid_width(self):
        return self._grid_main_pen.width()

    @decorators.returns(bool)
    def get_draw_main_grid(self):
        return self._draw_main_grid

    @decorators.accepts(bool)
    def set_draw_main_grid(self, draw):
        self._draw_main_grid = draw

    @decorators.returns(bool)
    def get_draw_secondary_grid(self):
        return self._draw_secondary_grid

    @decorators.accepts(bool)
    def set_draw_secondary_grid(self, draw):
        self._draw_secondary_grid = draw

    @decorators.returns(bool)
    def get_fit_grid(self):
        return self._fit_grid

    @decorators.accepts(bool)
    def set_fit_grid(self, fit):
        self._fit_grid = fit

    grid_main_spacing = property(get_grid_main_spacing, set_grid_main_spacing)
    grid_secondary_spacing = property(get_grid_secondary_spacing, set_grid_secondary_spacing)
    grid_main_pen_color = property(get_main_pen_color, set_main_pen_color)
    grid_secondary_pen_color = property(get_secondary_pen_color, set_secondary_pen_color)
    grid_width = property(get_grid_width, set_grid_width)
    draw_main_grid = property(get_draw_main_grid, set_draw_main_grid)
    draw_secondary_grid = property(get_draw_secondary_grid, set_draw_secondary_grid)
    fit_grid = property(get_fit_grid, set_fit_grid)

    # region Override Functions
    def drawBackground(self, painter, rect):
        """
        Draw grid background for the graph scene
        """

        scene_rect = self.sceneRect()
        gradient = QColor(65, 65, 65)
        painter.fillRect(rect.intersected(scene_rect), QBrush(gradient))
        painter.setPen(QPen())
        painter.drawRect(scene_rect)

        if len(self.views()) <= 0:
            LOGGER.error('Scene has not view associated to it!')
            return
        if not self.views()[0]:
            LOGGER.error('View {0} is not valid!'.format(self.views()[0]))
            return
        if hasattr(self.views()[0], 'is_grid_visible'):
            if self.views()[0].is_grid_visible:
                return

        if self._fit_grid:
            if not self._fit_grid_draw:
                if self._draw_main_grid:
                    pos = float(self.width() / self._fit_grid_main_divisions)
                    for div in range(self._fit_grid_main_divisions):
                        if div == 0:
                            continue
                        line = QGraphicsLineItem(0, pos * div, self.width(), pos * div)
                        line.setZValue(-1)
                        line.setPen(self._grid_main_pen)
                        self.addItem(line)
                        line = QGraphicsLineItem(pos * div, 0, pos * div, self.width())
                        line.setZValue(-1)
                        line.setPen(self._grid_main_pen)
                        self.addItem(line)
                    rect = QGraphicsRectItem(self.sceneRect())
                    rect.setZValue(-1)
                    self.addItem(rect)

                if self._draw_secondary_grid:
                    pos = float(self.width() / self._fit_grid_secondary_divisions)
                    for div in range(self._fit_grid_secondary_divisions):
                        if div == 0:
                            continue
                        line = QGraphicsLineItem(0, pos * div, self.width(), pos * div)
                        line.setZValue(-1)
                        line.setPen(self._grid_secondary_pen)
                        self.addItem(line)
                        line = QGraphicsLineItem(pos * div, 0, pos * div, self.width())
                        line.setZValue(-1)
                        line.setPen(self._grid_secondary_pen)
                        self.addItem(line)
                    rect = QGraphicsRectItem(self.sceneRect())
                    rect.setZValue(-1)
                    self.addItem(rect)
                self._fit_grid_draw = True
        else:

            if self._draw_main_grid:
                left = int(self.sceneRect().left()) - (int(self.sceneRect().left()) % self._grid_main_spacing)
                top = int(self.sceneRect().top()) - (int(self.sceneRect().top()) % self._grid_main_spacing)

                painter.setPen(self._grid_main_pen)

                # draw grid vertical lines
                for x in range(left, int(self.sceneRect().right()), self.grid_main_spacing):
                    painter.drawLine(x, self.sceneRect().top(), x, self.sceneRect().bottom())

                # draw grid horizontal lines
                for y in range(top, int(self.sceneRect().bottom()), self.grid_main_spacing):
                    painter.drawLine(self.sceneRect().left(), y, self.sceneRect().right(), y)

            if self._draw_secondary_grid:
                left = int(self.sceneRect().left()) - (int(self.sceneRect().left()) % self._grid_secondary_spacing)
                top = int(self.sceneRect().top()) - (int(self.sceneRect().top()) % self._grid_secondary_spacing)

                painter.setPen(self._grid_secondary_pen)

                # draw grid vertical lines
                for x in range(left, int(self.sceneRect().right()), self.grid_secondary_spacing * 10):
                    painter.drawLine(x, self.sceneRect().top(), x, self.sceneRect().bottom())

                # draw grid horizontal lines
                for y in range(top, int(self.sceneRect().bottom()), self.grid_secondary_spacing * 10):
                    painter.drawLine(self.sceneRect().left(), y, self.sceneRect().right(), y)
    # endregion


class DropEditableScene(GridScene, object):
    def __init__(self, parent=None):
        super(DropEditableScene, self).__init__(parent=parent)

        self._editable = True

    @decorators.returns(bool)
    def get_editable(self):
        return self._editable

    @decorators.accepts(bool)
    def set_editable(self, value):
        self._editable = value
        self.update()

    def get_bounding_rect(self, margin=0):
        """
        Return scene content bounding box with specified margin
        """

        if self._editable:
            return self.sceneRect()
        scene_rect = self.itemsBoundingRect()
        if not margin:
            return scene_rect
        scene_rect.setX(scene_rect.x() - margin)
        scene_rect.setY(scene_rect.y() - margin)
        scene_rect.setWidth(scene_rect.width() + margin)
        scene_rect.setHeight(scene_rect.height() + margin)
        return scene_rect
