from __future__ import annotations

import typing
from typing import Sequence

import unreal

from . import consts

if typing.TYPE_CHECKING:
    from .nodes import NodePinInputOutput


class ControlRig:
    """
    Class that stores data related with control rig build.
    """

    def __init__(self):
        super().__init__()

        self._blueprint: unreal.ControlRigBlueprint | None = None
        self._vm_models: list[unreal.RigVMController] = []
        self._function_library: unreal.RigVMFunctionLibrary | None = None
        self._library_controller: unreal.RigVMController | None = None
        self._hierarchy_controller: unreal.RigHierarchyController | None = None
        self._function_blueprint: unreal.ControlRigBlueprint | None = None
        self._function_stacks: list[list[ControlRigFunctionData]] = []
        self._current_solver: int = 0

    @property
    def blueprint(self) -> unreal.ControlRigBlueprint:
        """
        Getter method that returns the Control Rig Blueprint.

        :return: Control Rig Blueprint.
        """

        return self._blueprint

    @property
    def library(self) -> unreal.RigVMController:
        """
        Getter method that returns the Rig Function Library.

        :return: Rig Function Library.
        """

        return self._library_controller

    @property
    def hierarchy(self) -> unreal.RigHierarchyController:
        """
        Getter method that returns the Rig Hierarchy Controller.

        :return: Rig Hierarchy Controller.
        """

        return self._hierarchy_controller

    @property
    def function_library(self) -> unreal.RigVMFunctionLibrary:
        """
        Getter method that returns the Function Library.

        :return: Function Library.
        """

        return self._function_library

    @property
    def function_stacks(self) -> list[list[ControlRigFunctionData]]:
        """
        Getter method that returns the function stacks.

        :return: list[list[ControlRigFunctionData]] with the function stacks.
        """

        return self._function_stacks

    @property
    def current_solver(self) -> int:
        """
        Getter method that returns the current solver index.

        :return: int with the current solver index.
        """

        return self._current_solver

    @current_solver.setter
    def current_solver(self, value: int):
        """
        Setter method that sets the current solver index.

        :param value: int with the new solver index.
        """

        self._current_solver = value

    def init(self, blueprint: unreal.ControlRigBlueprint) -> ControlRig:
        """
        Initializes the Control Rig instance.

        :param blueprint: Control Rig Blueprint to build.
        """

        self._blueprint = blueprint
        self._vm_models.append(blueprint.get_controller_by_name("RigVMModel"))
        self._function_library = blueprint.get_local_function_library()
        self._library_controller = blueprint.get_controller(self._function_library)
        self._hierarchy_controller = blueprint.hierarchy.get_controller()
        self._function_blueprint = unreal.load_object(
            name="/ControlRig/StandardFunctionLibrary/StandardFunctionLibrary.StandardFunctionLibrary",
            outer=None,
        )
        self._function_stacks = [
            [
                ControlRigFunctionData(
                    self._vm_models[0],
                    None,
                    solver=0,
                    execute_start="RigUnit_BeginExecution.ExecuteContext",
                )
            ],
            [
                ControlRigFunctionData(
                    self._vm_models[0],
                    None,
                    solver=1,
                    execute_start="RigUnit_InverseExecution.ExecuteContext",
                )
            ],
        ]

        self._blueprint.set_auto_vm_recompile(False)

        return self

    def function_stack(self) -> list[ControlRigFunctionData]:
        """
        Returns the current function stack based on current solver index..

        :return: list[ControlRigFunctionData] with the current function stack.
        """

        return self._function_stacks[self._current_solver]

    def latest_function_stack(self) -> ControlRigFunctionData:
        """
        Returns the latest function stack.

        :return: ControlRigFunctionData with the latest function stack.
        """

        return self.function_stack()[-1]

    def go_to_parent_execute(self):
        """
        Goes to the parent execute.
        """

        function_stack = self.function_stack()[-1]
        del function_stack.last_executes[-1]

    def add_function_to_stack(
        self,
        function_name: str,
        x_inputs: Sequence[NodePinInputOutput] | None = None,
        x_outputs: Sequence[NodePinInputOutput] | None = None,
        mutable: bool = True,
        sequence_node: str | None = None,
    ) -> ControlRigFunctionData:
        """
        Adds a new function to the stack.

        :param function_name: str with the function name.
        :param x_inputs: list[NodePinInputOutput] with the function inputs.
        :param x_outputs: list[NodePinInputOutput] with the function outputs.
        :param mutable: bool with whether the function is mutable or not.
        :param sequence_node: str with the sequence node name.
        :return: ControlRigFunctionData with the new function data.
        """

        function_data = ControlRigFunctionData(
            self._vm_models[0],
            function_name=function_name,
            mutable=mutable,
            sequence_node=sequence_node,
            solver=self._current_solver,
            x_inputs=x_inputs,
            x_outputs=x_outputs,
        )

        self.function_stack().append(function_data)

        return function_data

    def set_new_column(self, next_column_gap_factor: float = 1.0):
        """
        Sets the next function to be a new column.

        :param next_column_gap_factor: float with the next column gap factor.
        """

        function_stack = self.function_stack()[-1]
        function_stack.next_is_new_column = True
        function_stack.next_column_gap_factor = next_column_gap_factor

    def record_node_for_comment_box(
        self, vm_node: unreal.RigVMNode, estimated_size: list[int] | None = None
    ):
        """
        Records the node for the comment box.

        :param vm_node: Rig VM Node to record.
        :param estimated_size: list[int, int] with the estimated size of the node.
        """

        self.function_stack()[-1].record_node_for_comment_box(vm_node, estimated_size)

    def open_comment_box(self, comment: str):
        """
        Opens a comment box.

        :param comment: str with the comment box text.
        """

        self.function_stack()[-1].open_comment_box(comment)

    def close_comment_box(self, comment: str):
        """
        Closes a comment box.

        :param comment: str with the comment box text.
        """

        self.function_stack()[-1].close_comment_box(comment)


