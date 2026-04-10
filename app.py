import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.integrate import odeint
import math
import json
import zlib
import base64
from datetime import datetime

st.set_page_config(page_title="Jacketed Vessel Engineering", layout="wide")
st.title("🏭 Jacketed Vessel Process Design & Simulation")

# ==========================================
# 0. 데이터베이스 & 상태 관리 로직
# ==========================================
MATERIAL_K = {
    "Carbon Steel (SA-516)": 45.0,
    "Stainless Steel 304": 16.0,
    "Stainless Steel 316": 16.3,
    "Titanium": 17.0,
    "Glass-Lined (Steel base)": 1.2 
}

AGITATOR_DB = {
    "Pitched Blade (4-Blade 45°)": {
        "Np": 1.27, "desc": "혼합과 열전달에 두루 쓰이는 표준형. 축 방향(Axial) 흐름을 형성합니다.",
        "svg": """<svg viewBox="0 0 100 100" style="height:100px; background-color:#f8f9fa; border-radius:8px;"><path d="M 50 10 V 90" stroke="#2E4053" stroke-width="6"/><path d="M 30 40 L 70 60 M 30 60 L 70 40" stroke="#E74C3C" stroke-width="8" stroke-linecap="round"/></svg>"""
    },
    "Rushton Turbine (6-Blade Flat)": {
        "Np": 5.0, "desc": "강력한 전단력(High Shear)과 방사형(Radial) 흐름. 기체 분산에 적합하나 동력 소모가 큽니다.",
        "svg": """<svg viewBox="0 0 100 100" style="height:100px; background-color:#f8f9fa; border-radius:8px;"><rect x="40" y="45" width="20" height="10" fill="#2E4053"/><path d="M 50 10 V 90 M 20 50 H 80 M 20 35 V 65 M 80 35 V 65" stroke="#E74C3C" stroke-width="6"/></svg>"""
    },
    "Anchor (Nominal)": {
        "Np": 0.4, "desc": "고점도(High Viscosity) 유체의 벽면 고착을 막고 열전달을 촉진하는 데 필수적입니다.",
        "svg": """<svg viewBox="0 0 100 100" style="height:100px; background-color:#f8f9fa; border-radius:8px;"><path d="M 50 10 V 85 M 20 40 V 70 A 30 30 0 0 0 80 70 V 40" stroke="#E74C3C" stroke-width="8" fill="none" stroke-linecap="round"/></svg>"""
    },
    "Flat Paddle (2-Blade)": {
        "Np": 1.7, "desc": "단순한 구조의 저속 교반용. 방사형 흐름을 만듭니다.",
        "svg": """<svg viewBox="0 0 100 100" style="height:100px; background-color:#f8f9fa; border-radius:8px;"><rect x="30" y="40" width="40" height="20" fill="#E74C3C"/><path d="M 50 10 V 90" stroke="#2E4053" stroke-width="6"/></svg>"""
    },
    "Marine Propeller (3-Blade)": {
        "Np": 0.35, "desc": "저점도 유체의 고속 교반 및 고효율 축방향 순환에 유리합니다.",
        "svg": """<svg viewBox="0 0 100 100" style="height:100px; background-color:#f8f9fa; border-radius:8px;"><path d="M 50 10 V 90" stroke="#2E4053" stroke-width="6"/><ellipse cx="50" cy="50" rx="30" ry="8" transform="rotate(30 50 50)" fill="#E74C3C"/><ellipse cx="50" cy="50" rx="30" ry="8" transform="rotate(-30 50 50)" fill="#E74C3C"/></svg>"""
    },
    "Retreat Curve (Glass-Lined)": {
        "Np": 0.35, "desc": "Glass-Lined 반응기 전용. 날개가 휘어져 있어 코팅 손상을 방지하며 부드럽게 교반합니다.",
        "svg": """<svg viewBox="0 0 100 100" style="height:100px; background-color:#f8f9fa; border-radius:8px;"><path d="M 50 10 V 90" stroke="#2E4053" stroke-width="6"/><path d="M 50 80 Q 20 80 20 50" stroke="#E74C3C" stroke-width="8" fill="none"/><path d="M 50 80 Q 80 80 80 50" stroke="#E74C3C" stroke-width="8" fill="none"/></svg>"""
    }
}

