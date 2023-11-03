from tp.core import dcc, client, dccs


class NoddleBuilderClient(client.AbstractClient):

    def load_plugins(self):
        """
        Loads Noddle editor plugins
        """

        self.execute('load_plugins')

    def registered_nodes(self) -> dict:
        return self.execute('registered_nodes').get('ReturnValue', [])

    def open_file(self, file_path: str, force: bool = False) -> bool:
        """
        Open file within DCC scene.

        :param str file_path: absolute file path pointing to a valid Maya file.
        :param bool force: whether to force the opening of the file.
        :return: True if file was opened successfully; False otherwise.
        :rtype: bool
        """

        return self.execute('open_file', parameters={'file_path': file_path, 'force': force}).get('ReturnValue', False)

    def reference_file(self, file_path: str) -> bool:
        """
        References file within DCC scene.

        :param str file_path: absolute file path pointing to a valid Maya file.
        :return: True if file was referenced successfully; False otherwise.
        :rtype: bool
        """

        return self.execute('reference_file', parameters={'file_path': file_path}).get('ReturnValue', False)

    def reference_model(self):
        return self.execute('reference_model').get('ReturnValue', False)

    def clear_all_references(self):
        return self.execute('clear_all_references').get('ReturnValue', False)

    def increment_save_file(self, file_type):
        return self.execute('increment_save_file', parameters={'file_type': file_type}).get('ReturnValue', False)

    def save_file_as(self, file_type):
        return self.execute('save_file_as', parameters={'file_type': file_type}).get('ReturnValue', False)


class NoddleBuilderMayaClient(NoddleBuilderClient):
    def __init__(self):
        super().__init__(port=dcc.dcc_port(dccs.Maya), host_program=dccs.Maya)
