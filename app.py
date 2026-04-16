import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.integrate import odeint
import math
import json
import zlib
import base64

from core.config import MATERIAL_K, AGITATOR_DB, SERVICE_FLUID_DB
from core.fluid import get_service_fluid_props
from core.calc import (
    SimulationInputs,
    build_share_state,
    calculate_hi,
    calculate_ho_area,
    determine_operation_mode,
    find_time_to_target,
    jacket_ode,
    validate_inputs,
)
from utils.i18n import i18n
from utils.export import generate_html, create_pdf

st.set_page_config(page_title="Jacketed Vessel Engineering", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Main Background & Font overrides for premium look */
    .stApp {
        background-color: #f7f9fc;
    }
    
    /* Elegant Container Borders */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px;
        border: 1px solid rgba(0, 0, 0, 0.08);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        background-color: #ffffff;
        padding: 5px;
        margin-bottom: 5px;
    }

    h1, h2, h3 {
        color: #1a252f !important;
        font-weight: 700 !important;
    }
    
    /* Call to Action Button */
    div[data-testid="stButton"] > button {
        border-radius: 8px;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

def encode_state(state_dict):
    json_str = json.dumps(state_dict)
    compressed = zlib.compress(json_str.encode('utf-8'))
    return base64.urlsafe_b64encode(compressed).decode('utf-8')


def decode_state(b64_str):
    try:
        compressed = base64.urlsafe_b64decode(b64_str.encode('utf-8'))
        return json.loads(zlib.decompress(compressed).decode('utf-8'))
    except Exception:
        return {}


query_params = st.query_params
init = decode_state(query_params.get("data", "")) if "data" in query_params else {}
lang_opt = st.sidebar.radio("Language / 언어", ["en", "ko"], index=["en", "ko"].index(init.get("lang_opt", "en")))
t = i18n[lang_opt]

st.title(t["title"])

# ==========================================
# 1. 사이드바 (정보 및 상태 저장)
# ==========================================
with st.sidebar:
    st.header("📌 Identifications")
    tank_no = st.text_input("Vessel Tag No.", value=init.get("tank_no", "R-1001"), help=t["h_tank_no"])
    jacket_no = st.text_input("Jacket Tag No.", value=init.get("jacket_no", "J-1001"), help=t["h_jacket_no"])
    service_name = st.text_input("Service Name", value=init.get("service_name", "Polymerization"), help=t["h_service"])
    
    st.divider()
    st.header("⏱️ Simulation Target")
    t_target = st.number_input("Target Temp (°C)", value=init.get("t_target", 80.0), help=t["h_ttarget"])
    time_limit = st.number_input("Sim. Time (min)", value=init.get("time_limit", 120), min_value=10, help=t["h_tlimit"])
    
    st.divider()
    st.header("💾 State Management")
    if st.button("Generate Share Link", type="primary", use_container_width=True):
        st.session_state["save_trigger"] = True

tab1, tab2, tab3 = st.tabs([t["tab1"], t["tab2"], t["tab3"]])

with tab1:
    c1, c2, c3 = st.columns(3)
    
    with c1:
        with st.container(border=True):
            st.subheader("⚙️ " + t["geom_mat"])
            d_in = st.number_input("Vessel ID (mm)", value=init.get("d_in", 2000.0), step=100.0, help=t["h_din"]) / 1000.0
            tt_len = st.number_input("T/T Length (mm)", value=init.get("tt_len", 3000.0), step=100.0, help=t["h_ttlen"]) / 1000.0
            head_type = st.selectbox("Bottom Head Type", ["2:1 Ellipsoidal", "Hemispherical", "Torispherical"], index=["2:1 Ellipsoidal", "Hemispherical", "Torispherical"].index(init.get("head_type", "2:1 Ellipsoidal")), help=t["h_head"])
            wall_mat = st.selectbox("Wall Material", list(MATERIAL_K.keys()), index=list(MATERIAL_K.keys()).index(init.get("wall_mat", "Stainless Steel 304")), help=t["h_mat"])
            wall_thk = st.number_input("Wall Thickness (mm)", value=init.get("wall_thk", 12.0), help=t["h_thk"]) / 1000.0
            jacket_coverage = st.number_input("Jacket Straight Coverage (%)", value=init.get("jacket_coverage", 80.0), help=t["h_cov"]) / 100.0
            
        with st.container(border=True):
            st.subheader("🔧 Jacket Configuration")
            jacket_type = st.selectbox("Jacket Type", ["Half-Pipe", "Conventional (with Baffle)", "Dimple"], index=["Half-Pipe", "Conventional (with Baffle)", "Dimple"].index(init.get("jacket_type", "Half-Pipe")), help=t["h_jtype"])
            if jacket_type == "Half-Pipe":
                j_dim = st.number_input("Pipe ID (mm)", value=init.get("j_dim", 80.0), help=t["h_jdim"]) / 1000.0
                j_pitch = 0.0
            elif jacket_type == "Conventional (with Baffle)":
                j_dim = st.number_input("Annular Gap (mm)", value=init.get("j_dim", 50.0), help=t["h_jdim"]) / 1000.0
                j_pitch = st.number_input("Baffle Pitch (mm)", value=init.get("j_pitch", 200.0), help=t["h_jpitch"]) / 1000.0
            else:
                j_dim, j_pitch = 0.0, 0.0

    with c2:
        with st.container(border=True):
            st.subheader("🌪️ " + t["agit_specs"])
            agit_type = st.selectbox("Impeller Type", list(AGITATOR_DB.keys()), index=list(AGITATOR_DB.keys()).index(init.get("agit_type", "Pitched Blade (4-Blade 45°)")), help=t["h_atype"])
            agit_info = AGITATOR_DB[agit_type]
            st.markdown(agit_info["svg"], unsafe_allow_html=True)
            st.caption(f"**Power Number ($N_p$):** {agit_info['Np']}")
            rpm = st.number_input("Agitator Speed (RPM)", value=init.get("rpm", 60.0), help=t["h_rpm"])
            d_agit = st.number_input("Impeller Diameter (mm)", value=init.get("d_agit", 800.0), help=t["h_dagit"]) / 1000.0
            if d_agit >= d_in and "None" not in agit_type:
                st.error("⚠️ Error: Impeller Diameter must be smaller than Vessel ID.")
                
        with st.container(border=True):
            st.subheader("🔥 Reaction Heat")
            has_rxn = st.checkbox("Include Heat of Reaction", value=init.get("has_rxn", False), help=t["h_hrxn"])
            q_rxn_kw = st.number_input("Q_rxn (kW, + is Exothermic)", value=init.get("q_rxn_kw", 0.0), help=t["h_qrxn"]) if has_rxn else 0.0

        with st.container(border=True):
            st.subheader("🦠 Fouling Factors (m²K/W)")
            with st.expander("TEMA Recommended Values / 권장값 가이드"):
                st.markdown("- Organics / Polymers: ~0.0002 to 0.0004\n- Cooling Water (Utility): ~0.0002\n- Steam Condensing: ~0.0001\n- Brine: ~0.0002")
            r_fi = st.number_input("Inside Fouling (R_fi)", value=init.get("r_fi", 0.0002), format="%.5f")
            r_fo = st.number_input("Outside Fouling (R_fo)", value=init.get("r_fo", 0.0002), format="%.5f")

    with c3:
        with st.container(border=True):
            st.subheader("🧪 Process Fluid (Inside)")
            rho_p = st.number_input("Density (kg/m³)", value=init.get("rho_p", 1000.0), help=t["h_rhop"])
            cp_p = st.number_input("Specific Heat (J/kg·K)", value=init.get("cp_p", 4184.0), help=t["h_cpp"])
            mu_cp = st.number_input("Viscosity (cP)", value=init.get("mu_cp", 5.0), format="%.2f", help=t["h_mup"]) 
            k_p = st.number_input("Thermal Cond. (W/m·K)", value=init.get("k_p", 0.6), help=t["h_kp"])
            t_initial = st.number_input("Initial Temp (°C)", value=init.get("t_initial", 20.0), help=t["h_tinit"])

        with st.container(border=True):
            st.subheader("💧 Service Fluid (Jacket)")
            service_fluid_options = ["Water", "Thermal Oil (Dowtherm A)", "Steam (Condensing)", "Brine (20% NaCl)", "Custom"]
            service_fluid_type = st.selectbox(
                "Fluid Type",
                service_fluid_options,
                index=service_fluid_options.index(init.get("service_fluid_type", "Water")),
                help=t["h_stype"],
            )
            q_service = st.number_input("Service Flow Rate (m³/h)", value=init.get("q_service", 15.0), help=t["h_qserv"])
            t_service = st.number_input("Service Inlet Temp (°C)", value=init.get("t_service", 150.0), help=t["h_tserv"])
            
            c_dict = None
            if service_fluid_type == "Custom":
                custom_init = init.get("custom_fluid_data", {})
                st.caption("Enter 2 Temperature points for interpolation (T1 < T2)")
                tc1, tc2 = st.columns(2)
                with tc1:
                    c_t1 = st.number_input("T1 (°C)", value=custom_init.get("t1", 20.0))
                    c_rho1 = st.number_input("ρ1 (kg/m³)", value=custom_init.get("rho1", 1000.0))
                    c_cp1 = st.number_input("Cp1 (J/kg·K)", value=custom_init.get("cp1", 4180.0))
                    c_mu1 = st.number_input("μ1 (cP)", value=custom_init.get("mu1", 1.0))
                    c_k1 = st.number_input("k1 (W/m·K)", value=custom_init.get("k1", 0.6))
                with tc2:
                    c_t2 = st.number_input("T2 (°C)", value=custom_init.get("t2", 100.0))
                    c_rho2 = st.number_input("ρ2 (kg/m³)", value=custom_init.get("rho2", 958.0))
                    c_cp2 = st.number_input("Cp2 (J/kg·K)", value=custom_init.get("cp2", 4216.0))
                    c_mu2 = st.number_input("μ2 (cP)", value=custom_init.get("mu2", 0.28))
                    c_k2 = st.number_input("k2 (W/m·K)", value=custom_init.get("k2", 0.679))
                c_dict = {"t1":c_t1, "t2":c_t2, "rho1":c_rho1, "rho2":c_rho2, "cp1":c_cp1, "cp2":c_cp2, "mu1":c_mu1, "mu2":c_mu2, "k1":c_k1, "k2":c_k2}

sim_inputs = SimulationInputs(
    d_in=d_in,
    tt_len=tt_len,
    wall_thk=wall_thk,
    jacket_coverage=jacket_coverage,
    d_agit=d_agit,
    rpm=rpm,
    rho_p=rho_p,
    cp_p=cp_p,
    mu_p=mu_cp * 0.001,
    k_p=k_p,
    q_service_m3_h=q_service,
    t_initial=t_initial,
    t_service=t_service,
    t_target=t_target,
    time_limit_min=time_limit,
)
validation_errors = validate_inputs(sim_inputs)

if st.session_state.get("save_trigger"):
    current_state = build_share_state(
        tank_no=tank_no,
        jacket_no=jacket_no,
        service_name=service_name,
        t_target=t_target,
        time_limit=time_limit,
        d_in=d_in * 1000,
        tt_len=tt_len * 1000,
        head_type=head_type,
        wall_mat=wall_mat,
        wall_thk=wall_thk * 1000,
        jacket_coverage=jacket_coverage * 100,
        jacket_type=jacket_type,
        j_dim=j_dim * 1000,
        j_pitch=j_pitch * 1000,
        agit_type=agit_type,
        rpm=rpm,
        d_agit=d_agit * 1000,
        has_rxn=has_rxn,
        q_rxn_kw=q_rxn_kw,
        r_fi=r_fi,
        r_fo=r_fo,
        rho_p=rho_p,
        cp_p=cp_p,
        mu_cp=mu_cp,
        k_p=k_p,
        t_initial=t_initial,
        service_fluid_type=service_fluid_type,
        q_service=q_service,
        t_service=t_service,
        custom_fluid_data=c_dict,
        lang_opt=lang_opt,
    )
    st.query_params["data"] = encode_state(current_state)
    st.session_state["save_trigger"] = False
    st.sidebar.success("✅ Link Updated! Copy the URL.")

with tab2:
    st.header(t["tab2"])
    if validation_errors:
        for error in validation_errors:
            st.error(f"⚠️ {error}")
        st.stop()

    k_wall = MATERIAL_K[wall_mat]
    mu_p = mu_cp * 0.001 
    N_rps = rpm / 60.0
    Q_sec = q_service / 3600.0 
    
    fluid_props = get_service_fluid_props(service_fluid_type, t_service, c_dict)
    rho_s, cp_s, mu_s, k_s = fluid_props["rho"], fluid_props["cp"], fluid_props["mu"], fluid_props["k"]

    h_i_calc, Nu_p, Re_a, Pr_p, nu_const, Gr, Ra = calculate_hi(rho_p, mu_p, cp_p, k_p, N_rps, d_agit, d_in, agit_type)
    
    desc_hi_en = "The inside film coefficient (h_i) represents the heat transfer efficiency driven by the process fluid flow. It measures how effectively agitation (or free convection) reduces boundary layer thickness."
    desc_ho_en = "The outside film coefficient (h_o) indicates the heat transfer performance between the utility fluid and the vessel outer wall. The structural channel dictates cross-sectional area and fluid velocity, driving the Reynolds number."
    desc_u_en = "The Overall Heat Transfer Coefficient (U) is the final combined thermal transmittance, derived by summing the series resistances (inside/outside convection, fouling, wall conduction). Higher value means better thermal performance."

    desc_hi_ui = "내부 대류 열전달 계수($h_i$)는 반응기 내부 공정 유체의 흐름에 의해 발생하는 열전달 효율을 의미합니다. 교반기의 회전(또는 자연대류)으로 인한 난류가 경계층을 얼마나 얇게 만드느냐를 계산하는 과정입니다." if lang_opt == "ko" else desc_hi_en
    desc_ho_ui = "외부 대류 열전달 계수($h_o$)는 자켓을 흐르는 서비스 유체(냉각/가열 매체)와 반응기 외벽 간의 열전달 성능입니다. 자켓 구조(Half-pipe 등)에 따라 결정되는 유로의 단면적과 속도가 레이놀즈 수(Re) 형성에 직접적인 영향을 줍니다." if lang_opt == "ko" else desc_ho_en
    desc_u_ui = "총괄 열전달 계수($U$)는 내부 유체 대류, 내부 오염(Fouling), 벽면 용접부의 전도 저항, 외부 오염, 외부 대류 저항들을 모두 직렬 저항으로 보아 합산한 최종 열관류율입니다. 이 값이 높을수록 전반적인 열전달 성능이 우수함을 의미합니다." if lang_opt == "ko" else desc_u_en

    st.markdown("### 2.1 Inside Film Coefficient ($h_i$) - Agitation Details")
    st.info(desc_hi_ui)
    hi_calc_html = ""
    if "None" in agit_type:
        st.write(f"**Agitator Type: {agit_type}** | 자연 대류(Natural Convection) 적용 (가정: delta T = 10 K, beta = 0.0002)")
        st.latex(r"Gr = \frac{\rho_p^2 \cdot g \cdot \beta \cdot \Delta T \cdot D_{in}^3}{\mu_p^2} = " + f"{Gr:,.0f}")
        st.latex(r"Pr_p = \frac{C_{p,p} \cdot \mu_p}{k_p} = " + f"{Pr_p:.2f}")
        st.latex(r"Ra = Gr \cdot Pr_p = " + f"{Ra:,.0f}")
        st.latex(r"Nu_i = 0.1 \cdot Ra^{1/3} = \mathbf{" + f"{Nu_p:.1f}" + r"}")
        st.latex(r"h_i = \frac{Nu_i \cdot k_p}{D_{in}} = \mathbf{" + f"{h_i_calc:.1f}" + r" \text{ W/m}^2\text{K}}")
        hi_calc_html = f"Gr = {Gr:,.0f} <br> Pr = {Pr_p:.2f} <br> Ra = {Ra:,.0f} <br> Nu<sub>i</sub> = 0.1 &middot; Ra<sup>1/3</sup> = {Nu_p:.1f} <br> h<sub>i</sub> = {h_i_calc:.1f} W/m&sup2;K"
    else:
        st.latex(r"N = \frac{" + f"{rpm}" + r" \text{ RPM}}{60} = " + f"{N_rps:.3f}" + r" \text{ rps}")
        st.latex(r"Re_a = \frac{\rho_p \cdot N \cdot D_a^2}{\mu_p} = \frac{" + f"{rho_p} \\times {N_rps:.3f} \\times ({d_agit})^2" + r"}{" + f"{mu_p:.4f}" + r"} = \mathbf{" + f"{Re_a:,.0f}" + r"}")
        st.latex(r"Pr_p = \frac{C_{p,p} \cdot \mu_p}{k_p} = \frac{" + f"{cp_p} \\times {mu_p:.4f}" + r"}{" + f"{k_p}" + r"} = \mathbf{" + f"{Pr_p:.2f}" + r"}")
        st.latex(r"Nu_i = " + f"{nu_const}" + r" \cdot (Re_a)^{0.67} \cdot (Pr_p)^{0.33} = " + f"{nu_const}" + r" \cdot (" + f"{Re_a:,.0f}" + r")^{0.67} \cdot (" + f"{Pr_p:.2f}" + r")^{0.33} = \mathbf{" + f"{Nu_p:.1f}" + r"}")
        st.latex(r"h_i = \frac{Nu_i \cdot k_p}{D_{in}} = \frac{" + f"{Nu_p:.1f} \\times {k_p}" + r"}{" + f"{d_in}" + r"} = \mathbf{" + f"{h_i_calc:.1f}" + r" \text{ W/m}^2\text{K}}")
        hi_calc_html = f"Re<sub>a</sub> = {Re_a:,.0f} <br> Pr<sub>p</sub> = {Pr_p:.2f} <br> Nu<sub>i</sub> = {nu_const} &middot; Re<sub>a</sub><sup>0.67</sup> &middot; Pr<sub>p</sub><sup>0.33</sup> = {Nu_p:.1f} <br> h<sub>i</sub> = {h_i_calc:.1f} W/m&sup2;K"
    
    st.divider()
    st.markdown("### 2.2 Outside Film Coefficient ($h_o$) - Jacket Geometry Details")
    st.info(desc_ho_ui)
    h_o_calc, Nu_s, Re_s, v_s, A_cross, De, Pr_s, a_jacket, v_total = calculate_ho_area(
        jacket_type, j_dim, j_pitch, Q_sec, rho_s, mu_s, cp_s, k_s, d_in, wall_thk, tt_len, jacket_coverage, head_type
    )

    ho_calc_html = ""
    if jacket_type == "Half-Pipe":
        st.write(f"**Jacket Type: {jacket_type}** | 반원형 파이프 횡단면 적용")
        st.latex(r"A_c = \frac{\pi \cdot (d_{pipe})^2}{8} = \frac{\pi \cdot (" + f"{j_dim}" + r")^2}{8} = " + f"{A_cross:.5f}" + r" \text{ m}^2")
        st.latex(r"D_e = 0.61 \cdot d_{pipe} = 0.61 \cdot " + f"{j_dim}" + r" = " + f"{De:.4f}" + r" \text{ m}")
        st.latex(r"v_s = \frac{Q_{sec}}{A_c} = \frac{" + f"{Q_sec:.5f}" + r"}{" + f"{A_cross:.5f}" + r"} = " + f"{v_s:.2f}" + r" \text{ m/s}")
        st.latex(r"Re_o = \frac{\rho_s \cdot v_s \cdot D_e}{\mu_s} = \frac{" + f"{rho_s:.1f} \\times {v_s:.2f} \\times {De:.4f}" + r"}{" + f"{mu_s:.4e}" + r"} = \mathbf{" + f"{Re_s:,.0f}" + r"}")
        st.latex(r"Nu_o = 0.023 \cdot (Re_o)^{0.8} \cdot (Pr_s)^{0.4} = \mathbf{" + f"{Nu_s:.1f}" + r"}")
        st.latex(r"h_o = \frac{Nu_o \cdot k_s}{D_e} = \frac{" + f"{Nu_s:.1f} \\times {k_s:.3f}" + r"}{" + f"{De:.4f}" + r"} = \mathbf{" + f"{h_o_calc:.1f}" + r" \text{ W/m}^2\text{K}}")
        ho_calc_html = f"A<sub>c</sub> = {A_cross:.5f} m&sup2; <br> D<sub>e</sub> = {De:.4f} m <br> v<sub>s</sub> = {v_s:.2f} m/s <br> Re<sub>o</sub> = {Re_s:,.0f} <br> Nu<sub>o</sub> = 0.023 &middot; Re<sub>o</sub><sup>0.8</sup> &middot; Pr<sub>s</sub><sup>0.4</sup> = {Nu_s:.1f} <br> h<sub>o</sub> = {h_o_calc:.1f} W/m&sup2;K"
    elif jacket_type == "Conventional (with Baffle)":
        st.write(f"**Jacket Type: {jacket_type}** | Annular Gap 및 Baffle Pitch 적용")
        st.latex(r"A_c = Gap \times Pitch = " + f"{j_dim} \\times {j_pitch}" + r" = " + f"{A_cross:.5f}" + r" \text{ m}^2")
        st.latex(r"D_e = 2 \cdot Gap = 2 \cdot " + f"{j_dim}" + r" = " + f"{De:.4f}" + r" \text{ m}")
        st.latex(r"v_s = \frac{Q_{sec}}{A_c} = \frac{" + f"{Q_sec:.5f}" + r"}{" + f"{A_cross:.5f}" + r"} = " + f"{v_s:.2f}" + r" \text{ m/s}")
        st.latex(r"Re_o = \frac{\rho_s \cdot v_s \cdot D_e}{\mu_s} = \frac{" + f"{rho_s:.1f} \\times {v_s:.2f} \\times {De:.4f}" + r"}{" + f"{mu_s:.4e}" + r"} = \mathbf{" + f"{Re_s:,.0f}" + r"}")
        st.latex(r"Nu_o = 0.027 \cdot (Re_o)^{0.8} \cdot (Pr_s)^{0.33} = \mathbf{" + f"{Nu_s:.1f}" + r"}")
        st.latex(r"h_o = \frac{Nu_o \cdot k_s}{D_e} = \mathbf{" + f"{h_o_calc:.1f}" + r" \text{ W/m}^2\text{K}}")
        ho_calc_html = f"A<sub>c</sub> = {A_cross:.5f} m&sup2; <br> D<sub>e</sub> = {De:.4f} m <br> v<sub>s</sub> = {v_s:.2f} m/s <br> Re<sub>o</sub> = {Re_s:,.0f} <br> Nu<sub>o</sub> = 0.027 &middot; Re<sub>o</sub><sup>0.8</sup> &middot; Pr<sub>s</sub><sup>0.33</sup> = {Nu_s:.1f} <br> h<sub>o</sub> = {h_o_calc:.1f} W/m&sup2;K"
    else:
        st.latex(r"h_o \approx \mathbf{1500.0 \text{ W/m}^2\text{K}} \text{ (Vendor Empirical Data)}")
        ho_calc_html = f"h<sub>o</sub> &approx; 1500.0 W/m&sup2;K (Vendor Empirical Data)"

    st.divider()
    st.markdown("### 2.3 Overall Heat Transfer Coefficient ($U$)")
    st.info(desc_u_ui)
    R_i = 1 / h_i_calc if h_i_calc > 0 else 0
    R_w = wall_thk / k_wall
    R_o = 1 / h_o_calc if h_o_calc > 0 else 0
    R_total = R_i + r_fi + R_w + r_fo + R_o
    U_calc = 1 / R_total if R_total > 0 else 0
    
    st.latex(r"R_{total} = \frac{1}{h_i} + R_{fi} + \frac{t}{k_w} + R_{fo} + \frac{1}{h_o}")
    st.latex(r"R_{total} = " + f"{R_i:.5f} + {r_fi:.5f} + {R_w:.5f} + {r_fo:.5f} + {R_o:.5f} = {R_total:.5f}" + r" \text{ m}^2\text{K/W}")
    st.latex(r"U = \frac{1}{R_{total}} = \mathbf{" + f"{U_calc:.1f}" + r" \text{ W/m}^2\text{K}}")
    u_calc_html = f"R<sub>total</sub> = 1/h<sub>i</sub> + R<sub>fi</sub> + t/k<sub>w</sub> + R<sub>fo</sub> + 1/h<sub>o</sub> = {R_total:.5f} m&sup2;K/W <br> U = 1/R<sub>total</sub> = {U_calc:.1f} W/m&sup2;K"


with tab3:
    st.header(t["tab3"])
    M_cp_total = v_total * rho_p * cp_p 
    P_agit_watts = AGITATOR_DB[agit_type]["Np"] * rho_p * (N_rps**3) * (d_agit**5)
    Q_rxn_W = q_rxn_kw * 1000.0 if has_rxn else 0.0

    C_min = Q_sec * rho_s * cp_s 
    if C_min > 0:
        NTU = (U_calc * a_jacket) / C_min
        epsilon = 1.0 - math.exp(-NTU)
    else:
        NTU = 0.0
        epsilon = 0.0
    
    effective_UA = epsilon * C_min

    t_span = np.linspace(0, time_limit * 60, 500)
    T_solution = odeint(jacket_ode, t_initial, t_span, args=(effective_UA, t_service, M_cp_total, P_agit_watts, Q_rxn_W))
    T_profile = T_solution.flatten()
    time_min = t_span / 60

    try:
        op_mode = determine_operation_mode(t_initial, t_service, t_target)
    except ValueError as exc:
        st.error(f"⚠️ {exc}")
        st.stop()

    time_to_target = find_time_to_target(T_profile, time_min, t_target, op_mode)
    
    if time_to_target is not None:
        st.success(f"✅ 목표 온도 도달 예상 시간: **{time_to_target:.1f} min**")
    else:
        st.error(f"❌ 설정된 시간({time_limit}min) 내에 목표 온도에 도달하지 못합니다.")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time_min, y=T_profile, line=dict(color='#ff4b4b', width=3), name='Temp Profile'))
    fig.add_hline(y=t_target, line_dash="dash", line_color="#00cc96", annotation_text="Target Temp")
    if time_to_target is not None:
        fig.add_vline(x=time_to_target, line_dash="dot", line_color="#3498DB", annotation_text=f"Reached: {time_to_target:.1f} min", annotation_position="bottom right")
    fig.update_layout(xaxis_title='Time (min)', yaxis_title='Temp (°C)', height=400, template="plotly_white", margin=dict(l=20, r=20, t=30, b=20))
    with st.container(border=True):
        st.plotly_chart(fig, use_container_width=True)

    try:
        import matplotlib.pyplot as plt
        import io
        
        fig_mpl, ax = plt.subplots(figsize=(8, 4))
        ax.plot(time_min, T_profile, color='#ff4b4b', linewidth=2.5, label='Temp Profile')
        ax.axhline(y=t_target, color='#00cc96', linestyle='--', linewidth=2, label='Target Temp')
        
        if time_to_target is not None:
            ax.axvline(x=time_to_target, color='#3498DB', linestyle=':', label=f'Target Reached ({time_to_target:.1f} m)')
            ax.plot(time_to_target, t_target, 'ko', markersize=5)
            ax.text(time_to_target + (time_limit * 0.02), t_target + (t_target * 0.02), f"{time_to_target:.1f} min", color='#3498DB', fontweight='bold')
            
        ax.set_xlabel('Time (min)')
        ax.set_ylabel('Temp (°C)')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend()
        fig_mpl.tight_layout()
        
        buf = io.BytesIO()
        fig_mpl.savefig(buf, format='png', dpi=150)
        plt.close(fig_mpl)
        
        buf.seek(0)
        fig_b64 = base64.b64encode(buf.read()).decode('utf-8')
        fig_img_html = f'<img src="data:image/png;base64,{fig_b64}" style="max-width:100%; border: 1px solid #ddd; border-radius:8px;">'
    except Exception as e:
        fig_img_html = f"<div style='border:1px dashed #ccc; padding:20px; text-align:center; color:#e00;'>[Simulation Chart image generation failed for PDF: {str(e)}]</div>"

    st.divider()
    
    ctx = {
        "op_mode": op_mode, "service_name": service_name, "tank_no": tank_no, "jacket_no": jacket_no,
        "v_total": v_total, "a_jacket": a_jacket, "wall_mat": wall_mat, "wall_thk": wall_thk*1000,
        "fluid_type": service_fluid_type, "t_service": t_service, "jacket_type": jacket_type,
        "agit_type": agit_type, "rpm": rpm, "q_rxn": q_rxn_kw, "hi": h_i_calc, "ho": h_o_calc,
        "U": U_calc, "epsilon": epsilon, "NTU": NTU, "t_init": t_initial, "t_target": t_target,
        "tt_target": round(time_to_target, 1) if time_to_target else "N/A",
        "hi_calc_html": hi_calc_html, "ho_calc_html": ho_calc_html, "u_calc_html": u_calc_html,
        "fig_img_html": fig_img_html, "desc_hi": desc_hi_en, "desc_ho": desc_ho_en, "desc_u": desc_u_en
    }
    
    html_report = generate_html(ctx)
    pdf_bytes = create_pdf(html_report)
    
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(label=t["download_html"], data=html_report, file_name=f"Report_{tank_no}_{jacket_no}.html", mime="text/html", type="primary", use_container_width=True)
    with col_dl2:
        if pdf_bytes:
            st.download_button(label=t["download_pdf"], data=pdf_bytes, file_name=f"Report_{tank_no}_{jacket_no}.pdf", mime="application/pdf", type="primary", use_container_width=True)
        else:
            st.error("Error generating PDF.")
