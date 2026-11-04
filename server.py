import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from backend.models.database import MODULE_CATALOG, INVERTER_CATALOG, BATTERY_CATALOG, PRAGUE_CLIMATE, PROJECT_ARCHETYPES
from backend.core.sam_energy_engine import simulate_sam_photovoltaic_system
from backend.core.sam_financial_engine import calculate_sam_financial_metrics, run_sam_monte_carlo_risk
from backend.core.sam_ghg_engine import calculate_ghg_lifecycle_analysis
from backend.core.sam_mv_engine import analyze_ipmvp_full_suite
from backend.core.grid_interconnection import analyze_grid_interconnection_pcc, simulate_8760_hourly_generation_and_sizing
from backend.core.project_db import list_projects, get_project, save_project, delete_project
from backend.core.market_spot import get_live_market_spot_data
from backend.core.battery_arbitrage import calculate_bess_arbitrage_and_degradation
from backend.core.multi_tech_engine import simulate_wind_turbine_system, simulate_small_hydro_system, simulate_chp_cogeneration_system
from backend.core.vpp_mpc_engine import optimize_24h_day_ahead_mpc, simulate_ceps_vpp_ancillary_services
from backend.core.auth_rbac import authenticate_user, verify_jwt, list_tenant_users
from backend.core.iot_scada_engine import process_telemetry_packet, get_live_scada_status
from backend.core.ai_copilot_engine import generate_audit_copilot_commentary
from backend.core.residential_engine import generate_residential_8760_load_profile, calculate_residential_nzu_subsidy, simulate_residential_pv_economics
from backend.core.hardware_database import get_all_hardware, add_custom_component
from backend.core.gis_shading_engine import simulate_3d_shading_matrix
from backend.core.ppa_finance_engine import simulate_corporate_ppa_contract, calculate_advanced_debt_syndication
from backend.core.optimization_engine import run_multicriteria_pv_bess_optimization
from backend.core.live_data_engine import fetch_live_ote_day_ahead_prices, fetch_7day_weather_forecast
from backend.core.community_energy_engine import simulate_community_energy_sharing
from backend.core.cad_sld_generator import generate_dxf_single_line_diagram
from backend.core.audit_compliance_engine import evaluate_audit_compliance
from backend.core.bess_physics_degradation import simulate_bess_electrochemical_degradation
from backend.core.bifacial_optics_engine import simulate_bifacial_gain
from backend.core.grid_stability_iec60909 import calculate_iec60909_short_circuit_and_harmonics
from backend.core.sector_coupling_h2_p2h import simulate_green_hydrogen_production, simulate_power_to_heat_steam
from backend.core.intraday_svr_aggregator import simulate_ceps_svr_revenue, simulate_intraday_imbalance_mitigation
from backend.core.bim_cable_routing_engine import optimize_cables_and_generate_boq, generate_ifc_bim_stub
from backend.core.nis2_cybersecurity_engine import evaluate_nis2_cybersecurity_posture
from backend.core.retscreen_full_engine import calculate_retscreen_complete_feasibility

PORT = 8080
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")

class SamServerHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            index_path = os.path.join(FRONTEND_DIR, "index.html")
            if os.path.exists(index_path):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                with open(index_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
        elif parsed.path == "/user_onboarding.js":
            js_path = os.path.join(FRONTEND_DIR, "user_onboarding.js")
            if os.path.exists(js_path):
                self.send_response(200)
                self.send_header('Content-Type', 'application/javascript; charset=utf-8')
                self.end_headers()
                with open(js_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
        elif parsed.path == "/api/health":
            self._send_json({"status": "ok", "app": "AuraEnergy SAM OS Grid Pro", "version": "11.0.0"})
            return
        elif parsed.path == "/api/catalogs":
            self._send_json({
                "modules": [m.model_dump() for m in MODULE_CATALOG],
                "inverters": [i.model_dump() for i in INVERTER_CATALOG],
                "batteries": [b.model_dump() for b in BATTERY_CATALOG],
                "archetypes": [a.model_dump() for a in PROJECT_ARCHETYPES],
                "climate": PRAGUE_CLIMATE.model_dump()
            })
            return
        elif parsed.path == "/api/projects":
            self._send_json(list_projects())
            return
        elif parsed.path.startswith("/api/projects/"):
            pid = parsed.path.split("/api/projects/")[1]
            proj = get_project(pid)
            if proj:
                self._send_json(proj)
            else:
                self.send_error(404, "Project Not Found")
            return
        elif parsed.path == "/api/market/spot-prices":
            self._send_json(get_live_market_spot_data())
            return
        elif parsed.path == "/api/scada/live-status":
            self._send_json(get_live_scada_status())
            return
        elif parsed.path == "/api/auth/users":
            self._send_json(list_tenant_users("tenant_corp_01"))
            return
        elif parsed.path == "/api/hardware/catalog":
            cat = None
            if "?" in self.path:
                q = self.path.split("?")[1]
                for param in q.split("&"):
                    if param.startswith("category="):
                        cat = param.split("=")[1].upper()
            self._send_json(get_all_hardware(cat))
            return
            
        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        payload = json.loads(body.decode('utf-8')) if body else {}

        if parsed.path == "/api/wizard/simulate-full-project":
            mod_id = payload.get("module_id", "mod-topcon-580")
            inv_id = payload.get("inverter_id", "inv-huawei-100ktl")
            modules_count = int(payload.get("modules_count", 172))
            tilt = float(payload.get("tilt_deg", 35.0))
            azimuth = float(payload.get("azimuth_deg", 180.0))
            
            selected_mod = next((m for m in MODULE_CATALOG if m.id == mod_id), MODULE_CATALOG[0])
            selected_inv = next((i for i in INVERTER_CATALOG if i.id == inv_id), INVERTER_CATALOG[0])
            
            # 1. SAM Energetická simulace
            energy_sim = simulate_sam_photovoltaic_system(
                module=selected_mod,
                inverter=selected_inv,
                modules_count=modules_count,
                tilt_deg=tilt,
                azimuth_deg=azimuth,
                climate=PRAGUE_CLIMATE
            )
            
            # 2. Finanční pro-forma
            capex = float(payload.get("capex_eur", 78000.0))
            tariff = float(payload.get("electricity_tariff_eur_mwh", 165.0))
            self_cons = float(payload.get("self_consumption_pct", 65.0))
            om_annual = float(payload.get("annual_om_cost_eur", 950.0))
            
            fin = calculate_sam_financial_metrics(
                installed_capex=capex,
                annual_om_cost_year1=om_annual,
                annual_generation_mwh_year1=energy_sim["annual_ac_generation_mwh"],
                electricity_tariff_eur_mwh=tariff,
                self_consumption_pct=self_cons
            )
            
            risk = run_sam_monte_carlo_risk(
                installed_capex=capex,
                annual_om_cost=om_annual,
                annual_generation_mwh=energy_sim["annual_ac_generation_mwh"],
                electricity_tariff_eur_mwh=tariff,
                iterations=1200
            )
            
            ghg = calculate_ghg_lifecycle_analysis(
                annual_clean_generation_mwh=energy_sim["annual_ac_generation_mwh"]
            )

            # 3. Posouzení připojitelnosti k síti PCC dle PNE 33 3430-1
            dist_m = float(payload.get("distance_to_substation_m", 180.0))
            cable = payload.get("cable_type", "al_150")
            trafo_cap = float(payload.get("transformer_capacity_kva", 630.0))
            
            grid_check = analyze_grid_interconnection_pcc(
                installed_ac_power_kw=selected_inv.rated_ac_power_kw,
                pcc_voltage_v=400.0,
                transformer_capacity_kva=trafo_cap,
                distance_to_substation_m=dist_m,
                cable_type=cable
            )
            
            # 4. Hodinový 8760h TMY profil a dimenzování jističů / RK
            hourly_sim = simulate_8760_hourly_generation_and_sizing(
                installed_capacity_kwp=energy_sim["system_dc_capacity_kw"],
                inverter_ac_power_kw=selected_inv.rated_ac_power_kw,
                tilt_deg=tilt
            )
            
            # 5. Generování AI Copilot komentáře energetického auditora pro PDF zprávu
            audit_copilot = generate_audit_copilot_commentary(
                project_name=payload.get("project_name", "FVE Průmyslový Areál 100 kWp"),
                system_size_kw=energy_sim["system_dc_capacity_kw"],
                energy_sim=energy_sim,
                financial_analysis=fin,
                monte_carlo=risk,
                grid_interconnection=grid_check,
                ghg_lifecycle=ghg
            )

            self._send_json({
                "energy_simulation": energy_sim,
                "financial_analysis": fin,
                "monte_carlo_risk": risk,
                "ghg_lifecycle": ghg,
                "grid_interconnection": grid_check,
                "hourly_8760": hourly_sim,
                "audit_copilot": audit_copilot
            })
            return

        elif parsed.path == "/api/grid/pcc-check":
            ac_p = float(payload.get("installed_ac_power_kw", 100.0))
            dist_m = float(payload.get("distance_to_substation_m", 180.0))
            cable = payload.get("cable_type", "al_150")
            trafo_cap = float(payload.get("transformer_capacity_kva", 630.0))
            
            res = analyze_grid_interconnection_pcc(
                installed_ac_power_kw=ac_p,
                distance_to_substation_m=dist_m,
                cable_type=cable,
                transformer_capacity_kva=trafo_cap
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/bess/physics-degradation":
            cap = float(payload.get("nominal_capacity_kwh", 100.0))
            chem = payload.get("chemistry", "LFP")
            cycles = float(payload.get("daily_cycles", 1.2))
            soc = float(payload.get("avg_soc_pct", 55.0))
            dod = float(payload.get("avg_dod_pct", 80.0))
            c_rate = float(payload.get("avg_c_rate", 0.5))
            temp = float(payload.get("ambient_cell_temp_c", 25.0))
            years = int(payload.get("project_lifetime_years", 20))
            res = simulate_bess_electrochemical_degradation(
                nominal_capacity_kwh=cap, chemistry=chem, daily_cycles=cycles,
                avg_soc_pct=soc, avg_dod_pct=dod, avg_c_rate=c_rate,
                ambient_cell_temp_c=temp, project_lifetime_years=years
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/pv/bifacial-gain":
            kwp = float(payload.get("pv_capacity_kwp", 100.0))
            gen = float(payload.get("front_annual_generation_mwh", 110.0))
            albedo = payload.get("albedo_type", "GRASS")
            bf_fact = float(payload.get("bifaciality_factor", 0.80))
            h = float(payload.get("clearance_height_m", 1.2))
            pitch = float(payload.get("row_pitch_m", 6.0))
            tilt = float(payload.get("tilt_deg", 25.0))
            res = simulate_bifacial_gain(
                pv_capacity_kwp=kwp, front_annual_generation_mwh=gen, albedo_type=albedo,
                bifaciality_factor=bf_fact, clearance_height_m=h, row_pitch_m=pitch, tilt_deg=tilt
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/grid/iec60909-stability":
            un = float(payload.get("grid_voltage_v", 400.0))
            trafo = float(payload.get("transformer_apparent_power_kva", 630.0))
            uk = float(payload.get("transformer_uk_pct", 4.0))
            inv = float(payload.get("inverter_rated_power_kw", 250.0))
            cable_m = float(payload.get("cable_length_m", 60.0))
            csa = float(payload.get("cable_csa_mm2", 150.0))
            res = calculate_iec60909_short_circuit_and_harmonics(
                grid_voltage_v=un, transformer_apparent_power_kva=trafo, transformer_uk_pct=uk,
                inverter_rated_power_kw=inv, cable_length_m=cable_m, cable_csa_mm2=csa
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/hydrogen/simulate":
            surplus = float(payload.get("surplus_power_kwh_annual", 250000.0))
            cap = float(payload.get("electrolyzer_capacity_kw", 100.0))
            tech = payload.get("electrolyzer_tech", "PEM")
            res = simulate_green_hydrogen_production(surplus_power_kwh_annual=surplus, electrolyzer_capacity_kw=cap, electrolyzer_tech=tech)
            self._send_json(res)
            return

        elif parsed.path == "/api/power-to-heat/simulate":
            surplus = float(payload.get("surplus_power_kwh_annual", 300000.0))
            cop = float(payload.get("heat_pump_cop", 3.2))
            res = simulate_power_to_heat_steam(surplus_power_kwh_annual=surplus, heat_pump_cop=cop)
            self._send_json(res)
            return

        elif parsed.path == "/api/ceps/svr-flexibility":
            mw = float(payload.get("battery_power_mw", 2.0))
            mwh = float(payload.get("battery_capacity_mwh", 4.0))
            srv = payload.get("contracted_service", "aFRR")
            res = simulate_ceps_svr_revenue(battery_power_mw=mw, battery_capacity_mwh=mwh, contracted_service=srv)
            self._send_json(res)
            return

        elif parsed.path == "/api/cables/optimize-boq":
            pv_kwp = float(payload.get("pv_capacity_kwp", 100.0))
            inv_kw = float(payload.get("inverter_capacity_kw", 80.0))
            ac_len = float(payload.get("ac_cable_run_length_m", 65.0))
            cond = payload.get("preferred_ac_conductor", "AL")
            res = optimize_cables_and_generate_boq(pv_capacity_kwp=pv_kwp, inverter_capacity_kw=inv_kw, ac_cable_run_length_m=ac_len, preferred_ac_conductor=cond)
            self._send_json(res)
            return

        elif parsed.path == "/api/bim/export-ifc":
            pname = payload.get("project_name", "AuraEnergy Model")
            kwp = float(payload.get("pv_capacity_kwp", 100.0))
            ifc_content = generate_ifc_bim_stub(pname, kwp)
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-step; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename="bim_{pname.replace(" ", "_")}.ifc"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(ifc_content.encode('utf-8'))
            return

        elif parsed.path == "/api/security/nis2-audit":
            proto = payload.get("scada_protocol", "MODBUS_TCP_TLS")
            mfa = bool(payload.get("mfa_enabled", True))
            fw = bool(payload.get("firmware_up_to_date", True))
            ot = bool(payload.get("air_gapped_ot_network", True))
            res = evaluate_nis2_cybersecurity_posture(scada_protocol=proto, mfa_enabled=mfa, firmware_up_to_date=fw, air_gapped_ot_network=ot)
            self._send_json(res)
            return

        elif parsed.path == "/api/retscreen/full-feasibility":
            ftype = payload.get("facility_type", "Commercial - Office")
            area = float(payload.get("facility_gross_floor_area_m2", 4500.0))
            hours = float(payload.get("annual_operating_hours", 3200.0))
            loc = payload.get("climate_location", "Praha, CZ (50.08°N, 14.43°E)")
            cdd = float(payload.get("cooling_degree_days", 180.0))
            hdd = float(payload.get("heating_degree_days", 3100.0))

            b_elec_rate = float(payload.get("base_electricity_rate_eur_kwh", 0.165))
            b_heat_rate = float(payload.get("base_heating_fuel_rate_eur_kwh", 0.085))
            b_elec_mwh = float(payload.get("base_annual_electricity_mwh", 650.0))
            b_heat_mwh = float(payload.get("base_annual_heating_mwh", 420.0))

            pv_gen = float(payload.get("proposed_pv_generation_mwh", 125.0))
            pv_self = float(payload.get("proposed_pv_self_consumption_pct", 75.0))
            export_tariff = float(payload.get("proposed_surplus_export_tariff_eur_kwh", 0.055))
            ee_save = float(payload.get("proposed_energy_efficiency_savings_pct", 18.0))

            c_feas = float(payload.get("cost_feasibility_study_eur", 3500.0))
            c_dev = float(payload.get("cost_development_permits_eur", 4500.0))
            c_eng = float(payload.get("cost_engineering_design_eur", 5800.0))
            c_equip = float(payload.get("cost_equipment_pv_bess_eur", 65000.0))
            c_bos = float(payload.get("cost_balance_of_system_eur", 12000.0))
            c_inst = float(payload.get("cost_installation_labor_eur", 11500.0))
            c_cont = float(payload.get("cost_contingency_reserve_eur", 4000.0))
            om_fixed = float(payload.get("annual_om_fixed_eur", 1200.0))

            infl = float(payload.get("inflation_rate_pct", 2.5))
            disc = float(payload.get("discount_rate_pct", 6.0))
            debt_rat = float(payload.get("debt_ratio_pct", 70.0))
            debt_int = float(payload.get("debt_interest_rate_pct", 5.2))
            debt_t = int(payload.get("debt_term_years", 15))
            tax_r = float(payload.get("income_tax_rate_pct", 21.0))
            depr_y = int(payload.get("depreciation_years", 10))

            res = calculate_retscreen_complete_feasibility(
                facility_type=ftype,
                facility_gross_floor_area_m2=area,
                annual_operating_hours=hours,
                climate_location=loc,
                cooling_degree_days=cdd,
                heating_degree_days=hdd,
                base_electricity_rate_eur_kwh=b_elec_rate,
                base_heating_fuel_rate_eur_kwh=b_heat_rate,
                base_annual_electricity_mwh=b_elec_mwh,
                base_annual_heating_mwh=b_heat_mwh,
                proposed_pv_generation_mwh=pv_gen,
                proposed_pv_self_consumption_pct=pv_self,
                proposed_surplus_export_tariff_eur_kwh=export_tariff,
                proposed_energy_efficiency_savings_pct=ee_save,
                cost_feasibility_study_eur=c_feas,
                cost_development_permits_eur=c_dev,
                cost_engineering_design_eur=c_eng,
                cost_equipment_pv_bess_eur=c_equip,
                cost_balance_of_system_eur=c_bos,
                cost_installation_labor_eur=c_inst,
                cost_contingency_reserve_eur=c_cont,
                annual_om_fixed_eur=om_fixed,
                inflation_rate_pct=infl,
                discount_rate_pct=disc,
                debt_ratio_pct=debt_rat,
                debt_interest_rate_pct=debt_int,
                debt_term_years=debt_t,
                income_tax_rate_pct=tax_r,
                depreciation_years=depr_y
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/mv/ipmvp-c-verify":
            dates = payload.get("baseline_dates", [])
            base_e = payload.get("baseline_energy_kwh", [])
            base_hdd = payload.get("baseline_hdd", [])
            base_cdd = payload.get("baseline_cdd", None)
            rep_dates = payload.get("reporting_dates", None)
            rep_e = payload.get("reporting_energy_kwh", None)
            rep_hdd = payload.get("reporting_hdd", None)
            
            res = analyze_ipmvp_full_suite(
                baseline_dates=dates,
                baseline_energy_kwh=base_e,
                baseline_hdd=base_hdd,
                baseline_cdd=base_cdd,
                reporting_dates=rep_dates,
                reporting_energy_kwh=rep_e,
                reporting_hdd=rep_hdd
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/bess/physics-degradation":
            cap = float(payload.get("nominal_capacity_kwh", 100.0))
            chem = payload.get("chemistry", "LFP")
            cycles = float(payload.get("daily_cycles", 1.2))
            soc = float(payload.get("avg_soc_pct", 55.0))
            dod = float(payload.get("avg_dod_pct", 80.0))
            c_rate = float(payload.get("avg_c_rate", 0.5))
            temp = float(payload.get("ambient_cell_temp_c", 25.0))
            years = int(payload.get("project_lifetime_years", 20))
            res = simulate_bess_electrochemical_degradation(
                nominal_capacity_kwh=cap, chemistry=chem, daily_cycles=cycles,
                avg_soc_pct=soc, avg_dod_pct=dod, avg_c_rate=c_rate,
                ambient_cell_temp_c=temp, project_lifetime_years=years
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/pv/bifacial-gain":
            kwp = float(payload.get("pv_capacity_kwp", 100.0))
            gen = float(payload.get("front_annual_generation_mwh", 110.0))
            albedo = payload.get("albedo_type", "GRASS")
            bf_fact = float(payload.get("bifaciality_factor", 0.80))
            h = float(payload.get("clearance_height_m", 1.2))
            pitch = float(payload.get("row_pitch_m", 6.0))
            tilt = float(payload.get("tilt_deg", 25.0))
            res = simulate_bifacial_gain(
                pv_capacity_kwp=kwp, front_annual_generation_mwh=gen, albedo_type=albedo,
                bifaciality_factor=bf_fact, clearance_height_m=h, row_pitch_m=pitch, tilt_deg=tilt
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/grid/iec60909-stability":
            un = float(payload.get("grid_voltage_v", 400.0))
            trafo = float(payload.get("transformer_apparent_power_kva", 630.0))
            uk = float(payload.get("transformer_uk_pct", 4.0))
            inv = float(payload.get("inverter_rated_power_kw", 250.0))
            cable_m = float(payload.get("cable_length_m", 60.0))
            csa = float(payload.get("cable_csa_mm2", 150.0))
            res = calculate_iec60909_short_circuit_and_harmonics(
                grid_voltage_v=un, transformer_apparent_power_kva=trafo, transformer_uk_pct=uk,
                inverter_rated_power_kw=inv, cable_length_m=cable_m, cable_csa_mm2=csa
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/hydrogen/simulate":
            surplus = float(payload.get("surplus_power_kwh_annual", 250000.0))
            cap = float(payload.get("electrolyzer_capacity_kw", 100.0))
            tech = payload.get("electrolyzer_tech", "PEM")
            res = simulate_green_hydrogen_production(surplus_power_kwh_annual=surplus, electrolyzer_capacity_kw=cap, electrolyzer_tech=tech)
            self._send_json(res)
            return

        elif parsed.path == "/api/power-to-heat/simulate":
            surplus = float(payload.get("surplus_power_kwh_annual", 300000.0))
            cop = float(payload.get("heat_pump_cop", 3.2))
            res = simulate_power_to_heat_steam(surplus_power_kwh_annual=surplus, heat_pump_cop=cop)
            self._send_json(res)
            return

        elif parsed.path == "/api/ceps/svr-flexibility":
            mw = float(payload.get("battery_power_mw", 2.0))
            mwh = float(payload.get("battery_capacity_mwh", 4.0))
            srv = payload.get("contracted_service", "aFRR")
            res = simulate_ceps_svr_revenue(battery_power_mw=mw, battery_capacity_mwh=mwh, contracted_service=srv)
            self._send_json(res)
            return

        elif parsed.path == "/api/cables/optimize-boq":
            pv_kwp = float(payload.get("pv_capacity_kwp", 100.0))
            inv_kw = float(payload.get("inverter_capacity_kw", 80.0))
            ac_len = float(payload.get("ac_cable_run_length_m", 65.0))
            cond = payload.get("preferred_ac_conductor", "AL")
            res = optimize_cables_and_generate_boq(pv_capacity_kwp=pv_kwp, inverter_capacity_kw=inv_kw, ac_cable_run_length_m=ac_len, preferred_ac_conductor=cond)
            self._send_json(res)
            return

        elif parsed.path == "/api/bim/export-ifc":
            pname = payload.get("project_name", "AuraEnergy Model")
            kwp = float(payload.get("pv_capacity_kwp", 100.0))
            ifc_content = generate_ifc_bim_stub(pname, kwp)
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-step; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename="bim_{pname.replace(" ", "_")}.ifc"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(ifc_content.encode('utf-8'))
            return

        elif parsed.path == "/api/security/nis2-audit":
            proto = payload.get("scada_protocol", "MODBUS_TCP_TLS")
            mfa = bool(payload.get("mfa_enabled", True))
            fw = bool(payload.get("firmware_up_to_date", True))
            ot = bool(payload.get("air_gapped_ot_network", True))
            res = evaluate_nis2_cybersecurity_posture(scada_protocol=proto, mfa_enabled=mfa, firmware_up_to_date=fw, air_gapped_ot_network=ot)
            self._send_json(res)
            return

        elif parsed.path == "/api/retscreen/full-feasibility":
            ftype = payload.get("facility_type", "Commercial - Office")
            area = float(payload.get("facility_gross_floor_area_m2", 4500.0))
            hours = float(payload.get("annual_operating_hours", 3200.0))
            loc = payload.get("climate_location", "Praha, CZ (50.08°N, 14.43°E)")
            cdd = float(payload.get("cooling_degree_days", 180.0))
            hdd = float(payload.get("heating_degree_days", 3100.0))

            b_elec_rate = float(payload.get("base_electricity_rate_eur_kwh", 0.165))
            b_heat_rate = float(payload.get("base_heating_fuel_rate_eur_kwh", 0.085))
            b_elec_mwh = float(payload.get("base_annual_electricity_mwh", 650.0))
            b_heat_mwh = float(payload.get("base_annual_heating_mwh", 420.0))

            pv_gen = float(payload.get("proposed_pv_generation_mwh", 125.0))
            pv_self = float(payload.get("proposed_pv_self_consumption_pct", 75.0))
            export_tariff = float(payload.get("proposed_surplus_export_tariff_eur_kwh", 0.055))
            ee_save = float(payload.get("proposed_energy_efficiency_savings_pct", 18.0))

            c_feas = float(payload.get("cost_feasibility_study_eur", 3500.0))
            c_dev = float(payload.get("cost_development_permits_eur", 4500.0))
            c_eng = float(payload.get("cost_engineering_design_eur", 5800.0))
            c_equip = float(payload.get("cost_equipment_pv_bess_eur", 65000.0))
            c_bos = float(payload.get("cost_balance_of_system_eur", 12000.0))
            c_inst = float(payload.get("cost_installation_labor_eur", 11500.0))
            c_cont = float(payload.get("cost_contingency_reserve_eur", 4000.0))
            om_fixed = float(payload.get("annual_om_fixed_eur", 1200.0))

            infl = float(payload.get("inflation_rate_pct", 2.5))
            disc = float(payload.get("discount_rate_pct", 6.0))
            debt_rat = float(payload.get("debt_ratio_pct", 70.0))
            debt_int = float(payload.get("debt_interest_rate_pct", 5.2))
            debt_t = int(payload.get("debt_term_years", 15))
            tax_r = float(payload.get("income_tax_rate_pct", 21.0))
            depr_y = int(payload.get("depreciation_years", 10))

            res = calculate_retscreen_complete_feasibility(
                facility_type=ftype,
                facility_gross_floor_area_m2=area,
                annual_operating_hours=hours,
                climate_location=loc,
                cooling_degree_days=cdd,
                heating_degree_days=hdd,
                base_electricity_rate_eur_kwh=b_elec_rate,
                base_heating_fuel_rate_eur_kwh=b_heat_rate,
                base_annual_electricity_mwh=b_elec_mwh,
                base_annual_heating_mwh=b_heat_mwh,
                proposed_pv_generation_mwh=pv_gen,
                proposed_pv_self_consumption_pct=pv_self,
                proposed_surplus_export_tariff_eur_kwh=export_tariff,
                proposed_energy_efficiency_savings_pct=ee_save,
                cost_feasibility_study_eur=c_feas,
                cost_development_permits_eur=c_dev,
                cost_engineering_design_eur=c_eng,
                cost_equipment_pv_bess_eur=c_equip,
                cost_balance_of_system_eur=c_bos,
                cost_installation_labor_eur=c_inst,
                cost_contingency_reserve_eur=c_cont,
                annual_om_fixed_eur=om_fixed,
                inflation_rate_pct=infl,
                discount_rate_pct=disc,
                debt_ratio_pct=debt_rat,
                debt_interest_rate_pct=debt_int,
                debt_term_years=debt_t,
                income_tax_rate_pct=tax_r,
                depreciation_years=depr_y
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/projects/save":
            save_res = save_project(payload)
            self._send_json(save_res)
            return

        elif parsed.path == "/api/projects/delete":
            pid = payload.get("id")
            success = delete_project(pid) if pid else False
            self._send_json({"status": "deleted" if success else "error", "id": pid})
            return

        elif parsed.path == "/api/market/bess-arbitrage":
            bat_kwh = float(payload.get("battery_capacity_kwh", 100.0))
            bat_kw = float(payload.get("battery_power_kw", 50.0))
            spread = float(payload.get("avg_price_spread_eur_mwh", 95.0))
            ps_savings = float(payload.get("peak_shaving_monthly_savings_eur", 350.0))
            bess_res = calculate_bess_arbitrage_and_degradation(
                battery_capacity_kwh=bat_kwh,
                battery_power_kw=bat_kw,
                avg_price_spread_eur_mwh=spread,
                peak_shaving_monthly_savings_eur=ps_savings
            )
            self._send_json(bess_res)
            return

        elif parsed.path == "/api/multitech/simulate":
            tech = payload.get("technology", "WIND_TURBINE")
            if tech == "WIND_TURBINE":
                res = simulate_wind_turbine_system(
                    turbine_rated_power_kw=float(payload.get("rated_power_kw", 2000.0)),
                    hub_height_m=float(payload.get("hub_height_m", 105.0)),
                    mean_wind_speed_at_hub_m_s=float(payload.get("mean_wind_speed_m_s", 6.8)),
                    turbines_count=int(payload.get("turbines_count", 1))
                )
            elif tech == "SMALL_HYDRO":
                res = simulate_small_hydro_system(
                    gross_head_m=float(payload.get("gross_head_m", 12.0)),
                    design_flow_m3_s=float(payload.get("design_flow_m3_s", 3.5))
                )
            elif tech == "CHP_COGENERATION":
                res = simulate_chp_cogeneration_system(
                    fuel_input_kw_th=float(payload.get("fuel_input_kw_th", 1000.0)),
                    electrical_efficiency_pct=float(payload.get("electrical_efficiency_pct", 42.0)),
                    thermal_efficiency_pct=float(payload.get("thermal_efficiency_pct", 48.0))
                )
            else:
                res = {"error": f"Unknown technology {tech}"}
            self._send_json(res)
            return

        elif parsed.path == "/api/bess/physics-degradation":
            cap = float(payload.get("nominal_capacity_kwh", 100.0))
            chem = payload.get("chemistry", "LFP")
            cycles = float(payload.get("daily_cycles", 1.2))
            soc = float(payload.get("avg_soc_pct", 55.0))
            dod = float(payload.get("avg_dod_pct", 80.0))
            c_rate = float(payload.get("avg_c_rate", 0.5))
            temp = float(payload.get("ambient_cell_temp_c", 25.0))
            years = int(payload.get("project_lifetime_years", 20))
            res = simulate_bess_electrochemical_degradation(
                nominal_capacity_kwh=cap, chemistry=chem, daily_cycles=cycles,
                avg_soc_pct=soc, avg_dod_pct=dod, avg_c_rate=c_rate,
                ambient_cell_temp_c=temp, project_lifetime_years=years
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/pv/bifacial-gain":
            kwp = float(payload.get("pv_capacity_kwp", 100.0))
            gen = float(payload.get("front_annual_generation_mwh", 110.0))
            albedo = payload.get("albedo_type", "GRASS")
            bf_fact = float(payload.get("bifaciality_factor", 0.80))
            h = float(payload.get("clearance_height_m", 1.2))
            pitch = float(payload.get("row_pitch_m", 6.0))
            tilt = float(payload.get("tilt_deg", 25.0))
            res = simulate_bifacial_gain(
                pv_capacity_kwp=kwp, front_annual_generation_mwh=gen, albedo_type=albedo,
                bifaciality_factor=bf_fact, clearance_height_m=h, row_pitch_m=pitch, tilt_deg=tilt
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/grid/iec60909-stability":
            un = float(payload.get("grid_voltage_v", 400.0))
            trafo = float(payload.get("transformer_apparent_power_kva", 630.0))
            uk = float(payload.get("transformer_uk_pct", 4.0))
            inv = float(payload.get("inverter_rated_power_kw", 250.0))
            cable_m = float(payload.get("cable_length_m", 60.0))
            csa = float(payload.get("cable_csa_mm2", 150.0))
            res = calculate_iec60909_short_circuit_and_harmonics(
                grid_voltage_v=un, transformer_apparent_power_kva=trafo, transformer_uk_pct=uk,
                inverter_rated_power_kw=inv, cable_length_m=cable_m, cable_csa_mm2=csa
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/hydrogen/simulate":
            surplus = float(payload.get("surplus_power_kwh_annual", 250000.0))
            cap = float(payload.get("electrolyzer_capacity_kw", 100.0))
            tech = payload.get("electrolyzer_tech", "PEM")
            res = simulate_green_hydrogen_production(surplus_power_kwh_annual=surplus, electrolyzer_capacity_kw=cap, electrolyzer_tech=tech)
            self._send_json(res)
            return

        elif parsed.path == "/api/power-to-heat/simulate":
            surplus = float(payload.get("surplus_power_kwh_annual", 300000.0))
            cop = float(payload.get("heat_pump_cop", 3.2))
            res = simulate_power_to_heat_steam(surplus_power_kwh_annual=surplus, heat_pump_cop=cop)
            self._send_json(res)
            return

        elif parsed.path == "/api/ceps/svr-flexibility":
            mw = float(payload.get("battery_power_mw", 2.0))
            mwh = float(payload.get("battery_capacity_mwh", 4.0))
            srv = payload.get("contracted_service", "aFRR")
            res = simulate_ceps_svr_revenue(battery_power_mw=mw, battery_capacity_mwh=mwh, contracted_service=srv)
            self._send_json(res)
            return

        elif parsed.path == "/api/cables/optimize-boq":
            pv_kwp = float(payload.get("pv_capacity_kwp", 100.0))
            inv_kw = float(payload.get("inverter_capacity_kw", 80.0))
            ac_len = float(payload.get("ac_cable_run_length_m", 65.0))
            cond = payload.get("preferred_ac_conductor", "AL")
            res = optimize_cables_and_generate_boq(pv_capacity_kwp=pv_kwp, inverter_capacity_kw=inv_kw, ac_cable_run_length_m=ac_len, preferred_ac_conductor=cond)
            self._send_json(res)
            return

        elif parsed.path == "/api/bim/export-ifc":
            pname = payload.get("project_name", "AuraEnergy Model")
            kwp = float(payload.get("pv_capacity_kwp", 100.0))
            ifc_content = generate_ifc_bim_stub(pname, kwp)
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-step; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename="bim_{pname.replace(" ", "_")}.ifc"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(ifc_content.encode('utf-8'))
            return

        elif parsed.path == "/api/security/nis2-audit":
            proto = payload.get("scada_protocol", "MODBUS_TCP_TLS")
            mfa = bool(payload.get("mfa_enabled", True))
            fw = bool(payload.get("firmware_up_to_date", True))
            ot = bool(payload.get("air_gapped_ot_network", True))
            res = evaluate_nis2_cybersecurity_posture(scada_protocol=proto, mfa_enabled=mfa, firmware_up_to_date=fw, air_gapped_ot_network=ot)
            self._send_json(res)
            return

        elif parsed.path == "/api/retscreen/full-feasibility":
            ftype = payload.get("facility_type", "Commercial - Office")
            area = float(payload.get("facility_gross_floor_area_m2", 4500.0))
            hours = float(payload.get("annual_operating_hours", 3200.0))
            loc = payload.get("climate_location", "Praha, CZ (50.08°N, 14.43°E)")
            cdd = float(payload.get("cooling_degree_days", 180.0))
            hdd = float(payload.get("heating_degree_days", 3100.0))

            b_elec_rate = float(payload.get("base_electricity_rate_eur_kwh", 0.165))
            b_heat_rate = float(payload.get("base_heating_fuel_rate_eur_kwh", 0.085))
            b_elec_mwh = float(payload.get("base_annual_electricity_mwh", 650.0))
            b_heat_mwh = float(payload.get("base_annual_heating_mwh", 420.0))

            pv_gen = float(payload.get("proposed_pv_generation_mwh", 125.0))
            pv_self = float(payload.get("proposed_pv_self_consumption_pct", 75.0))
            export_tariff = float(payload.get("proposed_surplus_export_tariff_eur_kwh", 0.055))
            ee_save = float(payload.get("proposed_energy_efficiency_savings_pct", 18.0))

            c_feas = float(payload.get("cost_feasibility_study_eur", 3500.0))
            c_dev = float(payload.get("cost_development_permits_eur", 4500.0))
            c_eng = float(payload.get("cost_engineering_design_eur", 5800.0))
            c_equip = float(payload.get("cost_equipment_pv_bess_eur", 65000.0))
            c_bos = float(payload.get("cost_balance_of_system_eur", 12000.0))
            c_inst = float(payload.get("cost_installation_labor_eur", 11500.0))
            c_cont = float(payload.get("cost_contingency_reserve_eur", 4000.0))
            om_fixed = float(payload.get("annual_om_fixed_eur", 1200.0))

            infl = float(payload.get("inflation_rate_pct", 2.5))
            disc = float(payload.get("discount_rate_pct", 6.0))
            debt_rat = float(payload.get("debt_ratio_pct", 70.0))
            debt_int = float(payload.get("debt_interest_rate_pct", 5.2))
            debt_t = int(payload.get("debt_term_years", 15))
            tax_r = float(payload.get("income_tax_rate_pct", 21.0))
            depr_y = int(payload.get("depreciation_years", 10))

            res = calculate_retscreen_complete_feasibility(
                facility_type=ftype,
                facility_gross_floor_area_m2=area,
                annual_operating_hours=hours,
                climate_location=loc,
                cooling_degree_days=cdd,
                heating_degree_days=hdd,
                base_electricity_rate_eur_kwh=b_elec_rate,
                base_heating_fuel_rate_eur_kwh=b_heat_rate,
                base_annual_electricity_mwh=b_elec_mwh,
                base_annual_heating_mwh=b_heat_mwh,
                proposed_pv_generation_mwh=pv_gen,
                proposed_pv_self_consumption_pct=pv_self,
                proposed_surplus_export_tariff_eur_kwh=export_tariff,
                proposed_energy_efficiency_savings_pct=ee_save,
                cost_feasibility_study_eur=c_feas,
                cost_development_permits_eur=c_dev,
                cost_engineering_design_eur=c_eng,
                cost_equipment_pv_bess_eur=c_equip,
                cost_balance_of_system_eur=c_bos,
                cost_installation_labor_eur=c_inst,
                cost_contingency_reserve_eur=c_cont,
                annual_om_fixed_eur=om_fixed,
                inflation_rate_pct=infl,
                discount_rate_pct=disc,
                debt_ratio_pct=debt_rat,
                debt_interest_rate_pct=debt_int,
                debt_term_years=debt_t,
                income_tax_rate_pct=tax_r,
                depreciation_years=depr_y
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/vpp/day-ahead-mpc":
            cap_kwh = float(payload.get("battery_capacity_kwh", 100.0))
            power_kw = float(payload.get("battery_power_kw", 50.0))
            spot = payload.get("spot_prices_eur_mwh", None)
            res = optimize_24h_day_ahead_mpc(battery_capacity_kwh=cap_kwh, battery_power_kw=power_kw, spot_prices_eur_mwh=spot)
            self._send_json(res)
            return

        elif parsed.path == "/api/bess/physics-degradation":
            cap = float(payload.get("nominal_capacity_kwh", 100.0))
            chem = payload.get("chemistry", "LFP")
            cycles = float(payload.get("daily_cycles", 1.2))
            soc = float(payload.get("avg_soc_pct", 55.0))
            dod = float(payload.get("avg_dod_pct", 80.0))
            c_rate = float(payload.get("avg_c_rate", 0.5))
            temp = float(payload.get("ambient_cell_temp_c", 25.0))
            years = int(payload.get("project_lifetime_years", 20))
            res = simulate_bess_electrochemical_degradation(
                nominal_capacity_kwh=cap, chemistry=chem, daily_cycles=cycles,
                avg_soc_pct=soc, avg_dod_pct=dod, avg_c_rate=c_rate,
                ambient_cell_temp_c=temp, project_lifetime_years=years
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/pv/bifacial-gain":
            kwp = float(payload.get("pv_capacity_kwp", 100.0))
            gen = float(payload.get("front_annual_generation_mwh", 110.0))
            albedo = payload.get("albedo_type", "GRASS")
            bf_fact = float(payload.get("bifaciality_factor", 0.80))
            h = float(payload.get("clearance_height_m", 1.2))
            pitch = float(payload.get("row_pitch_m", 6.0))
            tilt = float(payload.get("tilt_deg", 25.0))
            res = simulate_bifacial_gain(
                pv_capacity_kwp=kwp, front_annual_generation_mwh=gen, albedo_type=albedo,
                bifaciality_factor=bf_fact, clearance_height_m=h, row_pitch_m=pitch, tilt_deg=tilt
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/grid/iec60909-stability":
            un = float(payload.get("grid_voltage_v", 400.0))
            trafo = float(payload.get("transformer_apparent_power_kva", 630.0))
            uk = float(payload.get("transformer_uk_pct", 4.0))
            inv = float(payload.get("inverter_rated_power_kw", 250.0))
            cable_m = float(payload.get("cable_length_m", 60.0))
            csa = float(payload.get("cable_csa_mm2", 150.0))
            res = calculate_iec60909_short_circuit_and_harmonics(
                grid_voltage_v=un, transformer_apparent_power_kva=trafo, transformer_uk_pct=uk,
                inverter_rated_power_kw=inv, cable_length_m=cable_m, cable_csa_mm2=csa
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/hydrogen/simulate":
            surplus = float(payload.get("surplus_power_kwh_annual", 250000.0))
            cap = float(payload.get("electrolyzer_capacity_kw", 100.0))
            tech = payload.get("electrolyzer_tech", "PEM")
            res = simulate_green_hydrogen_production(surplus_power_kwh_annual=surplus, electrolyzer_capacity_kw=cap, electrolyzer_tech=tech)
            self._send_json(res)
            return

        elif parsed.path == "/api/power-to-heat/simulate":
            surplus = float(payload.get("surplus_power_kwh_annual", 300000.0))
            cop = float(payload.get("heat_pump_cop", 3.2))
            res = simulate_power_to_heat_steam(surplus_power_kwh_annual=surplus, heat_pump_cop=cop)
            self._send_json(res)
            return

        elif parsed.path == "/api/ceps/svr-flexibility":
            mw = float(payload.get("battery_power_mw", 2.0))
            mwh = float(payload.get("battery_capacity_mwh", 4.0))
            srv = payload.get("contracted_service", "aFRR")
            res = simulate_ceps_svr_revenue(battery_power_mw=mw, battery_capacity_mwh=mwh, contracted_service=srv)
            self._send_json(res)
            return

        elif parsed.path == "/api/cables/optimize-boq":
            pv_kwp = float(payload.get("pv_capacity_kwp", 100.0))
            inv_kw = float(payload.get("inverter_capacity_kw", 80.0))
            ac_len = float(payload.get("ac_cable_run_length_m", 65.0))
            cond = payload.get("preferred_ac_conductor", "AL")
            res = optimize_cables_and_generate_boq(pv_capacity_kwp=pv_kwp, inverter_capacity_kw=inv_kw, ac_cable_run_length_m=ac_len, preferred_ac_conductor=cond)
            self._send_json(res)
            return

        elif parsed.path == "/api/bim/export-ifc":
            pname = payload.get("project_name", "AuraEnergy Model")
            kwp = float(payload.get("pv_capacity_kwp", 100.0))
            ifc_content = generate_ifc_bim_stub(pname, kwp)
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-step; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename="bim_{pname.replace(" ", "_")}.ifc"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(ifc_content.encode('utf-8'))
            return

        elif parsed.path == "/api/security/nis2-audit":
            proto = payload.get("scada_protocol", "MODBUS_TCP_TLS")
            mfa = bool(payload.get("mfa_enabled", True))
            fw = bool(payload.get("firmware_up_to_date", True))
            ot = bool(payload.get("air_gapped_ot_network", True))
            res = evaluate_nis2_cybersecurity_posture(scada_protocol=proto, mfa_enabled=mfa, firmware_up_to_date=fw, air_gapped_ot_network=ot)
            self._send_json(res)
            return

        elif parsed.path == "/api/retscreen/full-feasibility":
            ftype = payload.get("facility_type", "Commercial - Office")
            area = float(payload.get("facility_gross_floor_area_m2", 4500.0))
            hours = float(payload.get("annual_operating_hours", 3200.0))
            loc = payload.get("climate_location", "Praha, CZ (50.08°N, 14.43°E)")
            cdd = float(payload.get("cooling_degree_days", 180.0))
            hdd = float(payload.get("heating_degree_days", 3100.0))

            b_elec_rate = float(payload.get("base_electricity_rate_eur_kwh", 0.165))
            b_heat_rate = float(payload.get("base_heating_fuel_rate_eur_kwh", 0.085))
            b_elec_mwh = float(payload.get("base_annual_electricity_mwh", 650.0))
            b_heat_mwh = float(payload.get("base_annual_heating_mwh", 420.0))

            pv_gen = float(payload.get("proposed_pv_generation_mwh", 125.0))
            pv_self = float(payload.get("proposed_pv_self_consumption_pct", 75.0))
            export_tariff = float(payload.get("proposed_surplus_export_tariff_eur_kwh", 0.055))
            ee_save = float(payload.get("proposed_energy_efficiency_savings_pct", 18.0))

            c_feas = float(payload.get("cost_feasibility_study_eur", 3500.0))
            c_dev = float(payload.get("cost_development_permits_eur", 4500.0))
            c_eng = float(payload.get("cost_engineering_design_eur", 5800.0))
            c_equip = float(payload.get("cost_equipment_pv_bess_eur", 65000.0))
            c_bos = float(payload.get("cost_balance_of_system_eur", 12000.0))
            c_inst = float(payload.get("cost_installation_labor_eur", 11500.0))
            c_cont = float(payload.get("cost_contingency_reserve_eur", 4000.0))
            om_fixed = float(payload.get("annual_om_fixed_eur", 1200.0))

            infl = float(payload.get("inflation_rate_pct", 2.5))
            disc = float(payload.get("discount_rate_pct", 6.0))
            debt_rat = float(payload.get("debt_ratio_pct", 70.0))
            debt_int = float(payload.get("debt_interest_rate_pct", 5.2))
            debt_t = int(payload.get("debt_term_years", 15))
            tax_r = float(payload.get("income_tax_rate_pct", 21.0))
            depr_y = int(payload.get("depreciation_years", 10))

            res = calculate_retscreen_complete_feasibility(
                facility_type=ftype,
                facility_gross_floor_area_m2=area,
                annual_operating_hours=hours,
                climate_location=loc,
                cooling_degree_days=cdd,
                heating_degree_days=hdd,
                base_electricity_rate_eur_kwh=b_elec_rate,
                base_heating_fuel_rate_eur_kwh=b_heat_rate,
                base_annual_electricity_mwh=b_elec_mwh,
                base_annual_heating_mwh=b_heat_mwh,
                proposed_pv_generation_mwh=pv_gen,
                proposed_pv_self_consumption_pct=pv_self,
                proposed_surplus_export_tariff_eur_kwh=export_tariff,
                proposed_energy_efficiency_savings_pct=ee_save,
                cost_feasibility_study_eur=c_feas,
                cost_development_permits_eur=c_dev,
                cost_engineering_design_eur=c_eng,
                cost_equipment_pv_bess_eur=c_equip,
                cost_balance_of_system_eur=c_bos,
                cost_installation_labor_eur=c_inst,
                cost_contingency_reserve_eur=c_cont,
                annual_om_fixed_eur=om_fixed,
                inflation_rate_pct=infl,
                discount_rate_pct=disc,
                debt_ratio_pct=debt_rat,
                debt_interest_rate_pct=debt_int,
                debt_term_years=debt_t,
                income_tax_rate_pct=tax_r,
                depreciation_years=depr_y
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/vpp/ceps-ancillary":
            flex_kw = float(payload.get("available_flexibility_kw", 100.0))
            srv = payload.get("service_type", "aFRR")
            res = simulate_ceps_vpp_ancillary_services(available_flexibility_kw=flex_kw, service_type=srv)
            self._send_json(res)
            return

        elif parsed.path == "/api/bess/physics-degradation":
            cap = float(payload.get("nominal_capacity_kwh", 100.0))
            chem = payload.get("chemistry", "LFP")
            cycles = float(payload.get("daily_cycles", 1.2))
            soc = float(payload.get("avg_soc_pct", 55.0))
            dod = float(payload.get("avg_dod_pct", 80.0))
            c_rate = float(payload.get("avg_c_rate", 0.5))
            temp = float(payload.get("ambient_cell_temp_c", 25.0))
            years = int(payload.get("project_lifetime_years", 20))
            res = simulate_bess_electrochemical_degradation(
                nominal_capacity_kwh=cap, chemistry=chem, daily_cycles=cycles,
                avg_soc_pct=soc, avg_dod_pct=dod, avg_c_rate=c_rate,
                ambient_cell_temp_c=temp, project_lifetime_years=years
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/pv/bifacial-gain":
            kwp = float(payload.get("pv_capacity_kwp", 100.0))
            gen = float(payload.get("front_annual_generation_mwh", 110.0))
            albedo = payload.get("albedo_type", "GRASS")
            bf_fact = float(payload.get("bifaciality_factor", 0.80))
            h = float(payload.get("clearance_height_m", 1.2))
            pitch = float(payload.get("row_pitch_m", 6.0))
            tilt = float(payload.get("tilt_deg", 25.0))
            res = simulate_bifacial_gain(
                pv_capacity_kwp=kwp, front_annual_generation_mwh=gen, albedo_type=albedo,
                bifaciality_factor=bf_fact, clearance_height_m=h, row_pitch_m=pitch, tilt_deg=tilt
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/grid/iec60909-stability":
            un = float(payload.get("grid_voltage_v", 400.0))
            trafo = float(payload.get("transformer_apparent_power_kva", 630.0))
            uk = float(payload.get("transformer_uk_pct", 4.0))
            inv = float(payload.get("inverter_rated_power_kw", 250.0))
            cable_m = float(payload.get("cable_length_m", 60.0))
            csa = float(payload.get("cable_csa_mm2", 150.0))
            res = calculate_iec60909_short_circuit_and_harmonics(
                grid_voltage_v=un, transformer_apparent_power_kva=trafo, transformer_uk_pct=uk,
                inverter_rated_power_kw=inv, cable_length_m=cable_m, cable_csa_mm2=csa
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/hydrogen/simulate":
            surplus = float(payload.get("surplus_power_kwh_annual", 250000.0))
            cap = float(payload.get("electrolyzer_capacity_kw", 100.0))
            tech = payload.get("electrolyzer_tech", "PEM")
            res = simulate_green_hydrogen_production(surplus_power_kwh_annual=surplus, electrolyzer_capacity_kw=cap, electrolyzer_tech=tech)
            self._send_json(res)
            return

        elif parsed.path == "/api/power-to-heat/simulate":
            surplus = float(payload.get("surplus_power_kwh_annual", 300000.0))
            cop = float(payload.get("heat_pump_cop", 3.2))
            res = simulate_power_to_heat_steam(surplus_power_kwh_annual=surplus, heat_pump_cop=cop)
            self._send_json(res)
            return

        elif parsed.path == "/api/ceps/svr-flexibility":
            mw = float(payload.get("battery_power_mw", 2.0))
            mwh = float(payload.get("battery_capacity_mwh", 4.0))
            srv = payload.get("contracted_service", "aFRR")
            res = simulate_ceps_svr_revenue(battery_power_mw=mw, battery_capacity_mwh=mwh, contracted_service=srv)
            self._send_json(res)
            return

        elif parsed.path == "/api/cables/optimize-boq":
            pv_kwp = float(payload.get("pv_capacity_kwp", 100.0))
            inv_kw = float(payload.get("inverter_capacity_kw", 80.0))
            ac_len = float(payload.get("ac_cable_run_length_m", 65.0))
            cond = payload.get("preferred_ac_conductor", "AL")
            res = optimize_cables_and_generate_boq(pv_capacity_kwp=pv_kwp, inverter_capacity_kw=inv_kw, ac_cable_run_length_m=ac_len, preferred_ac_conductor=cond)
            self._send_json(res)
            return

        elif parsed.path == "/api/bim/export-ifc":
            pname = payload.get("project_name", "AuraEnergy Model")
            kwp = float(payload.get("pv_capacity_kwp", 100.0))
            ifc_content = generate_ifc_bim_stub(pname, kwp)
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-step; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename="bim_{pname.replace(" ", "_")}.ifc"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(ifc_content.encode('utf-8'))
            return

        elif parsed.path == "/api/security/nis2-audit":
            proto = payload.get("scada_protocol", "MODBUS_TCP_TLS")
            mfa = bool(payload.get("mfa_enabled", True))
            fw = bool(payload.get("firmware_up_to_date", True))
            ot = bool(payload.get("air_gapped_ot_network", True))
            res = evaluate_nis2_cybersecurity_posture(scada_protocol=proto, mfa_enabled=mfa, firmware_up_to_date=fw, air_gapped_ot_network=ot)
            self._send_json(res)
            return

        elif parsed.path == "/api/retscreen/full-feasibility":
            ftype = payload.get("facility_type", "Commercial - Office")
            area = float(payload.get("facility_gross_floor_area_m2", 4500.0))
            hours = float(payload.get("annual_operating_hours", 3200.0))
            loc = payload.get("climate_location", "Praha, CZ (50.08°N, 14.43°E)")
            cdd = float(payload.get("cooling_degree_days", 180.0))
            hdd = float(payload.get("heating_degree_days", 3100.0))

            b_elec_rate = float(payload.get("base_electricity_rate_eur_kwh", 0.165))
            b_heat_rate = float(payload.get("base_heating_fuel_rate_eur_kwh", 0.085))
            b_elec_mwh = float(payload.get("base_annual_electricity_mwh", 650.0))
            b_heat_mwh = float(payload.get("base_annual_heating_mwh", 420.0))

            pv_gen = float(payload.get("proposed_pv_generation_mwh", 125.0))
            pv_self = float(payload.get("proposed_pv_self_consumption_pct", 75.0))
            export_tariff = float(payload.get("proposed_surplus_export_tariff_eur_kwh", 0.055))
            ee_save = float(payload.get("proposed_energy_efficiency_savings_pct", 18.0))

            c_feas = float(payload.get("cost_feasibility_study_eur", 3500.0))
            c_dev = float(payload.get("cost_development_permits_eur", 4500.0))
            c_eng = float(payload.get("cost_engineering_design_eur", 5800.0))
            c_equip = float(payload.get("cost_equipment_pv_bess_eur", 65000.0))
            c_bos = float(payload.get("cost_balance_of_system_eur", 12000.0))
            c_inst = float(payload.get("cost_installation_labor_eur", 11500.0))
            c_cont = float(payload.get("cost_contingency_reserve_eur", 4000.0))
            om_fixed = float(payload.get("annual_om_fixed_eur", 1200.0))

            infl = float(payload.get("inflation_rate_pct", 2.5))
            disc = float(payload.get("discount_rate_pct", 6.0))
            debt_rat = float(payload.get("debt_ratio_pct", 70.0))
            debt_int = float(payload.get("debt_interest_rate_pct", 5.2))
            debt_t = int(payload.get("debt_term_years", 15))
            tax_r = float(payload.get("income_tax_rate_pct", 21.0))
            depr_y = int(payload.get("depreciation_years", 10))

            res = calculate_retscreen_complete_feasibility(
                facility_type=ftype,
                facility_gross_floor_area_m2=area,
                annual_operating_hours=hours,
                climate_location=loc,
                cooling_degree_days=cdd,
                heating_degree_days=hdd,
                base_electricity_rate_eur_kwh=b_elec_rate,
                base_heating_fuel_rate_eur_kwh=b_heat_rate,
                base_annual_electricity_mwh=b_elec_mwh,
                base_annual_heating_mwh=b_heat_mwh,
                proposed_pv_generation_mwh=pv_gen,
                proposed_pv_self_consumption_pct=pv_self,
                proposed_surplus_export_tariff_eur_kwh=export_tariff,
                proposed_energy_efficiency_savings_pct=ee_save,
                cost_feasibility_study_eur=c_feas,
                cost_development_permits_eur=c_dev,
                cost_engineering_design_eur=c_eng,
                cost_equipment_pv_bess_eur=c_equip,
                cost_balance_of_system_eur=c_bos,
                cost_installation_labor_eur=c_inst,
                cost_contingency_reserve_eur=c_cont,
                annual_om_fixed_eur=om_fixed,
                inflation_rate_pct=infl,
                discount_rate_pct=disc,
                debt_ratio_pct=debt_rat,
                debt_interest_rate_pct=debt_int,
                debt_term_years=debt_t,
                income_tax_rate_pct=tax_r,
                depreciation_years=depr_y
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/auth/login":
            email = payload.get("email", "")
            pwd = payload.get("password", "")
            auth_res = authenticate_user(email, pwd)
            if auth_res:
                self._send_json(auth_res)
            else:
                self._send_json({"error": "Neplatné přihlašovací údaje"}, status=401)
            return

        elif parsed.path == "/api/scada/ingest-telemetry":
            dev_id = payload.get("device_id", "inv_meter_01")
            ts = float(payload.get("timestamp", time.time()))
            p_kw = float(payload.get("active_power_ac_kw", 0.0))
            poa = float(payload.get("poa_irradiance_w_m2", 0.0))
            t_cell = float(payload.get("cell_temperature_c", 25.0))
            v_grid = float(payload.get("grid_voltage_v", 400.0))
            fdd_res = process_telemetry_packet(dev_id, ts, p_kw, poa, t_cell, v_grid)
            self._send_json(fdd_res)
            return

        elif parsed.path == "/api/residential/simulate":
            sys_kwp = float(payload.get("pv_system_kwp", 8.0))
            bat_kwh = float(payload.get("battery_capacity_kwh", 10.0))
            capex = float(payload.get("gross_capex_czk", 380000.0))
            has_hp = bool(payload.get("has_heat_pump", True))
            has_ev = bool(payload.get("has_ev_wallbox", True))
            has_tuv = bool(payload.get("has_electric_hot_water_boiler", True))
            mode = payload.get("feedin_mode", "SPOT_OR_FIXED")

            load_prof = generate_residential_8760_load_profile(
                has_heat_pump=has_hp,
                has_ev_wallbox=has_ev,
                has_electric_hot_water_boiler=has_tuv
            )
            # Approx PV generation in CZ: 1,080 kWh / kWp
            gen_kwh = sys_kwp * 1080.0
            res_econ = simulate_residential_pv_economics(
                system_kwp=sys_kwp,
                battery_kwh=bat_kwh,
                gross_capex_czk=capex,
                annual_generation_kwh=gen_kwh,
                residential_load_kwh=load_prof["annual_total_electricity_kwh"],
                feedin_mode=mode,
                has_ev_wallbox=has_ev
            )
            self._send_json({
                "load_profile": load_prof,
                "economics": res_econ
            })
            return

        elif parsed.path == "/api/hardware/add-component":
            category = payload.get("category", "MODULE")
            mfg = payload.get("manufacturer", "Vlastní Výrobce")
            model = payload.get("model_name", "Nový Model")
            params = payload.get("params", {})
            res = add_custom_component(category, mfg, model, params)
            self._send_json(res)
            return

        elif parsed.path == "/api/bess/physics-degradation":
            cap = float(payload.get("nominal_capacity_kwh", 100.0))
            chem = payload.get("chemistry", "LFP")
            cycles = float(payload.get("daily_cycles", 1.2))
            soc = float(payload.get("avg_soc_pct", 55.0))
            dod = float(payload.get("avg_dod_pct", 80.0))
            c_rate = float(payload.get("avg_c_rate", 0.5))
            temp = float(payload.get("ambient_cell_temp_c", 25.0))
            years = int(payload.get("project_lifetime_years", 20))
            res = simulate_bess_electrochemical_degradation(
                nominal_capacity_kwh=cap, chemistry=chem, daily_cycles=cycles,
                avg_soc_pct=soc, avg_dod_pct=dod, avg_c_rate=c_rate,
                ambient_cell_temp_c=temp, project_lifetime_years=years
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/pv/bifacial-gain":
            kwp = float(payload.get("pv_capacity_kwp", 100.0))
            gen = float(payload.get("front_annual_generation_mwh", 110.0))
            albedo = payload.get("albedo_type", "GRASS")
            bf_fact = float(payload.get("bifaciality_factor", 0.80))
            h = float(payload.get("clearance_height_m", 1.2))
            pitch = float(payload.get("row_pitch_m", 6.0))
            tilt = float(payload.get("tilt_deg", 25.0))
            res = simulate_bifacial_gain(
                pv_capacity_kwp=kwp, front_annual_generation_mwh=gen, albedo_type=albedo,
                bifaciality_factor=bf_fact, clearance_height_m=h, row_pitch_m=pitch, tilt_deg=tilt
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/grid/iec60909-stability":
            un = float(payload.get("grid_voltage_v", 400.0))
            trafo = float(payload.get("transformer_apparent_power_kva", 630.0))
            uk = float(payload.get("transformer_uk_pct", 4.0))
            inv = float(payload.get("inverter_rated_power_kw", 250.0))
            cable_m = float(payload.get("cable_length_m", 60.0))
            csa = float(payload.get("cable_csa_mm2", 150.0))
            res = calculate_iec60909_short_circuit_and_harmonics(
                grid_voltage_v=un, transformer_apparent_power_kva=trafo, transformer_uk_pct=uk,
                inverter_rated_power_kw=inv, cable_length_m=cable_m, cable_csa_mm2=csa
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/hydrogen/simulate":
            surplus = float(payload.get("surplus_power_kwh_annual", 250000.0))
            cap = float(payload.get("electrolyzer_capacity_kw", 100.0))
            tech = payload.get("electrolyzer_tech", "PEM")
            res = simulate_green_hydrogen_production(surplus_power_kwh_annual=surplus, electrolyzer_capacity_kw=cap, electrolyzer_tech=tech)
            self._send_json(res)
            return

        elif parsed.path == "/api/power-to-heat/simulate":
            surplus = float(payload.get("surplus_power_kwh_annual", 300000.0))
            cop = float(payload.get("heat_pump_cop", 3.2))
            res = simulate_power_to_heat_steam(surplus_power_kwh_annual=surplus, heat_pump_cop=cop)
            self._send_json(res)
            return

        elif parsed.path == "/api/ceps/svr-flexibility":
            mw = float(payload.get("battery_power_mw", 2.0))
            mwh = float(payload.get("battery_capacity_mwh", 4.0))
            srv = payload.get("contracted_service", "aFRR")
            res = simulate_ceps_svr_revenue(battery_power_mw=mw, battery_capacity_mwh=mwh, contracted_service=srv)
            self._send_json(res)
            return

        elif parsed.path == "/api/cables/optimize-boq":
            pv_kwp = float(payload.get("pv_capacity_kwp", 100.0))
            inv_kw = float(payload.get("inverter_capacity_kw", 80.0))
            ac_len = float(payload.get("ac_cable_run_length_m", 65.0))
            cond = payload.get("preferred_ac_conductor", "AL")
            res = optimize_cables_and_generate_boq(pv_capacity_kwp=pv_kwp, inverter_capacity_kw=inv_kw, ac_cable_run_length_m=ac_len, preferred_ac_conductor=cond)
            self._send_json(res)
            return

        elif parsed.path == "/api/bim/export-ifc":
            pname = payload.get("project_name", "AuraEnergy Model")
            kwp = float(payload.get("pv_capacity_kwp", 100.0))
            ifc_content = generate_ifc_bim_stub(pname, kwp)
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-step; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename="bim_{pname.replace(" ", "_")}.ifc"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(ifc_content.encode('utf-8'))
            return

        elif parsed.path == "/api/security/nis2-audit":
            proto = payload.get("scada_protocol", "MODBUS_TCP_TLS")
            mfa = bool(payload.get("mfa_enabled", True))
            fw = bool(payload.get("firmware_up_to_date", True))
            ot = bool(payload.get("air_gapped_ot_network", True))
            res = evaluate_nis2_cybersecurity_posture(scada_protocol=proto, mfa_enabled=mfa, firmware_up_to_date=fw, air_gapped_ot_network=ot)
            self._send_json(res)
            return

        elif parsed.path == "/api/retscreen/full-feasibility":
            ftype = payload.get("facility_type", "Commercial - Office")
            area = float(payload.get("facility_gross_floor_area_m2", 4500.0))
            hours = float(payload.get("annual_operating_hours", 3200.0))
            loc = payload.get("climate_location", "Praha, CZ (50.08°N, 14.43°E)")
            cdd = float(payload.get("cooling_degree_days", 180.0))
            hdd = float(payload.get("heating_degree_days", 3100.0))

            b_elec_rate = float(payload.get("base_electricity_rate_eur_kwh", 0.165))
            b_heat_rate = float(payload.get("base_heating_fuel_rate_eur_kwh", 0.085))
            b_elec_mwh = float(payload.get("base_annual_electricity_mwh", 650.0))
            b_heat_mwh = float(payload.get("base_annual_heating_mwh", 420.0))

            pv_gen = float(payload.get("proposed_pv_generation_mwh", 125.0))
            pv_self = float(payload.get("proposed_pv_self_consumption_pct", 75.0))
            export_tariff = float(payload.get("proposed_surplus_export_tariff_eur_kwh", 0.055))
            ee_save = float(payload.get("proposed_energy_efficiency_savings_pct", 18.0))

            c_feas = float(payload.get("cost_feasibility_study_eur", 3500.0))
            c_dev = float(payload.get("cost_development_permits_eur", 4500.0))
            c_eng = float(payload.get("cost_engineering_design_eur", 5800.0))
            c_equip = float(payload.get("cost_equipment_pv_bess_eur", 65000.0))
            c_bos = float(payload.get("cost_balance_of_system_eur", 12000.0))
            c_inst = float(payload.get("cost_installation_labor_eur", 11500.0))
            c_cont = float(payload.get("cost_contingency_reserve_eur", 4000.0))
            om_fixed = float(payload.get("annual_om_fixed_eur", 1200.0))

            infl = float(payload.get("inflation_rate_pct", 2.5))
            disc = float(payload.get("discount_rate_pct", 6.0))
            debt_rat = float(payload.get("debt_ratio_pct", 70.0))
            debt_int = float(payload.get("debt_interest_rate_pct", 5.2))
            debt_t = int(payload.get("debt_term_years", 15))
            tax_r = float(payload.get("income_tax_rate_pct", 21.0))
            depr_y = int(payload.get("depreciation_years", 10))

            res = calculate_retscreen_complete_feasibility(
                facility_type=ftype,
                facility_gross_floor_area_m2=area,
                annual_operating_hours=hours,
                climate_location=loc,
                cooling_degree_days=cdd,
                heating_degree_days=hdd,
                base_electricity_rate_eur_kwh=b_elec_rate,
                base_heating_fuel_rate_eur_kwh=b_heat_rate,
                base_annual_electricity_mwh=b_elec_mwh,
                base_annual_heating_mwh=b_heat_mwh,
                proposed_pv_generation_mwh=pv_gen,
                proposed_pv_self_consumption_pct=pv_self,
                proposed_surplus_export_tariff_eur_kwh=export_tariff,
                proposed_energy_efficiency_savings_pct=ee_save,
                cost_feasibility_study_eur=c_feas,
                cost_development_permits_eur=c_dev,
                cost_engineering_design_eur=c_eng,
                cost_equipment_pv_bess_eur=c_equip,
                cost_balance_of_system_eur=c_bos,
                cost_installation_labor_eur=c_inst,
                cost_contingency_reserve_eur=c_cont,
                annual_om_fixed_eur=om_fixed,
                inflation_rate_pct=infl,
                discount_rate_pct=disc,
                debt_ratio_pct=debt_rat,
                debt_interest_rate_pct=debt_int,
                debt_term_years=debt_t,
                income_tax_rate_pct=tax_r,
                depreciation_years=depr_y
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/gis/shading-analysis":
            tilt = float(payload.get("tilt_deg", 35.0))
            az = float(payload.get("azimuth_deg", 180.0))
            lat = float(payload.get("latitude_deg", 50.08))
            obs = payload.get("obstacles", None)
            kwp = float(payload.get("installed_capacity_kwp", 100.0))
            shading_res = simulate_3d_shading_matrix(obstacles=obs, roof_tilt_deg=tilt, roof_azimuth_deg=az, latitude_deg=lat, installed_capacity_kwp=kwp)
            self._send_json(shading_res)
            return

        elif parsed.path == "/api/ppa/simulate":
            gen = float(payload.get("annual_generation_mwh", 1200.0))
            ctype = payload.get("contract_type", "ON_SITE_PPA")
            price = float(payload.get("base_ppa_price_eur_mwh", 78.0))
            term = int(payload.get("ppa_term_years", 15))
            offtaker = payload.get("corporate_offtaker_name", "Škoda Auto / Průmyslový Partner a.s.")
            ppa_res = simulate_corporate_ppa_contract(annual_generation_mwh=gen, contract_type=ctype, base_ppa_price_eur_mwh=price, ppa_term_years=term, corporate_offtaker_name=offtaker)
            self._send_json(ppa_res)
            return

        elif parsed.path == "/api/finance/advanced-debt":
            capex = float(payload.get("total_capex_eur", 1000000.0))
            sr_pct = float(payload.get("senior_debt_pct", 65.0))
            mezz_pct = float(payload.get("mezzanine_debt_pct", 15.0))
            cfads = float(payload.get("annual_cfads_year1", 95000.0))
            debt_res = calculate_advanced_debt_syndication(total_capex_eur=capex, senior_debt_pct=sr_pct, mezzanine_debt_pct=mezz_pct, annual_cfads_year1=cfads)
            self._send_json(debt_res)
            return

        elif parsed.path == "/api/optimize/scenarios":
            load = float(payload.get("base_annual_load_kwh", 120000.0))
            price = float(payload.get("electricity_price_eur_mwh", 165.0))
            pv_list = payload.get("pv_candidates_kwp", None)
            bess_list = payload.get("bess_candidates_kwh", None)
            opt_res = run_multicriteria_pv_bess_optimization(
                base_annual_load_kwh=load,
                electricity_price_eur_mwh=price,
                pv_candidates_kwp=pv_list,
                bess_candidates_kwh=bess_list
            )
            self._send_json(opt_res)
            return

        elif parsed.path == "/api/live/ote-market":
            date_param = payload.get("date", None)
            self._send_json(fetch_live_ote_day_ahead_prices(date_param))
            return

        elif parsed.path == "/api/live/weather-forecast":
            lat = float(payload.get("latitude", 50.08))
            lon = float(payload.get("longitude", 14.43))
            self._send_json(fetch_7day_weather_forecast(lat, lon))
            return

        elif parsed.path == "/api/community/simulate":
            pv_kwp = float(payload.get("community_pv_capacity_kwp", payload.get("pv_capacity_kwp", 100.0)))
            annual_gen = float(payload.get("annual_pv_generation_kwh", pv_kwp * 1100.0))
            mode = payload.get("sharing_mode", "DYNAMIC_ALLOCATION")
            count = int(payload.get("members_count", 5))
            discount = float(payload.get("local_distribution_discount_pct", 30.0))
            grid_price = float(payload.get("grid_retail_price_czk_kwh", 5.20))
            internal_price = float(payload.get("community_internal_price_czk_kwh", 3.20))
            surplus_price = float(payload.get("surplus_feedin_price_czk_kwh", 1.40))
            
            res = simulate_community_energy_sharing(
                pv_capacity_kwp=pv_kwp,
                annual_pv_generation_kwh=annual_gen,
                sharing_mode=mode,
                members_count=count,
                local_distribution_discount_pct=discount,
                grid_retail_price_czk_kwh=grid_price,
                community_internal_price_czk_kwh=internal_price,
                surplus_feedin_price_czk_kwh=surplus_price
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/bess/physics-degradation":
            cap = float(payload.get("nominal_capacity_kwh", 100.0))
            chem = payload.get("chemistry", "LFP")
            cycles = float(payload.get("daily_cycles", 1.2))
            soc = float(payload.get("avg_soc_pct", 55.0))
            dod = float(payload.get("avg_dod_pct", 80.0))
            c_rate = float(payload.get("avg_c_rate", 0.5))
            temp = float(payload.get("ambient_cell_temp_c", 25.0))
            years = int(payload.get("project_lifetime_years", 20))
            res = simulate_bess_electrochemical_degradation(
                nominal_capacity_kwh=cap, chemistry=chem, daily_cycles=cycles,
                avg_soc_pct=soc, avg_dod_pct=dod, avg_c_rate=c_rate,
                ambient_cell_temp_c=temp, project_lifetime_years=years
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/pv/bifacial-gain":
            kwp = float(payload.get("pv_capacity_kwp", 100.0))
            gen = float(payload.get("front_annual_generation_mwh", 110.0))
            albedo = payload.get("albedo_type", "GRASS")
            bf_fact = float(payload.get("bifaciality_factor", 0.80))
            h = float(payload.get("clearance_height_m", 1.2))
            pitch = float(payload.get("row_pitch_m", 6.0))
            tilt = float(payload.get("tilt_deg", 25.0))
            res = simulate_bifacial_gain(
                pv_capacity_kwp=kwp, front_annual_generation_mwh=gen, albedo_type=albedo,
                bifaciality_factor=bf_fact, clearance_height_m=h, row_pitch_m=pitch, tilt_deg=tilt
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/grid/iec60909-stability":
            un = float(payload.get("grid_voltage_v", 400.0))
            trafo = float(payload.get("transformer_apparent_power_kva", 630.0))
            uk = float(payload.get("transformer_uk_pct", 4.0))
            inv = float(payload.get("inverter_rated_power_kw", 250.0))
            cable_m = float(payload.get("cable_length_m", 60.0))
            csa = float(payload.get("cable_csa_mm2", 150.0))
            res = calculate_iec60909_short_circuit_and_harmonics(
                grid_voltage_v=un, transformer_apparent_power_kva=trafo, transformer_uk_pct=uk,
                inverter_rated_power_kw=inv, cable_length_m=cable_m, cable_csa_mm2=csa
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/hydrogen/simulate":
            surplus = float(payload.get("surplus_power_kwh_annual", 250000.0))
            cap = float(payload.get("electrolyzer_capacity_kw", 100.0))
            tech = payload.get("electrolyzer_tech", "PEM")
            res = simulate_green_hydrogen_production(surplus_power_kwh_annual=surplus, electrolyzer_capacity_kw=cap, electrolyzer_tech=tech)
            self._send_json(res)
            return

        elif parsed.path == "/api/power-to-heat/simulate":
            surplus = float(payload.get("surplus_power_kwh_annual", 300000.0))
            cop = float(payload.get("heat_pump_cop", 3.2))
            res = simulate_power_to_heat_steam(surplus_power_kwh_annual=surplus, heat_pump_cop=cop)
            self._send_json(res)
            return

        elif parsed.path == "/api/ceps/svr-flexibility":
            mw = float(payload.get("battery_power_mw", 2.0))
            mwh = float(payload.get("battery_capacity_mwh", 4.0))
            srv = payload.get("contracted_service", "aFRR")
            res = simulate_ceps_svr_revenue(battery_power_mw=mw, battery_capacity_mwh=mwh, contracted_service=srv)
            self._send_json(res)
            return

        elif parsed.path == "/api/cables/optimize-boq":
            pv_kwp = float(payload.get("pv_capacity_kwp", 100.0))
            inv_kw = float(payload.get("inverter_capacity_kw", 80.0))
            ac_len = float(payload.get("ac_cable_run_length_m", 65.0))
            cond = payload.get("preferred_ac_conductor", "AL")
            res = optimize_cables_and_generate_boq(pv_capacity_kwp=pv_kwp, inverter_capacity_kw=inv_kw, ac_cable_run_length_m=ac_len, preferred_ac_conductor=cond)
            self._send_json(res)
            return

        elif parsed.path == "/api/bim/export-ifc":
            pname = payload.get("project_name", "AuraEnergy Model")
            kwp = float(payload.get("pv_capacity_kwp", 100.0))
            ifc_content = generate_ifc_bim_stub(pname, kwp)
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-step; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename="bim_{pname.replace(" ", "_")}.ifc"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(ifc_content.encode('utf-8'))
            return

        elif parsed.path == "/api/security/nis2-audit":
            proto = payload.get("scada_protocol", "MODBUS_TCP_TLS")
            mfa = bool(payload.get("mfa_enabled", True))
            fw = bool(payload.get("firmware_up_to_date", True))
            ot = bool(payload.get("air_gapped_ot_network", True))
            res = evaluate_nis2_cybersecurity_posture(scada_protocol=proto, mfa_enabled=mfa, firmware_up_to_date=fw, air_gapped_ot_network=ot)
            self._send_json(res)
            return

        elif parsed.path == "/api/retscreen/full-feasibility":
            ftype = payload.get("facility_type", "Commercial - Office")
            area = float(payload.get("facility_gross_floor_area_m2", 4500.0))
            hours = float(payload.get("annual_operating_hours", 3200.0))
            loc = payload.get("climate_location", "Praha, CZ (50.08°N, 14.43°E)")
            cdd = float(payload.get("cooling_degree_days", 180.0))
            hdd = float(payload.get("heating_degree_days", 3100.0))

            b_elec_rate = float(payload.get("base_electricity_rate_eur_kwh", 0.165))
            b_heat_rate = float(payload.get("base_heating_fuel_rate_eur_kwh", 0.085))
            b_elec_mwh = float(payload.get("base_annual_electricity_mwh", 650.0))
            b_heat_mwh = float(payload.get("base_annual_heating_mwh", 420.0))

            pv_gen = float(payload.get("proposed_pv_generation_mwh", 125.0))
            pv_self = float(payload.get("proposed_pv_self_consumption_pct", 75.0))
            export_tariff = float(payload.get("proposed_surplus_export_tariff_eur_kwh", 0.055))
            ee_save = float(payload.get("proposed_energy_efficiency_savings_pct", 18.0))

            c_feas = float(payload.get("cost_feasibility_study_eur", 3500.0))
            c_dev = float(payload.get("cost_development_permits_eur", 4500.0))
            c_eng = float(payload.get("cost_engineering_design_eur", 5800.0))
            c_equip = float(payload.get("cost_equipment_pv_bess_eur", 65000.0))
            c_bos = float(payload.get("cost_balance_of_system_eur", 12000.0))
            c_inst = float(payload.get("cost_installation_labor_eur", 11500.0))
            c_cont = float(payload.get("cost_contingency_reserve_eur", 4000.0))
            om_fixed = float(payload.get("annual_om_fixed_eur", 1200.0))

            infl = float(payload.get("inflation_rate_pct", 2.5))
            disc = float(payload.get("discount_rate_pct", 6.0))
            debt_rat = float(payload.get("debt_ratio_pct", 70.0))
            debt_int = float(payload.get("debt_interest_rate_pct", 5.2))
            debt_t = int(payload.get("debt_term_years", 15))
            tax_r = float(payload.get("income_tax_rate_pct", 21.0))
            depr_y = int(payload.get("depreciation_years", 10))

            res = calculate_retscreen_complete_feasibility(
                facility_type=ftype,
                facility_gross_floor_area_m2=area,
                annual_operating_hours=hours,
                climate_location=loc,
                cooling_degree_days=cdd,
                heating_degree_days=hdd,
                base_electricity_rate_eur_kwh=b_elec_rate,
                base_heating_fuel_rate_eur_kwh=b_heat_rate,
                base_annual_electricity_mwh=b_elec_mwh,
                base_annual_heating_mwh=b_heat_mwh,
                proposed_pv_generation_mwh=pv_gen,
                proposed_pv_self_consumption_pct=pv_self,
                proposed_surplus_export_tariff_eur_kwh=export_tariff,
                proposed_energy_efficiency_savings_pct=ee_save,
                cost_feasibility_study_eur=c_feas,
                cost_development_permits_eur=c_dev,
                cost_engineering_design_eur=c_eng,
                cost_equipment_pv_bess_eur=c_equip,
                cost_balance_of_system_eur=c_bos,
                cost_installation_labor_eur=c_inst,
                cost_contingency_reserve_eur=c_cont,
                annual_om_fixed_eur=om_fixed,
                inflation_rate_pct=infl,
                discount_rate_pct=disc,
                debt_ratio_pct=debt_rat,
                debt_interest_rate_pct=debt_int,
                debt_term_years=debt_t,
                income_tax_rate_pct=tax_r,
                depreciation_years=depr_y
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/cad/generate-sld":
            pv_kwp = float(payload.get("pv_capacity_kwp", 100.0))
            mod_count = int(payload.get("modules_count", round(pv_kwp * 1000.0 / 580.0)))
            mod_power = float(payload.get("module_power_w", 580.0))
            strings = int(payload.get("strings_count", 8))
            mod_per_str = int(payload.get("modules_per_string", 22))
            inv_name = payload.get("inverter_name", f"Střídač {round(pv_kwp * 0.9, 0):.0f} kW")
            breaker = int(payload.get("main_breaker_a", round(pv_kwp * 1.5, 0)))
            cable = payload.get("cable_type", "CYKY 4x95 mm²" if pv_kwp < 100 else "AYKY 4x150 mm²")
            pname = payload.get("project_name", "AuraEnergy FVE Projekt")
            
            dxf_text = generate_dxf_single_line_diagram(
                project_name=pname,
                modules_count=mod_count,
                module_power_w=mod_power,
                strings_count=strings,
                modules_per_string=mod_per_str,
                inverter_name=inv_name,
                main_breaker_a=breaker,
                cable_type=cable
            )
            self.send_response(200)
            self.send_header('Content-Type', 'application/dxf; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename="sld_{pname.replace(" ", "_")}.dxf"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(dxf_text.encode('utf-8'))
            return

        elif parsed.path == "/api/audit/compliance-check":
            ptype = payload.get("project_type", "commercial")
            pv_kwp = float(payload.get("pv_capacity_kwp", 100.0))
            bess_kwh = float(payload.get("battery_capacity_kwh", 60.0))
            prod_mwh = float(payload.get("annual_production_mwh", 105.0))
            cons_mwh = float(payload.get("annual_consumption_mwh", 150.0))
            self_mwh = float(payload.get("self_consumption_mwh", 75.0))
            exp_mwh = float(payload.get("export_mwh", 30.0))
            imp_mwh = float(payload.get("grid_import_mwh", 75.0))
            capex = float(payload.get("capex_czk", 2500000.0))
            roof = bool(payload.get("installed_roof", True))
            agri = bool(payload.get("agrivoltaics", False))
            brown = bool(payload.get("brownfield", False))

            res = evaluate_audit_compliance(
                project_type=ptype,
                pv_capacity_kwp=pv_kwp,
                battery_capacity_kwh=bess_kwh,
                annual_production_mwh=prod_mwh,
                annual_consumption_mwh=cons_mwh,
                self_consumption_mwh=self_mwh,
                export_mwh=exp_mwh,
                grid_import_mwh=imp_mwh,
                capex_czk=capex,
                installed_roof=roof,
                agrivoltaics=agri,
                brownfield=brown
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/bess/physics-degradation":
            cap = float(payload.get("nominal_capacity_kwh", 100.0))
            chem = payload.get("chemistry", "LFP")
            cycles = float(payload.get("daily_cycles", 1.2))
            soc = float(payload.get("avg_soc_pct", 55.0))
            dod = float(payload.get("avg_dod_pct", 80.0))
            c_rate = float(payload.get("avg_c_rate", 0.5))
            temp = float(payload.get("ambient_cell_temp_c", 25.0))
            years = int(payload.get("project_lifetime_years", 20))
            res = simulate_bess_electrochemical_degradation(
                nominal_capacity_kwh=cap, chemistry=chem, daily_cycles=cycles,
                avg_soc_pct=soc, avg_dod_pct=dod, avg_c_rate=c_rate,
                ambient_cell_temp_c=temp, project_lifetime_years=years
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/pv/bifacial-gain":
            kwp = float(payload.get("pv_capacity_kwp", 100.0))
            gen = float(payload.get("front_annual_generation_mwh", 110.0))
            albedo = payload.get("albedo_type", "GRASS")
            bf_fact = float(payload.get("bifaciality_factor", 0.80))
            h = float(payload.get("clearance_height_m", 1.2))
            pitch = float(payload.get("row_pitch_m", 6.0))
            tilt = float(payload.get("tilt_deg", 25.0))
            res = simulate_bifacial_gain(
                pv_capacity_kwp=kwp, front_annual_generation_mwh=gen, albedo_type=albedo,
                bifaciality_factor=bf_fact, clearance_height_m=h, row_pitch_m=pitch, tilt_deg=tilt
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/grid/iec60909-stability":
            un = float(payload.get("grid_voltage_v", 400.0))
            trafo = float(payload.get("transformer_apparent_power_kva", 630.0))
            uk = float(payload.get("transformer_uk_pct", 4.0))
            inv = float(payload.get("inverter_rated_power_kw", 250.0))
            cable_m = float(payload.get("cable_length_m", 60.0))
            csa = float(payload.get("cable_csa_mm2", 150.0))
            res = calculate_iec60909_short_circuit_and_harmonics(
                grid_voltage_v=un, transformer_apparent_power_kva=trafo, transformer_uk_pct=uk,
                inverter_rated_power_kw=inv, cable_length_m=cable_m, cable_csa_mm2=csa
            )
            self._send_json(res)
            return

        elif parsed.path == "/api/hydrogen/simulate":
            surplus = float(payload.get("surplus_power_kwh_annual", 250000.0))
            cap = float(payload.get("electrolyzer_capacity_kw", 100.0))
            tech = payload.get("electrolyzer_tech", "PEM")
            res = simulate_green_hydrogen_production(surplus_power_kwh_annual=surplus, electrolyzer_capacity_kw=cap, electrolyzer_tech=tech)
            self._send_json(res)
            return

        elif parsed.path == "/api/power-to-heat/simulate":
            surplus = float(payload.get("surplus_power_kwh_annual", 300000.0))
            cop = float(payload.get("heat_pump_cop", 3.2))
            res = simulate_power_to_heat_steam(surplus_power_kwh_annual=surplus, heat_pump_cop=cop)
            self._send_json(res)
            return

        elif parsed.path == "/api/ceps/svr-flexibility":
            mw = float(payload.get("battery_power_mw", 2.0))
            mwh = float(payload.get("battery_capacity_mwh", 4.0))
            srv = payload.get("contracted_service", "aFRR")
            res = simulate_ceps_svr_revenue(battery_power_mw=mw, battery_capacity_mwh=mwh, contracted_service=srv)
            self._send_json(res)
            return

        elif parsed.path == "/api/cables/optimize-boq":
            pv_kwp = float(payload.get("pv_capacity_kwp", 100.0))
            inv_kw = float(payload.get("inverter_capacity_kw", 80.0))
            ac_len = float(payload.get("ac_cable_run_length_m", 65.0))
            cond = payload.get("preferred_ac_conductor", "AL")
            res = optimize_cables_and_generate_boq(pv_capacity_kwp=pv_kwp, inverter_capacity_kw=inv_kw, ac_cable_run_length_m=ac_len, preferred_ac_conductor=cond)
            self._send_json(res)
            return

        elif parsed.path == "/api/bim/export-ifc":
            pname = payload.get("project_name", "AuraEnergy Model")
            kwp = float(payload.get("pv_capacity_kwp", 100.0))
            ifc_content = generate_ifc_bim_stub(pname, kwp)
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-step; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename="bim_{pname.replace(" ", "_")}.ifc"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(ifc_content.encode('utf-8'))
            return

        elif parsed.path == "/api/security/nis2-audit":
            proto = payload.get("scada_protocol", "MODBUS_TCP_TLS")
            mfa = bool(payload.get("mfa_enabled", True))
            fw = bool(payload.get("firmware_up_to_date", True))
            ot = bool(payload.get("air_gapped_ot_network", True))
            res = evaluate_nis2_cybersecurity_posture(scada_protocol=proto, mfa_enabled=mfa, firmware_up_to_date=fw, air_gapped_ot_network=ot)
            self._send_json(res)
            return

        elif parsed.path == "/api/retscreen/full-feasibility":
            ftype = payload.get("facility_type", "Commercial - Office")
            area = float(payload.get("facility_gross_floor_area_m2", 4500.0))
            hours = float(payload.get("annual_operating_hours", 3200.0))
            loc = payload.get("climate_location", "Praha, CZ (50.08°N, 14.43°E)")
            cdd = float(payload.get("cooling_degree_days", 180.0))
            hdd = float(payload.get("heating_degree_days", 3100.0))

            b_elec_rate = float(payload.get("base_electricity_rate_eur_kwh", 0.165))
            b_heat_rate = float(payload.get("base_heating_fuel_rate_eur_kwh", 0.085))
            b_elec_mwh = float(payload.get("base_annual_electricity_mwh", 650.0))
            b_heat_mwh = float(payload.get("base_annual_heating_mwh", 420.0))

            pv_gen = float(payload.get("proposed_pv_generation_mwh", 125.0))
            pv_self = float(payload.get("proposed_pv_self_consumption_pct", 75.0))
            export_tariff = float(payload.get("proposed_surplus_export_tariff_eur_kwh", 0.055))
            ee_save = float(payload.get("proposed_energy_efficiency_savings_pct", 18.0))

            c_feas = float(payload.get("cost_feasibility_study_eur", 3500.0))
            c_dev = float(payload.get("cost_development_permits_eur", 4500.0))
            c_eng = float(payload.get("cost_engineering_design_eur", 5800.0))
            c_equip = float(payload.get("cost_equipment_pv_bess_eur", 65000.0))
            c_bos = float(payload.get("cost_balance_of_system_eur", 12000.0))
            c_inst = float(payload.get("cost_installation_labor_eur", 11500.0))
            c_cont = float(payload.get("cost_contingency_reserve_eur", 4000.0))
            om_fixed = float(payload.get("annual_om_fixed_eur", 1200.0))

            infl = float(payload.get("inflation_rate_pct", 2.5))
            disc = float(payload.get("discount_rate_pct", 6.0))
            debt_rat = float(payload.get("debt_ratio_pct", 70.0))
            debt_int = float(payload.get("debt_interest_rate_pct", 5.2))
            debt_t = int(payload.get("debt_term_years", 15))
            tax_r = float(payload.get("income_tax_rate_pct", 21.0))
            depr_y = int(payload.get("depreciation_years", 10))

            res = calculate_retscreen_complete_feasibility(
                facility_type=ftype,
                facility_gross_floor_area_m2=area,
                annual_operating_hours=hours,
                climate_location=loc,
                cooling_degree_days=cdd,
                heating_degree_days=hdd,
                base_electricity_rate_eur_kwh=b_elec_rate,
                base_heating_fuel_rate_eur_kwh=b_heat_rate,
                base_annual_electricity_mwh=b_elec_mwh,
                base_annual_heating_mwh=b_heat_mwh,
                proposed_pv_generation_mwh=pv_gen,
                proposed_pv_self_consumption_pct=pv_self,
                proposed_surplus_export_tariff_eur_kwh=export_tariff,
                proposed_energy_efficiency_savings_pct=ee_save,
                cost_feasibility_study_eur=c_feas,
                cost_development_permits_eur=c_dev,
                cost_engineering_design_eur=c_eng,
                cost_equipment_pv_bess_eur=c_equip,
                cost_balance_of_system_eur=c_bos,
                cost_installation_labor_eur=c_inst,
                cost_contingency_reserve_eur=c_cont,
                annual_om_fixed_eur=om_fixed,
                inflation_rate_pct=infl,
                discount_rate_pct=disc,
                debt_ratio_pct=debt_rat,
                debt_interest_rate_pct=debt_int,
                debt_term_years=debt_t,
                income_tax_rate_pct=tax_r,
                depreciation_years=depr_y
            )
            self._send_json(res)
            return

        self.send_error(404, "API endpoint not found")

def run():
    server_address = ('127.0.0.1', PORT)
    httpd = HTTPServer(server_address, SamServerHandler)
    print(f"AuraEnergy SAM OS Grid Pro v11.0 Server running at http://127.0.0.1:{PORT}")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