class ControlRigFunctionData:
    def __init__(
        self,
        rig_vm_controller: unreal.RigVMController,
        function_name: str | None,
        mutable: bool = True,
        sequence_node: str | None = None,
        solver: int = 0,
        execute_start: str = "Entry.ExecuteContext",
        x_inputs: list[NodePinInputOutput] = None,
        x_outputs: list[NodePinInputOutput] | None = None,
    ):
        super().__init__()

        self._vm_model = rig_vm_controller
        self._function_name = function_name
        self._mutable = mutable
        self._sequence_node = sequence_node
        self._last_sequencer_plug: unreal.RigVMPin | None = None
        self._current_sequence_plug_count = 0
        self._current_node_position = [0, consts.TOP_NODE_DEFAULTS[solver]]
        self._top_node_position = consts.TOP_NODE_DEFAULTS[solver]
        self._maximum_height = 0
        self._last_node_size = (0, 0)
        self._gap = 100
        self._last_executes: list[str] = []
        self._next_is_new_column = True
        self._next_column_gap_factor = 1.0
        self._comment_boxes_node_points = {}
        self._inputs = {
            _input.name: (_input.type, _input.is_array) for _input in x_inputs or []
        }
        self._outputs = {
            _output.name: (_output.type, _output.is_array)
            for _output in x_outputs or []
        }

        if mutable:
            self._last_executes.append(execute_start)

    @property
    def vm_model(self) -> unreal.RigVMController:
        """
        Getter method that returns the Rig VM Controller.

        :return: Rig VM Controller.
        """

        return self._vm_model

    @vm_model.setter
    def vm_model(self, value: unreal.RigVMController):
        """
        Setter method that sets the Rig VM Controller.

        :param value: Rig VM Controller.
        """

        self._vm_model = value

    @property
    def function_name(self) -> str:
        """
        Getter method that returns the function name.

        :return: str with the function name.
        """

        return self._function_name

    @property
    def mutable(self) -> bool:
        """
        Getter method that returns whether the function is mutable.

        :return: True if the function is mutable; False otherwise.
        """

        return self._mutable

    @property
    def sequence_node(self) -> str:
        """
        Getter method that returns the name of the sequence node associated with this function.

        :return: name of the sequencer node.
        """

        return self._sequence_node

    @sequence_node.setter
    def sequence_node(self, value: str):
        """
        Setter method that sets the sequence node name associated with this function.

        :param value: name of the sequence node.
        """

        self._sequence_node = value

    @property
    def last_sequencer_plug(self) -> unreal.RigVMPin:
        """
        Getter method that returns the last sequencer plug.

        :return: RigVMPin with the last sequencer plug.
        """

        return self._last_sequencer_plug

    @last_sequencer_plug.setter
    def last_sequencer_plug(self, value: unreal.RigVMPin):
        """
        Setter method that sets the last sequencer plug.

        :param value: RigVMPin with the last sequencer plug.
        """

        self._last_sequencer_plug = value

    @property
    def current_sequence_plug_count(self) -> int:
        """
        Getter method that returns the current sequence plug count.

        :return: int with the current sequence plug count.
        """

        return self._current_sequence_plug_count

    @current_sequence_plug_count.setter
    def current_sequence_plug_count(self, value: int):
        """
        Setter method that sets the current sequence plug count.

        :param value: int with the new sequence plug count.
        """

        self._current_sequence_plug_count = value

    @property
    def next_is_new_column(self) -> bool:
        """
        Getter method that returns whether the next function is a new column.

        :return: True if the next function is a new column; False otherwise.
        """

        return self._next_is_new_column

    @next_is_new_column.setter
    def next_is_new_column(self, value: bool):
        """
        Setter method that sets whether the next function is a new column.

        :param value: bool with the new value.
        """

        self._next_is_new_column = value

    @property
    def next_column_gap_factor(self) -> float:
        """
        Getter method that returns the next column gap factor.

        :return: float with the next column gap factor.
        """

        return self._next_column_gap_factor

    @next_column_gap_factor.setter
    def next_column_gap_factor(self, value: float):
        """
        Setter method that sets the next column gap factor.

        :param value: float with the new next column gap factor.
        """

        self._next_column_gap_factor = value

    @property
    def last_executes(self) -> list[str]:
        """
        Getter method that returns the last executes.

        :return: list[str] with the last executes.
        """

        return self._last_executes

    @property
    def current_node_position(self) -> list[int]:
        """
        Getter method that returns the current node position.

        :return: list[int] with the current node position.
        """

        return self._current_node_position

    @property
    def top_node_position(self) -> int:
        """
        Getter method that returns the top node position.

        :return: int with the top node position.
        """

        return self._top_node_position

    @top_node_position.setter
    def top_node_position(self, value: int):
        """
        Setter method that sets the top node position.

        :param value: int with the new top node position.
        """

        self._top_node_position = value

    @property
    def maximum_height(self) -> int:
        """
        Getter method that returns the maximum height.

        :return: int with the maximum height.
        """

        return self._maximum_height

    @maximum_height.setter
    def maximum_height(self, value: int):
        """
        Setter method that sets the maximum height.

        :param value: int with the new maximum height.
        """

        self._maximum_height = value

    @property
    def last_node_size(self) -> tuple[int, int]:
        """
        Getter method that returns the last node size.

        :return: tuple[int, int] with the last node size.
        """

        return self._last_node_size

    @last_node_size.setter
    def last_node_size(self, value: tuple[int, int]):
        """
        Setter method that sets the last node size.

        :param value: tuple[int, int] with the new last node size.
        """

        self._last_node_size = value

    @property
    def gap(self) -> int:
        """
        Getter method that returns the gap between nodes.

        :return: int with the gap between nodes.
        """

        return self._gap

    @property
    def inputs(self) -> dict[str, tuple[str, bool]]:
        """
        Getter method that returns the inputs.

        :return: dict[str, tuple[str, bool]] with the inputs.
        """

        return self._inputs

    @property
    def outputs(self) -> dict[str, tuple[str, bool]]:
        """
        Getter method that returns the outputs.

        :return: dict[str, tuple[str, bool]] with the outputs.
        """

        return self._outputs

    def record_node_for_comment_box(
        self, vm_node: unreal.RigVMNode, estimated_size: list[int, int] | None = None
    ):
        """
        Records the node for the comment box.

        :param vm_node: Rig VM Node to record.
        :param estimated_size: list[int, int] with the estimated size of the node.
        """

        estimated_size = estimated_size or [200, 200]
        position = vm_node.get_position()
        for comment in list(self._comment_boxes_node_points.keys()):
            self._comment_boxes_node_points[comment].append([position.x, position.y])
            self._comment_boxes_node_points[comment].append(
                [position.x + estimated_size[0], position.y + estimated_size[1]]
            )

    def open_comment_box(self, comment: str):
        """
        Opens a comment box.

        :param comment: str with the comment box text.
        """

        self._comment_boxes_node_points[comment] = []

    def close_comment_box(
        self, comment: str, color: list[float, float, float] | None = None
    ):
        """
        Closes a comment box.

        :param comment: str with the comment box text.
        :param color: list[float, float, float] with the comment box color.
        :raises Exception: If the comment is not valid.
        """

        color = color or [0.25, 0.25, 0.25]

        if comment not in self._comment_boxes_node_points:
            raise Exception(
                f"Invalid comment, possible comments in this function are {', '.join(list(self._comment_boxes_node_points.keys()))}"
            )

        nodes_points = self._comment_boxes_node_points[comment]
        if len(nodes_points):
            all_x = [fPos[0] for fPos in nodes_points]
            all_y = [fPos[1] for fPos in nodes_points]
            smallest_x = min(all_x)
            smallest_y = min(all_y)
            size_x = max(all_x) - smallest_x
            size_y = max(all_y) - smallest_y
            self.vm_model.add_comment_node(
                comment,
                unreal.Vector2D(
                    smallest_x - consts.COMMENT_BOX_BORDER_SIZE,
                    smallest_y - consts.COMMENT_BOX_BORDER_SIZE,
                ),
                unreal.Vector2D(
                    size_x + consts.COMMENT_BOX_BORDER_SIZE * 2,
                    size_y + consts.COMMENT_BOX_BORDER_SIZE * 2,
                ),
                unreal.LinearColor(color[0], color[1], color[2], 0.2),
                "EdGraphNode_Comment",
                setup_undo_redo=False,
            )
        del self._comment_boxes_node_points[comment]
