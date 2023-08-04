from overrides import override

from tp.libs.rig.crit.maya.core import component
from tp.libs.rig.crit.maya.meta import nodes

GOD_NODE_ID = 'godnode'


class GodComponent(component.Component):

	ID = 'god'
	DESCRIPTION = 'Master component for all CRIT rigs'

	@override
	def setup_inputs(self):
		super().setup_inputs()

		descriptor = self.descriptor
		input_layer = self.input_layer()
		god_node_guide_descriptor = descriptor.guide_layer.guide(GOD_NODE_ID)
		input_node = input_layer.input_node(god_node_guide_descriptor.id)
		transform_matrix = god_node_guide_descriptor.transformation_matrix(scale=False)
		input_node.setWorldMatrix(transform_matrix.asMatrix())

	@override
	def setup_skeleton_layer(self, parent_joint: nodes.Joint):

		descriptor = self.descriptor
		guide_layer_descriptor = descriptor.guide_layer
		skeleton_layer_descriptor = descriptor.skeleton_layer
		requires_joint = guide_layer_descriptor.guide_setting('rootJoint').value
		has_existing_joint = skeleton_layer_descriptor.joint(GOD_NODE_ID)
		if requires_joint and not has_existing_joint:
			guide_descriptor = guide_layer_descriptor.guide(GOD_NODE_ID)
			skeleton_layer_descriptor.create_joint(
				name=guide_descriptor.name, id=GOD_NODE_ID, rotateOrder=guide_descriptor.get('rotateOrder', 0),
				translate=guide_descriptor.get('translate', (0.0, 0.0, 0.0)),
				rotate=guide_descriptor.get('rotate', (0.0, 0.0, 0.0, 1.0)), parent=None)
		elif not requires_joint and has_existing_joint:
			skeleton_layer_descriptor.delete_joints(GOD_NODE_ID)

		super().setup_skeleton_layer(parent_joint)
