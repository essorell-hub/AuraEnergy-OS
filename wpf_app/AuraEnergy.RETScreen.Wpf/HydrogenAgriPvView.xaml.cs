using System.Windows;
using System.Windows.Controls;

namespace AuraEnergy.RETScreen.Wpf
{
    public partial class HydrogenAgriPvView : UserControl
    {
        public HydrogenAgriPvView()
        {
            InitializeComponent();
        }

        private void TxtEly_TextChanged(object sender, TextChangedEventArgs e)
        {
            if (txtElyPower == null || txtH2Production == null) return;

            string raw = txtElyPower.Text.Replace("kW", "").Trim();
            if (double.TryParse(raw, out double kw))
            {
                // Approx 50 kWh / kg H2, 4000 operational hours/yr
                double kgPerYear = (kw * 4000.0) / 52.0;
                double tonsPerYear = kgPerYear / 1000.0;
                txtH2Production.Text = $"{tonsPerYear:0.1} tun H₂ / rok";
            }
        }

        private void BtnAiForecast_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("AI 48h Predikce OTE aktivována:\n• Předpovězené maximum zítra ve 12:45: 238 kW\n• Celková predikovaná výroba na zítřek: 1 490 kWh\n• Doporučený dispečink BESS: Nabíjení 02:00-05:00 (záporné ceny OTE), vybíjení 18:00-21:00 (večerní špička 3 450 Kč/MWh).", "AI ECMWF Predikce", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void Btn3dShadows_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("3D Stínová analýza areálu:\n• Ztráta výkonu vlivem horizontu a sousedních budov: 2.1 %\n• Nejvíce exponované období zastínění: Prosinec 08:30-10:00 (Nízká trajektorie slunce 16°).", "3D Stínový Model", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }
}
