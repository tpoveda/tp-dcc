from __future__ import annotations

import os
import re
import logging

from maya import mel, cmds

from tp.python import paths

logger = logging.getLogger(__name__)


def setup() -> bool:
    """
    Installs modifications to the dagProcMenu script for the current session.
    """

    try:
        dag_menu_script_path = str(
            paths.find_first_in_environment_variable(
                "dagMenuProc.mel", "MAYA_SCRIPT_PATH"
            )
        ).replace("\\", "/")
    except Exception:
        logger.error(
            "Cannot find dagMenuProc.mel script. Aborting marking menu override.",
            exc_info=True,
        )
        return False

    try:
        poly_cut_uv_options_popup_script_path = str(
            paths.find_first_in_environment_variable(
                "polyCutUVOptionsPopup.mel", "MAYA_SCRIPT_PATH"
            )
        ).replace("\\", "/")
    except Exception:
        logger.error(
            "Cannot find polyCutUVOptionsPopup.mel script. Aborting marking menu override.",
            exc_info=True,
        )
        return False

    temp_script_path = os.path.join(
        cmds.internalVar(userTmpDir=True), "tpDagMenuProc_override.mel"
    )

    def _write_tp_dcc_lines(fstream, _parent_var_str: str, _object_var_str: str):
        fstream.write("\n/// TP DCC MODS ########################\n")
        fstream.write("\tsetParent -m $parent;\n")
        fstream.write("\tmenuItem -d 1;\n")
        fstream.write('\tpython("from tp.maya import triggers");\n')
        fstream.write(
            """\tint $killState = python("triggers.build_trigger_menu('"+{}+"', '"+{}+"')");\n""".format(
                parent_var_str, _object_var_str
            )
        )
        fstream.write("\tif($killState) return;\n")
        fstream.write("/// END TP DCC MODS ####################\n\n")

    global_proc_def_regex = re.compile(
        "^global +proc +dagMenuProc *\(*string *(\$[a-zA-Z0-9_]+), *string *(\$[a-zA-Z0-9_]+) *\)"
    )
    with open(dag_menu_script_path) as f:
        dag_menu_script_line_iter = iter(f)
        with open(temp_script_path, "w") as f2:
            has_dag_menu_proc_been_setup: bool = False
            for line in dag_menu_script_line_iter:
                f2.write(line)
                global_proc_def_search = global_proc_def_regex.search(line)
                if global_proc_def_search:
                    parent_var_str, object_var_str = global_proc_def_search.groups()
                    if "{" in line:
                        _write_tp_dcc_lines(f2, parent_var_str, object_var_str)
                        has_dag_menu_proc_been_setup = True
                    if not has_dag_menu_proc_been_setup:
                        for line in dag_menu_script_line_iter:
                            f2.write(line)
                            if "{" in line:
                                _write_tp_dcc_lines(f2, parent_var_str, object_var_str)
                                has_dag_menu_proc_been_setup = True
                                break

        if not has_dag_menu_proc_been_setup:
            logger.error("Was not possible to auto setup the marking menu override.")
            return False

        mel.eval(f'source "{poly_cut_uv_options_popup_script_path}";')
        mel.eval(f'source "{temp_script_path}";')

    os.remove(temp_script_path)

    return True


def reset():
    """
    Resets the marking menu override.
    """

    try:
        dag_menu_script_path = str(
            paths.find_first_in_environment_variable(
                "dagMenuProc.mel", "MAYA_SCRIPT_PATH"
            )
        ).replace("\\", "/")
    except Exception:
        logger.error(
            "Cannot find dagMenuProc.mel script. Aborting marking menu override.",
            exc_info=True,
        )
        return False

    mel.eval(f'source "{dag_menu_script_path}";')
