from __future__ import annotations

from Qt.QtWidgets import QWidget, QTabWidget
from Qt.QtGui import QColor

from ..views import uiconsts


class NodeGraphWidget(QTabWidget):
    """
    Node graph widget class.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self.setTabsClosable(True)
        self.setTabBarAutoHide(True)

        bg_color = QColor(*uiconsts.NODE_GRAPH_BACKGROUND_COLOR).darker(120).getRgb()
        text_color = tuple(map(lambda i, j: i - j, (255, 255, 255), bg_color))
        style_dict = {
            "QWidget": {
                "background-color": "rgb({0},{1},{2})".format(
                    *uiconsts.NODE_GRAPH_BACKGROUND_COLOR
                ),
            },
            "QTabWidget::pane": {
                "background": "rgb({0},{1},{2})".format(
                    *uiconsts.NODE_GRAPH_BACKGROUND_COLOR
                ),
                "border": "0px",
                "border-top": "0px solid rgb({0},{1},{2})".format(*bg_color),
            },
            "QTabBar::tab": {
                "background": "rgb({0},{1},{2})".format(*bg_color),
                "border": "0px solid black",
                "color": "rgba({0},{1},{2},30)".format(*text_color),
                "min-width": "10px",
                "padding": "10px 20px",
            },
            "QTabBar::tab:selected": {
                "color": "rgb({0},{1},{2})".format(*text_color),
                "background": "rgb({0},{1},{2})".format(
                    *uiconsts.NODE_GRAPH_BACKGROUND_COLOR
                ),
                "border-top": "1px solid rgb({0},{1},{2})".format(
                    *uiconsts.NODE_BORDER_SELECTED_COLOR
                ),
            },
            "QTabBar::tab:hover": {
                "color": "rgb({0},{1},{2})".format(*text_color),
                "border-top": "1px solid rgb({0},{1},{2})".format(
                    *uiconsts.NODE_BORDER_SELECTED_COLOR
                ),
            },
        }
        stylesheet = ""
        for css_class, css in style_dict.items():
            style = "{} {{\n".format(css_class)
            for elm_name, elm_val in css.items():
                style += "  {}:{};\n".format(elm_name, elm_val)
            style += "}\n"
            stylesheet += style
        self.setStyleSheet(stylesheet)
