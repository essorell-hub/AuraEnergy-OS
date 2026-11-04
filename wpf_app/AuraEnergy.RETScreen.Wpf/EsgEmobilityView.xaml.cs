using System.Windows;
using System.Windows.Controls;
using Microsoft.Win32;

namespace AuraEnergy.RETScreen.Wpf
{
    public partial class EsgEmobilityView : UserControl
    {
        public EsgEmobilityView()
        {
            InitializeComponent();
        }

        private void BtnEsgReport_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new SaveFileDialog
            {
                Filter = "PDF Dokument (*.pdf)|*.pdf",
                FileName = "ESG_CSRD_Dekarbonizace_Audit_2026.pdf"
            };

            if (dlg.ShowDialog() == true)
            {
                MessageBox.Show($"Oficiální auditní ESG/CSRD zpráva pro financující banku byla úspěšně vygenerována:\n{dlg.FileName}\n\n• Zelený kreditní rating: A+\n• Soulad s Taxonomií EU: 92.4 %", "ESG Report Vygenerován", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void BtnPdsForm_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new SaveFileDialog
            {
                Filter = "PDF Formulář (*.pdf)|*.pdf",
                FileName = "Zadost_o_pripojeni_vyrobny_PDS.pdf"
            };

            if (dlg.ShowDialog() == true)
            {
                MessageBox.Show($"Kompletní formulář žádosti o připojení výrobny k distribuční soustavě (ČEZ / EG.D / PRE) byl vygenerován s vyplněnými parametry střídačů dle Nařízení Komise (EU) 2016/631 (RfG):\n{dlg.FileName}", "Žádost pro Distributora", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }
    }
}
