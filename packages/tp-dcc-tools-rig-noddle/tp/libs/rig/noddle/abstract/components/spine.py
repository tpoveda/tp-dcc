import enum


class AbstractSpineComponent:
    pass


class AbstractFKIKSpineComponent(AbstractSpineComponent):

    class Hooks(enum.Enum):

        ROOT = 0
        HIPS = 1
        MID = 2
        CHEST = 3
