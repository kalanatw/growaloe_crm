import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ProductsPage } from './pages/ProductsPage';
import { NewCreateInvoicePage } from './pages/NewCreateInvoicePage';
import { InvoicesPage } from './pages/InvoicesPage';
import { ShopsPage } from './pages/ShopsPage';
import { CreateShopPage } from './pages/CreateShopPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { InvoiceDetailPage } from './pages/InvoiceDetailPage';
import { ShopDetailPage } from './pages/ShopDetailPage';
import { TransactionsPage } from './pages/TransactionsPage';
import { SalesmenPage } from './pages/SalesmenPage';
import { CreateSalesmanPage } from './pages/CreateSalesmanPage';
import { InvoiceSettlementPage } from './pages/InvoiceSettlementPage';
import { DeliveriesPage } from './pages/DeliveriesPage';
import { USER_ROLES } from './config/constants';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <Router>
            <div className="App">
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route
                  path="/"
                  element={
                    <ProtectedRoute allowedRoles={[USER_ROLES.OWNER, USER_ROLES.SALESMAN]}>
                      <DashboardPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/products"
                  element={
                    <ProtectedRoute allowedRoles={[USER_ROLES.OWNER]}>
                      <ProductsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/invoices/create"
                  element={
                    <ProtectedRoute allowedRoles={[USER_ROLES.OWNER, USER_ROLES.SALESMAN]}>
                      <NewCreateInvoicePage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/invoices"
                  element={
                    <ProtectedRoute allowedRoles={[USER_ROLES.OWNER, USER_ROLES.SALESMAN]}>
                      <InvoicesPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/shops"
                  element={
                    <ProtectedRoute allowedRoles={[USER_ROLES.OWNER, USER_ROLES.SALESMAN]}>
                      <ShopsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/shops/create"
                  element={
                    <ProtectedRoute allowedRoles={[USER_ROLES.OWNER, USER_ROLES.SALESMAN]}>
                      <CreateShopPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/shops/:id"
                  element={
                    <ProtectedRoute allowedRoles={[USER_ROLES.OWNER, USER_ROLES.SALESMAN]}>
                      <ShopDetailPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/invoices/:id"
                  element={
                    <ProtectedRoute allowedRoles={[USER_ROLES.OWNER, USER_ROLES.SALESMAN]}>
                      <InvoiceDetailPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/analytics"
                  element={
                    <ProtectedRoute allowedRoles={[USER_ROLES.OWNER, USER_ROLES.SALESMAN]}>
                      <AnalyticsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/transactions"
                  element={
                    <ProtectedRoute allowedRoles={[USER_ROLES.OWNER]}>
                      <TransactionsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/salesmen"
                  element={
                    <ProtectedRoute allowedRoles={[USER_ROLES.OWNER]}>
                      <SalesmenPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/salesmen/create"
                  element={
                    <ProtectedRoute allowedRoles={[USER_ROLES.OWNER]}>
                      <CreateSalesmanPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/deliveries"
                  element={
                    <ProtectedRoute allowedRoles={[USER_ROLES.OWNER, USER_ROLES.SALESMAN]}>
                      <DeliveriesPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/invoice-settlement"
                  element={
                    <ProtectedRoute allowedRoles={[USER_ROLES.OWNER, USER_ROLES.SALESMAN]}>
                      <InvoiceSettlementPage />
                    </ProtectedRoute>
                  }
                />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
              <Toaster
                position="top-right"
                toastOptions={{
                  duration: 4000,
                  style: {
                    background: 'var(--toast-bg)',
                    color: 'var(--toast-color)',
                  },
                }}
              />
            </div>
          </Router>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
