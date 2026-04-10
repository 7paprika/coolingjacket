import numpy as np
from scipy.interpolate import interp1d
from core.config import SERVICE_FLUID_DB

def get_service_fluid_props(fluid_type, t_service, custom_data=None):
    if fluid_type == "Custom" and custom_data:
        T_arr = np.array([custom_data['t1'], custom_data['t2']])
        rho_arr = np.array([custom_data['rho1'], custom_data['rho2']])
        cp_arr = np.array([custom_data['cp1'], custom_data['cp2']])
        mu_arr = np.array([custom_data['mu1'], custom_data['mu2']]) * 0.001
        k_arr = np.array([custom_data['k1'], custom_data['k2']])
    else:
        db = SERVICE_FLUID_DB[fluid_type]
        T_arr = np.array(db["T"])
        rho_arr = np.array(db["rho"])
        cp_arr = np.array(db["cp"])
        mu_arr = np.array(db["mu"])
        k_arr = np.array(db["k"])
        
    f_rho = interp1d(T_arr, rho_arr, fill_value="extrapolate")
    f_cp = interp1d(T_arr, cp_arr, fill_value="extrapolate")
    f_mu = interp1d(T_arr, mu_arr, fill_value="extrapolate")
    f_k = interp1d(T_arr, k_arr, fill_value="extrapolate")

    return {
        "rho": float(f_rho(t_service)),
        "cp": float(f_cp(t_service)),
        "mu": float(f_mu(t_service)),
        "k": float(f_k(t_service))
    }
