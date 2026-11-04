"""
Pre-populated catalog databases for Modules, Inverters, Batteries and Climate Benchmarks.
"""
from backend.models.schemas import (
    PVModuleEntity, InverterEntity, BatteryEntity, ClimateDataset,
    MonthlyClimateMetric, CellTechnology, InverterType, BatteryChemistry,
    ProjectArchetype, FacilityType
)

MODULE_CATALOG = [
    PVModuleEntity(
        id="mod-topcon-580",
        manufacturer="JinkoSolar",
        model_name="Tiger Neo N-type 72HL4-BDV 580W Bifacial",
        rated_power_stc_w=580.0,
        cell_technology=CellTechnology.TOPCON,
        efficiency_pct=22.45,
        bifaciality_factor=0.80,
        temp_coefficient_pmax_pct_per_c=-0.30,
        noct_c=45.0,
        area_m2=2.58,
        annual_degradation_pct=0.40
    ),
    PVModuleEntity(
        id="mod-hjt-700",
        manufacturer="Huasun",
        model_name="Himalaya G12-132 700W HJT",
        rated_power_stc_w=700.0,
        cell_technology=CellTechnology.HJT,
        efficiency_pct=22.53,
        bifaciality_factor=0.85,
        temp_coefficient_pmax_pct_per_c=-0.26,
        noct_c=44.0,
        area_m2=3.10,
        annual_degradation_pct=0.35
    ),
    PVModuleEntity(
        id="mod-mono-430",
        manufacturer="Trina Solar",
        model_name="Vertex S+ 430W Monofacial",
        rated_power_stc_w=430.0,
        cell_technology=CellTechnology.MONO_PERC,
        efficiency_pct=21.50,
        bifaciality_factor=0.0,
        temp_coefficient_pmax_pct_per_c=-0.34,
        noct_c=45.0,
        area_m2=2.00,
        annual_degradation_pct=0.55
    )
]

INVERTER_CATALOG = [
    InverterEntity(
        id="inv-huawei-100ktl",
        manufacturer="Huawei",
        model_name="SUN2000-100KTL-M2",
        rated_ac_power_kw=100.0,
        max_dc_power_kw=150.0,
        euro_efficiency_pct=98.4,
        mppt_channels_count=10,
        inverter_type=InverterType.STRING
    ),
    InverterEntity(
        id="inv-fronius-50",
        manufacturer="Fronius",
        model_name="Tauro ECO 50-3-D",
        rated_ac_power_kw=50.0,
        max_dc_power_kw=75.0,
        euro_efficiency_pct=98.1,
        mppt_channels_count=3,
        inverter_type=InverterType.STRING
    ),
    InverterEntity(
        id="inv-sungrow-hybrid-20",
        manufacturer="Sungrow",
        model_name="SH20T Commercial Hybrid",
        rated_ac_power_kw=20.0,
        max_dc_power_kw=32.0,
        euro_efficiency_pct=97.9,
        mppt_channels_count=3,
        inverter_type=InverterType.HYBRID
    )
]

BATTERY_CATALOG = [
    BatteryEntity(
        id="bat-byd-cube-100",
        manufacturer="BYD",
        model_name="Battery-Box Commercial C100",
        nominal_capacity_kwh=107.5,
        usable_capacity_kwh=102.0,
        max_continuous_power_kw=50.0,
        roundtrip_efficiency_pct=92.0,
        chemistry=BatteryChemistry.LFP,
        cycle_life_80dod=6500
    ),
    BatteryEntity(
        id="bat-tesla-megapack-lite",
        manufacturer="Tesla Energy",
        model_name="Commercial Powerpack 200",
        nominal_capacity_kwh=232.0,
        usable_capacity_kwh=215.0,
        max_continuous_power_kw=100.0,
        roundtrip_efficiency_pct=90.5,
        chemistry=BatteryChemistry.LFP,
        cycle_life_80dod=7000
    )
]

