from __future__ import annotations

import os

import yaml

from tp.core import log
from tp.preferences.interfaces import crit
from tp.common.python import decorators, folder, yamlio
from tp.libs.rig.crit import consts
from tp.libs.rig.crit.core import errors, serializer

logger = log.rigLogger


@decorators.add_metaclass(decorators.Singleton)
class TemplatesManager:
    """
    Class to register CRIT templates, which are the serialized form of rigs.
    """

    def __init__(self):
        self._templates: dict[str, str] = {}
        self._template_roots = []
        self._preference_interface = crit.crit_interface()

    @property
    def templates(self) -> dict[str, str]:
        """
        Getter method that returns a dictionary of templates in the form of {'template_name': 'template_path'}.

        :return: dictionary of templates.
        :rtype: dict[str, str]
        """

        valid: dict[str, str] = {}
        for template_name, template_path in self._templates.items():
            if not template_path or not os.path.exists(template_path):
                continue
            valid[template_name] = template_path
        self._templates = valid

        return self._templates

    def refresh(self):
        """
        Refreshes the manager by clearing the register and then rediscovering available templates.
        """

        self._templates.clear()
        self.discover_templates()

    def has_template(self, name: str) -> bool:
        """
        Returns whether template with given name exists.

        :param str name: name of the template.
        :return: True if template with given name already exists; False otherwise.
        :rtype: bool
        """

        return self.template_path(name) != ''

    def template(self, name: str) -> dict:
        """
        Returns the rig template dictionary from the manager.

        :param str name: template name.
        :return: loaded template dictionary.
        :rtype: dict
        """

        return yamlio.read_file(self.template_path(name))

    def template_path(self, name: str) -> str:
        """
        Returns the absolute file path for the template with the given name.

        :param str name: template name.
        :return: file path for the template with the given name, or empty string if no template with given name was
            found.
        :rtype: str
        """

        return self.templates.get(name.lower(), '')

    def add_template(self, template_path: str) -> bool:
        """
        Adds a template to the manager.

        :param str template_path: absolute file path for the template.
        :return: True if template path was added successfully; False otherwise.
        :rtype: bool
        """

        if not template_path.endswith(consts.TEMPLATE_EXTENSION):
            return False

        self._templates[os.path.splitext(os.path.basename(template_path))[0].lower()] = template_path.replace('\\', '/')
        return True

    def discover_templates(self):
        """
        Discovers all available templates and stores them within the manager.
        """

        paths = os.getenv(consts.TEMPLATES_ENV_VAR_KEY, '').split(os.pathsep)
        paths += self._preference_interface.user_template_paths()
        if not paths:
            return

        self._template_roots = paths
        for template_path in paths:
            if not os.path.exists(template_path):
                continue
            elif os.path.isfile(template_path):
                self.add_template(template_path)
            else:
                for root, _, files in os.walk(template_path):
                    for file_name in iter(files):
                        self.add_template(os.path.join(root, file_name))

    def save_location(self) -> str:
        """
        Returns the current default save folder path from the CRIT preferences file.

        :return: templates save location.
        :rtype: str
        """

        return self._preference_interface.user_template_save_path()

    def save_template(
            self, name: str, template: dict, template_root_path: str | None = None, overwrite: bool = False) -> str:
        """
        Saves a template to the given location on disk.

        :param str name: name of the template.
        :param dict template: template data to be saved.
        :param str or None template_root_path: root directory where template should be saved. If not given, default save
            location will be used.
        :param bool overwrite: whether to overwrite an existing template with the same name.
        :return: absolute file path where the template was saved.
        :rtype: str
        :raises errors.CritTemplateAlreadyExistsError: if a template with the same already exists and `overwrite` is
            False.
        :raises IOError: if there was an error writing the template to the specified file path.
        """

        template['name'] = name
        root = template_root_path or self.save_location()
        new_template_path = os.path.join(root, f'{name}{consts.TEMPLATE_EXTENSION}')
        if os.path.exists(new_template_path) and not overwrite:
            logger.error(f'Template path: {new_template_path} already exist.')
            raise errors.CritTemplateAlreadyExistsError(new_template_path)
        folder.ensure_folder_exists(os.path.dirname(new_template_path))

        try:
            with open(new_template_path, 'w') as yaml_file:
                yaml.dump(template, yaml_file, default_flow_style=False, Dumper=serializer.CritDumper)
            saved = True
        except IOError:
            saved = False
        if not saved:
            raise IOError(f'Failed to write template for unknown reasons to file: {new_template_path}')
        self.add_template(new_template_path)

        return new_template_path
