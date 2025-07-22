#!/bin/bash

# Aloe Vera Paradise Database Reset Script
# This script resets the database and creates a fresh admin user

echo "🌿 Aloe Vera Paradise - Database Reset Script"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "backend/manage.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   (The directory containing backend/ and frontend/ folders)"
    exit 1
fi

# Navigate to backend directory
cd backend

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not detected. Attempting to activate..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ Virtual environment not found. Please activate it manually:"
        echo "   cd backend && source venv/bin/activate"
        exit 1
    fi
fi

# Check if Django is available
python -c "import django" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Django not found. Please install requirements:"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Run the reset script
echo "🚀 Starting database reset..."
python reset_database.py

# Check if reset was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Database reset completed successfully!"
    echo ""
    echo "🔗 Quick Links:"
    echo "   Admin Panel: http://localhost:8000/admin/"
    echo "   Frontend:    http://localhost:3000/"
    echo ""
    echo "👤 Admin Credentials:"
    echo "   Username: admin"
    echo "   Password: admin123"
    echo ""
    echo "🚀 To start the servers:"
    echo "   Backend:  cd backend && python manage.py runserver"
    echo "   Frontend: cd frontend && npm start"
else
    echo "❌ Database reset failed. Please check the error messages above."
    exit 1
fi