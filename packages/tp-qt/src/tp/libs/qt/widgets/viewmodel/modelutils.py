from __future__ import annotations

from Qt.QtCore import (
    QModelIndex,
    QAbstractItemModel,
    QAbstractProxyModel,
)
from Qt.QtGui import QStandardItemModel


def get_source_model(
    proxy_model: QAbstractProxyModel,
) -> QAbstractItemModel | QStandardItemModel | None:
    """Get the root source model from a proxy model chain.

    Traverses through a stack of proxy models to find the ultimate source model
    at the root of the chain. If the input is already a source
    model (not a proxy), it returns that model unchanged.

    Args:
        proxy_model: The proxy model to traverse. Can be None or any model type.

    Returns:
        The root source model at the end of the proxy chain, or None if:
            - The input model is `None.`
            - No valid source model is found in the chain.
            - Chain is broken (sourceModel() returns None).
    """

    if proxy_model is None:
        return None

    current_model = proxy_model
    while isinstance(current_model, QAbstractProxyModel):
        current_model = current_model.sourceModel()
        if not current_model:
            return None

    return current_model


def map_to_source_model(
    proxy_index: QModelIndex,
) -> tuple[QModelIndex, QAbstractItemModel | QStandardItemModel]:
    """Map a proxy model index to its source model index and model.

    Traverses the proxy model chain to find the root source model and the
    corresponding index. If the input index is already from a source model
    (not a proxy), it returns the index and model unchanged.

    Args:
        proxy_index: The model index from a proxy model to map to source.

    Returns:
        A tuple containing:
            - The mapped index in the source model
            - The source model instance
    """

    data_model = proxy_index.model()
    model_index_mapped = proxy_index
    while isinstance(data_model, QAbstractProxyModel):
        # noinspection PyUnresolvedReferences
        model_index_mapped = data_model.mapToSource(model_index_mapped)
        if not model_index_mapped.isValid():
            return model_index_mapped, data_model
        data_model = model_index_mapped.model()

    return model_index_mapped, data_model
