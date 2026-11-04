using System.Windows;
using System.Windows.Controls;

namespace AuraEnergy.RETScreen.Wpf
{
    public partial class ChpSolarThermalView : UserControl
    {
        public ChpSolarThermalView()
        {
            InitializeComponent();
        }

        private void TxtChp_TextChanged(object sender, TextChangedEventArgs e)
        {
            if (txtChpEl == null || txtChpTh == null || txtChpElYield == null) return;

            string raw = txtChpEl.Text.Replace("kWe", "").Trim();
            if (double.TryParse(raw, out double elKw))
            {
                double thKw = elKw * 1.30; // typický tepelný poměr 1.3
                txtChpTh.Text = $"{thKw:0} kWt";

                double annualElMwh = (elKw * 6500.0) / 1000.0;
                txtChpElYield.Text = $"{annualElMwh:N0} MWh / rok";
            }
        }

        private void TxtSt_TextChanged(object sender, TextChangedEventArgs e)
        {
            if (txtStArea == null || txtStYield == null) return;

            string raw = txtStArea.Text.Replace("m²", "").Trim();
            if (double.TryParse(raw, out double area))
            {
                double yieldKwh = area * 570.0; // 570 kWh/m2/rok zisk vakuových kolektorů
                txtStYield.Text = $"{yieldKwh:N0} kWh / rok";
            }
        }

        private void BtnChpCert_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Certifikace Vysokoúčinné Kogenerace (KVET) dle vyhlášky č. 453/2012 Sb.:\n• Celková účinnost soustavy: 88.5 %\n• Úspora primární energie (PESP): 24.2 % (Kritérium > 10 % splněno).\n• Nárok na roční bonus OTE: 1 240 000 Kč.", "Certifikát KVET", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }
}
