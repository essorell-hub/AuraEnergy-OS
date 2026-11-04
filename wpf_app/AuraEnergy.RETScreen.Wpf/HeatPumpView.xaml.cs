using System.Windows;
using System.Windows.Controls;

namespace AuraEnergy.RETScreen.Wpf
{
    public partial class HeatPumpView : UserControl
    {
        private double _unitKw = 60.0;

        public HeatPumpView()
        {
            InitializeComponent();
        }

        private void BtnBrowseHp_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new ProductBrowserDialog("Pump") { Owner = Window.GetWindow(this) };
            if (dlg.ShowDialog() == true && dlg.SelectedProduct != null)
            {
                var p = dlg.SelectedProduct;
                txtHpModel.Text = $"{p.Manufacturer} {p.Name} ({p.Capacity:0.0} kWt)";
                _unitKw = p.Capacity > 0 ? p.Capacity : 60.0;
                Recalculate();
            }
        }

        private void TxtHpParam_TextChanged(object sender, TextChangedEventArgs e)
        {
            Recalculate();
        }

        private void Recalculate()
        {
            if (txtHpCount == null || txtHpCapacity == null || txtHeatSupply == null || txtGasSavings == null || txtGhgSaved == null) return;

            if (int.TryParse(txtHpCount.Text, out int count))
            {
                double totalKw = count * _unitKw;
                txtHpCapacity.Text = $"{totalKw:0.0} kWt";

                double annualHeatKwh = totalKw * 2900.0; // 2900 full load hours
                txtHeatSupply.Text = $"{annualHeatKwh:N0} kWh/rok";

                double savedGasM3 = annualHeatKwh / 10.5 * 0.92; // 10.5 kWh/m3, 92% boiler eta
                txtGasSavings.Text = $"{savedGasM3:N0} m³ / rok";

                double ghgTons = (savedGasM3 * 2.02) / 1000.0;
                txtGhgSaved.Text = $"{ghgTons:0.1} t CO₂ / rok";
            }
        }
    }
}
