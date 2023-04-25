#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utility functions related with images
"""

import os
import re
import base64
import traceback

try:
    import urllib2 as urllib
except ImportError:
    import urllib

from Qt.QtCore import Qt, Signal, QByteArray, QRunnable, QObject, QTimer
from Qt.QtGui import QImage, QPixmap, QBitmap, QIcon, QColor, QPainter

from tp.core import log
from tp.common.python import helpers, path as path_utils

LOGGER = log.tpLogger

ImageFormats = {
    QImage.Format_Mono: 'L',                            # Mono
    QImage.Format_MonoLSB: 'L',                         # Mono LSB
    QImage.Format_Indexed8: 'P',                        # 8bit Color Map
    QImage.Format_RGB32: 'RGB',                         # RGB32
    QImage.Format_ARGB32: 'RGBA',                       # RGBA32
    QImage.Format_ARGB32_Premultiplied: 'RGBA',         # RGBA_Premultiplied
    QImage.Format_RGB16: 'RGB',                         # RGB16
    QImage.Format_ARGB8565_Premultiplied: 'RGBA',       # RGBA24 Premultiplied (5-6-5-8)
    QImage.Format_RGB666: 'RGB',                        # RGB24 (6-6-6)
    QImage.Format_ARGB6666_Premultiplied: 'RGBA',       # RGBA24 Premultiplied (6-6-6-6)
    QImage.Format_RGB555: 'RGB',                        # RGB16 (5-5-5)
    QImage.Format_ARGB8555_Premultiplied: 'RGBA',       # RGB24 Premultiplied (5-5-5-8)
    QImage.Format_RGB888: 'RGB',                        # RGB (8-8-8)
    QImage.Format_RGB444: 'RGB',                        # RGB (4-4-4)
    QImage.Format_ARGB4444_Premultiplied: 'RGB'         # RGBA16 Premultiplied (4-4-4-4)
}


def mode_to_qformat(mode):
    """
    Returns specific image mode taking into account given mode string
    :param mode: str
    :return: QImage.Format
    """

    if mode == 'RGBA':
        return QImage.Format_ARGB32_Premultiplied
    else:
        return QImage.Format_RGB32


def create_image(width, height, mode):
    """
    Creates a new QImage with the given resolution and mode
    :param width: int
    :param height: int
    :param mode: str
    :return: QImage
    """

    mode = mode_to_qformat(mode)
    if width <= 0 or height <= 0:
        raise Exception('Resolution for new image is negative or zero (X: {}, Y: {})'.format(width, height))
    new_image = QImage(width, height, mode)

    return new_image


def create_empty_image(output=None, resolution_x=1920, resolution_y=1080, background_color=None):
    """
    Creates an empty image and stores it in the given path
    :param output: str
    :param resolution_x: int
    :param resolution_y: int
    :param background_color: list(int, int, int)
    :return: str or QImage
    """

    if background_color is None:
        background_color = [0, 0, 0]

    pixmap = QPixmap(resolution_x, resolution_y)
    pixmap.fill(QColor(*background_color))
    if output:
        output_path = path_utils.clean_path(output)
        output_dir = os.path.dirname(output_path)
        if os.access(output_dir, os.W_OK):
            pixmap.save(output_path)
            return output_path

    return QImage(pixmap)


def get_image_width(image_path):
    """
    Returns the width of the image stored in given file path
    :param image_path: str
    :return: float
    """

    if not image_path or not os.path.isfile(image_path):
        return 0

    image = QImage(image_path)
    if not image or image.isNull():
        return 0

    return image.width()


def get_image_height(image_path):
    """
    Returns the height of the image stored in given file path
    :param image_path: str
    :return: float
    """

    if not image_path or not os.path.isfile(image_path):
        return 0

    image = QImage(image_path)
    if not image or image.isNull():
        return 0

    return image.height()


def paint_background(image, background_color=None):
    """
    Paints a background of the given color into the given QImage
    :param image: QImage
    :param background_color: tuple(r, g, b)
    :return: QImage, image with painted background
    """

    if not background_color:
        background_color = [0, 0, 0]

    if type(background_color) not in (list, tuple) or len(background_color) != 3:
        LOGGER.warning(
            'background_color argument is not valid ({}) using black color instead!'.format(background_color))
        background_color = [0, 0, 0]
    background_color = helpers.force_list(background_color)

    for i in range(len(background_color)):
        if background_color[i] < 0 or background_color[i] > 255:
            LOGGER.warning(
                'Background color channel ({})({}) out of limit (0, 255). Fixing to fit range ...'.format(
                    i, background_color[i]))
            background_color[i] = min(max(background_color[i], 0), 255)

    image.fill(QColor(*background_color).rgb())

    return image


def fit_image_in_resolution(image, width, height):
    """
    Resizes given image to fit in given width and height.
    :param image: QImage
    :param width: int
    :param height: int
    :return: QImage
    """

    resize_ratio = min((float(width) / float(image.width())), float(height) / float(image.height()))
    new_width = int(round(float(image.width()) * resize_ratio))
    new_height = int(round(float(image.height()) * resize_ratio))

    return image.scaled(new_width, new_height, Qt.KeepAspectRatio)


def overlay_image(front_image, back_image, x, y):
    """
    Overlays front image on top of given background image
    :param front_image: QImage
    :param back_image: QImage
    :param x: int
    :param y: int
    """

    painter = QPainter(back_image)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.drawImage(x, y, front_image)
    painter.end()


def download_image(image_url, target_image_path):
    """
    Downloads image from URL and stores in given target path in disk
    :param image_url: str
    :param target_image_path: str
    """

    if not os.path.isfile(target_image_path):
        with open(target_image_path, 'wb') as temp_out_image:
            try:
                file_image_url = urllib.urlopen(image_url)
            except urllib.HTTPError as exc:
                raise Exception('HTTPError: {} | {}'.format(image_url, exc.code))
            except urllib.URLError as exc:
                raise Exception('URLError: {} | {}'.format(image_url, exc))
            except Exception as exc:
                raise Exception('Generic exception: {} | {}'.format(image_url, traceback.format_exc()))

            temp_out_image.write(file_image_url.read())
            file_image_url.close()


class ImageWorker(QRunnable, object):
    """
    Class that loads an image in a thread
    """

    class ImageWorkerSignals(QObject, object):
        triggered = Signal(object)

    def __init__(self, *args):
        super(ImageWorker, self).__init__(*args)

        self._path = None
        self.signals = ImageWorker.ImageWorkerSignals()

    def set_path(self, path):
        """
        Set the image path to be loaded
        :param path: str
        """

        self._path = path

    def run(self):
        """
        Overrides base QRunnable run function
        This is the starting point for the thread
        """

        try:
            if self._path:
                image = QImage(str(self._path))
                self.signals.triggered.emit(image)
        except Exception as e:
            LOGGER.error('Cannot load thumbnail image!')


class ImageSequence(QObject, object):

    DEFAULT_FPS = 24

    frameChanged = Signal(int)

    def __init__(self, path, *args):
        super(ImageSequence, self).__init__(*args)

        self._fps = self.DEFAULT_FPS
        self._timer = None
        self._frame = 0
        self._frames = list()
        self._dirname = None
        self._paused = False

        if path:
            self.set_dirname(path)

    def set_path(self, path):
        """
        Sets s single frame image sequence
        :param path: str
        """

        if not path:
            return

        if os.path.isfile(path):
            self._frame = 0
            self._frames = [path]
        elif os.path.isdir(path):
            self.set_dirname(path)

    def dirname(self):
        """
        Return the location to the image sequence in disk
        :return: str
        """

        return self._dirname

    def set_dirname(self, dirname):
        """
        Set the location where image sequence files are located
        :param dirname: str
        """

        def natural_sort_items(items):
            """
            Sort the given list in the expected way
            :param items: list(str)
            """

            def _convert(text):
                return int(text) if text.isdigit() else text

            def _alphanum_key(key):
                return [_convert(c) for c in re.split('([0-9]+)', key)]

            items.sort(key=_alphanum_key)

        self._dirname = dirname
        if os.path.isdir(dirname):
            self._frames = [dirname + '/' + filename for filename in os.listdir(dirname)]
            natural_sort_items(self._frames)

    def first_frame(self):
        """
        Returns the path of the first frame of the sequence
        :return: str
        """

        if not self._frames:
            return ''

        return self._frames[0]

    def start(self):
        """
        Starts the image sequence
        """

        self.reset()
        if self._timer:
            self._timer.start(1000.0 / self._fps)

    def pause(self):
        """
        Pause image sequence
        """

        self._paused = True
        if self._timer:
            self._timer.stop()

    def resume(self):
        """
        Play image sequence after Pause
        """

        if self._paused:
            self._paused = False
            if self._timer:
                self._timer.start()

    def stop(self):
        """
        Stop the image sequence
        """

        if self._timer:
            self._timer.stop()

    def reset(self):
        """
        Stop and reset the current frame to 0
        """

        if not self._timer:
            self._timer = QTimer(self.parent())
            self._timer.setSingleShot(False)
            self._timer.timeout.connect(self._on_frame_changed)

        if not self._paused:
            self._frame = 0
        self._timer.stop()

    def frames(self):
        """
        Return all the filenames in the image sequence
        :return: list(str)
        """

        return self._frames

    def percent(self):
        """
        Return the current frame position as a percentage
        :return: float
        """

        if len(self._frames) == self._frame + 1:
            _percent = 1
        else:
            _percent = float((len(self._frames) + self._frame)) / len(self._frames) - 1

        return _percent

    def frame_count(self):
        """
        Returns the number of frames
        :return: int
        """

        return len(self._frames)

    def current_frame_number(self):
        """
        Returns the current frame
        :return: int
        """

        return self._frame

    def current_filename(self):
        """
        Returns the current file name
        :return: str
        """

        try:
            return self._frames[self.current_frame_number()]
        except IndexError:
            pass

    def current_icon(self):
        """
        Returns the current frames as QIcon
        :return: QIcon
        """

        return QIcon(self.current_filename())

    def current_pixmap(self):
        """
        Returns the current frame as QPixmap
        :return: QPixmap
        """

        return QPixmap(self.current_filename())

    def jump_to_frame(self, frame):
        """
        Set the current frame
        :param frame: int
        """

        if frame >= self.frame_count():
            frame = 0
        self._frame = frame
        self.frameChanged.emit(frame)

    def _on_frame_changed(self):
        """
        Internal callback function that is called when the current frame changes
        """

        if not self._frames:
            return

        frame = self._frame
        frame += 1
        self.jump_to_frame(frame)


def image_to_base64(image_path):
    """
    Converts image file to base64
    :param image_path: str
    :return: str
    """

    if os.path.isfile(image_path):
        with open(image_path, 'rb') as image_file:
            base64_data = base64.b64encode(image_file.read())
            if helpers.is_python2():
                return base64_data
            else:
                return base64_data.decode("utf-8")


def base64_to_image(base64_string, image_format='PNG'):
    """
    Converts base64 to QImage
    :param base64_string: str
    :param image_format: str
    :return: QImage
    """

    try:
        ba = QByteArray.fromBase64(base64_string)
        image = QImage.fromData(ba, image_format)
        return image
    except Exception:
        return None


def base64_to_bitmap(base64_string, bitmap_format='PNG'):
    """
    Converts base64 to QBitmap
    :param base64_string: str
    :param image_format: str
    :return: QBitmap
    """

    image = base64_to_image(base64_string, bitmap_format)
    if image is not None:
        bitmap = QBitmap.fromImage(image)
        return bitmap


def base64_to_icon(base64_string, icon_format='PNG'):
    """
    Converts base64 to QIcon
    :param base64_string: str
    :param icon_format: str
    :return: QIcon
    """

    bitmap = base64_to_bitmap(base64_string, icon_format)
    if bitmap is not None:
        icon = QIcon(bitmap)
        return icon