PRAGUE_CLIMATE = ClimateDataset(
    location_name="Praha / Střední Čechy (CZ)",
    latitude=50.087,
    longitude=14.421,
    elevation_m=280.0,
    monthly=[
        MonthlyClimateMetric(month=1, ghi_kwh_m2=28.5, dni_kwh_m2=35.0, dhi_kwh_m2=18.0, avg_temperature_c=0.5, avg_wind_speed_m_s=4.2, heating_degree_days=540),
        MonthlyClimateMetric(month=2, ghi_kwh_m2=48.2, dni_kwh_m2=55.0, dhi_kwh_m2=28.0, avg_temperature_c=2.1, avg_wind_speed_m_s=4.0, heating_degree_days=445),
        MonthlyClimateMetric(month=3, ghi_kwh_m2=92.4, dni_kwh_m2=98.0, dhi_kwh_m2=51.0, avg_temperature_c=6.4, avg_wind_speed_m_s=3.8, heating_degree_days=360),
        MonthlyClimateMetric(month=4, ghi_kwh_m2=138.6, dni_kwh_m2=135.0, dhi_kwh_m2=72.0, avg_temperature_c=11.2, avg_wind_speed_m_s=3.4, heating_degree_days=205),
        MonthlyClimateMetric(month=5, ghi_kwh_m2=178.5, dni_kwh_m2=170.0, dhi_kwh_m2=88.0, avg_temperature_c=15.8, avg_wind_speed_m_s=3.1, heating_degree_days=85),
        MonthlyClimateMetric(month=6, ghi_kwh_m2=189.2, dni_kwh_m2=175.0, dhi_kwh_m2=95.0, avg_temperature_c=19.4, avg_wind_speed_m_s=2.9, heating_degree_days=20),
        MonthlyClimateMetric(month=7, ghi_kwh_m2=192.4, dni_kwh_m2=182.0, dhi_kwh_m2=94.0, avg_temperature_c=21.2, avg_wind_speed_m_s=2.8, heating_degree_days=10),
        MonthlyClimateMetric(month=8, ghi_kwh_m2=162.8, dni_kwh_m2=160.0, dhi_kwh_m2=82.0, avg_temperature_c=20.6, avg_wind_speed_m_s=2.7, heating_degree_days=15),
        MonthlyClimateMetric(month=9, ghi_kwh_m2=108.5, dni_kwh_m2=112.0, dhi_kwh_m2=58.0, avg_temperature_c=15.5, avg_wind_speed_m_s=3.0, heating_degree_days=95),
        MonthlyClimateMetric(month=10, ghi_kwh_m2=62.4, dni_kwh_m2=68.0, dhi_kwh_m2=36.0, avg_temperature_c=9.8, avg_wind_speed_m_s=3.3, heating_degree_days=255),
        MonthlyClimateMetric(month=11, ghi_kwh_m2=32.1, dni_kwh_m2=38.0, dhi_kwh_m2=20.0, avg_temperature_c=4.8, avg_wind_speed_m_s=3.7, heating_degree_days=395),
        MonthlyClimateMetric(month=12, ghi_kwh_m2=22.4, dni_kwh_m2=26.0, dhi_kwh_m2=15.0, avg_temperature_c=1.4, avg_wind_speed_m_s=4.1, heating_degree_days=515)
    ]
)

PROJECT_ARCHETYPES = [
    ProjectArchetype(
        id="arch-office-b",
        facility_type=FacilityType.COMMERCIAL_OFFICE,
        name="Komerční administrativní budova (Třída B/C)",
        benchmark_eui_kwh_m2_year=145.0,
        typical_floor_area_m2=2500.0,
        daily_operational_hours=11
    ),
    ProjectArchetype(
        id="arch-logistics-hall",
        facility_type=FacilityType.WAREHOUSE_LOGISTICS,
        name="Logistická hala / Skladový areál",
        benchmark_eui_kwh_m2_year=85.0,
        typical_floor_area_m2=8000.0,
        daily_operational_hours=16
    ),
    ProjectArchetype(
        id="arch-manufacturing",
        facility_type=FacilityType.INDUSTRIAL_MANUFACTURING,
        name="Průmyslová výrobní hala (2-směnný provoz)",
        benchmark_eui_kwh_m2_year=260.0,
        typical_floor_area_m2=4500.0,
        daily_operational_hours=16
    )
]
