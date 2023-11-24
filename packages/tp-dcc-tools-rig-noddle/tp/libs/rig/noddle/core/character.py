from tp.core import dcc


if dcc.is_maya():
    from tp.libs.rig.noddle.maya.meta.components import character as maya_character
    Character = maya_character.Character
else:
    raise ImportError(f'Unable to import Character class for: {dcc.current_dcc()}')
