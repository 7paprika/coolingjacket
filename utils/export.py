import io
from xhtml2pdf import pisa
from datetime import datetime

def generate_html(ctx):
    op_color = 'red' if ctx['op_mode'] == 'Heating Mode' else 'blue'
    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{ size: A4; margin: 2cm; }}
            body {{ font-family: 'Helvetica', sans-serif; font-size: 12px; color: #333; }}
            h1 {{ border-bottom: 2px solid #2E4053; color: #2E4053; font-size: 20px; }}
            h2 {{ color: #E74C3C; margin-top: 20px; font-size: 16px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
            th, td {{ border: 1px solid #bdc3c7; padding: 8px; text-align: left; }}
            th {{ background-color: #ecf0f1; width: 30%; }}
        </style>
    </head>
    <body>
        <h1>Jacketed Vessel Thermal Calculation Report</h1>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | <strong>Service:</strong> {ctx['service_name']}</p>
        
        <h2>1. Identifications</h2>
        <table>
            <tr><th>Vessel Tag No.</th><td>{ctx['tank_no']}</td><th>Jacket Tag No.</th><td>{ctx['jacket_no']}</td></tr>
            <tr><th>Vessel Volume</th><td>{ctx['v_total']:.2f} m³</td><th>Heat Transfer Area (OD)</th><td>{ctx['a_jacket']:.2f} m²</td></tr>
            <tr><th>Material</th><td>{ctx['wall_mat']}</td><th>Wall Thickness</th><td>{ctx['wall_thk']:.1f} mm</td></tr>
            <tr><th>Operation Mode</th><td colspan="3" style="font-weight:bold; color:{op_color};">{ctx['op_mode']}</td></tr>
        </table>

        <h2>2. Heat Transfer Results</h2>
        <table>
            <tr><th>Service Fluid</th><td>{ctx['fluid_type']} ({ctx['t_service']}°C)</td><th>Jacket Type</th><td>{ctx['jacket_type']}</td></tr>
            <tr><th>Agitator Type</th><td>{ctx['agit_type']} ({ctx['rpm']} RPM)</td><th>Reaction Heat</th><td>{ctx['q_rxn']} kW</td></tr>
            <tr><th>Inside Coefficient (h_i)</th><td>{ctx['hi']:.1f} W/m²K</td><th>Outside Coefficient (h_o)</th><td>{ctx['ho']:.1f} W/m²K</td></tr>
            <tr><th>Calculated U-Value</th><td>{ctx['U']:.1f} W/m²K</td><th>Effectiveness (ε) / NTU</th><td>{ctx['epsilon']:.3f} / {ctx['NTU']:.2f}</td></tr>
        </table>
        {f"<table><tr><th>Half-Pipe Pitch</th><td>{ctx['half_pipe_pitch_mm']} mm</td><th>Estimated Turns</th><td>{ctx['half_pipe_turns']}</td></tr><tr><th>Total Helix Length</th><td>{ctx['half_pipe_helix_length_m']} m</td><th colspan='2'></th></tr></table>" if ctx.get('half_pipe_turns') is not None else ''}
        
        <h2>3. Dynamic Simulation Summary</h2>
        <table>
            <tr><th>Initial Temp</th><td>{ctx['t_init']} °C</td><th>Service Temp</th><td>{ctx['t_service']} °C</td></tr>
            <tr><th>Target Temp</th><td>{ctx['t_target']} °C</td><th>Estimated Time to Target</th><td><strong style="color:green;">{ctx['tt_target']} min</strong></td></tr>
        </table>
        
        <div style="margin-top:20px; text-align:center;">
            {ctx['fig_img_html']}
        </div>
        
        <div style="page-break-before: always;"></div>
        <h2>4. Detailed Calculation Procedures</h2>
        <h3>4.1 Inside Film Coefficient (h_i)</h3>
        <p style="color: #555; background-color: #f0f0f0; padding: 10px; font-size: 11px;"><i>{ctx['desc_hi']}</i></p>
        <p style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498DB; line-height: 1.6; font-family: monospace;">
            {ctx['hi_calc_html']}
        </p>

        <h3>4.2 Outside Film Coefficient (h_o)</h3>
        <p style="color: #555; background-color: #f0f0f0; padding: 10px; font-size: 11px;"><i>{ctx['desc_ho']}</i></p>
        <p style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #E74C3C; line-height: 1.6; font-family: monospace;">
            {ctx['ho_calc_html']}
        </p>

        <h3>4.3 Overall Heat Transfer Coefficient (U)</h3>
        <p style="color: #555; background-color: #f0f0f0; padding: 10px; font-size: 11px;"><i>{ctx['desc_u']}</i></p>
        <p style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #27AE60; line-height: 1.6; font-family: monospace;">
            {ctx['u_calc_html']}
        </p>
    </body>
    </html>
    """
    return html

def create_pdf(html_content):
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
    if pisa_status.err:
        return None
    return pdf_buffer.getvalue()
