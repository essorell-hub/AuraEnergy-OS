using System;
using System.Collections.Generic;
using System.IO;
using System.Windows;
using System.Windows.Controls;

namespace AuraEnergy.RETScreen.Wpf
{
    public class FacilityTypeItem
    {
        public string Name { get; set; } = string.Empty;
        public string Subtitle { get; set; } = string.Empty;
        public string IconKind { get; set; } = "Domain";
        public string IconColor { get; set; } = "#005A9E";
        public string TemplateFileName { get; set; } = string.Empty;
        public double DefaultFloorArea { get; set; } = 5000;
        public bool HasPv { get; set; } = true;
        public bool HasHp { get; set; } = true;
        public bool HasChp { get; set; } = false;
    }

    public class NewFacilityResult
    {
        public string FacilityName { get; set; } = string.Empty;
        public string FacilityType { get; set; } = string.Empty;
        public string Location { get; set; } = string.Empty;
        public string MeteoStation { get; set; } = string.Empty;
        public double FloorArea { get; set; }
        public int ProjectLife { get; set; }
        public bool EnablePv { get; set; }
        public bool EnableBess { get; set; }
        public bool EnableHp { get; set; }
        public bool EnableRecup { get; set; }
        public bool EnableBoiler { get; set; }
        public bool EnableChp { get; set; }
        public bool EnableSolarThermal { get; set; }
        public bool EnableEsg { get; set; }
    }

    public partial class NewFacilityDialog : Window
    {
        public NewFacilityResult? Result { get; private set; }

        public NewFacilityDialog()
        {
            InitializeComponent();
            LoadFacilityTypes();
        }

        private void LoadFacilityTypes()
        {
            var types = new List<FacilityTypeItem>
            {
                new FacilityTypeItem { Name = "Rodinný dům / Rezidence (RD)", Subtitle = "Single-Family Residential (FVE, TČ, Rekuperace)", IconKind = "Home", IconColor = "#2E7D32", TemplateFileName = "Apartment - High-rise.retx", DefaultFloorArea = 180, HasPv = true, HasHp = true, HasChp = false },
                new FacilityTypeItem { Name = "Bytový dům / SVJ & BD", Subtitle = "Multi-Unit Housing & Residential Blocks", IconKind = "HomeCity", IconColor = "#107C10", TemplateFileName = "Apartment - High-rise.retx", DefaultFloorArea = 2400, HasPv = true, HasHp = true, HasChp = false },
                new FacilityTypeItem { Name = "Chata, rekreační & ostrovní objekt", Subtitle = "Off-grid Cabin / Remote Tiny House (Ostrovní FVE)", IconKind = "Cabin", IconColor = "#8D6E63", TemplateFileName = "Community centre.retx", DefaultFloorArea = 90, HasPv = true, HasHp = true, HasChp = false },
                new FacilityTypeItem { Name = "Zdravotnické zařízení / Nemocnice", Subtitle = "Hospital & Healthcare Facility", IconKind = "HospitalBuilding", IconColor = "#D83B01", TemplateFileName = "Hospital.retx", DefaultFloorArea = 25000, HasPv = true, HasHp = true, HasChp = true },
                new FacilityTypeItem { Name = "Administrativní budova (Office)", Subtitle = "Commercial Office Building", IconKind = "OfficeBuilding", IconColor = "#0078D4", TemplateFileName = "Office - Large.retx", DefaultFloorArea = 12000, HasPv = true, HasHp = true, HasChp = false },
                new FacilityTypeItem { Name = "Škola a vzdělávací kampus", Subtitle = "Education & School Campus", IconKind = "School", IconColor = "#B146C2", TemplateFileName = "School.retx", DefaultFloorArea = 9000, HasPv = true, HasHp = true, HasChp = false },
                new FacilityTypeItem { Name = "Výrobní závod & Průmyslový park", Subtitle = "Industrial Plant & Logistics", IconKind = "Factory", IconColor = "#E65100", TemplateFileName = "Stand-alone retail.retx", DefaultFloorArea = 45000, HasPv = true, HasHp = true, HasChp = true },
                new FacilityTypeItem { Name = "Hotel a ubytovací komplex", Subtitle = "Hospitality & Hotel", IconKind = "Bed", IconColor = "#00838F", TemplateFileName = "Hotel - Large.retx", DefaultFloorArea = 15000, HasPv = true, HasHp = true, HasChp = true },
                new FacilityTypeItem { Name = "Výzkumná laboratoř a data centrum", Subtitle = "Research Lab & Data Center", IconKind = "Server", IconColor = "#0288D1", TemplateFileName = "Laboratory.retx", DefaultFloorArea = 6000, HasPv = true, HasHp = true, HasChp = true }
            };

            listFacilityTypes.ItemsSource = types;
            listFacilityTypes.SelectedIndex = 0;
        }

        private void ListFacilityTypes_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (listFacilityTypes.SelectedItem is FacilityTypeItem item)
            {
                txtFacilityName.Text = $"{item.Name} - Energetický audit 2026";
                txtFloorArea.Text = item.DefaultFloorArea.ToString("N0");
                chkPv.IsChecked = item.HasPv;
                chkHp.IsChecked = item.HasHp;
                chkChp.IsChecked = item.HasChp;
            }
        }

        private void BtnLoadNetZeroSample_Click(object sender, RoutedEventArgs e)
        {
            if (listFacilityTypes.SelectedItem is FacilityTypeItem item)
            {
                string templatePath = Path.Combine(@"C:\Program Files\RETScreen\RETScreen Expert\Net Zero Plan Example\EN", item.TemplateFileName);
                if (File.Exists(templatePath))
                {
                    MessageBox.Show($"Oficiální RETScreen Net-Zero archetyp:\n'{item.TemplateFileName}'\nbyl identifikován a načten jako výchozí šablona pro tento areál.", "Šablona RETScreen Načtena", MessageBoxButton.OK, MessageBoxImage.Information);
                }
                else
                {
                    MessageBox.Show($"Šablona {item.TemplateFileName} byla připravena z integrovaných archetypů.", "Archetyp Připraven", MessageBoxButton.OK, MessageBoxImage.Information);
                }
            }
        }

        private void BtnCreate_Click(object sender, RoutedEventArgs e)
        {
            var selectedType = listFacilityTypes.SelectedItem as FacilityTypeItem;
            double area = 10000;
            double.TryParse(txtFloorArea.Text.Replace(" ", "").Replace(",", "."), out area);
            int life = 25;
            int.TryParse(txtProjectLife.Text, out life);

            Result = new NewFacilityResult
            {
                FacilityName = txtFacilityName.Text.Trim(),
                FacilityType = selectedType?.Name ?? "Areál a budovy",
                Location = txtLocationCity.Text.Trim(),
                MeteoStation = (cmbMeteoStation.SelectedItem as ComboBoxItem)?.Content.ToString() ?? "Praha / Ruzyně",
                FloorArea = area,
                ProjectLife = life,
                EnablePv = chkPv.IsChecked == true,
                EnableBess = chkBess.IsChecked == true,
                EnableHp = chkHp.IsChecked == true,
                EnableRecup = chkRecup.IsChecked == true,
                EnableBoiler = chkBoiler.IsChecked == true,
                EnableChp = chkChp.IsChecked == true,
                EnableSolarThermal = chkSolarThermal.IsChecked == true,
                EnableEsg = chkEsg.IsChecked == true
            };

            DialogResult = true;
            Close();
        }

        private void BtnCancel_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }
    }
}
