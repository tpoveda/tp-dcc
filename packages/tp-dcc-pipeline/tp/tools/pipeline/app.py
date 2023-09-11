from __future__ import annotations

import sys

from PySide6.QtCore import QSharedMemory

from Qt.QtCore import Qt, Slot, QTimer, QtMsgType, QMessageLogContext, qDebug, qInstallMessageHandler, QCoreApplication
from Qt.QtWidgets import QApplication
from Qt.QtGui import QIcon

from tp.tools.pipeline import consts, style


class MessageHandler:

    @staticmethod
    def message_output(type: QtMsgType, context: QMessageLogContext, msg: str):
        file = context.file or ''
        function = context.function or ''
        if type == QtMsgType.QtDebugMsg:
            sys.stderr.write(f'Debug: {msg} ({file}:{context.line}, {function})\n')
        elif type == QtMsgType.QtInfoMsg:
            sys.stderr.write(f'{msg}\n')
        elif type == QtMsgType.QtWarningMsg:
            sys.stderr.write(f'Warning: {msg} ({file}:{context.line}, {function})\n')
        elif type == QtMsgType.QtCriticalMsg:
            sys.stderr.write(f'Critical: {msg} ({file}:{context.line}, {function})\n')
        elif type == QtMsgType.QtFatalMsg:
            sys.stderr.write(f'Fatal: {msg} ({file}:{context.line}, {function})\n')


class PipelineApplication(QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        qInstallMessageHandler(MessageHandler.message_output)
        qDebug('Initializing application')
        qDebug('Creating ')

        # Used to check whether another instance is running
        shared_memory_key = f'{consts.ORGANIZATION_NAME}_{consts.PRODUCT_NAME}_{consts.VERSION}'
        qDebug(f'Key {shared_memory_key}')
        self._singular = QSharedMemory(shared_memory_key, self)

        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
        style.PipelineUiStyle.update_css(':/styles/default')
        QApplication.instance().setWindowIcon(QIcon(consts.APP_ICON))

        QCoreApplication.setOrganizationName(consts.ORGANIZATION_NAME)
        QCoreApplication.setOrganizationDomain(consts.AUTHOR_NAME)
        QCoreApplication.setApplicationName(consts.PRODUCT_NAME)
        QCoreApplication.setApplicationVersion(consts.VERSION)

        self._idle_timer = QTimer()
        self._idle_timer.timeout.connect(self._on_idle_timeout)
        self._idle_timeout = 120 * 60 * 1000
        self._idle_timer.start(self._idle_timeout)

    def __del__(self):
        if self._singular.isAttached():
            self._singular.detach()
        del self

    @Slot()
    def _on_idle_timeout(self):
        print('gogogogog')


