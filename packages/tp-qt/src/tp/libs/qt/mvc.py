from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Type, Iterator, Any

from Qt.QtCore import QObject
from Qt.QtWidgets import (
    QWidget,
    QCheckBox,
    QLineEdit,
    QPlainTextEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QProgressBar,
)

from tp.libs.python import helpers, collections

from .widgets import (
    comboboxes,
    checkboxes,
    groups,
    lineedits,
    search,
    stringedit,
    labels,
)

logger = logging.getLogger(__name__)


@dataclass
class UiProperty:
    """A data class for storing property information for a UI element.

    Attributes:
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
    type: Type | None = None


@dataclass
class UiPropertyGetSet:
    """A data class for storing getter and setter information for a UI property.

    Attributes:
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
    """A data class for storing information related to updating UI property widgets.

    Attributes:
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


class WidgetRegistrationError(Exception):
    """Exception raised when a widget type is already registered."""

    pass


class WidgetNotRegisteredError(Exception):
    """Exception raised when a widget type is not registered."""

    pass


class WidgetManager:
    """Class that manages widget types and their associated UiPropertyWidgetUpdate configurations."""

    _INSTANCE: WidgetManager | None = None

    def __new__(cls, *args, **kwargs):
        if cls._INSTANCE is None:
            cls._INSTANCE = super().__new__(cls, *args, **kwargs)
            cls._INSTANCE._initialized = False
            logger.debug("WidgetManager singleton instance created.")

        return cls._INSTANCE

    def __init__(self):
        # Avoid reinitialization of the singleton instance after the first initialization.
        if self._initialized:
            return

        # Dictionary to store widget types and their UiPropertyWidgetUpdate configurations
        self._widget_updates: dict[Type, UiPropertyWidgetUpdate] = {}
        self._initialized = True

        self._register_default_widgets()

    def register_widget_update(self, widget_type: Type, update: UiPropertyWidgetUpdate):
        """Register a new widget type with its associated UiPropertyWidgetUpdate configuration.
        Avoids duplicate registrations.

        :param widget_type: The widget class/type to register.
        :param update: The UiPropertyWidgetUpdate configuration for the widget.
        :raises WidgetRegistrationError: If the widget type is already registered.
        """

        if widget_type in self._widget_updates:
            logger.error(
                f"Attempt to register duplicate widget type: {widget_type.__name__}"
            )
            raise WidgetRegistrationError(
                f"Widget type {widget_type.__name__} is already registered."
            )

        self._widget_updates[widget_type] = update
        logger.debug(
            f"Registered widget type: {widget_type.__name__} with event: {update}"
        )

    def get_widget_update(self, widget_type: Type) -> UiPropertyWidgetUpdate:
        """Retrieve the UiPropertyWidgetUpdate configuration for a given widget type.

        :param widget_type: The widget class/type to look up.
        :return: The UiPropertyWidgetUpdate for the widget type if registered.
        :raises WidgetNotRegisteredError: If the widget type is not registered.
        """

        # Direct lookup for registered widget type.
        if widget_type in self._widget_updates:
            logger.debug(
                f"Directly retrieved widget update for: {widget_type.__name__}"
            )
            return self._widget_updates[widget_type]

        # Attempt to find a registered superclass.
        for registered_type, update in self._widget_updates.items():
            if issubclass(widget_type, registered_type):
                logger.debug(
                    f"Retrieved widget update for {widget_type.__name__} via superclass {registered_type.__name__}"
                )
                return update

        # If no match is found, raise an error.
        logger.error(
            f"Widget type {widget_type.__name__} or any of its superclasses is not registered."
        )
        raise WidgetNotRegisteredError(
            f"Widget type {widget_type.__name__} or its superclasses are not registered."
        )

    def unregister_widget(self, widget_type: Type):
        """Unregister a widget type if it is registered.

        :param widget_type: The widget class/type to remove from registration.
        :raises WidgetNotRegisteredError: If the widget type is not registered.
        """

        if widget_type not in self._widget_updates:
            logger.error(
                f"Attempt to unregister non-existent widget type: {widget_type.__name__}"
            )
            raise WidgetNotRegisteredError(
                f"Widget type {widget_type.__name__} is not registered."
            )

        del self._widget_updates[widget_type]
        logger.debug(f"Unregistered widget type: {widget_type.__name__}")

    def iterate_registered_widgets(self) -> Iterator[Type]:
        """Provides an iterator over all registered widget types.

        :return: An iterator over the registered widget types.
        """

        return iter(self._widget_updates.keys())

    def registered_widgets(self) -> list[Type]:
        """Returns a list of all registered widget types.

        :return: A list of all registered widget types.
        """

        return list(self._widget_updates.keys())

    def _register_default_widgets(self):
        """Registers a set of default widget types and their associated configurations."""

        default_widgets: dict[Type, UiPropertyWidgetUpdate] = {
            QCheckBox: UiPropertyWidgetUpdate(
                "toggled", [UiPropertyGetSet("isChecked", "setChecked")]
            ),
            QLineEdit: UiPropertyWidgetUpdate(
                "textChanged", [UiPropertyGetSet("text", "setText")]
            ),
            QPlainTextEdit: UiPropertyWidgetUpdate(
                "textChanged", [UiPropertyGetSet("toPlainText", "setPlainText")]
            ),
            QComboBox: UiPropertyWidgetUpdate(
                "itemChanged", [UiPropertyGetSet("currentIndex", "setCurrentIndex")]
            ),
            QSpinBox: UiPropertyWidgetUpdate(
                "valueChanged", [UiPropertyGetSet("value", "setValue")]
            ),
            QDoubleSpinBox: UiPropertyWidgetUpdate(
                "valueChanged", [UiPropertyGetSet("value", "setValue")]
            ),
            QProgressBar: UiPropertyWidgetUpdate(
                "valueChanged", [UiPropertyGetSet("value", "setValue")]
            ),
            checkboxes.BaseCheckBoxWidget: UiPropertyWidgetUpdate(
                "stateChanged", [UiPropertyGetSet("isChecked", "setChecked")]
            ),
            comboboxes.BaseComboBox: UiPropertyWidgetUpdate(
                "currentIndexChanged",
                [UiPropertyGetSet("currentIndex", "setCurrentIndex")],
            ),
            comboboxes.ComboBoxRegularWidget: UiPropertyWidgetUpdate(
                "itemChanged", [UiPropertyGetSet("current_index", "set_index")]
            ),
            comboboxes.ComboBoxSearchableWidget: UiPropertyWidgetUpdate(
                "itemChanged", [UiPropertyGetSet("current_index", "set_index")]
            ),
            groups.RadioButtonGroup: UiPropertyWidgetUpdate(
                "toggled", [UiPropertyGetSet("checked_index", "set_checked")]
            ),
            search.SearchLineEdit: UiPropertyWidgetUpdate(
                "textChanged", [UiPropertyGetSet("text", "setText")]
            ),
            lineedits.BaseLineEdit: UiPropertyWidgetUpdate(
                "textChanged", [UiPropertyGetSet("text", "setText")]
            ),
            lineedits.StringLineEditWidget: UiPropertyWidgetUpdate(
                "textChanged", [UiPropertyGetSet("text", "set_text")]
            ),
            lineedits.FloatLineEditWidget: UiPropertyWidgetUpdate(
                "textChanged", [UiPropertyGetSet("value", "set_value")]
            ),
            lineedits.IntLineEditWidget: UiPropertyWidgetUpdate(
                "textChanged", [UiPropertyGetSet("value", "set_value")]
            ),
            stringedit.StringEdit: UiPropertyWidgetUpdate(
                "textChanged", [UiPropertyGetSet("text", "set_text")]
            ),
            stringedit.IntEdit: UiPropertyWidgetUpdate(
                "textChanged", [UiPropertyGetSet("text", "set_text")]
            ),
            stringedit.FloatEdit: UiPropertyWidgetUpdate(
                "textChanged", [UiPropertyGetSet("text", "set_text")]
            ),
            labels.BaseLabel: UiPropertyWidgetUpdate(
                "textChanged", [UiPropertyGetSet("text", "setText")]
            ),
        }

        for widget_type, update in default_widgets.items():
            try:
                self.register_widget_update(widget_type, update)
            except WidgetRegistrationError as e:
                logger.error(
                    f"Failed to register widget type {widget_type.__name__}: {e}"
                )


class Model(QObject):
    """Class that exposes functions to store data and handles data updates automatically when UI is changed."""

    def __init__(self):
        super().__init__()

        self._widgets = collections.WeakRefList()
        self._properties: helpers.ObjectDict[str, UiProperty] = self.setup_properties()
        self._listeners: dict[str, callable] = {}
        self._show_warnings: bool = True
        self._block_save: bool = False

    @property
    def properties(self) -> helpers.ObjectDict:
        """Gets the properties associated with the instance.

        This property returns the properties associated with the instance.
        """

        return self._properties

    @staticmethod
    def widget_property_name(widget: QWidget) -> str:
        """Returns the property name associated with the given widget.

        This static method returns the property name associated with the given widget.

        :param widget: The widget for which to retrieve the property name.
        :return: The property name associated with the widget.
        """

        return widget.property("prop")

    # noinspection PyMethodMayBeStatic
    def initialize_properties(self) -> list[UiProperty]:
        """Initializes the properties associated with the instance.

        This method initializes the properties associated with the instance.

        :return: A list of initialized UI properties.
        """

        return []

    def setup_properties(
        self, properties: list[UiProperty] | None = None
    ) -> helpers.ObjectDict:
        """Sets up the properties associated with the instance.

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

    def link_property(self, widget: QWidget, ui_property_name: str) -> bool:
        """Links a property to a widget.

        This method links a property to a widget.

        :param widget: The widget to link the property to.
        :param ui_property_name: The name of the UI property to link.
        :return: True if the property was successfully linked, False otherwise.
        """

        widgets = [widget for widget in self._widgets]
        if widget in widgets:
            return False

        modified = False
        widget_type = type(widget)
        widget_info: UiPropertyWidgetUpdate | None = WidgetManager().get_widget_update(
            widget_type
        )
        if widget_info:
            signal = getattr(widget, widget_info.save_signal)
            signal.connect(self.save_properties)
            modified = True

        if not modified and self._show_warnings:
            logger.warning(
                f"Unsupported widget: {widget}. Property: {ui_property_name}"
            )
            return False

        widget.setProperty("prop", ui_property_name)
        self._widgets.append(widget)

        return True

    def iterate_linkable_properties(
        self, widget: QObject
    ) -> Iterator[tuple[str, QWidget]]:
        """Iterates over linkable properties for the given widget.

        This method iterates over linkable properties for the given widget.

        :param widget: The widget to iterate over.
        :return: An iterator of tuples, each containing the name of a linkable property and the widget.
        """

        for attr in widget.__dict__:
            if type(getattr(widget, attr)) in WidgetManager().registered_widgets():
                yield attr, getattr(widget, attr)

        children = widget.children()
        for child in children:
            for attr in child.__dict__:
                if type(getattr(child, attr)) in WidgetManager().registered_widgets():
                    yield attr, getattr(child, attr)
            for grandchild in self.iterate_linkable_properties(child):
                yield grandchild

    def property_widgets(self) -> list[QWidget]:
        """Returns a list of property widgets associated with the instance.

        This method returns a list of property widgets associated with the instance.

        :return: A list of property widgets.
        """

        return [widget for widget in self._widgets]

    def reset_properties(self, update_widgets: bool = True):
        """Resets the properties associated with the instance.

        This method resets the properties associated with the instance.

        :param update_widgets: A boolean indicating whether to update the widgets after resetting the properties.
            Defaults to True.
        """

        for ui_property in self.properties.values():
            ui_property.value = ui_property.default

        if update_widgets:
            self.update_widgets_from_properties()

    def widgets_linked_to_property(self, property_name: str) -> list[QWidget]:
        """Returns a list of widgets linked to the specified property.

        This method returns a list of widgets that are linked to the specified property.

        :param property_name: The name of the property to find linked widgets for.
        :return: A list of widgets linked to the specified property.
        """

        found_widgets: list[QWidget] = []
        for widget in self._widgets:
            child_property = widget.property("prop")
            if child_property is None or child_property != property_name:
                continue
            found_widgets.append(widget)

        return found_widgets

    def update_widget(self, widget: QWidget):
        """Update given widget based on its linked UI property value.

        :param qt.QWidget widget: widget to update.
        """

        modified = False
        widget_type = type(widget)
        widget_name = self.widget_property_name(widget)
        widget_info: UiPropertyWidgetUpdate | None = WidgetManager().get_widget_update(
            widget_type
        )
        if widget_info:
            for i, getset in enumerate(widget_info.getsets):
                prop = "value" if i == 0 else getset.getter
                value = getattr(self.properties[widget_name], prop)
                setter = getattr(widget, getset.setter)
                try:
                    setter(value)
                except TypeError as err:
                    raise TypeError(
                        f"Unable to set widget attribute method: {widget_name}; property: {getset.setter}; "
                        f"value: {value}: {err}"
                    )
                modified = True
        if not modified and self._show_warnings:
            logger.warning(f"Unsupported widget: {widget}. Property: {widget_name}")

    def update_widget_from_property(self, ui_property_name: str):
        """Updates the widget associated with the specified UI property.

        This method updates the widget associated with the specified UI property.

        :param ui_property_name: The name of the UI property to update the widget for.
        """

        self._block_save = True

        property_widgets = self.widgets_linked_to_property(ui_property_name)
        for widget in property_widgets:
            self.update_widget(widget)
        for widget in property_widgets:
            widget.blockSignals(False)

        self._block_save = False

    def update_widgets_from_properties(self):
        """Updates all widgets to current linked property internal value."""

        # self.block_callbacks(True)
        self._block_save = True
        try:
            property_widgets = self.property_widgets()
            for widget in property_widgets:
                self.update_widget(widget)
            for widget in property_widgets:
                widget.blockSignals(False)
        finally:
            self._block_save = False
        # self.block_callbacks(False)

        for property_name, listeners in self._listeners.items():
            for listener in listeners:
                listener(self.properties[property_name].value)

    def widget_values(self, widget: QWidget) -> dict[str, UiProperty]:
        """Gets the values of properties associated with the specified widget.

        This method retrieves the values of properties associated with the specified widget.

        :param widget: The widget to get property values for.
        :return: A dictionary where keys are property names and values are corresponding UiProperty instances.
        """

        widget_type = type(widget)
        widget_name = self.widget_property_name(widget)
        widget_info: UiPropertyWidgetUpdate | None = WidgetManager().get_widget_update(
            widget_type
        )
        if widget_info:
            result: dict[str, Any] = {}
            for i, getset in enumerate(widget_info.getsets):
                prop = "value" if i == 0 else getset.getter
                result[prop] = getattr(widget, getset.getter)()

            extra_properties: dict = {}
            if isinstance(widget.property("extraProperties"), dict):
                extra_properties.update(widget.property("extraProperties"))
            for k, v in extra_properties.items():
                result[k] = getattr(widget, v)()

            return result

        if self._show_warnings:
            logger.warning(f"Unsupported widget: {widget}. Property: {widget_name}")

        return {}

    def save_properties(self):
        """Saves the properties from the widget into the internal UI attributes."""

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
                    if k == "value":
                        listener(v)

    def update_property(self, ui_property_name: str, value: Any):
        """Updates the value of the specified UI property.

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
        """Registers a listener for changes to the specified UI property.

        This method registers a listener function to be called whenever the specified UI property changes.

        :param ui_property_name: The name of the UI property to listen for changes to.
        :param listener: The listener function to register.
        """

        self._listeners[ui_property_name] = self._listeners.get(
            ui_property_name, []
        ) + [listener]


class Controller(QObject):
    """Simple Controller class that handles all DCC specific logic code
    should be handled by a controller."""

    def __init__(self, model: Model):
        super().__init__()

        self.setup_model(model)

    def setup_model(self, model: Model) -> None:
        """Sets up the model associated with the controller.

        This method sets up the model associated with the controller.

        Args:
            model: The model to associate with the controller.
        """

        pass
