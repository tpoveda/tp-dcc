from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from tp.tools.rig.noddle.builder.graph.core.scene import Scene


class AbstractNode:

    ID: int | None = None
    DEFAULT_TITLE = 'Abstract Node'

    def __init__(self, scene: Scene, graphics: type):
        super().__init__()

        self._scene = scene

        _node_item = graphics
        if _node_item is None:
            raise RuntimeError('No node view specified node')

        self._setup_inner_classes(graphics)

        self.scene.add_node(self)
        self.scene.graphics_scene.addItem(self._graphics_node)

    @property
    def scene(self) -> Scene:
        return self._scene

    def _setup_inner_classes(self, graphics_class: type):
        """
        Internal function that initializes node inner classes.
        """

        self._graphics_node = graphics_class(self)
