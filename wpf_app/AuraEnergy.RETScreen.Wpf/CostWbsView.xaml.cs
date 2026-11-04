using System.Collections.ObjectModel;
using System.Linq;
using System.Windows;
using System.Windows.Controls;

namespace AuraEnergy.RETScreen.Wpf
{
    public class WbsItem
    {
        public string Code { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string Category { get; set; } = string.Empty;
        public double Quantity { get; set; }
        public string Unit { get; set; } = string.Empty;
        public double UnitCost { get; set; }
        public double TotalCost => Quantity * UnitCost;
    }

    public partial class CostWbsView : UserControl
    {
        public ObservableCollection<WbsItem> Items { get; set; } = new();

        public CostWbsView()
        {
            InitializeComponent();
            LoadDefaultWbs();
            gridWbs.ItemsSource = Items;
            RecalculateTotals();
        }

        private void LoadDefaultWbs()
        {
            Items.Clear();
            Items.Add(new WbsItem { Code = "1.1", Name = "Předinvestiční energetický audit a posudek", Category = "Feasibility", Quantity = 1, Unit = "kpl", UnitCost = 180000 });
            Items.Add(new WbsItem { Code = "2.1", Name = "Projektová dokumentace DSP/DPS a inženýring", Category = "Development", Quantity = 1, Unit = "kpl", UnitCost = 420000 });
            Items.Add(new WbsItem { Code = "2.2", Name = "Povolení připojení k distribuční soustavě (PCC)", Category = "Development", Quantity = 1, Unit = "kpl", UnitCost = 85000 });
            Items.Add(new WbsItem { Code = "3.1", Name = "FVE Panely TOPCon 670Wp (Canadian Solar)", Category = "Equipment", Quantity = 374, Unit = "ks", UnitCost = 3850 });
            Items.Add(new WbsItem { Code = "3.2", Name = "Stringové střídače 100 kW s AFCI ochranou", Category = "Equipment", Quantity = 2, Unit = "ks", UnitCost = 145000 });
            Items.Add(new WbsItem { Code = "3.3", Name = "BESS Bateriové úložiště LFP 300 kWh", Category = "Equipment", Quantity = 1, Unit = "kpl", UnitCost = 4850000 });
            Items.Add(new WbsItem { Code = "3.4", Name = "Tepelné čerpadlo NIBE F1345 120 kWt", Category = "Equipment", Quantity = 1, Unit = "kpl", UnitCost = 2100000 });
            Items.Add(new WbsItem { Code = "4.1", Name = "Nosná konstrukce a 1osý tracker systém", Category = "Balance of System", Quantity = 1, Unit = "kpl", UnitCost = 1350000 });
            Items.Add(new WbsItem { Code = "4.2", Name = "Solární DC kabeláže, přepěťové ochrany SPD", Category = "Balance of System", Quantity = 1, Unit = "kpl", UnitCost = 650000 });
            Items.Add(new WbsItem { Code = "5.1", Name = "Montáž, revize, oživení a zprovoznění", Category = "Labor", Quantity = 1, Unit = "kpl", UnitCost = 1450000 });
        }

        private void RecalculateTotals()
        {
            double baseSum = Items.Sum(x => x.TotalCost);
            double vat = baseSum * 0.21;
            double grant = 4350000;
            double net = (baseSum + vat) - grant;

            txtBaseTotal.Text = $"{baseSum:N0} Kč";
            txtVatTotal.Text = $"{vat:N0} Kč";
            txtGrantTotal.Text = $"-{grant:N0} Kč";
            txtNetTotal.Text = $"{net:N0} Kč";
        }

        private void BtnAddRow_Click(object sender, RoutedEventArgs e)
        {
            Items.Add(new WbsItem
            {
                Code = $"4.{Items.Count + 1}",
                Name = "Nová rozpočtová položka",
                Category = "Balance of System",
                Quantity = 1,
                Unit = "kpl",
                UnitCost = 50000
            });
            RecalculateTotals();
        }

        private void BtnGrant_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Uplatněna podpora z Modernizačního fondu ve výši 30 % způsobilých výdajů.\nSnížení čistých nákladů o 4 350 000 Kč.", "Investiční Podpora", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }
}
