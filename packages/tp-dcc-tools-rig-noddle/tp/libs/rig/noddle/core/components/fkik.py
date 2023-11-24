from __future__ import annotations

from tp.core import dcc


if dcc.is_maya():
    from tp.libs.rig.noddle.maya.meta.components import fkik
    FKIKComponent = fkik.FKIKComponent

else:
    from tp.libs.rig.noddle.abstract.components import fkik
    FKIKComponent = fkik.AbstractFKIKComponent
