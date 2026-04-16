from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Iterable

import numpy as np


@dataclass
class HalfPipeGeometry:
    turn_count: float
    helix_length_m: float
    contact_area_m2: float
    covered_height_m: float


@dataclass
class SimulationInputs:
    d_in: float
    tt_len: float
    wall_thk: float
    jacket_coverage: float
    d_agit: float
    rpm: float
    rho_p: float
    cp_p: float
    mu_p: float
    k_p: float
    q_service_m3_h: float
    t_initial: float
    t_service: float
    t_target: float
    time_limit_min: float
    jacket_type: str = "Half-Pipe"
    j_pitch: float = 0.0


def validate_inputs(inputs: SimulationInputs) -> list[str]:
    errors: list[str] = []
    if inputs.d_in <= 0:
        errors.append("d_in must be greater than zero.")
    if inputs.tt_len <= 0:
        errors.append("tt_len must be greater than zero.")
    if inputs.wall_thk <= 0 or inputs.wall_thk >= inputs.d_in / 2:
        errors.append("wall_thk must be positive and smaller than the vessel radius.")
    if not 0 < inputs.jacket_coverage <= 1:
        errors.append("jacket_coverage must be between 0 and 1.")
    if inputs.jacket_type == "Half-Pipe" and inputs.j_pitch <= 0:
        errors.append("half-pipe pitch must be greater than zero.")
    if inputs.d_agit < 0:
        errors.append("agitator diameter must not be negative.")
    if inputs.d_agit >= inputs.d_in:
        errors.append("agitator diameter must be smaller than vessel ID.")
    if inputs.rpm < 0:
        errors.append("rpm must be zero or greater.")
    if inputs.rho_p <= 0:
        errors.append("rho_p must be greater than zero.")
    if inputs.cp_p <= 0:
        errors.append("cp_p must be greater than zero.")
    if inputs.mu_p <= 0:
        errors.append("mu_p must be greater than zero.")
    if inputs.k_p <= 0:
        errors.append("k_p must be greater than zero.")
    if inputs.q_service_m3_h <= 0:
        errors.append("q_service must be greater than zero.")
    if inputs.time_limit_min <= 0:
        errors.append("time_limit must be greater than zero.")
    return errors


def determine_operation_mode(t_initial: float, t_service: float, t_target: float) -> str:
    if math.isclose(t_initial, t_target, rel_tol=0.0, abs_tol=1e-9):
        return "Holding Mode"
    if t_service > t_initial:
        if t_target < t_initial:
            raise ValueError("Heating service cannot reach a target below the initial temperature.")
        return "Heating Mode"
    if t_service < t_initial:
        if t_target > t_initial:
            raise ValueError("Cooling service cannot reach a target above the initial temperature.")
        return "Cooling Mode"
    raise ValueError("Service temperature equals initial temperature, so there is no thermal driving force.")


def find_time_to_target(
    profile: Iterable[float],
    times_min: Iterable[float],
    t_target: float,
    op_mode: str,
) -> float | None:
    profile_arr = np.asarray(list(profile), dtype=float)
    times_arr = np.asarray(list(times_min), dtype=float)
    if profile_arr.size == 0 or times_arr.size == 0:
        return None
    if op_mode == "Holding Mode":
        return 0.0
    if op_mode == "Heating Mode":
        idx = np.where(profile_arr >= t_target)[0]
    else:
        idx = np.where(profile_arr <= t_target)[0]
    return float(times_arr[idx[0]]) if len(idx) > 0 else None


def build_share_state(**kwargs: Any) -> dict[str, Any]:
    state = dict(kwargs)
    if "custom_fluid_data" not in state:
        state["custom_fluid_data"] = None
    return state


def calculate_half_pipe_geometry(
    vessel_outer_diameter: float,
    straight_length: float,
    coverage_fraction: float,
    half_pipe_width: float,
    pitch: float,
) -> HalfPipeGeometry:
    covered_height = straight_length * coverage_fraction
    if pitch <= 0 or half_pipe_width <= 0 or covered_height <= 0:
        return HalfPipeGeometry(0.0, 0.0, 0.0, max(covered_height, 0.0))

    turn_count = covered_height / pitch
    helix_per_turn = math.sqrt((math.pi * vessel_outer_diameter) ** 2 + pitch**2)
    total_helix_length = turn_count * helix_per_turn
    contact_area = total_helix_length * half_pipe_width
    return HalfPipeGeometry(turn_count, total_helix_length, contact_area, covered_height)


