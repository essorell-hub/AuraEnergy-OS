# AuraEnergy OS

Operační a rozhodovací systém pro čistou energetiku nové generace nahrazující desktopový software **RETScreen Expert** (NRCan) a **NREL SAM** (System Advisor Model).

## Klíčové Vlastnosti a Moduly
1. **SAM Energy Engine:** Perezův transpoziční model (GHI -> POA), teplotní modely článků z NOCT a větru, 8 760h syntetický profil, Performance Ratio (PR % > 81.5 %) a Capacity Utilization Factor (CUF %).
2. **Síťová připojitelnost PCC (PNE 33 3430-1 & ČSN EN 50160):** Výpočet nárůstu napětí $\Delta U \le 2.0\%$, model impedance distribučních kabelů (AYKY/CYKY 150/240 mm²), zatížení transformátoru, autonomní regulace jalového výkonu střídačem $Q(U)$ a dimenzování jističů a rezervované kapacity (RK).
3. **Finanční a rizikový model:** Fisherova rovnice pro reálné a nominální LCOE, 25leté pro-forma Cash-flow, DSCR, daňové odpisy a 1 200 iterací Monte Carlo rizikové simulace (P10, P50, P90).
4. **Dekarbonizace & IPMVP Option C M&V:** Bilance úspor emisí $CO_2$ dle IPCC a CSRD ESRS E1, vícerozměrná OLS regrese spotřeby budovy (HDD/CDD), statistická verifikace dle ASHRAE Guideline 14 ($R^2$, CV(RMSE), NMBE), CUSUM kumulativní úspory.
5. **Multi-Technology Engine:** Větrné turbíny s Weibullovou distribucí a výkonovými křivkami, malé vodní elektrárny (MVE) s čárou překročení průtoků a kogenerace (CHP) s výpočtem Primary Energy Savings (PES) dle směrnice 2012/27/EU.
6. **AI Day-Ahead MPC & Virtuální Elektrárna (VPP):** Matematická 24h dopředná optimalizace BESS (SciPy Linprog) s trhem OTE / EPEX SPOT a dispečink podpůrných služeb pro přenosovou soustavu (ČEPS SVR aFRR).
7. **SQLite Project Management:** Ukládání a správa variant projektů s plnou persistencí.
8. **1-Klik Tiskový Export PDF:** Bankovní layout optimalizovaný pro energetické auditory a management.

---

## Rychlé spuštění přes Docker (Doporučeno)

Pro spuštění celé aplikace včetně databáze a frontendu na portu `8080` bez nutnosti instalovat Python:

```bash
docker compose up -d --build
```

Aplikace bude okamžitě dostupná na:
👉 **http://127.0.0.1:8080**

Kontrola zdraví kontejneru:
```bash
docker compose ps
curl http://localhost:8080/api/health
```

Zastavení kontejneru se zachováním databáze:
```bash
docker compose down
```

---

## Lokální spuštění bez Dockeru (Python 3.12)

```bash
pip install -r requirements.txt
python server.py
```

Spuštění automatických testů:
```bash
python -m unittest test_suite.py -v
```