def encode_state(state_dict):
    json_str = json.dumps(state_dict)
    compressed = zlib.compress(json_str.encode('utf-8'))
    return base64.urlsafe_b64encode(compressed).decode('utf-8')

def decode_state(b64_str):
    try:
        compressed = base64.urlsafe_b64decode(b64_str.encode('utf-8'))
        return json.loads(zlib.decompress(compressed).decode('utf-8'))
    except:
        return {}

query_params = st.query_params
init = decode_state(query_params.get("data", "")) if "data" in query_params else {}

# ==========================================
# 1. 사이드바 (정보 및 상태 저장)
# ==========================================
with st.sidebar:
    st.header("📌 Identifications")
    tank_no = st.text_input("Vessel Tag No.", value=init.get("tank_no", "R-1001"))
    jacket_no = st.text_input("Jacket Tag No.", value=init.get("jacket_no", "J-1001"))
    service_name = st.text_input("Service Name", value=init.get("service_name", "Polymerization"))
    
    st.divider()
    st.header("⏱️ Simulation Target")
    t_target = st.number_input("Target Temp (°C)", value=init.get("t_target", 80.0))
    time_limit = st.number_input("Sim. Time (min)", value=init.get("time_limit", 120), min_value=10)
    
    st.divider()
    st.header("💾 State Management")
    if st.button("Generate Share Link", type="primary", use_container_width=True):
        st.session_state["save_trigger"] = True

# ==========================================
# 2. 메인 화면 - 탭 1: 상세 입력
# ==========================================
tab1, tab2, tab3 = st.tabs(["⚙️ 1. Design Inputs", "🧮 2. Engineering Calcs (Detailed)", "📈 3. Simulation & Report"])

