import math
import numpy as np

def calculate_hi(rho, mu, cp, k_p, N_rps, d_agit, d_in, agit_type):
    Pr_p = (cp * mu) / k_p
    
    if "None" in agit_type:
        # Natural Convection calculation roughly assuming dT = 10 K, beta = 0.0002 1/K
        g = 9.81
        beta = 0.0002
        dT = 10.0
        Gr = (rho**2 * g * beta * dT * (d_in**3)) / (mu**2) if mu > 0 else 0
        Ra = Gr * Pr_p
        Nu_p = 0.1 * (Ra**(1/3)) if Ra > 0 else 0
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
    
    if jacket_type == "Half-Pipe":
        De = 0.61 * j_dim
        A_cross = (math.pi * j_dim**2) / 8
        v_s = Q_sec / A_cross if A_cross > 0 else 0
        Re_s = (rho_s * v_s * De) / mu_s
        Nu_s = 0.023 * (Re_s**0.8) * (Pr_s**0.4)
        h_o = (Nu_s * k_s) / De if De > 0 else 0

    elif jacket_type == "Conventional (with Baffle)":
        De = 2 * j_dim
        A_cross = j_dim * j_pitch
        v_s = Q_sec / A_cross if A_cross > 0 else 0
        Re_s = (rho_s * v_s * De) / mu_s
        Nu_s = 0.027 * (Re_s**0.8) * (Pr_s**0.33)
        h_o = (Nu_s * k_s) / De if De > 0 else 0
    else:
        Re_s = 0
        Nu_s = 0
        v_s = 0
        h_o = 1500.0
        
    d_out = d_in + 2*wall_thk
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
    a_jacket = (math.pi * d_out * tt_len * jacket_coverage) + head_area 
        
    return h_o, Nu_s, Re_s, v_s, A_cross, De, Pr_s, a_jacket, v_total

def jacket_ode(T, t, eff_UA, T_s, M_cp, Q_a, Q_r):
    return (eff_UA * (T_s - T) + Q_a + Q_r) / M_cp
