from __future__ import annotations

import sys
import logging
import traceback
from typing import Iterator, Type, Any
from dataclasses import dataclass, field

from ..externals.Qt.QtCore import Signal, QObject
from ..externals.Qt.QtWidgets import QWidget, QLineEdit, QCheckBox,  QStackedWidget
from ..dcc import callback
from ..python import helpers, decorators, plugin
from ..qt import utils as qtutils
from ..qt.widgets import frameless, comboboxes, groups, lineedits, search

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
# noinspection SpellCheckingInspection
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


@dataclass
class UiData:
    """
    A data class for storing UI-related data for a tool.

    Attributes
    ----------
    label : str
        The label to be displayed for the UI element. Defaults to an empty string.
    icon : str
        The path to the icon to be used for the UI element. Defaults to an empty string.
    tooltip : str
        The tooltip text for the UI element. Defaults to an empty string.
    auto_link_properties : bool
        A flag indicating whether properties should be auto-linked. Defaults to False.
    """

    label: str = ''
    icon: str = ''
    tooltip: str = ''
    auto_link_properties: bool = False


@dataclass
class UiProperty:
    """
    A data class for storing property information for a UI element.

    Attributes
    ----------
    name : str
        The name of the property.
    value : Any, optional
        The current value of the property. Defaults to None.
    default : Any, optional
        The default value of the property. Defaults to None.
    """

    name: str
    value: Any = None
    default: Any = None


@dataclass
class UiPropertyGetSet:
    """
    A data class for storing getter and setter information for a UI property.

    Attributes
    ----------
    getter : str
        The name of the getter method for the property.
    setter : str
        The name of the setter method for the property.
    """

    getter: str
    setter: str


# noinspection SpellCheckingInspection
@dataclass
class UiPropertyWidgetUpdate:
    """
    A data class for storing information related to updating UI property widgets.

    Attributes
    ----------
    save_signal : str
        The name of the signal used to save changes in the UI property widget.
    getsets : list[UiPropertyGetSet], optional
        A list of UiPropertyGetSet instances representing getter and setter information for properties.
        Defaults to an empty list.
    skip_children : bool
        A flag indicating whether to skip updating child widgets. Defaults to True.
    """

    save_signal: str
    getsets: list[UiPropertyGetSet] = field(default_factory=lambda: [])
    skip_children: bool = True


SUPPORT_WIDGET_TYPES: dict[Type, UiPropertyWidgetUpdate] = {
    comboboxes.ComboBoxRegularWidget:
        UiPropertyWidgetUpdate('itemChanged', [UiPropertyGetSet('current_index', 'set_index')]),
    groups.RadioButtonGroup: UiPropertyWidgetUpdate('toggled', [UiPropertyGetSet('checked_index', 'set_checked')]),
    search.SearchLineEdit: UiPropertyWidgetUpdate('textChanged', [UiPropertyGetSet('text', 'setText')]),
    lineedits.BaseLineEdit: UiPropertyWidgetUpdate('textChanged', [UiPropertyGetSet('text', 'setText')]),
    lineedits.StringLineEditWidget: UiPropertyWidgetUpdate('textChanged', [UiPropertyGetSet('text', 'set_text')]),
    lineedits.FloatLineEditWidget: UiPropertyWidgetUpdate('textChanged', [UiPropertyGetSet('value', 'set_value')]),
    lineedits.IntLineEditWidget: UiPropertyWidgetUpdate('textChanged', [UiPropertyGetSet('value', 'set_value')]),
    QLineEdit: UiPropertyWidgetUpdate('textChanged', [UiPropertyGetSet('text', 'setText')]),
    QCheckBox: UiPropertyWidgetUpdate('toggled', [UiPropertyGetSet('isChecked', 'setChecked')])
}


