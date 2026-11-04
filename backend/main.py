from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os

from backend.core.financial import calculate_cash_flow, calculate_lcoe, run_monte_carlo
from backend.core.solarpv import calculate_solar_pv_yield, calculate_battery_storage
from backend.core.energy_efficiency import calculate_heat_pump_savings, calculate_ghg_emissions
from backend.core.mv_analysis import analyze_ipmvp_option_c
from backend.core.climate import get_climate_data

app = FastAPI(
    title="AuraEnergy API",
    description="Clean Energy Decision Support Engine (Modern RETScreen Alternative)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- PYDANTIC SCHÉMATA -----------------

class ClimateRequest(BaseModel):
    latitude: float = 50.087
    longitude: float = 14.421

class SolarFeasibilityRequest(BaseModel):
    capacity_kwp: float = 50.0
    tilt_deg: float = 35.0
    azimuth_deg: float = 180.0
    capex: float = 45000.0 # EUR celková investice
    annual_om_cost: float = 600.0 # EUR/rok
    electricity_price_mwh: float = 160.0 # EUR/MWh úspora nebo výkup
    grid_feed_in_price_mwh: float = 60.0 # EUR/MWh pro přetoky
    self_consumption_ratio_pct: float = 60.0
    discount_rate_pct: float = 6.0
    lifetime_years: int = 25
    annual_ghi_kwh_m2: Optional[float] = 1120.0
    # BESS
    battery_capacity_kwh: Optional[float] = 0.0

class HeatPumpRequest(BaseModel):
    current_fuel: str = "natural_gas"
    annual_heat_demand_mwh: float = 120.0
    heat_pump_scop: float = 3.8
    electricity_price_mwh: float = 170.0
    existing_fuel_price_mwh: float = 85.0
    existing_boiler_efficiency: float = 0.88
    capex: float = 35000.0
    annual_om_cost: float = 400.0
    discount_rate_pct: float = 6.0
    lifetime_years: int = 20

class MvAnalysisRequest(BaseModel):
    baseline_dates: List[str]
    baseline_energy: List[float]
    baseline_hdd: List[float]
    baseline_cdd: Optional[List[float]] = None
    reporting_dates: Optional[List[str]] = None
    reporting_energy: Optional[List[float]] = None
    reporting_hdd: Optional[List[float]] = None
    reporting_cdd: Optional[List[float]] = None

# ----------------- API ENDPOINTY -----------------

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "AuraEnergy Clean Energy Engine", "version": "1.0.0"}

@app.post("/api/climate")
def api_climate(req: ClimateRequest):
    return get_climate_data(req.latitude, req.longitude)

