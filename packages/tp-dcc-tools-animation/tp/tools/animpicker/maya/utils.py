from __future__ import annotations

from typing import List

import maya.cmds as cmds


def filter_picker_nodes() -> List[str]:
	return [n for n in cmds.ls(type='geometryVarGroup') if cmds.objExists(f'{n}.animPickerMap')]
