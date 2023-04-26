#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes to create different kind of labels
"""

from Qt.QtCore import Qt, Signal, Property, QRect, QSize, QPropertyAnimation
from Qt.QtWidgets import QSizePolicy, QLabel, QLineEdit, QStyle, QStyleOption
from Qt.QtGui import QFontMetrics, QTextCursor, QTextDocument, QPainter, QMouseEvent

from tp.core.managers import resources
from tp.common.qt import consts, qtutils, dpi
from tp.common.qt.widgets import menus, graphicseffects
# from tp.common.resources import theme


def label(text='', tooltip='', upper=False, bold=False, elide=False, parent=None):
    """
    Creates a new label widget.

    :param str text: label text.
    :param str tooltip: label tooltip.
    :param bool upper: whether label text is forced to be uppercase.
    :param bool bold: whether label font is bold.
    :param QWidget parent: parent widget.
    :return: new label widget instance.
    :rtype: BaseLabel
    """

    new_label = BaseLabel(text=text, tooltip=tooltip, bold=bold, upper=upper, parent=parent)

    return new_label


def icon_label(
        pixmap, colors=None, size=None, description='', state=False, pixmap_category=None, theme=None, parent=None):
    """
    Custom QLabel implementation to create square icon buttons as labels.

    :param str pixmap: name of the resource file without the extension.
    :param tuple(QColor, QColor) colors: a tuple of QColors for enabled and disabled states.
    :param int size: value for width and height.
    :param str description: optional user readable description of the action the button performs.
    :param bool state: whether the button is clicked by default.
    :param QWidget parent: parent widget.
    """

    colors = colors or (consts.Colors.SECONDARY_TEXT, consts.Colors.SECONDARY_TEXT)
    size = size if size is not None else consts.Sizes.MARGIN

    new_label = ClickableIconLabel(
        pixmap=pixmap, colors=colors, size=size, description=description, state=state,
        pixmap_category=pixmap_category, theme=theme, parent=parent)

    return new_label


def clipped_label(text='', width=0, ellipsis=True, always_show_all=False, parent=None):
    """
    Custom QLabel that clips itself if the widget width is smaller than the text.

    :param str text: label text.
    :param int width: minimum width.
    :param bool ellipsis: whether label will have ellipsis.
    :param bool always_show_all: force the label to show the complete text or hide the complete text.
    :param QWidget parent: parent widget.
    """

    new_label = ClippedLabel(text=text, width=width, ellipsis=ellipsis, always_show_all=always_show_all, parent=parent)
    return new_label


def h1_label(text='', tooltip='', upper=False, bold=False, parent=False):
    """
    Creates a new H1label widget.

    :param str text: label text.
    :param str tooltip: label tooltip.
    :param bool upper: whether label text is forced to be uppercase.
    :param bool bold: whether label font is bold.
    :param QWidget parent: parent widget.
    :return: new label widget instance.
    :rtype: BaseLabel
    """

    new_label = label(text=text, tooltip=tooltip, upper=upper, bold=bold, parent=parent).h1()

    return new_label


def h2_label(text='', tooltip='', upper=False, bold=False, parent=False):
    """
    Creates a new H2 label widget.

    :param str text: label text.
    :param str tooltip: label tooltip.
    :param bool upper: whether label text is forced to be uppercase.
    :param bool bold: whether label font is bold.
    :param QWidget parent: parent widget.
    :return: new label widget instance.
    :rtype: BaseLabel
    """

    new_label = label(text=text, tooltip=tooltip, upper=upper, bold=bold, parent=parent).h2()

    return new_label


def h3_label(text='', tooltip='', upper=False, bold=False, parent=False):
    """
    Creates a new H3 label widget.

    :param str text: label text.
    :param str tooltip: label tooltip.
    :param bool upper: whether label text is forced to be uppercase.
    :param bool bold: whether label font is bold.
    :param QWidget parent: parent widget.
    :return: new label widget instance.
    :rtype: BaseLabel
    """

    new_label = label(text=text, tooltip=tooltip, upper=upper, bold=bold, parent=parent).h3()

    return new_label


def h4_label(text='', tooltip='', upper=False, bold=False, parent=False):
    """
    Creates a new H4 label widget.

    :param str text: label text.
    :param str tooltip: label tooltip.
    :param bool upper: whether label text is forced to be uppercase.
    :param bool bold: whether label font is bold.
    :param QWidget parent: parent widget.
    :return: new label widget instance.
    :rtype: BaseLabel
    """

    new_label = label(text=text, tooltip=tooltip, upper=upper, bold=bold, parent=parent).h4()

    return new_label


def h5_label(text='', tooltip='', upper=False, bold=False, parent=False):
    """
    Creates a new H5 label widget.

    :param str text: label text.
    :param str tooltip: label tooltip.
    :param bool upper: whether label text is forced to be uppercase.
    :param bool bold: whether label font is bold.
    :param QWidget parent: parent widget.
    :return: new label widget instance.
    :rtype: BaseLabel
    """

    new_label = label(text=text, tooltip=tooltip, upper=upper, bold=bold, parent=parent).h5()

    return new_label


# @theme.mixin
@menus.mixin
class BaseLabel(QLabel, dpi.DPIScaling):
    """
    Custom QLabel implementation that extends standard Qt QLabel class
    """

    clicked = Signal()
    leftClicked = Signal()
    middleClicked = Signal()
    rightClicked = Signal()

    class Levels(object):
        """
        Class that defines different label header levels
        """

        H1 = 1          # header 1
        H2 = 2          # header 2
        H3 = 3          # header 3
        H4 = 4          # header 4
        H5 = 5          # header 5

    class Types(object):
        """
        Class that defines different label types
        """

        SECONDARY = 'secondary'
        WARNING = 'warning'
        DANGER = 'danger'

    def __init__(self, text='', tooltip='', upper=False, bold=False, enable_menu=True, menu_vertical_offset=20,
                 parent=None):

        text = text.upper() if upper else text
        self._enable_menu = enable_menu
        self._actual_text = text

        super(BaseLabel, self).__init__(text, parent)

        self._type = ''
        self._level = 0
        self._underline = False
        self._mark = False
        self._delete = False
        self._strong = False
        self._code = False
        self._elide_mode = Qt.ElideNone

        self.setToolTip(tooltip)
        self.setTextInteractionFlags(Qt.TextBrowserInteraction | Qt.LinksAccessibleByMouse)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.strong(bold)

        if self._enable_menu:
            self._setup_menu_class

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    def _get_type(self):
        """
        Internal Qt property function that returns label type.

        :return: label type.
        :rtype: BaseLabel.Types
        """

        return self._type

    def _set_type(self, value):
        """
        Internal Qt property function that sets label type.

        :param BaseLabel.Types value: label type.
        """

        self._type = value
        self.style().polish(self)

    def _get_level(self):
        """
        Internal Qt property function that returns label level.

        :return: label level.
        :rtype: str
        """

        return self._level

    def _set_level(self, value):
        """
        Internal Qt property function that sets label level.

        :param str value: label level.
        """

        self._level = value
        self.style().polish(self)

    def _get_underline(self):
        """
        Internal Qt property function that returns whether or not label is using an underline style.

        :return: True if labael has underline style; False otherwise.
        :rtype: bool
        """

        return self._underline

    def _set_underline(self, flag):
        """
        Internal Qt property function that sets label to use an underline style.

        :param bool flag: underline flag.
        """

        self._underline = flag
        self.style().polish(self)

    def _get_delete(self):
        """
        Internal Qt property function that returns whether or not label is using a delete style.

        :return: True if the label has a delete style; False otherwise.
        :rtype: bool
        """

        return self._delete

    def _set_delete(self, flag):
        """
         Internal Qt property function that sets label to use a delete style.

         :param bool flag: delete flag
         """

        self._delete = flag
        self.style().polish(self)

    def _get_strong(self):
        """
        Internal Qt property function that returns whether or not label is using a strong style.

        :return: True if the label has a strong style; False otherwise.
        :type: bool
        """

        return self._strong

    def _set_strong(self, flag):
        """
         Internal Qt property function that sets label to use a strong style.

         :param bool flag: strong flag.
         """

        self._strong = flag
        self.style().polish(self)

    def _get_mark(self):
        """
        Internal Qt property function that returns whether or not label is using a mark style.

        :return: True if the label has a mark style; False otherwise.
        :rtype: bool
        """

        return self._mark

    def _set_mark(self, flag):
        """
         Internal Qt property function that sets label to use a mark style.

         :param bool flag: mark flag.
         """

        self._mark = flag
        self.style().polish(self)

    def _get_code(self):
        """
        Internal Qt property function that returns whether or not label is using a code style.

        :return: True if the label has a code style; False otherwise.
        :rtype: bool
        """

        return self._code

    def _set_code(self, flag):
        """
        Internal Qt property function that sets label to use a code style.

        :param bool flag: code flag.
        """

        self._code = flag
        self.style().polish(self)

    def _get_elide_mode(self):
        """
        Internal Qt property function that returns which elide mode label is using.

        :return: label elide mode.
        :rtype: Qt.ElideLeft or Qt.ElideMiddle or Qt.ElideRight or Qt.ElideNone
        """

        return self._elide_mode

    def _set_elide_mode(self, value):
        """
        Internal Qt property function that sets elide mode used by the label.


        :param Qt.ElideLeft or Qt.ElideMiddle or Qt.ElideRight or Qt.ElideNone value: elide mode.
        """

        self._elide_mode = value
        self._update_elided_text()

    theme_type = Property(str, _get_type, _set_type)
    theme_level = Property(int, _get_level, _set_level)
    theme_underline = Property(bool, _get_underline, _set_underline)
    theme_delete = Property(bool, _get_delete, _set_delete)
    theme_mark = Property(bool, _get_mark, _set_mark)
    theme_strong = Property(bool, _get_strong, _set_strong)
    theme_code = Property(bool, _get_code, _set_code)
    theme_elide_mode = Property(bool, _get_elide_mode, _set_elide_mode)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def mousePressEvent(self, event):
        """
        Overrides mousePressEvent function to emit clicked signal each time user clicks on the label.

        :param QEvent event: Qt mouse event.
        """

        self.clicked.emit()
        super(BaseLabel, self).mousePressEvent(event)

    # in some scenarios this scales down the text a lot (for example, when adding
    # a label within a tree widget item).
    # def minimumSizeHint(self):
    #     """
    #      Overrides base QObject minimumSizeHint function
    #      :return: QSize
    #      """
    #
    #     return QSize(1, self.fontMetrics().height())

    def resizeEvent(self, event):
        """
        Overrides base QObject resizeEvent function
        """

        self._update_elided_text()

    def text(self):
        """
        Overrides base QLabel text function
        :return: str
        """

        return self._actual_text

    def setText(self, text):
        """
        Overrides base QLabel setText function
        :return: str
        """

        self._actual_text = text
        self._update_elided_text()
        self.setToolTip(text)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def h1(self):
        """
        Sets label with h1 type.
        """

        self.theme_level = self.Levels.H1

        return self

    def h2(self):
        """
        Sets label with h2 type.
        """

        self.theme_level = self.Levels.H2

        return self

    def h3(self):
        """
        Sets label with h3 type.
        """

        self.theme_level = self.Levels.H3

        return self

    def h4(self):
        """
        Sets label with h4 type.
        """

        self.theme_level = self.Levels.H4

        return self

    def h5(self):
        """
        Sets label with h4 type.
        """

        self.theme_level = self.Levels.H5

        return self

    def secondary(self):
        """
        Sets label with secondary type.
        """

        self.theme_type = self.Types.SECONDARY

        return self

    def warning(self):
        """
        Sets label with warning type.
        """

        self.theme_type = self.Types.WARNING

        return self

    def danger(self):
        """
        Sets label with danger type.
        """

        self.theme_type = self.Types.DANGER

        return self

    def strong(self, flag=True):
        """
        Sets label with strong type.

        :param bool flag: whether or not enable strong mode.
        """

        self.theme_strong = flag

        return self

    def mark(self, flag=True):
        """
        Sets label with mark type.

        :param bool flag: whether or not enable mar mode.
        """

        self.theme_mark = flag

        return self

    def code(self, flag=True):
        """
        Sets label with code type.

        :param bool flag: whether or not enable code mode.
        """

        self.theme_code = flag

        return self

    def delete(self, flag=True):
        """
        Sets label with delete type.

        :param bool flag: whether or not enable delete mode.
        """

        self.theme_delete = flag

        return self

    def underline(self, flag=True):
        """
        Sets label with underline type.

        :param bool flag: whether or not enable underline mode.
        """

        self.theme_underline = flag

        return self

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _update_elided_text(self):
        """
        Internal function that updates the elided text on the label
        """

        font_metrics = self.fontMetrics()
        elided_text = font_metrics.elidedText(self._actual_text, self._elide_mode, self.width() - 2 * 2)
        super(BaseLabel, self).setText(elided_text)


