import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.integrate import odeint
import math

st.set_page_config(page_title="Jacketed Vessel Engineering", layout="wide")
st.title("🏭 Jacketed Vessel Process Design & Simulation")

# ==========================================
# 0. 데이터베이스 & SVG 그래픽
# ==========================================
# 임펠러 가이드 및 형태(SVG)
AGITATOR_DB = {
    "Pitched Blade (4-Blade 45°)": {
        "Np": 1.27,
        "desc": "혼합(Blending)과 열전달에 두루 쓰이는 표준형. 축 방향(Axial) 흐름을 형성하여 상하 믹싱에 유리합니다.",
        "svg": """<svg viewBox="0 0 100 100" style="height:120px; background-color:#f8f9fa; border-radius:8px;"><path d="M 50 10 V 90" stroke="#2E4053" stroke-width="6"/><path d="M 30 40 L 70 60 M 30 60 L 70 40" stroke="#E74C3C" stroke-width="8" stroke-linecap="round"/></svg>"""
    },
    "Rushton Turbine (6-Blade Flat)": {
        "Np": 5.0,
        "desc": "강력한 전단력(High Shear)과 방사형(Radial) 흐름을 만듭니다. 기체 분산(Gas dispersion)이나 유화 공정에 적합하나 동력 소모가 큽니다.",
        "svg": """<svg viewBox="0 0 100 100" style="height:120px; background-color:#f8f9fa; border-radius:8px;"><rect x="40" y="45" width="20" height="10" fill="#2E4053"/><path d="M 50 10 V 90 M 20 50 H 80 M 20 35 V 65 M 80 35 V 65" stroke="#E74C3C" stroke-width="6"/></svg>"""
    },
    "Anchor (Nominal)": {
        "Np": 0.4,
        "desc": "벽면과의 간극(Clearance)이 좁아 고점도(High Viscosity) 유체의 벽면 고착을 막고 열전달을 촉진하는 데 필수적입니다.",
        "svg": """<svg viewBox="0 0 100 100" style="height:120px; background-color:#f8f9fa; border-radius:8px;"><path d="M 50 10 V 85 M 20 40 V 70 A 30 30 0 0 0 80 70 V 40" stroke="#E74C3C" stroke-width="8" fill="none" stroke-linecap="round"/></svg>"""
    }
}

# ==========================================
# 1. 메인 화면 탭 구성 (Inputs)
# ==========================================
tab1, tab2, tab3 = st.tabs(["⚙️ 1. Design Inputs", "🧮 2. Engineering Calcs (Logic)", "📈 3. Simulation"])

with tab1:
    st.header("Step 1: Detailed Design Parameters")
    
    col_geom, col_agit, col_fluid = st.columns(3)
    
    with col_geom:
        st.subheader("Geometry & Jacket")
        d_in = st.number_input("Vessel ID (mm)", value=2000.0, step=100.0) / 1000.0
        tt_len = st.number_input("T/T Length (mm)", value=3000.0, step=100.0) / 1000.0
        wall_thk = st.number_input("Wall Thickness (mm)", value=12.0) / 1000.0
        
        st.divider()
        jacket_type = st.selectbox("Jacket Type", ["Half-Pipe", "Conventional (with Baffle)", "Dimple"])
        if jacket_type == "Half-Pipe":
            j_dim = st.number_input("Pipe ID (mm, 보통 3~4인치)", value=80.0) / 1000.0
        elif jacket_type == "Conventional (with Baffle)":
            j_dim = st.number_input("Annular Gap (mm, 간격)", value=50.0) / 1000.0
            j_pitch = st.number_input("Baffle Pitch (mm)", value=200.0) / 1000.0
        else:
            j_dim = 0 # Dimple은 복잡 형상이므로 치수 입력 제외
            st.info("Dimple Jacket은 형상 복잡성으로 인해 경험식을 적용합니다.")

    with col_agit:
        st.subheader("Agitator Specs")
        agit_type = st.selectbox("Impeller Type", list(AGITATOR_DB.keys()))
        
        # 선택된 임펠러 정보 및 SVG 출력
        agit_info = AGITATOR_DB[agit_type]
        st.markdown(agit_info["svg"], unsafe_allow_html=True)
        st.caption(f"**Guide:** {agit_info['desc']}")
        st.caption(f"**Power Number ($N_p$):** {agit_info['Np']}")
        
        rpm = st.number_input("Agitator Speed (RPM)", value=60.0)
        d_agit = st.number_input("Impeller Diameter (mm)", value=800.0) / 1000.0

    with col_fluid:
        st.subheader("Process & Service Fluid")
        st.markdown("**Process Fluid (Inside)**")
        rho_p = st.number_input("Density (kg/m³)", value=1000.0)
        cp_p = st.number_input("Specific Heat (J/kg·K)", value=4184.0)
        mu_cp = st.number_input("Viscosity (cP)", value=5.0) 
        k_p = st.number_input("Thermal Cond. (W/m·K)", value=0.6)
        
        st.markdown("**Service Fluid (Jacket - e.g., Cooling Water)**")
        q_service = st.number_input("Service Flow Rate (m³/h)", value=15.0)
        t_service = st.number_input("Service Temp (°C)", value=15.0)
        st.caption("※ 이 시뮬레이션에서는 Service 유체를 물(Water) 기준으로 동적 점도, 밀도를 간이 적용하여 계산합니다.")

