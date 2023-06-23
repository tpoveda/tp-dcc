from __future__ import annotations

import collections

from tp.common.python import helpers
from tp.maya import api

from tp.libs.rig.crit import consts
from tp.libs.rig.crit.maya.descriptors import nodes, attributes, graphs


def traverse_descriptor_layer_dag(layer_descriptor: LayerDescriptor) -> collections.Iterator:
	"""
	Depth first search recursive generator function which walks the layer descriptor DAG nodes.

	:param LayerDescriptor layer_descriptor: layer descriptor to traverse.
	:return: iterated DAG nodes.
	:rtype: collections.Iterator
	"""

	def _node_iter(_node):
		for _child in iter(_node.get('children', list())):
			yield _child
			for i in _node_iter(_child):
				yield i

	for node in iter(layer_descriptor.get(consts.DAG_DESCRIPTOR_KEY, list())):
		yield node
		for child in _node_iter(node):
			yield child


class LayerDescriptor(helpers.ObjectDict):
	"""
	Base layer descriptor used as containers to organise a single CRIT rig structure.

	..warning:: this class should never be instantiated directly, but its subclasses.
	"""

	@classmethod
	def from_data(cls, layer_data: dict) -> LayerDescriptor:
		"""
		Transforms given data to valid descriptor instances and returns an instance of this layer descriptor based on
		given data.

		:param dict layer_data: layer dictionary data.
		:return: new layer descriptor instance.
		:rtype: LayerDescriptor
		"""

		return cls()

	def has_node(self, node_id: str) -> bool:
		"""
		Returns whether DAG node with given ID exists within this layer.

		:param str node_id: DAG node ID to check.
		:return: True if DAG node with given ID exists within this layer; False otherwise.
		:rtype: bool
		"""

		return self.node(node_id) is not None

	def node(self, node_id: str) -> nodes.TransformDescriptor:
		"""
		Returns DAG node from layer with given ID.

		:param str node_id: DAG node ID.
		:return: found DAG node with given ID.
		:rtype: nodes.TransformDescriptor
		"""

		for found_node in traverse_descriptor_layer_dag(self):
			if found_node['id'] == node_id:
				return found_node

	def iterate_nodes(self, include_root: bool = True) -> collections.Iterator[nodes.TransformDescriptor]:
		"""
		Generator function that iterates over all DAG nodes within this layer.

		:param bool include_root: whether to include root node.
		:return: iterated DAG nodes.
		:rtype: collections.Iterator[nodes.TransformDescriptor]
		"""

		for found_node in traverse_descriptor_layer_dag(self):
			if not include_root and found_node['id'] == 'root':
				continue
			yield found_node

	def find_nodes(self, *node_ids: tuple) -> list[nodes.TransformDescriptor | None]:
		"""
		Loops through all nodes within this layer and returns a list with found nodes.

		:param tuple[str] node_ids: list of node IDs to search.
		:return: list[nodes.TransformDescriptor | None]
		"""

		results = [None] * len(node_ids)
		for found_node in traverse_descriptor_layer_dag(self):
			node_id = found_node['id']
			if node_id in node_ids:
				results[node_ids.index(node_id)] = found_node

		return results