def calculate_hi(rho, mu, cp, k_p, N_rps, d_agit, d_in, agit_type):
    Pr_p = (cp * mu) / k_p

    if "None" in agit_type:
        g = 9.81
        beta = 0.0002
        dT = 10.0
        Gr = (rho**2 * g * beta * dT * (d_in**3)) / (mu**2) if mu > 0 else 0
        Ra = Gr * Pr_p
        Nu_p = 0.1 * (Ra**(1 / 3)) if Ra > 0 else 0
        h_i = (Nu_p * k_p) / d_in if d_in > 0 else 0
        return h_i, Nu_p, 0, Pr_p, 0.1, Gr, Ra

    Re_agit = (rho * N_rps * (d_agit**2)) / mu

    if Re_agit > 0:
        if "Rushton Turbine" in agit_type:
            nu_const = 0.73
        elif "Anchor" in agit_type:
            nu_const = 0.36
        elif "Retreat Curve" in agit_type:
            nu_const = 0.37
        else:
            nu_const = 0.53
        Nu_p = nu_const * (Re_agit**0.67) * (Pr_p**0.33)
    else:
        nu_const = 0.53
        Nu_p = 0

    h_i = (Nu_p * k_p) / d_in if d_in > 0 else 0
    return h_i, Nu_p, Re_agit, Pr_p, nu_const, 0, 0


def calculate_ho_area(jacket_type, j_dim, j_pitch, Q_sec, rho_s, mu_s, cp_s, k_s, d_in, wall_thk, tt_len, jacket_coverage, head_type):
    Pr_s = (cp_s * mu_s) / k_s
    A_cross = 0
    De = 0
    half_pipe_turns = 0.0
    half_pipe_helix_length = 0.0

    d_out = d_in + 2 * wall_thk

    if jacket_type == "Half-Pipe":
        De = 0.61 * j_dim
        A_cross = (math.pi * j_dim**2) / 8
        v_s = Q_sec / A_cross if A_cross > 0 else 0
        Re_s = (rho_s * v_s * De) / mu_s if mu_s > 0 else 0
        Nu_s = 0.023 * (Re_s**0.8) * (Pr_s**0.4) if Re_s > 0 else 0
        h_o = (Nu_s * k_s) / De if De > 0 else 0
        half_pipe_geometry = calculate_half_pipe_geometry(d_out, tt_len, jacket_coverage, j_dim, j_pitch)
        half_pipe_turns = half_pipe_geometry.turn_count
        half_pipe_helix_length = half_pipe_geometry.helix_length_m
        straight_contact_area = half_pipe_geometry.contact_area_m2

    elif jacket_type == "Conventional (with Baffle)":
        De = 2 * j_dim
        A_cross = j_dim * j_pitch
        v_s = Q_sec / A_cross if A_cross > 0 else 0
        Re_s = (rho_s * v_s * De) / mu_s if mu_s > 0 else 0
        Nu_s = 0.027 * (Re_s**0.8) * (Pr_s**0.33) if Re_s > 0 else 0
        h_o = (Nu_s * k_s) / De if De > 0 else 0
        straight_contact_area = math.pi * d_out * tt_len * jacket_coverage
    else:
        Re_s = 0
        Nu_s = 0
        v_s = 0
        h_o = 1500.0
        straight_contact_area = math.pi * d_out * tt_len * jacket_coverage

    v_cyl = (math.pi / 4) * (d_in**2) * tt_len

    if head_type == "2:1 Ellipsoidal":
        v_head = (math.pi / 24) * (d_in**3)
        head_area = 1.084 * (d_out**2)
    elif head_type == "Hemispherical":
        v_head = (math.pi / 12) * (d_in**3)
        head_area = (math.pi / 2) * (d_out**2)
    else:
        v_head = 0.08 * (d_in**3)
        head_area = 1.013 * (d_out**2)

    v_total = v_cyl + v_head
    a_jacket = straight_contact_area + head_area

    return h_o, Nu_s, Re_s, v_s, A_cross, De, Pr_s, a_jacket, v_total, half_pipe_turns, half_pipe_helix_length


def jacket_ode(T, t, eff_UA, T_s, M_cp, Q_a, Q_r):
    return (eff_UA * (T_s - T) + Q_a + Q_r) / M_cp
