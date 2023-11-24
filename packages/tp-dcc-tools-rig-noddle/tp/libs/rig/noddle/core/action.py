from __future__ import annotations

import os
import re
import sys
import fnmatch
import logging
import importlib
from typing import Any
from typing import Iterator
from types import ModuleType

from overrides import override

from tp.core import log
from tp.common.python import decorators
from tp.libs.rig.noddle.core import colors, serializer

logger = log.rigLogger


def load_actions():
    """
    Loads all available actions.
    """

    BuildActionPackageRegistry().load_actions()


def reload_actions():
    """
    Clears all loaded actions from the registry and load actions again.
    """

    BuildActionPackageRegistry().reload_actions()


@decorators.add_metaclass(decorators.Singleton)
class BuildActionRegistry:
    """
    Registry class that contains all build actions available for use.
    """

    def __init__(self):
        self._action_specs: dict[str, BuildActionSpec] = {}

    def add_action(self, action_spec: BuildActionSpec):
        """
        Adds a BuildActionSpec to the manager.

        :param BuildActionSpec action_spec: build action spec to register.
        """

        if not action_spec.is_valid():
            logger.error(f'Build Action spec is not valid: {action_spec}')
            return

        action_id = action_spec.id
        if action_id in self._action_specs:
            if self._action_specs[action_id].is_equal(action_spec):
                return
            else:
                logger.error(f'A BuildAction already exists with ID: {action_id}')
                return

        self._action_specs[action_id] = action_spec

    def find_action(self, action_id: str) -> BuildActionSpec | None:
        """
        Finds a BuildActionSpec with given ID.

        :param str action_id: build action spec ID to find.
        :return: found build action spec.
        :rtype: BuildActionSpec or None
        """

        return self._action_specs.get(action_id, None)

    def find_action_by_class(self, action_class: type[BuildAction]) -> BuildActionSpec | None:
        """
        Finds a BuildActionSpec with given class.

        :param type[BuildAction] action_class: build action class to find.
        :return: found build action spec.
        :rtype: BuildActionSpec or None
        """

        found_build_spec: BuildActionSpec | None = None
        for spec in self._action_specs.values():
            if spec.action_class == action_class:
                found_build_spec = spec
                break

        return found_build_spec

    def remove_action(self, action_id: str):
        """
        Removes a BuildActionSpec with given ID.

        :param str action_id: Build Action ID we want to remove.
        """

        if action_id not in self._action_specs:
            return

        del self._action_specs[action_id]

    def remove_all(self):
        """
        Remove all actions from this registry.
        """

        self._action_specs.clear()


@decorators.add_metaclass(decorators.Singleton)
class BuildActionPackageRegistry:
    """
    Registry class that contains packages where actions should be loaded.
    Also keep tracks whether all packages have been loaded and allows to reload of packages when necessary.
    """

    def __init__(self):
        self._registered_actions: dict[str, BuildActionSpec] = {}
        self._action_packages: list[ModuleType] = []
        self._use_builtin_actions = True
        self._has_loaded_actions = False

        if self._use_builtin_actions:
            self._add_builtin_actions()

    @property
    def registered_actions(self) -> dict[str, BuildActionSpec]:
        """
        Getter method that returns a map of all registered actions by ID.

        :return: registered actions.
        :rtype: dict[str, BuildActionSpec]
        """

        return self._registered_actions

    @property
    def action_packages(self) -> list[ModuleType]:
        """
        Getter method that returns a list of Python package containing Noddle actions to load.

        :return: list of packages.
        :rtype: list[ModuleType]
        """

        return self._action_packages

    def add_package(self, package: ModuleType, reload: bool = False):
        """
        Adds an actions package to the registry.

        :param ModuleType package: package to load actions from.
        :param bool reload: whether to reload actions.
        """

        if package not in self._action_packages:
            self._action_packages.append(package)

        if reload:
            self.reload_actions()

    def load_actions(self):
        """
        Loads all available Noddle actions.
        """

        if self._has_loaded_actions:
            return

        loader = BuildActionLoader()

        for package in self._action_packages:
            loader.load_actions_from_package(package)

        self._has_loaded_actions = True

    def reload_actions(self):
        """
        Clears all loaded actions from the registry and load actions again.
        """

        BuildActionRegistry().remove_all()
        self._has_loaded_actions = False
        self.load_actions()

    def remove_all(self, reload: bool = False):
        """
        Removes all registered action packages.

        :param bool reload: whether to reload actions.
        """

        self._action_packages.clear()

        if self._use_builtin_actions:
            self._add_builtin_actions()

        if reload:
            self.reload_actions()

    def _add_builtin_actions(self):
        """
        Internal function that registers builtin Noddle actions.
        """

        from tp.libs.rig.noddle import actions
        self.add_package(actions)


