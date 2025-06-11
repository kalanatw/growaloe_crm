export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  phone?: string;
  address?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Salesman {
  id: number;
  user: User;
  owner: number;
  name: string;
  description?: string;
  profit_margin: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Shop {
  id: number;
  salesman: Salesman;
  user?: User;
  name: string;
  address: string;
  contact_person: string;
  phone: string;
  email?: string;
  shop_code?: string;
  shop_margin: number;
  credit_limit: number;
  current_balance: number;
  payment_terms?: string;
  is_active: boolean;
  date_created?: string;
  date_updated?: string;
  created_at: string;
  updated_at: string;
}

export interface Category {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Product {
  id: number;
  name: string;
  description?: string;
  sku: string;
  category?: Category;
  category_name?: string;
  image_url?: string;
  cost_price: number;
  base_price: number;
  unit: string;
  stock_quantity: number;
  min_stock_level: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SalesmanStock {
  id: number;
  salesman: number;
  salesman_name: string;
  product: number;
  product_name: string;
  product_sku: string;
  product_base_price: number;
  allocated_quantity: number;
  available_quantity: number;
  created_at: string;
  updated_at: string;
}

export interface InvoiceItem {
  id: number;
  product: number | { id: number; name: string; sku: string; };
  product_name: string;
  product_sku: string;
  quantity: number;
  unit_price: number;
  calculated_price: number;
  total_price: number;
  salesman_margin: number;
  shop_margin: number;
  line_total: number;
}

export interface Invoice {
  id: number;
  invoice_number: string;
  salesman: number;
  salesman_name: string;
  shop: number;
  shop_name: string;
  invoice_date: string;
  due_date?: string;
  subtotal: number;
  tax_amount: number;
  tax_rate?: number;
  discount_amount: number;
  discount?: number;
  net_total: number;
  paid_amount: number;
  balance_due: number;
  total_amount: number;
  status: string;
  notes?: string;
  terms_conditions?: string;
  payment_method?: string;
  payment_date?: string;
  date_created?: string;
  created_by?: number;
  created_at: string;
  updated_at: string;
  items: InvoiceItem[];
  items_count: number;
}

export interface Transaction {
  id: number;
  invoice: number;
  invoice_number: string;
  shop?: Shop;
  payment_method: string;
  amount: number;
  transaction_type: string;
  status: string;
  description?: string;
  reference_number?: string;
  bank_name?: string;
  cheque_date?: string;
  transaction_date: string;
  date_created: string;
  created_by?: number;
  processed_by_name?: string;
  notes?: string;
  created_at: string;
}

export interface CreateInvoiceData {
  shop: number;
  due_date?: string;
  tax_amount?: number;
  discount_amount?: number;
  notes?: string;
  terms_conditions?: string;
  items: {
    product: number;
    quantity: number;
    unit_price: number;
    salesman_margin?: number;
    shop_margin?: number;
  }[];
}

export interface CreateShopData {
  name: string;
  address: string;
  contact_person: string;
  phone: string;
  email?: string;
  shop_margin?: number;
  credit_limit?: number;
  is_active?: boolean;
}

export interface CreateTransactionData {
  invoice?: number;
  shop_id?: string;
  payment_method: string;
  amount: number;
  transaction_type?: string;
  description?: string;
  reference_number?: string;
  bank_name?: string;
  cheque_date?: string;
  notes?: string;
}

export interface CreateUserData {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  phone?: string;
  address?: string;
  role: string;
}

export interface CreateSalesmanData {
  user: CreateUserData;
  name: string;
  description?: string;
  profit_margin: number;
  is_active?: boolean;
}

export interface CreateProductData {
  name: string;
  description?: string;
  sku: string;
  category?: number;
  image_url?: string;
  cost_price: number;
  base_price: number;
  unit: string;
  stock_quantity?: number;
  min_stock_level?: number;
  is_active?: boolean;
}

export interface ProfitCalculation {
  cost_price: number;
  base_price: number;
  selling_price: number;
  total_profit: number;
  salesman_margin_amount: number;
  shop_margin_amount: number;
  owner_profit: number;
  profit_percentage: number;
}

export interface SalesAnalytics {
  salesman_id: number;
  salesman_name: string;
  total_sales: number;
  total_invoices: number;
  average_sale: number;
  commission_earned: number;
}

export interface MonthlyTrend {
  month: string;
  month_name: string;
  total_sales: number;
  invoice_count: number;
}

export interface TopProduct {
  product__id: number;
  product__name: string;
  product__sku: string;
  total_quantity: number;
  total_revenue: number;
}

export interface AnalyticsData {
  totalSales?: number;
  totalOrders?: number;
  totalShops?: number;
  totalProductsSold?: number;
  salesGrowth?: number;
  ordersGrowth?: number;
  productsGrowth?: number;
  averageOrderValue?: number;
  totalProfitMargin?: number;
  pendingPayments?: number;
  salesByDay?: Array<{
    date: string;
    total_sales: number;
  }>;
  topProducts?: Array<{
    product_name: string;
    quantity_sold: number;
  }>;
  revenueByMonth?: Array<{
    month: string;
    revenue: number;
  }>;
}

export interface CompanySettings {
  id: number;
  company_name: string;
  company_address: string;
  company_phone: string;
  company_email: string;
  company_website?: string;
  company_tax_id?: string;
  company_logo?: string;
  primary_color: string;
  secondary_color: string;
  invoice_prefix: string;
  invoice_footer_text: string;
  show_logo_on_invoice: boolean;
  show_company_details: boolean;
  default_tax_rate: number;
  default_currency: string;
  currency_symbol: string;
  default_payment_terms?: string;
  default_due_days: number;
  created_at: string;
  updated_at: string;
}

export interface UpdateCompanySettingsData {
  company_name?: string;
  company_address?: string;
  company_phone?: string;
  company_email?: string;
  company_website?: string;
  company_tax_id?: string;
  company_logo?: File;
  primary_color?: string;
  secondary_color?: string;
  invoice_prefix?: string;
  invoice_footer_text?: string;
  show_logo_on_invoice?: boolean;
  show_company_details?: boolean;
  default_tax_rate?: number;
  default_currency?: string;
  currency_symbol?: string;
  default_payment_terms?: string;
  default_due_days?: number;
}
