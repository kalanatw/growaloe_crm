# API Testing Guide

## Quick Start Guide

This guide will help you quickly test the Business Management API using the Swagger UI and sample data.

## Prerequisites

1. **Start the Django server:**
```bash
cd /Users/kalana/Desktop/Personal/ZentraLabs/grow-aloe/backend
source venv/bin/activate
python manage.py runserver
```

2. **Create sample data (if not already done):**
```bash
python manage.py create_sample_data
```

## Accessing the API Documentation

- **Swagger UI:** http://127.0.0.1:8000/api/docs/
- **ReDoc:** http://127.0.0.1:8000/api/redoc/
- **OpenAPI Schema:** http://127.0.0.1:8000/api/schema/

## Authentication Setup

### Step 1: Get Authentication Token

1. Open Swagger UI: http://127.0.0.1:8000/api/docs/
2. Navigate to **Authentication** section
3. Click on **POST /api/auth/login/**
4. Click "Try it out"
5. Use these sample credentials:

**Owner Account:**
```json
{
  "username": "john_owner",
  "password": "password123"
}
```

**Salesman Account:**
```json
{
  "username": "mike_sales",
  "password": "password123"
}
```

**Shop Account:**
```json
{
  "username": "corner_shop",
  "password": "password123"
}
```

6. Click "Execute"
7. Copy the `access` token from the response

### Step 2: Authorize in Swagger

1. Click the **"Authorize"** button at the top of Swagger UI
2. Enter: `Bearer YOUR_ACCESS_TOKEN` (replace with actual token)
3. Click "Authorize"
4. Click "Close"

Now you can test all authenticated endpoints!

## Testing Different User Roles

### As Owner (john_owner)
- **Full Access:** Can view and manage all data
- **Test Cases:**
  - View all invoices: `GET /api/sales/invoices/`
  - View all products: `GET /api/products/products/`
  - Create new products: `POST /api/products/products/`
  - View financial reports: `GET /api/reports/financial-reports/`

### As Salesman (mike_sales)
- **Limited Access:** Can only see own data
- **Test Cases:**
  - View own invoices: `GET /api/sales/invoices/`
  - View assigned stock: `GET /api/products/salesman-stock/my_stock/`
  - Create invoices: `POST /api/sales/invoices/`
  - View sales performance: `GET /api/sales/analytics/sales_performance/`

### As Shop (corner_shop)
- **Shop Access:** Can see purchase history
- **Test Cases:**
  - View shop invoices: `GET /api/sales/invoices/`
  - View transactions: `GET /api/sales/transactions/`
  - Create returns: `POST /api/sales/returns/`

## Sample API Test Scenarios

### Scenario 1: Create a New Invoice

1. **Login as Salesman:** Use `mike_sales` credentials
2. **Get Available Stock:**
   ```
   GET /api/products/salesman-stock/my_stock/
   ```
3. **Create Invoice:**
   ```
   POST /api/sales/invoices/
   ```
   Request Body:
   ```json
   {
     "shop": 1,
     "customer_name": "Test Customer",
     "customer_phone": "+1234567890",
     "due_date": "2025-06-15",
     "items": [
       {
         "product": 1,
         "quantity": 5,
         "unit_price": "4.00"
       },
       {
         "product": 2,
         "quantity": 3,
         "unit_price": "4.50"
       }
     ],
     "discount_amount": "2.00",
     "notes": "Test invoice created via API"
   }
   ```

### Scenario 2: Process a Payment

1. **Create Transaction:**
   ```
   POST /api/sales/transactions/
   ```
   Request Body:
   ```json
   {
     "invoice": 1,
     "transaction_type": "PAYMENT",
     "payment_method": "CASH",
     "amount": "35.50",
     "reference_number": "TXN-TEST-001",
     "notes": "Cash payment received"
   }
   ```

### Scenario 3: Process a Return

1. **Create Return:**
   ```
   POST /api/sales/returns/
   ```
   Request Body:
   ```json
   {
     "invoice": 1,
     "product": 1,
     "quantity_returned": 2,
     "reason": "DAMAGED",
     "notes": "Product damaged during transport"
   }
   ```

2. **Approve Return (as Owner):**
   ```
   PATCH /api/sales/returns/{return_id}/approve/
   ```

### Scenario 4: Generate Reports

1. **Dashboard Metrics:**
   ```
   GET /api/reports/dashboard-metrics/latest/
   ```

2. **Sales Analytics:**
   ```
   GET /api/sales/analytics/monthly_trends/
   ```

3. **Product Performance:**
   ```
   GET /api/reports/analytics/product_performance/
   ```

## Advanced Testing

### Filtering and Search

1. **Filter Invoices by Status:**
   ```
   GET /api/sales/invoices/?status=PAID
   ```

2. **Search Products:**
   ```
   GET /api/products/products/?search=apple
   ```

3. **Order by Date:**
   ```
   GET /api/sales/invoices/?ordering=-created_at
   ```

### Pagination

```
GET /api/sales/invoices/?page=2&page_size=10
```

### Complex Filtering

```
GET /api/sales/invoices/?status=PAID&salesman=1&invoice_date=2025-06-01&ordering=-total_amount
```

## Error Testing

### Test Invalid Data

1. **Invalid Login:**
   ```json
   {
     "username": "invalid_user",
     "password": "wrong_password"
   }
   ```

2. **Invalid Invoice Data:**
   ```json
   {
     "shop": 999,
     "items": []
   }
   ```

3. **Unauthorized Access:**
   - Try accessing `/api/reports/financial-reports/` as a salesman

## Performance Testing

### Test with Large Datasets

1. **Pagination Performance:**
   ```
   GET /api/sales/invoices/?page=1&page_size=100
   ```

2. **Search Performance:**
   ```
   GET /api/products/products/?search=test
   ```

## API Response Examples

### Successful Invoice Creation
```json
{
  "id": 6,
  "invoice_number": "INV-2025-1006",
  "salesman": {
    "id": 1,
    "name": "Mike Johnson"
  },
  "shop": {
    "id": 1,
    "name": "Corner Grocery Store"
  },
  "customer_name": "Test Customer",
  "customer_phone": "+1234567890",
  "invoice_date": "2025-06-01",
  "due_date": "2025-06-15",
  "subtotal": "33.50",
  "discount_amount": "2.00",
  "net_total": "31.50",
  "status": "DRAFT",
  "items": [
    {
      "id": 11,
      "product": {
        "id": 1,
        "name": "Organic Bananas",
        "sku": "ORG-BAN-001"
      },
      "quantity": 5,
      "unit_price": "4.00",
      "total_price": "20.00"
    },
    {
      "id": 12,
      "product": {
        "id": 2,
        "name": "Red Apples",
        "sku": "RED-APP-001"
      },
      "quantity": 3,
      "unit_price": "4.50",
      "total_price": "13.50"
    }
  ],
  "created_at": "2025-06-01T16:30:00Z"
}
```

### Error Response Example
```json
{
  "shop": [
    "Invalid pk \"999\" - object does not exist."
  ],
  "items": [
    "This field may not be empty."
  ]
}
```

## Tips for Testing

1. **Always authenticate first** - Most endpoints require authentication
2. **Use the correct user role** - Test with different roles to verify permissions
3. **Check response status codes** - 200/201 for success, 400 for validation errors, 403 for permissions
4. **Validate response structure** - Ensure responses match expected format
5. **Test edge cases** - Try invalid data, non-existent IDs, etc.
6. **Use sample data** - Run `create_sample_data` command for realistic test data

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check if token is valid and not expired
   - Ensure "Bearer " prefix in Authorization header

2. **403 Forbidden**
   - User doesn't have permission for this action
   - Try with a different user role

3. **404 Not Found**
   - Check if the resource ID exists
   - Verify the URL path is correct

4. **400 Bad Request**
   - Check request body format
   - Validate required fields are provided
   - Ensure data types are correct

### Debug Steps

1. Check Django server logs in terminal
2. Verify database has sample data
3. Test with Swagger UI first, then external tools
4. Use browser developer tools to inspect network requests

## Next Steps

After testing the API:

1. **Frontend Integration:** Use these endpoints in your React frontend
2. **Mobile App:** Build mobile apps using these APIs
3. **Third-party Integration:** Connect with other business systems
4. **Custom Reports:** Build custom dashboards using the analytics endpoints