class DragDropLine(QLineEdit, object):
    """
    QLineEdit that supports drag and drop behaviour
    """

    def __init__(self, parent=None):
        super(DragDropLine, self).__init__(parent)

        self.setDragEnabled(True)
        self.setReadOnly(True)

    def dragEnterEvent(self, event):
        """
        Overrides QWidget dragEnterEvent to enable drop behaviour with file
        :param event: QDragEnterEvent
        :return:
        """
        data = event.mimeData()
        urls = data.urls()
        if (urls and urls[0].scheme() == 'file'):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if (urls and urls[0].scheme() == 'file'):
            event.acceptProposedAction()

    def dropEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if (urls and urls[0].scheme() == 'file'):
            self.setText(urls[0].toLocalFile())


class ClickLabel(QLabel, object):
    """
    This label emits a clicked signal when the user clicks on it
    """

    clicked = Signal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super(ClickLabel, self).mousePressEvent(event)


class RightElidedLabel(BaseLabel, object):
    """
    Custom label which supports elide right
    """

    def __init__(self, *args, **kwargs):
        super(RightElidedLabel, self).__init__(*args, **kwargs)
        self._text = self.text()

    def setText(self, text):
        """
        Overrides base QLabel setText function
        Used to store original text
        :param text: str
        """

        self._text = text
        super(RightElidedLabel, self).setText(text)

    def resizeEvent(self, event):
        """
        Overrides base QLabel resizeEvent function
        Modifies the text with elided text
        :param event: QResizeEvent
        """

        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self._text, Qt.ElideRight, self.width())
        super(RightElidedLabel, self).setText(elided)


