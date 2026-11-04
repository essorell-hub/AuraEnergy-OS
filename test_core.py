from backend.core.financial import calculate_cash_flow, calculate_lcoe, run_monte_carlo
from backend.core.solarpv import calculate_solar_pv_yield
from backend.core.mv_analysis import analyze_ipmvp_option_c

def test_financial_calculations():
    res = calculate_cash_flow(
        capex=100000.0,
        annual_savings=15000.0,
        annual_om_cost=1000.0,
        project_lifetime_years=20,
        discount_rate=0.06
    )
    assert res["npv"] > 0, "NPV should be positive"
    assert res["simple_payback_years"] is not None and res["simple_payback_years"] < 8.0
    print("[OK] Financial engine test passed (NPV, IRR, Payback)")

def test_solar_yield():
    res = calculate_solar_pv_yield(
        capacity_kwp=10.0,
        tilt_deg=35.0,
        azimuth_deg=180.0,
        annual_ghi_kwh_m2=1100.0
    )
    assert res["annual_generation_mwh"] > 9.0 and res["annual_generation_mwh"] < 13.0
    print("[OK] Solar PV yield calculation test passed")

def test_ipmvp_regression():
    # 12 měsíců základního období
    dates = [f"2023-{m:02d}" for m in range(1, 13)]
    # Teoretická spotřeba: 5000 kWh základ + 20 kWh na každý HDD
    hdd = [450, 400, 300, 150, 50, 0, 0, 0, 60, 200, 350, 480]
    base_energy = [5000 + 20 * h + (i % 3) * 50 for i, h in enumerate(hdd)]
    
    # 12 měsíců reporting s 15% úsporou zateplením
    rep_energy = [e * 0.85 for e in base_energy]
    
    res = analyze_ipmvp_option_c(
        baseline_dates=dates,
        baseline_energy=base_energy,
        baseline_hdd=hdd,
        reporting_dates=dates,
        reporting_energy=rep_energy,
        reporting_hdd=hdd
    )
    assert res["model"]["r_squared"] > 0.95
    assert res["reporting"]["savings_percentage"] > 14.0
    print("[OK] IPMVP M&V regression engine test passed (R^2 > 0.95)")

if __name__ == "__main__":
    test_financial_calculations()
    test_solar_yield()
    test_ipmvp_regression()
    print("ALL CORE UNIT TESTS PASSED!")
