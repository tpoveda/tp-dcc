from __future__ import annotations

from tp.maya import api

from tp.libs.rig.crit import api as crit
from tp.libs.rig.crit.maya.core import component
from tp.libs.rig.crit.maya.library.functions import joints


class VChainComponent(component.Component):

	ID = 'vlimbchain'

	def setup_rig(self, parent_node: crit.Joint | api.DagNode | None = None):
		pass
