#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tpDcc reroute decorator implementation
Decorator that reroutes the function call on runtime to specific DCC implementations of the given function
"""

import os
import importlib
from functools import wraps

from tp.core import log, dcc

logger = log.tpLogger

_REROUTE_CACHE = {}


def reroute_factory(module_path=None, module_name=None):
	def reroute(fn):
		@wraps(fn)
		def wrapper(*args, **kwargs):

			global _REROUTE_CACHE

			current_dcc = os.getenv('REROUTE_DCC', dcc.name())
			if not current_dcc:
				return None

			mod_path = module_path
			mod_name = module_name
			if not mod_path:
				mod_path = fn.__module__
			fn_name = fn.__name__
			fn_mod_path = '{}.dccs.{}'.format(mod_path.replace('-', '.'), current_dcc)
			if mod_name:
				fn_mod_path = '{}.{}'.format(fn_mod_path, mod_name)
			fn_path = '{}.{}'.format(fn_mod_path, fn_name)

			dcc_fn = _REROUTE_CACHE.get(fn_mod_path, dict()).get(fn_name, None)
			if not dcc_fn:
				fn_mod = None
				try:
					fn_mod = importlib.import_module(fn_mod_path)
				except ImportError as exc:
					logger.warning(
						'{} | Function {} not implemented: {}'.format(current_dcc, fn_path, exc))
				except Exception as exc:
					logger.warning(
						'{} | Error while rerouting function {}: {}'.format(current_dcc, fn_path, exc))
				if fn_mod:
					if hasattr(fn_mod, fn_name):
						_REROUTE_CACHE.setdefault(fn_mod_path, dict())
						_REROUTE_CACHE[fn_mod_path][fn_name] = getattr(fn_mod, fn_name)
					else:
						logger.warning('{} | Function {} not implemented!'.format(current_dcc, fn_path))
			dcc_fn = _REROUTE_CACHE.get(fn_mod_path, dict()).get(fn_name, None)
			if dcc_fn:
				return dcc_fn(*args, **kwargs)
			else:
				return fn(*args, **kwargs)

		return wrapper

	return reroute
