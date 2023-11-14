from overrides import override

from tp.libs.rig.noddle.core import component, animcomponent
from tp.tools.rig.noddle.builder import api


class ComponentNode(api.NoddleNode):

    DEFAULT_TITLE = 'Component'
    TITLE_EDITABLE = True

    def __init__(self, scene: api.Scene, title: str | None = None):
        super().__init__(scene=scene, title=title)

        self._component_instance: component.Component | None = None

    @property
    def in_meta_parent(self) -> api.InputSocket:
        return self._in_meta_parent

    @property
    def in_side(self) -> api.InputSocket:
        return self._in_side

    @property
    def in_name(self) -> api.InputSocket:
        return self._in_name

    @property
    def in_tag(self) -> api.InputSocket:
        return self._in_tag

    @property
    def out_self(self) -> api.OutputSocket:
        return self._out_self

    @property
    def out_meta_parent(self) -> api.OutputSocket:
        return self._out_meta_parent

    @property
    def out_meta_children(self) -> api.OutputSocket:
        return self._out_meta_children

    @property
    def out_side(self) -> api.OutputSocket:
        return self._out_side

    @property
    def out_name(self) -> api.OutputSocket:
        return self._out_name

    @property
    def out_tag(self) -> api.OutputSocket:
        return self._out_tag

    @override
    def setup_sockets(self):
        super().setup_sockets()

        self._in_meta_parent = self.add_input(api.dt.Component, label='Parent', value=None)
        self._in_side = self.add_input(api.dt.String, label='Side', value='c')
        self._in_name = self.add_input(api.dt.String, label='Name', value='component')
        self._in_tag = self.add_input(api.dt.String, label='Tag', value='')

        self.mark_input_as_required(self._in_name)
        self.mark_input_as_required(self._in_side)

        self._out_self = self.add_output(api.dt.Component, label='Self', value=None)
        self._out_meta_parent = self.add_output(api.dt.Component, label='Parent', value=None)
        self._out_meta_children = self.add_output(api.dt.List, label='Children')
        self._out_side = self.add_output(api.dt.String, label='Side', value='c')
        self._out_name = self.add_output(api.dt.String, label='Name', value='component')
        self._out_tag = self.add_output(api.dt.String, label='Tag', value='')

        self._in_meta_parent.affects(self._out_meta_parent)
        self._in_side.affects(self._out_side)
        self._in_name.affects(self._out_name)
        self._in_tag.affects(self._in_tag)


class AnimComponentNode(ComponentNode):

    DEFAULT_TITLE = 'Anim Component'
    COMPONENT_CLASS = animcomponent.AnimComponent

    @override
    def setup_sockets(self):
        super().setup_sockets()

        self.out_self.data_type = api.dt.AnimComponent
        self.in_meta_parent.data_type = api.dt.AnimComponent
        self.out_meta_parent.data_type = api.dt.AnimComponent
        self.in_name.set_value('anim_component')

        self.in_character = self.add_input(api.dt.Character, label='Character')
        self.in_hook = self.add_input(api.dt.Numeric, label='In Hook')
        self.mark_input_as_required(self.in_character)

        self.out_character = self.add_output(api.dt.Character, label='Character')
        self.out_in_hook = self.add_output(api.dt.Numeric, label='In Hook')

        self.in_character.affects(self.out_character)
        self.in_hook.affects(self.out_in_hook)

        self.in_hook.set_value(None)


def register_plugin(register_node: callable, register_function: callable, register_data_type: callable):

    register_function(
        AnimComponentNode.COMPONENT_CLASS.character, api.dt.AnimComponent,
        inputs={'AnimComponent': api.dt.AnimComponent}, outputs={'Character': api.dt.Character},
        nice_name='Get Character', category='Anim Component')

    register_function(
        AnimComponentNode.COMPONENT_CLASS.controls, api.dt.AnimComponent,
        inputs={'AnimComponent': api.dt.AnimComponent}, outputs={'Controls': api.dt.List},
        nice_name='List Controls', category='Anim Component')
