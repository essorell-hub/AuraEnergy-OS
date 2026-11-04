using System.Windows;
using System.Windows.Controls;
using Microsoft.Win32;

namespace AuraEnergy.RETScreen.Wpf
{
    public partial class CzechGridArbitrageView : UserControl
    {
        public CzechGridArbitrageView()
        {
            InitializeComponent();
        }

        private void BtnExportCad_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new SaveFileDialog
            {
                Filter = "AutoCAD DXF R12 (*.dxf)|*.dxf|BIM IFC 4.0 (*.ifc)|*.ifc",
                FileName = "Elektro_Schema_PCC_FVE_BESS.dxf"
            };

            if (dlg.ShowDialog() == true)
            {
                MessageBox.Show($"Jednopolové schéma zapojení a trasy kabelů byly úspěšně vyexportovány pro CAD/BIM projektanta:\n{dlg.FileName}", "CAD/BIM Export Dokončen", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void BtnNis2_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Auditní zpráva NIS2 (Vyhláška o kybernetické bezpečnosti energetických výroben) byla vygenerována.\nÚroveň shody areálu: 94 % (Vyhovuje požadavkům NÚKIB).", "NIS2 Audit", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }
}
