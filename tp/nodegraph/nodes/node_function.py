from __future__ import annotations

from typing import Type

from ..core.node import Node


class FunctionNode(Node):
    def __init__(
        self,
        func: callable,
        input_types: Type | list[Type],
        output_types: Type | list[Type],
        name: str = "function",
    ):
        super().__init__(name=name)


class AbsNode(FunctionNode):
    def __init__(self, name: str = "abs"):
        super().__init__(
            name=name,
            func=abs,
            input_types=[int, float],
            output_types=[int, float],
        )


class SubtractNode(FunctionNode):
    def __init__(self, name: str = "subtract"):
        super().__init__(
            name=name,
            func=lambda x, y: x - y,
            input_types=[int, float],
            output_types=[int, float],
        )


class MultiplyNode(FunctionNode):
    def __init__(self, name: str = "multiply"):
        super().__init__(
            name=name,
            func=lambda x, y: x * y,
            input_types=[int, float],
            output_types=[int, float],
        )
