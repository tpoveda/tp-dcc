#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tpDcc-libs-unittest unit test base settings class
"""

import os
import uuid
import tempfile

from tpDcc import dcc
from tpDcc.libs.python import decorators


class MetaUnitTestSettings(type):

    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            if dcc.is_maya():
                from tpDcc.libs.unittests.dccs.maya import settings
                cls._instance = type.__call__(settings.MayaUnitTestSettings, *args, **kwargs)
            else:
                cls._instance = type.__call__(BaseUnitTestSettings, *args, **kwargs)

        return cls._instance


class BaseUnitTestSettings(object):
    """
    Settings for running unit tests
    """

    # Specifies where file generated during tests should be stored
    # Use a uuid subdirectory so test that are running concurrently such as on a build server do not conflict
    # with each other

    # Here we use uuid4() because it generates a random unique UUID, uuid1() generated a random UUID containing the
    # user computer's network address
    temp_dir = os.path.join(tempfile.gettempdir(), '{}_unittest'.format(dcc.name()), str(uuid.uuid4()))

    # Controls whether temp files should be deleted after running all tests in the test case
    delete_files = True


@decorators.add_metaclass(MetaUnitTestSettings)
class UnitTestSettings(object):
    pass
