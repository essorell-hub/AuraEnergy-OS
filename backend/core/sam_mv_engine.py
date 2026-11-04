"""
IPMVP-Compliant Measurement and Verification (M&V) Module.
Options: Option C (Whole Facility Regression Analysis)
Features:
- Weather-normalized multivariable OLS regression (HDD & CDD)
- Statistical validation: R2, Adjusted R2, CV(RMSE), NMBE (ASHRAE Guideline 14 standards)
- CUSUM (Cumulative Sum of Differences) savings verification
- Load Duration Curve (LDC) generation.
"""
import numpy as np
from typing import Dict, Any, List, Optional

def analyze_ipmvp_full_suite(
    baseline_dates: List[str],
    baseline_energy_kwh: List[float],
    baseline_hdd: List[float],
    baseline_cdd: Optional[List[float]] = None,
    reporting_dates: Optional[List[str]] = None,
    reporting_energy_kwh: Optional[List[float]] = None,
    reporting_hdd: Optional[List[float]] = None,
    reporting_cdd: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Executes full IPMVP Option C analysis compliant with EVO (Efficiency Valuation Organization).
    """
    n = len(baseline_energy_kwh)
    if n < 6:
        raise ValueError("Minimum 6 baseline monthly points required for regression.")
        
    y = np.array(baseline_energy_kwh, dtype=float)
    
    if baseline_cdd and len(baseline_cdd) == n:
        X = np.column_stack([np.ones(n), baseline_hdd, baseline_cdd])
    else:
        X = np.column_stack([np.ones(n), baseline_hdd])
        
    # Ordinary Least Squares regression
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    y_pred = X @ beta
    
    residuals = y - y_pred
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    p = X.shape[1] - 1
    adj_r2 = 1.0 - (1.0 - r2) * ((n - 1) / (n - p - 1)) if (n - p - 1) > 0 else r2
    
    # ASHRAE Guideline 14 Criteria:
    # CV(RMSE) = (sqrt(ss_res / (n - p - 1)) / y_mean) * 100% (Must be < 15% for monthly data)
    # NMBE = (sum(residuals) / ((n - p - 1) * y_mean)) * 100% (Must be within +/- 5%)
    y_mean = np.mean(y)
    rmse = np.sqrt(ss_res / max(1, n - p - 1))
    cv_rmse_pct = (rmse / y_mean) * 100.0 if y_mean > 0 else 0.0
    nmbe_pct = (np.sum(residuals) / (max(1, n - p - 1) * y_mean)) * 100.0 if y_mean > 0 else 0.0
    
    ashrae_compliant = bool(r2 >= 0.75 and cv_rmse_pct <= 15.0 and abs(nmbe_pct) <= 5.0)

    # Load Duration Curve (LDC) calculation: Sort baseline descending
    sorted_baseline = sorted(baseline_energy_kwh, reverse=True)
    load_duration_curve = [
        {"percentile_pct": round((i / max(1, n - 1)) * 100.0, 1), "energy_kwh": round(val, 1)}
        for i, val in enumerate(sorted_baseline)
    ]

    # Reporting period verification & CUSUM
    reporting_results = None
    if reporting_energy_kwh and reporting_hdd:
        n_rep = len(reporting_energy_kwh)
        if X.shape[1] > 2 and reporting_cdd and len(reporting_cdd) == n_rep:
            X_rep = np.column_stack([np.ones(n_rep), reporting_hdd, reporting_cdd])
        else:
            X_rep = np.column_stack([np.ones(n_rep), reporting_hdd])
            
        adjusted_baseline = X_rep @ beta
        actual = np.array(reporting_energy_kwh, dtype=float)
        monthly_savings = adjusted_baseline - actual
        cusum_savings = np.cumsum(monthly_savings)
        
        table = []
        for i in range(n_rep):
            table.append({
                "period": reporting_dates[i] if reporting_dates and i < len(reporting_dates) else f"M{i+1}",
                "adjusted_baseline_kwh": round(float(adjusted_baseline[i]), 1),
                "actual_consumption_kwh": round(float(actual[i]), 1),
                "verified_savings_kwh": round(float(monthly_savings[i]), 1),
                "cusum_savings_kwh": round(float(cusum_savings[i]), 1)
            })
            
        total_sav = float(np.sum(monthly_savings))
        total_adj = float(np.sum(adjusted_baseline))
        
        reporting_results = {
            "total_verified_savings_kwh": round(total_sav, 1),
            "savings_percentage": round((total_sav / total_adj * 100.0), 2) if total_adj > 0 else 0.0,
            "table": table
        }

    return {
        "model_statistics": {
            "r_squared": round(float(r2), 4),
            "adjusted_r_squared": round(float(adj_r2), 4),
            "cv_rmse_pct": round(float(cv_rmse_pct), 2),
            "nmbe_pct": round(float(nmbe_pct), 2),
            "ashrae_guideline_14_compliant": ashrae_compliant,
            "intercept_beta0": round(float(beta[0]), 2),
            "hdd_coefficient_beta1": round(float(beta[1]), 2),
            "cdd_coefficient_beta2": round(float(beta[2]), 2) if X.shape[1] > 2 else 0.0
        },
        "load_duration_curve": load_duration_curve,
        "reporting_verification": reporting_results
    }
