from __future__ import annotations

from Qt.QtCore import Qt, QObject, Slot, Signal, QSize, QRunnable
from Qt.QtGui import qRgb, QImage


class IconLoaderSignals(QObject):
    """Define the available signals for the icon loading process.

    Attributes:
        progress: Emits an integer signal representing the progress percentage
            of the icon loading process.
        updated: Emits an object signal when the icon loading process is
            updated, it contains the `QImage` data currently available. If the
            image data is not fully loaded yet, it emits a placeholder image.
        finished: Emits when the icon loading process completes successfully.
        result: Emits an object signal containing the result or data from the
            loaded icons.
        error: Emits a tuple signal containing error information
            (e.g., error type and message) if the icon loading process fails.
    """

    progress = Signal(int)
    updated = Signal(object)
    finished = Signal()
    result = Signal(object)
    error = Signal(tuple)


class IconLoader(QRunnable):
    """Class to load and process icons asynchronously.

    This class is designed to handle the process of loading icons from
    specified file paths into memory, with optional resizing based on given
    dimensions.

    It uses Qt's threading and signal mechanisms to provide a responsive
    interface for updating clients with progress or error signals. The class
    ensures proper management of the icon loading lifecycle, including states
    such as `running` or `finished`.

    Attributes:
        _signals: The signal object for communicating progress, updates,
            errors, and completion status with connected clients.
        _placeholder_image: A placeholder image used to emit an initial visual
            update before loading the actual icon.
        _path: The file path of the icon to be loaded.
        _width: The maximum width to resize the loaded icon, maintaining
            its aspect ratio.
        _height: The maximum height to resize the loaded icon, maintaining
            its aspect ratio.
        _running: Indicates whether the icon loading process is currently
            active.
        _finished: Indicates whether the icon loading process has been
            completed.
    """

    def __init__(
        self, icon_path: str, width: int = 512, height: int = 512, *args, **kwargs
    ):
        # noinspection PyArgumentList
        super().__init__(*args, **kwargs)

        self._signals = IconLoaderSignals()
        kwargs["progress_callback"] = self._signals.progress

        self._placeholder_image = QImage(50, 50, QImage.Format_ARGB32)
        self._placeholder_image.fill(qRgb(96, 96, 96))

        self._path = icon_path
        self._width = width
        self._height = height
        self._running = False
        self._finished = False

    @property
    def signals(self) -> IconLoaderSignals:
        """The signals used by the icon loader."""

        return self._signals

    @Slot()
    def run(self):
        if not self._path or self._finished:
            return

        self._running = True
        self._signals.updated.emit(self._placeholder_image)
        try:
            image = QImage(self._path)
            if image.width() > self._width or image.height() > self._height:
                image = image.scaled(
                    QSize(self._width, self._height), Qt.KeepAspectRatio
                )
        except Exception as e:
            self._signals.error.emit(e)
            self.finish(True)
            self._running = False
            return

        if image.isNull():
            self._signals.error.emit(
                f"Was not possible to load image from path: {self._path}. "
                f"Make sure:\n\t-File path exists."
                f"\n\t-File is a valid image format."
                f"\n\tFile path has a valid extension."
            )
        else:
            self._signals.updated.emit(image)

        self.finish(True)
        self._running = False

    def is_running(self) -> bool:
        """Check if the icon loading process is currently running.

        Returns:
            True if the icon loading process is running; False otherwise.
        """

        return self._running

    def is_finished(self) -> bool:
        """Check if the icon loading process is finished.

        Returns:
            True if the icon loading process is finished; False otherwise.
        """

        return self._finished

    def finish(self, state: bool = False):
        """Finish the icon loading process.

        Args:
            state: If True, the icon loading process is considered successful.
                If False, it indicates an error or cancellation.
        """

        self._finished = state
        self._signals.finished.emit()
