from __future__ import annotations

from Qt.QtCore import qDebug, QFile, QFileInfo, QRegularExpression
from Qt.QtWidgets import QApplication
from Qt.QtGui import QGuiApplication

from tp.tools.pipeline import consts


class PipelineUiStyle:

    _INSTANCE = None

    def __init__(self):
        super().__init__()

        self._css_values: list[list[str, str, str], ...] = []

    @staticmethod
    def instance() -> PipelineUiStyle:
        if not PipelineUiStyle._INSTANCE:
            PipelineUiStyle._INSTANCE = PipelineUiStyle()
        return PipelineUiStyle._INSTANCE

    @staticmethod
    def update_css(css_file_name: str):
        css_files: list[str] = [css_file_name]
        QApplication.instance().setStyleSheet('')
        css_file_info = QFileInfo(css_file_name)
        include_name = f'{css_file_info.completeBaseName()}-{consts.INTERNAL_NAME}'.lower()
        include_path = f'{css_file_info.path()}/{include_name}.css'
        include_file = QFile(include_path)
        include_path = f'{css_file_info.path()}/{include_name}'
        if not include_file.exists():
            include_file.setFileName(include_path)
        if include_file.exists():
            css_files.append(include_path)
        css = PipelineUiStyle.load_css(css_files)
        QApplication.instance().setStyleSheet(css)

    @staticmethod
    def load_css(css_file_name: str | list[str] = ':/styles/default', style_values: str = '') -> str:
        """
        Loads a CSS file. This function tries to find css_file_name-values file and, if found, these values will
        be used. If a list of css files is given, the first CSS file will be used to find the values file.

        :param str css_file_name: file name/s (with complete path) of the CSS.
        :param str style_values: optional style values to override.
        :return: CSS string.
        :rtype: str
        """

        css = ''
        if isinstance(css_file_name, str):
            css_file_name = [css_file_name]
        for file in css_file_name:
            css_file = QFile(file)
            if not css_file.exists():
                continue
            if css_file.open(QFile.ReadOnly):
                css += css_file.readAll()
                css_file.close()

        css_info = QFileInfo(css_file_name[0])
        if not style_values:
            style_values = f'{css_info.path()}/{css_info.completeBaseName()}-values'
        values_file = QFile(style_values)
        if values_file.exists():
            if values_file.open(QFile.ReadOnly):
                PipelineUiStyle.instance().clear_css_values()
                css += '\n'
                while not values_file.atEnd():
                    line = str(values_file.readLine())
                    re = QRegularExpression('(@(\\w+)(?:-(\\w+(?:-\\w+)*))?) *= *(\\S+)')
                    match = re.match(line)
                    if match.hasMatch():
                        name = match.captured(1)
                        type = match.captured(2)
                        type_name = match.captured(3)
                        value = match.captured(4)
                        try:
                            pixel_index = value.index('px')
                            if pixel_index:
                                value = str(PipelineUiStyle.scale_size(int(value[:-3])))
                        except ValueError:
                            value = value.rstrip().replace('\\r', '').replace('\\n', '')[:-1]
                        css = css.replace(name, value)
                        css_value = [type, type_name, value]
                        PipelineUiStyle.instance().add_css_value(css_value)

        qDebug(f'{PipelineUiStyle.__name__}: CSS ready!')

        return css

    @staticmethod
    def scale_size(value: int | float, ratio: int = 0) -> int | float:
        """
        Scales given size.

        :param int or float value: value to scale.
        :param int ratio: scale ratio .If 0, device pixel ratio of primary screen will be used.
        :return: scaled value.
        :rtype: int or float
        """

        ratio = QGuiApplication.primaryScreen().devicePixelRatio() if ratio == 0 else ratio
        return value * ratio

    def add_css_value(self, value: list[str, str, str]):
        """
        Add given values to the list of CSS values.

        :param list[str, str, str] value: list containing the type, type name and value.
        """

        self._css_values.extend(value)

    def css_values(self) -> list[list[str, str, str], ...]:
        """
        Returns list of CSS values.

        :return: list of CSS values.
        :rtype: list[list[str, str, str], ...]
        """

        return self._css_values

    def clear_css_values(self):
        """
        Clear stored CSS values.
        """

        self._css_values.clear()
