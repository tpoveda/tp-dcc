from __future__ import annotations

import os
import pathlib
from collections import deque

from tp.libs.python import helpers, paths, settings, decorators

NAMING_PRESET_HIERARCHY = "namingPresetHierarchy"
NAMING_PRESET_SAVE_PATH = "namingPresetSavePath"
NAMING_PRESET_PATHS = "namingPresetPaths"
COMPONENTS_PATHS_KEY = "componentsPaths"
TEMPLATES_PATHS_KEY = "templatesPaths"
TEMPLATE_SAVE_PATH_KEY = "templateSavePath"
GRAPH_PATHS_KEY = "graphsPaths"
EXPORT_PLUGIN_OVERRIDES_KEY = "exportPluginOverrides"


class ModRigSettings(settings.YAMLSettings, metaclass=decorators.Singleton):
    """Class that defines Noddle settings."""

    def __init__(self):
        super().__init__(paths.canonical_path("../settings.yaml"))

    @staticmethod
    def default_naming_config_path() -> str:
        """Return the absolute path where default naming presets are located.

        Returns:
            The default naming preset absolute path.
        """

        return paths.canonical_path("../../naming")

    @staticmethod
    def default_modules_config_path() -> str:
        """Return the absolute path where default modules are located.

        Returns:
            The default modules absolute path.
        """

        return paths.canonical_path("../library/modules")

    @staticmethod
    def default_user_templates_path() -> str:
        """Return the default ModRig templates path.

        Returns:
            The default template absolute path.
        """

        return paths.canonical_path("../library/templates")

    @staticmethod
    def default_user_graphs_path() -> str:
        """Return the default ModRig graphs path.

        Returns:
            The default graph absolute path.
        """

        return paths.canonical_path("../library/graphs")

    @staticmethod
    def default_export_plugin_path() -> str:
        """Return the default Noddle export plugins path.

        Returns:
            The default export plugins absolute path.
        """

        return paths.canonical_path("../library/exporters")

    def naming_preset_paths(self) -> list[str]:
        """Return the paths whether presets are located.

        Returns:
            The list of naming preset paths.
        """

        preset_paths = self.get(NAMING_PRESET_PATHS, [])
        return helpers.remove_dupes([self.default_naming_config_path()] + preset_paths)

    def naming_preset_hierarchy(self) -> dict:
        """Return the naming preset hierarchies from the ModRig preferences
        file.

        Returns:
            Dictionary with naming presets hierarchy.
        """

        return self.get(NAMING_PRESET_HIERARCHY, {})

    def naming_preset_save_path(self) -> str:
        """Return the path where new naming presets will be stored into.

        Returns:
            The absolute path where naming presets will be saved.
        """

        return self.get(NAMING_PRESET_PATHS, []) or self.default_naming_config_path()

    def set_naming_preset_paths(self, preset_paths: list[str], save: bool = True):
        """Set the naming preset paths for the ModRig preferences file.

        Args:
            preset_paths: List of naming preset paths to set.
            save: Whether to save the preference file changes.
        """

        self.set(NAMING_PRESET_PATHS, preset_paths, save=save)

    def set_naming_preset_hierarchy(self, hierarchy: dict, save: bool = True):
        """Set the naming preset hierarchies for the ModRig preferences file.

        Args:
            hierarchy: Dictionary with naming presets hierarchy to set.
            save: Whether to save the preference file changes.
        """

        self.set(NAMING_PRESET_HIERARCHY, hierarchy, save=save)

    def set_naming_preset_save_path(self, save_path: str, save: bool = True):
        """Set the naming preset save path for the ModRig preferences file.

        Args:
            save_path: The preset save path to set.
            save: Whether to save the preference file changes.
        """

        default_naming_path = self.default_naming_config_path()
        if pathlib.Path(save_path).resolve() == pathlib.Path(default_naming_path):
            return
        self.set(NAMING_PRESET_SAVE_PATH, save_path, save=save)

    def user_modules_paths(self) -> list[str]:
        """Return the user modules folder paths.

        Returns:
            The list of user modules folder paths.
        """

        return self.get(COMPONENTS_PATHS_KEY, [])

    def module_paths(self) -> list[str]:
        """Return all registered modules paths.

        Returns:
            The list of all registered modules paths.
        """

        return helpers.remove_dupes(
            [self.default_modules_config_path()] + self.user_modules_paths()
        )

    def user_template_paths(self) -> list[str]:
        """Return the user template folder paths.

        Returns:
            List of user template folder paths.
        """

        found_paths = self.get(TEMPLATES_PATHS_KEY, [])
        return found_paths or [self.default_user_templates_path()]

    def user_template_save_path(self) -> str:
        """Return the user template save path.

        Returns:
            The user template save path, expanding environment variables
                and user home directory.
        """

        user_template_path = self.get(TEMPLATE_SAVE_PATH_KEY, "")
        resolved = os.path.expandvars(os.path.expanduser(user_template_path))
        if not os.path.exists(resolved):
            user_template_path = os.getenv("NODDLE_TEMPLATE_SAVE_PATH", "")
            resolved = os.path.expandvars(os.path.expanduser(user_template_path))
            if not os.path.exists(resolved):
                user_template_path = self.default_user_templates_path()

        return user_template_path

    def user_graph_paths(self) -> list[str]:
        """Return the user graph folder paths.

        Returns:
            The list of user graph folder paths.
        """

        found_paths = self.get(GRAPH_PATHS_KEY, [])
        return found_paths or [self.default_user_graphs_path()]

    def empty_scenes_path(self) -> str:
        """Returns the absolute path where empty scene templates are located.

        Returns:
            The location where empty scene templates are located.
        """

        return pathlib.Path(
            self.default_user_templates_path(), "emptyScenes"
        ).as_posix()

    def recent_max(self) -> int:
        """Return the maximum number of recent projects to retrieve.

        Returns:
            The maximum number of recent projects to retrieve.
        """

        return self.get("maxRecent", 3)

    def recent_projects_queue(self) -> deque:
        """Return a queue of recent projects.

        Returns:
            The deque containing recent projects, with a maximum length
            defined by `recent_max()`. If no recent projects are found,
            an empty deque with the maximum length is returned.
        """

        max_length = self.recent_max()
        projects = self.get("recentProjects", [])
        if not projects:
            return deque(maxlen=max_length)

        return deque(projects, maxlen=max_length)

    def previous_project(self) -> str:
        """Return the previous project path.

        Returns:
            The previous project path, or an empty string if not set.
        """

        project = self.get("project", {})
        return project.get("previousProject", "")

    def set_previous_project(self, project_path: str):
        """Set the given path as the previous project path.

        Args:
            project_path: The path to set as the previous project.
        """

        project = self.get("project", {})
        project["previousProject"] = str(project_path)
        self.set("project", project, save=True)

    def add_recent_project(self, name: str, project_path: str) -> bool:
        """Add the given project name and path entry as a recent project.

        Args:
            name: Name of the project to add as the recent one.
            project_path: Path of the project to add as a recent one.

        Returns:
            True if the project was added into the list of recent projects;
                False otherwise.
        """

        recent_projects = self.recent_projects_queue()
        entry = [name, project_path]
        if entry in recent_projects:
            return False
        recent_projects.appendleft(entry)
        project = self.get("project", {})
        project["recentProjects"] = list(recent_projects)
        self.set("project", project, save=True)
        return True

    def refresh_recent_projects(self):
        """Refresh recent projects by removing recent project folders that do
        not exist.
        """

        recent_projects = self.recent_projects_queue()
        existing_projects = []
        for recent_project in recent_projects:
            if not recent_project or not os.path.isdir(recent_project):
                continue
            existing_projects.append(recent_project)
        project = self.get("project", {})
        project["recentProjects"] = existing_projects
        self.set("project", project, save=True)

    def asset_types(self) -> list[str]:
        """Return the asset types.

        Returns:
            List of asset types defined in the settings.
        """

        assets = self.get("assets", {})
        return assets.get("types", [])

    def rig_display_line_width(self) -> float:
        """Return the default display line width for newly created rig
        controls.

        Returns:
            The display line width for rig controls.
        """

        rig_settings = self.get("rig", {})
        return rig_settings.get("display", {}).get("lineWidth", 1.0)

    def exporter_plugin_paths(self) -> list[str]:
        """Return the paths where exporter plugins are located.

        Returns:
            List of exporter plugin paths. If no paths are found in the
                settings, it returns the default export plugin path.
        """

        found_settings = self.get(TEMPLATES_PATHS_KEY, [])
        return found_settings or [self.default_export_plugin_path()]

    def exporter_plugin_overrides(self) -> dict[str, str]:
        """Return the export plugin overrides.

        Returns:
            A dictionary where keys are plugin IDs and values are the
                corresponding override paths.
        """

        return self.get(EXPORT_PLUGIN_OVERRIDES_KEY, {})
