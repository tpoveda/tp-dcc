from __future__ import annotations

import os
import sys

from Qt.QtWidgets import QApplication

from tp.python import paths
from tp.nodegraph.core import consts
from tp.nodegraph.examples import tool


if __name__ == "__main__":
    # sys.path.append(paths.canonical_path("./../../.."))
    nodes_paths = [paths.canonical_path("./nodes")]
    os.environ[consts.NODE_PATHS_ENV_VAR] = os.pathsep.join(nodes_paths)

    app = QApplication(sys.argv)
    new_tool = tool.show()
    new_tool.closed.connect(app.quit)
    sys.exit(app.exec())
