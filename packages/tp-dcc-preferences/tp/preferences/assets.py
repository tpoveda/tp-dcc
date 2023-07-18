from __future__ import annotations

import os
import uuid
import typing
import inspect
from typing import List, Dict

from overrides import override

from tp.core import log
from tp.bootstrap import consts
from tp.bootstrap.core import manager
from tp.common.python import path, folder, decorators

if typing.TYPE_CHECKING:
	from tp.preferences.preference import PreferenceInterface

logger = log.tpLogger


class AssetPreference:

	_DEFAULT_ITEMS = None				# type: List[str]

	def __init__(self, asset_folder: str, preference_interface: PreferenceInterface):
		super().__init__()

		self._asset_folder = asset_folder
		self._preference_interface = preference_interface
		self._manager = self._preference_interface.manager

	@decorators.abstractmethod
	def has_old_assets(self) -> bool:
		"""
		Returns whether assets folder contains old assets.

		:return: True if there are old assets located within assets folder; False otherwise.
		:rtype: bool
		"""

		return False

	@decorators.abstractmethod
	def build_asset_directories(self):
		"""
		Builds the asset directories in a safe way if it is missing.
		"""

		raise NotImplementedError

	def prefs_path(self) -> str:
		"""
		Returns the assets folder specific to this user and for this preference. e.g: ../tp/preferences/assets/scenes

		:return: asset preferences path.
		:rtype: str
		"""

		return path.normalize_path(path.join_path(self.user_asset_root(), self._asset_folder))

	def prefs_default_path(self) -> str:
		"""
		Returns the path to default assets in preferences.

		:return: default asset preference path.
		:rtype: str
		"""

		return path.join_path(self.prefs_path(), 'defaults')

	def user_asset_root(self) -> str:
		"""
		Returns the path to the user assets folder e.g: ../tp/preferences/assets

		:return: user assets folder.
		:rtype: str
		"""

		user_prefs_path = str(self._manager.root('user_preferences'))
		assets_path = path.join_path(user_prefs_path, 'assets')
		if not path.is_dir(assets_path):
			os.makedirs(assets_path)

		return assets_path

	def current_package_path(self) -> str | None:
		"""
		Retuns the absolute path where this tp-dcc framework package is located. e.g:
			"E:\tools\dev\tp-dcc-tools\packages\tp-dcc-tools-utility"

		:return: package absolute path.
		:rtype: str
		"""

		found_package = None
		class_file = inspect.getfile(self._preference_interface.__class__)
		for directory in path.iterate_parent_path(class_file):
			found_package_path = path.join_path(directory, consts.PACKAGE_NAME)
			if path.exists(found_package_path):
				found_package = manager.current_package_manager().resolver.package_from_path(found_package_path).root
				break

		return found_package

	def default_assets_path(self) -> str:
		"""
		Returns the default assets path for a tp-dcc framework package, usually located at:
			{self}/preferences/assets/<assetFolder>

		:return: default assets path.
		:rtype: str
		"""

		package_path = self.current_package_path()
		return path.join_path(package_path, 'preferences', 'assets', self._asset_folder)

	def default_asset_items(self, refresh: bool = False) -> List[str]:
		"""
		Returns the default items from the default directory.

		:param bool refresh: whether to refresh cached items.
		:return: lsit of default asset items.
		:rtype: List[str]
		"""

		if not refresh and self._DEFAULT_ITEMS is not None:
			return self._DEFAULT_ITEMS

		default_path = self.default_assets_path()
		if not path.exists(default_path):
			return

		self._DEFAULT_ITEMS = path.files_in_directory(default_path, include_extension=False)

		return self._DEFAULT_ITEMS

	def copy_default_assets(self, target_path: str) -> str | None:
		"""
		Copies default assets into given path.

		:param str target_path: path to copy default asses into.
		:return: copy target path.
		:rtype: str or None
		"""

		default_asset_path = self.default_assets_path()
		if not os.path.exists(default_asset_path):
			logger.warning(f'Assets folder was not copied because it does not exist: "{default_asset_path}"')
			return

		folder.copy_directory_contents_safe(default_asset_path, target_path)
		logger.debug(f'Default assets copied: "{default_asset_path}" --> "{target_path}"')

		return target_path