@app.post("/api/feasibility/solar-pv")
def api_solar_feasibility(req: SolarFeasibilityRequest):
    # 1. Energetický výnos
    pv_yield = calculate_solar_pv_yield(
        capacity_kwp=req.capacity_kwp,
        tilt_deg=req.tilt_deg,
        azimuth_deg=req.azimuth_deg,
        annual_ghi_kwh_m2=req.annual_ghi_kwh_m2 or 1120.0
    )
    
    total_mwh = pv_yield["annual_generation_mwh"]
    
    # Baterie nebo přímé rozdělení
    if req.battery_capacity_kwh and req.battery_capacity_kwh > 0:
        bess = calculate_battery_storage(
            pv_annual_kwh=pv_yield["annual_generation_kwh"],
            building_annual_consumption_kwh=pv_yield["annual_generation_kwh"] * 1.5,
            battery_capacity_kwh=req.battery_capacity_kwh
        )
        self_consumed_mwh = bess["total_self_consumed_kwh"] / 1000.0
        feed_in_mwh = bess["grid_feed_in_kwh"] / 1000.0
    else:
        self_consumed_mwh = total_mwh * (req.self_consumption_ratio_pct / 100.0)
        feed_in_mwh = total_mwh - self_consumed_mwh
        
    annual_revenue = (self_consumed_mwh * req.electricity_price_mwh) + (feed_in_mwh * req.grid_feed_in_price_mwh)
    
    # 2. Finanční analýza
    fin = calculate_cash_flow(
        capex=req.capex,
        annual_savings=annual_revenue,
        annual_om_cost=req.annual_om_cost,
        project_lifetime_years=req.lifetime_years,
        discount_rate=req.discount_rate_pct / 100.0
    )
    
    # 3. LCOE
    lcoe = calculate_lcoe(
        capex=req.capex,
        annual_om_cost=req.annual_om_cost,
        annual_generation_mwh=total_mwh,
        project_lifetime_years=req.lifetime_years,
        discount_rate=req.discount_rate_pct / 100.0
    )
    
    # 4. Monte Carlo riziko
    monte_carlo = run_monte_carlo(
        capex=req.capex,
        annual_savings=annual_revenue,
        annual_om_cost=req.annual_om_cost,
        iterations=1500,
        project_lifetime_years=req.lifetime_years,
        discount_rate=req.discount_rate_pct / 100.0
    )
    
    # 5. Emise GHG
    ghg = calculate_ghg_emissions(electricity_saved_mwh=total_mwh)
    
    return {
        "pv_technical": pv_yield,
        "annual_revenue_eur": round(annual_revenue, 2),
        "financial_summary": {
            "capex": req.capex,
            "npv": fin["npv"],
            "irr_pct": fin["irr"],
            "simple_payback_years": fin["simple_payback_years"],
            "discounted_payback_years": fin["discounted_payback_years"],
            "lcoe_eur_mwh": lcoe
        },
        "cash_flow": fin,
        "monte_carlo": monte_carlo,
        "ghg_emissions": ghg
    }

@app.post("/api/feasibility/heat-pump")
def api_heat_pump_feasibility(req: HeatPumpRequest):
    hp_tech = calculate_heat_pump_savings(
        current_fuel_type=req.current_fuel,
        annual_heat_demand_mwh=req.annual_heat_demand_mwh,
        heat_pump_scop=req.heat_pump_scop,
        electricity_price_mwh=req.electricity_price_mwh,
        existing_fuel_price_mwh=req.existing_fuel_price_mwh,
        existing_boiler_efficiency=req.existing_boiler_efficiency
    )
    
    fin = calculate_cash_flow(
        capex=req.capex,
        annual_savings=hp_tech["annual_cost_savings"],
        annual_om_cost=req.annual_om_cost,
        project_lifetime_years=req.lifetime_years,
        discount_rate=req.discount_rate_pct / 100.0
    )
    
    ghg = calculate_ghg_emissions(
        electricity_saved_mwh=-hp_tech["heat_pump_electricity_mwh"], # Přírůstek elektřiny
        gas_saved_mwh=hp_tech["baseline_fuel_demand_mwh"] if req.current_fuel == "natural_gas" else 0.0,
        coal_saved_mwh=hp_tech["baseline_fuel_demand_mwh"] if req.current_fuel == "coal" else 0.0
    )
    
    return {
        "technical_summary": hp_tech,
        "financial_summary": {
            "capex": req.capex,
            "npv": fin["npv"],
            "irr_pct": fin["irr"],
            "simple_payback_years": fin["simple_payback_years"],
            "discounted_payback_years": fin["discounted_payback_years"]
        },
        "cash_flow": fin,
        "ghg_emissions": ghg
    }

@app.post("/api/performance/ipmvp-c")
def api_ipmvp_analysis(req: MvAnalysisRequest):
    try:
        res = analyze_ipmvp_option_c(
            baseline_dates=req.baseline_dates,
            baseline_energy=req.baseline_energy,
            baseline_hdd=req.baseline_hdd,
            baseline_cdd=req.baseline_cdd,
            reporting_dates=req.reporting_dates,
            reporting_energy=req.reporting_energy,
            reporting_hdd=req.reporting_hdd,
            reporting_cdd=req.reporting_cdd
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Statické soubory pro webový frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AuraEnergy API running. Frontend under development."}
