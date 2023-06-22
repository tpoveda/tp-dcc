from __future__ import annotations

import getpass
import datetime
from typing import List, Dict, Callable

from tp.core import log, dcc
from tp.common.qt import api as qt
from tp.common.python import decorators, modules

logger = log.modelLogger


class ModelCheckerController(qt.QObject):

	filteredNodes = qt.Signal(object)
	filteredTopNode = qt.Signal(str)

	def __init__(self, commands_data: Dict, command_module_paths: List[str]):
		super().__init__()

		self._commands_data = commands_data
		self._command_module_paths = command_module_paths
		self._modules = []
		self._command_functions = {}

		self._results = {}
		self._command_label = {}
		self._command_run_button = {}

	@property
	def commands(self) -> Dict:
		return self._commands_data

	@property
	def results(self) -> Dict:
		return self._results

	def command_function(self, command_name: str) -> Callable | None:
		"""
		Returns the command function with given name.

		:param str command_name: name of the command function to get.
		:return: command function with given name.
		:rtype: Callable or None
		"""

		found_command_function = self._command_functions.get(command_name, None)
		if found_command_function is not None:
			return found_command_function

		if not self._modules:
			for module_path in self._command_module_paths:
				module = modules.import_module(module_path)
				if not modules:
					continue
				self._modules.append(module)
		if not self._modules:
			logger.warning(f'No modules to find command "{command_name}" in!')
			return None

		found_command_function = None
		for module in self._modules:
			try:
				module_function = getattr(module, command_name)
			except AttributeError:
				module_function = None
			if not module_function:
				continue
			found_command_function = module_function
			self._command_functions[command_name] = found_command_function
			break

		return found_command_function

	def categories(self) -> List[str]:
		"""
		Returns a list with all available categories.

		:return: list of category names.
		:rtype: List[str]
		"""

		all_categories = set()
		for command in self._commands_data.values():
			command_category = command.get('category', '')
			if not command_category:
				continue
			all_categories.add(command_category)
		categories = list(all_categories)
		categories.sort(key=str.lower)

		return categories

	def scene_metadata(self) -> Dict:
		"""
		Returns scene metadata.

		:return: report metadata.
		:rtype: Dict
		"""

		return {
			'user': getpass.getuser(),
			'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
			'dccVersion': dcc.version(),
			'dccScene': dcc.scene_name() or 'Untitled'
		}

	def clear_report(self):
		"""
		Clears report related internal variables.
		"""

		self._results.clear()

	@decorators.abstractmethod
	def top_node(self) -> str:
		"""
		Returns the name of the top node from current selection.

		:return: top node name.
		:rtype: str
		"""

		raise NotImplementedError()

	@decorators.abstractmethod
	def select_nodes(self, nodes: List[str]):
		"""
		Selects all given nodes.

		:param List[str] nodes: list of node names to select.
		"""

		raise NotImplementedError()

	@decorators.abstractmethod
	def filter_nodes(self, top_node: str | None = None) -> List[str]:
		"""
		Returns valid nodes to be considered during the checking process of a command.

		:param str or None top_node: optional top node to filter hierarchy of. If not given, all nodes
			within current scene will be considered as valid ones.
		:return: list of filtered node names.
		:rtype: List[str]
		"""

		raise NotImplementedError()

	@decorators.abstractmethod
	def run_commands(self, command_names: List[str], nodes: List[str]) -> Dict:
		"""
		Run given command names.

		:param List[str] command_names: list of command names to run.
		:param List[str] or None nodes: optional list of filter node names.
		:return: dictionary containing the result of the executed commands.
		:rtype: Dict
		"""

		raise NotImplementedError()
