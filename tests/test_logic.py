import math

import pytest

from core.calc import (
    SimulationInputs,
    build_share_state,
    determine_operation_mode,
    find_time_to_target,
    validate_inputs,
)


def sample_inputs(**overrides):
    data = {
        "d_in": 2.0,
        "tt_len": 3.0,
        "wall_thk": 0.012,
        "jacket_coverage": 0.8,
        "d_agit": 0.8,
        "rpm": 60.0,
        "rho_p": 1000.0,
        "cp_p": 4184.0,
        "mu_p": 0.005,
        "k_p": 0.6,
        "q_service_m3_h": 15.0,
        "t_initial": 20.0,
        "t_service": 150.0,
        "t_target": 80.0,
        "time_limit_min": 120.0,
        "jacket_type": "Half-Pipe",
        "j_pitch": 0.10,
    }
    data.update(overrides)
    return SimulationInputs(**data)


def test_validate_inputs_rejects_nonphysical_geometry_and_process_values():
    errors = validate_inputs(
        sample_inputs(
            d_in=0.0,
            tt_len=0.0,
            wall_thk=2.5,
            jacket_coverage=1.2,
            d_agit=3.0,
            rpm=-1.0,
            rho_p=0.0,
            cp_p=0.0,
            mu_p=0.0,
            k_p=0.0,
            q_service_m3_h=-1.0,
            time_limit_min=0.0,
        )
    )

    assert any("d_in" in err for err in errors)
    assert any("tt_len" in err for err in errors)
    assert any("wall_thk" in err for err in errors)
    assert any("jacket_coverage" in err for err in errors)
    assert any("agitator" in err.lower() for err in errors)
    assert any("rpm" in err.lower() for err in errors)
    assert any("rho_p" in err for err in errors)
    assert any("cp_p" in err for err in errors)
    assert any("mu_p" in err for err in errors)
    assert any("k_p" in err for err in errors)
    assert any("q_service" in err for err in errors)
    assert any("time_limit" in err for err in errors)


def test_determine_operation_mode_rejects_unreachable_target_direction():
    with pytest.raises(ValueError):
        determine_operation_mode(t_initial=80.0, t_service=20.0, t_target=100.0)

    with pytest.raises(ValueError):
        determine_operation_mode(t_initial=20.0, t_service=150.0, t_target=10.0)


def test_find_time_to_target_returns_zero_when_already_at_target():
    profile = [80.0, 81.0, 82.0]
    times = [0.0, 1.0, 2.0]

    result = find_time_to_target(profile, times, t_target=80.0, op_mode="Heating Mode")

    assert result == pytest.approx(0.0)


def test_find_time_to_target_returns_none_if_target_never_reached():
    profile = [20.0, 25.0, 30.0]
    times = [0.0, 1.0, 2.0]

    result = find_time_to_target(profile, times, t_target=80.0, op_mode="Heating Mode")

    assert result is None


def test_build_share_state_preserves_extended_fields():
    state = build_share_state(
        tank_no="R-1001",
        jacket_no="J-1001",
        service_name="Polymerization",
        t_target=80.0,
        time_limit=120,
        d_in=2.0,
        tt_len=3.0,
        head_type="2:1 Ellipsoidal",
        wall_mat="Stainless Steel 304",
        wall_thk=0.012,
        jacket_coverage=0.8,
        jacket_type="Conventional (with Baffle)",
        j_dim=0.05,
        j_pitch=0.2,
        agit_type="Pitched Blade (4-Blade 45°)",
        rpm=60.0,
        d_agit=0.8,
        has_rxn=True,
        q_rxn_kw=12.5,
        r_fi=0.0002,
        r_fo=0.0003,
        rho_p=1000.0,
        cp_p=4184.0,
        mu_cp=5.0,
        k_p=0.6,
        t_initial=20.0,
        service_fluid_type="Custom",
        q_service=15.0,
        t_service=150.0,
        custom_fluid_data={"t1": 20.0, "t2": 100.0},
        lang_opt="ko",
        half_pipe_mode="turns",
        half_pipe_turn_count=18.0,
    )

    assert state["has_rxn"] is True
    assert state["q_rxn_kw"] == pytest.approx(12.5)
    assert state["r_fi"] == pytest.approx(0.0002)
    assert state["r_fo"] == pytest.approx(0.0003)
    assert state["service_fluid_type"] == "Custom"
    assert state["custom_fluid_data"] == {"t1": 20.0, "t2": 100.0}
    assert state["lang_opt"] == "ko"
    assert state["half_pipe_mode"] == "turns"
    assert state["half_pipe_turn_count"] == pytest.approx(18.0)
