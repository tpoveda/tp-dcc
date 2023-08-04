import os
import re

import maya.mel as mel
import maya.cmds as cmds

from tp.core import log
from tp.common.python import path

logger = log.tpLogger


def setup():
	"""
	Installs modifications to the dagProcMenu function for the current session.
	"""

	def _write_tp_lines(_fstream, _parent_var_str: str, _object_var_str: str):
		_fstream.write('\n/// TPDCC MODS ########################\n')
		_fstream.write('\tsetParent -m $parent;\n')
		_fstream.write('\tmenuItem -d 1;\n')
		_fstream.write('\tpython("from tp.maya.libs.triggers import api as triggers");\n')
		_fstream.write(
			"""\tint $killState = python("triggers.build_trigger_menu('"+{}+"', '"+{}+"')");\n""".format(
				_parent_var_str,
				_object_var_str))
		_fstream.write('\tif($killState) return;\n')
		_fstream.write('/// END TPDCC MODS ####################\n\n')

	try:
		dag_menu_script_path = path.normalize_path(path.find_first_in_env('dagMenuProc.mel', 'MAYA_SCRIPT_PATH'))
	except Exception:
		logger.error('Cannot find dagMenuProc.mel script - aborting custom marking menu override', exc_info=True)
		return

	try:
		poly_cut_uv_options_popup_script_path = path.normalize_path(
			path.find_first_in_env('polyCutUVOptionsPopup.mel', 'MAYA_SCRIPT_PATH'))
	except Exception:
		logger.error(
			'Cannot find polyCutUVOptionsPopup.mel script - aborting custom marking menu override', exc_info=True)
		return

	tmp_script_path = path.join_path(cmds.internalVar(usd=True), 'tpDagMenuProc_override.mel')

	global_proc_def_rex = re.compile(
		"^global +proc +dagMenuProc *\(*string *(\$[a-zA-Z0-9_]+), *string *(\$[a-zA-Z0-9_]+) *\)")
	with open(dag_menu_script_path) as f:
		dag_menu_script_line_iter = iter(f)
		with open(tmp_script_path, 'w') as f2:
			has_dag_menu_proc_been_setup = False
			for line in dag_menu_script_line_iter:
				f2.write(line)
				global_proc_def_search = global_proc_def_rex.search(line)
				if global_proc_def_search:
					parent_var_str, object_var_str = global_proc_def_search.groups()
					if '{' in line:
						_write_tp_lines(f2, parent_var_str, object_var_str)
						has_dag_menu_proc_been_setup = True
					if not has_dag_menu_proc_been_setup:
						for line in dag_menu_script_line_iter:
							f2.write(line)
							if '{' in line:
								_write_tp_lines(f2, parent_var_str, object_var_str)
								has_dag_menu_proc_been_setup = True
								break

		if not has_dag_menu_proc_been_setup:
			logger.error('Could not auto setup dagMenProc')
			return

		# force polyCutUVOptionsPopup to be loaded first which internally handles the load of dagMenuProc.mel
		mel.eval('source "{}";'.format(str(poly_cut_uv_options_popup_script_path)))
		mel.eval('source "{}";'.format(str(tmp_script_path)))

	os.remove(tmp_script_path)


def reset():
	try:
		dag_menu_script_path = path.normalize_path(path.find_first_in_env('dagMenuProc.mel', 'MAYA_SCRIPT_PATH'))
	except Exception:
		logger.error('Cannot find dagMenuProc.mel script - aborting custom marking menu override', exc_info=True)
		return

	mel.eval('source "{}";'.format(dag_menu_script_path))
