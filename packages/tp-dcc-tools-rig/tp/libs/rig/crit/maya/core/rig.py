from __future__ import annotations

import collections

from tp.core import log
from tp.common.python import helpers, profiler
from tp.maya.meta import base

from tp.libs.rig.crit import consts
from tp.libs.rig.crit.core import errors
from tp.libs.rig.crit.maya.core import config
from tp.libs.rig.crit.maya.meta import rig

logger = log.rigLogger


def iterate_scene_rig_meta_nodes() -> collections.Iterator[rig.CritRig]:
	"""
	Generator function that iterates over all rig meta node instances within the current scene.

	:return: iterated scene rig meta node instances.
	:rtype: collections.Iterator[rig.CritRig]
	"""

	for found_meta_rig in base.find_meta_nodes_by_class_type(consts.RIG_TYPE):
		yield found_meta_rig


def iterate_scene_rigs() -> collections.Iterator[Rig]:
	"""
	Generator function that iterates over all rig instances within the current scene.

	:return: iterated scene rig instances.
	:rtype: collections.Iterator[Rig]
	"""

	for meta_rig in iterate_scene_rig_meta_nodes():
		rig_instance = Rig(meta=meta_rig)
		rig_instance.start_session()
		yield rig_instance


def root_rig_by_name(name:str, namespace: str | None = None) -> rig.CritRig | None:
	"""
	Finds the root meta with the given name in the "name" attribute.

	:param str name: rig name to find meta node rig instance.
	:param str or None namespace: optional valid namespace to search for the rig meta node instance.
	:return: found root meta node instance with given name.
	:rtype: rig.CritRig or None
	"""

	meta_rigs = list()
	meta_rig_names = list()

	found_meta_rig = None
	for found_meta_rig in iterate_scene_rig_meta_nodes():
		meta_rigs.append(found_meta_rig)
		meta_rig_names.append(found_meta_rig.attribute(consts.CRIT_NAME_ATTR))
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


class Rig:
	"""
	Main entry class for any given rig, which is composed by a root node and a meta node.
	This class handles the construction and destruction of rig components.
	"""

	def __init__(self, rig_config: config.RigConfiguration | None = None, meta: rig.CritRig | None = None):
		super().__init__()

		self._meta = meta
		self._config = rig_config or config.RigConfiguration()

	def __repr__(self) -> str:
		return f'<{self.__class__.__name__}> name:{self.name()}'

	def __bool__(self) -> bool:
		return self.exists()

	def __eq__(self, other: Rig) -> bool:
		return self._meta == other.meta

	def __ne__(self, other: Rig) -> bool:
		return self._meta != other.meta

	def __hash__(self):
		return hash(self._meta) if self._meta is not None else hash(id(self))

	@property
	def meta(self) -> rig.CritRig:
		return self._meta

	@property
	def configuration(self) -> config.RigConfiguration:
		return self._config

	@profiler.fn_timer
	def start_session(self, name: str | None = None, namespace: str | None = None):
		"""
		Starts a rig session for the rig with given name.

		:param str or None name: optional rig name to initialize, if it does not exist, one will be created.
		:param namespace: optional rig namespace.
		:return: root meta node instance for this rig.
		:rtype: rig.CritRig
		"""

		meta = self._meta
		if meta is None:
			meta = root_rig_by_name(name=name, namespace=namespace)
		if meta is not None:
			self._meta = meta
			logger.info(f'Found rig in scene, initializing rig "{self.name()}" for session')
			self.configuration.update_from_rig(self)
			return self._meta

		namer = self.naming_manager()
		meta = rig.CritRig(name=namer.resolve('rigMeta', {'rigName': name, 'type': 'meta'}))
		meta.attribute(consts.CRIT_NAME_ATTR).set(name)
		meta.attribute(consts.CRIT_ID_ATTR).set(name)
		meta.create_transform(namer.resolve('rigHrc', {'rigName': name, 'type': 'hrc'}))
		meta.create_selection_sets(namer)
		self._meta = meta

		return self._meta

	def exists(self) -> bool:
		"""
		Returns whether this rig exists by checking the existing of the meta node.

		:return: True if rig exists within current scene; False otherwise.
		:rtype: bool
		"""

		return self._meta is not None and self._meta.exists()

	def name(self) -> str:
		"""
		Retursn the name of the rig by accessing meta node data.

		:return: rig name.
		:rtype: str
		"""

		return self._meta.rig_name() if self.exists() else ''

	def naming_manager(self) -> 'tp.common.naming.manager.NameManager':
		"""
		Returns the naming manager for the current rig instance.

		:return: naming manager.
		:rtype: tp.common.naming.manager.NameManager
		"""

		return self.configuration.find_name_manager_for_type('rig')
