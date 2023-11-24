from __future__ import annotations

from tp.core import log, dcc
from tp.bootstrap.core import exceptions, package

if dcc.is_maya():
    from tp.libs.rig.freeform import startup as freeform_startup


logger = log.tpLogger


def startup(_: package.Package):
    """
    This function is automatically called by tpDcc packages Manager when environment setup is initialized.
    """

    logger.info('Loading tp-dcc-tools-rig-freeform package...')

    if not dcc.is_maya():
        return

    freeform_startup.startup()


def shutdown(bootstrap_package: package.Package):
    """
    Shutdown function that is called during tpDcc framework shutdown.
    This function is called at the end of tpDcc framework shutdown.

    :param Package bootstrap_package: package instance.
    """

    logger.info('Shutting down tp-dcc-tools-rig-freeform package...')

    if not dcc.is_maya():
        return

    if not bootstrap_package:
        raise exceptions.MissingPackage(package)

    logger.info('Shutting down tp-dcc-tools-rig-freeform package...')

    freeform_startup.shutdown()
