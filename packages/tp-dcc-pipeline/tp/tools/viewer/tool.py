from __future__ import annotations

import os
import argparse

from overrides import override

from tp.core import tool


class ViewerTool(tool.Tool):

    id = 'tp.game.tools.viewer'
    creator = 'Tomi Poveda'
    tags = ['3d', 'viewer']

    @override
    def execute(self, *args, **kwargs):

        scene = kwargs.get('scene')

        from tp.common.qt import api as qt
        from tp.tools.viewer import view

        win = view.ViewerWindow()
        win.show()

        if scene and os.path.isfile(scene):
            qt.QApplication.processEvents()
            win.load_file(scene)

        return win


if __name__ == '__main__':

    # load framework
    import tp.bootstrap
    tp.bootstrap.init(package_version_file='package_version_standalone.config')

    parser = argparse.ArgumentParser(description='3D Viewer', add_help=False)
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    parser.add_argument('--scene', type=str, required=False, default=None, help='Scene to open')

    args = parser.parse_args()

    from tp.core.managers import tools

    tools.ToolsManager().launch_tool_by_id('tp.game.tools.viewer', scene=args.scene)
