from tp.preferences import manager


def crit_Interface():
	"""
	Returns the CRIT preference interface.

	:return: CRIT preference interface instance.
	:rtype: CritPreferenceInterface
	"""

	return manager.preference.interface('crit')
