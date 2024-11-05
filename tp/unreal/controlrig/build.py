from __future__ import annotations

import sys
import time
import logging
from typing import Callable

from Qt.QtCore import Qt, QTimer, QUrl
from Qt.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QTextBrowser,
    QProgressBar,
)
from Qt.QtGui import QTextCursor

from tp.qt import factory as qt
from tp.qt.widgets import window

logger = logging.getLogger(__name__)

# Global variable that stores the ControlRigBuildWindow instance.
_BUILD_WINDOW: ControlRigBuildWindow | None = None


class ControlRigBuildWindow(window.Window):
    """
    Base class for Unreal Control Rig build Windows.
    """

    def __init__(self, *args, **kwargs):
        kwargs["width"] = 500
        kwargs["height"] = 300
        kwargs["name"] = "ControlRigBuildWindow"
        kwargs["title"] = "Control Rig Build"
        run_callback: Callable | None = kwargs.pop("run_callback", None)
        super().__init__(*args, **kwargs)

        self._time_last_since_log: int | None = None

        if run_callback:
            QTimer.singleShot(10, run_callback)

    @property
    def progress_bar(self) -> QProgressBar:
        """
        Getter method that returns the progress bar of the window.

        :return: progress bar instance.
        """

        return self._progress

    # noinspection PyAttributeOutsideInit
    def setup_widgets(self):
        super().setup_widgets()

        self._label = qt.label(
            "Control Rig Build", alignment=Qt.AlignCenter, parent=self
        ).strong()

        self._browser = QTextBrowser(parent=self)
        self._browser.setOpenLinks(False)
        self._browser.setReadOnly(True)
        self._browser.setStyleSheet("color: black;")
        self._browser.append("....")
        self._progress = QProgressBar(parent=self)
        self._progress.setRange(0, 10)
        self._progress.setValue(0)

    def setup_layouts(self, main_layout: QVBoxLayout | QHBoxLayout | QGridLayout):
        super().setup_layouts(main_layout)

        main_layout.addWidget(self._label)
        main_layout.addWidget(self._browser)
        main_layout.addWidget(self._progress)

    def setup_signals(self):
        super().setup_signals()

        self._browser.anchorClicked.connect(self._on_browser_anchor_clicked)

    def add_log_text(
        self,
        text: str,
        log_text: bool = True,
        quotations_to_link: bool = True,
        log_time_when_done: bool = True,
    ):
        """
        Function that logs a message in the Control Rig Build Window.

        :param text: message to log.
        :param log_text: Whether to log the text or not.
        :param quotations_to_link:
        :param log_time_when_done:
        """

        if log_text:
            logger.info(text)

        if self._time_last_since_log is not None:
            self.add_to_end(
                "  (%0.3f seconds)" % (time.time() - self._time_last_since_log)
            )

        lines = text.split("\n")
        comma_line = ", line"

        # if quotations_to_link:
        #     for i, line in enumerate(lines):
        #         index_first_quotation = line.find('"', 0)
        #         if index_first_quotation != -1:
        #             index_second_quotation = line.find('"', index_first_quotation + 1)
        #             if index_second_quotation != -1:
        #                 file_path = line[
        #                     index_first_quotation + 1 : index_second_quotation
        #                 ]
        #                 if "/" in file_path or "\\" in file_path:
        #                     found_link = file_path
        #                     index_comma_line = line.find(
        #                         comma_line, index_second_quotation
        #                     )
        #                     if index_comma_line != -1:
        #                         number_start_index = index_comma_line + len(comma_line)
        #                         number_end_index = line.find(",", number_start_index)
        #                         if number_end_index == -1:
        #                             number_end_index = len(line)
        #                         found_number = line[
        #                             number_start_index:number_end_index
        #                         ].strip()
        #                         found_link = "%s@%s" % (found_link, found_number)
        #                     lines[i] = '%s<a href="%s"> "%s" </a>%s' % (
        #                         line[:index_first_quotation],
        #                         found_link.replace("\\", "/"),
        #                         file_path,
        #                         line[index_second_quotation + 1 :],
        #                     )

        for line in lines:
            self._browser.append(line)

        self._time_last_since_log = time.time() if log_time_when_done else None

    def add_to_end(self, text: str):
        """
        Function that adds text to the end of the log.

        :param text: text to add.
        """

        text_cursor = self._browser.textCursor()
        text_cursor.movePosition(QTextCursor.End)
        text_cursor.insertText(text)

    # noinspection PyMethodMayBeStatic
    def _on_browser_anchor_clicked(self, link: QUrl):
        """
        Function that is called when a link is clicked in the browser.

        :param link: link clicked.
        """

        link = link.toString()
        link_splits = link.split("@")
        if ".py" in link_splits[0]:
            pass


def open_build_window(run_callback, progress_count: int = 10) -> ControlRigBuildWindow:
    """
    Function that opens the Control Rig Build Window.

    :param run_callback: callback to run when tool is opened.
    :param progress_count: number of build steps to show in the progress bar.
    :return: newly created ControlRigBuildWindow instance.
    """

    global _BUILD_WINDOW

    # noinspection PyArgumentList
    if QApplication.instance():
        for win in QApplication.allWindows():
            if "ControlRigBuildWindow" in win.objectName():
                win.destroy()
    else:
        # noinspection PyTypeChecker
        QApplication(sys.argv)

    _BUILD_WINDOW = ControlRigBuildWindow(run_callback=run_callback)
    _BUILD_WINDOW.progress_bar.setRange(0, progress_count)
    _BUILD_WINDOW.progress_bar.setValue(0)
    _BUILD_WINDOW.show()

    return _BUILD_WINDOW


def log_build_message(message: str, log_time_when_done: bool = True):
    """
    Function that logs a message in the Control Rig Build Window.

    :param message: str, message to log.
    :param log_time_when_done: bool, Whether to log the time when the message is done or not.
    """

    global _BUILD_WINDOW

    if not _BUILD_WINDOW:
        return

    _BUILD_WINDOW.add_log_text(message, log_time_when_done=log_time_when_done)


def increment_build_progress():
    """
    Function that increments the progress bar of the Control Rig Build Window.
    """

    global _BUILD_WINDOW

    if not _BUILD_WINDOW:
        return

    _BUILD_WINDOW.progress_bar.setValue(_BUILD_WINDOW.progress_bar.value() + 1)
