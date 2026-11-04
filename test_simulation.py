"""
AuraEnergy OS - Verification and Automated Validation Suite (KROK 6)
Validates:
 1. 600 kWp Utility PV Reference Simulation:
    - PR % within standard IEC 61724 bounds (80.0% - 85.5%)
    - Real LCOE within standard benchmarks (0.80 - 2.50 CZK/kWh)
    - Fisher equation check: LCOE real <= LCOE nominal
 2. Grid Interconnection (PCC) Boundary & Stress Tests:
    - Normal connection (short cable, strong trafo) -> APPROVE_STANDARD (dU <= 2.0%)
    - Long cable borderline test -> APPROVE_WITH_QU (2.0% < dU <= 3.0%)
    - Severe stress test (long cable, weak trafo) -> REJECTED_OVERVOLTAGE (dU > 3.0%)
 3. Monte Carlo Risk Analysis:
    - 1,200 iterations consistency and monotonic quantiles P10 < P50 < P90
 4. Breaker Sizing & Reserved Capacity (RK):
    - IEC nominal current formula checks with safety multiplier
"""

import unittest
from backend.models.database import MODULE_CATALOG, INVERTER_CATALOG, PRAGUE_CLIMATE
from backend.models.schemas import PVModuleEntity, InverterEntity
from backend.core.sam_energy_engine import simulate_sam_photovoltaic_system
from backend.core.sam_financial_engine import calculate_sam_financial_metrics, run_sam_monte_carlo_risk
from backend.core.grid_interconnection import analyze_grid_interconnection_pcc, simulate_8760_hourly_generation_and_sizing


