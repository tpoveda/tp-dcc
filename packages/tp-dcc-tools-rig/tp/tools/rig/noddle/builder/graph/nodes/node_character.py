from tp.libs.rig.noddle.core import character
from tp.tools.rig.noddle.builder import api


class CharacterNode(api.ComponentNode):

    ID = 7
    IS_EXEC = True
    ICON = 'bindpose.png'
    DEFAULT_TITLE = 'Character'
    CATEGORY = 'Components'
    UNIQUE = True
    COMPONENT_CLASS = character.Character


def register_plugin(register_node: callable, register_function: callable, register_data_type: callable):
    register_node(CharacterNode.ID, CharacterNode)
    register_function(
        CharacterNode.COMPONENT_CLASS.control_rig_group, api.dt.Character,
        inputs={'Character': api.dt.Character}, outputs={'Control Rig': api.dt.String},
        nice_name='Get Control Rig', category='Character')
