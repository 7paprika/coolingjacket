import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.integrate import odeint
import math

st.set_page_config(page_title="Jacketed Vessel Engineering", layout="wide")
st.title("🏭 Jacketed Vessel Process Design & Simulation")

# ==========================================
# 1. 사이드바: 주요 메타데이터 (Tag, Info)
# ==========================================
with st.sidebar:
    st.header("📌 Identifications")
    tank_no = st.text_input("Vessel Tag No.", value="R-1001")
    jacket_no = st.text_input("Jacket Tag No.", value="J-1001")
    service_name = st.text_input("Service Name", value="Polymerization Reactor")
    st.divider()
    st.header("⏱️ Simulation Target")
    t_target = st.number_input("Target Temp (°C)", value=80.0)
    time_limit = st.number_input("Sim. Time (min)", value=120, min_value=10)

# ==========================================
# 2. 메인 화면 탭 구성
# ==========================================
tab1, tab2, tab3 = st.tabs(["⚙️ 1. Design Inputs", "🧮 2. Engineering Calcs", "📈 3. Simulation & Report"])

with tab1:
    st.header("Step 1: Detailed Design Parameters")
    
    col_geom, col_agit, col_fluid = st.columns(3)
    
    with col_geom:
        st.subheader("Geometry & Vessel")
        d_in = st.number_input("Vessel ID (mm)", value=2000.0, step=100.0) / 1000.0 # m 변환
        tt_len = st.number_input("T/T Length (mm)", value=3000.0, step=100.0) / 1000.0 # m 변환
        head_type = st.selectbox("Bottom Head Type", ["2:1 Ellipsoidal", "Hemispherical", "Torispherical"])
        wall_thk = st.number_input("Wall Thickness (mm)", value=12.0) / 1000.0
        k_wall = st.number_input("Wall Thermal Cond. (W/m·K)", value=16.0) # SS304 기준
        jacket_coverage = st.number_input("Jacket Straight Coverage (%)", value=80.0, min_value=10.0, max_value=100.0) / 100.0
        
    with col_agit:
        st.subheader("Agitator Specs")
        agit_type = st.selectbox("Impeller Type", ["Pitched Blade Turbine", "Anchor", "Rushton"])
        rpm = st.number_input("Agitator Speed (RPM)", value=60.0)
        d_agit = st.number_input("Impeller Diameter (mm)", value=800.0) / 1000.0
        motor_kw = st.number_input("Motor Power (kW)", value=15.0)

    with col_fluid:
        st.subheader("Fluid Properties (at Ref. Temp)")
        st.markdown("**Process Fluid (Inside)**")
        rho_p = st.number_input("Density (kg/m³)", value=1000.0, key="rho_p")
        cp_p = st.number_input("Specific Heat (J/kg·K)", value=4184.0, key="cp_p")
        mu_p = st.number_input("Viscosity (Pa·s)", value=0.001, format="%.4f", key="mu_p")
        k_p = st.number_input("Thermal Cond. (W/m·K)", value=0.6, key="k_p")
        t_initial = st.number_input("Initial Temp (°C)", value=20.0)

        st.markdown("**Service Fluid (Jacket)**")
        t_service = st.number_input("Service Temp (°C)", value=150.0)
        # 단순화를 위해 Jacket 쪽 h_o는 고정값 입력 (실제로는 flow rate 필요)
        st.caption("※ Jacket 측 대류계수는 유량 조건에 따라 변동되므로 직접 입력")
        h_o_input = st.number_input("Est. Jacket h_o (W/m²·K)", value=1500.0)

