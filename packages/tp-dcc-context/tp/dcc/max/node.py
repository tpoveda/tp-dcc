from tp.dcc import abstract
from tp.dcc.abstract import node


class MaxNode(node.Node):

    __slots__ = ()
    __array_index_type__ = abstract.ArrayIndexType.OneBased
