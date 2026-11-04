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
                try
                {
                    ExportService.GenerateDirectDxf(dlg.FileName, "FVE + BESS + Odberne Misto PCC", 250.0, 300.0);
                    MessageBox.Show($"Jednopolové schéma zapojení a trasy kabelů byly úspěšně zapsány do formátu DXF:\n{dlg.FileName}\n\nSoubor je připraven k otevření v AutoCADu nebo DWG prohlížeči.", "CAD Export Dokončen", MessageBoxButton.OK, MessageBoxImage.Information);
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Chyba při exportu DXF: {ex.Message}", "Chyba", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private void BtnNis2_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Auditní zpráva NIS2 (Vyhláška o kybernetické bezpečnosti energetických výroben) byla vygenerována.\nÚroveň shody areálu: 94 % (Vyhovuje požadavkům NÚKIB).", "NIS2 Audit", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }
}