class BuildActionLoader:
    """
    Helper class that handles the finding nad build loading of build action modules and returns then as BuildActionSpec
    objects.
    """

    def __init__(self, use_registry: bool = True):
        super().__init__()

        self._use_registry = use_registry

    @staticmethod
    def import_all_submodules(package_name: str):
        """
        Imports all Python modules within given package recursively.

        :param str package_name: name of Python package where verything will be imported.
        """

        package_module = sys.modules[package_name]
        package_path = package_module.__path__[0]

        for base_dir, _, file_names in os.walk(package_path):
            if os.path.basename(base_dir) in ('__pycache__',):
                continue
            sub_package_name = os.path.relpath(base_dir, package_path).replace('/', '.').replace('\\', '.')
            for file_name in file_names:
                if file_name in ('__init__.py', '__main__.py'):
                    continue
                if not fnmatch.fnmatch(file_name, '*.py'):
                    continue
                module_name = os.path.splitext(file_name)[0]
                sub_module_name = f'.{sub_package_name}.{module_name}'
                importlib.import_module(sub_module_name, package_name)

    def register_actions(self, action_specs: list[BuildActionSpec]):
        """
        Registers given action specs.

        :param list[BuildActionSpec] action_specs: list of build action specs to register.
        """

        for action_spec in action_specs:
            BuildActionRegistry().add_action(action_spec)

    def load_actions_from_package(self, package: ModuleType) -> list[BuildActionSpec]:
        """
        Recursive function that finds all Noddle actions in a Python package.

        :param ModuleType package: Python package containing BuildAction classes.
        :return: list of build action specs retrieve from package or module.
        :rtype: list[BuildActionSpec]
        """

        def _is_module(_obj: Any) -> bool:
            """
            Internal function that returns whether given object is a Python module.

            :param Any _obj: Python object to check.
            :return: True if given object is a Python module; False otherwise.
            :rtype: bool
            """

            return isinstance(_obj, ModuleType)

        def _is_submodule(_obj: Any, _parent_module: ModuleType) -> bool:
            """
            Internal function that returns whether given object is submodule of the given parent Python module.

            :param Any _obj: Python object to check.
            :param ModuleType _parent_module: parent Python module to check.
            :return: True if given Python object is a submodule of the given parent Python module; False otherwise.
            :rtype: bool
            """

            _parent_name = _parent_module.__name__
            if _is_module(_obj):
                if _obj.__name__ == _parent_name:
                    return False
                if not _obj.__package__:
                    return False
                return _obj.__package__ == _parent_name or _obj.__package__.startswith(f'{_parent_name}')

        def _is_valid_build_action_class(_obj: Any) -> bool:
            """
            Returns whether given Python object is a valid BuildAction subclass.

            :param Any _obj: Python object to check.
            :return: True if given Python object is a valid BuildAction subclass; False otherwise.
            :rtype: bool
            """

            return isinstance(_obj, type) and issubclass(_obj, BuildAction) and _obj is not BuildAction

        def _load_actions_from_module(_module: ModuleType) -> list[BuildActionSpec]:
            """
            Internal function that performs the actual recursive loading of actions within a package or module.

            :param ModuleType _module: Python module or package containing BuildAction classes.
            :return: list of build action specs retrieve from package or module.
            :rtype: list[BuildActionSpec]
            """

            _action_specs: list[BuildActionSpec] = []
            for _name in dir(_module):
                _obj = getattr(_module, _name)
                if _is_submodule(_obj, _module):
                    _action_specs.extend(_load_actions_from_module(_obj))
                elif _is_valid_build_action_class(_obj):
                    _action_spec = BuildActionSpec(_obj, _module)
                    _action_specs.append(_action_spec)

            if self._use_registry:
                self.register_actions(_action_specs)

            return _action_specs

        logger.info(f'Loading Noddle Actions from package: {package}')
        return _load_actions_from_module(package)




class BuildActionSpec:
    """
    Class that contains information about a registered build action class and its configuration.
    """

    def __init__(self, action_class: type[BuildAction], module: ModuleType):
        super().__init__()

        self._action_class = action_class
        self._module = module

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} "{self.id}">'

    @property
    def action_class(self) -> type[BuildAction]:
        """
        Getter method that returns the build action class associated with this build action specification.

        :return: build action instance.
        :rtype: type[BuildAction]
        """

        return self._action_class

    @property
    def id(self) -> str:
        """
        Getter method that returns the unique action ID.

        :return: unique action ID.
        :rtype: str
        """

        return self._action_class.id if self._action_class else None

    @property
    def display_name(self) -> str:
        """
        Getter method that returns the display name of the action.

        :return: action display name.
        :rtype: str
        """

        return self._action_class.display_name if self._action_class else None

    @property
    def description(self) -> str:
        """
        Getter method that returns the description of the action.

        :return: action description.
        :rtype: str
        """

        doc = self._action_class.__doc__ if self._action_class else ''
        return doc.strip().split('\n')[0] if doc else ''

    @property
    def color(self) -> tuple[int, int, int]:
        """
        Getter method that returns the color of the action.

        :return: action color.
        :rtype: str
        """

        return self._action_class.color if self._action_class else (1, 1, 1)

    @property
    def category(self) -> str:
        """
        Getter method that returns the category of the action.

        :return: action category.
        :rtype: str
        """

        return self._action_class.category if self._action_class else 'General'

    @property
    def attributes(self) -> list[dict]:
        """
        Getter method that returns list with all attribute definitions of the action.

        :return: action attribute definitions.
        :rtype: list[dict]
        """

        return self._action_class.attribute_definitions if self._action_class else []

    def is_valid(self) -> bool:
        """
        Returns whether build action specification instance is valid.

        :return: True if build action specification is valid; False otherwise.
        :rtype: bool
        """

        return self._action_class is not None and self.id

    def is_equal(self, other: BuildActionSpec) -> bool:
        """
        Returns whether this action spec is the same as another one.

        :param BuildActionSpec other: build action specification instance to compare with.
        :return: True if given build action specification and this instance are equal; False otherwise.
        :rtype: bool
        """

        return self._action_class == other._action_class


