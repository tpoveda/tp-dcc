from overrides import override

import typing

from tp.core import log, dcc, tool
from tp.maya import api
from tp.maya.meta import base, metaproperty
from tp.common.python import helpers
from tp.common.qt import api as qt

from tp.libs.rig.freeform import consts
from tp.libs.rig.freeform.library.functions import skeleton
from tp.libs.rig.freeform.meta import properties
from tp.tools.rig.freeform.rigger import ui as rigger
from tp.tools.rig.freeform.regionseditor import ui as regionseditor

if typing.TYPE_CHECKING:
	from tp.libs.rig.freeform.meta.character import FreeformCharacter

logger = log.rigLogger


class FreeformRiggerTool(tool.Tool):

	id = 'tp.rig.freeform.rigger'
	creator = 'Tomi Poveda'
	tags = ['freeform', 'rig', 'ui']

	@override
	def execute(self, *args, **kwargs):

		if not dcc.is_maya() or dcc.version() < 2020:
			qt.show_warning(title='Unsupported version', message='Only supports Maya +2020')
			return

		win = rigger.FreeformRiggerWindow()
		win.show()


class FreeformRegionsEditorTool(tool.Tool):

	id = 'tp.rig.freeform.regionseditor'
	creator = 'Tomi Poveda'
	tags = ['freeform', 'regions', 'editor']

	@override
	def execute(self, *args, **kwargs):

		if not dcc.is_maya() or dcc.version() < 2020:
			qt.show_warning(title='Unsupported version', message='Only supports Maya +2020')
			return

		from tp.tools.rig.freeform.regionseditor import model, controller

		self._region_model = model.FreeformRegionsEditorModel()
		self._region_controller = controller.FreeformController()
		win = regionseditor.FreeformRegionsEditorWindow(model=self._region_model)

		rig_name = kwargs.get('rig_name', '')
		if not rig_name:
			logger.warning('No rig name provided')
			return

		self._rig = api.node_by_name(rig_name)
		if not self._rig:
			logger.warning(f'No rig node with name "{rig_name}" found within scene')
			return

		character_meta = base.create_meta_node_from_node(self._rig)			# type: FreeformCharacter
		root_joint = character_meta.joints().root_joint
		skeleton_dict = skeleton.skeleton_dict(root_joint)
		for side, region_dict in skeleton_dict.items():
			for region, joint_dict in region_dict.items():
				markup_properties = metaproperty.properties(
					[api.node_by_name(joint_dict['root'])], properties.RegionMarkupProperty)
				markup = helpers.first_in_list([x for x in markup_properties if x.data()[consts.SIDE_ATTR] == side and x.data()[consts.REGION_ATTR] == region])
				markup_data = markup.data()
				self._region_model.add_region(
					side=side, name=region, group=markup_data.get('group', ''), root=joint_dict['root'].fullPathName(),
					end=joint_dict['end'].fullPathName(), com_object=markup_data.get('comObject', ''),
					com_region=markup_data.get('comRegion', ''), com_weight=markup_data.get('comWeight', 0.0))

		self._region_model.rig_name = character_meta.name(include_namespace=False)

		self._region_model.pickEvent.connect(self._region_controller.pick_node)
		self._region_model.addRegionEvent.connect(self._region_controller.add_region)
		self._region_model.rootChangedEvent.connect(self._region_controller.change_root)
		self._region_model.endChangedEvent.connect(self._region_controller.change_end)

		win.show()
