#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes to handle version files
"""

import os
import getpass

from tp.core import log
from tp.common.python import folder, path, fileio, jsonio, sort, name as name_utils

logger = log.tpLogger


class SemanticVersion(object):
    """
    Class that defines Semantic version following: <https://semver.org>
    """

    def __init__(self, major, minor, patch):
        super(SemanticVersion, self).__init__()

        assert(isinstance(major, int))
        assert(isinstance(minor, int))
        self._major = major
        self._minor = minor
        self._patch = patch

    @staticmethod
    def from_string(version_string):
        """
        Returns semantic version instance from given string
        :param version_string: str
        :return: SemanticVersion
        """

        major, minor, patch = version_string.split('.')
        return SemanticVersion(int(major), int(minor), patch)

    @staticmethod
    def from_pep440_string(pep440_string):
        """
        Returns semantic version from PEP440 version string
        :param pep440_string: str
        :return: SemanticVersion
        """

        # Invalid pep440 version was given
        if 'unparseable' in pep440_string or 'unknown' in pep440_string:
            return SemanticVersion(0, 0, 0)

        pep440_string_split = pep440_string.split('+')
        if pep440_string_split[1].startswith('untagged'):
            # Major: 0 because no tag was found
            # Minor: number of commits since the most recent tag
            # Patch: Unique identifier for latest commit
            clean_string = pep440_string_split[1].split('.')
            patch = clean_string[2]
            return SemanticVersion(int(pep440_string_split[0]), int(clean_string[1]), patch)
        else:
            clean_string = [int(version_part) for version_part in pep440_string_split[0].split('.')]
            return SemanticVersion(*clean_string)

    def __str__(self):
        return '{}.{}.{}'.format(self._major, self._minor, self._patch)

    def __eq__(self, other):
        return all([self.major == other.major, self.minor == other.minor, self.patch == other.patch])

    def __ge__(self, other):
        lhs = int(''.join([str(self.major), str(self.minor), str(self.patch)]))
        rhs = int(''.join([str(other.major), str(other.minor), str(other.patch)]))
        return lhs >= rhs

    def __gt__(self, other):
        lhs = int(''.join([str(self.major), str(self.minor), str(self.patch)]))
        rhs = int(''.join([str(other.major), str(other.minor), str(other.patch)]))
        return lhs > rhs

    @property
    def major(self):
        """
        Returns major field of the semantic version
        :return: int
        """

        return self._major

    @property
    def minor(self):
        """
        Returns minor field of the semantic version
        :return: int
        """

        return self._minor

    @property
    def patch(self):
        """
        Returns patch field of the semantic version
        :return: int
        """

        return self._patch


class VersionFile(object):
    """
    Utility class to hold version for files and folders
    """

    def __init__(self, file_path):
        self._file_path = file_path
        self._path = path.dirname(file_path)
        self._version_folder_name = '__version__'
        self._version_folder = None
        self._comment_file = None
        self._updated_old = False

    @property
    def file_path(self):
        return self._file_path

    @property
    def file_name(self):
        if not self._file_path:
            return ''

        return path.basename(self._file_path)

    @property
    def updated_old(self):
        return self._updated_old

    def get_version_path(self, version_number):
        """
        Returns the path to the version
        :param version_number: int, version number
        :return: str, path to the version
        """

        return self._get_version_path(version_number)

    def get_version_comment(self, version_number):
        """
        Returns the comment of the given version
        :param version_number: int, version number
        :return: str, version comment
        """

        comment, user = self.get_version_data(version_number)

        return comment

    def set_version_folder(self, folder_path):
        """
        Sets the folder where the version folder should be created
        :param folder_path: str, full path to where the version folder should be created
        """

        self._path = folder_path

    def set_version_folder_name(self, folder_name):
        """
        Sets the name of the version folder
        :param folder_name: str, name of the version folder
        """

        self._version_folder_name = folder_name

    def has_default(self):
        file_name = self._default_version_file_name()
        if path.is_file(file_name):
            return True

        return False

    def has_versions(self):
        """
        Returns if the current version file has version or not
        :return: bool
        """

        version_folder = self._get_version_folder()
        if path.is_dir(version_folder):
            return True

        return False

    def get_default(self):
        file_name = self._default_version_file_name()

        return file_name

    def get_count(self):
        """
        Returns the number of versions
        :return: int
        """

        versions = self.get_version_numbers()
        if versions:
            return len(versions)

        return 0

    def save_comment(self, comment=None, version_file=None):
        """
        Saves a comment to a log file
        :param comment: str, comment to save
        :param version_file: str, correspnding version file
        """

        version = version_file.split('.')
        if version:
            version = version[-1]

        user = getpass.getuser()

        if not comment:
            comment = '-'
        comment.replace('"', '\"')

        current_data = jsonio.read_file(self._comment_file) or list()

        version_data = {'version': version, 'comment': comment, 'user': user}
        current_data.append(version_data)
        jsonio.write_to_file(current_data, self._comment_file)

    def save(self, comment=None):
        """
        Saves a new version
        :param comment: str, comment to add to the version
        :return: str, new version file name
        """

        self._prepare_directories()

        if comment is None:
            comment = ' '
        else:
            comment.replace('\n', '   ')
            comment.replace('\r', '   ')

        unique_file_name = self._increment_version_file_name()
        self._save(unique_file_name)
        self.save_comment(comment, unique_file_name)

        return unique_file_name

    def save_default(self):
        self._prepare_directories()

        file_name = self._default_version_file_name()
        if file_name:
            self._save(file_name)
        else:
            logger.warning('Could not save default version!')

        return file_name

    def get_latest_version(self):
        """
        Returns the file path to the latest version
        :return: str
        """

        versions = self.get_versions()
        latest_version = versions[list(versions.keys())[-1]]

        return path.join_path(self._file_path, '{}/{}'.format(self._version_folder_name, latest_version))

    def get_versions(self, return_version_numbers=False):
        """
        Get file paths of all versions
        :param return_version_numbers: bool, Whether to return also version numbers or only paths
        :return: variant, list<str> | list<str>, list<int>
        """

        version_folder = self._get_version_folder()
        version_files = folder.get_files_and_folders(version_folder)
        if not version_files:
            logger.warning('Impossible to get versions because no version exist!')
            return None

        number_list = list()
        pass_files = list()
        for f in version_files:
            split_name = f.split('.')
            if not len(split_name) == 2 or split_name[0] != '':
                continue

            version_number = int(split_name[1])
            number_list.append(version_number)
            pass_files.append(f)

        if not pass_files:
            logger.warning('No valid version files found in folder: {}'.format(version_folder))
            return

        quick_sort = sort.QuickNumbersListSort(number_list)
        quick_sort.set_follower_list(pass_files)
        pass_files = quick_sort.run()

        pass_dict = dict()
        for i in range(len(number_list)):
            pass_dict[pass_files[0][i]] = pass_files[1][i]

        if return_version_numbers:
            return pass_dict, pass_files[0]
        else:
            return pass_dict

    def get_version_numbers(self):
        """
        Returns numbers of all versions
        :return: list<int>
        """

        version_folder = self._get_version_folder()
        version_files = folder.get_files_and_folders(version_folder)
        if not version_files:
            logger.warning('Impossible to get version numbers because no version exist!')
            return None

        number_list = list()
        for f in version_files:
            if not f.startswith(self._version_name):
                continue
            split_name = f.split('.')
            if split_name[1] == 'json' or split_name[1] == 'default' or not len(split_name) == 2:
                continue

            version_number = int(split_name[1])
            number_list.append(version_number)

        number_list.sort()

        return number_list

    def get_version_data(self, version_number):
        """
        Returns the data (comment and user) of the given version
        :param version_number: int
        :return: tuple(str, str)
        """

        comment_path = self._get_comment_path()
        if not comment_path:
            return None, None

        if not path.is_file(comment_path):
            return None, None

        version_data = jsonio.read_file(comment_path)
        if not version_data:
            return None, None

        for version_dict in version_data:

            version = version_dict.get('version', None)
            comment = version_dict.get('comment', '')
            user = version_dict.get('user', '')

            if version == str(version_number):
                return comment, user

        return None, None

    def get_organized_version_data(self):
        """
        Returns all the version data:
        [version, comment, user, file_size, modified, version_file]
        :return: list
        """

        raise NotImplementedError

        # versions = self.get_versions(return_version_numbers=True)
        # if not versions:
        #     return
        #
        # version_paths = versions[0]
        # version_numbers = versions[1]
        #
        # comment_path = self._get_comment_path()
        # if not comment_path:
        #     return []
        #
        # datas = list()
        # if path.is_file(comment_path):
        #     read = fileio.FileReader(comment_path)
        #     lines = read.read()
        #     for line in lines:
        #         line_info_dict = dict()
        #         user = None
        #         comment = None
        #         split_line = line.split(';')
        #         for sub_line in split_line:
        #             assign = sub_line.split('=')
        #             if assign and assign[0]:
        #                 data_name = assign[0].strip()
        #                 data_value = assign[1].strip()
        #                 line_info_dict[data_name] = data_value
        #
        #         if 'version' not in line_info_dict:
        #             continue
        #
        #         version = int(line_info_dict['version'])
        #         if not int(line_info_dict['version']) in version_numbers:
        #             continue
        #
        #         if 'comment' in line_info_dict:
        #             comment = line_info_dict['comment']
        #             comment = comment[1:-1]
        #         if 'user' in line_info_dict:
        #             user = line_info_dict['user']
        #             user = user[1:-1]
        #
        #         version_file = version_paths[version]
        #         version_file = path.join_path(self._file_path, '{}/{}'.format(
        #         self._version_folder_name, version_file))
        #
        #         file_size = fileio.get_file_size(version_file)
        #         modified = fileio.get_last_modified_date(version_file)
        #
        #         datas.append([version, comment, user, file_size, modified, version_file])
        #
        # return datas

    def _prepare_directories(self):
        """
        Internal function used to prepare necessary directories and files for version
        :return:
        """
        self._create_version_folder()
        self._create_comment_file()

    def _create_version_folder(self):
        self._version_folder = folder.create_folder(self._version_folder_name, self._path)

    def _create_comment_file(self):
        self._comment_file = fileio.create_file('comments.json', self._version_folder)

    def _increment_version_file_name(self):
        version_path = path.join_path(self._version_folder, '.1')
        return path.unique_path_name(version_path)

    def _get_version_number(self, file_path):
        version_number = name_utils.get_end_number(file_path)
        return version_number

    def _get_version_path(self, version_number):
        version_path = path.join_path(self._get_version_folder(), self._version_name + '.' + str(version_number))
        return version_path

    def _get_version_folder(self):
        if path.is_file(self._file_path):
            version_dir = path.dirname(self._file_path)
            version_path = path.join_path(version_dir, self._version_folder_name)
            if not os.path.isdir(version_path):
                version_path = path.join_path(self._path, self._version_folder_name)
        else:
            version_path = path.join_path(self._file_path, self._version_folder_name)

        return version_path

    def _get_comment_path(self):
        version_folder = self._get_version_folder()
        comment_path = None
        if version_folder:
            comment_path = path.join_path(version_folder, 'comments.json')

        return comment_path

    def _default_version_file_name(self):
        if not self._version_name:
            return

        version_folder = self._get_version_folder()
        version_path = path.join_path(version_folder, self._version_name + '.default')

        return version_path

    def _save(self, file_name):
        self._prepare_directories()
        if path.is_dir(self._file_path):
            folder.copy_folder(self._file_path, file_name)
        elif path.is_file(self._file_path):
            fileio.copy_file(self._file_path, file_name)

    def delete_version(self, version_number):
        """
        Deletes specific version file
        :param version_number: int
        """

        version_path = self.get_version_path(version_number)
        if path.is_file(version_path):
            fileio.delete_file(version_path)
        else:
            folder.delete_folder(path)


def delete_versions(folder, keep=1):
    """
    Deletes all version in the given folder maintaining only the exact number of keep versions
    :param folder: str
    :param keep: int
    """

    version_inst = VersionFile(folder)
    version_list = version_inst.get_version_numbers()
    if not version_list:
        return

    count = len(version_list)
    if count <= keep:
        return

    deleted = 0
    for version in version_list:
        version_inst.delete_version(version)
        deleted += 1
        if count - deleted == keep:
            break


def get_comments(comment_directory, comment_filename=None):
    """
    Returns all the comments from a comments.txt file
    :param comment_directory: str, directory where comment.txt file is located
    :param comment_filename: str, name of the c omment file. By default, comment.txt.
    :return: dict(filename, value), (comment, user)
    """

    comment_filename = comment_filename or 'comments.json'
    comment_file = path.join_path(comment_directory, comment_filename)
    if not comment_file or not os.path.isfile(comment_file):
        return

    comments = dict()
    comments_data = jsonio.read_file(comment_file)
    if not comments_data:
        return comments

    for version_dict in comments_data:
        file_name = version_dict.get('version', None)
        comment = version_dict.get('comment', '')
        user = version_dict.get('user', '')
        if comment_filename and comment_filename == file_name:
            return comment,
        comments[file_name] = [comment, user]

    return comments
