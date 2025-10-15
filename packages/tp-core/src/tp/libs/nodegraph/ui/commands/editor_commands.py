from __future__ import annotations

from Qt.QtWidgets import QMessageBox

from tp.libs.nodegraph.ui import NodeGraphEditorCommand


class NewGraphCommand(NodeGraphEditorCommand):
    id = "graph.new"
    ui_data = {
        "label": "New Graph",
        "icon": "tp-icons:document-new.svg",
        "shortcut": "Ctrl+N",
    }

    def execute(self, *args, **kwargs):
        should_save = self.editor.should_save()
        if should_save == QMessageBox.Cancel:
            return
        elif should_save == QMessageBox.Save:
            self.editor.save()

        self.editor.new_graph()
