from __future__ import annotations

import logging
from typing import Any
from dataclasses import dataclass

from Qt.QtCore import Qt, Signal, QObject, QModelIndex
from Qt.QtWidgets import QStyledItemDelegate

from tp.qt.mvc import Model, UiProperty
from tp.qt.widgets.viewmodel.models import TableModel
from tp.qt.widgets.viewmodel.data import BaseDataSource, ColumnDataSource
from tp.qt.widgets.viewmodel.roles import BUTTON_CLICKED_ROLE
from tp.qt.widgets.viewmodel.delegates import LineEditButtonDelegate

from tp.libs.noddle.library.matching import matchconstants, matchutils

from .events import GetSelectionFromSceneEvent, BuildRigFromSkeletonEvent

logger = logging.getLogger(__name__)

SKELETONS: list[tuple[str, dict[str, str] | dict[str, list[str]]]] = (
    matchconstants.SKELETONS
)
NODDLE_IDS: list[tuple[str, dict[str, list[str]], list[str]]] = [
    matchconstants.NODDLE_IDS[0]
]


class RigFromSkeletonModel(Model):
    """Model class for Rig from Skeleton tool."""

    getSelectionFromScene = Signal(GetSelectionFromSceneEvent)
    buildRigFromSkeleton = Signal(BuildRigFromSkeletonEvent)

    def __init__(self):
        super().__init__()

        self._table_model = RigFromSkeletonTableModel()
        self._source_column = SourceColumn(model=self, header_text="Source Joints")
        self._target_column = TargetColumn(
            model=self, header_text="Matching Noddle Guides"
        )
        self._source_mapping_list: list[
            tuple[str, dict[str, str] | dict[str, list[str]]]
        ] = SKELETONS
        self._target_mapping_list: list[tuple[str, dict[str, list[str]], list[str]]] = (
            NODDLE_IDS
        )
        self._noddle_orders: list[list[str]] = []
        self._scene_selection: list[Any] = []

    def initialize_properties(self) -> list[UiProperty]:
        """
        Initializes the properties associated with the instance.

        This method initializes the properties associated with the instance.

        :return: A list of initialized UI properties.
        """

        properties = [
            UiProperty("auto_left_right", True),
            UiProperty("source_namespace", ""),
            UiProperty("source_left", "_L"),
            UiProperty("source_right", "_R"),
            UiProperty("source_always_prefix", False),
            UiProperty("source_always_suffix", False),
            UiProperty("source_separator", False),
            UiProperty("source_prefix", ""),
            UiProperty("source_suffix", ""),
            UiProperty("active_preset_source_index", 0),
            UiProperty("active_preset_target_index", 0),
            UiProperty("preset_source_names", [], type=list[str]),
            UiProperty("preset_target_names", [], type=list[str]),
            UiProperty("selected_rows_indexes", [], type=list[QModelIndex]),
            UiProperty("progress", 0),
            UiProperty("progress_message", ""),
        ]

        return properties

    @property
    def table_model(self) -> RigFromSkeletonTableModel:
        """
        Getter method that returns the table model of the model.

        :return: Table model of the model.
        """

        return self._table_model

    @property
    def source_column(self) -> SourceColumn:
        """
        Getter method that returns the source column of the model.

        :return: Source column of the model.
        """

        return self._source_column

    @property
    def target_column(self) -> TargetColumn:
        """
        Getter method that returns the target column of the model.

        :return: Target column of the model.
        """

        return self._target_column

    @property
    def active_preset_source_name(self) -> str:
        """
        Getter method that returns the active preset source name of the model.

        :return: Active preset source name of the model.
        """

        return self.properties.preset_source_names.value[
            self.properties.active_preset_source_index.value
        ]

    @property
    def active_preset_target_name(self) -> str:
        """
        Getter method that returns the active preset target name of the model.

        :return: Active preset target name of the model.
        """

        return self.properties.preset_target_names.value[
            self.properties.active_preset_target_index.value
        ]

    @property
    def active_preset_names(self) -> tuple[str, str]:
        """
        Getter method that returns the active preset names of the model.

        :return: Active preset names of the model.
        """

        return self.active_preset_source_name, self.active_preset_target_name

    @property
    def scene_selection(self) -> list[str]:
        """
        Getter method that returns the scene selection of the model.

        :return: Scene selection of the model.
        """

        return self._scene_selection

    @property
    def source_target_data(self) -> tuple[list[str], list[str]]:
        """
        Getter method that returns the source and target data of the model.

        :return: Source and target data of the model.
        """

        source_data: list[str] = []
        target_data: list[str] = []
        for i in range(self._table_model.rowCount()):
            item = self._table_model.row_data_source.user_object(i)
            source_data.append(item.source)
            target_data.append(item.target)

        return source_data, target_data

    @property
    def ids(self) -> dict[str, list[str]]:
        """
        Getter method that returns the IDs of the model.

        :return: IDs of the model.
        """

        _, target_preset_name = self.active_preset_names

        noddle_ids: dict[str, list[str]] = {}
        for i, preset in enumerate(self._target_mapping_list):
            if target_preset_name == preset[0]:
                noddle_ids = preset[1]
                break

        return noddle_ids

    @property
    def order(self) -> list[str]:
        """
        Getter method that returns the order of the model.

        :return: Order of the model.
        """

        _, target_preset_name = self.active_preset_names

        noddle_order: list[str] = []
        for i, preset in enumerate(self._target_mapping_list):
            if target_preset_name == preset[0]:
                noddle_order = self._noddle_orders[i]
                break
            else:
                noddle_order = self._noddle_orders[0]

        return noddle_order

    @property
    def skeleton(self) -> dict[str, str]:
        source_preset_name, _ = self.active_preset_names

        # Update sources,as the order may have changed.
        skeleton: dict[str, str] = {}
        for preset in self._source_mapping_list:
            if source_preset_name == preset[0]:
                skeleton = preset[1]
                break

        return skeleton

    def load_presets(self):
        """Loads the presets from the model."""

        self.load_preset_source_names()
        self.load_preset_target_names()

    def load_preset_source_names(self):
        """Loads the preset source names from the model."""

        preset_source_names: list[str] = []
        for i in range(len(self._source_mapping_list)):
            preset_source_names.append(self._source_mapping_list[i][0])
        preset_source_names.insert(0, "--- Select Skeleton ---")
        self.update_property("preset_source_names", preset_source_names)

    def load_preset_target_names(self):
        """Loads the preset target names from the model."""

        self._noddle_orders.clear()
        preset_target_names: list[str] = []
        for i in range(len(self._target_mapping_list)):
            preset_target_names.append(self._target_mapping_list[i][0])
            self._noddle_orders.append(self._target_mapping_list[i][2])

        preset_target_names.insert(0, "--- Select Noddle Biped ---")
        self.update_property("preset_target_names", preset_target_names)

    def update_sources_from_active_presets(self):
        """
        Updates the sources from the active presets.
        """

        source_preset_name, _ = self.active_preset_names

        noddle_order = self.order
        skeleton = self.skeleton
        if not skeleton:
            return

        ordered_joints = matchutils.skeleton_ordered_list(skeleton, order=noddle_order)
        if not ordered_joints:
            logger.warning(f"Preset not found: {source_preset_name}")
            return

        self._table_model.add_joints(ordered_joints)

    def update_targets_from_active_presets(self):
        """
        Updates the targets from the active presets.
        """

        source_preset_name, target_preset_name = self.active_preset_names

        noddle_ids = self.ids
        noddle_order = self.order
        if not noddle_ids:
            return
        noddle_ids_list = matchutils.noddle_ids_dict_string_list(
            noddle_ids, order=noddle_order
        )
        if not noddle_ids_list:
            logger.warning(f"Preset not found: {target_preset_name}")
            return

        self._table_model.add_noddle_ids(noddle_ids_list)

        skeleton = self.skeleton
        if not skeleton:
            return

        ordered_joints = matchutils.skeleton_ordered_list(skeleton, order=noddle_order)
        if not ordered_joints:
            logger.warning(f"Preset not found: {source_preset_name}")
            return

        self._table_model.add_joints(ordered_joints)

    def update_scene_selection(self) -> list[Any]:
        """
        Updates the scene selection from the model.

        :return: Scene selection from the model.
        """

        event = GetSelectionFromSceneEvent()
        self.getSelectionFromScene.emit(event)
        self._scene_selection = event.selection

        return self._scene_selection

    def insert_item(self):
        """
        Inserts an item into the table model based on current selection.
        """

        indexes = self.properties.selected_rows_indexes.value
        insert_index = self._table_model.rowCount()
        if indexes:
            insert_index = indexes[0].row()

        items = [TableModelItem("", "")]
        self._table_model.insert_items(items, insert_index=insert_index)

    def remove_selected_item(self):
        """
        Removes an item from the table model based on current selection.
        """

        indexes = self.properties.selected_rows_indexes.value
        if not indexes:
            return

        for index in indexes:
            self._table_model.removeRow(index.row())

    def remove_selected_items(self):
        """
        Removes selected items from the table model.
        """

        indexes = self.properties.selected_rows_indexes.value
        if not indexes:
            return

        for index in reversed(indexes):
            self._table_model.removeRow(index.row())

    def clear_items(self):
        """
        Clears all items from the table model.
        """

        self._table_model.clear()

    def build_from_skeleton(self, rig_name: str = ''):
        """
        Builds the rig from the skeleton.

        :param rig_name: Name of the rig to build.
        """

        source_joints, target_ids = self.source_target_data
        event = BuildRigFromSkeletonEvent(
            source_joints=source_joints,
            target_ids=target_ids,
            order=self.order,
            rig_name=rig_name or "biped",
            source_namespace=self.properties.source_namespace.value,
            source_prefix=self.properties.source_prefix.value,
            source_suffix=self.properties.source_suffix.value,
            update_function=self._update_progress,
        )
        self.buildRigFromSkeleton.emit(event)

    def _update_progress(self, progress: int, message: str):
        """
        Internal function that updates the progress of the operation.

        :param progress: progress value.
        :param message: progress message.
        """

        logger.info("----------------------")
        logger.info(message)
        logger.info("----------------------")

        self.update_property("progress", progress)
        self.update_property("progress_message", message)

        if progress == 0:
            pass
        elif progress == 100:
            pass


