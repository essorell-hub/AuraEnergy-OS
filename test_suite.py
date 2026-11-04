"""
AuraEnergy OS - Comprehensive Automated Test Suite (test_suite.py)
Validates:
 1. Reference 600 kWp Utility PV Plant:
    - Performance Ratio (PR %) strictly between 80.0% and 85.5% (IEC 61724 compliant)
    - Specific yield > 1,000 kWh/kWp/year in CZ climate
    - Real LCOE between 0.80 and 2.50 CZK/kWh with Fisher equation check (LCOE real <= LCOE nominal)
    - 25-year NPV positive with 60% debt financing
 2. Monte Carlo Risk Distribution (1,200 iterations):
    - Monotonic quantiles: P10 < P50 < P90
    - Probability of positive NPV > 70%
 3. Grid Interconnection (PCC) Boundary & Stress Tests (PNE 33 3430-1 / EN 50160):
    - Low impedance / short distance: Delta U <= 2.0% -> APPROVE_STANDARD
    - Marginal boundary condition: 2.0% < Delta U <= 3.0% -> APPROVE_WITH_QU (autonomous reactive power Q(U))
    - Severe network stress / weak grid: Delta U > 3.0% -> REJECT_GRID_REINFORCEMENT
 4. PDF / Executive Summary Data Integrity:
    - All simulation outputs checked for null / NaN / undefined values
 5. SQLite Project Database CRUD operations
 6. OTE / EPEX SPOT Market and BESS Arbitrage engine
"""

import math
import unittest
import numpy as np

from backend.models.database import MODULE_CATALOG, INVERTER_CATALOG, BATTERY_CATALOG, PRAGUE_CLIMATE
from backend.core.sam_energy_engine import simulate_sam_photovoltaic_system
from backend.core.sam_financial_engine import calculate_sam_financial_metrics, run_sam_monte_carlo_risk
from backend.core.grid_interconnection import analyze_grid_interconnection_pcc, simulate_8760_hourly_generation_and_sizing
from backend.core.sam_ghg_engine import calculate_ghg_lifecycle_analysis
from backend.core.sam_mv_engine import analyze_ipmvp_full_suite
from backend.core.project_db import init_db, save_project, list_projects, get_project, delete_project
from backend.core.market_spot import get_live_market_spot_data
from backend.core.battery_arbitrage import calculate_bess_arbitrage_and_degradation


class TestAuraEnergyOSCompleteSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def test_01_reference_600kwp_pv_and_pr_bounds(self):
        """KROK/FÁZE 6: 600 kWp FVE Reference Simulation & PR (80-85%)"""
        mod = MODULE_CATALOG[0] # JinkoSolar Tiger Neo TOPCon 580 W
        inv = INVERTER_CATALOG[0]  # Huawei SUN2000-100KTL-M2
        modules_count = int(round(600_000.0 / mod.rated_power_stc_w))

        sim = simulate_sam_photovoltaic_system(
            module=mod,
            inverter=inv,
            modules_count=modules_count,
            tilt_deg=35.0,
            azimuth_deg=180.0,
            climate=PRAGUE_CLIMATE
        )

        pr = sim["performance_ratio_pr_pct"]
        mwh = sim["annual_ac_generation_mwh"]
        spec_yield = sim["specific_yield_kwh_kwp"]

        print(f"\n[SUITE - 600 kWp] PR: {pr:.2f}% | Annual MWh: {mwh:.1f} | Spec Yield: {spec_yield:.0f} kWh/kWp")

        self.assertGreaterEqual(pr, 80.0, f"PR {pr}% is below 80.0%")
        self.assertLessEqual(pr, 85.5, f"PR {pr}% is above 85.5%")
        self.assertGreater(mwh, 600.0, "Generation should exceed 600 MWh")
        self.assertGreater(spec_yield, 1000.0, "Specific yield should exceed 1000 kWh/kWp")

    def test_02_financial_lcoe_and_fisher_equation(self):
        """KROK/FÁZE 6: LCOE benchmarks and Fisher equation consistency"""
        fin = calculate_sam_financial_metrics(
            installed_capex=480_000.0, # 12,000,000 CZK
            annual_om_cost_year1=4_800.0,
            annual_generation_mwh_year1=733.0,
            electricity_tariff_eur_mwh=160.0,
            export_feedin_tariff_eur_mwh=65.0,
            debt_fraction_pct=60.0
        )

        lcoe_nom_czk = (fin["lcoe_nominal_eur_mwh"] * 25.0) / 1000.0
        lcoe_real_czk = (fin["lcoe_real_eur_mwh"] * 25.0) / 1000.0
        npv_czk = fin["npv_eur"] * 25.0
        irr = fin["irr_pct"]

        print(f"[SUITE - Finance] LCOE Nom: {lcoe_nom_czk:.2f} CZK/kWh | LCOE Real: {lcoe_real_czk:.2f} CZK/kWh | NPV: {npv_czk:,.0f} CZK | IRR: {irr:.2f}%")

        self.assertGreater(lcoe_real_czk, 0.80)
        self.assertLess(lcoe_real_czk, 2.50)
        self.assertLessEqual(lcoe_real_czk, lcoe_nom_czk, "Fisher equation violation: Real LCOE must be <= Nominal LCOE")
        self.assertGreater(npv_czk, 0, "NPV must be positive")

    def test_03_monte_carlo_distribution_1200_iter(self):
        """KROK/FÁZE 6: 1,200 Iterations Monte Carlo Risk Distribution P10 < P50 < P90"""
        mc = run_sam_monte_carlo_risk(
            installed_capex=100_000.0,
            annual_om_cost=1_500.0,
            annual_generation_mwh=115.0,
            electricity_tariff_eur_mwh=160.0,
            iterations=1200
        )

        p10 = mc["npv_p10_conservative_eur"]
        p50 = mc["npv_p50_median_eur"]
        p90 = mc["npv_p90_optimistic_eur"]
        prob = mc["probability_of_positive_npv_pct"]

        print(f"[SUITE - Monte Carlo] P10: {p10:,.0f} € | P50: {p50:,.0f} € | P90: {p90:,.0f} € | P(NPV>0): {prob:.1f}%")

        self.assertEqual(mc["iterations"], 1200)
        self.assertLess(p10, p50, "P10 must be strictly less than P50")
        self.assertLess(p50, p90, "P50 must be strictly less than P90")
        self.assertGreater(prob, 70.0, "Probability of positive NPV should be > 70%")

    def test_04_grid_pcc_boundary_and_qu_regulation(self):
        """KROK/FÁZE 6: PCC Voltage Rise (Delta U) and Autonomous Q(U) Logic"""
        # 1. Normal state: Delta U <= 2.0%
        res_ok = analyze_grid_interconnection_pcc(installed_ac_power_kw=100.0, distance_to_substation_m=120.0, cable_type="cu_150", transformer_capacity_kva=630.0)
        self.assertLessEqual(res_ok["voltage_rise_pct"], 2.0)
        self.assertEqual(res_ok["decision_code"], "APPROVE_STANDARD")
        self.assertFalse(res_ok["qu_regulation_required"])

        # 2. Limit boundary condition triggering Q(U)
        res_qu = analyze_grid_interconnection_pcc(installed_ac_power_kw=100.0, distance_to_substation_m=180.0, cable_type="al_150", transformer_capacity_kva=630.0)
        self.assertGreater(res_qu["voltage_rise_pct"], 2.0)
        self.assertLessEqual(res_qu["voltage_rise_pct"], 3.0)
        self.assertEqual(res_qu["decision_code"], "APPROVE_WITH_QU")
        self.assertTrue(res_qu["qu_regulation_required"])

        # 3. Severe overvoltage condition triggering Rejection
        res_rej = analyze_grid_interconnection_pcc(installed_ac_power_kw=300.0, distance_to_substation_m=500.0, cable_type="al_150", transformer_capacity_kva=250.0)
        self.assertGreater(res_rej["voltage_rise_pct"], 3.0)
        self.assertEqual(res_rej["decision_code"], "REJECT_GRID_REINFORCEMENT")

    def test_05_pdf_executive_summary_data_integrity(self):
        """KROK/FÁZE 6: Check that all executive summary fields are valid numbers (no NaN / None / inf)"""
        mod = MODULE_CATALOG[0]
        inv = INVERTER_CATALOG[0]
        sim = simulate_sam_photovoltaic_system(mod, inv, modules_count=172, climate=PRAGUE_CLIMATE)
        fin = calculate_sam_financial_metrics(installed_capex=78000.0, annual_om_cost_year1=950.0, annual_generation_mwh_year1=sim["annual_ac_generation_mwh"], electricity_tariff_eur_mwh=165.0)
        grid = analyze_grid_interconnection_pcc(installed_ac_power_kw=100.0, distance_to_substation_m=180.0)
        ghg = calculate_ghg_lifecycle_analysis(annual_clean_generation_mwh=sim["annual_ac_generation_mwh"])

        critical_values = [
            sim["annual_ac_generation_mwh"],
            sim["performance_ratio_pr_pct"],
            fin["npv_eur"],
            fin["lcoe_real_eur_mwh"],
            grid["voltage_rise_pct"],
            ghg["annual_net_reduction_tco2"]
        ]

        for val in critical_values:
            self.assertIsNotNone(val)
            self.assertFalse(math.isnan(val), f"Executive summary value {val} is NaN!")
            self.assertFalse(math.isinf(val), f"Executive summary value {val} is infinite!")

    def test_06_database_crud_lifecycle(self):
        """KROK/FÁZE 7: SQLite Project Database CRUD operations"""
        test_id = "proj_test_automated_001"
        save_project({
            "id": test_id,
            "name": "Automatizovaný Test FVE 100 kWp",
            "location": "Ostrava",
            "system_size_kw": 100.0,
            "capex_total_czk": 2200000.0,
            "params": {"tilt": 35, "cable": "cu_150"}
        })

        proj = get_project(test_id)
        self.assertIsNotNone(proj)
        self.assertEqual(proj["name"], "Automatizovaný Test FVE 100 kWp")
        self.assertEqual(proj["params"]["cable"], "cu_150")

        # Delete project
        deleted = delete_project(test_id)
        self.assertTrue(deleted)
        self.assertIsNone(get_project(test_id))

    def test_07_spot_market_and_bess_arbitrage(self):
        """KROK/FÁZE 8: Spot OTE 24h curve and BESS arbitrage schedule"""
        spot = get_live_market_spot_data()
        self.assertEqual(len(spot["hourly_prices"]), 24)
        self.assertGreater(spot["metrics"]["max_spread_eur_mwh"], 20.0)
        self.assertGreater(len(spot["optimal_bess_schedule"]["charge_hours"]), 0)
        self.assertGreater(len(spot["optimal_bess_schedule"]["discharge_hours"]), 0)

        # BESS Arbitrage calculation
        bess = calculate_bess_arbitrage_and_degradation(battery_capacity_kwh=100.0, battery_power_kw=50.0, avg_price_spread_eur_mwh=spot["metrics"]["max_spread_eur_mwh"])
        self.assertGreater(bess["total_annual_revenue_year1_eur"], 1000.0)
        self.assertGreater(bess["simple_payback_years"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
