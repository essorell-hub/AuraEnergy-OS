using System.Windows;
using System.Windows.Controls;

namespace AuraEnergy.RETScreen.Wpf
{
    public partial class PvSystemView : UserControl
    {
        private double _moduleWp = 670.0;

        public PvSystemView()
        {
            InitializeComponent();
        }

        private void BtnBrowsePv_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new ProductBrowserDialog("Solar") { Owner = Window.GetWindow(this) };
            if (dlg.ShowDialog() == true && dlg.SelectedProduct != null)
            {
                var p = dlg.SelectedProduct;
                txtPvModel.Text = $"{p.Manufacturer} {p.Name} ({p.Capacity * 1000:0} Wp)";
                _moduleWp = p.Capacity > 10 ? p.Capacity : p.Capacity * 1000;
                Recalculate();
            }
        }

        private void TxtPvCount_TextChanged(object sender, TextChangedEventArgs e)
        {
            Recalculate();
        }

        private void Recalculate()
        {
            if (txtPvCount == null || txtPvKwp == null || txtAnnualGen == null) return;

            if (int.TryParse(txtPvCount.Text, out int count))
            {
                double totalKwp = (count * _moduleWp) / 1000.0;
                txtPvKwp.Text = $"{totalKwp:0.1} kWp";
                double annualKwh = totalKwp * 1220.0; // 1-axis tracker specific yield
                txtAnnualGen.Text = $"{annualKwh:N0} kWh/rok";
            }
        }
    }
}