class BuildActionAttribute:
    """
    A single attribute of a build action.
    This class contains the attribute configuration as well as current valud and validation logic.

    This class should not be instantiated directly but using `BuildActionAttribute.from_spec()` to ensure that
    appropriate subclass will be instanced based on the attribute type, since each subclass has its own validation
    logic.
    """

    class Type:
        Unknown = None
        Bool = 'bool'
        Int = 'int'
        Float = 'float'
        Vector3 = 'vector3'
        String = 'string'
        StringList = 'stringlist'
        Option = 'option'
        Node = 'node'
        NodeList = 'nodelist'
        File = 'file'

    # The attribute type that this class is designed to handle.
    class_attribute_type: str = Type.Unknown

    # Cached map of attribute types to BuildActionAttribute for faster lookup
    _attributes_class_map: dict[str, type[BuildActionAttribute]] = {}

    def __init__(self, name: str, action_spec: BuildActionSpec | None = None, action_id: str | None = None):
        super().__init__()

        self._name = name
        self._action_spec = action_spec
        self._action_id = self._action_spec.id if self._action_spec is not None else action_id
        self._attr_config: dict | None = None
        self._value: Any = None
        self._is_valid = True
        self._invalid_reason: str | None = None

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} "{self.action_id}.{self.name}">'

    @classmethod
    def from_spec(
            cls, name: str, action_spec: BuildActionSpec | None = None,
            action_id: str | None = None) -> BuildActionAttribute:
        """
        Creates a BuildActionAttribute instance from a name and a build action specification instance, using the
        appropriate class based on the attribute type.

        :param str name: name of the attribute.
        :param BuildActionSpec or None action_spec: build action specification.
        :param str or None action_id: optional action ID.
        :return: new build action attribute instance.
        :rtype: BuildActionAttribute
        """

        attr_type: str = cls._find_attribute_config(name, action_spec).get('type')
        subclass: type[BuildActionAttribute] | None = cls._find_attribute_class(attr_type)
        if subclass is not None:
            return subclass(name, action_spec, action_id)

        return BuildActionAttribute(name, action_spec, action_id)

    @property
    def name(self) -> str:
        """
        Getter method that returns the name of the attribute.

        :return: attribute name.
        :rtype: str
        """

        return self._name

    @property
    def action_spec(self) -> BuildActionSpec | None:
        """
        Getter method that returns the action specification with the attributes definitions.

        :return: action specification.
        :rtype: BuildActionSpec or None
        """

        return self._action_spec

    @property
    def action_id(self) -> str:
        """
        Getter method that returns the action ID of the specification.

        :return: specification action ID.
        :rtype: str
        """

        return self._action_id

    @property
    def config(self) -> dict:
        """
        Getter method that returns the configuration for this attribute.

        :return: attribute configuration.
        :rtype: dict
        """

        if self._attr_config is None:
            self._attr_config = self._find_attribute_config(self.name, self.action_spec)

        return self._attr_config

    @property
    def is_valid(self) -> bool:
        """
        Getter method that returns whether current value of this attribute is valid.

        :return: True if value is valid; False otherwise.
        :rtype: bool
        ..info:: `validate` function should be called first to check the value. `invalid_reason property can be
            accessed to determine why the attribute is invalid if applicable.`
        """

        return self._is_valid

    @property
    def invalid_reason(self) -> str | None:
        """
        Getter method that returns why the value is invalid.

        :return: invalid reason.
        :rtype: str or None
        """

        return self._invalid_reason

    def validate(self):
        """
        Validates the attribute, checking its current value and other requirements and storing the reason it is invalid
        if applicable.
        """

        if self.class_attribute_type == BuildActionAttribute.Type.Unknown:
            self._is_valid = False
            self._invalid_reason = 'unknown_type'
        else:
            self._is_valid = True
            self._invalid_reason = None

    def clear_value(self):
        """
        Clears the assigned value of this attribute, resetting it to the default value.
        """

        self._value = None

    @staticmethod
    def _find_attribute_config(attribute_name: str, action_spec: BuildActionSpec) -> dict:
        """
        Internal function that finds and returns the configuration for an attribute from an action specification.

        :param str attribute_name: name of the attribute.
        :param action_spec: action specification.
        :return: attribute configuration.
        :rtype: dict
        """

        if not action_spec:
            return {}

        found_attr_config: dict | None = None
        attrs_config = action_spec.attributes
        for attr_config in attrs_config:
            if attr_config.get('name') == attribute_name:
                found_attr_config = attr_config
                break

        return found_attr_config

    @classmethod
    def _find_attribute_class(cls, attribute_type: str) -> type[BuildActionAttribute] | None:
        """
        Internal function that returns the build action attribute class to use based on the given attribute type.

        :param str attribute_type: attribute type name.
        :return: build action attribute class.
        :rtype: type[BuildActionAttribute] or None
        """

        if attribute_type in cls._attributes_class_map:
            return cls._attributes_class_map[attribute_type]

        found_subclass: type[BuildActionAttribute] | None = None
        for subclass in cls.__subclasses__():
            if subclass.class_attribute_type == attribute_type:
                cls._attributes_class_map[attribute_type] = subclass
                found_subclass = subclass
                break

        return found_subclass


class BuildActionBoolAttribute(BuildActionAttribute):
    """
    Boolean attribute for build actions.
    """

    class_attribute_type = BuildActionAttribute.Type.Bool


class BuildActionIntAttribute(BuildActionAttribute):
    """
    Integer attribute for build actions.
    """

    class_attribute_type = BuildActionAttribute.Type.Int


class BuildActionFloatAttribute(BuildActionAttribute):
    """
    Float attribute for build actions.
    """

    class_attribute_type = BuildActionAttribute.Type.Float


