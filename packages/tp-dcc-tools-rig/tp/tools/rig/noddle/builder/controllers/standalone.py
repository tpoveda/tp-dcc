from __future__ import annotations

from tp.tools.rig.noddle.builder.controllers import abstract


class StandaloneNoddleController(abstract.AbstractNoddleController):

    def open_file(self, file_path: str, force: bool = False) -> bool:
        """
        Open file within DCC scene.

        :param str file_path: absolute file path pointing to a valid Maya file.
        :param bool force: whether to force the opening of the file.
        :return: True if file was opened successfully; False otherwise.
        :rtype: bool
        """

        return True

    def reference_file(self, file_path: str) -> bool:
        """
        References file within DCC scene.

        :param str file_path: absolute file path pointing to a valid Maya file.
        :return: True if file was referenced successfully; False otherwise.
        :rtype: bool
        """

        return True

    def reference_model(self):
        pass

    def clear_all_references(self):
        pass

    def increment_save_file(self, file_type):
        pass

    def save_file_as(self, file_type):
        pass