with tab1:
    st.header("Step 1: Detailed Design Parameters")
    col_geom, col_agit, col_fluid = st.columns(3)
    
    with col_geom:
        st.subheader("Geometry & Material")
        d_in = st.number_input("Vessel ID (mm)", value=init.get("d_in", 2000.0), step=100.0) / 1000.0
        tt_len = st.number_input("T/T Length (mm)", value=init.get("tt_len", 3000.0), step=100.0) / 1000.0
        head_type = st.selectbox("Bottom Head Type", ["2:1 Ellipsoidal", "Hemispherical", "Torispherical"], index=["2:1 Ellipsoidal", "Hemispherical", "Torispherical"].index(init.get("head_type", "2:1 Ellipsoidal")))
        wall_mat = st.selectbox("Wall Material", list(MATERIAL_K.keys()), index=list(MATERIAL_K.keys()).index(init.get("wall_mat", "Stainless Steel 304")))
        wall_thk = st.number_input("Wall Thickness (mm)", value=init.get("wall_thk", 12.0)) / 1000.0
        jacket_coverage = st.number_input("Jacket Straight Coverage (%)", value=init.get("jacket_coverage", 80.0)) / 100.0
        
        st.divider()
        jacket_type = st.selectbox("Jacket Type", ["Half-Pipe", "Conventional (with Baffle)", "Dimple"], index=["Half-Pipe", "Conventional (with Baffle)", "Dimple"].index(init.get("jacket_type", "Half-Pipe")))
        if jacket_type == "Half-Pipe":
            j_dim = st.number_input("Pipe ID (mm, 보통 3~4인치)", value=init.get("j_dim", 80.0)) / 1000.0
            j_pitch = 0.0
        elif jacket_type == "Conventional (with Baffle)":
            j_dim = st.number_input("Annular Gap (mm)", value=init.get("j_dim", 50.0)) / 1000.0
            j_pitch = st.number_input("Baffle Pitch (mm)", value=init.get("j_pitch", 200.0)) / 1000.0
        else:
            j_dim, j_pitch = 0.0, 0.0

    with col_agit:
        st.subheader("Agitator Specs")
        agit_type = st.selectbox("Impeller Type", list(AGITATOR_DB.keys()), index=list(AGITATOR_DB.keys()).index(init.get("agit_type", "Pitched Blade (4-Blade 45°)")))
        agit_info = AGITATOR_DB[agit_type]
        st.markdown(agit_info["svg"], unsafe_allow_html=True)
        st.caption(f"**Power Number ($N_p$):** {agit_info['Np']}")
        rpm = st.number_input("Agitator Speed (RPM)", value=init.get("rpm", 60.0))
        d_agit = st.number_input("Impeller Diameter (mm)", value=init.get("d_agit", 800.0)) / 1000.0

    with col_fluid:
        st.subheader("Fluid Properties")
        st.markdown("**Process Fluid (Inside)**")
        rho_p = st.number_input("Density (kg/m³)", value=init.get("rho_p", 1000.0))
        cp_p = st.number_input("Specific Heat (J/kg·K)", value=init.get("cp_p", 4184.0))
        mu_cp = st.number_input("Viscosity (cP)", value=init.get("mu_cp", 5.0), format="%.2f") 
        k_p = st.number_input("Thermal Cond. (W/m·K)", value=init.get("k_p", 0.6))
        t_initial = st.number_input("Initial Temp (°C)", value=init.get("t_initial", 20.0))

        st.markdown("**Service Fluid (Jacket - Water assumed for properties)**")
        q_service = st.number_input("Service Flow Rate (m³/h)", value=init.get("q_service", 15.0))
        t_service = st.number_input("Service Temp (°C)", value=init.get("t_service", 150.0))

if st.session_state.get("save_trigger"):
    current_state = {
        "tank_no": tank_no, "jacket_no": jacket_no, "service_name": service_name, "t_target": t_target, "time_limit": time_limit,
        "d_in": d_in*1000, "tt_len": tt_len*1000, "head_type": head_type, "wall_mat": wall_mat, "wall_thk": wall_thk*1000, "jacket_coverage": jacket_coverage*100,
        "jacket_type": jacket_type, "j_dim": j_dim*1000, "j_pitch": j_pitch*1000, "agit_type": agit_type, "rpm": rpm, "d_agit": d_agit*1000,
        "rho_p": rho_p, "cp_p": cp_p, "mu_cp": mu_cp, "k_p": k_p, "t_initial": t_initial, "q_service": q_service, "t_service": t_service
    }
    st.query_params["data"] = encode_state(current_state)
    st.session_state["save_trigger"] = False
    st.sidebar.success("✅ Link Updated! Copy the URL.")

