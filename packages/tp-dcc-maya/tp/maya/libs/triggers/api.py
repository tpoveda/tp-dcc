from tp.maya.libs.triggers.triggernode import TriggerNode, create_trigger_for_node
from tp.maya.libs.triggers.triggercommand import TriggerCommand
from tp.maya.libs.triggers.triggercallbacks import create_selection_callback, remove_selection_callback
from tp.maya.libs.triggers.commands.menu import build_trigger_menu

as_trigger_node = TriggerNode.from_node
has_trigger = TriggerNode.has_trigger
