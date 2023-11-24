from __future__ import annotations

from tp.core import log, dcc
from tp.bootstrap.core import exceptions, package

if dcc.is_maya():
    from tp.maya.plugins import rigloader


logger = log.tpLogger


def startup(_: package.Package):
    """
    This function is automatically called by tpDcc packages Manager when environment setup is initialized.
    """

    logger.info('Loading tp-dcc-tools-rig package...')

    if not dcc.is_maya():
        return

    rigloader.load_all_plugins()


def shutdown(bootstrap_package: package.Package):
    """
    Shutdown function that is called during tpDcc framework shutdown.
    This function is called at the end of tpDcc framework shutdown.

    :param Package bootstrap_package: package instance.
    """

    if not bootstrap_package:
        raise exceptions.MissingPackage(package)

    if not dcc.is_maya():
        return

    logger.info('Shutting down tp-dcc-tools-rig package...')

    rigloader.unload_all_plugins()
