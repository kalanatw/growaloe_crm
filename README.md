# Business Management Web Application

A complete, scalable, and modern business management web application for distributed sales business.

## 🚀 Tech Stack

### Backend
- Python 3.11+
- Django 5.x with Django REST Framework
- PostgreSQL database
- Redis (for caching and task queues)
- WeasyPrint for PDF generation

### Frontend
- ReactJS with Hooks and Zustand for state management
- TailwindCSS for responsive design
- Headless UI components
- Axios for API communication
- Framer Motion for animations

## 📋 Features

- Multi-role user management (Owner, Salesman, Shop)
- Product inventory management
- Invoice generation with PDF export
- Margin and pricing management
- Payment tracking (Cash, Cheque, Return, Bill-to-Bill)
- Real-time dashboards and analytics
- Mobile-responsive design

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 13+
- Redis (optional)

### Backend Setup

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Setup PostgreSQL database and update `.env` file

4. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Create superuser:
```bash
python manage.py createsuperuser
```

6. Run development server:
```bash
python manage.py runserver
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm start
```

## 📱 User Roles

- **Developer (SuperUser):** Full system access
- **Owner:** Manage products, margins, salesmen, shops, view all transactions
- **Salesman:** View stock, create invoices, manage shop balances
- **Shop:** View invoice history and balances (read-only)

## 📊 API Documentation

API endpoints are available at `/api/docs/` when running the backend server.

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

## 📦 Deployment

See deployment guide in `docs/deployment.md`

## 📄 License

MIT License
