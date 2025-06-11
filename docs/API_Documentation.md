# Business Management API Documentation

## Overview

This is a comprehensive business management system API built with Django REST Framework. The API provides endpoints for managing users, products, sales, and reports for a distribution business.

**Base URL:** `http://127.0.0.1:8000/api/`

**API Documentation:**
- **Swagger UI:** http://127.0.0.1:8000/api/docs/
- **ReDoc:** http://127.0.0.1:8000/api/redoc/
- **OpenAPI Schema:** http://127.0.0.1:8000/api/schema/

## Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Authentication Endpoints

#### 1. Login
- **Endpoint:** `POST /api/auth/login/`
- **Description:** Authenticate user and get JWT tokens
- **Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```
- **Response:**
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token"
}
```

#### 2. Refresh Token
- **Endpoint:** `POST /api/auth/refresh/`
- **Description:** Refresh access token using refresh token
- **Request Body:**
```json
{
  "refresh": "jwt_refresh_token"
}
```

#### 3. Register
- **Endpoint:** `POST /api/auth/register/`
- **Description:** Register a new user
- **Request Body:**
```json
{
  "username": "string",
  "email": "email@example.com",
  "password": "string",
  "confirm_password": "string",
  "first_name": "string",
  "last_name": "string",
  "role": "OWNER|SALESMAN|SHOP",
  "phone": "string",
  "address": "string"
}
```

#### 4. Profile
- **Endpoint:** `GET /api/auth/profile/`
- **Description:** Get current user profile
- **Authentication Required:** Yes

#### 5. Change Password
- **Endpoint:** `POST /api/auth/change-password/`
- **Description:** Change user password
- **Authentication Required:** Yes
- **Request Body:**
```json
{
  "old_password": "string",
  "new_password": "string",
  "confirm_password": "string"
}
```

## User Management

### Users
- **Base Endpoint:** `/api/auth/users/`
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Permissions:** Authenticated users

#### List Users
- **Endpoint:** `GET /api/auth/users/`
- **Description:** Get list of all users
- **Query Parameters:**
  - `role`: Filter by user role
  - `is_active`: Filter by active status
  - `search`: Search by username, email, name

#### User Actions
- **Activate User:** `POST /api/auth/users/{id}/activate/`
- **Deactivate User:** `POST /api/auth/users/{id}/deactivate/`

### Owners
- **Base Endpoint:** `/api/auth/owners/`
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Description:** Manage business owners

### Salesmen
- **Base Endpoint:** `/api/auth/salesmen/`
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Description:** Manage salesmen

#### Salesman Actions
- **Summary:** `GET /api/auth/salesmen/summary/` - Get salesmen summary

### Shops
- **Base Endpoint:** `/api/auth/shops/`
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Description:** Manage shops

#### Shop Actions
- **Summary:** `GET /api/auth/shops/summary/` - Get shops summary
- **Balance History:** `GET /api/auth/shops/{id}/balance_history/` - Get balance history

### Margin Policies
- **Base Endpoint:** `/api/auth/margin-policies/`
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Description:** Manage margin policies

## Product Management

### Categories
- **Base Endpoint:** `/api/products/categories/`
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Description:** Manage product categories

### Products
- **Base Endpoint:** `/api/products/products/`
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Description:** Manage products

#### Product Actions
- **Stock Summary:** `GET /api/products/products/stock_summary/` - Get stock summary for all products
- **Stock by Salesman:** `GET /api/products/products/{id}/stock_by_salesman/` - Get stock distribution for a specific product

### Salesman Stock
- **Base Endpoint:** `/api/products/salesman-stock/`
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Description:** Manage salesman stock allocations

#### Salesman Stock Actions
- **My Stock:** `GET /api/products/salesman-stock/my_stock/` - Get current user's stock (for salesmen)
- **Salesman Summary:** `GET /api/products/salesman-stock/salesman_summary/` - Get stock summary by salesman

### Stock Movements
- **Base Endpoint:** `/api/products/stock-movements/`
- **Methods:** GET (Read-only)
- **Description:** View stock movement history

## Sales Management

### Invoices
- **Base Endpoint:** `/api/sales/invoices/`
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Description:** Manage sales invoices

#### Invoice Actions
- **Generate PDF:** `POST /api/sales/invoices/{id}/generate_pdf/` - Generate PDF for an invoice
- **Update Status:** `PATCH /api/sales/invoices/{id}/update_status/` - Update invoice status
- **Summary:** `GET /api/sales/invoices/summary/` - Get invoice summary statistics

### Invoice Items
- **Base Endpoint:** `/api/sales/invoice-items/`
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Description:** Manage invoice line items

### Transactions
- **Base Endpoint:** `/api/sales/transactions/`
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Description:** Manage payment transactions

#### Transaction Actions
- **Summary:** `GET /api/sales/transactions/summary/` - Get transaction summary by type and method

### Returns
- **Base Endpoint:** `/api/sales/returns/`
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Description:** Manage product returns

#### Return Actions
- **Approve:** `PATCH /api/sales/returns/{id}/approve/` - Approve a return request
- **Pending:** `GET /api/sales/returns/pending/` - Get pending returns

