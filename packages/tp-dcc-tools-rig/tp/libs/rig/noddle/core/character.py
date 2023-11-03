from tp.core import dcc
from tp.libs.rig.noddle.abstract import character


if dcc.is_maya():
    from tp.libs.rig.noddle.maya.meta.components import character as maya_character
    Character = maya_character.Character
else:
    Character = character.AbstractCharacter
