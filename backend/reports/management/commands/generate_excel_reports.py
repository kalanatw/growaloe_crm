"""
Management command to generate Excel reports for testing and automation
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import os

from reports.excel_service import ExcelReportService, generate_all_reports


class Command(BaseCommand):
    help = 'Generate Excel reports for testing and automation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--report-type',
            type=str,
            choices=[
                'master_dashboard',
                'delivery_performance', 
                'salesman_performance',
                'cash_flow_analysis',
                'product_analytics',
                'customer_analysis',
                'all'
            ],
            default='all',
            help='Type of report to generate'
        )
        
        parser.add_argument(
            '--date-from',
            type=str,
            help='Start date (YYYY-MM-DD)'
        )
        
        parser.add_argument(
            '--date-to',
            type=str,
            help='End date (YYYY-MM-DD)'
        )
        
        parser.add_argument(
            '--period',
            type=str,
            choices=['today', 'week', 'month', 'quarter'],
            default='month',
            help='Predefined period for report generation'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting Excel report generation...')
        )
        
        # Determine date range
        date_from, date_to = self.get_date_range(options)
        
        self.stdout.write(
            f'Generating reports for period: {date_from} to {date_to}'
        )
        
        try:
            service = ExcelReportService()
            report_type = options['report_type']
            
            if report_type == 'all':
                # Generate all reports
                reports = generate_all_reports(date_from, date_to)
                
                self.stdout.write(
                    self.style.SUCCESS(f'Generated {len(reports)} reports:')
                )
                
                for report_name, filepath in reports.items():
                    if os.path.exists(filepath):
                        file_size = os.path.getsize(filepath) / 1024  # KB
                        self.stdout.write(
                            f'  ✓ {report_name}: {os.path.basename(filepath)} ({file_size:.1f} KB)'
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ {report_name}: File not found')
                        )
            
            else:
                # Generate specific report
                filepath = self.generate_single_report(service, report_type, date_from, date_to)
                
                if filepath and os.path.exists(filepath):
                    file_size = os.path.getsize(filepath) / 1024  # KB
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Generated {report_type}: {os.path.basename(filepath)} ({file_size:.1f} KB)'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to generate {report_type}')
                    )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating reports: {str(e)}')
            )
            raise
        
        self.stdout.write(
            self.style.SUCCESS('Excel report generation completed!')
        )

    def get_date_range(self, options):
        """Determine date range based on options"""
        if options['date_from'] and options['date_to']:
            date_from = datetime.strptime(options['date_from'], '%Y-%m-%d').date()
            date_to = datetime.strptime(options['date_to'], '%Y-%m-%d').date()
        else:
            today = timezone.now().date()
            period = options['period']
            
            if period == 'today':
                date_from = today
                date_to = today
            elif period == 'week':
                date_from = today - timedelta(days=today.weekday())
                date_to = today
            elif period == 'quarter':
                # Current quarter
                quarter = (today.month - 1) // 3 + 1
                if quarter == 1:
                    date_from = today.replace(month=1, day=1)
                elif quarter == 2:
                    date_from = today.replace(month=4, day=1)
                elif quarter == 3:
                    date_from = today.replace(month=7, day=1)
                else:
                    date_from = today.replace(month=10, day=1)
                date_to = today
            else:  # month
                date_from = today.replace(day=1)
                date_to = today
        
        return date_from, date_to

    def generate_single_report(self, service, report_type, date_from, date_to):
        """Generate a single report based on type"""
        if report_type == 'master_dashboard':
            return service.generate_master_dashboard(date_from, date_to)
        elif report_type == 'delivery_performance':
            return service.generate_delivery_performance(date_from, date_to)
        elif report_type == 'salesman_performance':
            return service.generate_salesman_performance(date_from, date_to)
        elif report_type == 'cash_flow_analysis':
            return service.generate_cash_flow_analysis(date_from, date_to)
        elif report_type == 'product_analytics':
            return service.generate_product_analytics(date_from, date_to)
        elif report_type == 'customer_analysis':
            return service.generate_customer_analysis(date_from, date_to)
        else:
            raise ValueError(f'Unknown report type: {report_type}')