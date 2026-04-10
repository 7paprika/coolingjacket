import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.integrate import odeint
import math
import json
import zlib
import base64

# ==========================================
# 0. 데이터베이스 & 상태 관리 로직
# ==========================================
# 재질별 열전도도 (W/m·K)
MATERIAL_K = {
    "Carbon Steel (SA-516)": 45.0,
    "Stainless Steel 304": 16.0,
    "Stainless Steel 316": 16.3,
    "Titanium": 17.0,
    "Glass-Lined (Steel base)": 1.2 
}

# 임펠러 종류별 난류 기준 Power Number (Np)
AGITATOR_NP = {
    "Rushton Turbine (6-Blade Flat)": 5.0,
    "Flat Paddle (2-Blade)": 1.7,
    "Pitched Blade (4-Blade 45°)": 1.27,
    "Anchor (Nominal)": 0.4,
    "Marine Propeller (3-Blade)": 0.35,
    "Retreat Curve (Glass-Lined)": 0.35
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

st.set_page_config(page_title="Jacketed Vessel Engineering", layout="wide")
st.title("🏭 Jacketed Vessel Process Design & Simulation")

# URL 파라미터 로드
query_params = st.query_params
init = decode_state(query_params.get("data", "")) if "data" in query_params else {}

# ==========================================
# 1. 사이드바: 주요 메타데이터 & 상태 저장
# ==========================================
with st.sidebar:
    st.header("📌 Identifications")
    tank_no = st.text_input("Vessel Tag No.", value=init.get("tank_no", "R-1001"))
    jacket_no = st.text_input("Jacket Tag No.", value=init.get("jacket_no", "J-1001"))
    service_name = st.text_input("Service Name", value=init.get("service_name", "Polymerization Reactor"))
    
    st.divider()
    st.header("⏱️ Simulation Target")
    t_target = st.number_input("Target Temp (°C)", value=init.get("t_target", 80.0))
    time_limit = st.number_input("Sim. Time (min)", value=init.get("time_limit", 120), min_value=10)
    
    st.divider()
    st.header("💾 State Management")
    if st.button("Generate Share Link", type="primary", use_container_width=True):
        # 현재 세션의 모든 입력을 긁어모으기 (하단에서 state_to_save 딕셔너리로 정의)
        st.session_state["save_trigger"] = True

# ==========================================
# 2. 메인 화면 탭 구성 (Inputs)
# ==========================================
tab1, tab2, tab3 = st.tabs(["⚙️ 1. Design Inputs", "🧮 2. Engineering Calcs", "📈 3. Simulation & Report"])

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
        
    with col_agit:
        st.subheader("Agitator Specs")
        agit_type = st.selectbox("Impeller Type", list(AGITATOR_NP.keys()), index=list(AGITATOR_NP.keys()).index(init.get("agit_type", "Pitched Blade (4-Blade 45°)")))
        rpm = st.number_input("Agitator Speed (RPM)", value=init.get("rpm", 60.0))
        d_agit = st.number_input("Impeller Diameter (mm)", value=init.get("d_agit", 800.0)) / 1000.0

    with col_fluid:
        st.subheader("Fluid Properties")
        st.markdown("**Process Fluid (Inside)**")
        rho_p = st.number_input("Density (kg/m³)", value=init.get("rho_p", 1000.0))
        cp_p = st.number_input("Specific Heat (J/kg·K)", value=init.get("cp_p", 4184.0))
        mu_cp = st.number_input("Viscosity (cP)", value=init.get("mu_cp", 1.0), format="%.2f") 
        k_p = st.number_input("Thermal Cond. (W/m·K)", value=init.get("k_p", 0.6))
        t_initial = st.number_input("Initial Temp (°C)", value=init.get("t_initial", 20.0))

        st.markdown("**Service Fluid (Jacket)**")
        t_service = st.number_input("Service Temp (°C)", value=init.get("t_service", 150.0))
        h_o_input = st.number_input("Est. Jacket h_o (W/m²·K)", value=init.get("h_o_input", 1500.0))

# --- Save State Trigger Logic ---
if st.session_state.get("save_trigger"):
    current_state = {
        "tank_no": tank_no, "jacket_no": jacket_no, "service_name": service_name,
        "t_target": t_target, "time_limit": time_limit,
        "d_in": d_in*1000, "tt_len": tt_len*1000, "head_type": head_type, "wall_mat": wall_mat, "wall_thk": wall_thk*1000, "jacket_coverage": jacket_coverage*100,
        "agit_type": agit_type, "rpm": rpm, "d_agit": d_agit*1000,
        "rho_p": rho_p, "cp_p": cp_p, "mu_cp": mu_cp, "k_p": k_p, "t_initial": t_initial,
        "t_service": t_service, "h_o_input": h_o_input
    }
    st.query_params["data"] = encode_state(current_state)
    st.session_state["save_trigger"] = False
    st.sidebar.success("✅ Link Updated! Copy the URL.")

# ==========================================
# 3. 메인 화면 탭 구성 (Calculations)
# ==========================================
with tab2:
    st.header("Step 2: Engineering Calculations")
    
    # 단위 변환 및 데이터 맵핑
    k_wall = MATERIAL_K[wall_mat]
    Np = AGITATOR_NP[agit_type]
    mu_p = mu_cp * 0.001  # cP -> Pa·s (kg/m·s) 변환
    N_rps = rpm / 60.0
    
    # 2.1 Geometry Calculations
    v_cyl = (math.pi / 4) * (d_in**2) * tt_len
    a_cyl = math.pi * d_in * tt_len
    
    if head_type == "2:1 Ellipsoidal":
        v_head = (math.pi / 24) * (d_in**3)
        a_head = 1.084 * (d_in**2)
    elif head_type == "Hemispherical":
        v_head = (math.pi / 12) * (d_in**3)
        a_head = (math.pi / 2) * (d_in**2)
    else: # Torispherical
        v_head = 0.08 * (d_in**3)
        a_head = 0.93 * (d_in**2)
        
    v_total = v_cyl + v_head
    a_jacket = (a_cyl * jacket_coverage) + a_head
    
    # 2.2 Agitation Power & Dimensionless Numbers
    Re_agit = (rho_p * N_rps * (d_agit**2)) / mu_p
    Pr_p = (cp_p * mu_p) / k_p
    
    # 실제 유체 전달 동력 (Agitation Power) 계산
    P_agit_watts = Np * rho_p * (N_rps**3) * (d_agit**5)
    
    # Nusselt correlation (범용 식 적용: Nu = 0.53 * Re^0.67 * Pr^0.33)
    Nu_p = 0.53 * (Re_agit**0.67) * (Pr_p**0.33) if Re_agit > 0 else 0
    h_i_calc = (Nu_p * k_p) / d_in if d_in > 0 else 0
    
    # 2.3 Overall Heat Transfer Coefficient (U)
    foul_i = 0.0002
    foul_o = 0.0002
    R_total = (1/h_i_calc) + foul_i + (wall_thk/k_wall) + foul_o + (1/h_o_input)
    U_calc = 1 / R_total
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("📐 **Geometry & Material**")
        st.write(f"- **Volume:** {v_total:.2f} m³")
        st.write(f"- **Jacket Area:** {a_jacket:.2f} m²")
        st.write(f"- **Wall Cond. ($k$):** {k_wall} W/m·K")
    with c2:
        st.success("🔬 **Fluid Dynamics**")
        st.write(f"- **Power No. ($N_p$):** {Np}")
        st.write(f"- **Reynolds No.:** {Re_agit:,.0f}")
        st.write(f"- **Agit. Power:** {P_agit_watts/1000:.2f} kW")
    with c3:
        st.warning("🌡️ **Heat Transfer Coeff.**")
        st.write(f"- **Inside ($h_i$):** {h_i_calc:.1f} W/m²·K")
        st.write(f"- **Outside ($h_o$):** {h_o_input:.1f} W/m²·K")
        st.write(f"- **Overall ($U$):** **{U_calc:.1f} W/m²·K**")

# ==========================================
# 4. 메인 화면 탭 구성 (Simulation)
# ==========================================
with tab3:
    st.header("Step 3: Dynamic Simulation & Report")
    
    M_cp_total = v_total * rho_p * cp_p # J/K
    
    def jacket_heating_ode(T, t, U, A, T_service, M_cp, Q_agit):
        Q_in = U * A * (T_service - T)
        dTdt = (Q_in + Q_agit) / M_cp
        return dTdt

    t_span = np.linspace(0, time_limit * 60, 500)
    T_solution = odeint(jacket_heating_ode, t_initial, t_span, args=(U_calc, a_jacket, t_service, M_cp_total, P_agit_watts))
    T_profile = T_solution.flatten()
    time_min = t_span / 60
    
    # Target 도달 시간 계산
    target_idx = np.where(T_profile >= t_target)[0]
    if len(target_idx) > 0:
        time_to_target = time_min[target_idx[0]]
        st.success(f"✅ 목표 온도({t_target}°C) 도달 예상 시간: **{time_to_target:.1f} 분**")
    else:
        st.error(f"❌ 설정된 시간({time_limit}분) 내에 목표 온도에 도달하지 못합니다.")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time_min, y=T_profile, mode='lines', name='Process Temp', line=dict(color='firebrick', width=3)))
    fig.add_hline(y=t_target, line_dash="dash", line_color="green", annotation_text="Target Temp")
    fig.update_layout(xaxis_title='Time (minutes)', yaxis_title='Temperature (°C)', height=400, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    if st.button("Generate HTML/PDF Report"):
        st.info(f"Vessel [{tank_no}] / Jacket [{jacket_no}] 리포트 생성 로직 트리거됨.")
