using System.Windows;
using System.Windows.Controls;

namespace AuraEnergy.RETScreen.Wpf
{
    public partial class ProductBrowserDialog : Window
    {
        public CertifiedProduct? SelectedProduct { get; private set; }

        public ProductBrowserDialog(string initialQuery = "")
        {
            InitializeComponent();
            txtSearch.Text = initialQuery;
            LoadData(initialQuery);
        }

        private void LoadData(string query)
        {
            var list = ProductDatabaseService.SearchProducts(query: query);
            gridProducts.ItemsSource = list;
            if (list.Count > 0)
            {
                gridProducts.SelectedIndex = 0;
            }
        }

        private void BtnSearch_Click(object sender, RoutedEventArgs e)
        {
            LoadData(txtSearch.Text.Trim());
        }

        private void TxtSearch_TextChanged(object sender, TextChangedEventArgs e)
        {
            if (txtSearch.Text.Length > 2)
            {
                LoadData(txtSearch.Text.Trim());
            }
        }

        private void BtnSelect_Click(object sender, RoutedEventArgs e)
        {
            if (gridProducts.SelectedItem is CertifiedProduct prod)
            {
                SelectedProduct = prod;
                DialogResult = true;
                Close();
            }
            else
            {
                MessageBox.Show("Vyberte prosím produkt ze seznamu.", "Výběr", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void BtnClose_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }
    }
}
