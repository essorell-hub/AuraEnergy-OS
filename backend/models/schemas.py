"""
Core Database Models & Typed Schemas for AuraEnergy SAM Engine.
Entities: PVModule, Inverter, Battery, ClimateDataset, ProjectArchetype.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class CellTechnology(str, Enum):
    MONO_PERC = "mono_perc"
    TOPCON = "topcon"
    HJT = "hjt"
    BIFACIAL = "bifacial"
    THIN_FILM = "thin_film"

class InverterType(str, Enum):
    STRING = "string"
    CENTRAL = "central"
    MICRO = "micro"
    HYBRID = "hybrid"

class BatteryChemistry(str, Enum):
    LFP = "lfp" # Lithium Iron Phosphate
    NMC = "nmc" # Nickel Manganese Cobalt
    SODIUM_ION = "sodium_ion"
    FLOW = "flow"

class FacilityType(str, Enum):
    COMMERCIAL_OFFICE = "commercial_office"
    INDUSTRIAL_MANUFACTURING = "industrial_manufacturing"
    WAREHOUSE_LOGISTICS = "warehouse_logistics"
    RESIDENTIAL_MULTI = "residential_multi"
    AGRICULTURAL = "agricultural"
    HOSPITAL_HEALTHCARE = "hospital_healthcare"

# --- 1. Equipment Catalog Entities ---

class PVModuleEntity(BaseModel):
    id: str
    manufacturer: str
    model_name: str
    rated_power_stc_w: float = Field(..., description="P_mp at STC (1000 W/m2, 25C)")
    cell_technology: CellTechnology
    efficiency_pct: float
    bifaciality_factor: float = 0.0 # 0.0 for monofacial, 0.70-0.85 for bifacial
    temp_coefficient_pmax_pct_per_c: float = -0.34 # %/deg C
    temp_coefficient_voc_pct_per_c: float = -0.27
    temp_coefficient_isc_pct_per_c: float = 0.045
    noct_c: float = 45.0 # Nominal Operating Cell Temperature
    area_m2: float = 2.0
    warranty_years: int = 25
    annual_degradation_pct: float = 0.45 # Modern TOPCon/HJT ~ 0.40%

class InverterEntity(BaseModel):
    id: str
    manufacturer: str
    model_name: str
    rated_ac_power_kw: float
    max_dc_power_kw: float
    euro_efficiency_pct: float = 98.2
    cec_weighted_efficiency_pct: float = 98.5
    mppt_channels_count: int = 2
    inverter_type: InverterType
    nighttime_tare_loss_w: float = 15.0

class BatteryEntity(BaseModel):
    id: str
    manufacturer: str
    model_name: str
    nominal_capacity_kwh: float
    usable_capacity_kwh: float
    max_continuous_power_kw: float
    roundtrip_efficiency_pct: float = 91.0
    chemistry: BatteryChemistry
    cycle_life_80dod: int = 6000
    calendar_life_years: int = 15

# --- 2. Climate & Meteorological Entities ---

class MonthlyClimateMetric(BaseModel):
    month: int # 1 to 12
    ghi_kwh_m2: float # Global Horizontal Irradiance
    dni_kwh_m2: float # Direct Normal Irradiance
    dhi_kwh_m2: float # Diffuse Horizontal Irradiance
    avg_temperature_c: float
    avg_wind_speed_m_s: float
    albedo: float = 0.20
    heating_degree_days: float = 0.0
    cooling_degree_days: float = 0.0

class ClimateDataset(BaseModel):
    location_name: str
    latitude: float
    longitude: float
    elevation_m: float
    source: str = "NASA POWER / Open-Meteo"
    monthly: List[MonthlyClimateMetric]

# --- 3. Project Archetype & Facility Entity ---

class ProjectArchetype(BaseModel):
    id: str
    facility_type: FacilityType
    name: str
    benchmark_eui_kwh_m2_year: float # Energy Use Intensity benchmark
    typical_floor_area_m2: float
    daily_operational_hours: int
    weekday_vs_weekend_ratio: float = 0.40
    default_grid_emission_factor_t_per_mwh: float = 0.40