@dataclass
class TableModelItem:
    """Data class that represents an item in the table model."""

    source: str
    target: str


class RigFromSkeletonTableModel(TableModel):
    """
    Table model class for Rig from Skeleton tool.
    """

    def clear(self):
        """Clears the table model of the model."""

        self.row_data_source.set_user_objects([])
        self.reload()

    def add_joints(self, joint_names: list[str]):
        """
        Adds joints to the table model.

        :param joint_names: list of joint names to add.
        """

        if not joint_names:
            return

        items = self._auto_add_rows(joint_names)
        for i, item in enumerate(items):
            item.source = joint_names[i]

        self._update_from_items(items, clear_existing=True)

    def add_noddle_ids(self, ids: list[str]):
        """
        Adds Noddle IDs to the table model.

        :param ids: list of Noddle IDs to add.
        """

        self.clear()

        if not ids:
            return

        items = self._auto_add_rows(ids)
        for i, item in enumerate(items):
            item.target = ids[i]

        self._update_from_items(items, clear_existing=True)

    def insert_items(
        self, items: list[TableModelItem], insert_index: int | None = None
    ):
        """
        Inserts items into the table model.

        :param items: items to insert.
        :param insert_index: index to insert new rows at. If None, they will be appended to the end of the table.
        """

        self._update_from_items(items, clear_existing=False, insert_index=insert_index)

    def _all_items(self) -> list[TableModelItem]:
        """
        Internal function that returns all items in the table model.

        :return: All items in the table model.
        """

        items: list[TableModelItem] = []
        row_count = self.rowCount()
        for i in range(row_count):
            item = self.row_data_source.user_object(i)
            items.append(item)

        return items

    def _auto_add_rows(self, items: list[str]):
        """
        Internal function that automatically add rows to the table to ensure enough
        rows for the items are available.
        """

        new_count = len(items)
        items = self._all_items()
        row_count = len(items)
        if new_count > row_count:
            new_rows = new_count - row_count
            for _ in range(new_rows):
                new_item = TableModelItem("", "")
                items.append(new_item)

        return items

    def _update_from_items(
        self,
        items: list[TableModelItem],
        clear_existing: bool = True,
        insert_index: int | None = None,
    ):
        """Internal function that updates the table with given items.

        :param items: items to update the table with.
        :param clear_existing: whether to clear existing items or not.
        :param insert_index: index to insert new rows at. If None, they will be appended to the end of the table.
        """

        if clear_existing:
            self.clear()

        if insert_index is None:
            insert_index = self.rowCount()
        self.insertRows(insert_index, count=len(items), items=items)


