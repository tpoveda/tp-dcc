from __future__ import annotations

import typing
import weakref

import unreal

from .. import consts
from . import factory

if typing.TYPE_CHECKING:
    from ..controllers import ControlRig


class Control:
    """
    Class that represents a control rig control object.
    """

    ALL_CREATED_CONTROLS: list[Control] = []

    def __init__(self, control_rig: ControlRig):
        super().__init__()

        self._control_rig = weakref.ref(control_rig)
        self._name: str | None = None
        self._side: str | None = None
        self._passer: unreal.RigElementKey | None = None
        self._control: unreal.RigElementKey | None = None
        self._out: unreal.RigElementKey | None = None
        self._offsets: dict[str, unreal.RigElementKey] = {}

    @classmethod
    def create(
        cls,
        control_rig: ControlRig,
        name: str = "noname",
        side: str = "m",
        index: int | None = None,
        matrix: list[list[float]] | None = None,
        slider_scale: list[float] | None = None,
        extra_slider_scale: bool = False,
        parent: unreal.RigElementKey | None = None,
        shape_matrix: list[list[float]] | None = None,
        passer: bool = True,
        proxy: bool = False,
        out: bool = False,
        shape: str = "cube",
        filtered_channels: list[str] | None = None,
        is_no_control: bool = False,
        overwrite_color: tuple[float, float, float] | None = None,
        control_type: str = "transform",
        offsets: list[str] | None = None,
        offset_matrices: dict[str, list[float, float, float, float]] | None = None,
        driven_controls: list[unreal.RigElementKey] | None = None,
    ) -> Control:
        """
        Creates a new control object.

        :param control_rig: control rig object that will contain the new control.
        :param name: name of the control.
        :param side: side of the control.
        :param index:
        :param matrix:
        :param slider_scale:
        :param extra_slider_scale:
        :param parent:
        :param shape_matrix:
        :param passer:
        :param proxy:
        :param out:
        :param shape:
        :param filtered_channels:
        :param is_no_control:
        :param overwrite_color:
        :param control_type:
        :param offsets:
        :param offset_matrices:
        :param driven_controls:
        :return:
        """

        matrix = matrix or consts.IDENTITY_MATRIX.copy()

        new_control = cls(control_rig)
        new_control.name = name
        new_control.side = side
        new_control.index = index

        control_splits = [""] * 4
        control_splits[0] = name
        if new_control.index is not None:
            control_splits[1] = "%03d" % new_control.index
        if new_control.side == "l":
            control_splits[2] = "_l"
        elif new_control.side == "r":
            control_splits[2] = "_r"
        control_splits[3] = "__" if is_no_control else "_ctrl"
        control_name = "".join(control_splits)

        if passer:
            new_control.passer = factory.create_null(
                control_rig,
                f"{side}_{name}Passer",
                matrix=matrix,
                slider_scale=[1, 1, 1] if extra_slider_scale else slider_scale,
                parent=parent,
            )

        filtered_channels = [
            consts.FILTERED_CHANNELS[channel] for channel in filtered_channels
        ]
        new_control.control = factory.create_control(
            control_rig,
            name=control_name,
            parent=new_control.passer if passer else parent,
            side=new_control.side,
            shape=shape,
            shape_matrix=shape_matrix,
            overwrite_color=overwrite_color,
            control_type=control_type,
            filtered_channels=filtered_channels,
            proxy=proxy,
            driven_controls=driven_controls,
        )
        if not passer:
            new_control.passer = new_control.control

        if out:
            new_control.out = factory.create_null(
                control_rig,
                f"{side}_{name}Out",
                parent=new_control.control,
                match=new_control.control,
                transform_in_global=False,
                slider_scale=[
                    1.0 / slider_scale[0],
                    1.0 / slider_scale[1],
                    1.0 / slider_scale[2],
                ],
            )
        else:
            new_control.out = new_control.control

        new_control.offsets.clear()
        if extra_slider_scale and "slider" not in offsets:
            offsets.append("slider")
        new_control.add_offsets(
            offsets,
            slider_scale_on_slider=slider_scale if extra_slider_scale else [1, 1, 1],
            offset_matrices=offset_matrices,
        )

        Control.ALL_CREATED_CONTROLS.append(new_control)

        return new_control

    @property
    def control_rig(self) -> ControlRig:
        """
        Returns the control rig object that contains this control.

        :return: ControlRig
        """
        return self._control_rig()

    @property
    def name(self) -> str:
        """
        Returns the name of the control.

        :return: str
        """
        return self._name

    @name.setter
    def name(self, value: str):
        """
        Sets the name of the control.

        :param value: str
        """
        self._name = value

    @property
    def side(self) -> str:
        """
        Returns the side of the control.

        :return: str
        """
        return self._side

    @side.setter
    def side(self, value: str):
        """
        Sets the side of the control.

        :param value: str
        """
        self._side = value

    @property
    def passer(self) -> unreal.RigElementKey:
        """
        Returns the passer of the control.

        :return: unreal.RigElementKey
        """
        return self._passer

    @passer.setter
    def passer(self, value: unreal.RigElementKey):
        """
        Sets the passer of the control.

        :param value: unreal.RigElementKey
        """
        self._passer = value

    @property
    def control(self) -> unreal.RigElementKey:
        """
        Returns the control of the control.

        :return: unreal.RigElementKey
        """
        return self._control

    @control.setter
    def control(self, value: unreal.RigElementKey):
        """
        Sets the control of the control.

        :param value: unreal.RigElementKey
        """
        self._control = value

    @property
    def out(self) -> unreal.RigElementKey:
        """
        Returns the out of the control.

        :return: unreal.RigElementKey
        """
        return self._out

    @out.setter
    def out(self, value: unreal.RigElementKey):
        """
        Sets the out of the control.

        :param value: unreal.RigElementKey
        """
        self._out = value

    @property
    def offsets(self) -> dict[str, unreal.RigElementKey]:
        """
        Returns the offsets of the control.

        :return: dict[str, unreal.RigElementKey]
        """
        return self._offsets

    def add_offset(self, offset_name: str) -> unreal.RigElementKey:
        """
        Adds an offset to the control.

        :param offset_name: name of the offset.
        :return: created offset.
        """

        offset = factory.create_null(
            self.control_rig,
            f"grp_{self.side}_{self.name}_{offset_name}offset",
            self.control,
            parent=self.passer,
            transform_in_global=False,
        )
        self.control_rig.hierarchy.set_parent(
            self.control, offset, maintain_global_transform=True, setup_undo=False
        )
        self.offsets[offset_name] = offset

        return offset

    def add_offsets(
        self,
        offset_names: list[str],
        slider_scale_on_slider: list[float] | None = None,
        offset_matrices: dict | None = None,
    ) -> list[unreal.RigElementKey]:
        """
        Adds offsets to the control.

        :param offset_names: list of offset names.
        :param slider_scale_on_slider:
        :param offset_matrices:
        :return: created offsets.
        """

        slider_scale_on_slider = slider_scale_on_slider or [1, 1, 1]
        offset_matrices = offset_matrices or {}

        offsets: list[unreal.RigElementKey] = []
        last_parent = self.passer
        for offset_name in offset_names[::-1]:
            prefix = f"grp_{self.side}_{self.name}Offset"
            if offset_name.startswith(prefix):
                offset_key = offset_name.replace(prefix, "").lower()
            else:
                offset_key = offset_name
            offset = factory.create_null(
                self.control_rig,
                f"{prefix}{offset_key.title()}",
                match=self.control,
                parent=last_parent,
                transform_in_global=False,
                slider_scale=slider_scale_on_slider
                if offset_key == "slider"
                else [1, 1, 1],
                matrix=offset_matrices.get(offset_key, consts.IDENTITY_MATRIX.copy()),
            )
            self.control_rig.hierarchy.set_parent(
                self.control,
                offset,
                maintain_global_transform=False,
                setup_undo=False,
            )
            self.offsets[offset_key] = offset
            last_parent = offset
            offsets.append(offset)

        return offsets
