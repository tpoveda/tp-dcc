from __future__ import annotations

import typing
from typing import Iterator

from tp.common.python import helpers
from tp.maya.meta import base

from tp.libs.rig.crit import consts
from tp.libs.rig.crit.core import errors
from tp.libs.rig.crit.maya.core import rig

if typing.TYPE_CHECKING:
	from tp.maya.api import DGNode
	from tp.libs.rig.crit.maya.meta.rig import CritRig


def iterate_scene_rig_meta_nodes() -> Iterator[CritRig]:
	"""
	Generator function that iterates over all rig meta node instances within the current scene.

	:return: iterated scene rig meta node instances.
	:rtype: Iterator[CritRig]
	"""

	for found_meta_rig in base.find_meta_nodes_by_class_type(consts.RIG_TYPE):
		yield found_meta_rig


def iterate_scene_rigs() -> Iterator[rig.Rig]:
	"""
	Generator function that iterates over all rig instances within the current scene.

	:return: iterated scene rig instances.
	:rtype: Iterator[Rig]
	"""

	for meta_rig in iterate_scene_rig_meta_nodes():
		rig_instance = rig.Rig(meta=meta_rig)
		rig_instance.start_session()
		yield rig_instance


def root_by_rig_name(name: str, namespace: str | None = None) -> CritRig | None:
	"""
	Finds the root meta with the given name in the "name" attribute.

	:param str name: rig name to find meta node rig instance.
	:param str or None namespace: optional valid namespace to search for the rig meta node instance.
	:return: found root meta node instance with given name.
	:rtype: CritRig or None
	"""

	meta_rigs = list()
	meta_rig_names = list()

	found_meta_rig = None
	for meta_node in iterate_scene_rig_meta_nodes():
		meta_rigs.append(meta_node)
		meta_rig_names.append(meta_node.attribute(consts.CRIT_NAME_ATTR).value())
	if not meta_rigs:
		return None
	if not namespace:
		dupes = helpers.duplicates_in_list(meta_rig_names)
		if dupes:
			raise errors.CritRigDuplicationError(dupes)
		for meta_rig in meta_rigs:
			if meta_rig.attribute(consts.CRIT_NAME_ATTR).value() == name:
				found_meta_rig = meta_rig
				break
	if found_meta_rig is None and namespace:
		namespace = namespace if namespace.startswith(':') else f':{namespace}'
		for meta_rig in meta_rigs:
			rig_namespace = meta_rig.namespace()
			if rig_namespace == namespace and meta_rig.attribute(consts.CRIT_NAME_ATTR).value() == name:
				found_meta_rig = meta_rig
				break

	return found_meta_rig


def rig_from_node(node: DGNode) -> rig.Rig | None:
	"""
	Returns rig from given node.

	:param DGNode node: scene node to find rig from.
	:return: found rig.
	:rtype: rig.Rig or None
	"""

	meta_nodes = base.
