from __future__ import annotations

import json
import copy
import pprint
import typing
from typing import Dict, Any

from tp.common.python import helpers

from tp.libs.rig.crit import consts
from tp.libs.rig.crit.maya.descriptors import layers


SCENE_LAYER_ATTR_TO_DESCRIPTOR = {
	consts.INPUT_LAYER_DESCRIPTOR_KEY: [
		consts.CRIT_DESCRIPTOR_CACHE_INPUT_DAG_ATTR,
		consts.CRIT_DESCRIPTOR_CACHE_INPUT_SETTINGS_ATTR,
		consts.CRIT_DESCRIPTOR_CACHE_INPUT_METADATA_ATTR,
		''
	],
	consts.OUTPUT_LAYER_DESCRIPTOR_KEY: [
		consts.CRIT_DESCRIPTOR_CACHE_OUTPUT_DAG_ATTR,
		consts.CRIT_DESCRIPTOR_CACHE_OUTPUT_SETTINGS_ATTR,
		consts.CRIT_DESCRIPTOR_CACHE_OUTPUT_METADATA_ATTR,
		''
	],
	consts.GUIDE_LAYER_DESCRIPTOR_KEY: [
		consts.CRIT_DESCRIPTOR_CACHE_GUIDE_DAG_ATTR,
		consts.CRIT_DESCRIPTOR_CACHE_GUIDE_SETTINGS_ATTR,
		consts.CRIT_DESCRIPTOR_CACHE_GUIDE_METADATA_ATTR,
		consts.CRIT_DESCRIPTOR_CACHE_GUIDE_DG_ATTR,
	],
	consts.SKELETON_LAYER_DESCRIPTOR_KEY: [
		consts.CRIT_DESCRIPTOR_CACHE_DEFORM_DAG_ATTR,
		consts.CRIT_DESCRIPTOR_CACHE_DEFORM_SETTINGS_ATTR,
		consts.CRIT_DESCRIPTOR_CACHE_DEFORM_METADATA_ATTR,
		''
	],
	consts.RIG_LAYER_DESCRIPTOR_KEY: [
		consts.CRIT_DESCRIPTOR_CACHE_RIG_DAG_ATTR,
		consts.CRIT_DESCRIPTOR_CACHE_RIG_SETTINGS_ATTR,
		consts.CRIT_DESCRIPTOR_CACHE_RIG_METADATA_ATTR,
		consts.CRIT_DESCRIPTOR_CACHE_RIG_DG_ATTR,
	]
}


def load_descriptor(descriptor_data: Dict, original_descriptor: Dict, path: str | None = None) -> ComponentDescriptor:
	"""
	Loads descriptor instance from given data.

	:param Dict descriptor_data: descriptor data.
	:param Dict original_descriptor: original descriptor.
	:param str or None path: optional descriptor path.
	:return: component descriptor instance.
	:rtype: ComponentDescriptor
	"""

	latest_data = migrate_to_latest_version(descriptor_data, original_descriptor=original_descriptor)
	return ComponentDescriptor(data=latest_data, original_descriptor=copy.deepcopy(original_descriptor), path=path)


def migrate_to_latest_version(descriptor_data: Dict, original_descriptor: Dict | None = None):
	"""
	Migrates descriptor schema from an old version to the latest one.

	:param Dict descriptor_data: descriptor data as a raw dictionary.
	:param Dict original_descriptor: original descriptor.
	:return: translated descriptor data to the latest schema.
	:rtype: Dict
	"""

	# expect rig layer to come from the base descriptor not the scene, so keep original rig data
	if original_descriptor:
		descriptor_data[consts.RIG_LAYER_DESCRIPTOR_KEY] = original_descriptor.get(
			consts.RIG_LAYER_DESCRIPTOR_KEY, dict())

	return descriptor_data


def parse_raw_descriptor(descriptor_data: Dict) -> Dict:
	"""
	Function that parses the given descriptor data by transforming strings into dictionaries and by removing
	all descriptor keys that are empty.

	:param Dict descriptor_data: descriptor data usually retrieved from current scene.
	:return: cleanup descriptor data.
	:rtype: Dict
	"""

	translated_data = dict()

	for k, v in descriptor_data.items():
		if not v:
			continue
		if k == 'info':
			translated_data.update(json.loads(v))
			continue
		elif k == consts.SPACE_SWITCH_DESCRIPTOR_KEY:
			translated_data[consts.SPACE_SWITCH_DESCRIPTOR_KEY] = json.loads(v)
			continue
		dag, settings, metadata = (
			v[consts.DAG_DESCRIPTOR_KEY] or '[]',
			v[consts.SETTINGS_DESCRIPTOR_KEY] or ('{}' if k == consts.RIG_LAYER_DESCRIPTOR_KEY else '[]'),
			v[consts.METADATA_DESCRIPTOR_KEY] or '[]'
		)
		translated_data[k] = {
			consts.DAG_DESCRIPTOR_KEY: json.loads(dag),
			consts.SETTINGS_DESCRIPTOR_KEY: json.loads(settings),
			consts.METADATA_DESCRIPTOR_KEY: json.loads(metadata)
		}

	return translated_data