# ==========================================
# 2. 메인 화면 탭 구성 (Calculations & Logic Exposure)
# ==========================================
with tab2:
    st.header("Step 2: Heat Transfer Calculation Logic")
    
    # 기초 변환
    k_wall = 16.0 # SS304 기준
    mu_p = mu_cp * 0.001
    N_rps = rpm / 60.0
    Q_sec = q_service / 3600.0 # m3/s
    
    # Service Fluid (Water) Assumed Properties
    rho_s, mu_s, k_s, Pr_s = 998.0, 0.001, 0.6, 7.0 
    
    st.subheader("1. Inside Film Coefficient ($h_i$) - Agitation")
    Re_agit = (rho_p * N_rps * (d_agit**2)) / mu_p
    Pr_p = (cp_p * mu_p) / k_p
    Nu_p = 0.53 * (Re_agit**0.67) * (Pr_p**0.33) if Re_agit > 0 else 0
    h_i_calc = (Nu_p * k_p) / d_in if d_in > 0 else 0
    
    st.latex(r"Re_a = \frac{\rho N D_a^2}{\mu} = " + f"{Re_agit:,.0f}")
    st.latex(r"Nu_i = 0.53 \cdot Re_a^{0.67} \cdot Pr^{0.33} \rightarrow \mathbf{h_i = " + f"{h_i_calc:.1f}" + r" \text{ W/m}^2\text{K}}")
    
    st.divider()
    st.subheader("2. Outside Film Coefficient ($h_o$) - Jacket Type")
    
    # Jacket 형태별 분기 계산 노출
    if jacket_type == "Half-Pipe":
        De = 0.61 * j_dim # 수력학적 직경
        A_cross = (math.pi * j_dim**2) / 8 # 반원 단면적
        v_s = Q_sec / A_cross
        Re_s = (rho_s * v_s * De) / mu_s
        Nu_s = 0.023 * (Re_s**0.8) * (Pr_s**0.4) # Dittus-Boelter
        h_o_calc = (Nu_s * k_s) / De
        
        st.info("💡 **Half-Pipe Logic:** 반원형 덕트 유동으로 간주하여 높은 유속과 강한 난류(Turbulent) 형성을 확인합니다.")
        st.latex(r"D_e \approx 0.61 \cdot d_{pipe} = " + f"{De:.4f} \text{ m}")
        st.latex(r"v = \frac{Q}{A_c} = " + f"{v_s:.2f} \text{ m/s}")
        st.latex(r"Re_o = " + f"{Re_s:,.0f}")
        st.latex(r"h_o = \frac{Nu \cdot k}{D_e} = \mathbf{" + f"{h_o_calc:.1f}" + r" \text{ W/m}^2\text{K}}")

    elif jacket_type == "Conventional (with Baffle)":
        De = 2 * j_dim # Gap
        A_cross = j_dim * j_pitch
        v_s = Q_sec / A_cross
        Re_s = (rho_s * v_s * De) / mu_s
        Nu_s = 0.027 * (Re_s**0.8) * (Pr_s**0.33)
        h_o_calc = (Nu_s * k_s) / De
        
        st.info("💡 **Conventional Logic:** Annular Gap과 Baffle Pitch에 의해 단면적이 결정됩니다. 유속이 상대적으로 느립니다.")
        st.latex(r"D_e \approx 2 \cdot Gap = " + f"{De:.4f} \text{ m}")
        st.latex(r"v = \frac{Q}{Gap \times Pitch} = " + f"{v_s:.2f} \text{ m/s}")
        st.latex(r"Re_o = " + f"{Re_s:,.0f}")
        st.latex(r"h_o = \mathbf{" + f"{h_o_calc:.1f}" + r" \text{ W/m}^2\text{K}}")

    else: # Dimple
        h_o_calc = 1500.0 # Vendor Assumed
        st.warning("💡 **Dimple Logic:** 형상 내부의 3차원 Vortex 발생으로 1차원 배관 수식 적용이 불가합니다. Vendor 보수적 경험값(1500 W/m²K)을 적용합니다.")
        st.latex(r"h_o \approx \mathbf{1500.0 \text{ W/m}^2\text{K}} \text{ (Empirical)}")

    st.divider()
    st.subheader("3. Overall Heat Transfer Coefficient ($U$)")
    R_total = (1/h_i_calc) + 0.0002 + (wall_thk/k_wall) + 0.0002 + (1/h_o_calc)
    U_calc = 1 / R_total
    
    st.latex(r"U = \frac{1}{\frac{1}{h_i} + R_{fi} + \frac{t}{k} + R_{fo} + \frac{1}{h_o}} = \mathbf{" + f"{U_calc:.1f}" + r" \text{ W/m}^2\text{K}}")

# ==========================================
# 3. 메인 화면 탭 구성 (Simulation)
# ==========================================
with tab3:
    st.header("Step 3: Dynamic Temperature Curve")
    st.write(f"계산된 최종 **U-Value: {U_calc:.1f} W/m²K** 를 바탕으로 시간에 따른 온도를 시뮬레이션합니다.")
    
    # 임시 볼륨 및 면적 (Geometry 상세 계산은 생략하고 근사치 적용)
    v_total = (math.pi / 4) * (d_in**2) * tt_len * 1.2
    a_jacket = math.pi * d_in * tt_len * 0.8
    M_cp_total = v_total * rho_p * cp_p 
    P_agit_watts = AGITATOR_DB[agit_type]["Np"] * rho_p * (N_rps**3) * (d_agit**5)
    
    def jacket_ode(T, t, U, A, T_s, M_cp, Q_a):
        return (U * A * (T_s - T) + Q_a) / M_cp

    t_span = np.linspace(0, 120 * 60, 500)
    T_solution = odeint(jacket_ode, 20.0, t_span, args=(U_calc, a_jacket, t_service, M_cp_total, P_agit_watts))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t_span/60, y=T_solution.flatten(), line=dict(color='firebrick', width=3)))
    fig.update_layout(xaxis_title='Time (min)', yaxis_title='Temp (°C)', height=400)
    st.plotly_chart(fig, use_container_width=True)
