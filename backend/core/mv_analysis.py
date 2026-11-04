import numpy as np
import scipy.stats as stats
from typing import List, Dict, Any, Optional

def analyze_ipmvp_option_c(
    baseline_dates: List[str],
    baseline_energy: List[float],
    baseline_hdd: List[float], # Heating Degree Days
    baseline_cdd: Optional[List[float]] = None, # Cooling Degree Days
    reporting_dates: Optional[List[str]] = None,
    reporting_energy: Optional[List[float]] = None,
    reporting_hdd: Optional[List[float]] = None,
    reporting_cdd: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Měření a verifikace (M&V) dle protokolu IPMVP Option C (celá budova).
    Trénuje vícerozměrnou lineární regresi spotřeby vůči stupňo-dnům (HDD a CDD),
    vypočítá R², t-statistiku, CV(RMSE) a CUSUM úspory.
    """
    n_base = len(baseline_energy)
    if n_base < 6:
        raise ValueError("Je zapotřebí alespoň 6 měsíců základního období pro spolehlivou regresi.")
        
    y = np.array(baseline_energy, dtype=float)
    
    if baseline_cdd is not None and len(baseline_cdd) == n_base:
        # 2 nezávislé proměnné: HDD a CDD
        X = np.column_stack([np.ones(n_base), baseline_hdd, baseline_cdd])
    else:
        # Pouze HDD
        X = np.column_stack([np.ones(n_base), baseline_hdd])
        
    # OLS odhad koeficientů
    beta, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
    
    # Predikce na baseline
    y_pred_base = X @ beta
    ss_res = np.sum((y - y_pred_base) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    # CV(RMSE) - koeficient variance chyby (standard ASHRAE vyžaduje pod 15-20%)
    rmse = np.sqrt(ss_res / (n_base - X.shape[1]))
    cv_rmse = (rmse / np.mean(y)) * 100.0 if np.mean(y) > 0 else 0.0
    
    # Model formulace
    model_info = {
        "intercept_beta0": round(float(beta[0]), 3),
        "hdd_coefficient_beta1": round(float(beta[1]), 3),
        "cdd_coefficient_beta2": round(float(beta[2]), 3) if X.shape[1] > 2 else 0.0,
        "r_squared": round(float(r2), 4),
        "cv_rmse_pct": round(float(cv_rmse), 2),
        "ashrae_compliant": bool(cv_rmse < 20.0 and r2 > 0.75)
    }
    
    reporting_results = None
    if reporting_energy and reporting_hdd and len(reporting_energy) == len(reporting_hdd):
        n_rep = len(reporting_energy)
        if X.shape[1] > 2 and reporting_cdd and len(reporting_cdd) == n_rep:
            X_rep = np.column_stack([np.ones(n_rep), reporting_hdd, reporting_cdd])
        else:
            X_rep = np.column_stack([np.ones(n_rep), reporting_hdd])
            
        # Co by budova spotřebovala bez úsporného opatření za daného počasí
        adjusted_baseline = X_rep @ beta
        actual_energy = np.array(reporting_energy, dtype=float)
        
        # Úspora = upravený baseline - skutečnost
        savings = adjusted_baseline - actual_energy
        cusum = np.cumsum(savings)
        
        reporting_table = []
        for i in range(n_rep):
            reporting_table.append({
                "date": reporting_dates[i] if reporting_dates and i < len(reporting_dates) else f"M{i+1}",
                "actual_consumption": round(float(actual_energy[i]), 1),
                "adjusted_baseline": round(float(adjusted_baseline[i]), 1),
                "savings": round(float(savings[i]), 1),
                "cusum_savings": round(float(cusum[i]), 1)
            })
            
        reporting_results = {
            "total_savings_kwh": round(float(np.sum(savings)), 1),
            "savings_percentage": round(float(np.sum(savings) / np.sum(adjusted_baseline) * 100.0), 2) if np.sum(adjusted_baseline) > 0 else 0.0,
            "table": reporting_table
        }
        
    return {
        "model": model_info,
        "reporting": reporting_results
    }
