#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya specific functions and classes to work with Maya evaluation cache.
This functionality is only available in Maya 2019 or newer versions.
"""

_EVALUATION_CACHE_AVAILABLE = True
try:
	from maya.plugin import evaluator
	from maya.app.prefs import OptionVarManager
except ImportError:
	# Do nothing on earlier versions of Maya.
	_EVALUATION_CACHE_AVAILABLE = False

_cache_rules = ('CACHE_STANDARD_MODE_VP2_HW', 'CACHE_STANDARD_MODE_VP2_SW', 'CACHE_STANDARD_MODE_EVAL')


def make_evaluation_cache_rule(node_type):
	"""
	Returns a valid evaluation cache rule for the given node type.

	:param str node_type: node type we want to create evaluation cache rule for.
	:return: evaluation cache rule.
	:rtype: dict
	"""

	return {
		'newFilter': 'nodeTypes',
		'newFilterParam': 'types=+{}'.format(node_type),
		'newAction': 'enableEvaluationCache'
	}


def enable_caching_for_node_type(node_type):
	"""
	Adds given given node type to the list of cachable nodes if it's not already present.

	:param str node_type: name of the node type we want to add to evaluation cache.
	"""

	if not _EVALUATION_CACHE_AVAILABLE:
		return

	rule = make_evaluation_cache_rule(node_type)

	# add the rule to each cache mode
	for mode in _cache_rules:
		cache_rules = getattr(evaluator.CacheEvaluatorManager, mode)
		if rule not in cache_rules:
			cache_rules.insert(0, rule)

	# Make sure cache sees our changes.
	optvar = OptionVarManager.OptionVarManager.option_vars.get('cachedPlaybackMode')
	if optvar is not None:
		optvar.set_state_from_preference()


def disable_caching_for_node_type(node_type):
	"""
	Removes given node type from the list of cachable nodes.

	:param str node_type: name of the node type we want to remove from evaluation cache.
	"""

	if not _EVALUATION_CACHE_AVAILABLE:
		return

	rule = make_evaluation_cache_rule(node_type)
	for mode in _cache_rules:
		cache_rules = getattr(evaluator.CacheEvaluatorManager, mode)
		if rule in cache_rules:
			cache_rules.remove(rule)

	# make sure cache sees our changes.
	evaluator.cache_preferences.OptionVarManager.set_state_from_preferences()
