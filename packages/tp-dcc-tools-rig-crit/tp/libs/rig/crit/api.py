from tp.core import dcc
from tp.common.naming.manager import NameManager

from tp.commands.crit import create_rig, create_components
from tp.libs.rig.crit import consts
from tp.libs.rig.crit.core import naming, namingpresets
from tp.libs.rig.crit.core.config import Configuration
from tp.libs.rig.crit.library.functions.descriptors import path_as_descriptor_expression

if dcc.is_maya():
	from tp.commands import crit as commands
	from tp.libs.rig.crit.maya.core.rig import Rig
	from tp.libs.rig.crit.maya.meta.nodes import ControlNode, Guide, Joint
	from tp.libs.rig.crit.maya.meta.layers import CritSkeletonLayer
	from tp.libs.rig.crit.maya.library.functions.rigs import (
		iterate_scene_rigs, iterate_scene_rig_meta_nodes, root_by_rig_name, load_rig_from_template,
		load_rig_from_template_file
	)
	from tp.libs.rig.crit.maya.library.functions.components import (
		components_from_nodes, component_from_node, components_from_selected
	)
	from tp.libs.rig.crit.maya.library.functions.guides import align_guides
	from tp.libs.rig.crit.maya.core.component import Component, SpaceSwitchUIDriver, SpaceSwitchUIDriven
	from tp.libs.rig.crit.maya.core.config import MayaConfiguration as Configuration
	from tp.libs.rig.crit.maya.library import components
