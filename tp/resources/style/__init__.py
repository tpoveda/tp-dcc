from __future__ import annotations

import os
import inspect

from ...externals.Qt.QtCore import QResource

RESOURCE_REGISTERED = False


def style_file_path() -> str:
    """
    Returns path pointing to style.

    :return: style file path.
    """

    root_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    return os.path.join(root_path, 'style.qss')


def setup():
    """
    Setup stylesheet.
    """

    global RESOURCE_REGISTERED
    if RESOURCE_REGISTERED:
        return

    root_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    icons_rcc = os.path.join(root_path, 'icons.rcc')

    if os.path.isfile(icons_rcc) and not RESOURCE_REGISTERED:
        QResource.registerResource(icons_rcc)
        RESOURCE_REGISTERED = True
