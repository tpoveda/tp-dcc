from __future__ import annotations

from typing import Tuple

from Qt.QtCore import QModelIndex, QAbstractItemModel, QAbstractProxyModel


def data_model_from_proxy_model(model: QAbstractProxyModel) -> QAbstractItemModel | None:
	"""
	Returns the root source data model from the given proxy model.

	:param QAbstractProxyModel model: proxy model to walk.
	:return: root data item model.
	:rtype: QAbstractItemModel
	"""

	if model is None:
		return None

	current_model = model
	while isinstance(current_model, QAbstractProxyModel):
		current_model = current_model.sourceModel()
		if not current_model:
			return None

	return current_model


def data_model_index_from_index(model_index: QModelIndex) -> Tuple[QModelIndex, QAbstractItemModel]:
	"""
	Returns the index from the root data model by walking the proxy model stack if present.

	:param QModelIndex model_index: Qt model index from the proxy model.
	:return: model index from the root data.
	:rtype: Tuple[QModelIndex, QAbstractItemModel]
	"""

	data_model = model_index.model()
	model_index_mapped = model_index
	while isinstance(data_model, QAbstractProxyModel):
		model_index_mapped = data_model.mapToSource(model_index_mapped)
		if not model_index.isValid():
			return model_index_mapped
		data_model = model_index_mapped.model()

	return model_index_mapped, data_model
