# Grow Aloe CRM System

A comprehensive Customer Relationship Management (CRM) system built with Django REST Framework and React, specifically designed for businesses managing salesmen, shops, products, and invoicing workflows.

## 🚀 Features

### Backend (Django REST Framework)
- **User Management**: Role-based authentication (Owner, Developer, Salesman, Shop)
- **Product Management**: Products with categories, stock tracking, and pricing
- **Inventory Control**: Salesman stock allocation and movement tracking
- **Invoice System**: Complete invoicing with PDF generation using ReportLab
- **Transaction Management**: Payment tracking and transaction history
- **Analytics Dashboard**: Sales performance and trend analytics
- **API Documentation**: Comprehensive Swagger/OpenAPI documentation

### Frontend (React + TypeScript)
- **Modern UI**: Clean, responsive design with Tailwind CSS
- **Dashboard**: Real-time analytics and key metrics
- **Invoice Creation**: Modal-based invoice creation with shop and product selection
- **PDF Generation**: Automatic PDF download for invoices
- **Role-based Access**: Different interfaces based on user roles
- **Dark/Light Theme**: User preference theme switching

## 🛠️ Technology Stack

### Backend
- **Framework**: Django 5.0.7 + Django REST Framework 3.15.2
- **Database**: PostgreSQL with psycopg2-binary
- **Authentication**: JWT with SimpleJWT
- **PDF Generation**: ReportLab 4.2.2 (pure Python, no system dependencies)
- **API Documentation**: drf-spectacular
- **CORS**: django-cors-headers

### Frontend
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS
- **Forms**: React Hook Form
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Notifications**: React Hot Toast
- **Routing**: React Router DOM

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- npm or yarn

## 🔧 Installation

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/kalanatw/growaloe_crm.git
   cd growaloe_crm/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and settings
   ```

5. **Database Setup**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic
   ```

6. **Create Sample Data (Optional)**
   ```bash
   python manage.py create_sample_data
   ```

7. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd ../frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm start
   ```

## 🔐 Environment Variables

Create a `.env` file in the backend directory with the following variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# CORS Settings
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## 📚 API Documentation

Once the backend server is running, access the interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/api/schema/swagger-ui/`
- **ReDoc**: `http://localhost:8000/api/schema/redoc/`

## 🏗️ Project Structure

```
growaloe_crm/
├── backend/
│   ├── accounts/          # User management and authentication
│   ├── products/          # Product and inventory management
│   ├── sales/             # Invoices, transactions, analytics
│   ├── core/              # Company settings and configuration
│   ├── reports/           # Reporting functionality
│   └── business_management/ # Django project settings
├── frontend/
│   ├── src/
│   │   ├── components/    # Reusable React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API service functions
│   │   ├── contexts/      # React contexts
│   │   └── types/         # TypeScript type definitions
│   └── public/
└── docs/                  # Documentation files
```

## 🎯 Key Features Explained

### Role-Based Access Control
- **Owner/Developer**: Full system access
- **Salesman**: Manage own products and create invoices
- **Shop**: View assigned invoices and transactions

### Invoice Management
- Modal-based invoice creation
- Real-time total calculations with margins
- Automatic PDF generation and download
- Customizable invoice templates

### PDF Generation
- Uses ReportLab (pure Python, no system dependencies)
- Professional invoice templates
- Customizable company branding
- Automatic file naming and download

### Stock Management
- Automatic stock movement tracking
- Salesman-specific stock allocation
- Real-time availability checking
- Stock reduction on invoice creation

## 🧪 Testing

### Backend Tests
```bash
cd backend
python manage.py test
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🚀 Deployment

### Backend Deployment
1. Set `DEBUG=False` in production
2. Configure proper database settings
3. Set up static file serving
4. Use gunicorn for WSGI server

### Frontend Deployment
1. Build the React app: `npm run build`
2. Serve static files through a web server

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Contact: [kalanathathsara99@gmail.com]

## 🔄 Recent Updates

- ✅ Replaced WeasyPrint with ReportLab for system-independent PDF generation
- ✅ Enhanced invoice creation with modal-based interface
- ✅ Added automatic PDF download functionality
- ✅ Implemented comprehensive stock management
- ✅ Added role-based permission system
- ✅ Created customizable company settings

---

**Grow Aloe CRM** - Streamlining business operations with modern technology.
