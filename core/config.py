MATERIAL_K = {
    "Carbon Steel (SA-516)": 45.0,
    "Stainless Steel 304": 16.0,
    "Stainless Steel 316": 16.3,
    "Titanium": 17.0,
    "Glass-Lined (Steel base)": 1.2 
}

AGITATOR_DB = {
    "None (Natural Convection)": {
        "Np": 0.0, "desc": "교반기 없음. 자연 대류(Natural Convection)에 의한 열전달이 발생합니다.",
        "svg": """<svg viewBox="0 0 100 100" style="height:50px; background-color:#f8f9fa; border-radius:8px;"><path d="M 20 80 Q 50 50 80 80 M 30 90 Q 50 60 70 90" stroke="#3498DB" stroke-width="4" fill="none" stroke-dasharray="5,5"/></svg>"""
    },
    "Pitched Blade (4-Blade 45°)": {
        "Np": 1.27, "desc": "혼합과 열전달에 두루 쓰이는 표준형. 축 방향(Axial) 흐름을 형성합니다.",
        "svg": """<svg viewBox="0 0 100 100" style="height:50px; background-color:#f8f9fa; border-radius:8px;"><path d="M 50 10 V 90" stroke="#2E4053" stroke-width="6"/><path d="M 30 40 L 70 60 M 30 60 L 70 40" stroke="#E74C3C" stroke-width="8" stroke-linecap="round"/></svg>"""
    },
    "Rushton Turbine (6-Blade Flat)": {
        "Np": 5.0, "desc": "강력한 전단력(High Shear)과 방사형(Radial) 흐름. 기체 분산에 적합하나 동력 소모가 큽니다.",
        "svg": """...""" # shortened for brevity, will replace with original in app.py if needed, let me just keep it simple.
    },
    "Anchor (Nominal)": {"Np": 0.4, "desc": "", "svg": ""},
    "Flat Paddle (2-Blade)": {"Np": 1.7, "desc": "", "svg": ""},
    "Marine Propeller (3-Blade)": {"Np": 0.35, "desc": "", "svg": ""},
    "Retreat Curve (Glass-Lined)": {"Np": 0.35, "desc": "", "svg": ""}
}

# The SVG parts from original:
AGITATOR_DB["Rushton Turbine (6-Blade Flat)"]["svg"] = """<svg viewBox="0 0 100 100" style="height:50px; background-color:#f8f9fa; border-radius:8px;"><rect x="40" y="45" width="20" height="10" fill="#2E4053"/><path d="M 50 10 V 90 M 20 50 H 80 M 20 35 V 65 M 80 35 V 65" stroke="#E74C3C" stroke-width="6"/></svg>"""
AGITATOR_DB["Anchor (Nominal)"]["svg"] = """<svg viewBox="0 0 100 100" style="height:50px; background-color:#f8f9fa; border-radius:8px;"><path d="M 50 10 V 85 M 20 40 V 70 A 30 30 0 0 0 80 70 V 40" stroke="#E74C3C" stroke-width="8" fill="none" stroke-linecap="round"/></svg>"""
AGITATOR_DB["Flat Paddle (2-Blade)"]["svg"] = """<svg viewBox="0 0 100 100" style="height:50px; background-color:#f8f9fa; border-radius:8px;"><rect x="30" y="40" width="40" height="20" fill="#E74C3C"/><path d="M 50 10 V 90" stroke="#2E4053" stroke-width="6"/></svg>"""
AGITATOR_DB["Marine Propeller (3-Blade)"]["svg"] = """<svg viewBox="0 0 100 100" style="height:50px; background-color:#f8f9fa; border-radius:8px;"><path d="M 50 10 V 90" stroke="#2E4053" stroke-width="6"/><ellipse cx="50" cy="50" rx="30" ry="8" transform="rotate(30 50 50)" fill="#E74C3C"/><ellipse cx="50" cy="50" rx="30" ry="8" transform="rotate(-30 50 50)" fill="#E74C3C"/></svg>"""
AGITATOR_DB["Retreat Curve (Glass-Lined)"]["svg"] = """<svg viewBox="0 0 100 100" style="height:50px; background-color:#f8f9fa; border-radius:8px;"><path d="M 50 10 V 90" stroke="#2E4053" stroke-width="6"/><path d="M 50 80 Q 20 80 20 50" stroke="#E74C3C" stroke-width="8" fill="none"/><path d="M 50 80 Q 80 80 80 50" stroke="#E74C3C" stroke-width="8" fill="none"/></svg>"""

SERVICE_FLUID_DB = {
    "Water": {
        "T": [0, 20, 40, 60, 80, 100, 150],
        "rho": [999.8, 998.2, 992.2, 983.2, 971.8, 958.4, 917.0],
        "cp": [4217, 4182, 4178, 4184, 4196, 4216, 4310],
        "mu": [1.79e-3, 1.00e-3, 0.65e-3, 0.47e-3, 0.35e-3, 0.28e-3, 0.18e-3],
        "k": [0.561, 0.598, 0.630, 0.654, 0.670, 0.679, 0.683]
    },
    "Thermal Oil (Dowtherm A)": {
        "T": [20, 100, 150, 200, 250, 300, 350],
        "rho": [1060, 995, 954, 913, 871, 828, 785],
        "cp": [1550, 1780, 1920, 2060, 2210, 2350, 2490],
        "mu": [4.0e-3, 0.6e-3, 0.4e-3, 0.25e-3, 0.18e-3, 0.14e-3, 0.12e-3],
        "k": [0.138, 0.125, 0.117, 0.109, 0.101, 0.093, 0.085]
    },
    "Steam (Condensing)": {
        "T": [100, 120, 150, 180],
        "rho": [958, 943, 917, 887],
        "cp": [4216, 4240, 4310, 4410],
        "mu": [0.28e-3, 0.23e-3, 0.18e-3, 0.15e-3],
        "k": [0.679, 0.683, 0.683, 0.675]
    },
    "Brine (20% NaCl)": {
        "T": [-20, 0, 20, 40, 60, 80],
        "rho": [1160, 1155, 1148, 1140, 1130, 1118],
        "cp": [3200, 3250, 3300, 3330, 3360, 3400],
        "mu": [5.0e-3, 2.5e-3, 1.5e-3, 1.0e-3, 0.7e-3, 0.5e-3],
        "k": [0.54, 0.56, 0.58, 0.59, 0.60, 0.61]
    }
}