class BuildActionVector3Attribute(BuildActionAttribute):
    """
    Vector3 attribute for build actions.
    """

    class_attribute_type = BuildActionAttribute.Type.Vector3


class BuildActionStringAttribute(BuildActionAttribute):
    """
    String attribute for build actions.
    """

    class_attribute_type = BuildActionAttribute.Type.String


class BuildActionStringListAttribute(BuildActionAttribute):
    """
    String list attribute for build actions.
    """

    class_attribute_type = BuildActionAttribute.Type.StringList


class BuildActionOptionAttribute(BuildActionAttribute):
    """
    Option attribute for build actions.
    """

    class_attribute_type = BuildActionAttribute.Type.Option


class BuildActionNodeAttribute(BuildActionAttribute):
    """
    Node attribute for build actions.
    """

    class_attribute_type = BuildActionAttribute.Type.Node


class BuildActionNodeListAttribute(BuildActionAttribute):
    """
    Node list attribute for build actions.
    """

    class_attribute_type = BuildActionAttribute.Type.NodeList


class BuildActionFileAttribute(BuildActionAttribute):
    """
    File attribute for build actions.
    """

    class_attribute_type = BuildActionAttribute.Type.File


class BuildActionData:
    """
    Class that holds attribute values for an action to be executed during a build step.
    """

    def __init__(self, action_id: str | None = None):
        super().__init__()

        self._action_id = action_id
        self._spec: BuildActionSpec | None = None
        self._is_missing_spec = False
        self._attributes: dict[str, BuildActionAttribute] = {}

        self.find_spec()

        self._init_attributes()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} "{self._action_id}"'

    @property
    def action_id(self) -> str:
        """
        Getter method that returns the unique ID for this action, which is used to identify the action when serialized.
        :return: unique action ID.
        :rtype: str
        """

        return self._action_id

    @property
    def spec(self) -> BuildActionSpec | None:
        """
        Getter method that returns the build action specification that contains action configuration for this action
        data.

        :return: action data build action specification.
        :rtype: BuildActionSpec or None
        """

        return self._spec

    @property
    def is_missing_spec(self) -> bool:
        """
        Getter method that returns whether action ID is set but no specification is set.

        :return: True if specification is not set; False otherwise.
        :rtype: bool
        """

        return self._is_missing_spec

    @property
    def attributes(self) -> dict[str, BuildActionAttribute]:
        """
        Getter method that returns the dictionary that maps attribute names with their build action attribute.

        :return: build action attributes mapping.
        :rtype: dict[str, BuildActionAttribute]
        """

        return self._attributes

    def is_valid(self) -> bool:
        """
        Returns whether there is not a build action specification associated to this build action data.

        :return: True if build action specification is assigned; False otherwise.
        :rtype: bool
        """

        return self._spec is not None

    def is_action_id_valid(self) -> bool:
        """
        Returns whether action ID is defined for this build action.

        :return: True if action ID is defined; False otherwise.
        :rtype: bool
        """

        return self._action_id is not None

    def has_warnings(self) -> bool:
        """
        Returns whether there are invalid attributes or other problems with this action data.

        :return: True if this action data has problems; False otherwise.
        :rtype: bool
        """

        for attr in self._attributes.values():
            attr.validate()
            if not attr.is_valid:
                return True

        return False

    def find_spec(self):
        """
        Finds the action specification file for this data when using the current action ID.
        """

        if not self._action_id:
            return

        self._spec = BuildActionRegistry().find_action(self._action_id)
        self._is_missing_spec = False if self._spec is not None else True
        if self._is_missing_spec:
            logger.warning(f'Failed to find action specification for "{self._action_id}"')

    def num_attributes(self) -> int:
        """
        Returns the number of attributes that this build action has.

        :return: attributes count.
        :rtype: int
        """

        return len(self._attributes)

    def attributes(self) -> dict[str, BuildActionAttribute]:
        """
        Returns all attributes for this build action.

        :return: all attributes.
        :rtype: dict[str, BuildActionAttribute]
        """

        return self._attributes

    def known_attributes(self) -> dict[str, BuildActionAttribute]:
        """
        Returns all known attributes for this build action.

        :return: all known attributes.
        :rtype: dict[str, BuildActionAttribute]
        """

        return {name: attr for name, attr in self._attributes.items() if attr.is_known_attribute()}

    def iterate_attribute_names(self) -> Iterator[str]:
        """
        Generator function that yields all attribute names.

        :return: iterated attribute names.
        :rtype: Iterator[str]
        """

        for attr in self._attributes.values():
            yield attr.name

    def attribute(self, name: str) -> BuildActionAttribute | None:
        """
        Returns build action attribute with given name.

        :param str name: name of the attribute to retrieve.
        :return: build action instance.
        :rtype: BuildActionAttribute or None
        """

        return self._attributes.get(name, None)

    def has_attribute(self, name: str) -> bool:
        """
        Returns whether attribute with given name exists within this build action.

        :param str name: name of the attribute to check existence of.
        :return: True if attribute with given name exists; False otherwise.
        :rtype: bool
        """

        return name in self._attributes

    def add_attribute(self, attribute_name: str) -> BuildActionAttribute:
        """
        Adds an action attribute. If the attribute already exists this function does nothing.

        :param str attribute_name: name of the attribute to add.
        :return: build action attribute instance.
        :rtype: BuildActionAttribute
        """

        if attribute_name in self._attributes:
            return self._attributes[attribute_name]

        attr = BuildActionAttribute.from_spec(attribute_name, self._spec, self._action_id)
        self._attributes[attribute_name] = attr
        return attr

    def add_attributes(self, attribute_names: list[str]):
        """
        Adds multiple attributes.

        :param list[str] attribute_names: list of attribute names to add.
        """

        for attr_name in attribute_names:
            self.add_attribute(attr_name)

    def remove_attribute(self, attribute_name: str):
        """
        Removes attribute with given name.

        :param str attribute_name: name of the attribute to delete.
        """

        if attribute_name not in self._attributes:
            return

        del self._attributes[attribute_name]

    def serialize(self) -> serializer.UnsortableOrderedDict:
        """
        Returns this build action data as a serialized dictionary object.

        :return: serialized build action data.
        :rtype: serializer.UnsortableOrderedDict
        """

        data = serializer.UnsortableOrderedDict()

        data['id'] = self._action_id

        # If this action's spec is not valid, then keep all invalid attributes since we do not know if they are real
        # attributes or not.
        keep_invalid = not self.is_valid()
        for attr_name, attr in self._attributes.items():
            if not (attr.is_known_attribute() or keep_invalid):
                logger.info(f'Discarding unknown attribute data: {attr}')
                continue
            if attr.is_value_set():
                data[attr_name] = attr.value()

        return data

    def deserialize(self, data: serializer.UnsortableOrderedDict) -> bool:
        """
        Deserializes given build acton data and updates this build action data based on that data.

        :param dict data: build aciton data serialized data.
        :return: True if the data was deserialized successfully; False otherwise.
        :rtype: bool
        """

        self._action_id = data['id']

        self.find_spec()

        self._init_attributes()

        if self.is_valid():
            for attr_name, attr in self._attributes.items():
                if attr_name in data:
                    attr.set_value(data[attr_name])
        else:
            logger.warning(f'Failed to find BuildActionSpec "{self._action_id}", action values will be preserved')
            for attr_name in data.keys():
                if attr_name not in self._attributes and attr_name not in ('id', 'variantAttrs', 'variants'):
                    self.add_attribute(attr_name)
            for attr_name, value in data.items():
                attr = self.attribute(attr_name)
                if attr:
                    attr.set_value(value)

    def _init_attributes(self):
        """
        Internal function that initializes the set of attributes for this action data.
        """

        self._attributes.clear()
        if not self._spec:
            return

        attr_names = [attr.get('name') for attr in self._spec.attributes]
        self.add_attributes(attr_names)