class ElidedLabel(BaseLabel, object):
    """
    This label elides text and adds ellipses if the text does not fit
    properly withing the widget frame
    """

    def __init__(self, text='', parent=None):
        super(ElidedLabel, self).__init__(parent=parent)

        self._elide_mode = Qt.ElideRight
        self._actual_text = ""
        self._line_width = 0
        self._ideal_width = None

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.setText(text)

    def sizeHint(self):

        base_size_hint = super(ElidedLabel, self).sizeHint()
        return QSize(self._get_width_hint(), base_size_hint.height())

    def _get_width_hint(self):

        if not self._ideal_width:

            doc = QTextDocument()
            try:
                # add the extra space to buffer the width a bit
                doc.setHtml(self._actual_text + "&nbsp;")
                doc.setDefaultFont(self.font())
                width = doc.idealWidth()
            except Exception:
                width = self.width()
            finally:
                qtutils.safe_delete_later(doc)

            self._ideal_width = width

        return self._ideal_width

    def _get_elide_mode(self):
        """
        Returns current elide mode
        """

        return self._elide_mode

    def _set_elide_mode(self, value):
        """
        Set the current elide mode.
        """

        if value != Qt.ElideLeft and value != Qt.ElideRight:
            raise ValueError("elide_mode must be set to either QtCore.Qt.ElideLeft or QtCore.Qt.ElideRight")
        self._elide_mode = value
        self._update_elided_text()

    elide_mode = property(_get_elide_mode, _set_elide_mode)

    def text(self):
        """
        Overridden base method to return the original unmodified text
        """
        return self._actual_text

    def setText(self, text):
        """
        Overridden base method to set the text on the label
        """
        # clear out the ideal width so that the widget can recalculate based on
        # the new text
        self._ideal_width = None
        self._actual_text = text
        self._update_elided_text()

        # if we're elided, make the tooltip show the full text
        if super(ElidedLabel, self).text() != self._actual_text:
            # wrap the actual text in a paragraph so that it wraps nicely
            self.setToolTip("<p>%s</p>" % (self._actual_text,))
        else:
            self.setToolTip("")

    def resizeEvent(self, event):
        """
        Overridden base method called when the widget is resized.
        """

        self._update_elided_text()

    def _update_elided_text(self):
        """
        Update the elided text on the label
        """

        text = self._elide_text(self._actual_text, self._elide_mode)
        QLabel.setText(self, text)

    def _elide_text(self, text, elide_mode):
        """
        Elide the specified text using the specified mode
        :param text:        The text to elide
        :param elide_mode:  The elide mode to use
        :returns:           The elided text.
        """

        # target width is the label width:
        target_width = self.width()

        # Use a QTextDocument to measure html/richtext width
        doc = QTextDocument()
        try:
            doc.setHtml(text)
            doc.setDefaultFont(self.font())

            # if line width is already less than the target width then great!
            line_width = doc.idealWidth()
            if line_width <= target_width:
                self._line_width = line_width
                return text

            # depending on the elide mode, insert ellipses in the correct place
            cursor = QTextCursor(doc)
            ellipses = ""
            if elide_mode != Qt.ElideNone:
                # add the ellipses in the correct place:
                ellipses = "..."
                if elide_mode == Qt.ElideLeft:
                    cursor.setPosition(0)
                elif elide_mode == Qt.ElideRight:
                    char_count = doc.characterCount()
                    cursor.setPosition(char_count - 1)
                cursor.insertText(ellipses)
            ellipses_len = len(ellipses)

            # remove characters until the text fits within the target width:
            while line_width > target_width:

                start_line_width = line_width

                # if string is less than the ellipses length then just return
                # an empty string
                char_count = doc.characterCount()
                if char_count <= ellipses_len:
                    self._line_width = 0
                    return ""

                # calculate the number of characters to remove - should always remove at least 1
                # to be sure the text gets shorter!
                line_width = doc.idealWidth()
                p = target_width / line_width
                # play it safe and remove a couple less than the calculated amount
                chars_to_delete = max(1, char_count - int(float(char_count) * p) - 2)

                # remove the characters:
                if elide_mode == Qt.ElideLeft:
                    start = ellipses_len
                    end = chars_to_delete + ellipses_len
                else:
                    # default is to elide right
                    start = max(0, char_count - chars_to_delete - ellipses_len - 1)
                    end = max(0, char_count - ellipses_len - 1)

                cursor.setPosition(start)
                cursor.setPosition(end, QTextCursor.KeepAnchor)
                cursor.removeSelectedText()

                # update line width:
                line_width = doc.idealWidth()

                if line_width == start_line_width:
                    break

            self._line_width = line_width
            return doc.toHtml()
        finally:
            qtutils.safe_delete_later(doc)

    @property
    def line_width(self):
        """
        :returns: int, width of the line of text in pixels
        """
        return self._line_width


