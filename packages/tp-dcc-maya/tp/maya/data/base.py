#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base classes for Maya
"""

import logging
import traceback

import maya.cmds

from tpDcc import dcc
from tpDcc.core import data, scripts
from tpDcc.libs.python import path, osplatform, version
from tpDcc.dccs.maya.core import constants, geometry, scene, helpers

LOGGER = logging.getLogger('tpDcc-dccs-maya')


class DataTypes(data.DataTypes, object):
    MayaAscii = 'MayaAscii'
    MayaBinary = 'MayaBinary'


class ScriptTypes(scripts.ScriptTypes, object):
    MEL = 'MELScript'


class ScriptMelData(scripts.ScriptData, object):

    @staticmethod
    def get_data_type():
        return constants.ScriptLanguages.MEL

    @staticmethod
    def get_data_extension():
        return 'mel'


class MayaCustomData(data.CustomData, object):

    def _center_view(self):
        if scene.is_batch():
            return

        try:
            maya.cmds.select(cl=True)
            maya.cmds.viewFit(an=True)
            self._fix_camera()
        except Exception:
            LOGGER.debug('Could not center view: {}'.format(traceback.format_exc()))

    def _fix_camera(self):
        camera_pos = maya.cmds.xform('persp', q=True, ws=True, t=True)
        dst = mathlib.get_distance_between_vectors([0, 0, 0], camera_pos)
        maya.cmds.setAttr('persp.farClipPlane', dst * 10)
        near = 0.1
        if dst > 10000:
            near = (dst / 10000) * near
        maya.cmds.setAttr('persp.nearClipPlane', near)


class MayaFileData(MayaCustomData, object):
    maya_binary = 'mayaBinary'
    maya_ascii = 'mayaAscii'

    def __init__(self, name=None, path=None):
        super(MayaFileData, self).__init__(name=name, path=path)

        self.maya_file_type = self.get_maya_file_type()

    def get_data_title(self):
        return 'maya_file'

    def set_directory(self, directory):
        super(MayaFileData, self).set_directory(directory)
        self.file_path = path.join_path(directory, '{}.{}'.format(self.name, self.get_data_extension()))

    def get_maya_file_type(self):
        return self.maya_binary

    def open(self, file_path=None):
        if not dcc.is_maya():
            LOGGER.warning('Maya data must be accessed from within Maya!')
            return

        open_file = None
        if file_path:
            open_file = file_path
        if not open_file:
            file_path = self.get_file()
            if not path.is_file(file_path):
                LOGGER.warning('Could not open file: {}'.format(file_path))
                return
            open_file = file_path

        helpers.display_info('Opening: {}'.format(open_file))

        try:
            maya.cmds.file(open_file, f=True, o=True, iv=True, pr=True)
        except Exception:
            LOGGER.error('Impossible to open Maya file: {} | {}'.format(open_file, traceback.format_exc()))

        self._after_open()

        top_transforms = scene.get_top_dag_nodes(exclude_cameras=True)

        return top_transforms

    def export_data(self, comment='-', create_version=True, *args, **kwargs):
        if not dcc.is_maya():
            LOGGER.warning('Maya data must be saved from within Maya!')
            return

        file_path = self.get_file()
        osplatform.get_permission(file_path)
        self._handle_unknowns()
        self._clean_scene()

        if not file_path.endswith('.mb') and not file_path.endswith('.ma'):
            file_path = maya.cmds.workspace(query=True, rd=True)
            if self.maya_file_type == self.maya_ascii:
                file_path = maya.cmds.fileDialog(ds=1, fileFilter='Maya Ascii (*.ma)', dir=file_path)
            elif self.maya_file_type == self.maya_binary:
                file_path = maya.cmds.fileDialog(ds=1, fileFilter='Maya Binary (*.mb)', dir=file_path)
            if file_path:
                file_path = file_path[0]

        saved = scene.save_as(file_path)
        if saved:
            if create_version:
                version_file = version.VersionFile(file_path)
                # if scene.is_batch() or not version_file.has_versions():
                version_file.save(comment)

            helpers.display_info('Saved {} data'.format(self.name))
            return True

        return False

    def import_data(self, file_path=''):
        """
        Loads data object
        :param file_path: str, file path of file to load
        """

        if not dcc.is_maya():
            LOGGER.warning('Data must be accessed from within Maya!')
            return

        if file_path:
            import_file = file_path
        else:
            import_file = self.get_file()
        if not path.is_file(import_file):
            LOGGER.warning('Impossible to import invalid data file: {}'.format(file_path))
            return

        track = scene.TrackNodes()
        track.load('transform')

        scene.import_scene(import_file, do_save=False)
        self._after_open()

        transforms = track.get_delta()
        top_transforms = scene.get_top_dag_nodes_in_list(transforms)

        return top_transforms

    def reference_data(self, file_path=''):
        if not dcc.is_maya():
            LOGGER.warning('Data must be accessed from within Maya!')
            return

        if file_path:
            reference_file = file_path
        else:
            reference_file = self.get_file()
        if not path.is_file(reference_file):
            LOGGER.warning('Impossible to reference invalid data file: {}'.format(file_path))
            return

        track = scene.TrackNodes()
        track.load('transform')

        scene.reference_scene(reference_file)

        transforms = track.get_delta()
        top_transforms = scene.get_top_dag_nodes_in_list(transforms)

        return top_transforms

    def clean_student_license(self, file_path=''):
        if not dcc.is_maya():
            LOGGER.warning('Data must be accessed from within Maya!')
            return

        if file_path:
            file_to_clean = file_path
        else:
            file_to_clean = self.get_file()
        if not path.is_file(file_to_clean):
            LOGGER.warning('Impossible to reference invalid data file: {}'.format(file_path))
            return

        changed = helpers.clean_student_line(file_to_clean)
        if changed:
            LOGGER.debug('Cleaned student license from file: {}'.format(file_to_clean))

    def _check_after_save(self, client_data, comment=None):
        file_path = maya.cmds.file(query=True, sn=True)
        version_file = version.VersionFile(file_path)
        dir_path = path.dirname(file_path)
        if version.VersionFile(dir_path).has_versions():
            if not comment:
                comment = 'Automatically versioned with Maya save'

            version.save(comment)
            helpers.display_info('New version saved!')

    def _after_open(self):
        geometry.smooth_preview_all(False)
        self._center_view()

    def _clean_scene(self):
        LOGGER.debug('Cleaning Maya scene ...')
        scene.delete_turtle_nodes()
        if helpers.maya_version() > 2014:
            scene.delete_garbage()
            scene.delete_unused_plugins()

    def _handle_unknowns(self):
        unknown_nodes = maya.cmds.ls(type='unknown')
        if unknown_nodes:
            value = maya.cmds.confirmDialog(
                title='Unknown Nodes!',
                message='Unknown nodes usually happen when a plugin that was being used is not loaded.\n'
                        'Load the missing plugin, and the unknown nodes could become valid.\n\nDelete unknown nodes?\n',
                button=['Yes', 'No'],
                defaultButton='Yes',
                cancelButton='No',
                dismissString='No'
            )

            if value == 'Yes':
                scene.delete_unknown_nodes()
            if value == 'No':
                if self.maya_file_type == self.maya_binary:
                    maya.cmds.warning('\tThis file contains unknown nodes. Try saving as Maya ASCII instead.')

    def _prepare_scene_for_export(self):
        outliner_sets = scene.get_sets()
        top_nodes = scene.get_top_dag_nodes()
        to_select = outliner_sets + top_nodes
        if not to_select:
            to_select = ['persp', 'side', 'top', 'front']
        maya.cmds.select(to_select, r=True)


class MayaBinaryFileData(MayaFileData):
    def __init__(self, name=None, path=None):
        super(MayaBinaryFileData, self).__init__(name=name, path=path)

    @staticmethod
    def get_data_type():
        return 'maya.binary'

    @staticmethod
    def get_data_extension():
        return 'mb'

    @staticmethod
    def get_data_title(self):
        return 'Maya Binary'

    def get_maya_file_type(self):
        return self.maya_binary


class MayaAsciiFileData(MayaFileData):
    def __init__(self, name=None, path=None):
        super(MayaAsciiFileData, self).__init__(name=name, path=path)

    @staticmethod
    def get_data_type():
        return 'maya.ascii'

    @staticmethod
    def get_data_extension():
        return 'ma'

    @staticmethod
    def get_data_title():
        return 'Maya ASCII'

    def get_maya_file_type(self):
        return self.maya_ascii
