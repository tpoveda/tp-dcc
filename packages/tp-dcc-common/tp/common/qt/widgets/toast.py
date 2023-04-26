#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains toast widget implementation
"""

from Qt.QtCore import Qt, Signal, QPoint, QSize, QTimer, QPropertyAnimation, QEasingCurve, QAbstractAnimation
from Qt.QtWidgets import QLabel
from Qt.QtGui import QFontMetricsF

from tpDcc import dcc
from tpDcc.managers import resources
from tpDcc.libs.resources.core import theme
from tpDcc.libs.qt.core import base, animation
from tpDcc.libs.qt.widgets import layouts, label, avatar, loading


# @theme.mixin
class BaseToast(base.BaseWidget, object):

    class ToastTypes(object):
        INFO = 'info'
        SUCCESS = 'success'
        WARNING = 'warning'
        ERROR = 'error'
        LOADING = 'loading'

    DEFAULT_CONFIG = {'duration': 2}

    toastClosed = Signal()

    def __init__(self, text, duration=None, toast_type=None, parent=None):
        self._text = text
        self._duration = duration
        self._toast_type = toast_type
        self._parent = parent
        super(BaseToast, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = layouts.VerticalLayout(margins=(0, 0, 0, 0))

        return main_layout

    def ui(self):
        super(BaseToast, self).ui()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WA_TranslucentBackground | Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setFixedSize(QSize(120, 120))

        icon_layout = layouts.HorizontalLayout()
        icon_layout.addStretch()

        widget_theme = self.theme()

        if self._toast_type == self.ToastTypes.LOADING:
            icon_layout.addWidget(loading.CircleLoading(size=widget_theme.huge, color=widget_theme.text_color_inverse))
        else:
            icon_label = avatar.Avatar()
            icon_label.theme_size = 60
            icon_label.image = resources.pixmap(
                self._toast_type or self.ToastTypes.INFO, color=widget_theme.text_color_inverse)
            icon_layout.addWidget(icon_label)
        icon_layout.addStretch()

        content_label = label.BaseLabel()
        content_label.setText(self._text or '')
        content_label.setAlignment(Qt.AlignCenter)

        self.main_layout.addStretch()
        self.main_layout.addLayout(icon_layout)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(content_label)
        self.main_layout.addStretch()

        close_timer = QTimer(self)
        close_timer.setSingleShot(True)
        close_timer.timeout.connect(self.close)
        close_timer.timeout.connect(self.toastClosed.emit)
        close_timer.setInterval((self._duration or self.DEFAULT_CONFIG.get('duration', 2)) * 1000)

        anim_timer = QTimer(self)
        anim_timer.timeout.connect(self._fade_out)
        anim_timer.setInterval((self._duration or self.DEFAULT_CONFIG.get('duration', 2)) * 1000 - 300)

        self._opacity_anim = QPropertyAnimation()
        self._opacity_anim.setTargetObject(self)
        self._opacity_anim.setDuration(300)
        self._opacity_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._opacity_anim.setPropertyName('windowOpacity')
        self._opacity_anim.setStartValue(0.0)
        self._opacity_anim.setEndValue(0.9)

        close_timer.start()
        anim_timer.start()

        self._get_center_position(self._parent)
        self._fade_in()

    @classmethod
    def info(cls, text, parent, duration=None):
        inst = cls(text, duration=duration, toast_type=cls.ToastTypes.INFO, parent=parent)
        inst.show()

        return inst

    @classmethod
    def success(cls, text, parent, duration=None):
        inst = cls(text, duration=duration, toast_type=cls.ToastTypes.SUCCESS, parent=parent)
        inst.show()

        return inst

    @classmethod
    def warning(cls, text, parent, duration=None):
        inst = cls(text, duration=duration, toast_type=cls.ToastTypes.WARNING, parent=parent)
        inst.show()

        return inst

    @classmethod
    def error(cls, text, parent, duration=None):
        inst = cls(text, duration=duration, toast_type=cls.ToastTypes.ERROR, parent=parent)
        inst.show()

        return inst

    @classmethod
    def loading(cls, text, parent, duration=None):
        inst = cls(text, duration=duration, toast_type=cls.ToastTypes.LOADING, parent=parent)
        inst.show()

        return inst

    @classmethod
    def config(cls, duration):
        if duration is not None:
            cls.DEFAULT_CONFIG['duration'] = duration

    def _fade_out(self):
        self._opacity_anim.setDirection(QAbstractAnimation.Backward)
        self._opacity_anim.start()

    def _fade_in(self):
        self._opacity_anim.start()

    def _get_center_position(self, parent):
        parent_parent = parent.parent()
        dcc_win = dcc.main_window()
        if dcc_win:
            dcc_window = parent_parent == dcc_win or parent_parent.objectName() == dcc_win.objectName()
        else:
            dcc_window = None
        parent_geo = parent.geometry()
        pos = parent_geo.topLeft() if dcc_window else parent.mapToGlobal(parent_geo.topLeft())
        offset = 0
        for child in parent.children():
            if isinstance(child, BaseToast) and child.isVisible():
                offset = max(offset, child.y())
        target_x = pos.x() + parent_geo.width() / 2 - self.width() / 2
        target_y = pos.y() + parent_geo.height() / 2 - self.height() / 2
        self.setProperty('pos', QPoint(target_x, target_y))


class ToastWidget(QLabel, object):
    """
    Toast widget used to show quick messages to user
    """

    DEFAULT_DURATION = 500
    DEFAULT_PADDING = 30

    def __init__(self, *args):
        super(ToastWidget, self).__init__(*args)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_fade_out)

        self._duration = self.DEFAULT_DURATION

        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignCenter)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        if self.parent():
            self.parent().installEventFilter(self)

    # def eventFilter(self, obj, event):
    #     """
    #     Overrides base QLabel eventFilter function
    #     Updates the geometry when the parent widget changes size
    #     :param obj: QWidget
    #     :param event: QEvent
    #     """
    #
    #     if event.type() == QEvent.Resize:
    #         self.updateGeometry()
    #     return super(ToastWidget, self).eventFilter(obj, event)

    def updateGeometry(self):
        """
        Overrides base QLabel updateGeometry function
        Updates and aligns the geometry to the parent widget
        """

        padding = self.DEFAULT_PADDING
        widget = self.parent()

        width = self.text_width() + padding
        height = self.text_height() + padding
        x = widget.width() * 0.5 - width * 0.5
        y = (widget.height() - height) / 1.2

        self.setGeometry(x, y, width, height)

    def setText(self, *args, **kwargs):
        """
        Overrides base QLabel setText function
        Updates the size depending on the text width
        :param text: str
        """

        super(ToastWidget, self).setText(*args, **kwargs)
        self.updateGeometry()

    def show(self):
        """
        Overrides base QLabel show function
        Starts the timer to hide the toast
        """

        duration = self.duration()
        self._timer.stop()
        self._timer.start(duration)
        if not self.isVisible():
            animation.fade_in_widget(self, duration=0)
            super(ToastWidget, self).show()

    def duration(self):
        """
        Returns duration
        :return: int
        """

        return self._duration

    def set_duration(self, duration):
        """
        Sets how long to show the toast (in milliseconds)
        :param duration: int
        """

        self._duration = duration

    def text_rect(self):
        """
        Returns the bounding box rect for the text
        :return: QRect
        """

        text = self.text()
        font = self.font()
        metrics = QFontMetricsF(font)

        return metrics.boundingRect(text)

    def text_width(self):
        """
        Returns the width of the text
        :return: int
        """

        text_width = self.text_rect().width()
        return max(0, text_width)

    def text_height(self):
        """
        Returns the height of the text
        :return: int
        """

        text_height = self.text_rect().height()
        return max(0, text_height)

    def _on_fade_out(self, duration=250):
        """
        Internal callback function that fades out the toast message
        :param duration: int
        """

        animation.fade_out_widget(self, duration=duration, on_finished=self.hide)