class ThumbnailLabel(QLabel, object):
    def __init__(self, parent=None):
        super(ThumbnailLabel, self).__init__(parent=parent)

    def setPixmap(self, pixmap):
        if pixmap.height() > 55 or pixmap.width() > 80:
            pixmap = pixmap.scaled(QSize(80, 55), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        super(ThumbnailLabel, self).setPixmap(pixmap)


class AnimatedLabel(QLabel, object):
    def __init__(self, text='', duration=800, parent=None):
        super(AnimatedLabel, self).__init__(text, parent=parent)

        font = self.font()
        font.setPointSize(18)
        font.setBold(True)
        self.setFont(font)

        self.opacity_effect = graphicseffects.OpacityEffect(target=self, duration=duration)

        self.opacity_effect.animation.valueChanged.connect(self._set_label_opacity)
        self.opacity_effect.animation.finished.connect(self.hide)

    # region Properties
    def get_duration(self):
        return self.opacity_effect.duration

    def set_duration(self, value):
        self.opacity_effect.duration = value

    duration = property(get_duration, set_duration)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setOpacity(self.opacity_effect.animation.currentValue())
        if self.text():
            painter.drawText(event.rect(), self.text())

    def show_message(self, text):
        self.setText(text)
        parent = self.parent()
        if parent:
            # TODO: Add option to set aligment of the text inside its parent
            self.move(10, parent.size().height() - self.fontMetrics().height() - 10)
            # if isinstance(parent, QAbstractScrollArea) and parent.verticalScrollBar().isVisible():
            #     self.move(
            #     parent.size().width() - self.fontMetrics().width(text) - 10 - parent.verticalScrollBar().width(), 0)
            # else:
            #     self.move(parent.size().width() - self.fontMetrics().width(text) - 10, 0)
        self.opacity_effect.fade_in_out()

    def _set_label_opacity(self, value):
        if self.opacity_effect.animation.state() == QPropertyAnimation.Running:
            self.setVisible(value > 0)
            self.update()


class IconLabel(QLabel, object):
    """
    Displays an icon beside a standard label
    """

    clicked = Signal()

    def __init__(self, *args, **kwargs):
        self._icon = kwargs.pop('icon') if 'icon' in kwargs else None
        self._press = False
        self._two_sided = True

        super(IconLabel, self).__init__(*args, **kwargs)

        self.setContentsMargins(20, 0, 0, 0)
        self._value_a = self.text()
        self._value_b = self.text()

    def get_value_a(self):
        return self._value_a

    def get_value_b(self):
        return self._value_b

    value_a = property(get_value_a)
    value_b = property(get_value_b)

    def mousePressEvent(self, event):
        if self._two_sided:
            self._press = True
            self.setText(self._value_a, False)
            self.update()
        self.clicked.emit()

    def mouseReleaseEvent(self, event):
        if self._two_sided:
            self._press = False
            self.setText(self._value_b, False)
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        if self._icon:
            self._icon.paint(p, QRect(0, self.height() * 0.5 - 5, 12, 12))
        super(IconLabel, self).paintEvent(event)

    def setText(self, text, update=True):
        super(IconLabel, self).setText('<font>%s</font>' % text)
        if update:
            self._value_b = text

    def set_icon(self, icon):
        self._icon = icon


class ClickableIconLabel(QLabel):
    """
    Custom widget implementation to create square icon buttons as labels.

    :param str pixmap: name of the resource file without the extension.
    :param tuple(QColor, QColor) colors: a tuple of QColors for enabled and disabled states.
    :param int size: value for width and height.
    :param str description: optional user readable description of the action the button performs.
    :param bool state: whether the button is clicked by default.
    :param QWidget parent: parent widget.
    """

    clicked = Signal()
    doubleClicked = Signal()

    def __init__(self, pixmap, colors, size, description='', state=False, pixmap_category=None, theme=None,
                 parent=None):
        super(ClickableIconLabel, self).__init__(parent=parent)

        self._pixmap = pixmap
        self._category = pixmap_category or 'icons'
        self._theme = theme or 'default'
        self._size = size
        self._state = state
        self._on_color = colors[0]
        self._off_color = colors[1]

        self.setStatusTip(description)
        self.setToolTip(description)
        self.setWhatsThis(description)
        self.setFixedSize(QSize(size, size))
        self.setAlignment(Qt.AlignCenter)
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        # self.setAttribute(Qt.WA_NoBackground)
        # self.setAttribute(Qt.WA_TranslucentBackground)

        self.clicked.connect(self._on_clicked)
        self.clicked.connect(self.update)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def enterEvent(self, event):
        self.repaint()

    def leaveEvent(self, event):
        self.repaint()

    def mouseDoubleClickEvent(self, event):
        if not isinstance(event, QMouseEvent):
            return
        self.doubleClicked.emit()

    def mouseReleaseEvent(self, event):
        if not isinstance(event, QMouseEvent):
            return
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

    def pixmap(self):
        if not self.isEnabled():
            return resources.pixmap(
                self._pixmap, category=self._category, theme=self._theme, color=self._off_color, size=self._size)
        if self.get_state():
            return resources.pixmap(
                self._pixmap, category=self._category, theme=self._theme, color=self._on_color, size=self._size)
        return resources.pixmap(
            self._pixmap, category=self._category, theme=self._theme, color=self._off_color, size=self._size)

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)
        hover = option.state & QStyle.State_MouseOver
        painter = QPainter()
        painter.begin(self)
        painter.setOpacity(0.0)
        if hover:
            painter.setOpacity(1.0)
        if not self.get_state():
            painter.setOpacity(0.5)
        pixmap = self.pixmap()
        painter.drawPixmap(self.rect(), pixmap, pixmap.rect())
        painter.end()

    def contextMenuEvent(self, event):
        pass

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def get_state(self):
        return self._state

    # =================================================================================================================
    # CALLBACKS
    # =================================================================================================================

    def _on_clicked(self):
        """
        Internal callback function that is called when users left-click on the label.

        ..note:: this function should be reimplemented in derived classes
        """

        pass