class ComponentDescriptor(helpers.ObjectDict):
	"""
	Class that describes a component.
	"""

	VERSION = '1.0'

	def __init__(self, data: Dict | None = None, original_descriptor: Dict | None = None, path: str | None = None):
		super().__init__(data)

		data = data or dict()
		data[consts.VERSION_DESCRIPTOR_KEY] = self.VERSION
		# data[consts.INPUT_LAYER_DESCRIPTOR_KEY] = layers.InputLayerDescriptor.from_data(
		# 	data.get(consts.INPUT_LAYER_DESCRIPTOR_KEY, dict()))
		# data[consts.OUTPUT_LAYER_DESCRIPTOR_KEY] = layers.OutputLayerDescriptor.from_data(
		# 	data.get(consts.OUTPUT_LAYER_DESCRIPTOR_KEY, dict()))
		data[consts.GUIDE_LAYER_DESCRIPTOR_KEY] = layers.GuideLayerDescriptor.from_data(
			data.get(consts.GUIDE_LAYER_DESCRIPTOR_KEY, dict()))
		# data[consts.SKELETON_LAYER_DESCRIPTOR_KEY] = layers.SkeletonLayerDescriptor.from_data(
		# 	data.get(consts.SKELETON_LAYER_DESCRIPTOR_KEY, dict()))
		# data[consts.RIG_LAYER_DESCRIPTOR_KEY] = layers.RigLayerDescriptor.from_data(
		# 	data.get(consts.RIG_LAYER_DESCRIPTOR_KEY, dict()))
		data[consts.PARENT_DESCRIPTOR_KEY] = data.get(consts.PARENT_DESCRIPTOR_KEY, list())
		data[consts.CONNECTIONS_DESCRIPTOR_KEY] = data.get(consts.CONNECTIONS_DESCRIPTOR_KEY, dict())
		# data[consts.SPACE_SWITCH_DESCRIPTOR_KEY] = [spaceswitch.SpaceSwitchDescriptor(i) for i in data.get(consts.SPACE_SWITCH_DESCRIPTOR_KEY, list())]

		super(ComponentDescriptor, self).__init__(data)

		self.path = path or ''
		self.original_descriptor = ComponentDescriptor(original_descriptor) if original_descriptor is not None else dict()

	def __repr__(self) -> str:
		return f'<{self.__class__.__name__}> {self.name}'

	def __getattr__(self, item: str) -> Any:
		try:
			return self[item]
		except KeyError:
			pass
		guid = self.guideLayer.guide(item)
		if guid is not None:
			return guid

		return super(ComponentDescriptor, self).__getattribute__(item)

	@property
	def guide_layer(self) -> layers.GuideLayerDescriptor | None:
		return self[consts.GUIDE_LAYER_DESCRIPTOR_KEY]

	def serialize(self) -> Dict:
		"""
		Serializes the contents of the descriptor.

		:return: serialized descriptor.
		:rtype: Dict
		"""

		data = dict()

		for k, v in self.items():
			if k in ('original_descriptor', 'path'):
				continue
			data[k] = v

		spaces = list()

		return data

	def to_json(self, template: bool = False) -> str:
		"""
		Returns the string version of this descriptor.

		:param bool template: whether to return the version template of the descriptor.
		:return: descriptor as a string.
		:rtype: str
		"""

		return json.dumps(self.to_template() if template else self.serialize())

	def to_scene_data(self):
		"""

		:return:
		"""

		serialized_data = self.serialize()

		output_data = dict()

		for layer_key, [dag_layer_attr_name, settings_attr_name, metadata_attr_name, dg_attr_name] in SCENE_LAYER_ATTR_TO_DESCRIPTOR.items():
			layer_data = serialized_data.get(layer_key, dict())
			output_data[dag_layer_attr_name] = json.dumps(layer_data.get(consts.DAG_DESCRIPTOR_KEY, list()))
			output_data[settings_attr_name] = json.dumps(layer_data.get(consts.SETTINGS_DESCRIPTOR_KEY, list() if layer_key != consts.RIG_LAYER_DESCRIPTOR_KEY else dict()))
			output_data[metadata_attr_name] = json.dumps(layer_data.get(consts.METADATA_DESCRIPTOR_KEY, list()))
			if dg_attr_name:
				output_data[dg_attr_name] = json.dumps(layer_data.get(consts.DG_DESCRIPTOR_KEY, list()))

		space_switch_data = serialized_data.get(consts.SPACE_SWITCH_DESCRIPTOR_KEY, dict())
		output_data[consts.CRIT_DESCRIPTOR_CACHE_SPACE_SWITCHING_ATTR] = json.dumps(space_switch_data)

		info_data = dict()
		for key in (
				consts.NAME_DESCRIPTOR_KEY, consts.SIDE_DESCRIPTOR_KEY, consts.CONNECTIONS_DESCRIPTOR_KEY,
				consts.PARENT_DESCRIPTOR_KEY, consts.VERSION_DESCRIPTOR_KEY, consts.TYPE_DESCRIPTOR_KEY,
				consts.GUIDE_MARKING_MENU_DESCRIPTOR_KEY, consts.SKELETON_MARKING_MENU_DESCRIPTOR_KEY,
				consts.RIG_MARKING_MENU_DESCRIPTOR_KYE, consts.ANIM_MARKING_MENU_DESCRIPTOR_KEY,
				consts.NAMING_PRESET_DESCRIPTOR_KEY):
			info_data[key] = serialized_data.get(key, '')

		output_data[consts.CRIT_DESCRIPTOR_CACHE_INFO_ATTR] = json.dumps(info_data)

		return output_data

	def pprint(self):
		"""
		Pretty prints the current descriptor.
		"""

		pprint.pprint(dict(self.serialize()))
