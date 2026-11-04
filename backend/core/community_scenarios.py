from typing import Dict, Any, List

def calculate_community_sharing(
    pv_generation_mwh_year: float = 180.0,
    production_site_consumption_mwh: float = 80.0,
    offsite_member_consumptions_mwh: List[float] = [35.0, 45.0, 20.0],
    grid_distribution_discount_pct: float = 30.0, # Sleva na distribuci při lokálním sdílení
    retail_electricity_price_eur_mwh: float = 180.0,
    wholesale_surplus_sale_price_eur_mwh: float = 55.0
) -> Dict[str, Any]:
    """
    Model energetického společenství a sdílení elektřiny (Lex OZE II / EU RED II).
    Kalkuluje přímou spotřebu v místě výroby, alokaci přebytků mezi členy
    a ušetřené distribuční poplatky.
    """
    # 1. Přímá spotřeba výrobce
    self_consumed_mwh = min(pv_generation_mwh_year, production_site_consumption_mwh)
    surplus_mwh = pv_generation_mwh_year - self_consumed_mwh
    
    # 2. Sdílení mezi externí odběrná místa (členy)
    total_member_demand_mwh = sum(offsite_member_consumptions_mwh)
    shared_to_members_mwh = min(surplus_mwh, total_member_demand_mwh)
    
    # 3. Zbytek do veřejné sítě
    grid_feedin_mwh = surplus_mwh - shared_to_members_mwh
    
    # Finanční bilance
    # Výrobce ušetřil na vlastní spotřebě
    producer_savings_eur = self_consumed_mwh * retail_electricity_price_eur_mwh
    # Členové ušetřili nákupem komunitní energie (se slevou)
    member_savings_eur = shared_to_members_mwh * (retail_electricity_price_eur_mwh * 0.40)
    # Příjem z prodeje zbylých přetoků do sítě
    grid_sale_revenue_eur = grid_feedin_mwh * wholesale_surplus_sale_price_eur_mwh
    
    total_community_economic_benefit_eur = producer_savings_eur + member_savings_eur + grid_sale_revenue_eur
    
    return {
        "pv_total_mwh": pv_generation_mwh_year,
        "self_consumed_onsite_mwh": round(self_consumed_mwh, 1),
        "shared_to_members_mwh": round(shared_to_members_mwh, 1),
        "grid_feedin_mwh": round(grid_feedin_mwh, 1),
        "community_utilization_pct": round(((self_consumed_mwh + shared_to_members_mwh) / pv_generation_mwh_year * 100.0), 1),
        "producer_savings_eur": round(producer_savings_eur, 2),
        "members_savings_eur": round(member_savings_eur, 2),
        "grid_sale_eur": round(grid_sale_revenue_eur, 2),
        "total_economic_benefit_eur_year": round(total_community_economic_benefit_eur, 2),
        "member_breakdown": [
            {"member_id": f"Odběrné místo #{i+1}", "allocated_shared_mwh": round(min(c, shared_to_members_mwh / len(offsite_member_consumptions_mwh)), 1)}
            for i, c in enumerate(offsite_member_consumptions_mwh)
        ]
    }

def compare_project_scenarios(
    baseline_energy_cost_eur: float = 35000.0,
    scenarios: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Multi-scénářový porovnávač investičních variant vedle sebe (např. Varianta A vs. B vs. C).
    """
    if not scenarios:
        scenarios = [
            {
                "name": "Varianta A: Jen FVE 50 kWp",
                "capex": 45000.0,
                "subsidy": 15000.0,
                "annual_savings": 8500.0,
                "co2_saved_tonnes": 22.0
            },
            {
                "name": "Varianta B: FVE 50 kWp + BESS 40 kWh",
                "capex": 68000.0,
                "subsidy": 28000.0,
                "annual_savings": 13200.0,
                "co2_saved_tonnes": 31.0
            },
            {
                "name": "Varianta C: FVE + BESS + Tepelné čerpadlo",
                "capex": 105000.0,
                "subsidy": 45000.0,
                "annual_savings": 22500.0,
                "co2_saved_tonnes": 68.0
            }
        ]
        
    compared_list = []
    for sc in scenarios:
        net_capex = sc["capex"] - sc["subsidy"]
        payback = net_capex / sc["annual_savings"] if sc["annual_savings"] > 0 else 0.0
        # Zjednodušené 20leté NPV
        npv_20 = sum((sc["annual_savings"]) / (1.06 ** y) for y in range(1, 21)) - net_capex
        
        compared_list.append({
            "name": sc["name"],
            "gross_capex": sc["capex"],
            "subsidy": sc["subsidy"],
            "net_capex": round(net_capex, 2),
            "annual_savings": sc["annual_savings"],
            "simple_payback_years": round(payback, 1),
            "npv_20y": round(npv_20, 2),
            "co2_saved_tonnes": sc["co2_saved_tonnes"]
        })
        
    return {
        "baseline_annual_cost_eur": baseline_energy_cost_eur,
        "scenarios": compared_list
    }
