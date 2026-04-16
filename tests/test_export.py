from utils.export import generate_html


def test_generate_html_contains_time_to_target_and_context():
    html = generate_html(
        {
            "op_mode": "Heating Mode",
            "service_name": "Polymerization",
            "tank_no": "R-1001",
            "jacket_no": "J-1001",
            "v_total": 12.3,
            "a_jacket": 45.6,
            "wall_mat": "Stainless Steel 304",
            "wall_thk": 12.0,
            "fluid_type": "Water",
            "t_service": 120.0,
            "jacket_type": "Half-Pipe",
            "agit_type": "Pitched Blade (4-Blade 45°)",
            "rpm": 60.0,
            "q_rxn": 0.0,
            "hi": 350.0,
            "ho": 800.0,
            "U": 210.0,
            "epsilon": 0.81,
            "NTU": 1.65,
            "t_init": 20.0,
            "t_target": 80.0,
            "tt_target": 24.5,
            "hi_calc_html": "hi details",
            "ho_calc_html": "ho details",
            "u_calc_html": "u details",
            "fig_img_html": "<img src='x'>",
            "desc_hi": "Inside description",
            "desc_ho": "Outside description",
            "desc_u": "Overall description",
        }
    )

    assert "24.5 min" in html
    assert "R-1001" in html
    assert "Heat Transfer Results" in html
