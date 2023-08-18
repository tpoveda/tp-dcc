from __future__ import annotations

from tp.maya import api

from tp.libs.rig.crit.maya.core import component
from tp.libs.rig.crit.maya.library.functions import joints


class VChainComponent(component.Component):

	ID = 'vlimbchain'