class Tool(QObject):
    """
    Base class used by tp-dcc-tools framework to implement DCC tools that have access to tp-dcc-tools functionality.
    """

    ID: str = ''

    closed = Signal()

    def __init__(self, factory: plugin.PluginFactory | None = None):
        super(Tool, self).__init__()

        self._factory = factory
        self._stats = plugin.PluginStats(self)
        self._widgets: list[QWidget] = []
        self._properties: helpers.ObjectDict[str, UiProperty] = self.setup_properties()
        self._listeners: dict[str, callable] = {}
        self._stacked_widget: QStackedWidget | None = None
        self._show_warnings: bool = True
        self._block_save: bool = False
        self._closed = False
        self._callbacks = callback.FnCallback()

    # noinspection PyMethodParameters
    @decorators.classproperty
    def id(cls) -> str:
        """
        Gets the identifier associated with the class.

        This class property returns the identifier associated with the class.
        """

        return ''

    # noinspection PyMethodParameters
    @decorators.classproperty
    def creator(cls) -> str:
        """
        Gets the creator associated with the class.

        This class property returns the creator associated with the class.
        """

        return 'Tomi Poveda'

    @decorators.classproperty
    def ui_data(cls) -> UiData:
        """
        Gets the UI data associated with the class.

        This class property returns the UI data associated with the class.
        """

        return UiData()

    # noinspection PyMethodParameters
    @decorators.classproperty
    def tags(cls) -> list[str]:
        """
        Gets the tags associated with the class.

        This class property returns the tags associated with the class.
        """

        return []

    @property
    def stats(self) -> plugin.PluginStats:
        """
        Gets the statistics associated with the instance.

        This property returns the statistics associated with the instance.
        """

        return self._stats

    @property
    def properties(self) -> helpers.ObjectDict:
        """
        Gets the properties associated with the instance.

        This property returns the properties associated with the instance.
        """

        return self._properties

    @property
    def callbacks(self) -> callback.FnCallback:
        """
        Gets the callbacks associated with the instance.

        This property returns the callbacks associated with the instance.
        """

        return self._callbacks

    @staticmethod
    def widget_property_name(widget: QWidget) -> str:
        """
        Returns the property name associated with the given widget.

        This static method returns the property name associated with the given widget.

        :param widget: The widget for which to retrieve the property name.
        :return: The property name associated with the widget.
        """

        return widget.property('prop')

    # noinspection PyUnusedLocal
    def execute(self, *args, **kwargs) -> frameless.FramelessWindow:
        """
        Executes the tool with the specified arguments and keyword arguments.

        This method executes the function with the provided arguments and keyword arguments.

        :param args: Positional arguments to pass to the function.
        :param kwargs: Keyword arguments to pass to the function.
        :return: The frameless window resulting from the function execution.
        """

        win = frameless.FramelessWindow()
        win.closed.connect(self.closed.emit)
        win.set_title(self.ui_data.label)
        self._stacked_widget = QStackedWidget(parent=win)
        win.main_layout().addWidget(self._stacked_widget)

        self.pre_content_setup()

        for widget in self.contents():
            self._stacked_widget.addWidget(widget)
            self._widgets.append(widget)

        self.auto_link_properties()

        self.populate_widgets()
        self.post_content_setup()
        self.update_widgets_from_properties()
        self.save_properties()

        win.show()
        win.closed.connect(self._run_teardown)

        return win

    def widgets(self) -> list[QWidget]:
        """
        Returns a list of widgets associated with the instance.

        This method returns a list of widgets associated with the instance.

        :return: A list of widgets associated with the instance.
        """

        return self._widgets

    # noinspection PyMethodMayBeStatic
    def initialize_properties(self) -> list[UiProperty]:
        """
        Initializes the properties associated with the instance.

        This method initializes the properties associated with the instance.

        :return: A list of initialized UI properties.
        """

        return []

    def reset_properties(self, update_widgets: bool = True):
        """
        Resets the properties associated with the instance.

        This method resets the properties associated with the instance.

        :param update_widgets: A boolean indicating whether to update the widgets after resetting the properties.
            Defaults to True.
        """

        for ui_property in self.properties.values():
            ui_property.value = ui_property.default

        if update_widgets:
            self.update_widgets_from_properties()

    def setup_properties(self, properties: list[UiProperty] | None = None) -> helpers.ObjectDict:
        """
        Sets up the properties associated with the instance.

        This method sets up the properties associated with the instance.

        :param properties: An optional dictionary containing properties to set up. Defaults to None.
        :return: An ObjectDict containing the setup properties.
        """

        properties = properties or self.initialize_properties()
        tool_properties = helpers.ObjectDict()
        for ui_property in properties:
            tool_properties[ui_property.name] = ui_property
            if ui_property.default is None:
                ui_property.default = ui_property.value

        return tool_properties

    def auto_link_properties(self):
        """
        Auto link UI properties to widgets if allowed.
        """

        if not self.ui_data.auto_link_properties:
            return

        new_properties: list[UiProperty] = []
        names: list[str] = []

        for name, widget in self.iterate_linkable_properties(self._stacked_widget):
            skip_children = SUPPORT_WIDGET_TYPES.get(type(widget)).skip_children
            widget.setProperty('skipChildren', skip_children)
            if not self.link_property(widget, name):
                continue
            if name not in names:
                new_property = UiProperty(name)
                widget_values = self.widget_values(widget)
                for k, v in widget_values.items():
                    setattr(new_property, k, v)
                new_properties.append(new_property)
                names.append(name)

        new_props = self.setup_properties(new_properties)
        self.properties.update(new_props)

        for ui_property in new_properties:
            for listener in self._listeners.get(ui_property.name, []):
                listener(ui_property.value)

    def link_property(self, widget: QWidget, ui_property_name: str) -> bool:
        """
        Links a property to a widget.

        This method links a property to a widget.

        :param widget: The widget to link the property to.
        :param ui_property_name: The name of the UI property to link.
        :return: True if the property was successfully linked, False otherwise.
        """

        if self.widget_property_name(widget) is None:
            widget.setProperty('prop', ui_property_name)
            return True

        return False

    def iterate_linkable_properties(self, widget: QObject) -> Iterator[tuple[str, QWidget]]:
        """
        Iterates over linkable properties for the given widget.

        This method iterates over linkable properties for the given widget.

        :param widget: The widget to iterate over.
        :return: An iterator of tuples, each containing the name of a linkable property and the widget.
        """

        for attr in widget.__dict__:
            if type(getattr(widget, attr)) in SUPPORT_WIDGET_TYPES:
                yield attr, getattr(widget, attr)

        children = widget.children()
        for child in children:
            for attr in child.__dict__:
                if type(getattr(child, attr)) in SUPPORT_WIDGET_TYPES:
                    yield attr, getattr(child, attr)
            for grandchild in self.iterate_linkable_properties(child):
                yield grandchild

    def populate_widgets(self):
        """
        Makes the connection for all widgets linked to UI properties.
        """

        property_widgets = self.property_widgets()
        for widget in property_widgets:
            modified = False
            widget_type = type(widget)
            widget_name = self.widget_property_name(widget)
            widget_info: UiPropertyWidgetUpdate | None = SUPPORT_WIDGET_TYPES.get(widget_type)
            if widget_info:
                signal = getattr(widget, widget_info.save_signal)
                signal.connect(self.save_properties)
                modified = True

            if not modified and self._show_warnings:
                logger.warning(f'Unsupported widget: {widget}. Property: {widget_name}')

    def property_widgets(self) -> list[QWidget]:
        """
        Returns a list of property widgets associated with the instance.

        This method returns a list of property widgets associated with the instance.

        :return: A list of property widgets.
        """

        found_widgets: list[QWidget] = []
        for child in qtutils.iterate_children(self._stacked_widget, skip='skipChildren'):
            if child.property('prop') is not None:
                found_widgets.append(child)

        return found_widgets

    def widgets_linked_to_property(self, property_name: str) -> list[QWidget]:
        """
        Returns a list of widgets linked to the specified property.

        This method returns a list of widgets that are linked to the specified property.

        :param property_name: The name of the property to find linked widgets for.
        :return: A list of widgets linked to the specified property.
        """

        found_widgets: list[QWidget] = []
        for child in qtutils.iterate_children(self._stacked_widget, skip='skipChildren'):
            child_property = child.property('prop')
            if child_property is None or child_property != property_name:
                continue
            found_widgets.append(child)

        return found_widgets

    def update_widget(self, widget: QWidget):
        """
        Update given widget based on its linked UI property value.

        :param qt.QWidget widget: widget to update.
        """

        modified = False
        widget_type = type(widget)
        widget_name = self.widget_property_name(widget)
        widget_info: UiPropertyWidgetUpdate | None = SUPPORT_WIDGET_TYPES.get(widget_type)
        if widget_info:
            for i, getset in enumerate(widget_info.getsets):
                prop = 'value' if i == 0 else getset.getter
                value = getattr(self.properties[widget_name], prop)
                setter = getattr(widget, getset.setter)
                try:
                    setter(value)
                except TypeError as err:
                    raise TypeError(
                        f'Unable to set widget attribute method: {widget_name}; property: {getset.setter}; '
                        f'value: {value}: {err}')
                modified = True
        if not modified and self._show_warnings:
            logger.warning(f'Unsupported widget: {widget}. Property: {widget_name}')

    def update_widget_from_property(self, ui_property_name: str):
        """
        Updates the widget associated with the specified UI property.

        This method updates the widget associated with the specified UI property.

        :param ui_property_name: The name of the UI property to update the widget for.
        """

        self._stacked_widget.setUpdatesEnabled(False)
        self._block_save = True

        property_widgets = self.widgets_linked_to_property(ui_property_name)
        for widget in property_widgets:
            self.update_widget(widget)
        for widget in property_widgets:
            widget.blockSignals(False)

        self._block_save = False
        self._stacked_widget.setUpdatesEnabled(True)

    def update_widgets_from_properties(self):
        """
        Updates all widgets to current linked property internal value.
        """

        # self.block_callbacks(True)
        self._block_save = True
        self._stacked_widget.setUpdatesEnabled(False)

        property_widgets = self.property_widgets()
        for widget in property_widgets:
            self.update_widget(widget)
        for widget in property_widgets:
            widget.blockSignals(False)

        self._stacked_widget.setUpdatesEnabled(True)
        self._block_save = False
        # self.block_callbacks(False)

    def widget_values(self, widget: QWidget) -> dict[str, UiProperty]:
        """
        Gets the values of properties associated with the specified widget.

        This method retrieves the values of properties associated with the specified widget.

        :param widget: The widget to get property values for.
        :return: A dictionary where keys are property names and values are corresponding UiProperty instances.
        """

        widget_type = type(widget)
        widget_name = self.widget_property_name(widget)
        widget_info: UiPropertyWidgetUpdate | None = SUPPORT_WIDGET_TYPES.get(widget_type)
        if widget_info:
            result: dict[str, Any] = {}
            for i, getset in enumerate(widget_info.getsets):
                prop = 'value' if i == 0 else getset.getter
                result[prop] = getattr(widget, getset.getter)()

            extra_properties: dict = {}
            if isinstance(widget.property('extraProperties'), dict):
                extra_properties.update(widget.property('extraProperties'))
            for k, v in extra_properties.items():
                result[k] = getattr(widget, v)()

            return result

        if self._show_warnings:
            logger.warning(f'Unsupported widget: {widget}. Property: {widget_name}')

        return {}

    def save_properties(self):
        """
        Saves the properties from the widget into the internal UI attributes.
        """

        if self._block_save:
            return

        property_widgets = self.property_widgets()
        for widget in property_widgets:
            property_name = self.widget_property_name(widget)
            widget_values = self.widget_values(widget)
            for k, v in widget_values.items():
                setattr(self.properties[property_name], k, v)
            for listener in self._listeners.get(property_name, []):
                for k, v in widget_values.items():
                    if k == 'value':
                        listener(v)

    def update_property(self, ui_property_name: str, value: Any):
        """
        Updates the value of the specified UI property.

        This method updates the value of the specified UI property.

        :param ui_property_name: The name of the UI property to update.
        :param value: The new value for the UI property.
        """

        if ui_property_name not in self.properties:
            return
        self.properties[ui_property_name].value = value

        self.update_widget_from_property(ui_property_name)

        for listener in self._listeners.get(ui_property_name, []):
            listener(value)

    def listen(self, ui_property_name: str, listener: callable):
        """
        Registers a listener for changes to the specified UI property.

        This method registers a listener function to be called whenever the specified UI property changes.

        :param ui_property_name: The name of the UI property to listen for changes to.
        :param listener: The listener function to register.
        """

        self._listeners[ui_property_name] = self._listeners.get(ui_property_name, []) + [listener]

    def pre_content_setup(self):
        """
        Function that is called before tool UI is created.
        Can be override in tool subclasses.
        """

        pass

    # noinspection PyMethodMayBeStatic
    def contents(self) -> list[QWidget]:
        """
        Function that returns tool widgets.
        """

        return []

    def post_content_setup(self):
        """
        Function that is called after tool UI is created.
        Can be override in tool subclasses.
        """

        pass

    def teardown(self):
        """
        Function that shutdown tool.
        """

        self._callbacks.clear()

    def run(self):
        """
        Runs the tool.

        This method runs the tool.
        """

        pass

    def _execute(self, *args, **kwargs) -> Tool:
        """
        Internal function that executes tool in a safe way.
        """

        self.stats.start()
        exc_type, exc_value, exc_tb = None, None, None
        try:
            self.execute(*args, **kwargs)
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            raise
        finally:
            tb = None
            if exc_type and exc_value and exc_tb:
                tb = traceback.format_exception(exc_type, exc_value, exc_tb)
            self.stats.finish(tb)

        return self

    def _run_teardown(self):
        """
        Internal function that tries to tear down the tool in a safe way.
        """

        if self._closed:
            logger.warning(f'Tool f"{self}" already closed')
            return

        try:
            self.teardown()
            self._closed = True
        except RuntimeError:
            logger.error(f'Failed to teardown tool: {self.id}', exc_info=True)
