from __future__ import annotations

import typing

from tp.libs.rig.crit.maya.library.functions import rigs

if typing.TYPE_CHECKING:
	from tp.maya.api import DGNode
	from tp.libs.rig.crit.maya.core.rig import Rig
	from tp.libs.rig.crit.maya.core.component import Component


def component_from_node(node: DGNode, rig: Rig | None = None) -> Component | None:
	"""
	Tries to find and returns the attached components class of the node.

	:param DGNode node: node to find component from.
	:param Rig rig: optional rig instance to find searches of. If not given, all rigs within current scene will be
		checked.
	:return: found component.
	:rtype: Component or None
	:raises ValueError: if cannot find a meta node or the meta node is not a valid CRIT node.
	"""

	rig = rig or rigs.rig



def components_from_selected():
	pass