class TestAuraEnergyOSCalculations(unittest.TestCase):

    def test_01_reference_600kw_energy_and_pr(self):
        """KROK 6.1 & 6.2: 600 kW PV Energy output, PR % in 80-85.5% range"""
        mod = MODULE_CATALOG[0] # JinkoSolar Tiger Neo TOPCon 580 W
        inv = INVERTER_CATALOG[0]  # Huawei SUN2000-100KTL-M2
        
        # 600 kWp approx 1,034 modules
        modules_count = int(round(600_000.0 / mod.rated_power_stc_w))
        
        sim = simulate_sam_photovoltaic_system(
            module=mod,
            inverter=inv,
            modules_count=modules_count,
            tilt_deg=35.0,
            azimuth_deg=180.0,
            climate=PRAGUE_CLIMATE
        )
        
        pr_pct = sim["performance_ratio_pr_pct"]
        annual_mwh = sim["annual_ac_generation_mwh"]
        cuf_pct = sim["capacity_utilization_cuf_pct"]
        spec_yield = sim["specific_yield_kwh_kwp"]

        print(f"\n[TEST 600 kW Energy] Annual: {annual_mwh:.1f} MWh | PR: {pr_pct:.2f}% | CUF: {cuf_pct:.2f}% | SpecYield: {spec_yield:.0f} kWh/kWp")
        
        self.assertGreaterEqual(pr_pct, 80.0, f"PR {pr_pct}% must be >= 80.0%")
        self.assertLessEqual(pr_pct, 85.5, f"PR {pr_pct}% must be <= 85.5%")
        self.assertGreater(annual_mwh, 600.0, "600 kW system should generate > 600 MWh/year in CZ climate")
        self.assertGreater(spec_yield, 1000.0, "Specific yield in CZ should be > 1000 kWh/kWp")

    def test_02_reference_600kw_financial_and_lcoe(self):
        """KROK 6.2: Financial model and LCOE benchmarks"""
        mod = MODULE_CATALOG[0]
        inv = INVERTER_CATALOG[0]
        modules_count = int(round(600_000.0 / mod.rated_power_stc_w))
        
        sim = simulate_sam_photovoltaic_system(mod, inv, modules_count, climate=PRAGUE_CLIMATE)
        annual_mwh = sim["annual_ac_generation_mwh"]

        # CAPEX approx 12,000,000 CZK (20,000 CZK / kWp) -> in EUR ~ 480,000 EUR
        fin = calculate_sam_financial_metrics(
            installed_capex=480_000.0,
            annual_om_cost_year1=4_800.0,
            annual_generation_mwh_year1=annual_mwh,
            electricity_tariff_eur_mwh=160.0, # ~ 4.0 CZK/kWh
            export_feedin_tariff_eur_mwh=65.0,
            debt_fraction_pct=60.0
        )

        lcoe_nom_czk = (fin["lcoe_nominal_eur_mwh"] * 25.0) / 1000.0
        lcoe_real_czk = (fin["lcoe_real_eur_mwh"] * 25.0) / 1000.0
        npv_czk = fin["npv_eur"] * 25.0
        irr = fin["irr_pct"]

        print(f"[TEST 600 kW Financial] LCOE Nom: {lcoe_nom_czk:.2f} CZK/kWh | LCOE Real: {lcoe_real_czk:.2f} CZK/kWh | NPV: {npv_czk:,.0f} CZK | IRR: {irr:.2f}%")

        self.assertGreater(lcoe_real_czk, 0.80, "LCOE real should be >= 0.80 CZK/kWh")
        self.assertLess(lcoe_real_czk, 2.50, "LCOE real should be <= 2.50 CZK/kWh for commercial utility PV")
        self.assertLessEqual(lcoe_real_czk, lcoe_nom_czk, "Fisher equation: Real LCOE <= Nominal LCOE with positive inflation")
        self.assertGreater(npv_czk, 0, "Commercial PV project with 60% debt and self-consumption must have positive NPV")

    def test_03_grid_boundary_and_qu_logic(self):
        """KROK 6.3: Boundary & stress conditions for PCC network interconnection (PNE 33 3430-1)"""
        # Case A: Normal safe connection -> Delta U <= 2.0% -> UNCONDITIONAL APPROVAL
        res_safe = analyze_grid_interconnection_pcc(
            installed_ac_power_kw=100.0,
            distance_to_substation_m=120.0,
            cable_type="cu_150",
            transformer_capacity_kva=630.0
        )
        self.assertLessEqual(res_safe["voltage_rise_pct"], 2.0)
        self.assertEqual(res_safe["decision_code"], "APPROVE_STANDARD")
        self.assertFalse(res_safe["qu_regulation_required"])

        # Case B: Cable length triggering Q(U) regulation (2.0% < Delta U <= 3.0%)
        # With AYKY 150 (R=0.206 ohm/km), at 180m: Delta U = (100,000 * 0.206 * 0.180) / (400^2) * 100 = 2.32%
        res_qu = analyze_grid_interconnection_pcc(
            installed_ac_power_kw=100.0,
            distance_to_substation_m=180.0,
            cable_type="al_150",
            transformer_capacity_kva=630.0
        )
        print(f"[TEST PCC Q(U)] Delta U: {res_qu['voltage_rise_pct']:.2f}% | Decision: {res_qu['decision_code']}")
        self.assertGreater(res_qu["voltage_rise_pct"], 2.0)
        self.assertLessEqual(res_qu["voltage_rise_pct"], 3.0)
        self.assertEqual(res_qu["decision_code"], "APPROVE_WITH_QU")
        self.assertTrue(res_qu["qu_regulation_required"])

        # Case C: Extreme stress test (weak trafo, long Al cable) -> REJECT_GRID_REINFORCEMENT
        res_rejected = analyze_grid_interconnection_pcc(
            installed_ac_power_kw=300.0,
            distance_to_substation_m=500.0,
            cable_type="al_150",
            transformer_capacity_kva=250.0
        )
        print(f"[TEST PCC Reject] Delta U: {res_rejected['voltage_rise_pct']:.2f}% | Decision: {res_rejected['decision_code']}")
        self.assertGreater(res_rejected["voltage_rise_pct"], 3.0)
        self.assertEqual(res_rejected["decision_code"], "REJECT_GRID_REINFORCEMENT")

    def test_04_monte_carlo_distribution(self):
        """KROK 6.2: Monte Carlo 1,200 iterations statistical consistency"""
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

        print(f"[TEST Monte Carlo] Iterations: {mc['iterations']} | P10: {p10:,.0f} EUR | P50: {p50:,.0f} EUR | P90: {p90:,.0f} EUR")
        self.assertEqual(mc["iterations"], 1200)
        self.assertLess(p10, p50, "P10 NPV must be strictly less than P50 NPV")
        self.assertLess(p50, p90, "P50 NPV must be strictly less than P90 NPV")

    def test_05_breaker_and_rk_sizing(self):
        """KROK 6.4: Breaker sizing and Reserved Capacity calculation"""
        sizing = simulate_8760_hourly_generation_and_sizing(installed_capacity_kwp=100.0, inverter_ac_power_kw=100.0)
        self.assertIn(sizing["recommended_main_breaker_a"], [160, 200])
        self.assertGreater(sizing["recommended_reserved_capacity_rk_kw"], 80.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
