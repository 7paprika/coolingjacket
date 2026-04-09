import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.integrate import odeint
import json
import zlib
import base64
from datetime import datetime

# ==========================================
# 1. 상태 관리 & 딥링킹 모듈 (Security & Sharing)
# ==========================================
def encode_state_to_url(state_dict):
    """딕셔너리를 압축 및 Base64 인코딩하여 안전한 문자열로 변환"""
    json_str = json.dumps(state_dict)
    compressed = zlib.compress(json_str.encode('utf-8'))
    b64_encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
    return b64_encoded

def decode_state_from_url(b64_str):
    """Base64 문자열을 디코딩 및 압축 해제하여 딕셔너리로 복원"""
    try:
        compressed = base64.urlsafe_b64decode(b64_str.encode('utf-8'))
        json_str = zlib.decompress(compressed).decode('utf-8')
        return json.loads(json_str)
    except Exception as e:
        st.error("잘못되거나 손상된 링크입니다. 기본값으로 시작합니다.")
        return {}

# ==========================================
# 2. 엔지니어링 계산 모듈 (Engineering Core)
# ==========================================
def calculate_overall_heat_transfer(h_i, h_o, wall_thickness, k_wall, foul_i, foul_o):
    """총괄 열전달 계수(U) 계산 (평면 벽 가정, 실제로는 원통형 보정 필요)"""
    # 시니어의 경고: 실제로는 D_o/D_i Log mean area를 써야 하지만 시뮬레이션 시연용으로 단순화함.
    R_total = (1/h_i) + foul_i + (wall_thickness / k_wall) + foul_o + (1/h_o)
    return 1 / R_total

def jacket_heating_ode(T, t, U, A, T_service, M_cp, Q_loss_coeff, T_amb, Q_agit):
    """
    미분 방정식: dT/dt = (Q_in - Q_loss + Q_agit) / (M * Cp)
    Lumped Model 적용. Radial gradient는 배제하고 Bulk 온도 기준 계산.
    """
    Q_in = U * A * (T_service - T) # LMTD 대신 미소 시간의 온도차 적용
    Q_loss = Q_loss_coeff * (T - T_amb)
    dTdt = (Q_in - Q_loss + Q_agit) / M_cp
    return dTdt

# ==========================================
# 3. Streamlit UI & 메인 로직
# ==========================================
st.set_page_config(page_title="Jacketed Vessel Simulator", layout="wide")
st.title("🏭 Jacketed Vessel Design & Dynamic Simulator")

# URL 파라미터 확인 및 초기화
query_params = st.query_params
initial_state = {}
if "data" in query_params:
    initial_state = decode_state_from_url(query_params["data"])

