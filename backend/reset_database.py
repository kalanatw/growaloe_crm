#!/usr/bin/env python
"""
Script to completely reset the database and start fresh
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from django.conf import settings

def reset_database():
    """Reset the entire database"""
    print("🔄 Starting database reset...")
    
    # Drop all tables
    print("📋 Dropping all tables...")
    with connection.cursor() as cursor:
        # Get all table names
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename NOT LIKE 'pg_%'
        """)
        tables = cursor.fetchall()
        
        if tables:
            # Drop all tables
            table_names = [table[0] for table in tables]
            cursor.execute(f"DROP TABLE IF EXISTS {', '.join(table_names)} CASCADE")
            print(f"✅ Dropped {len(table_names)} tables")
        else:
            print("ℹ️  No tables to drop")
    
    # Delete all migration files (except __init__.py)
    print("🗑️  Deleting migration files...")
    apps = ['accounts', 'products', 'sales', 'reports', 'core', 'finance']
    
    for app in apps:
        migrations_dir = f"{app}/migrations"
        if os.path.exists(migrations_dir):
            for file in os.listdir(migrations_dir):
                if file.endswith('.py') and file != '__init__.py':
                    file_path = os.path.join(migrations_dir, file)
                    os.remove(file_path)
                    print(f"   Deleted {file_path}")
    
    # Recreate migrations
    print("📝 Creating fresh migrations...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    
    # Apply migrations
    print("⚡ Applying migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Create superuser
    print("👤 Creating superuser...")
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User',
            role='developer'
        )
        print("✅ Created admin user (username: admin, password: admin123)")
    
    print("🎉 Database reset complete!")
    print("\n📋 Next steps:")
    print("1. Start the server: python manage.py runserver")
    print("2. Login with admin/admin123")
    print("3. Create your owner, salesman, and shop profiles")

if __name__ == '__main__':
    reset_database()