class BuildActionDataVariant(BuildActionData):
    """
    Build Action Data class that contains a partial set of attribute values.
    """

    def __init__(self, action_id: str | None = None, attr_names: list[str] | None = None):
        # Names of all attributes that are in this variant, only used during initialization.
        self._initial_attr_names = attr_names or []
        super().__init__(action_id=action_id)


class BuildActionProxy(BuildActionData):
    """
    Proxy class that as a stand-in for a BuildAction during blueprint editing.
    Contains all attribute values that are necessary to create real BuildActions at build time.

    A proxy action can represent multiple BuildAction through the usage of variants.
    This allows the user to create multiple actions, where only the values that are unique per variant are set, and
    the remaining attributes will be the same on all actions.
    """

    def __init__(self, action_id: str | None = None):
        super().__init__(action_id=action_id)

        self._variant_attr_names: list[str] = []
        self._variants: list[BuildActionDataVariant] = []
        self._is_mirrored = False

    @property
    def variant_attr_names(self) -> list[str]:
        """
        Getter method that returns list of all attribute names available to set on a variant.

        :return: variant attribute names.
        :rtype: list[str]
        """

        return self._variant_attr_names

    @property
    def is_mirrored(self) -> bool:
        """
        Getter method that returns whether mirrored actions for this proxy should be generated.

        :return: True if actions for this proxy should be generated; False otherwise.
        :rtype: bool
        """

        return self._is_mirrored

    @override
    def has_warnings(self) -> bool:
        """
         Returns whether there are invalid attributes or other problems with this action data.

         :return: True if this action data has problems; False otherwise.
         :rtype: bool
         """

        for attr_name, attr in self._attributes.items():
            if self.is_variant_attribute(attr_name):
                continue
            attr.validate()
            if not attr.is_valid:
                return True

        for variant in self._variants:
            if variant.has_warnings():
                return True

        return False

    @override
    def serialize(self) -> serializer.UnsortableOrderedDict:
        """
        Returns this build proxy step as a serialized dictionary object.

        :return: serialized build proxy step.
        :rtype: serializer.UnsortableOrderedDict
        """

        data = super().serialize()

        if self._is_mirrored:
            data['isMirrored'] = True

        if self._variant_attr_names:
            if self.is_valid():
                known_attrs = self.known_attrs()
                data['variantAttrs'] = [name for name in self._variant_attr_names if name in known_attrs]
            else:
                data['variantAttrs'] = self._variant_attr_names

        if self._variants:
            data['variants'] = [self.serialize_variant(v) for v in self._variants]

        return data

    @override
    def deserialize(self, data: serializer.UnsortableOrderedDict) -> bool:
        """
        Deserializes given build step proxy build step data and updates this build step proxy based on that data.

        :param dict data: build step proxy serialized data.
        :return: True if the data was deserialized successfully; False otherwise.
        :rtype: bool
        """

        result = super().deserialize(data)
        if not result:
            return False

        self._is_mirrored = data.get('isMirrored', False)
        self._variant_attr_names = data.get('variantAttrs', [])
        self._variants = [self.deserialize_variant(v) for v in data.get('variants', [])]

    def display_name(self) -> str:
        """
        Returns the display name of the build action.

        :return: build action name.
        :rtype: str
        """

        return self.spec.display_name

    def color(self) -> colors.LinearColor:
        """
        Returns the color of this action when represented in the UI.

        :return: action color.
        :rtype: colors.LinearColor
        """

        return colors.LinearColor(0.8, 0, 0) if self.is_missing_spec else colors.LinearColor.from_seq(self.spec.color)

    def is_variant_action(self) -> bool:
        """
        Returns whether this action proxy as any variant attributes.

        :return: True if action proxy has variant attributes; False otherwise.
        :rtype: bool
        """

        return bool(self._variant_attr_names)

    def num_variants(self) -> int:
        """
        Returns how many variants exist within this action proxy.

        :return: variants amount.
        :rtype: int
        """

        return len(self._variants)

    def iterate_variants(self) -> Iterator[BuildActionDataVariant]:
        """
        Generator function that yields all variants (containing their own subset of attributes)
        within this action proxy.

        :return: iterated variants.
        :rtype: Iterator[BuildActionDataVariant]
        """

        for variant in self._variants:
            yield variant

    def variants(self) -> list[BuildActionDataVariant]:
        """
        Return list with all variants (containing their own subset of attributes) within this action proxy.

        :return: list of variants.
        :rtype: list[BuildActionDataVariant]
        """

        return list(self.iterate_variants())

    def is_variant_attribute(self, attr_name: str) -> bool:
        """
        Returns whether the given attribute is variant, meaning it can have a different value in each variant.

        :param str attr_name: name of the attribute to check.
        :return: True if given attribute is variant; False otherwise.
        :rtype :bool
        """

        return attr_name in self._variant_attr_names

    def clear_variants(self):
        """
        Remove all variants.
        """

        self._variants.clear()