### Sales Analytics
- **Base Endpoint:** `/api/sales/analytics/`
- **Methods:** GET (ViewSet actions only)
- **Description:** Sales analytics and reports

#### Sales Analytics Actions
- **Sales Performance:** `GET /api/sales/analytics/sales_performance/` - Get sales performance by salesman
- **Monthly Trends:** `GET /api/sales/analytics/monthly_trends/` - Get monthly sales trends
- **Top Products:** `GET /api/sales/analytics/top_products/` - Get top selling products

## Reports Management

### Dashboard Metrics
- **Base Endpoint:** `/api/reports/dashboard-metrics/`
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Description:** Manage dashboard metrics

#### Dashboard Metrics Actions
- **Generate Current:** `POST /api/reports/dashboard-metrics/generate_current/` - Generate dashboard metrics for current date
- **Latest:** `GET /api/reports/dashboard-metrics/latest/` - Get latest dashboard metrics

### Sales Reports
- **Base Endpoint:** `/api/reports/sales-reports/`
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Description:** Manage sales reports

### Inventory Reports
- **Base Endpoint:** `/api/reports/inventory-reports/`
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Description:** Manage inventory reports

### Financial Reports
- **Base Endpoint:** `/api/reports/financial-reports/`
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Description:** Manage financial reports
- **Permissions:** Owner/Developer only

### Reports Analytics
- **Base Endpoint:** `/api/reports/analytics/`
- **Methods:** GET (ViewSet actions only)
- **Description:** Advanced reporting and analytics

#### Reports Analytics Actions
- **Summary:** `GET /api/reports/analytics/summary/` - Get reports summary
- **Sales Analytics:** `GET /api/reports/analytics/sales_analytics/` - Get sales analytics data
- **Product Performance:** `GET /api/reports/analytics/product_performance/` - Get product performance analytics

## User Roles & Permissions

### Role Types
1. **OWNER** - Full access to all features
2. **SALESMAN** - Access to own sales data and assigned shops
3. **SHOP** - Access to own purchase history and transactions

### Permission Levels
- **IsOwnerOrDeveloper** - Only owners and developers can access
- **IsAuthenticated** - Any authenticated user can access
- **Role-based filtering** - Data is filtered based on user role

## Common Query Parameters

Most list endpoints support the following query parameters:

### Filtering
- **Field-based filtering:** Filter by specific field values
- **Search:** Search across multiple fields
- **Ordering:** Sort results by specified fields

### Pagination
- **page:** Page number (default: 1)
- **page_size:** Number of items per page (default: 20)

### Example Filter Usage
```
GET /api/products/products/?category=1&is_active=true&search=apple&ordering=-created_at&page=2
```

## Response Format

### Success Response
```json
{
  "count": 100,
  "next": "http://127.0.0.1:8000/api/products/products/?page=3",
  "previous": "http://127.0.0.1:8000/api/products/products/?page=1",
  "results": [
    // Array of objects
  ]
}
```

### Error Response
```json
{
  "detail": "Error message",
  "errors": {
    "field_name": ["Field specific error message"]
  }
}
```

## Status Codes

- **200 OK** - Success
- **201 Created** - Resource created successfully
- **400 Bad Request** - Invalid request data
- **401 Unauthorized** - Authentication required
- **403 Forbidden** - Permission denied
- **404 Not Found** - Resource not found
- **500 Internal Server Error** - Server error

## Sample Data

To create sample data for testing, run:

```bash
cd backend
source venv/bin/activate
python manage.py create_sample_data
```

This will create:
- 1 Owner account
- 2 Salesman accounts
- 2 Shop accounts
- Product categories and products
- Sample invoices and transactions
- Stock allocations

## Testing the API

### Using curl

#### 1. Login
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_owner",
    "password": "password123"
  }'
```

#### 2. Get Products (with authentication)
```bash
curl -X GET http://127.0.0.1:8000/api/products/products/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Using the Swagger UI

1. Visit http://127.0.0.1:8000/api/docs/
2. Click "Authorize" button
3. Get a token by calling the login endpoint
4. Enter the token in the format: `Bearer YOUR_ACCESS_TOKEN`
5. Test any endpoint directly from the browser

## Environment Setup

1. **Clone the repository**
2. **Navigate to backend directory**
3. **Activate virtual environment:** `source venv/bin/activate`
4. **Install dependencies:** `pip install -r requirements.txt`
5. **Run migrations:** `python manage.py migrate`
6. **Create sample data:** `python manage.py create_sample_data`
7. **Start server:** `python manage.py runserver`

## Sample API Calls

### Get All Products
```bash
GET /api/products/products/
```

### Create New Invoice
```bash
POST /api/sales/invoices/
{
  "shop": 1,
  "items": [
    {
      "product": 1,
      "quantity": 5,
      "unit_price": "10.00"
    }
  ]
}
```

### Get Sales Analytics
```bash
GET /api/sales/analytics/monthly_trends/
```

For more detailed information and to test the API interactively, visit the Swagger documentation at http://127.0.0.1:8000/api/docs/
