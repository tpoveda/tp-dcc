import re

import maya.cmds as cmds

from tp.core import log
from tp.common.python import helpers
from tp.preferences.interfaces import crit

logger = log.rigLogger


def naming_template() -> str:
	"""
	Returns the current naming template to use.

	:return: naming template to use. Eg. '{side}_{name}_{suffix}'
	:rtype: str
	"""

	crit_preferences = crit.crit_interface()
	all_templates = crit_preferences.naming_templates()
	current_name = crit_preferences.current_naming_template()
	return all_templates.get(current_name)


def generate_name(name, side, suffix, override_index=None):

	if isinstance(name, (list, tuple)):
		name = '_'.join(name)

	crit_preferences = crit.crit_interface()
	timeout = 300
	template = naming_template()
	index = crit_preferences.name_start_index()
	zfill = crit_preferences.name_index_padding()
	index_str = str(index).zfill(zfill) if override_index is None else override_index
	indexed_name = f'{name}_{index_str}'
	full_name = template.format(side=side, name=indexed_name, suffix=suffix)
	while cmds.objExists(full_name):
		index += 1
		index_str = str(index).zfill(zfill) if override_index is None else override_index
		indexed_name = f'{name}_{index_str}'
		full_name = template.format(side=side, name=indexed_name, suffix=suffix)
		if index == timeout:
			logger.warning(f'Reached maximum number of iterations ({timeout}')
			break

	return full_name


def deconstruct_name(full_name: str) -> helpers.ObjectDict:
	"""
	Deconstruct name tokens using template.

	:param str full_name: name to deconstruct.
	:return: deconstructed name dictionary.
	:rtype: helpers.ObjectDict
	"""

	template = naming_template()
	full_name = full_name.split(':')[-1].split('|')[-1]
	name_parts = full_name.split('_')
	re_index = re.compile(r"\d+|^$")
	all_indexes = list(filter(re_index.match, name_parts))

	print(full_name)
	print(all_indexes)

	# index_index = len(name_parts) - name_parts[::-1].index(all_indexes[-1]) - 1
	# index = name_parts[index_index]
	# name_start_index = template.split('_').index('{name}')
	# name = '_'.join(name_parts[name_start_index:index_index])
	# indexed_name = '_'.join(name_parts[name_start_index:index_index + 1])
	# temp_name = full_name.replace(indexed_name, 'name')
	# side_index = template.split('_').index('{side}')
	# suffix_index = template.split('_').index('{suffix}')
	# side = temp_name.split('_')[side_index]
	# suffix = temp_name.split('_')[suffix_index]
	#
	# data = helpers.ObjectDict()
	# data.update({
	# 	'side': side,
	# 	'name': name,
	# 	'indexed_name': indexed_name,
	# 	'index': index,
	# 	'suffix': suffix
	# })
	#
	# return data