class SourceColumn(BaseDataSource):
    """
    Data in the first column (source) of the table.
    """

    def __init__(
        self,
        model: RigFromSkeletonModel,
        header_text: str | None = None,
        table_model: RigFromSkeletonTableModel | None = None,
        parent: BaseDataSource | None = None,
    ):
        super().__init__(header_text=header_text, model=table_model, parent=parent)

        self._rig_from_skeleton_model = model

    def column_count(self) -> int:
        """
        Overrides `column_count` function to return the total column count of the data source.

        :return: column count.
        """

        # NOTE: This specifies how many columns the item has, which is not the same
        # as the number of columns in the table view (this can be specified in the view
        # code directly).

        return 3

    def custom_roles(self, index: int) -> list[int]:
        """
        Overrides `custom_roles` function to return the custom roles at the given index.

        :param index: index to get the custom roles for.
        :return: custom roles at the given index.
        """

        return [BUTTON_CLICKED_ROLE]

    def data(self, index: int) -> Any:
        """
        Overrides `data` function to returns the data at the given index.

        :param index: index to get the data for.
        :return: data at the given index.
        """

        user_data = self.user_object(index)
        return user_data.source if user_data else ""

    def data_by_role(self, index: int, role: Qt.ItemDataRole) -> Any:
        """
        Overrides `data_by_role` function to returns the data at the given index by role.

        :param index: index to get the data for.
        :param role: role to get the data for.
        :return: data at the given index by role.
        """

        if role != BUTTON_CLICKED_ROLE:
            return None

        model_index = self.model.index(index, 0)
        if not model_index.isValid():
            return None

        selection = self._rig_from_skeleton_model.update_scene_selection()
        if not selection:
            logger.warning("Please select a joint to match a guide to.")
            return False

        # If we are not in the first column (source), we do not want to do anything.
        if model_index.column() != 0:
            return

        return self._model.setData(model_index, selection[0], Qt.EditRole)

    def set_data(self, index: int, value: Any):
        """
        Overrides `set_data` functino to set the data at the given index.

        :param index: index to set the data for.
        :param value: value to set.
        """

        user_data = self.user_object(index)
        if not user_data:
            return False

        user_data.source = value
        return True

    def insert_children(self, index: int, children: list[TableModelItem]):
        """
        Overrides `insert_children` function to inserts children at the given index.

        :param index: index to insert the children at.
        :param children: children to insert.
        """

        self._children[index:index] = children
        return True

    # noinspection PyMethodOverriding
    def insert_row_data_sources(
        self, index: int, count: int, items: list[TableModelItem]
    ) -> bool:
        """
        Inserts row data sources at the given index.

        :param index: index to insert the row data sources at.
        :param count: number of row data sources to insert.
        :param items: items to insert as row data sources.
        :return: True if the row data sources were inserted successfully; False otherwise.
        """

        return self.insert_children(index, items)

    def delegate(self, parent: QObject) -> QStyledItemDelegate:
        """
        Returns the delegate for the data source.

        :param parent: parent widget.
        :return: delegate for the data source.
        """

        return LineEditButtonDelegate(parent=parent)