class BrowserPreference(AssetPreference):

	_BROWSER_FOLDERS = 'browserFolders'
	_CATEGORIES = 'browserCategories'
	_ACTIVE_FOLDERS = 'activeFolders'
	_ACTIVE_CATEGORIES = 'activeCategories'
	_BROWSER_UNIFORM_ICONS = 'browserUniformIcons'

	def __init__(
			self, asset_folder: str, preference_interface: PreferenceInterface, build_assets: bool = True,
			file_types: List[str] | None = None, auto_fill_folders: bool = True, copy_defaults: bool = True):
		super().__init__(asset_folder=asset_folder, preference_interface=preference_interface)

		self._file_Types = file_types or []
		self._auto_fill_folders = auto_fill_folders
		self._copy_defaults = copy_defaults

		if build_assets:
			self.build_asset_directories()

	@property
	def _browser_folder_root(self) -> Dict:
		if not self.settings().get(self._BROWSER_FOLDERS):
			self.settings()[self._BROWSER_FOLDERS] = {}

		return self.settings()[self._BROWSER_FOLDERS]

	@property
	def _browser_folder(self) -> List[Dict]:
		browser_folder =self._browser_folder_root.get(self._asset_folder)
		if browser_folder is None:
			self._browser_folder_root[self._asset_folder] = []

		return self._browser_folder_root[self._asset_folder]

	@property
	def _active_folder_root(self) -> Dict:
		active_folders = self.settings().get(self._ACTIVE_FOLDERS)
		if active_folders is None:
			self.settings()[self._ACTIVE_FOLDERS] = {}

		return self.settings()[self._ACTIVE_FOLDERS]

	@property
	def _active_folders(self) -> List[str]:
		if not self._active_folder_root.get(self._asset_folder):
			self._active_folder_root[self._asset_folder] = []

		return self._active_folder_root.get(self._asset_folder)

	@property
	def _categories_root(self) -> Dict:
		categories = self.settings().get(self._CATEGORIES)
		if categories is None:
			self.settings()[self._CATEGORIES] = {}

		return self.settings()[self._CATEGORIES]

	@property
	def _categories(self) -> List[Dict]:
		if not self._categories_root.get(self._asset_folder):
			self._categories_root[self._asset_folder] = []

		return self._categories_root[self._asset_folder]

	@property
	def _active_categories_root(self) -> Dict:
		active_categories = self.settings().get(self._ACTIVE_CATEGORIES)
		if active_categories is None:
			self.settings()[self._ACTIVE_CATEGORIES] = {}

		return self.settings()[self._ACTIVE_CATEGORIES]

	@property
	def _active_categories(self) -> List[str]:
		if not self._active_categories_root.get(self._asset_folder):
			self._active_categories_root[self._asset_folder] = []

		return self._active_categories_root[self._asset_folder]

	@override
	def has_old_assets(self) -> bool:
		prefs_path = self.prefs_path()
		only_files = [f for f in os.listdir(prefs_path) if os.path.isfile(path.join_path(prefs_path, f))]
		extensions = [os.path.splitext(f)[1][1:] for f in only_files]
		for extension in extensions:
			if extension in self._file_Types:
				return True

		return False

	@override
	def build_asset_directories(self):

		folder_paths = self.browser_folder_paths()
		assets_path = self.user_asset_root()
		folder.ensure_folder_exists(assets_path)

		prefs_path = self.prefs_path()
		logger.info(f'Building asset directories for: {prefs_path}')

		if path.exists(prefs_path) and (self.has_old_assets() or not self._auto_fill_folders or self.asset_folder_empty()) and len(folder_paths) == 0:
			folder.ensure_folder_exists(prefs_path)
			self._init_default_directory()
			return

		if not path.exists(prefs_path):
			folder.ensure_folder_exists(prefs_path)
			self._init_default_directory()

		self.refresh_asset_folders(set_active=False, save=True)

	def settings(self) -> Dict:
		"""
		Returns the settings dictionary of the internal preference file handled by the interface class.

		:return: preference settings.
		:rtype: Dict
		"""

		return self._preference_interface.settings().get('settings', {})

	def save_settings(self, indent: bool = True, sort: bool = False):
		"""
		Save settings for the browser preferences into disk.

		:param bool indent: whether indent should be respected.
		:param bool sort: whether settings should be respect its order when saving.
		"""

		self._cleanup_actives()
		return self._preference_interface.save_settings(indent=indent, sort=sort)

	def directory_path(self, target_path: str) -> path.DirectoryPath | None:
		"""
		Returns the directory path of the given path.

		:param str target_path: path to get directory path instance of.
		:return: directory path instance.
		:rtype: path.DirectoryPath or None
		"""

		found_directory_path = None
		for dp in self._browser_folder:
			if path.normalize_path(dp['path']) == path.normalize_path(target_path):
				found_directory_path = path.DirectoryPath(pref=dp)
				break

		return found_directory_path

	def browser_folder_paths(self) -> List[path.DirectoryPath]:
		"""
		Returns all browser folder paths as DirectoryPath containing the folder path, id and alias.

		:return: list of browser folder paths.
		:rtype: List[path.DirectoryPath]
		"""

		return [path.DirectoryPath(pref=pref) for pref in self._browser_folder]

	def active_browser_paths(self) -> List[path.DirectoryPath]:
		"""
		Returns list of active browser folder paths as DirectoryPath containing the folder path, id and alias.

		:return: list of active browser folder paths.
		:rtype: List[path.DirectoryPath]
		"""

		active_folders = self.settings()[self._ACTIVE_FOLDERS][self._asset_folder]
		return [f for f in self.browser_folder_paths() if f.id in active_folders]

	def asset_folder_empty(self) -> bool:
		"""
		Returns whether the asset folder is empty.

		:return: True if asset folder is empty; False otherwise.
		:rtype: bool
		"""

		return not len(os.listdir(self.prefs_path())) > 0

	def add_browser_directory(self, directory: path.DirectoryPath, save: bool = True) -> bool:
		"""
		Adds given directory into the list of browser directories.

		:param path.DirectoryPath directory: directory path instance.
		:param bool save: whether to save settings.
		:return: True if directory was added successfully; False otherwise.
		:rtype: bool
		:raises TypeError: if given directory is not a valid path.DirectoryPath instance.
		"""

		if isinstance(directory, path.DirectoryPath):
			for d in self.browser_folder_paths():
				if d == directory:
					logger.debug(f'Duplicate folders found while adding browser, ignoring "{d.alias}"')
					return False

			asset_folder = self._browser_folder_root[self._asset_folder]
			asset_folder.append(directory.serialize())

			if save:
				self.save_settings()

			return True

	def add_browser_directories(self, directories: List[path.DirectoryPath], save: bool = True):
		"""
		Adds given directories into the list of browser directories.

		:param List[path.DirectoryPath] directories: list of directory path instances.
		:param bool save: whether to save settings.
		"""

		for d in directories:
			self.add_browser_directory(d, save=False)

		if save:
			self.save_settings()

	def clear_browser_directories(self, save: bool = True):
		"""
		Clears the browser directories.

		:param bool save: whether to save settings.
		"""

		self._browser_folder[:] = []

		if save:
			self.save_settings()

	def set_active_directory(self, directory_path: path.DirectoryPath, clear: bool = True):
		"""
		Sets the active directory.

		:param path.DirectoryPath directory_path: Directory path instance to set as active.
		:param bool clear: whether to clear current active folder settings.
		"""

		active_folder_settings = self._active_folders
		if clear:
			active_folder_settings[:] = []
		active_folder_settings.append(directory_path.id)
		self.save_settings()

	def set_active_directories(self, directories: List[path.DirectoryPath], save: bool = True):
		"""
		Sets active directories.

		:param List[path.DirectoryPath] directories: list of directory path instances to set as active ones.
		:param bool save: whether to save settings.
		"""

		self.settings()[self._ACTIVE_FOLDERS][self._asset_folder] = [d.id for d in directories]

		if save:
			self.save_settings()

	def browser_uniform_icons(self) -> bool:
		"""
		Returns whether asset browser should use uniform icons.

		:return: True to use uniform icons; False otherwise.
		:rtype: bool
		"""

		self._init_uniform_icons()
		return self.settings()[self._BROWSER_UNIFORM_ICONS][self._asset_folder]

	def set_browser_uniform_icons(self, flag: bool, save: bool = True):
		"""
		Sets whether browser should use uniform icons.

		:param bool flag: True to enable uniform icons; False otherwise.
		:param bool save: whether to save settings.
		"""

		self._init_uniform_icons()
		self.settings()[self._BROWSER_UNIFORM_ICONS][self._asset_folder] = flag

		if save:
			self.save_settings()

	def refresh_asset_folders(self, set_active: bool = True, save: bool = True):
		"""
		Retrieves folder in assets folder in preferences and set/save the settings.

		:param bool set_active: whether to set the new folder as active.
		:param bool save: whether to save the preferences.
		"""

		prefs = self.prefs_path()
		folder_paths = self.browser_folder_paths()
		dirs = [found_folder.path for found_folder in folder_paths]
		if self._copy_defaults:
			target_path = self.copy_default_assets(self.prefs_default_path())
			if target_path:
				dirs.append(target_path)

		if self._auto_fill_folders:
			new_folders = [path.join_path(prefs, f) for f in os.listdir(prefs) if path.is_dir(path.join_path(prefs, f)) and '_fileDependencies' not in f and not f.startswith('.')]
			dirs += new_folders
			logger.debug(f'Auto fill folders: Adding new folders: {new_folders}')
			dirs = sorted(list(set(dirs)))

		new_dirs = [path.DirectoryPath(path=d) for d in dirs if self.directory_path(d) is None]
		self.add_browser_directories(new_dirs, save=save)

		if path.exists(prefs) and not len(dirs) > 0:
			self._init_default_directory()

		if set_active:
			new_paths = [d for d in new_dirs if d not in folder_paths]
			self.set_active_directories(self.active_browser_paths() + new_paths)

	def create_category(self, name: str, category_id: str, parent: str, children: List[str]) -> Dict:
		"""
		Creates a new category.

		:param str name: category name.
		:param str category_id: category id.
		:param str parent: category parent id.
		:param List[str] children: list of children category ids.
		:return: newly created category.
		:rtype: Dict
		"""

		return {
			'id': category_id or str(uuid.uuid4())[:6],
			'alias': name,
			'parent': parent,
			'children': children
		}

	def add_category(self, category: Dict, save: bool = True):
		"""
		Adds category into browser settings.

		:param Dict category: category to add.
		:param bool save: whether to save settings.
		"""

		self.settings()[self._CATEGORIES].setdefault(self._asset_folder, []).append(category)

		if save:
			self.save_settings()

	def add_categories(self, categories: List[Dict], save: bool = True):
		"""
		Adds categories into browser settings.

		:param List[Dict] categories: categories to add.
		:param bool save: whether to save settings.
		"""

		existing = {i['id']: i for i in self.categories()}
		for cat in categories:
			existing_cat = existing.get(cat['id'])
			if existing_cat is not None:
				existing_cat['alias'] = cat['alias']
				existing_cat['parent'] = cat['parent']
				existing_cat['children'] = cat['children']
				continue
			existing[cat['id']] = cat
			self.add_category(cat, save=False)

		if save:
			self.save_settings()

	def update_category(self, category_id: str, data: Dict, save: bool = True):
		"""
		Updates category with given id with given data.

		:param str category_id: id of the category to update.
		:param Dict data: category data.
		:param bool save: whether to save settings.
		"""

		updated = False
		for cat in self._categories:
			if cat['id'] == category_id:
				cat.update(data)
				updated = True

		if save and updated:
			self.save_settings()

	def categories(self) -> List[Dict]:
		"""
		Returns list of categories.

		:return: list of categories.
		:rtype: List[Dict]
		"""

		return self._categories

	def clear_categories(self, save: bool = True):
		"""
		Clear categories.

		:param bool save: whether to save settings.
		"""

		self._categories[:] = []

		if save:
			self.save_settings()

	def active_categories(self) -> List[str]:
		"""
		Returns list of active categories.

		:return: list of active categories.
		:rtype: List[str]
		"""

		return self._active_categories

	def set_active_categories(self, category_ids: List[str], save: bool = True):
		"""
		Set list of active categories.

		:param List[str] category_ids: list of category IDs to set as active ones.
		:param bool save: whether to save settings.
		"""

		self.settings()[self._ACTIVE_CATEGORIES][self._asset_folder] = category_ids

		if save:
			self.save_settings()

	def remove_category(self, category_id: str, save: bool = True) -> bool:
		"""
		Deletes category with given id.

		:param str category_id: id of the category to delete.
		:param bool save: whether to save settings.
		:return: True if category was deleted successfully; False otherwise.
		:rtype: bool
		"""

		deleted = False
		for index, cat in enumerate(self._categories):
			if cat['id'] == category_id:
				del self._categories[index]
				deleted = True

		if deleted and save:
			self.save_settings()

		return deleted

	def _init_default_directory(self, set_active: bool = True):
		"""
		Internal function that initializes the default assets directory.

		:param bool set_active: whether to set initialized directory as the active one.
		"""

		directory_path = path.DirectoryPath(path=self.prefs_path())
		self._browser_folder[:] = [directory_path.serialize()]
		if set_active:
			self.set_active_directory(directory_path)

	def _init_uniform_icons(self):
		"""
		Internal function that initializes the default browser uniform icons.
		"""

		browser_uniform_icons = self.settings().get(self._BROWSER_UNIFORM_ICONS)
		if browser_uniform_icons is None:
			self.settings()[self._BROWSER_UNIFORM_ICONS] = {}

		uniform_icons = self.settings()[self._BROWSER_UNIFORM_ICONS].get(self._asset_folder, None)
		if uniform_icons is None:
			self.settings()[self._BROWSER_UNIFORM_ICONS][self._asset_folder] = True

		self.save_settings()

	def _cleanup_actives(self):
		"""
		Internal function that removes old active IDs that do not exist anymore.
		"""

		to_remove = []
		ids = [f['id'] for f in self._browser_folder]
		for active_folder in self._active_folders:
			if active_folder not in ids:
				to_remove.append(active_folder)

		for directory in to_remove:
			self._active_folders.remove(directory)
