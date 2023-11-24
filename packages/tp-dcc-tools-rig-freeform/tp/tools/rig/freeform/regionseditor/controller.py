from __future__ import annotations

import typing

import maya.cmds as cmds

from tp.maya import api
from tp.maya.cmds import joint
from tp.common.python import helpers
from tp.common.qt import api as qt
from tp.maya.meta import metaproperty

from tp.libs.rig.freeform import consts
from tp.libs.rig.freeform.meta import properties

if typing.TYPE_CHECKING:
	from tp.tools.rig.freeform.regionseditor.model import FreeformRegionsEditorModel, RegionEvent, FreeformRegion


class FreeformController(qt.QObject):

	def pick_node(self, selection_name: str):
		"""
		Pick node from current selected node.

		:param selection_name: whether to select "root" or "end" joint.
		"""

		model = self.sender()			# type: FreeformRegionsEditorModel
		selection = helpers.first_in_list(api.selected())
		if selection:
			if selection_name == 'root':
				model.root = selection.name(include_namespace=False)
			elif selection_name == 'end':
				model.end = selection.name(include_namespace=False)

	def add_region(self, event: RegionEvent):
		"""
		Adds new region.

		:param RegionEvent event: region event.
		"""

		selection = api.selected()
		root_joint = api.node_by_name(event.region.root) if cmds.objExists(event.region.root) else None
		end_joint = api.node_by_name(event.region.end) if cmds.objExists(event.region.end) else None
		if not root_joint or not end_joint:
			cmds.confirmDialog(
				title='Cannot Add Markup', message='Root or End joints not found', button=['OK'], defaultButton='OK',
				cancelButton='OK', dismissString='OK')
			return

		markup_properties = metaproperty.properties(
			[root_joint, end_joint], properties.RegionMarkupProperty)  # type: list[properties.RegionMarkupProperty]
		markup_exists = True if self._matching_markup(markup_properties, event.region) else False
		valid_check = joint.is_joint_below_hierarchy(end_joint.fullPathName(), root_joint.fullPathName())
		if valid_check and not markup_exists and root_joint and end_joint:
			self._add_region_properties(
				joint=root_joint, side=event.region.side, region=event.region.name, tag='root',
				group=event.region.group, com_object=event.region.com_object, com_region=event.region.com_region,
				com_weight=event.region.com_weight)
			self._add_region_properties(
				joint=end_joint, side=event.region.side, region=event.region.name, tag='end', group=event.region.group,
				com_object=event.region.com_object, com_region=event.region.com_region,
				com_weight=event.region.com_weight)
			event.success = True
		else:
			dialog_message = 'Markup already exists on joints.' if markup_exists else 'Cannot find picked joints'
			dialog_message = dialog_message if valid_check else 'Root and End joints cannot create a joint chain.'
			cmds.confirmDialog(
				title='Cannot add region markup', message=dialog_message,
				button=['OK'], defaultButton='OK', cancelButton='OK', dismissString='OK')

		api.select(selection)

	def change_root(self, event: RegionEvent):
		"""
		Checks whether the root region defined within event is valid.

		:param RegionEvent event: region event.
		"""

		old_root = api.node_by_name(event.region.root) if cmds.objExists(event.region.root) else None
		end_joint = api.node_by_name(event.region.end) if cmds.objExists(event.region.end) else None
		new_root = api.node_by_name(event.value) if cmds.objExists(event.value) else None

		valid_check = joint.is_joint_below_hierarchy(
			end_joint.fullPathName(), new_root.fullPathName()) if old_root and new_root else False
		if not valid_check:
			cmds.confirmDialog(
				title='Cannot change markup', message='Root and End joints cannot create a joint chain',
				button=['OK'], defaultButton='OK', cancelButton='OK', dismissString='OK')
			return

		markup_properties = metaproperty.properties(
			[old_root], properties.RegionMarkupProperty)		# type: list[properties.RegionMarkupProperty]
		for markup in self._matching_markup(markup_properties, event.region):
			markup.disconnect(old_root)
			markup.connect_node(new_root)
		event.success = True

	def change_end(self, region_event: RegionEvent):
		"""
		Checks whether the end region defined within event is valid.

		:param RegionEvent region_event: region event.
		"""

		old_end = api.node_by_name(region_event.region.end) if cmds.objExists(region_event.region.end) else None
		root_joint = api.node_by_name(region_event.region.root) if cmds.objExists(region_event.region.root) else None
		new_end = api.node_by_name(region_event.value) if cmds.objExists(region_event.value) else None

		valid_check = joint.is_joint_below_hierarchy(
			new_end.fullPathName(), root_joint.fullPathName()) if old_end and new_end else False
		if not valid_check:
			cmds.confirmDialog(
				title='Cannot change markup', message='Root and End joints cannot create a joint chain',
				button=['OK'], defaultButton='OK', cancelButton='OK', dismissString='OK')
			return

		markup_properties = metaproperty.properties(
			[old_end], properties.RegionMarkupProperty)		# type: list[properties.RegionMarkupProperty]
		for markup in self._matching_markup(markup_properties, region_event.region):
			markup.disconnect(old_end)
			markup.connect_node(new_end)
		region_event.success = True

	def _matching_markup(
			self, properties_list: list[properties.RegionMarkupProperty],
			region: FreeformRegion) -> list[properties.RegionMarkupProperty]:
		"""
		Internal function that returns the scene network rig markup node that matches the info given in the region model.

		:param list[properties.RegionMarkupProperty] properties_list:
		:param FreeformRegion region:
		:return: list of region markup nodes that matches the side and value of the given region.
		:rtype: list[properties.RegionMarkupProperty]
		"""

		markup_network_nodes = []
		for markup_network in properties_list:
			if markup_network.attribute(consts.SIDE_ATTR).value() == region.side and \
					markup_network.attribute(consts.REGION_ATTR).value() == region.name:
				markup_network_nodes.append(markup_network)

		return markup_network_nodes

	def _add_region_properties(
			self, joint: api.Joint, side: str, region: str, tag: str, group: str, com_object: str, com_region: str,
			com_weight: float):
		"""
		Internal function that adds a RegionMarkupProperty into the given node object.

		:param api.Joint joint: joint we want to add region markup property to.
		:param str side: name of the side.
		:param str region: name of the region.
		:param str tag: whether we are adding a root or end property.
		:param str group: name of the group.
		:param str com_object: name of the COM object.
		:param str com_region: name of the COM region.
		:param float com_weight: weight of the COM.
		"""

		rig_property = metaproperty.add_property(joint, properties.RegionMarkupProperty)
		rig_property.set_data({
			consts.SIDE_ATTR: side, consts.REGION_ATTR: region, consts.TAG_ATTR: tag, consts.GROUP_ATTR: group,
			consts.COM_OBJECT_ATTR: com_object, consts.COM_REGION_ATTR: com_region, consts.COM_WEIGHT_ATTR: com_weight
		})
