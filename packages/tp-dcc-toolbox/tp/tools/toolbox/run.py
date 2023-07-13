from tp.tools.toolbox import manager


def open_toolset(tool_ui_id: str):

	tool_ui_opened = manager.run_tool_ui(tool_ui_id, log_warning=False)
	if not tool_ui_opened:
		pass
