from django.core.management.base import BaseCommand
from django.test.client import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
import json


class Command(BaseCommand):
    help = 'Test financial API endpoints'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Test with admin user
        admin_user = User.objects.get(username='admin')
        
        # Create a test client and login
        client = Client()
        
        # Get JWT token for admin user
        login_response = client.post('/api/auth/login/', {
            'username': 'admin',
            'password': 'admin123'  # Assuming this is the admin password
        })
        
        if login_response.status_code == 200:
            token_data = json.loads(login_response.content)
            access_token = token_data['access']
            
            # Test financial dashboard endpoint
            self.stdout.write('Testing financial dashboard endpoint...')
            headers = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}
            
            dashboard_response = client.get(
                '/api/core/financial-dashboard/dashboard/?date_from=2025-06-01&date_to=2025-06-18',
                **headers
            )
            
            self.stdout.write(f'Dashboard response status: {dashboard_response.status_code}')
            
            if dashboard_response.status_code == 200:
                data = json.loads(dashboard_response.content)
                self.stdout.write(self.style.SUCCESS('✓ Dashboard API working!'))
                self.stdout.write(f'Net balance: ${data["transactions"]["net_balance"]}')
                self.stdout.write(f'Total debits: ${data["transactions"]["total_debits"]}')
                self.stdout.write(f'Total credits: ${data["transactions"]["total_credits"]}')
            else:
                self.stdout.write(self.style.ERROR(f'✗ Dashboard API failed: {dashboard_response.content}'))
            
            # Test bank book endpoint
            self.stdout.write('\nTesting bank book endpoint...')
            bankbook_response = client.get(
                '/api/core/financial-dashboard/bank_book/?date_from=2025-06-01&date_to=2025-06-18',
                **headers
            )
            
            self.stdout.write(f'Bank book response status: {bankbook_response.status_code}')
            
            if bankbook_response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('✓ Bank book API working!'))
                data = json.loads(bankbook_response.content)
                entry_count = len(data.get('entries', []))
                self.stdout.write(f'Bank book entries: {entry_count}')
            else:
                self.stdout.write(self.style.ERROR(f'✗ Bank book API failed: {bankbook_response.content}'))
                
        else:
            self.stdout.write(self.style.ERROR(f'Login failed: {login_response.content}'))
            self.stdout.write('Available users:')
            for user in User.objects.all():
                self.stdout.write(f'  {user.username} (role: {user.role})')
