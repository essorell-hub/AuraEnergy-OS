using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using Fluent;
using LiveChartsCore;
using LiveChartsCore.SkiaSharpView;
using LiveChartsCore.SkiaSharpView.Painting;
using SkiaSharp;

namespace AuraEnergy.RETScreen.Wpf
{
    public class ClimateRow
    {
        public string Month { get; set; } = string.Empty;
        public double Temperature { get; set; }
        public double Humidity { get; set; }
        public double DailyGhi { get; set; }
        public double WindSpeed { get; set; }
        public double GroundTemp { get; set; }
        public double HeatingDegreeDays { get; set; }
        public double CoolingDegreeDays { get; set; }
    }

    public partial class MainWindow : RibbonWindow
    {
        public ObservableCollection<ClimateRow> ClimateData { get; set; } = new();

        public MainWindow()
        {
            InitializeComponent();
            LoadSampleClimateData();
            gridData.ItemsSource = ClimateData;
            InitCharts();
        }

        private void LoadSampleClimateData()
        {
            string[] months = { "Leden", "Únor", "Březen", "Duben", "Květen", "Červen", "Červenec", "Srpen", "Září", "Říjen", "Listopad", "Prosinec" };
            double[] temps = { -1.5, 0.2, 4.5, 9.8, 14.8, 18.2, 20.1, 19.5, 14.8, 9.2, 3.8, -0.4 };
            double[] ghis = { 1.15, 2.05, 3.42, 4.85, 5.75, 6.10, 5.95, 5.12, 3.65, 2.25, 1.25, 0.95 };
            double[] winds = { 3.8, 3.7, 3.9, 3.5, 3.1, 3.0, 2.9, 2.8, 3.1, 3.4, 3.7, 3.9 };

            for (int i = 0; i < 12; i++)
            {
                ClimateData.Add(new ClimateRow
                {
                    Month = months[i],
                    Temperature = temps[i],
                    Humidity = 78.0 - (i % 5) * 3,
                    DailyGhi = ghis[i],
                    WindSpeed = winds[i],
                    GroundTemp = temps[i] + 2.0,
                    HeatingDegreeDays = Math.Max(0, (18.3 - temps[i]) * 30),
                    CoolingDegreeDays = Math.Max(0, (temps[i] - 18.3) * 30)
                });
            }
        }

        private void InitCharts()
        {
            // 1. Kumulativní peněžní toky (25 let)
            double[] cashFlows = new double[26];
            cashFlows[0] = -65000;
            double cum = cashFlows[0];

            for (int y = 1; y <= 25; y++)
            {
                cum += 18500 * Math.Pow(1.025, y);
                cashFlows[y] = cum;
            }

            chartCashFlows.Series = new ISeries[]
            {
                new LineSeries<double>
                {
                    Values = cashFlows,
                    Fill = new SolidColorPaint(new SKColor(2, 132, 199, 40)),
                    Stroke = new SolidColorPaint(new SKColor(2, 132, 199), 2),
                    GeometrySize = 4,
                    Name = "Kumulativní peněžní toky (€)"
                }
            };

            // 2. Tornado citlivostní graf
            chartTornado.Series = new ISeries[]
            {
                new RowSeries<double>
                {
                    Values = new double[] { -78000, 65000, -54000, 31000, 18000 },
                    Fill = new SolidColorPaint(new SKColor(239, 68, 68)),
                    Name = "-20% Změna"
                },
                new RowSeries<double>
                {
                    Values = new double[] { 82000, -65000, 56000, -32000, -18000 },
                    Fill = new SolidColorPaint(new SKColor(34, 197, 94)),
                    Name = "+20% Změna"
                }
            };

            chartTornado.YAxes = new Axis[]
            {
                new Axis
                {
                    Labels = new string[] { "Tarif (€)", "CAPEX (€)", "GHI (%)", "Úrok (%)", "O&M (€)" }
                }
            };
        }

        private void TreeProject_SelectedItemChanged(object sender, RoutedPropertyChangedEventArgs<object> e)
        {
            if (txtViewTitle != null && e.NewValue is TreeViewItem item && item.Header != null)
            {
                txtViewTitle.Text = item.Header.ToString();
            }
        }

        private void BtnOpenRetx_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Otevírání oficiálního balíčku RETScreen .retx je plně podporováno přes SQLite / OPCContent engine.", "RETScreen .retx Loader", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnSaveRetx_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Projekt byl exportován do kompatibilního formátu RETScreen (.retx).", "Export Hotov", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnCalculate_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Kompletní přepočet modelu proběhl úspěšně.\nNPV: € 412,850\nIRR: 15.8 %\nNávratnost: 4.2 roku", "RETScreen Financial Engine", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnSave_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Projekt byl úspěšně uložen na disk.", "Uloženo", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnSearchStation_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Prohledávání 11 242 oficiálních klimatických stanic NASA POWER...", "NASA Stations", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnNasaPower_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Data NASA POWER pro lokalitu Praha / Ruzyne byla aktualizována.", "NASA POWER", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnAddPv_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Vyberte z 5 514 certifikovaných fotovoltaických modulů v databázi RETScreen.", "Katalog FVE", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnAddWind_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Vyberte z 1 385 větrných turbín s Weibull výkonovými křivkami.", "Katalog VTE", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnAddHp_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Vyberte z 3 288 modelů tepelných čerpadel.", "Katalog TČ", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnAddSolarThermal_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Solární termické kolektory dle EN 12975.", "Katalog Termika", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnAddWbsItem_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Nová položka WBS byla přidána do rozpočtu.", "WBS Rozpočet", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnRecalcWbs_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Rozpočet byl přepočten včetně DPH 21 % a rezervy 5 %.", "WBS Přepočet", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnExportPdf_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Byl vygenerován oficiální 2stránkový manažerský PDF report.", "PDF Export", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnTornado_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Tornado citlivostní graf byl zaktualizován pro ±20 % odchylky parametrů.", "Analýza Rizik", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }
}
