from __future__ import annotations

import typing


from .. import consts

if typing.TYPE_CHECKING:
    from ..controllers import ControlRig


class Variable:
    def __init__(
        self, name: str, type: str = "double", cpp_type: str = "", local: bool = False
    ):
        super().__init__()

        self._name = name
        self._type = type
        self._cpp_type = cpp_type
        self._local = local

    def __repr__(self) -> str:
        """
        Returns a string representation of the variable.

        :return: string representation of the variable.
        """

        return f"<{self.__class__.__name__}: ({self._name}, {self._type})"

    def __str__(self) -> str:
        """
        Returns a string representation of the variable.

        :return: string representation of the variable.
        """

        return f"<{self.__class__.__name__}: ({self._name}, {self._type})"

    @property
    def name(self) -> str:
        """
        Returns the name of the variable.

        :return: str
        """

        return self._name

    @property
    def type(self) -> str:
        """
        Returns the type of the variable.

        :return: str
        """

        return self._type

    @property
    def cpp_type(self) -> str:
        """
        Returns the C++ type of the variable.

        :return: str
        """

        return self._cpp_type

    @property
    def local(self) -> bool:
        """
        Returns whether the variable is local or not.

        :return: bool
        """

        return self._local


# noinspection PyShadowingBuiltins
def new_variable(
    control_rig: ControlRig,
    name: str,
    type: str = "double",
    is_array: bool = False,
    local: bool = True,
) -> Variable:
    """
    Creates a new variable.

    :param control_rig: control rig to create the variable in.
    :param name: name of the variable.
    :param type: type of the variable.
    :param is_array: whether the variable is an array or not.
    :param local: whether the variable is local or not.
    :return: newly created variable.
    """

    cpp_type = consts.CPP_TYPE_TO_OBJECT_PATH.get(type, "")

    if local:
        function_stack = control_rig.latest_function_stack()
        if name in function_stack.inputs:
            raise Exception(
                f'The variable name "{name}" already exists in the inputs of the function stack.'
            )
        type_to_pass = f"TArray<{type}>" if is_array else type
        # noinspection PyTypeChecker
        function_stack.vm_model.add_local_variable_from_object_path(
            name, type_to_pass, cpp_type, "", setup_undo_redo=False
        )
        variable = Variable(name, type_to_pass, cpp_type, local=local)
    else:
        type_to_pass = cpp_type or type
        if is_array:
            type_to_pass = f"TArray<{type_to_pass}>"
        # noinspection PyTypeChecker
        control_rig.blueprint.add_member_variable(
            name, type_to_pass, is_public=False, is_read_only=False, default_value=""
        )
        variable = Variable(name, type_to_pass, cpp_type)

    return variable
