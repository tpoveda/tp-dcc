from tp.core import dcc

from tp.libs.rig.crit.core.project import Project
from tp.libs.rig.crit.core.asset import Asset

if dcc.is_maya():
	from tp.libs.rig.crit.maya.core.build import Build
	from tp.libs.rig.crit.maya.library import io
	from tp.libs.rig.crit.maya.core.component import Component
	from tp.libs.rig.crit.maya.library import components