class TargetColumn(ColumnDataSource):
    """
    Data in the second column (target) of the table.
    """

    def __init__(
        self,
        model: RigFromSkeletonModel,
        header_text: str | None = None,
        table_model: TableModel | None = None,
        parent: BaseDataSource | None = None,
    ):
        super().__init__(header_text=header_text, model=table_model, parent=parent)

        self._rig_from_skeleton_model = model

    def custom_roles(self, row_data_source: BaseDataSource, index: int) -> list[int]:
        """
        Overrides `custom_roles` to return the custom roles at the given index.

        :param row_data_source: row data source to get the custom roles for.
        :param index: index to get the custom roles for.
        :return: custom roles at the given index.
        """

        return [BUTTON_CLICKED_ROLE]

    def data(self, row_data_source: BaseDataSource, index: int) -> Any:
        """
        Overrides `data` function to return the data at the given index.

        :param row_data_source: row data source to get the data for.
        :param index: column index to get the data for.
        :return: data at the given index.
        """

        user_data = row_data_source.user_object(index)
        return user_data.target if user_data and user_data.target else ""

    def data_by_role(
        self, row_data_source: BaseDataSource, index: int, role: Qt.ItemDataRole
    ) -> Any:
        """
        Overrides `data_by_role` function to return the data at the given index by role.

        :param row_data_source: row data source to get the data for.
        :param index: index to get the data for.
        :param role: role to get the data for.
        :return: data at the given index by role.
        """

        if role != BUTTON_CLICKED_ROLE:
            return None

        model_index = self.model.index(index, 1)
        if not model_index.isValid():
            return None

        selection = self._rig_from_skeleton_model.update_scene_selection()
        if not selection:
            logger.warning("Please select a Noddle Guide to match to a joint.")
            return False

        # If we are not in the first column (target), we do not want to do anything.
        if model_index.column() != 1:
            return

        # return self._model.setData(model_index, selection[0], Qt.EditRole)

    def set_data(self, row_data_source: BaseDataSource, index: int, value: Any):
        """
        Overrides `set_data` function to sets the data at the given index.

        :param row_data_source: row data source to set the data for.
        :param index: column index to set the data for.
        :param value: value to set.
        """

        user_data = row_data_source.user_object(index)
        if not user_data:
            return False

        user_data.target = value

        return True

    def delegate(self, parent: QObject) -> QStyledItemDelegate:
        """
        Returns the delegate for the data source.

        :param parent: parent widget.
        :return: delegate for the data source.
        """

        return LineEditButtonDelegate(parent=parent)
