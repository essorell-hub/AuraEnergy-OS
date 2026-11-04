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
                // Fallback demo data if path not found
                return GetFallbackProducts();
            }

            try
            {
                using var conn = new SQLiteConnection($"Data Source={DbPath};Version=3;Read Only=True;");
                conn.Open();

                string sql = "SELECT id, manufacturer, model, category, capacity, efficiency FROM product WHERE 1=1";
                if (!string.IsNullOrEmpty(query))
                {
                    sql += " AND (model LIKE @q OR manufacturer LIKE @q)";
                }
                sql += " LIMIT 150;";

                using var cmd = new SQLiteCommand(sql, conn);
                if (!string.IsNullOrEmpty(query))
                {
                    cmd.Parameters.AddWithValue("@q", $"%{query}%");
                }

                using var rdr = cmd.ExecuteReader();
                while (rdr.Read())
                {
                    results.Add(new CertifiedProduct
                    {
                        Id = rdr.GetInt32(0),
                        Manufacturer = rdr.IsDBNull(1) ? "General" : rdr.GetString(1),
                        Name = rdr.IsDBNull(2) ? "Standard Model" : rdr.GetString(2),
                        Category = rdr.IsDBNull(3) ? "OZE" : rdr.GetString(3),
                        Capacity = rdr.IsDBNull(4) ? 0 : rdr.GetDouble(4),
                        Efficiency = rdr.IsDBNull(5) ? 0 : rdr.GetDouble(5),
                        Unit = "kW"
                    });
                }
            }
            catch
            {
                return GetFallbackProducts();
            }

            return results.Count > 0 ? results : GetFallbackProducts();
        }

        private static List<CertifiedProduct> GetFallbackProducts()
        {
            return new List<CertifiedProduct>
            {
                new CertifiedProduct { Id = 1, Manufacturer = "Canadian Solar", Name = "CS7N-670MS BiHiKu7", Category = "PV Module", Capacity = 0.670, Efficiency = 21.6, Unit = "kWp", Description = "Bifaciální monokrystalický panel TOPCon" },
                new CertifiedProduct { Id = 2, Manufacturer = "Trina Solar", Name = "Vertex TSM-DEG21C.20", Category = "PV Module", Capacity = 0.670, Efficiency = 21.4, Unit = "kWp", Description = "210mm křemíkové články s vysokým výkonem" },
                new CertifiedProduct { Id = 3, Manufacturer = "JinkoSolar", Name = "Tiger Neo 72HL4-BDVP", Category = "PV Module", Capacity = 0.585, Efficiency = 22.5, Unit = "kWp", Description = "N-type TOPCon technologie s nízkou degradací" },
                new CertifiedProduct { Id = 4, Manufacturer = "Huawei", Name = "SUN2000-100KTL-M2", Category = "Inverter", Capacity = 100.0, Efficiency = 98.8, Unit = "kW", Description = "10 MPPT inteligentní stringový střídač" },
                new CertifiedProduct { Id = 5, Manufacturer = "NIBE", Name = "F1345-60 kW", Category = "Heat Pump", Capacity = 60.0, Efficiency = 4.2, Unit = "kWt", Description = "Země-voda průmyslové tepelné čerpadlo SCOP 4.2" },
                new CertifiedProduct { Id = 6, Manufacturer = "Viessmann", Name = "Vitocal 300-A", Category = "Heat Pump", Capacity = 45.0, Efficiency = 3.9, Unit = "kWt", Description = "Vzduch-voda splitové čerpadlo s bivalentním bodem -7°C" },
                new CertifiedProduct { Id = 7, Manufacturer = "Vestas", Name = "V90-2.0 MW", Category = "Wind Turbine", Capacity = 2000.0, Efficiency = 48.0, Unit = "kW", Description = "Průměr rotoru 90m, výška osy rotoru 80-105m" }
            };
        }
    }
}