class ClippedLabel(QLabel, object):
    def __init__(self, text='', width=0, ellipsis=True, always_show_all=False, parent=None):
        super(ClippedLabel, self).__init__(text, parent)

        self._always_show_all = always_show_all
        self._ellipsis = ellipsis

        self._width = None
        self._text = None
        self._elided = None

        self.setMinimumWidth(width if width else 0)

    def paintEvent(self, event):
        painter = QPainter(self)
        self.drawFrame(painter)
        margin = self.margin()
        rect = self.contentsRect()
        rect.adjust(margin, margin, -margin, -margin)
        text = self.text()
        width = rect.width()
        if text != self._text or width != self._width:
            self._text = text
            self._width = width
            self._elided = self.fontMetrics().elidedText(text, Qt.ElideRight, width)
        option = QStyleOption()
        option.initFrom(self)

        if self._always_show_all:
            if self._width >= self.sizeHint().width():
                self.style().drawItemText(
                    painter, rect, self.alignment(), option.palette, self.isEnabled(),
                    self.text(), self.foregroundRole())
        else:
            if self._ellipsis:
                self.style().drawItemText(
                    painter, rect, self.alignment(), option.palette, self.isEnabled(),
                    self._elided, self.foregroundRole())
            else:
                self.style().drawItemText(
                    painter, rect, self.alignment(), option.palette, self.isEnabled(),
                    self.text(), self.foregroundRole())
