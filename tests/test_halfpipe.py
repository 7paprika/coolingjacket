import math

import pytest

from core.calc import calculate_half_pipe_geometry, calculate_ho_area


def test_calculate_half_pipe_geometry_uses_pitch_to_determine_turn_count_and_area():
    geometry = calculate_half_pipe_geometry(
        vessel_outer_diameter=2.024,
        straight_length=3.0,
        coverage_fraction=0.8,
        half_pipe_width=0.08,
        pitch=0.10,
    )

    expected_covered_height = 3.0 * 0.8
    expected_turns = expected_covered_height / 0.10
    expected_helix_per_turn = math.sqrt((math.pi * 2.024) ** 2 + 0.10 ** 2)
    expected_total_helix = expected_turns * expected_helix_per_turn
    expected_contact_area = expected_total_helix * 0.08

    assert geometry.turn_count == pytest.approx(expected_turns)
    assert geometry.helix_length_m == pytest.approx(expected_total_helix)
    assert geometry.contact_area_m2 == pytest.approx(expected_contact_area)


def test_calculate_ho_area_for_half_pipe_returns_turns_based_area_not_full_shell_area():
    result = calculate_ho_area(
        jacket_type="Half-Pipe",
        j_dim=0.08,
        j_pitch=0.10,
        Q_sec=15.0 / 3600.0,
        rho_s=917.0,
        mu_s=0.18e-3,
        cp_s=4310.0,
        k_s=0.683,
        d_in=2.0,
        wall_thk=0.012,
        tt_len=3.0,
        jacket_coverage=0.8,
        head_type="2:1 Ellipsoidal",
    )

    (
        h_o,
        _Nu_s,
        _Re_s,
        _v_s,
        _A_cross,
        _De,
        _Pr_s,
        a_jacket,
        _v_total,
        half_pipe_turns,
        half_pipe_helix_length,
    ) = result

    assert h_o > 0
    assert half_pipe_turns == pytest.approx((3.0 * 0.8) / 0.10)
    assert half_pipe_helix_length > math.pi * (2.0 + 2 * 0.012)
    assert a_jacket < (math.pi * (2.0 + 2 * 0.012) * 3.0 * 0.8) + 1.084 * ((2.0 + 2 * 0.012) ** 2)
