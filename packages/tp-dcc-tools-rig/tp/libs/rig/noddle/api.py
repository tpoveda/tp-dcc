from tp.core import dcc

from tp.libs.rig.noddle.core.project import Project
from tp.libs.rig.noddle.core.asset import Asset
from tp.libs.rig.noddle import io

if dcc.is_maya():
    from tp.libs.rig.noddle.core.build import Build
    from tp.libs.rig.noddle.maya.meta import components