class BuildAction(BuildActionData):
    """
    Base class for any action that can run during a build operation.

    Following functions can be overridden:
        - `run` to perform the build operations for the action.
        - `validate` to perform operations that can check whether the action can run.
    """

    # Global unique ID for the action.
    id: str | None = None

    # Display name of the action as seen in the UI.
    display_name: str = 'Unknown'

    # Color of the action for highlighting.
    color = (1, 1, 1)

    # Menu category where action will be grouped under.
    category = 'General'

    # List of attribute definition for this action with the following format:
    #   {'name': 'myAttr', 'type': BuildActionAttributeType.BOOL}
    attribute_definitions: list[dict] = []

    def __init__(self):
        super().__init__(self.id)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}>'

    def __getattr__(self, name: str) -> Any:
        attr = self.attribute(name)
        if not attr:
            raise ValueError(f'"{self.__class__.__name__}" object has no attribute "{attr}"')

        return attr.value()

    def should_abort_on_error(self) -> bool:
        """
        Returns whether the build should be aborted if an error occurs while this action is running.

        :return: True if build should be aborted if error happens while running this action; False otherwise.
        :rtype: bool
        """

        return False

    def validate(self):
        """
        Validates this build action. Can be override in subclasses to check whether the action attributes are valid
        and raise BuildActionErrors if anything is invalid.
        """

        pass

    @decorators.abstractmethod
    def run(self):
        """
        Performs the main functionality of this build action.
        Must be override in subclasses.
        """

        raise NotImplementedError


