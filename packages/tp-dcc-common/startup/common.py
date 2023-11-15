import os
import sys
import inspect

from Qt.QtWidgets import QApplication

from tp.core import log
from tp.common.resources import api as resources

logger = log.tpLogger


def startup(package_manager):
    """
    This function is automatically called by tpDcc packages Manager when environment setup is initialized.

    :param package_manager: current tpDcc packages Manager instance.
    :return: tpDccPackagesManager
    """

    logger.info('Loading tp-dcc-common package...')

    root_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

    # Make sure QApplication instance exists before registering resources
    app = QApplication.instance() or QApplication(sys.argv)
    resources_path = os.path.join(os.path.dirname(root_path), 'resources')
    resources.register_resource(resources_path, key='tp-dcc-common')


def shutdown(package_manager):
    """
    Shutdown function that is called during tpDcc framework shutdown.
    This function is called at the end of tpDcc framework shutdown.
    """

    logger.info('Shutting down tp-dcc-common package...')
