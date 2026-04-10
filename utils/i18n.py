i18n = {
    "en": {
        "title": "🏭 Jacketed Vessel Process Design & Simulation",
        "tab1": "⚙️ 1. Design Inputs",
        "tab2": "🧮 2. Engineering Calcs (Detailed)",
        "tab3": "📈 3. Simulation & Report",
        "geom_mat": "Geometry & Material",
        "agit_specs": "Agitator Specs",
        "fluid_props": "Fluid Properties",
        "download_html": "📥 Download HTML Report",
        "download_pdf": "📥 Download PDF Report",
        
        # Helptips (Enriched)
        "h_tank_no": "Unique identifier for the main process vessel (e.g., R-101). Used for report generation.",
        "h_jacket_no": "Unique identifier for the jacket heat exchanger.",
        "h_service": "Brief description of the process block or chemical application taking place.",
        "h_ttarget": "The desired final temperature constraint for the process fluid. The simulation will predict when it is reached.",
        "h_tlimit": "Maximum simulation duration. If the target is not reached within this limit, an error is reported.",
        
        "h_din": "Internal diameter (ID) of the main vessel shell. Must be strictly greater than impeller diameter.",
        "h_ttlen": "Tangent-to-Tangent (T/T) length of the straight cylindrical section where the primary jacket area is placed.",
        "h_head": "Shape of the bottom dished head. A 2:1 Ellipsoidal head has deeper volume than Torispherical, while Hemispherical provides maximum volume.",
        "h_mat": "Material of construction for the vessel shell wall. This uniquely sets the baseline thermal conductivity (k_w).",
        "h_thk": "Thickness of the vessel wall. Conductive resistance (R_w) scales linearly with this thickness.",
        "h_cov": "Percentage of the straight shell cylinder actually wrapped by the jacket. Usually 70~90% to avoid weld seams.",
        
        "h_jtype": "Type of jacket geometry. Half-pipe allows high service fluid velocity and pressure, whereas Conventional is better for uniform bulk flow.",
        "h_jdim": "For Half-pipe: Pipe internal cross-sectional diameter. For Conventional: The annular gap space between vessel wall and outer jacket wall.",
        "h_jpitch": "For Half-pipe: Bending pitch. For Conventional: Spacing between spiral baffles. Tighter pitch increases velocity and h_o, but also pressure drop.",

        "h_atype": "Impeller geometry. Dictates the Power Number (Np) and local Nusselt constant for forced convection inside the vessel.",
        "h_rpm": "Rotational speed of the agitator. Higher RPM significantly boosts inside film coefficient but drastically increases required motor power.",
        "h_dagit": "Outer sweep diameter of the impeller blades. Larger diamater increases shear and Reynolds Number.",
        
        "h_hrxn": "Enable this if an ongoing chemical reaction introduces intrinsic heat generation or cooling.",
        "h_qrxn": "Net heat of reaction in kW. Enter a positive number (+) for Exothermic (spontaneous heating) and negative (-) for Endothermic.",
        
        "h_rhop": "Bulk fluid density of the internal process fluid.",
        "h_cpp": "Specific heat capacity (Cp) of the internal process fluid. Higher Cp causes smaller temperature jumps.",
        "h_mup": "Dynamic viscosity of the inner fluid at operating conditions. High viscosity drastically reduces forced convection efficiency.",
        "h_kp": "Thermal conductivity of the inner fluid. Affects boundary layer heat transport.",
        "h_tinit": "Temperature of the process fluid at time t=0 of the simulation.",
        
        "h_stype": "Pre-configured heat transfer fluid curves. Custom option allows inputting 2 datapoints for linear interpolation.",
        "h_qserv": "Volumetric flow rate of the utility fluid entering the jacket. Directly drives the Reynolds number and effective Effectiveness (ε).",
        "h_tserv": "Inlet supply temperature of the utility fluid from the utility header."
    },
    "ko": {
        "title": "🏭 자켓 반응기 공정 설계 & 시뮬레이션",
        "tab1": "⚙️ 1. 설계 입력",
        "tab2": "🧮 2. 엔지니어링 계산 상세",
        "tab3": "📈 3. 시뮬레이션 & 리포트",
        "geom_mat": "형상 및 재질",
        "agit_specs": "교반기 제원",
        "fluid_props": "유체 물성",
        "download_html": "📥 HTML 리포트 다운로드",
        "download_pdf": "📥 PDF 리포트 다운로드",
        
        # Helptips (Enriched)
        "h_tank_no": "반응기를 식별하기 위한 고유 Tag (예: R-101). 리포트 출력 시 주요 식별자로 사용됩니다.",
        "h_jacket_no": "자켓을 식별하기 위한 고유 Tag.",
        "h_service": "수행할 공정의 명칭 및 설명 (예: 1차 중합반응, 촉매 승온).",
        "h_ttarget": "내부 공정 유체가 최종적으로 도달해야 하는 목표 온도. 이 목표 온도까지 소요되는 시간을 시뮬레이션합니다.",
        "h_tlimit": "시뮬레이션 구동을 허용할 최대 시간. 이 시간 내에 타겟 온도에 도달하지 못하면 프로세스가 지연됨을 의미합니다.",
        
        "h_din": "반응기 본체(Shell)의 내부 직경. 교반기 임펠러 외경보다 반드시 커야 합니다.",
        "h_ttlen": "반응기 본체의 직선 원통부 길이 (Tangent-to-Tangent Length). 실제 자켓이 설치될 수 있는 최대 길이를 결정합니다.",
        "h_head": "하단부 경판 형상. 2:1 타원형 경판, 반구형 경판 등 형상에 따라 하부 용적과 열교환 표면적이 달라집니다.",
        "h_mat": "반응기 벽면의 금속 재질. 이 재질에 따라 벽면의 열전도 능력(k)이 상수화되어 적용됩니다.",
        "h_thk": "반응기 벽면 철판 두께. 두께가 얇을수록 열전도는 좋아지지만 내압 설계 한계를 유의해야 합니다.",
        "h_cov": "직관부 전체 길이 중 자켓 구조물이 실제로 덮고 있는 영역의 비율(%).",
        
        "h_jtype": "자켓 구조의 형태. Half-pipe는 유속과 내압에 유리하며, Conventional 자켓은 골고루 넓은 면적에 유체를 접촉시킵니다.",
        "h_jdim": "Half-pipe의 경우 원형 배관의 내경을 뜻하며, Conventional 자켓의 경우 반응기 외벽과 자켓 내부 사이의 Gap 거리를 의미합니다.",
        "h_jpitch": "자켓 내부의 흐름을 꼬아주기 위한 나선형 배열 간격(Baffle Pitch). 좁을수록 유속이 증가하여 외부 대류 계수(h_o)는 증가하지만 압력 손실이 상승합니다.",

        "h_atype": "교반 임펠러 형태. 각 임펠러별로 발생하는 난류 패턴(방사형/축방향)이 다르며, 이는 Nusselt 수식과 소요 동력을 결정하는 상수입니다.",
        "h_rpm": "교반기 회전 속도. RPM이 높을수록 내부 대류 계수(h_i)는 크게 증가하지만, 소요 모터 동력은 속도의 3제곱에 비례하여 급상승합니다.",
        "h_dagit": "교반기 임펠러의 외경. 용기 내부 직경을 초과할 수 없으며 클수록 전단력이 강해집니다.",
        
        "h_hrxn": "용기 내부에서 자발적인 화학 반응(발열/흡열)이 발생하여 온도 변화율(ODE)에 영향을 줄 경우 체크하십시오.",
        "h_qrxn": "화학 반응으로 발생하는 총 열량(kW). 발열(온도를 스스로 높임)은 양수(+), 흡열(온도를 스스로 낮춤)은 음수(-)로 기입합니다.",
        
        "h_rhop": "내부 공정 유체의 밀도. 동 점성(Reynolds number) 계산 및 열용량 산출의 기초 단위입니다.",
        "h_cpp": "내부 유체의 비열. 비열이 클수록 1도를 올리거나 내리기 위해 더 많은 열량(J)이 요구됩니다.",
        "h_mup": "점도. 고점도 유체일 경우 내부 레이놀즈 수 및 Prandtl 교차 팩터가 낮아져 교반 효율이 급감합니다.",
        "h_kp": "내부 유체의 열전도율(Fluid Thermal Conductivity).",
        "h_tinit": "열전달 시뮬레이션이 시작되는 시점(t=0)에서의 반응기 내부 초기 온도.",
        
        "h_stype": "자켓으로 공급되는 열매체, 냉매체 종류 예약 프리셋. Custom을 선택하면 선형 보간을 위해 직접 물성을 입력할 수 있습니다.",
        "h_qserv": "시간당 자켓에 유입되는 서비스 유체의 부피 유량(m³/h). 유량이 높을수록 열전달 면의 유속이 높아져 벽면 정체 현상을 막습니다.",
        "h_tserv": "외부 유틸리티 설비(보일러, 칠러 등)에서 자켓 입구로 공급되는 서비스 유체의 절대 온도."
    }
}
