from __future__ import annotations

from .node import TriggerNode
from .command import TriggerCommand  # noqa: F401
from .manager import TriggersManager
from .commands.menu import build_trigger_menu  # noqa: F401
from .callbacks import block_selection_callback_decorator, create_selection_callback  # noqa: F401

has_trigger = TriggerNode.has_trigger
as_trigger_node = TriggerNode.from_node
has_command_type = TriggerNode.has_command_type
iterate_connected_trigger_nodes = TriggerNode.iterate_connected_trigger_nodes
create_trigger_from_node = TriggersManager.create_trigger_from_node
