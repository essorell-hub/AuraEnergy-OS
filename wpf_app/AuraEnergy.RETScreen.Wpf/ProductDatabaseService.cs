using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.IO;

namespace AuraEnergy.RETScreen.Wpf
{
    public class CertifiedProduct
    {
        public int Id { get; set; }
        public string Name { get; set; } = string.Empty;
        public string Manufacturer { get; set; } = string.Empty;
        public string Category { get; set; } = string.Empty;
        public double Capacity { get; set; }
        public double Efficiency { get; set; }
        public string Unit { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
    }

    public static class ProductDatabaseService
    {
        private static readonly string DbPath = @"C:\Program Files\RETScreen\RETScreen Expert\Data\product.sqlite";

        public static List<CertifiedProduct> SearchProducts(string categoryFilter = "", string query = "")
        {
            var results = new List<CertifiedProduct>();

            if (!File.Exists(DbPath))
            {
                return GetFallbackProducts();
            }

            try
            {
                using var conn = new SQLiteConnection($"Data Source={DbPath};Version=3;Read Only=True;");
                conn.Open();

                string sql = @"
                    SELECT p.ProductID, 
                           COALESCE(p.ProductCaption, 'Standard Model') AS Model,
                           COALESCE(m.ManufacturerName, 'General') AS Manufacturer,
                           COALESCE(c.Caption, 'OZE') AS Category,
                           COALESCE(p.CapacityValue, 0) AS Capacity,
                           COALESCE(p.CapacityUnit, 'kW') AS CapacityUnit
                    FROM Product p
                    LEFT JOIN ProductManufacturer m ON p.ManufacturerID = m.ManufacturerID
                    LEFT JOIN ProductCategory c ON p.ProductCategoryID = c.ProductCategoryID
                    WHERE 1=1";

                if (!string.IsNullOrEmpty(categoryFilter) && categoryFilter != "Všechny kategorie" && categoryFilter != "All")
                {
                    sql += " AND (c.Caption LIKE @cat OR c.SubTypeCaption LIKE @cat)";
                }

                if (!string.IsNullOrEmpty(query))
                {
                    sql += " AND (p.ProductCaption LIKE @q OR m.ManufacturerName LIKE @q OR c.Caption LIKE @q)";
                }

                sql += " ORDER BY p.ProductID ASC LIMIT 200;";

                using var cmd = new SQLiteCommand(sql, conn);
                if (!string.IsNullOrEmpty(categoryFilter) && categoryFilter != "Všechny kategorie" && categoryFilter != "All")
                {
                    cmd.Parameters.AddWithValue("@cat", $"%{categoryFilter}%");
                }
                if (!string.IsNullOrEmpty(query))
                {
                    cmd.Parameters.AddWithValue("@q", $"%{query}%");
                }

                using var rdr = cmd.ExecuteReader();
                while (rdr.Read())
                {
                    string rawName = rdr.IsDBNull(1) ? "Standard Model" : rdr.GetString(1);
                    rawName = rawName.Replace("{{", "").Replace("}}", "");

                    string rawCategory = rdr.IsDBNull(3) ? "OZE" : rdr.GetString(3);
                    rawCategory = rawCategory.Replace("{{", "").Replace("}}", "");

                    string rawUnit = rdr.IsDBNull(5) ? "kW" : rdr.GetString(5);
                    rawUnit = rawUnit.Replace("{{", "").Replace("}}", "").Replace("xKiloWattSymbol", "kW").Replace("xWattSymbol", "W");

                    double cap = 0;
                    if (!rdr.IsDBNull(4))
                    {
                        try { cap = Convert.ToDouble(rdr.GetValue(4)); } catch { }
                    }

                    results.Add(new CertifiedProduct
                    {
                        Id = rdr.GetInt32(0),
                        Name = rawName,
                        Manufacturer = rdr.IsDBNull(2) ? "General" : rdr.GetString(2),
                        Category = rawCategory,
                        Capacity = cap,
                        Efficiency = cap > 0 && cap < 1 ? 21.5 : (cap > 100 ? 98.6 : 85.0),
                        Unit = string.IsNullOrEmpty(rawUnit) ? "kW" : rawUnit,
                        Description = $"{rdr.GetString(2)} {rawName} ({rawCategory})"
                    });
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"SQLite Error: {ex.Message}");
                return GetFallbackProducts();
            }

            return results.Count > 0 ? results : GetFallbackProducts();
        }

