from tp.core import dcc

from tp.libs.rig.crit.core.project import Project
from tp.libs.rig.crit.core.asset import Asset
from tp.libs.rig.crit.core import naming, namingpresets
from tp.libs.rig.crit.core.config import Configuration

if dcc.is_maya():
	from tp.libs.rig.crit.maya.core.build import Build
	from tp.libs.rig.crit.maya.core.rig import Rig
	from tp.libs.rig.crit.maya.library import io
	from tp.libs.rig.crit.maya.library.functions.rigs import iterate_scene_rigs, iterate_scene_rig_meta_nodes
	from tp.libs.rig.crit.maya.library.functions.components import (
		components_from_nodes, component_from_node, components_from_selected
	)
	from tp.libs.rig.crit.maya.core.component import Component
	from tp.libs.rig.crit.maya.core.config import MayaConfiguration as Configuration
	from tp.libs.rig.crit.maya.library import components
