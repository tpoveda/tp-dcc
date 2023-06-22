from __future__ import annotations

import typing
from typing import List, Dict

from tp.core import dcc, command
from tp.maya.cmds import contexts

if typing.TYPE_CHECKING:
	from tp.maya.api import DagNode
	from tp.libs.rig.crit.maya.core.rig import Rig
	from tp.libs.rig.crit.maya.core.component import Component


def create_rig(name: str | None = None, namespace: str | None = None) -> Rig:
	"""
	Creates a new rig instance or returns an existing one.

	:param str name: name of the rig. If not given, a new one will be generated.
	:param str namespace: optional rig namespace.
	:return: newly created rig.
	:rtype: Rig
	"""

	if dcc.is_maya():
		with contexts.disable_node_editor_add_node_context():
			return command.execute('crit.rig.create', **locals())

	return command.execute('crit.rig.create', **locals())


def create_components(
		rig: Rig, components: List[Dict], build_guides: bool = False, build_rigs: bool = False,
		parent_node: DagNode | None = None) -> List[Component]:
	"""
	Creates components under the given rig.

	:param Rig rig: rig we want to create components for.
	:param List[Dict] components: list with the data of the components to create. e.g:
		[
			{'type': 'root', 'name': 'Root', 'side': 'left', 'descriptor': None},
			{'type': 'fkspine', 'name': 'Spine', 'side': 'right', 'descriptor': None},
		]
	:param bool build_guides: whether component guides should be built.
	:param bool build_rigs: whether component rigs should be built.
	:param DagNode or None parent_node: optional component root node parent node.
	:return: list of created components.
	:rtype: List[Component]
	"""

	if dcc.is_maya():
		with contexts.disable_node_editor_add_node_context():
			return command.execute('crit.rig.create.components', **locals())

	return command.execute('crit.rig.create.components', **locals())