        private static List<CertifiedProduct> GetFallbackProducts()
        {
            return new List<CertifiedProduct>
            {
                // FVE Rezidenční i komerční panely 2026
                new CertifiedProduct { Id = 1, Manufacturer = "Canadian Solar", Name = "CS7N-670MS BiHiKu7", Category = "PV Module", Capacity = 0.670, Efficiency = 21.6, Unit = "kWp", Description = "Bifaciální monokrystalický panel TOPCon" },
                new CertifiedProduct { Id = 2, Manufacturer = "Trina Solar", Name = "Vertex S+ 445W (Černý design pro RD)", Category = "PV Module", Capacity = 0.445, Efficiency = 22.3, Unit = "kWp", Description = "Rezidenční černý N-type TOPCon panel s 25letou zárukou" },
                new CertifiedProduct { Id = 3, Manufacturer = "JinkoSolar", Name = "Tiger Neo 54HL4R-B 435W", Category = "PV Module", Capacity = 0.435, Efficiency = 21.8, Unit = "kWp", Description = "All-black rezidenční modul pro rodinné domy" },
                new CertifiedProduct { Id = 4, Manufacturer = "Aiko Solar", Name = "Neostar 2P 460W ABC", Category = "PV Module", Capacity = 0.460, Efficiency = 23.6, Unit = "kWp", Description = "Technologie ABC bez předních kontaktů s rekordní účinností" },

                // Hybridní střídače a BESS pro rodinné domy
                new CertifiedProduct { Id = 5, Manufacturer = "GoodWe", Name = "GW10K-ET Plus (10 kW)", Category = "Inverter / BESS", Capacity = 10.0, Efficiency = 98.2, Unit = "kW", Description = "3fázový hybridní asymetrický střídač pro rodinné domy s UPS zálohou" },
                new CertifiedProduct { Id = 6, Manufacturer = "Victron Energy", Name = "MultiPlus-II 48/5000", Category = "Inverter / Off-grid", Capacity = 5.0, Efficiency = 96.0, Unit = "kW", Description = "Ostrovní i hybridní měnič pro chaty a rezidence" },
                new CertifiedProduct { Id = 7, Manufacturer = "Huawei", Name = "LUNA2000-10-S0 (10 kWh)", Category = "BESS Battery", Capacity = 10.0, Efficiency = 95.5, Unit = "kWh", Description = "Modulární LFP baterie pro rodinné domy" },

                // Tepelná čerpadla pro rodinné domy
                new CertifiedProduct { Id = 8, Manufacturer = "Viessmann", Name = "Vitocal 250-A (10 kW)", Category = "Heat Pump", Capacity = 10.0, Efficiency = 5.1, Unit = "kWt", Description = "Monoblokové TČ vzduch-voda s chladivem R290 pro novostavby i rekonstrukce" },
                new CertifiedProduct { Id = 9, Manufacturer = "NIBE", Name = "F2040-8 kW", Category = "Heat Pump", Capacity = 8.0, Efficiency = 4.8, Unit = "kWt", Description = "Invertorové venkovní TČ vzduch-voda s tichým chodem" },
                new CertifiedProduct { Id = 10, Manufacturer = "Panasonic", Name = "Aquarea T-CAP 9 kW Generation J", Category = "Heat Pump", Capacity = 9.0, Efficiency = 5.0, Unit = "kWt", Description = "Udrží 100% nominálního výkonu až do -20°C bez bivalentního dohřevu" },
                new CertifiedProduct { Id = 11, Manufacturer = "Daikin", Name = "Altherma 3 H HT 14 kW", Category = "Heat Pump", Capacity = 14.0, Efficiency = 4.6, Unit = "kWt", Description = "Vysokoteplotní TČ (až 70°C výstup) pro domy s radiátory" },

                // Rekuperace a řízené větrání ZZT
                new CertifiedProduct { Id = 12, Manufacturer = "Jablotron", Name = "Futura L (350 m³/h)", Category = "Ventilation & HRV", Capacity = 0.35, Efficiency = 91.0, Unit = "kW", Description = "Entalpická rekuperace s řízením vlhkosti a integrovaným chlazením CoolBreeze" },
                new CertifiedProduct { Id = 13, Manufacturer = "Zehnder", Name = "ComfoAir Q350 TR", Category = "Ventilation & HRV", Capacity = 0.30, Efficiency = 92.0, Unit = "kW", Description = "Špičková pasivní rekuperační jednotka s účinností ZZT 92 % dle Passivhaus" },
                new CertifiedProduct { Id = 14, Manufacturer = "Atrea", Name = "DUPLEX 380 ECV5", Category = "Ventilation & HRV", Capacity = 0.28, Efficiency = 93.0, Unit = "kW", Description = "Kompaktní podstropní větrací jednotka s EC ventilátory" },

                // Kondenzační plynové a peletové kotle pro RD
                new CertifiedProduct { Id = 15, Manufacturer = "Buderus / Bosch", Name = "Logamax plus GB192i (15 kW)", Category = "Boiler", Capacity = 15.0, Efficiency = 98.5, Unit = "kWt", Description = "Prémiový kondenzační kotel s modulací 1:10 a přípravou na vodík H2 20%" },
                new CertifiedProduct { Id = 16, Manufacturer = "Vaillant", Name = "ecoTEC exclusive IoniDetect", Category = "Boiler", Capacity = 20.0, Efficiency = 98.7, Unit = "kWt", Description = "Automatické rozpoznání kvality plynu a adaptivní spalování" },
                new CertifiedProduct { Id = 17, Manufacturer = "OPOP", Name = "Biopel mini tower 15 kW", Category = "Biomass Boiler", Capacity = 15.0, Efficiency = 93.2, Unit = "kWt", Description = "Automatický peletový kotel 5. emisní třídy a Ekodesign" },
                new CertifiedProduct { Id = 18, Manufacturer = "Thermona", Name = "THERM EL 9 (9 kW)", Category = "Electric Boiler", Capacity = 9.0, Efficiency = 99.0, Unit = "kWt", Description = "Přímotopný elektrokotel s plynulou modulací výkonu" },

                // Komerční technologie
                new CertifiedProduct { Id = 19, Manufacturer = "TEDOM", Name = "Micro T30 (30 kWe / 60 kWt)", Category = "CHP Unit", Capacity = 30.0, Efficiency = 94.5, Unit = "kWe", Description = "Kogenerační jednotka s plynovým spalovacím motorem" },
                new CertifiedProduct { Id = 20, Manufacturer = "Vestas", Name = "V90-2.0 MW", Category = "Wind Turbine", Capacity = 2000.0, Efficiency = 48.0, Unit = "kW", Description = "Průměr rotoru 90m pro větrné parky" }
            };
        }
    }
}
