from tp.common.python import strings, osplatform


def is_development_mode_enabled():
	"""
	Returns whether development mode is enabled.

	:return: True if development mode is enabled; False otherwise.
	:rtype: bool
	"""

	return strings.to_boolean(osplatform.get_env_var('TPDCC_DEV', 'False'))
