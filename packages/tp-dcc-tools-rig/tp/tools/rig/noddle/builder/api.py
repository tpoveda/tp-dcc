from tp.core import dcc

from tp.tools.rig.noddle.builder.graph import datatypes as dt
from tp.tools.rig.noddle.builder.graph.registers import DataType, DATA_TYPES_REGISTER, function_from_signature
from tp.tools.rig.noddle.builder.graph.core.scene import Scene
from tp.tools.rig.noddle.builder.graph.core.socket import InputSocket, OutputSocket
from tp.tools.rig.noddle.builder.graph.nodes.noddle_node import NoddleNode

if dcc.is_maya():
    from tp.tools.rig.noddle.builder.controllers.maya.nodes.node_component import ComponentNode, AnimComponentNode