# ==========================================
# 3. 메인 화면 - 탭 2: 초정밀 계산 로직
# ==========================================
with tab2:
    st.header("Step 2: Exhaustive Heat Transfer Calculation")
    
    k_wall = MATERIAL_K[wall_mat]
    mu_p = mu_cp * 0.001 # Pa.s
    N_rps = rpm / 60.0
    Q_sec = q_service / 3600.0 
    rho_s, mu_s, cp_s, k_s = 998.0, 0.001, 4184.0, 0.6 # Service Fluid Assumed (Water)
    Pr_s = (cp_s * mu_s) / k_s
    
    st.markdown("### 2.1 Inside Film Coefficient ($h_i$) - Agitation Details")
    st.write("입력된 유체 물성치 및 교반기 제원을 바탕으로 강제 대류에 의한 $h_i$를 도출합니다.")
    
    Re_agit = (rho_p * N_rps * (d_agit**2)) / mu_p
    Pr_p = (cp_p * mu_p) / k_p
    Nu_p = 0.53 * (Re_agit**0.67) * (Pr_p**0.33) if Re_agit > 0 else 0
    h_i_calc = (Nu_p * k_p) / d_in if d_in > 0 else 0
    
    # 상세 변수 대입 과정 수식화
    st.latex(r"N = \frac{" + f"{rpm}" + r" \text{ RPM}}{60} = " + f"{N_rps:.3f}" + r" \text{ rps}")
    st.latex(r"Re_a = \frac{\rho_p \cdot N \cdot D_a^2}{\mu_p} = \frac{" + f"{rho_p} \\times {N_rps:.3f} \\times ({d_agit})^2" + r"}{" + f"{mu_p:.4f}" + r"} = \mathbf{" + f"{Re_agit:,.0f}" + r"}")
    st.latex(r"Pr_p = \frac{C_{p,p} \cdot \mu_p}{k_p} = \frac{" + f"{cp_p} \\times {mu_p:.4f}" + r"}{" + f"{k_p}" + r"} = \mathbf{" + f"{Pr_p:.2f}" + r"}")
    st.latex(r"Nu_i = 0.53 \cdot (Re_a)^{0.67} \cdot (Pr_p)^{0.33} = 0.53 \cdot (" + f"{Re_agit:,.0f}" + r")^{0.67} \cdot (" + f"{Pr_p:.2f}" + r")^{0.33} = \mathbf{" + f"{Nu_p:.1f}" + r"}")
    st.latex(r"h_i = \frac{Nu_i \cdot k_p}{D_{in}} = \frac{" + f"{Nu_p:.1f} \\times {k_p}" + r"}{" + f"{d_in}" + r"} = \mathbf{" + f"{h_i_calc:.1f}" + r" \text{ W/m}^2\text{K}}")
    
    st.divider()
    st.markdown("### 2.2 Outside Film Coefficient ($h_o$) - Jacket Geometry Details")
    
    if jacket_type == "Half-Pipe":
        De = 0.61 * j_dim
        A_cross = (math.pi * j_dim**2) / 8
        v_s = Q_sec / A_cross if A_cross > 0 else 0
        Re_s = (rho_s * v_s * De) / mu_s
        Nu_s = 0.023 * (Re_s**0.8) * (Pr_s**0.4)
        h_o_calc = (Nu_s * k_s) / De if De > 0 else 0
        
        st.write(f"**Jacket Type: {jacket_type}** | 반원형 파이프 횡단면 적용")
        st.latex(r"A_c = \frac{\pi \cdot (d_{pipe})^2}{8} = \frac{\pi \cdot (" + f"{j_dim}" + r")^2}{8} = " + f"{A_cross:.5f}" + r" \text{ m}^2")
        st.latex(r"D_e = 0.61 \cdot d_{pipe} = 0.61 \cdot " + f"{j_dim}" + r" = " + f"{De:.4f}" + r" \text{ m}")
        st.latex(r"v_s = \frac{Q_{sec}}{A_c} = \frac{" + f"{Q_sec:.5f}" + r"}{" + f"{A_cross:.5f}" + r"} = " + f"{v_s:.2f}" + r" \text{ m/s}")
        st.latex(r"Re_o = \frac{\rho_s \cdot v_s \cdot D_e}{\mu_s} = \frac{" + f"{rho_s} \\times {v_s:.2f} \\times {De:.4f}" + r"}{" + f"{mu_s}" + r"} = \mathbf{" + f"{Re_s:,.0f}" + r"}")
        st.latex(r"Nu_o = 0.023 \cdot (Re_o)^{0.8} \cdot (Pr_s)^{0.4} = \mathbf{" + f"{Nu_s:.1f}" + r"}")
        st.latex(r"h_o = \frac{Nu_o \cdot k_s}{D_e} = \frac{" + f"{Nu_s:.1f} \\times {k_s}" + r"}{" + f"{De:.4f}" + r"} = \mathbf{" + f"{h_o_calc:.1f}" + r" \text{ W/m}^2\text{K}}")

    elif jacket_type == "Conventional (with Baffle)":
        De = 2 * j_dim
        A_cross = j_dim * j_pitch
        v_s = Q_sec / A_cross if A_cross > 0 else 0
        Re_s = (rho_s * v_s * De) / mu_s
        Nu_s = 0.027 * (Re_s**0.8) * (Pr_s**0.33)
        h_o_calc = (Nu_s * k_s) / De if De > 0 else 0
        
        st.write(f"**Jacket Type: {jacket_type}** | Annular Gap 및 Baffle Pitch 적용")
        st.latex(r"A_c = Gap \times Pitch = " + f"{j_dim} \\times {j_pitch}" + r" = " + f"{A_cross:.5f}" + r" \text{ m}^2")
        st.latex(r"D_e = 2 \cdot Gap = 2 \cdot " + f"{j_dim}" + r" = " + f"{De:.4f}" + r" \text{ m}")
        st.latex(r"v_s = \frac{Q_{sec}}{A_c} = \frac{" + f"{Q_sec:.5f}" + r"}{" + f"{A_cross:.5f}" + r"} = " + f"{v_s:.2f}" + r" \text{ m/s}")
        st.latex(r"Re_o = \frac{\rho_s \cdot v_s \cdot D_e}{\mu_s} = \frac{" + f"{rho_s} \\times {v_s:.2f} \\times {De:.4f}" + r"}{" + f"{mu_s}" + r"} = \mathbf{" + f"{Re_s:,.0f}" + r"}")
        st.latex(r"Nu_o = 0.027 \cdot (Re_o)^{0.8} \cdot (Pr_s)^{0.33} = \mathbf{" + f"{Nu_s:.1f}" + r"}")
        st.latex(r"h_o = \frac{Nu_o \cdot k_s}{D_e} = \mathbf{" + f"{h_o_calc:.1f}" + r" \text{ W/m}^2\text{K}}")
    else:
        h_o_calc = 1500.0
        st.latex(r"h_o \approx \mathbf{1500.0 \text{ W/m}^2\text{K}} \text{ (Vendor Empirical Data)}")

    st.divider()
    st.markdown("### 2.3 Overall Heat Transfer Coefficient ($U$)")
    
    R_i = 1 / h_i_calc if h_i_calc > 0 else 0
    R_fi = 0.0002
    R_w = wall_thk / k_wall
    R_fo = 0.0002
    R_o = 1 / h_o_calc if h_o_calc > 0 else 0
    R_total = R_i + R_fi + R_w + R_fo + R_o
    U_calc = 1 / R_total if R_total > 0 else 0
    
    st.latex(r"R_{total} = \frac{1}{h_i} + R_{fi} + \frac{t}{k_w} + R_{fo} + \frac{1}{h_o}")
    st.latex(r"R_{total} = " + f"{R_i:.5f} + {R_fi:.5f} + {R_w:.5f} + {R_fo:.5f} + {R_o:.5f} = {R_total:.5f}" + r" \text{ m}^2\text{K/W}")
    st.latex(r"U = \frac{1}{R_{total}} = \mathbf{" + f"{U_calc:.1f}" + r" \text{ W/m}^2\text{K}}")

