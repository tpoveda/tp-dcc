from overrides import override

from tp.core import tool


class FragTool(tool.Tool):

    id = 'tp.rig.frag.builder'
    creator = 'Tomi Poveda'
    tags = ['rig', 'actions']

    @override
    def execute(self, *args, **kwargs):

        from tp.tools.rig.frag import controller, window

        frag_controller = controller.FragController()

        win = window.FragWindow(controller=frag_controller)
        win.show()

        return win


if __name__ == '__main__':

    # load framework
    import tp.bootstrap
    tp.bootstrap.init(package_version_file='package_version_standalone.config')

    from tp.core.managers import tools
    tools.ToolsManager().launch_tool_by_id('tp.rig.frag.builder')
