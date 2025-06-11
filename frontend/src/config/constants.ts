// API Configuration
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// App Configuration
export const APP_CONFIG = {
  name: 'Grow Aloe',
  version: '1.0.0',
  description: 'Business Management System',
};

// Theme Configuration
export const THEME_CONFIG = {
  colors: {
    primary: '#2563eb',
    secondary: '#f97316',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6',
  },
};

// Invoice Status
export const INVOICE_STATUS = {
  DRAFT: 'draft',
  PENDING: 'pending',
  PAID: 'paid',
  PARTIAL: 'partial',
  OVERDUE: 'overdue',
  CANCELLED: 'cancelled',
} as const;

// Payment Methods
export const PAYMENT_METHODS = {
  CASH: 'cash',
  CHEQUE: 'cheque',
  BANK_TRANSFER: 'bank_transfer',
  BILL_TO_BILL: 'bill_to_bill',
  RETURNS: 'returns',
} as const;

// User Roles
export const USER_ROLES = {
  DEVELOPER: 'developer',
  OWNER: 'owner',
  SALESMAN: 'salesman',
  SHOP: 'shop',
} as const;

// Local Storage Keys
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_DATA: 'user_data',
  THEME: 'theme',
} as const;
