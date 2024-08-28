from __future__ import annotations

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QWidget, QFrame, QHBoxLayout

from .. import dpi
from . import labels


class Divider(QWidget, dpi.DPIScaling):
    """
    Basic standard splitter with optional text.
    """

    textChanged = Signal(str)

    _ALIGN_MAP = {Qt.AlignCenter: 50, Qt.AlignLeft: 20, Qt.AlignRight: 80}

    def __init__(
        self,
        text: str | None = None,
        shadow: bool = True,
        orientation: Qt.Orientation = Qt.Horizontal,
        alignment: Qt.AlignmentFlag = Qt.AlignLeft,
        parent: QWidget | None = None,
    ):
        """
        Initializes Divider.

        :param str text: Optional text to include as title in the splitter.
        :param bool shadow: True if you want a shadow above the splitter.
        :param Qt.Orientation orientation: Orientation of the splitter.
        :param Qt.AlignmentFlag alignment: Alignment of the splitter.
        :param QWidget or None parent: Parent of the splitter.
        """

        super().__init__(parent=parent)

        self._orient = orientation
        self._text = None

        main_layout = QHBoxLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        self._label = labels.BaseLabel(parent=self).strong(True)

        self._first_line = QFrame()
        self._second_line = QFrame()

        main_layout.addWidget(self._first_line)
        main_layout.addWidget(self._label)
        main_layout.addWidget(self._second_line)

        if orientation == Qt.Horizontal:
            self._first_line.setFrameShape(QFrame.HLine)
            self._first_line.setFrameShadow(QFrame.Sunken)
            self._first_line.setFixedHeight(
                2
            ) if shadow else self._first_line.setFixedHeight(1)
            self._second_line.setFrameShape(QFrame.HLine)
            self._second_line.setFrameShadow(QFrame.Sunken)
            self._second_line.setFixedHeight(
                2
            ) if shadow else self._second_line.setFixedHeight(1)
        else:
            self._label.setVisible(False)
            self._second_line.setVisible(False)
            self._first_line.setFrameShape(QFrame.VLine)
            self._first_line.setFrameShadow(QFrame.Sunken)
            self.setFixedWidth(2)
            self._first_line.setFixedWidth(
                2
            ) if shadow else self._first_line.setFixedWidth(1)

        main_layout.setStretchFactor(
            self._first_line, self._ALIGN_MAP.get(alignment, 50)
        )
        main_layout.setStretchFactor(
            self._second_line, 100 - self._ALIGN_MAP.get(alignment, 50)
        )

        self.set_text(text)

    @classmethod
    def left(cls, text: str = "") -> Divider:
        """
        Creates a horizontal splitter with text at left.

        :param text: divider left text.
        :return: Divider instance.
        """

        return cls(text, alignment=Qt.AlignLeft)

    @classmethod
    def right(cls, text: str = "") -> Divider:
        """
        Creates a horizontal splitter with text at right

        :param text: divider right text.
        :return: Divider instance.
        """

        return cls(text, alignment=Qt.AlignRight)

    @classmethod
    def center(cls, text: str = "") -> Divider:
        """
        Creates a horizontal splitter with text at center.

        :param text: divider center text.
        :return: Divider instance.
        """

        return cls(text, alignment=Qt.AlignCenter)

    @classmethod
    def vertical(cls) -> Divider:
        """
        Creates a vertical splitter.

        :return: Divider instance.
        """

        return cls(orientation=Qt.Vertical)

    def text(self) -> str:
        """
        Returns splitter text.

        :return: splitter text.
        """

        return self._label.text()

    def set_text(self, text: str):
        """
        Sets splitter text.

        :param text: splitter text.
        """

        self._text = text
        self._label.setText(text)
        if self._orient == Qt.Horizontal:
            self._label.setVisible(bool(text))
            self._second_line.setVisible(bool(text))

        self.textChanged.emit(self._text)