with tab2:
    st.header("Step 2: Intermediate Calculations")
    
    # 2.1 Geometry Calculations
    # Volume calculation
    v_cyl = (math.pi / 4) * (d_in**2) * tt_len
    a_cyl = math.pi * d_in * tt_len
    
    if head_type == "2:1 Ellipsoidal":
        v_head = (math.pi / 24) * (d_in**3)
        a_head = 1.084 * (d_in**2) # Approximate area formula
    elif head_type == "Hemispherical":
        v_head = (math.pi / 12) * (d_in**3)
        a_head = (math.pi / 2) * (d_in**2)
    else: # Torispherical (Approximation)
        v_head = 0.08 * (d_in**3)
        a_head = 0.93 * (d_in**2)
        
    v_total = v_cyl + v_head # Assuming flat top or filled to T/T
    a_jacket = (a_cyl * jacket_coverage) + a_head # Jacket covers bottom head + partial straight shell
    
    # 2.2 Heat Transfer Coefficients (Inside h_i)
    N_rps = rpm / 60.0
    Re_agit = (rho_p * N_rps * (d_agit**2)) / mu_p
    Pr_p = (cp_p * mu_p) / k_p
    
    # Nusselt correlation (Simplified for Pitched Blade Turbine: Nu = 0.53 * Re^0.67 * Pr^0.33)
    # 실제로는 임펠러 타입에 따라 상수가 다름.
    Nu_p = 0.53 * (Re_agit**0.67) * (Pr_p**0.33)
    h_i_calc = (Nu_p * k_p) / d_in
    
    # 2.3 Overall Heat Transfer Coefficient (U)
    foul_i = 0.0002
    foul_o = 0.0002
    R_total = (1/h_i_calc) + foul_i + (wall_thk/k_wall) + foul_o + (1/h_o_input)
    U_calc = 1 / R_total
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("📐 **Geometry Output**")
        st.write(f"- **Total Volume:** {v_total:.2f} m³")
        st.write(f"- **Jacket Heat Transfer Area:** {a_jacket:.2f} m²")
    with c2:
        st.success("🔬 **Dimensionless Numbers**")
        st.write(f"- **Reynolds No. (Re):** {Re_agit:,.0f}")
        st.write(f"- **Prandtl No. (Pr):** {Pr_p:.2f}")
        st.write(f"- **Nusselt No. (Nu):** {Nu_p:.1f}")
    with c3:
        st.warning("🌡️ **Heat Transfer Coefficients**")
        st.write(f"- **Inside ($h_i$):** {h_i_calc:.1f} W/m²·K")
        st.write(f"- **Outside ($h_o$):** {h_o_input:.1f} W/m²·K")
        st.write(f"- **Overall ($U$):** **{U_calc:.1f} W/m²·K**")

    st.latex(r"U = \frac{1}{\frac{1}{h_i} + R_{f,i} + \frac{t}{k} + R_{f,o} + \frac{1}{h_o}}")

with tab3:
    st.header("Step 3: Dynamic Simulation & Export")
    
    # Simulation ODE
    M_cp_total = v_total * rho_p * cp_p # J/K
    Q_agit_watts = motor_kw * 1000 # W
    
    def jacket_heating_ode(T, t, U, A, T_service, M_cp, Q_agit):
        Q_in = U * A * (T_service - T)
        dTdt = (Q_in + Q_agit) / M_cp
        return dTdt

    t_span = np.linspace(0, time_limit * 60, 500)
    T_solution = odeint(jacket_heating_ode, t_initial, t_span, args=(U_calc, a_jacket, t_service, M_cp_total, Q_agit_watts))
    T_profile = T_solution.flatten()
    time_min = t_span / 60
    
    # Plotly Chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time_min, y=T_profile, mode='lines', name='Process Temp', line=dict(color='firebrick', width=3)))
    fig.add_hline(y=t_target, line_dash="dash", line_color="green", annotation_text="Target Temp")
    fig.update_layout(xaxis_title='Time (minutes)', yaxis_title='Temperature (°C)', height=400, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
    
    # HTML Export Logic (Mockup for framework)
    st.markdown("---")
    if st.button("Generate HTML Report (Ready for PDF)"):
        st.success(f"Report generated for Vessel: {tank_no} / Jacket: {jacket_no}. (Integrate with WeasyPrint in backend).")
        # 실제 HTML 구조화 로직은 이전 코드와 동일하게 구현하면 됨.
