def unique_name_for_rig(rigs: list['tp.libs.rig.crit.core.rig.Rig'], name: str):
	"""
	Returns a unique name for a rig.

	:param list['tp.libs.rig.crit.core.rig.Rig'] rigs: list of rig instances to compare names with.
	:param str name: new name for the rig.
	:return: unique name for the rig based on the comparison with the names of the list of rigs.
	:rtype: str
	"""

	new_name = name
	current_names = [i.name() for i in rigs]
	index = 1
	while new_name in current_names:
		new_name = name + str(index).zfill(3)
		index += 1

	return new_name
