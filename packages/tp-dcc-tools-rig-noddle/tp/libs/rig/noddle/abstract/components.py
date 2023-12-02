from __future__ import annotations

import enum

from tp.libs.rig.noddle.abstract import animcomponent


class AbstractFKComponent(animcomponent.AbstractAnimComponent):
    pass


class AbstractHeadComponent(AbstractFKComponent):
    pass


class AbstractFKIKComponent(animcomponent.AbstractAnimComponent):
    pass


class AbstractReverseFootComponent(animcomponent.AbstractAnimComponent):
    pass


class AbstractSpineComponent(animcomponent.AbstractAnimComponent):
    pass


class AbstractFKIKSpineComponent(AbstractSpineComponent):
    class Hooks(enum.Enum):
        ROOT = 0
        HIPS = 1
        MID = 2
        CHEST = 3


class AbstractHandComponent(animcomponent.AbstractAnimComponent):
    pass


class AbstractIKSplineStretchComponent(animcomponent.AbstractAnimComponent):
    pass


class AbstractTwistComponent(animcomponent.AbstractAnimComponent):
    pass
