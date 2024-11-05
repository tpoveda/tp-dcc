from __future__ import annotations

import time
import logging
from collections import defaultdict

import unreal

from .controlrig import api

logger = logging.getLogger(__name__)


def get_control_rig_blueprint_to_build() -> api.ControlRig | None:
    """
    Returns the Control Rig Blueprint to build the Base Human Control Rig.

    :return: Control Rig Blueprint to build the Base Human Control Rig.
    """

    open_blueprints = unreal.ControlRigBlueprint.get_currently_open_rig_blueprints()
    if not open_blueprints:
        logger.error("No Control Rig Blueprints are currently open!")
        return None
    if len(open_blueprints) > 1:
        logger.error(
            "More than one Control Rig Blueprint is currently open. Please open only 1 blueprint."
        )
        return None
    blueprint = open_blueprints[0]
    control_rig = api.ControlRig().init(blueprint)

    return control_rig


def run() -> bool:
    """
    Builds the Base Human Control Rig.

    :return: Whether the operation was successful or not.
    """

    logger.info("===================== Base Human Control Rig =====================")
    start_time = time.time()
    try:
        control_rig = get_control_rig_blueprint_to_build()
        if not control_rig:
            return False

        origin = api.create_null(control_rig, "origin")

        control_rig.current_solver = 0
        api.start_function(control_rig, "FORWARD", create_sequence_node=True)

        # =============================================================================================================
        # Module.Start -> m_placement
        # Module.Inputs: []
        # Module.Outputs: ["jnt_m_placement"]
        api.log_build_message("Building m_placement ...")
        api.increment_build_progress()
        control_rig.set_new_column()
        placement_control = api.Control.create(
            control_rig,
            name="placement",
            side="m",
            matrix=[
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            slider_scale=[1.0, 1.0, 1.0],
            shape="Square_Thick",
            shape_matrix=[
                [5.0, 0.0, 0.0, 0.0],
                [0.0, 5.0, 0.0, 0.0],
                [0.0, 0.0, 5.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            parent=origin,
            overwrite_color=(1.0, 1.0, 0.0),
            control_type="transform",
            filtered_channels=[
                "TRANSLATION_X",
                "TRANSLATION_Y",
                "TRANSLATION_Z",
                "PITCH",
                "YAW",
                "ROLL",
                "SCALE_X",
                "SCALE_Y",
                "SCALE_Z",
            ],
            out=False,
            offsets=[],
            offset_matrices={},
            passer=True,
            proxy=False,
            extra_slider_scale=False,
            driven_controls=[],
        )
        control_rig.set_new_column()
        m_placement_feature_fk_node = api.create_single_bone(
            placement_control, "None", child_maintain_bone=None
        )
        control_rig.set_new_column()
        api.increment_build_progress()
        # Module.End -> m_placement
        # =============================================================================================================

        # =============================================================================================================
        # Module.Start -> m_cog
        # Module.Inputs: []
        # Module.Outputs: ["jnt_m_cog"]
        api.log_build_message("Building m_cog ...")
        api.increment_build_progress()
        control_rig.set_new_column()
        cog_control = api.Control.create(
            control_rig,
            name="cog",
            side="m",
            matrix=[
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, -1.5380725092582148, 101.41567586140484, 1.0],
            ],
            slider_scale=[1.0, 1.0, 1.0],
            shape="Circle_Thick",
            shape_matrix=[
                [5.0, 0.0, 0.0, 0.0],
                [0.0, 5.0, 0.0, 0.0],
                [0.0, 0.0, 5.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            parent=origin,
            overwrite_color=(0.0, 1.0, 0.0),
            control_type="transform",
            filtered_channels=[
                "TRANSLATION_X",
                "TRANSLATION_Y",
                "TRANSLATION_Z",
                "PITCH",
                "YAW",
                "ROLL",
                "SCALE_X",
                "SCALE_Y",
                "SCALE_Z",
            ],
            out=False,
            offsets=[],
            offset_matrices={},
            passer=True,
            proxy=False,
            extra_slider_scale=False,
            driven_controls=[],
        )
        control_rig.set_new_column()
        m_cog_feature_fk_node = api.create_single_bone(
            cog_control, "None", child_maintain_bone=None
        )
        attachers_feature_fk = defaultdict(list)
        attachers_feature_fk["ATTACHER_root_t"].extend([placement_control.control])
        attachers_feature_fk["ATTACHER_root_r"].extend([placement_control.control])
        for attacher, elements in attachers_feature_fk.items():
            api.connect_to_pin_constraint_parent_array(
                control_rig, elements, f"{m_cog_feature_fk_node}.{attacher}"
            )
        control_rig.set_new_column()
        api.increment_build_progress()
        # Module.End -> m_cog
        # =============================================================================================================

        # =============================================================================================================
        # Module.Start -> m_spine
        # Module.Inputs: []
        # Module.Outputs: ["jnt_m_cog"]
        api.log_build_message("Building m_spine ...")
        api.increment_build_progress()
        control_rig.set_new_column()
        m_spine_fk_spline_origin = api.create_null(
            control_rig, "m_spine_fkSpline_origin", parent=origin
        )
        spine_base_control = api.Control.create(
            control_rig,
            name="spineBase",
            side="m",
            matrix=[
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 0.9999999999999999, 0.0, 0.0],
                [0.0, 0.0, 0.9999999999999999, 0.0],
                [0.0, -3.0567650337770775, 90.06397956026694, 1.0],
            ],
            slider_scale=[1.0, 1.0, 1.0],
            shape="Circle_Thick",
            shape_matrix=[
                [5.0, 0.0, 0.0, 0.0],
                [0.0, 5.0, 0.0, 0.0],
                [0.0, 0.0, 5.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            parent=m_spine_fk_spline_origin,
            overwrite_color=(1.0, 1.0, 0.0),
            control_type="transform",
            filtered_channels=[
                "TRANSLATION_X",
                "TRANSLATION_Y",
                "TRANSLATION_Z",
                "PITCH",
                "YAW",
                "ROLL",
                "SCALE_X",
                "SCALE_Y",
                "SCALE_Z",
            ],
            out=False,
            offsets=[],
            offset_matrices={},
            passer=True,
            proxy=False,
            extra_slider_scale=False,
            driven_controls=[],
        )
        spine_spline_fk_a_ctrl = api.Control.create(
            control_rig,
            name="spineSplineFk_A",
            side="m",
            matrix=[
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 0.9999999999999999, 0.0, 0.0],
                [0.0, 0.0, 0.9999999999999999, 0.0],
                [0.0, -1.8991610230397653, 105.85806545030724, 1.0],
            ],
            slider_scale=[1.0, 1.0, 1.0],
            shape="Circle_Thick",
            shape_matrix=[
                [5.0, 0.0, 0.0, 0.0],
                [0.0, 5.0, 0.0, 0.0],
                [0.0, 0.0, 5.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            parent=spine_base_control.out,
            overwrite_color=(1.0, 1.0, 0.0),
            control_type="transform",
            filtered_channels=[
                "TRANSLATION_X",
                "TRANSLATION_Y",
                "TRANSLATION_Z",
                "PITCH",
                "YAW",
                "ROLL",
                "SCALE_X",
                "SCALE_Y",
                "SCALE_Z",
            ],
            out=False,
            offsets=[],
            offset_matrices={},
            passer=True,
            proxy=False,
            extra_slider_scale=False,
            driven_controls=[],
        )
        spine_spline_fk_b_ctrl = api.Control.create(
            control_rig,
            name="spineSplineFk_B",
            side="m",
            matrix=[
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 0.9999999999999999, 0.0, 0.0],
                [0.0, 0.0, 0.9999999999999999, 0.0],
                [1.232595164407831e-31, -2.415424995779227, 119.02518828686992, 1.0],
            ],
            slider_scale=[1.0, 1.0, 1.0],
            shape="Circle_Thick",
            shape_matrix=[
                [5.0, 0.0, 0.0, 0.0],
                [0.0, 5.0, 0.0, 0.0],
                [0.0, 0.0, 5.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            parent=spine_base_control.out,
            overwrite_color=(1.0, 1.0, 0.0),
            control_type="transform",
            filtered_channels=[
                "TRANSLATION_X",
                "TRANSLATION_Y",
                "TRANSLATION_Z",
                "PITCH",
                "YAW",
                "ROLL",
                "SCALE_X",
                "SCALE_Y",
                "SCALE_Z",
            ],
            out=False,
            offsets=[],
            offset_matrices={},
            passer=True,
            proxy=False,
            extra_slider_scale=False,
            driven_controls=[],
        )
        grp_m_spine_end = api.create_null(
            control_rig,
            "grp_m_spine_end",
            matrix=[
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 0.9999999999999999, 0.0, 0.0],
                [0.0, 0.0, 0.9999999999999999, 0.0],
                [0.0, -3.0229925501122263, 142.6740189726236, 1.0],
            ],
            parent=spine_spline_fk_b_ctrl.out,
        )
        control_rig.set_new_column()
        api.create_blend_attributes(
            control_rig,
            attribute_parent=spine_spline_fk_b_ctrl.control,
            attribute_names=["space_local", "space_base"],
        )
        control_rig.set_new_column()
        api.create_fk_spline(
            control_rig,
            m_spine_fk_spline_origin,
            controls=[
                spine_base_control,
                spine_spline_fk_a_ctrl,
                spine_spline_fk_b_ctrl,
            ],
            joints=[
                "jnt_m_spineSpine_000",
                "jnt_m_spineSpine_001",
                "jnt_m_spineSpine_002",
                "jnt_m_spineSpine_003",
                "jnt_m_spineSpine_end",
            ],
            side="m",
            control_weightings=[
                [0, 0, 0],
                [0, 1, 0.834954455271386],
                [1, 2, 0.7538332913297483],
                [2, 3, 0.39378084892979803],
                [2, 3, 0.9999992000862572],
            ],
            end_null=grp_m_spine_end,
            up_vector=[0.0, 0.9999998, -0.0006419],
        )
        # Module.End -> m_spine
        # =============================================================================================================

    except Exception:
        logger.exception(
            "Something went wrong while building Base Human Control Rig: {err}",
            exc_info=True,
        )
        raise

    logger.info(
        f"Base Human Control Rig build took: {time.time() - start_time} seconds"
    )

    return True


def run_ui():
    api.open_build_window(run, 20)
