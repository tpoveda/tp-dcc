from __future__ import annotations

from typing import List, Dict

from overrides import override
import pymel.core as pm

from tp.core import log
from tp.maya import api
from tp.maya.meta import base

from tp.libs.rig.noddle import consts
from tp.libs.rig.noddle.functions import naming, attributes

logger = log.rigLogger


class Component(base.MetaBase):

	ID = 'noddleComponent'
	REQUIRED_PLUGINS = []

	@classmethod
	def load_required_plugins(cls):
		"""
		Loads all the required plugins for this component to work as expected.
		"""

		for plugin_name in cls.REQUIRED_PLUGINS:
			if not pm.pluginInfo(plugin_name, query=True, loaded=True):
				try:
					logger.info(f'Loading plugin {plugin_name} required by {cls.as_str(name_only=True)}')
					pm.loadPlugin(plugin_name, quiet=True)
				except Exception:
					logger.exception(f'Failed to load plugin {plugin_name} required by {cls.as_str(name_only=True)}')
					raise

	@override(check_signature=False)
	def setup(self, parent: Component, component_name: str = 'component', side: str = 'c', tag: str = ''):

		logger.info(f'Building {self.as_str(name_only=True)}({side}_{component_name})')
		logger.info(f'Parent Component: {parent}')
		self.load_required_plugins()

		self.rename(naming.generate_name(component_name, side, suffix='meta'))
		self.set_tag(tag)

	@override
	def meta_attributes(self) -> list[dict]:

		attrs = super().meta_attributes()

		attrs.extend([
			dict(name='settings', type=api.kMFnMessageAttribute, isArray=True),
			dict(name='utilNodes', type=api.kMFnMessageAttribute, isArray=True)
		])

		return attrs

	@property
	def pynode(self) -> pm.PyNode:
		return pm.PyNode(self.fullPathName())

	@property
	def component_name(self) -> str:
		return naming.deconstruct_name(self.pynode).name

	@property
	def side(self) -> str:
		return naming.deconstruct_name(self.pynode).side

	@property
	def index(self) -> str:
		return naming.deconstruct_name(self.pynode).index

	@property
	def indexed_name(self) -> str:
		return naming.deconstruct_name(self.pynode).indexed_name

	@property
	def suffix(self) -> str:
		return naming.deconstruct_name(self.pynode).suffix

	def parent_component(self) -> Component | None:
		"""
		Returns the parent for this component.

		:return: parent component.
		:rtype: AnimComponent or None
		"""

		found_meta_parent = list(self.iterate_meta_parents(recursive=False))
		return found_meta_parent[0] if found_meta_parent else None

	def attach_to_component(self, parent_component: Component):
		"""
		Attaches this component into the given parent component.

		:param AnimComponent parent_component: component we want to attach this component under.
		"""

		if parent_component in self.iterate_meta_parents():
			return

		self.add_meta_parent(parent_component)
		logger.info(f'Meta Parent set {self} --> {parent_component}')

	def add_util_nodes(self, nodes: List[api.DGNode]):
		"""
		Connects given nodes into this meta node instance as util nodes.

		:param List[api.DGNode] nodes: nodes to add as util node.
		"""

		utils_array = self.attribute('utilNodes')
		for node in nodes:
			if not node.object():
				continue
			element = utils_array.nextAvailableDestElementPlug()
			node.message.connect(element)

	def _connect_settings(self, plugs: List[api.Plug]):
		"""
		Internal function that connects given plugs as settings for this component.

		:param List[api.Plug] plugs: plug representing component settings.
		"""

		for plug in plugs:
			if plug not in [_plug for _plug in self.attribute('settings').destinations()]:
				plug.connect(self.attribute('settings').nextAvailableDestElementPlug())
