from __future__ import annotations

import typing
from typing import Any
from abc import abstractmethod

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import (
    QWidget,
    QGraphicsItem,
    QGraphicsProxyWidget,
    QGroupBox,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QVBoxLayout,
)

from ..views import uiconsts
from ..core import exceptions

if typing.TYPE_CHECKING:
    from ..core.node import BaseNode


class AbstractNodeWidget(QGraphicsProxyWidget):
    """
    Main wrapper class that allows a QWidget to be used as a node widget.
    """

    valueChanged = Signal(str, object)

    def __init__(
        self,
        label: str = "",
        name: str | None = None,
        parent: QGraphicsItem | None = None,
    ):
        super().__init__(parent=parent)

        self._name = name
        self._label = label
        self._node: BaseNode | None = None

        self.setZValue(uiconsts.Z_VALUE_NODE_WIDGET)

    @property
    def widget_type(self) -> str:
        """
        Returns the type of the widget.

        :return: str
        """

        return self.__class__.__name__

    @property
    def name(self) -> str | None:
        """
        Returns the name of the widget.

        :return: str | None
        """

        return self._name

    @name.setter
    def name(self, value: str | None):
        """
        Sets the name of the widget.

        :param value: str | None
        """

        if not value:
            return
        if self._node:
            # noinspection PyTypeChecker
            raise exceptions.NodeWidgetAlreadyInitializedError(self._node.type)
        self._name = value

    @property
    def node(self) -> BaseNode | None:
        """
        Returns the node that owns the widget.

        :return: BaseNode | None
        """

        return self._node

    @node.setter
    def node(self, value: BaseNode | None):
        """
        Sets the node that owns the widget.

        :param value: BaseNode | None
        """

        self._node = value

    @property
    def label(self) -> str:
        """
        Returns the label of the widget.

        :return: str
        """

        return self._label

    @label.setter
    def label(self, value: str):
        """
        Sets the label of the widget.

        :param value: str
        """

        self._label = value
        # noinspection PyTypeChecker
        widget: NodeGroupBox | None = self.widget()
        if widget:
            widget.setTitle(value)

    @property
    def custom_widget(self) -> QWidget:
        """
        Returns the custom widget of the node.

        :return: custom node widget.
        """

        # noinspection PyTypeChecker
        widget: NodeGroupBox = self.widget()
        return widget.node_widget() if widget else None

    @custom_widget.setter
    def custom_widget(self, value: QWidget):
        """
        Sets the custom widget of the node.

        :param value: QWidget
        """

        if self.widget():
            raise exceptions.NodeWidgetAlreadyInitializedError(
                self._node.type if self._node else ""
            )
        group = NodeGroupBox(self._label, parent=self)
        group.add_node_widget(value)
        self.setWidget(group)

    def setToolTip(self, tooltip: str):
        """
        Sets the tooltip of the widget.

        :param tooltip: str
        """

        tooltip = tooltip.replace("\n", "<br/>")
        tooltip = "<b>{}</b><br/>{}".format(self.name, tooltip)
        super().setToolTip(tooltip)

    @abstractmethod
    def get_value(self) -> Any:
        """
        Returns the value of the widget.

        :return: Any
        """

        raise NotImplementedError

    @abstractmethod
    def set_value(self, value: Any):
        """
        Sets the value of the widget.

        :param value: Any
        """

        raise NotImplementedError

    # noinspection PyUnusedLocal
    def _on_value_changed(self, *args, **kwargs):
        """
        Internal callback function that is called when the value of the widget changes.
        """

        self.valueChanged.emit(self.name, self.get_value())