# --- 입력부 (슬라이더 절대 금지, 정확한 Number Input 사용) ---
with st.sidebar:
    st.header("1. General Information")
    tank_no = st.text_input("Tank No.", value=initial_state.get("tank_no", "TK-1001"))
    service_name = st.text_input("Service Name", value=initial_state.get("service_name", "Reactor Heating"))
    
    st.header("2. Geometry & Agitation")
    # 슬라이더 대신 number_input 적용. 단위 명확히 표기.
    v_vol = st.number_input("Working Volume (m³)", value=initial_state.get("v_vol", 5.0), min_value=0.1)
    a_jacket = st.number_input("Jacket Area (m²)", value=initial_state.get("a_jacket", 10.0), min_value=0.1)
    jacket_type = st.selectbox("Jacket Type", ["Conventional", "Half-pipe", "Dimple"], index=["Conventional", "Half-pipe", "Dimple"].index(initial_state.get("jacket_type", "Conventional")))
    agit_power = st.number_input("Agitator Power (kW)", value=initial_state.get("agit_power", 5.0), min_value=0.0)
    
    st.header("3. Process Conditions")
    t_initial = st.number_input("Initial Process Temp (°C)", value=initial_state.get("t_initial", 20.0))
    t_target = st.number_input("Target Process Temp (°C)", value=initial_state.get("t_target", 80.0))
    t_service = st.number_input("Service Fluid Temp (°C)", value=initial_state.get("t_service", 120.0))
    t_amb = st.number_input("Ambient Temp (°C)", value=initial_state.get("t_amb", 25.0))
    time_limit = st.number_input("Simulation Time (min)", value=initial_state.get("time_limit", 120), min_value=10)
    
    st.header("4. Heat Transfer Parameters")
    st.caption("※ 실제로는 유체 물성과 RPM으로 계산되어야 하나 임시 입력창 제공")
    h_i = st.number_input("Process side h (W/m²K)", value=initial_state.get("h_i", 800.0))
    h_o = st.number_input("Jacket side h (W/m²K)", value=initial_state.get("h_o", 1200.0))
    rho_cp = st.number_input("Process Density * Cp (kJ/m³K)", value=initial_state.get("rho_cp", 4184.0))

    if st.button("Generate Share Link"):
        current_state = {
            "tank_no": tank_no, "service_name": service_name, "v_vol": v_vol,
            "a_jacket": a_jacket, "jacket_type": jacket_type, "agit_power": agit_power,
            "t_initial": t_initial, "t_target": t_target, "t_service": t_service,
            "t_amb": t_amb, "time_limit": time_limit, "h_i": h_i, "h_o": h_o, "rho_cp": rho_cp
        }
        encoded = encode_state_to_url(current_state)
        # st.query_params 설정으로 URL 즉시 변경 (Streamlit 1.30 이상)
        st.query_params["data"] = encoded
        st.success("URL이 업데이트되었습니다. 주소창의 링크를 동료에게 공유하세요.")

# --- 가이드라인 및 결과 표출부 ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Design Guide & Setup")
    # 재질 및 형태별 가이드라인 동적 표출 (엔지니어링 피드백 반영)
    if jacket_type == "Conventional":
        st.info("💡 **Guide (Conventional):**\n제작이 용이하나 고압(High Pressure) Service에는 Vessel 벽 두께가 두꺼워져 불리합니다. 내부 Baffle 유무를 반드시 체크하십시오.")
    elif jacket_type == "Half-pipe":
        st.success("💡 **Guide (Half-pipe):**\n고압 Service Fluid 및 높은 열전달 계수(High Velocity)가 필요할 때 적합합니다. Vessel 전체 두께를 얇게 가져갈 수 있습니다.")
    else:
        st.warning("💡 **Guide (Dimple):**\n경량화에 유리하나 내부 응력 집중부위 피로파괴(Fatigue)에 주의하십시오. 열매체(Thermal Oil) 사용 시 국부 과열을 확인해야 합니다.")

    # 계산 전 Validation (오류 방지)
    if t_target >= t_service:
        st.error("비정상 입력: Target 온도가 Service 온도보다 높거나 같습니다. 열역학 제2법칙을 무시할 셈인가?")
        st.stop()

    # 사전 계산 (Pre-calculations)
    U_val = calculate_overall_heat_transfer(h_i, h_o, 0.01, 16.0, 0.0002, 0.0002)
    M_cp_total = v_vol * rho_cp * 1000 # J/K (단위 변환 주의)
    Q_agit_watts = agit_power * 1000 # W
    Q_loss_coeff = 50.0 # W/K (가상의 단열재 손실 계수, 실제 계산식 필요)

    st.write("### Calculated Parameters")
    st.metric(label="Overall U-Value (Estimate)", value=f"{U_val:.2f} W/m²K")
    st.metric(label="Total Thermal Capacity", value=f"{M_cp_total/1000:.1f} kJ/K")

