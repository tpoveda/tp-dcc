from tp.maya.meta import base


class MetaRigBase(base.DependentNode):

	DEPENDENT_NODE_CLASS = base.Core


class MetaRig(MetaRigBase):
	pass


class MetaSubSystem(MetaRigBase):
	pass


class MetaSupportSystem(MetaRigBase):
	pass