class GuideLayerDescriptor(LayerDescriptor):
	"""
	Guide layer descriptor class.
	"""

	def __getattr__(self, item: str) -> nodes.GuideDescriptor:
		"""
		Overrides __getattr__ function so guide objects are iterated and returns first one with the given name.

		:param str item: guide ID to get.
		:return: found guide or default behaviour.
		:rtype: nodes.GuideDescriptor
		"""

		key = self.get(item)
		if key is not None:
			return key

		guide = self.guide(item)
		if guide is not None:
			return guide

		return super().__getattribute__(item)

	def update(self, kwargs: dict):
		"""
		Overrides update function to update data with proper descriptors.

		:param dict kwargs: dictionary to update current one with.
		"""

		settings = self[consts.SETTINGS_DESCRIPTOR_KEY]
		consolidated_settings = dict((i['name'], i) for i in settings)
		for i in kwargs.get(consts.SETTINGS_DESCRIPTOR_KEY, list()):
			existing_setting = consolidated_settings.get(i['name'])
			if existing_setting is not None and i.get('value') is not None:
				existing_setting['value'] = i['value']
			else:
				consolidated_settings[i['name']] = attributes.attribute_class_for_descriptor(i)
		self[consts.SETTINGS_DESCRIPTOR_KEY] = list(consolidated_settings.values())

		current_guides = {i['id'] for i in self.iterate_guides()}
		new_or_updated = list()
		for guide_descriptor in traverse_descriptor_layer_dag(kwargs):
			new_or_updated.append(guide_descriptor['id'])
			current_node = self.guide(guide_descriptor['id'])
			guide_descriptor['pivotColor'] = current_node.get('pivotColor')
			guide_descriptor['pivotShape'] = current_node.get('pivotShape')
			if current_node is not None:
				children = guide_descriptor.get('children')
				if children:
					guide_descriptor['children'] = [nodes.GuideDescriptor.deserialize(i, guide_descriptor['id']) for i in children]
				current_node.update(guide_descriptor)
			else:
				self.create_guide(**guide_descriptor)
		to_purge = [i for i in current_guides if i not in new_or_updated]
		if to_purge:
			self.delete_guides(*to_purge)

		self[consts.METADATA_DESCRIPTOR_KEY] = [attributes.attribute_class_for_descriptor(s) for s in kwargs.get(
			consts.METADATA_DESCRIPTOR_KEY, list())] or self.get(consts.METADATA_DESCRIPTOR_KEY, list())

		dg_graphs = kwargs.get(consts.DG_DESCRIPTOR_KEY)
		if dg_graphs is not None:
			self[consts.DG_DESCRIPTOR_KEY] = graphs.NamedGraphs.from_data(dg_graphs)

	@classmethod
	def from_data(cls, layer_data: dict) -> GuideLayerDescriptor:
		"""
		Transforms given data to valid descriptor instances and returns an instance of this layer descriptor based on
		given data.

		:param dict layer_data: layer dictionary data.
		:return: new layer descriptor instance.
		:rtype: GuideLayerDescriptor
		"""

		new_settings = cls.merge_default_settings(layer_data.get(consts.SETTINGS_DESCRIPTOR_KEY, list()))
		new_metadata = cls.merge_default_metadata(layer_data.get(consts.METADATA_DESCRIPTOR_KEY, list()))

		data = {
			consts.DAG_DESCRIPTOR_KEY: [nodes.GuideDescriptor.deserialize(
				guide_data) for guide_data in iter(layer_data.get(consts.DAG_DESCRIPTOR_KEY, list()))],
			consts.SETTINGS_DESCRIPTOR_KEY: new_settings,
			consts.METADATA_DESCRIPTOR_KEY: new_metadata,
			consts.DG_DESCRIPTOR_KEY: graphs.NamedGraphs.from_data(layer_data.get(consts.DG_DESCRIPTOR_KEY, list()))
		}

		return cls(data)

	@classmethod
	def default_metadata_settings(cls) -> list[attributes.AttributeDescriptor]:
		"""
		Returns default metadata settings dictionary.

		:return: default metadata attribute settings.
		:rtype: list[attributes.AttributeDescriptor]
		"""

		data = [
			dict(name='guideVisibility', type=api.kMFnNumericBoolean, default=True, value=True),
			dict(name='guideControlVisibility', type=api.kMFnNumericBoolean, default=True, value=True),
			dict(name='pinSettings', type=api.kMFnCompoundAttribute, children=[
				dict(name='pinned', type=api.kMFnNumericBoolean),
				dict(name='pinnedConstraints', type=api.kMFnDataString),
			]),
		]

		return [attributes.attribute_class_for_descriptor(attr_data) for attr_data in data]

	@classmethod
	def default_guide_settings(cls) -> list[attributes.AttributeDescriptor]:
		"""
		Returns default guide setting dictionary.

		:return: default guide attribute settings.
		:rtype: list[attributes.AttributeDescriptor]
		"""

		data = [
			{
				'name': 'manualOrient', 'value': False, 'isArray': False, 'locked': False, 'default': False,
				'channelBox': True, 'keyable': False, 'type': api.kMFnNumericBoolean
			}
		]

		return [attributes.attribute_class_for_descriptor(attr_data) for attr_data in data]

	@classmethod
	def merge_default_settings(cls, new_state: dict) -> list[attributes.AttributeDescriptor]:
		"""
		Returns a dictionary with override guide settings based on default guide settings.

		:param dict new_state: override guide settings dictionary.
		:return: merged override default guide settings dictionary.
		:rtype: list[attributes.AttributeDescriptor]
		"""

		default_settings = dict((i['name'], i) for i in cls.default_guide_settings())
		for attr in new_state:
			existing_attr = default_settings.get(attr['name'])
			if existing_attr is not None:
				existing_attr['value'] = attr['value']
			else:
				default_settings[attr['name']] = attributes.attribute_class_for_descriptor(attr)

		return list(default_settings.values())

	@classmethod
	def merge_default_metadata(cls, new_state: dict) -> list[attributes.AttributeDescriptor]:
		"""
		Returns a dictionary with override metadata settings based on default metadata settings.

		:param dict new_state: override metadata settings dictionary.
		:return: merged override default metadata settings dictionary.
		:rtype: list[attributes.AttributeDescriptor]
		"""

		default_settings = dict((i['name'], i) for i in cls.default_guide_settings())
		for attr in new_state:
			default_settings[attr['name']] = attr

		return [attributes.attribute_class_for_descriptor(attr_data) for attr_data in default_settings.values()]

	def has_guides(self) -> bool:
		"""
		Returns whether this guide layer descriptor instances has guides.

		:return: True if this layer descriptor has guides; False otherwise.
		:rtype: bool
		"""

		return len(self.get(consts.DAG_DESCRIPTOR_KEY, list())) != 0

	def guide_count(self, include_root: bool = True) -> int:
		"""
		Returns the total amount of guides within this guide layer descriptor instance.

		:param bool include_root: whether to take root guide into consideration.
		:return: total amount of guides.
		:rtype: int
		"""

		return len(list(self.iterate_guides(include_root=include_root)))

	def iterate_guides(self, include_root: bool = True) -> collections.Iterator[nodes.GuideDescriptor]:
		"""
		Generator function that iterates over all guides defined within this descriptor instance.

		:param bool include_root: whether to take root guide into consideration.
		:return: collections.Iterator[nodes.GuideDescriptor]
		"""

		for guide_descriptor in iter(self.get(consts.DAG_DESCRIPTOR_KEY, list())):
			if not include_root and guide_descriptor.id == 'root':
				for child_descriptor in guide_descriptor.iterate_children():
					yield child_descriptor
			else:
				yield guide_descriptor
				for child_descriptor in guide_descriptor.iterate_children():
					yield child_descriptor

	def find_guides(self, *ids: tuple) -> list[nodes.GuideDescriptor | None]:
		"""
		Finds and returns all guides with the given IDs.

		:param tuple[str] ids: guide IDs to find.
		:return: list of guides in given order.
		:rtype: list[nodes.GuideDescriptor or None]
		"""

		return self.find_nodes(*ids)

	def has_guide(self, guide_id: str) -> bool:
		"""
		Returns whether guide with given ID exists within this descriptor.

		:param str guide_id: ID of the guide to search for.
		:return: True if guide with given ID exists within this descriptor; False otherwise.
		:rtype: bool
		"""

		return self.has_node(guide_id)

	def guide(self, guide_id: str ) -> nodes.GuideDescriptor | None:
		"""
		Returns the guide descriptor instance attached to this guide layer descriptor instance with given ID.

		:param str guide_id: guide ID value.
		:return: found guide descriptor instance with given ID.
		:rtype: nodes.GuideDescriptor or None
		"""

		return self.node(guide_id)

	def create_guide(self, **info: dict):
		"""
		Creates a new guide based on given info.

		:param dict info: guide data.
		:return: newly guide descriptor instance.
		:rtype: nodes.GuideDescriptor
		"""

		existing_guide = self.guide(info['id'])
		if existing_guide is not None:
			return existing_guide

		new_guide_descriptor = nodes.GuideDescriptor.deserialize(info, parent=info.get('parent'))
		self.add_guide(new_guide_descriptor)

		return new_guide_descriptor

	def set_guide_parent(self, child: nodes.GuideDescriptor, parent: nodes.GuideDescriptor):
		"""

		:param nodes.GuideDescriptor child: guide descriptor we want to set parent of.
		:param nodes.GuideDescriptor parent: guide descriptor we want to set as parent.
		:return: True if the set guide parent operation was successful; False otherwise.
		:rtype: bool
		"""

		if child.parent == parent:
			return False

		# Remove self from current parent and add self the new parent
		current_parent = self.guide(child.parent)
		if current_parent is not None:
			del current_parent.children[current_parent.children.index(child)]
		parent.children.append(child)
		child.parent = parent.id

		return True

	def add_guide(self, guide: nodes.GuideDescriptor) -> bool:
		"""
		Appends a new guide descriptor to this descriptor.

		:param nodes.GuideDescriptor guide: guide descriptor to add.
		:return: True if the add guide descriptor operation was successful; False otherwise.
		:rtype: bool
		"""

		guide['critType'] = 'guide'
		parent = guide.get('parent', None)
		if parent is None:
			self.setdefault(consts.DAG_DESCRIPTOR_KEY, list()).append(guide)
			return True

		parent_guide = None
		child = None
		for guide_descriptor in self.iterate_guides():
			if guide_descriptor['id'] == parent:
				parent_guide, child = guide_descriptor, guide
				break
		if parent_guide is not None:
			parent_guide['children'].append(child)

		return True

	def delete_guides(self, *guide_ids: tuple) -> bool:
		"""
		Deletes all guides with given IDs from this descriptor.

		:param tuple[str] guide_ids: list of guides IDs to delete.
		:return: True if the delete guides operation was successful; False otherwise.
		:rtype: bool
		"""

		root = self.guide('root')
		success = False
		for found_guide in self.iterate_guides():
			guide_id = found_guide.id
			if guide_id not in guide_ids:
				continue
			guide_parent_id = found_guide.parent
			guide_parent = self.guide(guide_parent_id) if guide_parent_id is not None else root
			if not guide_parent:
				continue
			deleted = guide_parent.delete_child(guide_id)
			if deleted:
				success = deleted

		return success

	def has_guide_setting(self, name: str) -> bool:
		"""
		Returns whether the given guide setting exists.

		:param str name: name of the guide setting to find.
		:return: True if the guide setting exists; False otherwise.
		:rtype: bool
		"""

		for guide_setting in self.iterate_guide_settings():
			if guide_setting.name == name:
				return True

		return False

	def iterate_guide_settings(self) -> collections.Iterator[attributes.AttributeDescriptor]:
		"""
		Generator function that iterates over all guide settings.

		:return: iterated guide settings.
		:rtype: collections.Iterator[attributes.AttributeDescriptor]
		"""

		return iter(self[consts.SETTINGS_DESCRIPTOR_KEY])

	def guide_setting(self, name: str) -> attributes.AttributeDescriptor | None:
		"""
		Returns the guide setting with the given name.

		:param str name: guide's setting name to retrieve.
		:return: found attribute descriptor with given name.
		:rtype: attribute.AttributeDescriptor or None
		"""

		for i in self.iterate_guide_settings():
			if i.name == name:
				return i

		return None

	def guide_settings(self, *names: tuple) -> helpers.ObjectDict[str, attributes.AttributeDescriptor]:
		"""
		Returns all matching guide settings attributes as a dict.

		:param tuple[str] names: guides settings attribute names to retrieve.
		:return: dictionary with the guide settings.
		:rtype: helpers.ObjectDict[str, attributes.AttributeDescriptor]
		"""

		settings = helpers.ObjectDict()
		for setting in self.iterate_guide_settings():
			name = setting.name
			if name in names:
				settings[name] = setting

		return settings

	def add_guide_setting(self, setting: attributes.AttributeDescriptor):
		"""
		Appends a new guide setting to this descriptor.

		:param attributes.AttributeDescriptor setting: attribute descriptor describing the guide setting.
		:return: True if the guide setting operation was successful; False otherwise.
		:rtype: bool
		"""

		if self.has_guide_setting(setting.name):
			return False

		self[consts.SETTINGS_DESCRIPTOR_KEY].append(setting)

		return True

	def delete_setting(self, name: str) -> bool:
		"""
		Deletes a setting by its name.

		:param str name: name of the setting to delete.
		:return: True if the delete setting operation was successful; False otherwise.
		:rtype: bool
		"""

		try:
			node_settings = self[consts.SETTINGS_DESCRIPTOR_KEY]
			for node_setting in node_settings:
				if node_setting.name == name:
					node_settings.remove(node_setting)
					return True
			return False
		except KeyError:
			return False

	def delete_settings(self, names: list[str]):
		"""
		Deletes all guide settings based on the given names.

		:param list[str] names: list of settings to delete.
		"""

		valid = list()
		for setting in self.iterate_guide_settings():
			if setting.name not in names:
				valid.append(setting)
		self[consts.SETTINGS_DESCRIPTOR_KEY] = valid
