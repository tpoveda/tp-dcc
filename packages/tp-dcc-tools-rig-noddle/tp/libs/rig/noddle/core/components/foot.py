from __future__ import annotations

from tp.core import dcc


if dcc.is_maya():
    from tp.libs.rig.noddle.maya.meta.components import foot
    FootComponent = foot.ReverseFootComponent

else:
    from tp.libs.rig.noddle.abstract.components import foot
    FootComponent = foot.AbstractReverseFootComponent