with col2:
    st.subheader("Dynamic Temperature Profile (Heating Curve)")
    
    # ODE Solver 실행
    t_span = np.linspace(0, time_limit * 60, 500) # 초(sec) 단위 시뮬레이션
    T_solution = odeint(
        jacket_heating_ode, 
        t_initial, 
        t_span, 
        args=(U_val, a_jacket, t_service, M_cp_total, Q_loss_coeff, t_amb, Q_agit_watts)
    )
    T_profile = T_solution.flatten()
    time_min = t_span / 60

    # 목표 온도 도달 시간 탐색
    target_idx = np.where(T_profile >= t_target)[0]
    if len(target_idx) > 0:
        time_to_target = time_min[target_idx[0]]
        st.success(f"✅ 목표 온도({t_target}°C) 도달 예상 시간: **{time_to_target:.1f} 분**")
    else:
        st.error(f"❌ 설정된 시간({time_limit}분) 내에 목표 온도에 도달하지 못합니다. 열전달 면적이나 Service 온도를 올리십시오.")

    # Plotly 시각화 (Interactive & Exportable)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time_min, y=T_profile, mode='lines', name='Process Temp', line=dict(color='firebrick', width=3)))
    fig.add_hline(y=t_target, line_dash="dash", line_color="green", annotation_text="Target Temp")
    fig.add_hline(y=t_service, line_dash="dot", line_color="blue", annotation_text="Service Fluid Temp")
    fig.update_layout(xaxis_title='Time (minutes)', yaxis_title='Temperature (°C)', height=500, template="plotly_white")
    
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 4. PDF Report Rendering Pipeline (임베딩 방식)
# ==========================================
st.markdown("---")
st.subheader("📄 Engineering Report Export")
st.caption("계산서 양식의 HTML을 렌더링하고 PDF로 변환하는 파이프라인의 뼈대입니다.")

if st.button("Generate PDF Report"):
    with st.spinner("Generating Report..."):
        # 1. Plotly 그래프를 Base64 이미지로 변환
        img_bytes = fig.to_image(format="png", width=800, height=500)
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        
        # 2. 일반적인 계산서 양식의 HTML 생성
        # (Jinja2를 쓰는 것이 정석이나, 구조를 보여주기 위해 f-string 사용)
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                h1 {{ color: #2E4053; border-bottom: 2px solid #2E4053; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .img-container {{ text-align: center; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <h1>Jacketed Vessel Thermal Calculation Report</h1>
            <p><strong>Tank No:</strong> {tank_no} | <strong>Date:</strong> {datetime.now().strftime("%Y-%m-%d")}</p>
            <table>
                <tr><th>Jacket Type</th><td>{jacket_type}</td><th>Target Temp</th><td>{t_target} °C</td></tr>
                <tr><th>Heat Transfer Area</th><td>{a_jacket} m²</td><th>Service Temp</th><td>{t_service} °C</td></tr>
                <tr><th>Overall U-Value</th><td>{U_val:.2f} W/m²K</td><th>Agitator Power</th><td>{agit_power} kW</td></tr>
            </table>
            <div class="img-container">
                <h3>Heating Curve</h3>
                <img src="data:image/png;base64,{img_base64}" alt="Heating Curve">
            </div>
        </body>
        </html>
        """
        
        # 3. PDF 변환 및 다운로드 (여기서는 xhtml2pdf 또는 weasyprint가 서버에 설치되어야 함)
        # 주의: 클라우드 환경에서는 패키지 종속성 문제가 발생하므로, 아래는 다운로드 버튼의 작동 원리만 구현.
        # 실제 적용 시에는 백엔드에 pdfkit + wkhtmltopdf 등을 세팅하고 변환된 byte를 data에 전달해야 함.
        st.info("HTML 양식이 성공적으로 생성되었습니다. (실제 환경에서는 여기서 WeasyPrint/xhtml2pdf를 거쳐 PDF 바이트로 변환됩니다.)")
        
        st.download_button(
            label="Download HTML Report (PDF 전처리 단계)",
            data=html_content,
            file_name=f"Report_{tank_no}.html",
            mime="text/html"
        )
