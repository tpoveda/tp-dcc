from __future__ import annotations

import typing

from tp.core import dcc, command
from tp.maya.cmds import contexts

if typing.TYPE_CHECKING:
	from tp.libs.rig.crit.maya.core.rig import Rig


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