# ==========================================
# 4. 메인 화면 - 탭 3: 시뮬레이션 및 리포트 (복원 완)
# ==========================================
with tab3:
    st.header("Step 3: Dynamic Simulation & Report Generation")
    
    v_cyl = (math.pi / 4) * (d_in**2) * tt_len
    if head_type == "2:1 Ellipsoidal":
        v_head = (math.pi / 24) * (d_in**3)
    elif head_type == "Hemispherical":
        v_head = (math.pi / 12) * (d_in**3)
    else:
        v_head = 0.08 * (d_in**3)
        
    v_total = v_cyl + v_head
    a_jacket = (math.pi * d_in * tt_len * jacket_coverage) + (1.084 * (d_in**2)) 
    M_cp_total = v_total * rho_p * cp_p 
    P_agit_watts = AGITATOR_DB[agit_type]["Np"] * rho_p * (N_rps**3) * (d_agit**5)
    
    def jacket_ode(T, t, U, A, T_s, M_cp, Q_a):
        return (U * A * (T_s - T) + Q_a) / M_cp

    t_span = np.linspace(0, time_limit * 60, 500)
    T_solution = odeint(jacket_ode, t_initial, t_span, args=(U_calc, a_jacket, t_service, M_cp_total, P_agit_watts))
    T_profile = T_solution.flatten()
    time_min = t_span / 60
    
    target_idx = np.where(T_profile >= t_target)[0] if t_service > t_initial else np.where(T_profile <= t_target)[0]
    time_to_target = time_min[target_idx[0]] if len(target_idx) > 0 else None
    
    if time_to_target is not None:
        st.success(f"✅ 목표 온도({t_target}°C) 도달 예상 시간: **{time_to_target:.1f} 분**")
    else:
        st.error(f"❌ 설정된 시간({time_limit}분) 내에 목표 온도에 도달하지 못합니다.")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time_min, y=T_profile, line=dict(color='firebrick', width=3), name='Temp Profile'))
    fig.add_hline(y=t_target, line_dash="dash", line_color="green", annotation_text="Target Temp")
    fig.update_layout(xaxis_title='Time (min)', yaxis_title='Temp (°C)', height=400, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    # --- HTML Report Generation Logic ---
    st.divider()
    st.subheader("📄 Engineering Report Export")
    
    # HTML 문자열 생성
    html_report = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Calculation Report: {tank_no}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 30px; color: #333; }}
            h1 {{ border-bottom: 2px solid #2E4053; color: #2E4053; }}
            h2 {{ color: #E74C3C; margin-top: 30px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background-color: #f8f9fa; width: 30%; }}
        </style>
    </head>
    <body>
        <h1>Jacketed Vessel Thermal Calculation Report</h1>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | <strong>Service:</strong> {service_name}</p>
        
        <h2>1. Identifications</h2>
        <table>
            <tr><th>Vessel Tag No.</th><td>{tank_no}</td><th>Jacket Tag No.</th><td>{jacket_no}</td></tr>
            <tr><th>Vessel Volume</th><td>{v_total:.2f} m³</td><th>Heat Transfer Area</th><td>{a_jacket:.2f} m²</td></tr>
            <tr><th>Material</th><td>{wall_mat}</td><th>Wall Thickness</th><td>{wall_thk*1000:.1f} mm</td></tr>
        </table>

        <h2>2. Heat Transfer Results</h2>
        <table>
            <tr><th>Agitator Type</th><td>{agit_type} ({rpm} RPM)</td><th>Jacket Type</th><td>{jacket_type}</td></tr>
            <tr><th>Inside Coefficient (h_i)</th><td>{h_i_calc:.1f} W/m²K</td><th>Outside Coefficient (h_o)</th><td>{h_o_calc:.1f} W/m²K</td></tr>
            <tr><th>Calculated U-Value</th><td colspan="3" style="font-weight:bold; font-size:1.2em; color:#2E4053;">{U_calc:.1f} W/m²K</td></tr>
        </table>
        
        <h2>3. Dynamic Simulation Summary</h2>
        <table>
            <tr><th>Initial Temp</th><td>{t_initial} °C</td><th>Service Temp</th><td>{t_service} °C</td></tr>
            <tr><th>Target Temp</th><td>{t_target} °C</td><th>Estimated Time to Target</th><td><strong style="color:green;">{time_to_target if time_to_target else 'N/A'} min</strong></td></tr>
        </table>
    </body>
    </html>
    """
    
    st.download_button(
        label="📥 Download Detailed HTML Report",
        data=html_report,
        file_name=f"Report_{tank_no}_{jacket_no}.html",
        mime="text/html",
        type="primary"
    )
