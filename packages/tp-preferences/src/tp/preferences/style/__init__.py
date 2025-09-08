import os
import inspect

from Qt.QtCore import QResource

RESOURCE_REGISTERED = False


def style_file_path() -> str:
    """Return absolute path pointing to style sheet file.

    Returns:
        Absolute file path pointing to QSS file.
    """

    root_path = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe()))
    )
    qss_path = os.path.join(root_path, "style.qss")
    return qss_path


def setup():
    """Setup stylesheet."""

    global RESOURCE_REGISTERED
    if RESOURCE_REGISTERED:
        return

    root_path = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe()))
    )
    icons_rcc = os.path.join(root_path, "icons.rcc")

    if not os.path.isfile(icons_rcc):
        return

    QResource.registerResource(icons_rcc)
    RESOURCE_REGISTERED = True


def shutdown():
    """Shutdown stylesheet."""

    global RESOURCE_REGISTERED
    if not RESOURCE_REGISTERED:
        return

    root_path = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe()))
    )
    icons_rcc = os.path.join(root_path, "icons.rcc")
    if not os.path.isfile(icons_rcc):
        return

    QResource.unregisterResource(icons_rcc)
    RESOURCE_REGISTERED = False
