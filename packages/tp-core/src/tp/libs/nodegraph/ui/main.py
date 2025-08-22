from __future__ import annotations

import sys

from Qt.QtWidgets import QApplication

from tp import bootstrap
from tp.libs.nodegraph.ui.widgets.window import NodeGraphWindow

if __name__ == "__main__":
    bootstrap.init()
    app = QApplication(sys.argv)
    window = NodeGraphWindow()
    window.closed.connect(app.quit)
    window.show()
    # noinspection PyUnresolvedReferences
    sys.exit(app.exec())