class NodeGroupBox(QGroupBox):
    """
    Main wrapper class that allows a QGroupBox to be used as a node widget.
    """

    def __init__(self, label: str, parent: AbstractNodeWidget | None = None):
        super().__init__()

        main_layout = QVBoxLayout()
        main_layout.setSpacing(1)
        self.setLayout(main_layout)
        self.setTitle(label)

    def setTitle(self, title: str):
        """
        Sets the title of the group box.

        :param title: str
        """

        margin = (0, 2, 0, 0) if title else (0, 0, 0, 0)
        self.layout().setContentsMargins(*margin)
        super(NodeGroupBox, self).setTitle(title)

    def add_node_widget(self, widget: QWidget):
        """
        Adds a node widget to the group box.

        :param widget: node widget
        """

        self.layout().addWidget(widget)

    def node_widget(self) -> QWidget:
        """
        Returns the node widget of the group box.

        :return: QWidget
        """

        return self.layout().itemAt(0).widget()

    def set_title_align(self, align: str = "center"):
        """
        Sets the alignment of the title of the group box.

        :param align: align.
        """

        text_color = tuple(
            map(
                lambda i, j: i - j,
                (255, 255, 255),
                uiconsts.NODE_GRAPH_BACKGROUND_COLOR,
            )
        )
        style_dict = {
            "QGroupBox": {
                "background-color": "rgba(0, 0, 0, 0)",
                "border": "0px solid rgba(0, 0, 0, 0)",
                "margin-top": "1px",
                "padding-bottom": "2px",
                "padding-left": "1px",
                "padding-right": "1px",
                "font-size": "8pt",
            },
            "QGroupBox::title": {
                "subcontrol-origin": "margin",
                "subcontrol-position": "top center",
                "color": "rgba({0}, {1}, {2}, 100)".format(*text_color),
                "padding": "0px",
            },
        }
        if self.title():
            style_dict["QGroupBox"]["padding-top"] = "14px"
        else:
            style_dict["QGroupBox"]["padding-top"] = "2px"

        if align == "center":
            style_dict["QGroupBox::title"]["subcontrol-position"] = "top center"
        elif align == "left":
            style_dict["QGroupBox::title"]["subcontrol-position"] += "top left"
            style_dict["QGroupBox::title"]["margin-left"] = "4px"
        elif align == "right":
            style_dict["QGroupBox::title"]["subcontrol-position"] += "top right"
            style_dict["QGroupBox::title"]["margin-right"] = "4px"
        stylesheet = ""
        for css_class, css in style_dict.items():
            style = "{} {{\n".format(css_class)
            for elm_name, elm_val in css.items():
                style += "  {}:{};\n".format(elm_name, elm_val)
            style += "}\n"
            stylesheet += style
        self.setStyleSheet(stylesheet)


class NodeComboBox(AbstractNodeWidget):
    """
    Class that displays a  `QComboBox` in a node.
    """

    def __init__(
        self,
        label: str = "",
        name: str | None = None,
        items: list[str] | None = None,
        parent: QGraphicsItem | None = None,
    ):
        super().__init__(label=label, name=name, parent=parent)

        combo = QComboBox()
        combo.setMinimumHeight(24)
        combo.addItems(items or [])
        combo.clearFocus()

        combo.currentIndexChanged.connect(self._on_value_changed)

        self.custom_widget = combo

    @property
    def widget_type(self) -> str:
        """
        Returns the type of the widget.

        :return: str
        """

        return "ComboNodeWidget"

    def get_value(self) -> str:
        """
        Returns the value of the widget.

        :return: combo box value.
        """

        # noinspection PyTypeChecker
        combo: QComboBox = self.custom_widget
        return str(combo.currentText())

    def set_value(self, text: str | list[str] = ""):
        """
        Sets the value of the widget.

        :param text: str
        """

        # noinspection PyTypeChecker
        combo: QComboBox = self.custom_widget
        if isinstance(text, (list, tuple)):
            combo.clear()
            combo.addItems(text)
            return
        if text == self.get_value():
            return
        index = combo.findText(text, Qt.MatchExactly)
        combo.setCurrentIndex(index)

    def add_item(self, item: str):
        """
        Adds an item to the combo box.

        :param item: str
        """

        # noinspection PyTypeChecker
        combo: QComboBox = self.custom_widget
        combo.addItem(item)

    def add_items(self, items: list[str] | None = None):
        """
        Adds items to the combo box.

        :param items: list[str]
        """

        # noinspection PyTypeChecker
        combo: QComboBox = self.custom_widget
        combo.addItems(items or [])

    def all_items(self) -> list[str]:
        """
        Returns all items in the combo box.

        :return: list[str]
        """

        # noinspection PyTypeChecker
        combo: QComboBox = self.custom_widget
        return [combo.itemText(i) for i in range(combo.count())]

    def sort_items(self, reverse: bool = False):
        """
        Sorts the items in the combo box.

        :param reverse: bool
        """

        # noinspection PyTypeChecker
        combo: QComboBox = self.custom_widget
        items = sorted(self.all_items(), reverse=reverse)
        combo.clear()
        combo.addItems(items)

    def clear(self):
        """
        Clears the combo box.
        """

        # noinspection PyTypeChecker
        combo: QComboBox = self.custom_widget
        combo.clear()