class BuildStep:
    """
    Class that represents a hierarchical step to perform when building a Blueprint.
    """

    # Default name for the build step
    default_name = 'New Step'

    def __init__(
            self, name: str | None = None, action_proxy: BuildActionProxy | None = None, action_id: str | None = None):
        super().__init__()

        self._name: str | None = None
        self._parent: BuildStep | None = None
        self._children: list[BuildStep] = []
        self._action_proxy = action_proxy
        self._is_disabled = False
        self._validate_results: list[logging.LogRecord] = []

        if action_id:
            self._action_proxy = BuildActionProxy(action_id)

        self.set_name(name)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} "{self.display_name()}"'

    @staticmethod
    def from_data(data: serializer.UnsortableOrderedDict) -> BuildStep:
        """
        Returns a new build step created from given serialized data.

        :param serializer.UnsortableOrderedDict data: serialized build step data.
        :return: newly created build step instance.
        :rtype: BuildStep
        """

        new_step = BuildStep()
        new_step.deserialize(data)
        return new_step

    @property
    def name(self) -> str:
        """
        Getter method that returns the name of this step (which is unique among siblings).

        :return: build step name.
        :rtype: str
        """

        return self._name

    @property
    def parent(self) -> BuildStep | None:
        """
        Getter method that returns the parent build step for this build step.

        :return: parent build step.
        :rtype: BuildStep or None
        """

        return self._parent

    @property
    def children(self) -> list[BuildStep]:
        """
        Getter method that returns a list with all build steps that are children of this build step.

        :return: build step children.
        :rtype: list[BuildStep]
        """

        return self._children

    @property
    def action_proxy(self) -> BuildActionProxy | None:
        """
        Getter method that returns the action proxy assigned to this build step.

        :return: action proxy instance.
        :rtype: BuildActionProxy or None
        """

        return self._action_proxy

    @action_proxy.setter
    def action_proxy(self, value: BuildActionProxy):
        """
        Setter method that sets a build action proxy for this build step.

        :param BuildActionProxy value: build action proxy instance to set.
        ..warning:: this function will fail if the build step has any children.
        """

        if self._children:
            logger.warning('Cannot a set a BuildActionProxy on a build step with children. Clear all children first.')
            return

        self._action_proxy = value

    @property
    def is_disabled(self) -> bool:
        """
        Returns whether this build step is disabled.

        :return: True if build step is disabled; False otherwise.
        :rtype: bool
        """

        return self._is_disabled

    @is_disabled.setter
    def is_disabled(self, flag: bool):
        """
        Sets whether this build step is disabled.

        :param bool flag: True to disable the build step; False to enable it.
        """

        self._is_disabled = flag

    def is_root(self) -> bool:
        """
        Returns whether this action is the root build step.
        A build step is considered to be root if it has not parents.

        :return: whether this is a root build step; False otherwise.
        :rtype: bool
        """

        return not self._parent

    def is_action(self) -> bool:
        """
        Returns whether an action proxy is assigned to this build step.

        :return: True if build step can execute an action; False otherwise.
        :rtype: bool
        """

        return self._action_proxy is not None

    def is_disabled_in_hierarchy(self) -> bool:
        """
        Returns whether this step or any of its parent are disabled.

        :return: True if this step or any of its parent are disabled ; False otherwise.
        :rtype: bool
        """

        if self._is_disabled:
            return True

        return self._parent.is_disabled_in_hierarchy() if self._parent else False

    def display_name(self) -> str:
        """
        Returns the display name for build step.
        This is the name that will be used for UIs.

        :return: build step display name.
        :rtype: str
        """

        if self._action_proxy is not None and self._action_proxy.is_variant_action():
            return f'{self._name} (x{self._action_proxy.num_variants()})'

        if self.can_have_children() and not self.is_root():
            return f'{self._name} ({self.num_children()})'

        return self._name

    def clean_name(self, name: str | None = None) -> str:
        """
        Returns a name for the build step without trailing spaces.

        :param str name: name to clean. If not given, action proxy display name will be used.
        :return: clean name.
        :rtype: str
        """

        name = name or (self._action_proxy.display_name() if self._action_proxy else self.default_name)
        return name.strip()

    def ensure_unique_name(self):
        """
        Updates the name of this build step to ensure that it is unique among siblings.
        """

        def _increment_name(_name: str) -> str:
            """
            Internal function that increments given name by adding or increasing a numerical suffix.

            :param str _name: name to increment suffix of.
            :return: new incremented name.
            :rtype: str
            """

            num_match = re.match("(.*?)([0-9]+$)", _name)
            if not num_match:
                return f'{_name} 1'

            base, num = num_match.group()
            return f'{base} {str(int(num) + 1)}'

        if not self._parent:
            return

        sibling_names = [child.name for child in self._parent.children if not (child is self)]
        while self._name in sibling_names:
            self._name = _increment_name(self._name)

    def set_name(self, new_name: str | None = None):
        """
        Sets the name of the build step, modifying it if necessary to ensure that it is unique among siblings.

        :param str new_name: new name of the step. If None, name will be rest to default.
        """

        new_name_clean = self.clean_name(new_name)
        if self._name == new_name_clean:
            return

        self._name = new_name_clean
        self.ensure_unique_name()

    def set_name_from_action(self):
        """
        Updates the name of the build step to match the action it contains.
        """

        if not self._action_proxy:
            return

        self.set_name(self._action_proxy.display_name())

    def description(self) -> str:
        """
        Returns the description of this build step's action.

        :return: build step action description.
        :rtype: str
        """

        if self._action_proxy is not None and self._action_proxy.spec:
            return self._action_proxy.spec.description

        return 'A group containing other actions'

    def color(self) -> colors.LinearColor:
        """
        Returns the color of this build step represented in the UI.

        :return: build step color.
        :rtype: colors.LinearColor
        """

        return colors.LinearColor(1.0, 1.0, 1.0) if self._action_proxy is None else self._action_proxy.color()

    def full_path(self) -> str:
        """
        Returns the full path to this build step within hierarchy.

        :return: build step hierarchy full path.
        :rtype: str
        """

        if not self._parent:
            return '/'

        parent_path = self._parent.full_path().rstrip('/')
        return f'{parent_path}/{self._name}'

    def has_parent(self, step: BuildStep) -> bool:
        """
        Returns whether the given build step is an immediate or distant parent of this build step.

        :param BuildStep step: build step to check.
        :return: True if given step is an immediate or distant parent of this build step; False otherwise.
        :rtype: bool
        """

        return False if not self.parent else True if self.parent == step else self.parent.has_parent(step)

    def index_in_parent(self) -> int:
        """
        Returns the index of this build step within its parent's list of children.

        :return: index of this build step within its parent hierarchy.
        :rtype: int
        """

        return self.parent.child_index(self) if self.parent is not None else 0

    def can_have_children(self) -> bool:
        """
        Returns whether this build step can have children.
        At this moment, only build steps that do not execute any action can have children.

        :return: True if build step can have children; False otherwise.
        :rtype: bool
        """

        return not self.is_action()

    def has_any_children(self) -> bool:
        """
        Returns whether this build step has any children parented under it.

        :return: True if build step has children; False otherwise.
        :rtype: bool
        """

        return self.num_children() > 0

    def num_children(self) -> int:
        """
        Returns the total number of child build steps. that are parented under this build step.

        :return: child count.
        :rtype: int
        """

        return len(self._children) if self.can_have_children() else 0

    def child_at(self, index: int) -> BuildStep | None:
        """
        Returns child build step located at given index within the list of children.

        :param int index: index to use.
        :return: found child build step at given index. If no child is found at given index, None will be returned.
        :rtype: BuildStep or None
        """

        if not self.can_have_children():
            return None

        if index < 0 or index >= len(self._children):
            logger.error(f'Child index out of range {index}, num children: {len(self._children)}')
            return None

        return self._children[index]

    def child_index(self, build_step: BuildStep) -> int:
        """
        Returns the index of given build step within this build step list of children.

        :param BuildStep build_step: build step we want to get its index within this build step hierarchy.
        :return: index of the given build step within this build step hierarchy.
        :rtype: int
        """

        return self._children.index(build_step) if self.can_have_children() else -1

    def child_by_name(self, step_name: str) -> BuildStep | None:
        """
        Returns a child build step by given name.

        :param str step_name: name of the child build step to find.
        :return: found child build step.
        :rtype: BuildStep or None
        """

        if not self.can_have_children():
            return None

        found_step: BuildStep | None = None
        for step in self._children:
            if step.name == step_name:
                found_step = step
                break

        return found_step

    def child_by_path(self, step_path: str) -> BuildStep | None:
        """
        Returns a child build step by given full path.

        :param str step_path: child build step path to find.
        :return: found child build step.
        :rtype: BuildStep or None
        """

        if not self.can_have_children():
            return None

        step_path = step_path.lstrip('/')
        if '/' in step_path:
            child_name, grand_child_path = step_path.split('/', 1)
            child = self.child_by_name(child_name)
            return child.child_by_path(grand_child_path) if child is not None else None

        return self.child_by_name(step_path)

    def add_child(self, build_step: BuildStep):
        """
        Adds given build step as a child of this build step.

        :param BuildStep build_step: child build step.
        :raises ValueError: cannot add step as child of itself.
        :raises BuildStep: if given build step does not have the expected type.
        """

        if not self.can_have_children():
            return

        if build_step is self:
            raise ValueError('Cannot add step as child of itself.')
        if not isinstance(build_step, BuildStep):
            raise TypeError(f'Expected BuildStep type, got {type(build_step).__name__}')

    def add_children(self, build_steps: list[BuildStep]):
        """
        Adds given list of build steps as children of this build step.

        :param list[BuildStep] build_steps: list of build steps to add as children.
        """

        for child_step in build_steps:
            self.add_child(child_step)

    def remove_child(self, build_step: BuildStep):
        """
        Removes given build step as child of this build step.

        :param BuildStep build_step: child build step to remove.
        """

        if not self.can_have_children():
            return

        if build_step not in self._children:
            return

        self._children.remove(build_step)
        build_step.set_parent_internal(None)

    def remove_child_internal(self, build_step: BuildStep):
        """
        Removes children from internal list of children.

        :param BuildStep build_step: build step to remove.
        """

        if build_step not in self._children:
            return

        self._children.remove(build_step)

    def clear_children(self):
        """
        Clears all this children build steps.
        """

        if not self.can_have_children():
            return

        for child_step in self._children:
            child_step.set_parent_internal(None)

        self._children.clear()

    def set_parent(self, new_parent: BuildStep | None):
        """
        Sets the parent of this build step.

        :param BuildStep or None new_parent: new parent build step.
        """

        if new_parent and not new_parent.can_have_children():
            raise ValueError(f'Cannot set parent to build step that cannot have children: {new_parent}')

        if self._parent is new_parent:
            return

        if self._parent:
            self._parent.remove_child_internal(self)
            self._parent = None
        if new_parent:
            new_parent.add_child(self)
        else:
            self.set_parent_internal(None)

    def set_parent_internal(self, new_parent: BuildStep | None):
        """
        Sets the internal variable that holds the parent of this build step.

        :param BuildStep or None new_parent: new parent build step.
        """

        self._parent = new_parent
        self.ensure_unique_name()

    def has_validation_errors(self) -> bool:
        """
        Returns whether this build step has any validation errors.

        :return: True if build step has validation errors; False otherwise.
        :rtype: bool
        """

        return bool(self._validate_results)

    def has_warnings(self) -> bool:
        """
        Returns whether this build step has any validation warnings, or if it's action has any warnings.

        :return: True if build step has warnings; False otherwise.
        :rtype: bool
        """

        return self.has_validation_errors() or (self.is_action() and self._action_proxy.has_warnings())

    def serialize(self) -> serializer.UnsortableOrderedDict:
        """
        Returns this build step as a serialized dictionary object.

        :return: serialized build step.
        :rtype: serializer.UnsortableOrderedDict
        """

        data = serializer.UnsortableOrderedDict()
        data['name'] = self.name
        if self.is_disabled:
            data['isDisabled'] = True
        if self._action_proxy:
            data['action'] = self._action_proxy.serialize()
        if self.num_children() > 0:
            data['children'] = [child.serialize() for child in self._children]

        return data

    def deserialize(self, data: serializer.UnsortableOrderedDict) -> bool:
        """
        Deserializes given blueprint build step data and updates this blueprint based on that data.

        :param dict data: build step serialized data.
        :return: True if the data was deserialized successfully; False otherwise.
        :rtype: bool
        """

        self._is_disabled = data.get('isDisabled', False)

        self._action_proxy = None
        if 'action' in data:
            new_action_proxy = BuildActionProxy()
            new_action_proxy.deserialize(data['action'])
            self.action_proxy = new_action_proxy

        # Set name after action, so that if no name has been set yet, it will be initialized with the name of the
        # action.
        self.set_name(data.get('name', None))

        if not self.can_have_children():
            return False

        self.clear_children()

        self._children = [BuildStep.from_data(child_data) for child_data in data.get('children', [])]
        for child in self._children:
            if not child:
                continue
            child.set_parent_internal(self)

        return True