class NodeLineEdit(AbstractNodeWidget):
    """
    Class that displays a `QLineEdit` in a node.
    """

    def __init__(
        self,
        label: str = "",
        name: str | None = None,
        text: str = "",
        placeholder_text: str = "",
        parent: QGraphicsItem | None = None,
    ):
        super().__init__(label=label, name=name, parent=parent)

        line_edit = QLineEdit()
        line_edit.setText(text)
        line_edit.setPlaceholderText(placeholder_text)
        line_edit.setAlignment(Qt.AlignCenter)
        line_edit.clearFocus()

        line_edit.editingFinished.connect(self._on_value_changed)

        self.custom_widget = line_edit
        self.widget().setMaximumWidth(140)

        bg_color = uiconsts.NODE_GRAPH_BACKGROUND_COLOR
        text_color = tuple(map(lambda i, j: i - j, (255, 255, 255), bg_color))
        text_sel_color = text_color
        style_dict = {
            "QLineEdit": {
                "background": "rgba({0},{1},{2},20)".format(*bg_color),
                "border": "1px solid rgb({0},{1},{2})".format(
                    *uiconsts.NODE_GRAPH_GRID_COLOR
                ),
                "border-radius": "3px",
                "color": "rgba({0},{1},{2},150)".format(*text_color),
                "selection-background-color": "rgba({0},{1},{2},100)".format(
                    *text_sel_color
                ),
            }
        }
        stylesheet = ""
        for css_class, css in style_dict.items():
            style = "{} {{\n".format(css_class)
            for elm_name, elm_val in css.items():
                style += "  {}:{};\n".format(elm_name, elm_val)
            style += "}\n"
            stylesheet += style
        line_edit.setStyleSheet(stylesheet)

    @property
    def widget_type(self) -> str:
        """
        Returns the type of the widget.

        :return: str
        """

        return "LineEditNodeWidget"

    def get_value(self) -> str:
        """
        Returns the value of the widget.

        :return: str
        """

        # noinspection PyTypeChecker
        line_edit: QLineEdit = self.custom_widget
        return str(line_edit.text())

    def set_value(self, text: str):
        """
        Sets the value of the widget.

        :param text: str
        """

        # noinspection PyTypeChecker
        line_edit: QLineEdit = self.custom_widget
        if text == self.get_value():
            return
        line_edit.setText(text)
        self._on_value_changed()


class NodeCheckBox(AbstractNodeWidget):
    """
    Class that displays a `QCheckBox` in a node.
    """

    def __init__(
        self,
        label: str = "",
        name: str | None = None,
        text: str = "",
        state: bool = False,
        parent: QGraphicsItem | None = None,
    ):
        super().__init__(label=label, name=name, parent=parent)

        check_box = QCheckBox(text)
        check_box.setChecked(state)
        check_box.setMinimumWidth(80)
        font = check_box.font()
        font.setPointSize(11)
        check_box.setFont(font)
        check_box.clearFocus()

        check_box.stateChanged.connect(self._on_value_changed)

        self.custom_widget = check_box
        self.widget().setMaximumWidth(140)

        text_color = tuple(
            map(
                lambda i, j: i - j,
                (255, 255, 255),
                uiconsts.NODE_GRAPH_BACKGROUND_COLOR,
            )
        )
        style_dict = {
            "QCheckBox": {
                "color": "rgba({0},{1},{2},150)".format(*text_color),
            }
        }
        stylesheet = ""
        for css_class, css in style_dict.items():
            style = "{} {{\n".format(css_class)
            for elm_name, elm_val in css.items():
                style += "  {}:{};\n".format(elm_name, elm_val)
            style += "}\n"
            stylesheet += style
        check_box.setStyleSheet(stylesheet)

    @property
    def widget_type(self) -> str:
        """
        Returns the type of the widget.

        :return: str
        """

        return "CheckBoxNodeWidget"

    def get_value(self) -> bool:
        """
        Returns the value of the widget.

        :return: bool
        """

        # noinspection PyTypeChecker
        check_box: QCheckBox = self.custom_widget
        return check_box.isChecked()

    def set_value(self, checked: bool):
        """
        Sets the value of the widget.

        :param checked: bool
        """

        # noinspection PyTypeChecker
        check_box: QCheckBox = self.custom_widget
        if checked == self.get_value():
            return
        check_box.setChecked(checked)
