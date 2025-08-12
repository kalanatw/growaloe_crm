"""
Comprehensive Excel Reporting Service for Delivery Management System

This service generates professional Excel reports with business intelligence
for sales performance, delivery analytics, cash flows, and salesman performance.
"""

import os
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from django.db.models import Sum, Count, Avg, Q, F, Case, When, Value
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, NamedStyle
from openpyxl.chart import LineChart, PieChart, BarChart, Reference
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

# Import models
from sales.models import Invoice, InvoiceItem, Transaction
from products.models import Delivery, DeliveryItem, DeliverySettlement, DeliveryExpense, Product, BatchAssignment
from accounts.models import Salesman, Shop, Owner
from django.db import models

logger = logging.getLogger(__name__)


class ExcelReportService:
    """
    Comprehensive Excel reporting service for delivery management system
    """
    
    def __init__(self):
        self.workbook = None
        self.styles = {}
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup Excel styles for professional formatting"""
        # Header style
        self.styles['header'] = NamedStyle(name="header")
        self.styles['header'].font = Font(bold=True, color="FFFFFF", size=12)
        self.styles['header'].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        self.styles['header'].alignment = Alignment(horizontal="center", vertical="center")
        self.styles['header'].border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        
        # Subheader style
        self.styles['subheader'] = NamedStyle(name="subheader")
        self.styles['subheader'].font = Font(bold=True, size=11)
        self.styles['subheader'].fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        self.styles['subheader'].alignment = Alignment(horizontal="center", vertical="center")
        
        # Data style
        self.styles['data'] = NamedStyle(name="data")
        self.styles['data'].font = Font(size=10)
        self.styles['data'].alignment = Alignment(horizontal="left", vertical="center")
        self.styles['data'].border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        
        # Currency style
        self.styles['currency'] = NamedStyle(name="currency")
        self.styles['currency'].font = Font(size=10)
        self.styles['currency'].alignment = Alignment(horizontal="right", vertical="center")
        self.styles['currency'].number_format = 'LKR #,##0.00'
        
        # Percentage style
        self.styles['percentage'] = NamedStyle(name="percentage")
        self.styles['percentage'].font = Font(size=10)
        self.styles['percentage'].alignment = Alignment(horizontal="right", vertical="center")
        self.styles['percentage'].number_format = '0.00%'
        
        # KPI positive style
        self.styles['kpi_positive'] = NamedStyle(name="kpi_positive")
        self.styles['kpi_positive'].font = Font(bold=True, color="00B050", size=11)
        self.styles['kpi_positive'].alignment = Alignment(horizontal="center", vertical="center")
        
        # KPI negative style
        self.styles['kpi_negative'] = NamedStyle(name="kpi_negative")
        self.styles['kpi_negative'].font = Font(bold=True, color="C00000", size=11)
        self.styles['kpi_negative'].alignment = Alignment(horizontal="center", vertical="center")
    
    def generate_master_dashboard(self, date_from: datetime, date_to: datetime, **filters) -> str:
        """
        Generate Master Sales Dashboard Report
        Executive summary for business owners
        """
        logger.info(f"Generating Master Dashboard Report from {date_from} to {date_to}")
        
        self.workbook = Workbook()
        ws = self.workbook.active
        ws.title = "Master Dashboard"
        
        # Report header
        self._add_report_header(ws, "Master Sales Dashboard", date_from, date_to)
        
        # KPI Summary Section
        row = self._add_kpi_summary(ws, date_from, date_to, start_row=4)
        
        # Sales Performance Section
        row = self._add_sales_performance(ws, date_from, date_to, start_row=row + 3)
        
        # Top Performers Section
        row = self._add_top_performers(ws, date_from, date_to, start_row=row + 3)
        
        # Trend Analysis Section
        self._add_trend_analysis(ws, date_from, date_to, start_row=row + 3)
        
        # Auto-adjust column widths
        self._auto_adjust_columns(ws)
        
        # Save file
        filename = f"master_dashboard_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.xlsx"
        filepath = self._save_report(filename)
        
        logger.info(f"Master Dashboard Report generated: {filepath}")
        return filepath
    
    def generate_delivery_performance(self, date_from: datetime, date_to: datetime, **filters) -> str:
        """
        Generate Delivery Performance Report
        Track delivery efficiency and settlement status
        """
        logger.info(f"Generating Delivery Performance Report from {date_from} to {date_to}")
        
        self.workbook = Workbook()
        
        # Main delivery performance sheet
        ws_main = self.workbook.active
        ws_main.title = "Delivery Overview"
        self._add_delivery_overview(ws_main, date_from, date_to)
        
        # Delivery details sheet
        ws_details = self.workbook.create_sheet("Delivery Details")
        self._add_delivery_details(ws_details, date_from, date_to)
        
        # Settlement analysis sheet
        ws_settlement = self.workbook.create_sheet("Settlement Analysis")
        self._add_settlement_analysis(ws_settlement, date_from, date_to)
        
        # Expense analysis sheet
        ws_expenses = self.workbook.create_sheet("Expense Analysis")
        self._add_expense_analysis(ws_expenses, date_from, date_to)
        
        filename = f"delivery_performance_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.xlsx"
        filepath = self._save_report(filename)
        
        logger.info(f"Delivery Performance Report generated: {filepath}")
        return filepath
    
    def generate_salesman_performance(self, date_from: datetime, date_to: datetime, **filters) -> str:
        """
        Generate Salesman Performance Report
        Individual and comparative salesman analysis
        """
        logger.info(f"Generating Salesman Performance Report from {date_from} to {date_to}")
        
        self.workbook = Workbook()
        
        # Performance summary sheet
        ws_summary = self.workbook.active
        ws_summary.title = "Performance Summary"
        self._add_salesman_summary(ws_summary, date_from, date_to)
        
        # Individual performance sheets for each salesman
        salesmen = Salesman.objects.filter(is_active=True)
        for salesman in salesmen:
            ws_individual = self.workbook.create_sheet(f"{salesman.name[:20]}")
            self._add_individual_salesman_performance(ws_individual, salesman, date_from, date_to)
        
        # Comparative analysis sheet
        ws_comparison = self.workbook.create_sheet("Comparative Analysis")
        self._add_salesman_comparison(ws_comparison, date_from, date_to)
        
        filename = f"salesman_performance_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.xlsx"
        filepath = self._save_report(filename)
        
        logger.info(f"Salesman Performance Report generated: {filepath}")
        return filepath
    
    def generate_cash_flow_analysis(self, date_from: datetime, date_to: datetime, **filters) -> str:
        """
        Generate Cash Flow Analysis Report
        Financial flow tracking and liquidity management
        """
        logger.info(f"Generating Cash Flow Analysis Report from {date_from} to {date_to}")
        
        self.workbook = Workbook()
        
        # Cash flow summary
        ws_summary = self.workbook.active
        ws_summary.title = "Cash Flow Summary"
        self._add_cash_flow_summary(ws_summary, date_from, date_to)
        
        # Payment method analysis
        ws_payments = self.workbook.create_sheet("Payment Analysis")
        self._add_payment_method_analysis(ws_payments, date_from, date_to)
        
        # Outstanding analysis
        ws_outstanding = self.workbook.create_sheet("Outstanding Analysis")
        self._add_outstanding_analysis(ws_outstanding, date_from, date_to)
        
        # Settlement tracking
        ws_settlements = self.workbook.create_sheet("Settlement Tracking")
        self._add_settlement_tracking(ws_settlements, date_from, date_to)
        
        filename = f"cash_flow_analysis_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.xlsx"
        filepath = self._save_report(filename)
        
        logger.info(f"Cash Flow Analysis Report generated: {filepath}")
        return filepath
    
    def generate_product_analytics(self, date_from: datetime, date_to: datetime, **filters) -> str:
        """
        Generate Product Analytics Report
        Product performance and inventory insights
        """
        logger.info(f"Generating Product Analytics Report from {date_from} to {date_to}")
        
        self.workbook = Workbook()
        
        # Product performance summary
        ws_summary = self.workbook.active
        ws_summary.title = "Product Performance"
        self._add_product_performance(ws_summary, date_from, date_to)
        
        # Inventory analysis
        ws_inventory = self.workbook.create_sheet("Inventory Analysis")
        self._add_inventory_analysis(ws_inventory, date_from, date_to)
        
        # Sales velocity analysis
        ws_velocity = self.workbook.create_sheet("Sales Velocity")
        self._add_sales_velocity_analysis(ws_velocity, date_from, date_to)
        
        # Margin analysis
        ws_margins = self.workbook.create_sheet("Margin Analysis")
        self._add_product_margin_analysis(ws_margins, date_from, date_to)
        
        filename = f"product_analytics_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.xlsx"
        filepath = self._save_report(filename)
        
        logger.info(f"Product Analytics Report generated: {filepath}")
        return filepath
    
    def generate_customer_analysis(self, date_from: datetime, date_to: datetime, **filters) -> str:
        """
        Generate Customer & Shop Analysis Report
        Customer relationship and territory analysis
        """
        logger.info(f"Generating Customer Analysis Report from {date_from} to {date_to}")
        
        self.workbook = Workbook()
        
        # Customer overview
        ws_overview = self.workbook.active
        ws_overview.title = "Customer Overview"
        self._add_customer_overview(ws_overview, date_from, date_to)
        
        # Shop performance
        ws_shops = self.workbook.create_sheet("Shop Performance")
        self._add_shop_performance(ws_shops, date_from, date_to)
        
        # Geographic analysis
        ws_geographic = self.workbook.create_sheet("Geographic Analysis")
        self._add_geographic_analysis(ws_geographic, date_from, date_to)
        
        # Payment behavior analysis
        ws_payment_behavior = self.workbook.create_sheet("Payment Behavior")
        self._add_payment_behavior_analysis(ws_payment_behavior, date_from, date_to)
        
        filename = f"customer_analysis_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.xlsx"
        filepath = self._save_report(filename)
        
        logger.info(f"Customer Analysis Report generated: {filepath}")
        return filepath
    
    def _add_report_header(self, ws, title: str, date_from: datetime, date_to: datetime):
        """Add professional report header"""
        # Main title
        ws.merge_cells('A1:H1')
        ws['A1'] = title
        ws['A1'].font = Font(bold=True, size=16, color="366092")
        ws['A1'].alignment = Alignment(horizontal="center", vertical="center")
        
        # Date range
        ws.merge_cells('A2:H2')
        ws['A2'] = f"Period: {date_from.strftime('%B %d, %Y')} to {date_to.strftime('%B %d, %Y')}"
        ws['A2'].font = Font(size=12, color="666666")
        ws['A2'].alignment = Alignment(horizontal="center", vertical="center")
        
        # Generation timestamp
        ws.merge_cells('A3:H3')
        ws['A3'] = f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}"
        ws['A3'].font = Font(size=10, color="999999")
        ws['A3'].alignment = Alignment(horizontal="center", vertical="center")
    
    def _add_kpi_summary(self, ws, date_from: datetime, date_to: datetime, start_row: int) -> int:
        """Add KPI summary section"""
        # Calculate KPIs
        kpis = self._calculate_kpis(date_from, date_to)
        
        # Section header
        ws.merge_cells(f'A{start_row}:H{start_row}')
        ws[f'A{start_row}'] = "KEY PERFORMANCE INDICATORS"
        ws[f'A{start_row}'].style = self.styles['header']
        
        # KPI headers
        headers = ['Metric', 'Current Period', 'Previous Period', 'Change', 'Trend']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=start_row + 1, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # KPI data
        row = start_row + 2
        for kpi_name, kpi_data in kpis.items():
            ws.cell(row=row, column=1, value=kpi_name).style = self.styles['data']
            ws.cell(row=row, column=2, value=kpi_data['current']).style = self.styles['currency']
            ws.cell(row=row, column=3, value=kpi_data['previous']).style = self.styles['currency']
            
            # Change calculation and styling
            change_cell = ws.cell(row=row, column=4, value=kpi_data['change_pct'])
            change_cell.style = self.styles['kpi_positive'] if kpi_data['change_pct'] >= 0 else self.styles['kpi_negative']
            change_cell.number_format = '0.0%'
            
            # Trend indicator
            trend_cell = ws.cell(row=row, column=5, value=kpi_data['trend'])
            trend_cell.style = self.styles['kpi_positive'] if kpi_data['trend'] == '↑' else self.styles['kpi_negative']
            
            row += 1
        
        return row
    
    def _calculate_kpis(self, date_from: datetime, date_to: datetime) -> Dict[str, Dict]:
        """Calculate key performance indicators"""
        # Current period data
        current_invoices = Invoice.objects.filter(
            invoice_date__range=[date_from, date_to]
        )
        
        # Previous period (same duration)
        period_days = (date_to - date_from).days
        prev_date_to = date_from - timedelta(days=1)
        prev_date_from = prev_date_to - timedelta(days=period_days)
        
        previous_invoices = Invoice.objects.filter(
            invoice_date__range=[prev_date_from, prev_date_to]
        )
        
        # Calculate metrics
        current_revenue = current_invoices.aggregate(total=Sum('net_total'))['total'] or Decimal('0')
        previous_revenue = previous_invoices.aggregate(total=Sum('net_total'))['total'] or Decimal('0')
        
        current_deliveries = Delivery.objects.filter(
            delivery_date__range=[date_from, date_to]
        ).count()
        previous_deliveries = Delivery.objects.filter(
            delivery_date__range=[prev_date_from, prev_date_to]
        ).count()
        
        current_outstanding = current_invoices.filter(
            status__in=['pending', 'partial']
        ).aggregate(total=Sum('balance_due'))['total'] or Decimal('0')
        
        previous_outstanding = previous_invoices.filter(
            status__in=['pending', 'partial']
        ).aggregate(total=Sum('balance_due'))['total'] or Decimal('0')
        
        # Calculate collection rate
        current_paid = current_invoices.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0')
        current_collection_rate = (current_paid / current_revenue * 100) if current_revenue > 0 else 0
        
        previous_paid = previous_invoices.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0')
        previous_collection_rate = (previous_paid / previous_revenue * 100) if previous_revenue > 0 else 0
        
        def calculate_change(current, previous):
            if previous == 0:
                return 1.0 if current > 0 else 0.0
            return float((current - previous) / previous)
        
        def get_trend(change_pct):
            return '↑' if change_pct > 0 else '↓' if change_pct < 0 else '→'
        
        return {
            'Total Revenue': {
                'current': float(current_revenue),
                'previous': float(previous_revenue),
                'change_pct': calculate_change(current_revenue, previous_revenue),
                'trend': get_trend(calculate_change(current_revenue, previous_revenue))
            },
            'Deliveries': {
                'current': current_deliveries,
                'previous': previous_deliveries,
                'change_pct': calculate_change(current_deliveries, previous_deliveries),
                'trend': get_trend(calculate_change(current_deliveries, previous_deliveries))
            },
            'Collection Rate': {
                'current': float(current_collection_rate),
                'previous': float(previous_collection_rate),
                'change_pct': calculate_change(current_collection_rate, previous_collection_rate),
                'trend': get_trend(calculate_change(current_collection_rate, previous_collection_rate))
            },
            'Outstanding': {
                'current': float(current_outstanding),
                'previous': float(previous_outstanding),
                'change_pct': calculate_change(current_outstanding, previous_outstanding),
                'trend': get_trend(-calculate_change(current_outstanding, previous_outstanding))  # Negative because less outstanding is better
            }
        }
    
    def _save_report(self, filename: str) -> str:
        """Save the Excel report and return filepath"""
        # Create reports directory if it doesn't exist
        reports_dir = os.path.join('media', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        filepath = os.path.join(reports_dir, filename)
        self.workbook.save(filepath)
        
        return filepath
    
    def _auto_adjust_columns(self, ws):
        """Auto-adjust column widths for better readability"""
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
            ws.column_dimensions[column_letter].width = adjusted_width    

    def _add_sales_performance(self, ws, date_from: datetime, date_to: datetime, start_row: int) -> int:
        """Add sales performance section"""
        # Section header
        ws.merge_cells(f'A{start_row}:H{start_row}')
        ws[f'A{start_row}'] = "SALES PERFORMANCE BREAKDOWN"
        ws[f'A{start_row}'].style = self.styles['header']
        
        # Get sales data by salesman
        sales_data = Invoice.objects.filter(
            invoice_date__range=[date_from, date_to]
        ).values(
            'salesman__name'
        ).annotate(
            total_sales=Sum('net_total'),
            total_invoices=Count('id'),
            avg_sale=Avg('net_total'),
            paid_amount=Sum('paid_amount'),
            outstanding=Sum('balance_due')
        ).order_by('-total_sales')
        
        # Headers
        headers = ['Salesman', 'Total Sales', 'Invoices', 'Avg Sale', 'Paid', 'Outstanding', 'Collection %']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=start_row + 1, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Data rows
        row = start_row + 2
        for data in sales_data:
            ws.cell(row=row, column=1, value=data['salesman__name']).style = self.styles['data']
            ws.cell(row=row, column=2, value=float(data['total_sales'] or 0)).style = self.styles['currency']
            ws.cell(row=row, column=3, value=data['total_invoices']).style = self.styles['data']
            ws.cell(row=row, column=4, value=float(data['avg_sale'] or 0)).style = self.styles['currency']
            ws.cell(row=row, column=5, value=float(data['paid_amount'] or 0)).style = self.styles['currency']
            ws.cell(row=row, column=6, value=float(data['outstanding'] or 0)).style = self.styles['currency']
            
            # Collection percentage
            collection_pct = (data['paid_amount'] / data['total_sales'] * 100) if data['total_sales'] else 0
            ws.cell(row=row, column=7, value=float(collection_pct)).style = self.styles['percentage']
            
            row += 1
        
        return row
    
    def _add_top_performers(self, ws, date_from: datetime, date_to: datetime, start_row: int) -> int:
        """Add top performers section"""
        # Section header
        ws.merge_cells(f'A{start_row}:H{start_row}')
        ws[f'A{start_row}'] = "TOP PERFORMERS"
        ws[f'A{start_row}'].style = self.styles['header']
        
        # Top salesmen by revenue
        top_salesmen = Invoice.objects.filter(
            invoice_date__range=[date_from, date_to]
        ).values(
            'salesman__name'
        ).annotate(
            total_sales=Sum('net_total'),
            collection_rate=Sum('paid_amount') * 100 / Sum('net_total')
        ).order_by('-total_sales')[:5]
        
        # Top products by revenue
        top_products = InvoiceItem.objects.filter(
            invoice__invoice_date__range=[date_from, date_to]
        ).values(
            'product__name'
        ).annotate(
            total_revenue=Sum(F('quantity') * F('unit_price')),
            total_quantity=Sum('quantity')
        ).order_by('-total_revenue')[:5]
        
        # Top salesmen table
        ws.cell(row=start_row + 1, column=1, value="Top Salesmen by Revenue").style = self.styles['subheader']
        headers = ['Rank', 'Salesman', 'Revenue', 'Collection Rate']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=start_row + 2, column=col, value=header)
            cell.style = self.styles['subheader']
        
        row = start_row + 3
        for rank, salesman in enumerate(top_salesmen, 1):
            ws.cell(row=row, column=1, value=rank).style = self.styles['data']
            ws.cell(row=row, column=2, value=salesman['salesman__name']).style = self.styles['data']
            ws.cell(row=row, column=3, value=float(salesman['total_sales'] or 0)).style = self.styles['currency']
            ws.cell(row=row, column=4, value=float(salesman['collection_rate'] or 0)).style = self.styles['percentage']
            row += 1
        
        # Top products table
        ws.cell(row=row + 1, column=1, value="Top Products by Revenue").style = self.styles['subheader']
        headers = ['Rank', 'Product', 'Revenue', 'Quantity Sold']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row + 2, column=col, value=header)
            cell.style = self.styles['subheader']
        
        row += 3
        for rank, product in enumerate(top_products, 1):
            ws.cell(row=row, column=1, value=rank).style = self.styles['data']
            ws.cell(row=row, column=2, value=product['product__name']).style = self.styles['data']
            ws.cell(row=row, column=3, value=float(product['total_revenue'] or 0)).style = self.styles['currency']
            ws.cell(row=row, column=4, value=product['total_quantity']).style = self.styles['data']
            row += 1
        
        return row
    
    def _add_trend_analysis(self, ws, date_from: datetime, date_to: datetime, start_row: int) -> int:
        """Add trend analysis section with charts"""
        # Section header
        ws.merge_cells(f'A{start_row}:H{start_row}')
        ws[f'A{start_row}'] = "TREND ANALYSIS"
        ws[f'A{start_row}'].style = self.styles['header']
        
        # Daily sales trend
        daily_sales = Invoice.objects.filter(
            invoice_date__range=[date_from, date_to]
        ).extra(
            select={'day': 'date(invoice_date)'}
        ).values('day').annotate(
            daily_revenue=Sum('net_total'),
            daily_invoices=Count('id')
        ).order_by('day')
        
        # Headers for trend data
        headers = ['Date', 'Revenue', 'Invoices', 'Avg per Invoice']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=start_row + 1, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Trend data
        row = start_row + 2
        for data in daily_sales:
            ws.cell(row=row, column=1, value=data['day']).style = self.styles['data']
            ws.cell(row=row, column=2, value=float(data['daily_revenue'] or 0)).style = self.styles['currency']
            ws.cell(row=row, column=3, value=data['daily_invoices']).style = self.styles['data']
            
            avg_per_invoice = (data['daily_revenue'] / data['daily_invoices']) if data['daily_invoices'] > 0 else 0
            ws.cell(row=row, column=4, value=float(avg_per_invoice)).style = self.styles['currency']
            row += 1
        
        return row
    
    def _add_delivery_overview(self, ws, date_from: datetime, date_to: datetime):
        """Add delivery overview to worksheet"""
        self._add_report_header(ws, "Delivery Performance Overview", date_from, date_to)
        
        # Delivery status summary
        delivery_stats = Delivery.objects.filter(
            delivery_date__range=[date_from, date_to]
        ).values('status').annotate(
            count=Count('id'),
            total_value=Sum('items__quantity') * Sum('items__unit_price')
        )
        
        # Section header
        ws.merge_cells('A5:F5')
        ws['A5'] = "DELIVERY STATUS SUMMARY"
        ws['A5'].style = self.styles['header']
        
        # Headers
        headers = ['Status', 'Count', 'Percentage', 'Total Value', 'Avg Value']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=6, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Data
        total_deliveries = sum(stat['count'] for stat in delivery_stats)
        row = 7
        for stat in delivery_stats:
            ws.cell(row=row, column=1, value=stat['status'].title()).style = self.styles['data']
            ws.cell(row=row, column=2, value=stat['count']).style = self.styles['data']
            
            percentage = (stat['count'] / total_deliveries * 100) if total_deliveries > 0 else 0
            ws.cell(row=row, column=3, value=percentage).style = self.styles['percentage']
            
            ws.cell(row=row, column=4, value=float(stat['total_value'] or 0)).style = self.styles['currency']
            
            avg_value = (stat['total_value'] / stat['count']) if stat['count'] > 0 else 0
            ws.cell(row=row, column=5, value=float(avg_value)).style = self.styles['currency']
            
            row += 1
    
    def _add_delivery_details(self, ws, date_from: datetime, date_to: datetime):
        """Add detailed delivery information"""
        self._add_report_header(ws, "Delivery Details", date_from, date_to)
        
        # Get detailed delivery data
        deliveries = Delivery.objects.filter(
            delivery_date__range=[date_from, date_to]
        ).select_related('salesman__user').prefetch_related('items__product')
        
        # Headers
        headers = [
            'Delivery Number', 'Salesman', 'Date', 'Status', 'Items Count', 
            'Total Value', 'Settlement Date', 'Margin Earned', 'Notes'
        ]
        
        row = 5
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Data rows
        row = 6
        for delivery in deliveries:
            ws.cell(row=row, column=1, value=delivery.delivery_number).style = self.styles['data']
            ws.cell(row=row, column=2, value=delivery.salesman.name).style = self.styles['data']
            ws.cell(row=row, column=3, value=delivery.delivery_date).style = self.styles['data']
            ws.cell(row=row, column=4, value=delivery.status.title()).style = self.styles['data']
            ws.cell(row=row, column=5, value=delivery.total_items).style = self.styles['data']
            ws.cell(row=row, column=6, value=delivery.total_value).style = self.styles['currency']
            ws.cell(row=row, column=7, value=delivery.settlement_date).style = self.styles['data']
            ws.cell(row=row, column=8, value=float(delivery.total_margin_earned)).style = self.styles['currency']
            ws.cell(row=row, column=9, value=delivery.notes or '').style = self.styles['data']
            row += 1
    
    def _add_settlement_analysis(self, ws, date_from: datetime, date_to: datetime):
        """Add settlement analysis"""
        self._add_report_header(ws, "Settlement Analysis", date_from, date_to)
        
        # Settlement turnaround analysis
        settlements = DeliverySettlement.objects.filter(
            settlement_date__range=[date_from, date_to]
        ).select_related('salesman__user')
        
        # Headers
        headers = [
            'Settlement Date', 'Salesman', 'Delivered Value', 'Cash Collected',
            'Sold Value', 'Cash Settled', 'Status'
        ]
        
        row = 5
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Data rows
        row = 6
        for settlement in settlements:
            ws.cell(row=row, column=1, value=settlement.settlement_date).style = self.styles['data']
            ws.cell(row=row, column=2, value=settlement.salesman.name).style = self.styles['data']
            ws.cell(row=row, column=3, value=float(settlement.total_delivered_value)).style = self.styles['currency']
            ws.cell(row=row, column=4, value=float(settlement.total_cash_collected)).style = self.styles['currency']
            ws.cell(row=row, column=5, value=float(settlement.total_sold_value)).style = self.styles['currency']
            ws.cell(row=row, column=6, value=float(settlement.cash_settled_amount)).style = self.styles['currency']
            ws.cell(row=row, column=7, value=settlement.status.title()).style = self.styles['data']
            row += 1
    
    def _add_expense_analysis(self, ws, date_from: datetime, date_to: datetime):
        """Add expense analysis"""
        self._add_report_header(ws, "Expense Analysis", date_from, date_to)
        
        # Expense breakdown by category
        expenses = DeliveryExpense.objects.filter(
            created_at__date__range=[date_from, date_to]
        ).values('category').annotate(
            total_amount=Sum('amount'),
            count=Count('id'),
            avg_amount=Avg('amount')
        ).order_by('-total_amount')
        
        # Headers
        headers = ['Category', 'Total Amount', 'Count', 'Average Amount', 'Percentage']
        
        row = 5
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Calculate total for percentage
        total_expenses = sum(exp['total_amount'] for exp in expenses)
        
        # Data rows
        row = 6
        for expense in expenses:
            ws.cell(row=row, column=1, value=expense['category'].title()).style = self.styles['data']
            ws.cell(row=row, column=2, value=float(expense['total_amount'])).style = self.styles['currency']
            ws.cell(row=row, column=3, value=expense['count']).style = self.styles['data']
            ws.cell(row=row, column=4, value=float(expense['avg_amount'])).style = self.styles['currency']
            
            percentage = (expense['total_amount'] / total_expenses * 100) if total_expenses > 0 else 0
            ws.cell(row=row, column=5, value=percentage).style = self.styles['percentage']
            
            row += 1
    
    def _add_salesman_summary(self, ws, date_from: datetime, date_to: datetime):
        """Add salesman performance summary"""
        self._add_report_header(ws, "Salesman Performance Summary", date_from, date_to)
        
        # Get comprehensive salesman data
        salesmen_data = Salesman.objects.filter(
            is_active=True
        ).annotate(
            total_sales=Sum(
                'invoices__net_total',
                filter=Q(invoices__invoice_date__range=[date_from, date_to])
            ),
            total_invoices=Count(
                'invoices',
                filter=Q(invoices__invoice_date__range=[date_from, date_to])
            ),
            total_deliveries=Count(
                'deliveries',
                filter=Q(deliveries__delivery_date__range=[date_from, date_to])
            ),
            cash_collected=Sum(
                'invoices__paid_amount',
                filter=Q(invoices__invoice_date__range=[date_from, date_to])
            ),
            outstanding_amount=Sum(
                'invoices__balance_due',
                filter=Q(invoices__invoice_date__range=[date_from, date_to])
            )
        ).order_by('-total_sales')
        
        # Headers
        headers = [
            'Rank', 'Salesman', 'Total Sales', 'Invoices', 'Deliveries',
            'Cash Collected', 'Outstanding', 'Collection Rate', 'Performance Score'
        ]
        
        row = 5
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Data rows with ranking
        row = 6
        for rank, salesman in enumerate(salesmen_data, 1):
            ws.cell(row=row, column=1, value=rank).style = self.styles['data']
            ws.cell(row=row, column=2, value=salesman.name).style = self.styles['data']
            ws.cell(row=row, column=3, value=float(salesman.total_sales or 0)).style = self.styles['currency']
            ws.cell(row=row, column=4, value=salesman.total_invoices or 0).style = self.styles['data']
            ws.cell(row=row, column=5, value=salesman.total_deliveries or 0).style = self.styles['data']
            ws.cell(row=row, column=6, value=float(salesman.cash_collected or 0)).style = self.styles['currency']
            ws.cell(row=row, column=7, value=float(salesman.outstanding_amount or 0)).style = self.styles['currency']
            
            # Collection rate
            collection_rate = 0
            if salesman.total_sales and salesman.total_sales > 0:
                collection_rate = (salesman.cash_collected or 0) / salesman.total_sales * 100
            ws.cell(row=row, column=8, value=collection_rate).style = self.styles['percentage']
            
            # Performance score (weighted average of sales, collection rate, and delivery efficiency)
            performance_score = self._calculate_performance_score(salesman, date_from, date_to)
            score_cell = ws.cell(row=row, column=9, value=performance_score)
            score_cell.style = self.styles['kpi_positive'] if performance_score >= 8 else self.styles['kpi_negative']
            
            row += 1
    
    def _calculate_performance_score(self, salesman, date_from: datetime, date_to: datetime) -> float:
        """Calculate performance score for salesman (0-10 scale)"""
        # Get salesman's metrics and convert to float
        total_sales = float(salesman.total_sales or 0)
        cash_collected = float(salesman.cash_collected or 0)
        total_deliveries = float(salesman.total_deliveries or 0)
        
        # Calculate component scores
        sales_score = min(10, (total_sales / 100000) * 10) if total_sales > 0 else 0  # Max at 100k
        collection_score = (cash_collected / total_sales * 10) if total_sales > 0 else 0
        delivery_score = min(10, total_deliveries) if total_deliveries > 0 else 0
        
        # Weighted average (40% sales, 40% collection, 20% delivery)
        performance_score = (sales_score * 0.4) + (collection_score * 0.4) + (delivery_score * 0.2)
        
        return round(performance_score, 1)
    
    def _add_individual_salesman_performance(self, ws, salesman: Salesman, date_from: datetime, date_to: datetime):
        """Add individual salesman performance sheet"""
        self._add_report_header(ws, f"Performance Report - {salesman.name}", date_from, date_to)
        
        # Individual metrics
        invoices = Invoice.objects.filter(
            salesman=salesman,
            invoice_date__range=[date_from, date_to]
        )
        
        deliveries = Delivery.objects.filter(
            salesman=salesman,
            delivery_date__range=[date_from, date_to]
        )
        
        # Key metrics section
        ws.merge_cells('A5:D5')
        ws['A5'] = "KEY METRICS"
        ws['A5'].style = self.styles['header']
        
        metrics = [
            ('Total Sales', float(invoices.aggregate(total=Sum('net_total'))['total'] or 0)),
            ('Total Invoices', invoices.count()),
            ('Average Sale', float(invoices.aggregate(avg=Avg('net_total'))['avg'] or 0)),
            ('Cash Collected', float(invoices.aggregate(total=Sum('paid_amount'))['total'] or 0)),
            ('Outstanding', float(invoices.aggregate(total=Sum('balance_due'))['total'] or 0)),
            ('Total Deliveries', deliveries.count()),
            ('Current Balance', float(salesman.current_balance)),
        ]
        
        row = 6
        for metric_name, value in metrics:
            ws.cell(row=row, column=1, value=metric_name).style = self.styles['data']
            if 'Total' in metric_name or 'Average' in metric_name or 'Cash' in metric_name or 'Outstanding' in metric_name or 'Balance' in metric_name:
                ws.cell(row=row, column=2, value=value).style = self.styles['currency']
            else:
                ws.cell(row=row, column=2, value=value).style = self.styles['data']
            row += 1
        
        # Recent invoices
        ws.merge_cells(f'A{row + 1}:F{row + 1}')
        ws[f'A{row + 1}'] = "RECENT INVOICES"
        ws[f'A{row + 1}'].style = self.styles['header']
        
        headers = ['Invoice #', 'Shop', 'Date', 'Amount', 'Paid', 'Status']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row + 2, column=col, value=header)
            cell.style = self.styles['subheader']
        
        row += 3
        recent_invoices = invoices.order_by('-invoice_date')[:10]
        for invoice in recent_invoices:
            ws.cell(row=row, column=1, value=invoice.invoice_number).style = self.styles['data']
            ws.cell(row=row, column=2, value=invoice.shop.name).style = self.styles['data']
            ws.cell(row=row, column=3, value=invoice.invoice_date.date()).style = self.styles['data']
            ws.cell(row=row, column=4, value=float(invoice.net_total)).style = self.styles['currency']
            ws.cell(row=row, column=5, value=float(invoice.paid_amount)).style = self.styles['currency']
            ws.cell(row=row, column=6, value=invoice.status.title()).style = self.styles['data']
            row += 1   
 
    def _add_salesman_comparison(self, ws, date_from: datetime, date_to: datetime):
        """Add comparative analysis between salesmen"""
        self._add_report_header(ws, "Salesman Comparative Analysis", date_from, date_to)
        
        # Get comparison metrics
        comparison_data = Salesman.objects.filter(is_active=True).annotate(
            sales_volume=Sum(
                'invoices__net_total',
                filter=Q(invoices__invoice_date__range=[date_from, date_to])
            ),
            invoice_count=Count(
                'invoices',
                filter=Q(invoices__invoice_date__range=[date_from, date_to])
            ),
            avg_invoice_value=Avg(
                'invoices__net_total',
                filter=Q(invoices__invoice_date__range=[date_from, date_to])
            ),
            collection_efficiency=Sum(
                'invoices__paid_amount',
                filter=Q(invoices__invoice_date__range=[date_from, date_to])
            ) * 100 / Sum(
                'invoices__net_total',
                filter=Q(invoices__invoice_date__range=[date_from, date_to])
            )
        ).order_by('-sales_volume')
        
        # Headers
        headers = [
            'Salesman', 'Sales Volume', 'Invoice Count', 'Avg Invoice',
            'Collection %', 'Market Share %', 'Growth Trend'
        ]
        
        row = 5
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Calculate total sales for market share
        total_market_sales = sum(
            float(data.sales_volume or 0) for data in comparison_data
        )
        
        # Data rows
        row = 6
        for data in comparison_data:
            ws.cell(row=row, column=1, value=data.name).style = self.styles['data']
            ws.cell(row=row, column=2, value=float(data.sales_volume or 0)).style = self.styles['currency']
            ws.cell(row=row, column=3, value=data.invoice_count or 0).style = self.styles['data']
            ws.cell(row=row, column=4, value=float(data.avg_invoice_value or 0)).style = self.styles['currency']
            ws.cell(row=row, column=5, value=float(data.collection_efficiency or 0)).style = self.styles['percentage']
            
            # Market share
            market_share = (float(data.sales_volume or 0) / total_market_sales * 100) if total_market_sales > 0 else 0
            ws.cell(row=row, column=6, value=market_share).style = self.styles['percentage']
            
            # Growth trend (simplified - would need historical data for accurate calculation)
            ws.cell(row=row, column=7, value="↑").style = self.styles['kpi_positive']
            
            row += 1
    
    def _add_cash_flow_summary(self, ws, date_from: datetime, date_to: datetime):
        """Add cash flow summary"""
        self._add_report_header(ws, "Cash Flow Summary", date_from, date_to)
        
        # Cash inflows
        cash_inflows = Transaction.objects.filter(
            transaction_date__range=[date_from, date_to]
        ).aggregate(
            total_cash=Sum('amount', filter=Q(payment_method='cash')),
            total_cheque=Sum('amount', filter=Q(payment_method='cheque')),
            total_bank=Sum('amount', filter=Q(payment_method='bank_transfer')),
            total_inflow=Sum('amount')
        )
        
        # Settlement outflows
        settlement_outflows = DeliverySettlement.objects.filter(
            settlement_date__range=[date_from, date_to]
        ).aggregate(
            total_settlements=Sum('cash_settled_amount')
        )
        
        # Expense outflows
        expense_outflows = DeliveryExpense.objects.filter(
            created_at__date__range=[date_from, date_to]
        ).aggregate(
            total_expenses=Sum('amount')
        )
        
        # Cash flow summary table
        ws.merge_cells('A5:D5')
        ws['A5'] = "CASH FLOW SUMMARY"
        ws['A5'].style = self.styles['header']
        
        # Inflows section
        ws.cell(row=6, column=1, value="INFLOWS").style = self.styles['subheader']
        
        inflow_data = [
            ('Cash Payments', float(cash_inflows['total_cash'] or 0)),
            ('Cheque Payments', float(cash_inflows['total_cheque'] or 0)),
            ('Bank Transfers', float(cash_inflows['total_bank'] or 0)),
            ('Total Inflows', float(cash_inflows['total_inflow'] or 0))
        ]
        
        row = 7
        for item, amount in inflow_data:
            ws.cell(row=row, column=1, value=item).style = self.styles['data']
            ws.cell(row=row, column=2, value=amount).style = self.styles['currency']
            row += 1
        
        # Outflows section
        ws.cell(row=row + 1, column=1, value="OUTFLOWS").style = self.styles['subheader']
        
        outflow_data = [
            ('Settlements to Owner', float(settlement_outflows['total_settlements'] or 0)),
            ('Delivery Expenses', float(expense_outflows['total_expenses'] or 0)),
            ('Total Outflows', float((settlement_outflows['total_settlements'] or 0) + (expense_outflows['total_expenses'] or 0)))
        ]
        
        row += 2
        for item, amount in outflow_data:
            ws.cell(row=row, column=1, value=item).style = self.styles['data']
            ws.cell(row=row, column=2, value=amount).style = self.styles['currency']
            row += 1
        
        # Net cash flow
        net_cash_flow = float(cash_inflows['total_inflow'] or 0) - float((settlement_outflows['total_settlements'] or 0) + (expense_outflows['total_expenses'] or 0))
        ws.cell(row=row + 1, column=1, value="NET CASH FLOW").style = self.styles['subheader']
        net_cell = ws.cell(row=row + 1, column=2, value=net_cash_flow)
        net_cell.style = self.styles['kpi_positive'] if net_cash_flow >= 0 else self.styles['kpi_negative']
        net_cell.number_format = 'LKR #,##0.00'
    
    def _add_payment_method_analysis(self, ws, date_from: datetime, date_to: datetime):
        """Add payment method analysis"""
        self._add_report_header(ws, "Payment Method Analysis", date_from, date_to)
        
        # Payment method breakdown
        payment_methods = Transaction.objects.filter(
            transaction_date__range=[date_from, date_to]
        ).values('payment_method').annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id'),
            avg_amount=Avg('amount')
        ).order_by('-total_amount')
        
        # Headers
        headers = ['Payment Method', 'Total Amount', 'Count', 'Average', 'Percentage']
        
        row = 5
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Calculate total for percentage
        total_payments = sum(pm['total_amount'] for pm in payment_methods)
        
        # Data rows
        row = 6
        for pm in payment_methods:
            ws.cell(row=row, column=1, value=pm['payment_method'].replace('_', ' ').title()).style = self.styles['data']
            ws.cell(row=row, column=2, value=float(pm['total_amount'])).style = self.styles['currency']
            ws.cell(row=row, column=3, value=pm['transaction_count']).style = self.styles['data']
            ws.cell(row=row, column=4, value=float(pm['avg_amount'])).style = self.styles['currency']
            
            percentage = (pm['total_amount'] / total_payments * 100) if total_payments > 0 else 0
            ws.cell(row=row, column=5, value=percentage).style = self.styles['percentage']
            
            row += 1
    
    def _add_outstanding_analysis(self, ws, date_from: datetime, date_to: datetime):
        """Add outstanding payments analysis"""
        self._add_report_header(ws, "Outstanding Payments Analysis", date_from, date_to)
        
        # Outstanding by age
        today = timezone.now().date()
        outstanding_invoices = Invoice.objects.filter(
            status__in=['pending', 'partial'],
            invoice_date__lte=date_to
        )
        
        # Age buckets using date filtering instead of annotated days
        from datetime import timedelta
        age_buckets = [
            ('0-30 days', outstanding_invoices.filter(invoice_date__gte=today - timedelta(days=30))),
            ('31-60 days', outstanding_invoices.filter(
                invoice_date__gte=today - timedelta(days=60),
                invoice_date__lt=today - timedelta(days=30)
            )),
            ('61-90 days', outstanding_invoices.filter(
                invoice_date__gte=today - timedelta(days=90),
                invoice_date__lt=today - timedelta(days=60)
            )),
            ('90+ days', outstanding_invoices.filter(invoice_date__lt=today - timedelta(days=90)))
        ]
        
        # Headers
        headers = ['Age Range', 'Count', 'Total Amount', 'Average', 'Percentage']
        
        row = 5
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Calculate totals
        total_outstanding = outstanding_invoices.aggregate(total=Sum('balance_due'))['total'] or 0
        
        # Data rows
        row = 6
        for age_range, invoices in age_buckets:
            count = invoices.count()
            total_amount = invoices.aggregate(total=Sum('balance_due'))['total'] or 0
            avg_amount = (total_amount / count) if count > 0 else 0
            percentage = (total_amount / total_outstanding * 100) if total_outstanding > 0 else 0
            
            ws.cell(row=row, column=1, value=age_range).style = self.styles['data']
            ws.cell(row=row, column=2, value=count).style = self.styles['data']
            ws.cell(row=row, column=3, value=float(total_amount)).style = self.styles['currency']
            ws.cell(row=row, column=4, value=float(avg_amount)).style = self.styles['currency']
            ws.cell(row=row, column=5, value=percentage).style = self.styles['percentage']
            
            row += 1
    
    def _add_settlement_tracking(self, ws, date_from: datetime, date_to: datetime):
        """Add settlement tracking"""
        self._add_report_header(ws, "Settlement Tracking", date_from, date_to)
        
        # Settlement details
        settlements = DeliverySettlement.objects.filter(
            settlement_date__range=[date_from, date_to]
        ).select_related('salesman__user').order_by('-settlement_date')
        
        # Headers
        headers = [
            'Date', 'Salesman', 'Delivered Value', 'Cash Collected',
            'Sold Value', 'Cash Settled', 'Status', 'Notes'
        ]
        
        row = 5
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Data rows
        row = 6
        for settlement in settlements:
            ws.cell(row=row, column=1, value=settlement.settlement_date).style = self.styles['data']
            ws.cell(row=row, column=2, value=settlement.salesman.name).style = self.styles['data']
            ws.cell(row=row, column=3, value=float(settlement.total_delivered_value)).style = self.styles['currency']
            ws.cell(row=row, column=4, value=float(settlement.total_cash_collected)).style = self.styles['currency']
            ws.cell(row=row, column=5, value=float(settlement.total_sold_value)).style = self.styles['currency']
            ws.cell(row=row, column=6, value=float(settlement.cash_settled_amount)).style = self.styles['currency']
            ws.cell(row=row, column=7, value=settlement.status.title()).style = self.styles['data']
            ws.cell(row=row, column=8, value=settlement.settlement_notes or '').style = self.styles['data']
            row += 1
    
    def _add_product_performance(self, ws, date_from: datetime, date_to: datetime):
        """Add product performance analysis"""
        self._add_report_header(ws, "Product Performance Analysis", date_from, date_to)
        
        # Product performance data
        products = InvoiceItem.objects.filter(
            invoice__invoice_date__range=[date_from, date_to]
        ).values(
            'product__name', 'product__sku', 'product__base_price'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('unit_price')),
            avg_price=Avg('unit_price'),
            invoice_count=Count('invoice', distinct=True)
        ).order_by('-total_revenue')
        
        # Headers
        headers = [
            'Product Name', 'SKU', 'Quantity Sold', 'Revenue',
            'Avg Price', 'Base Price', 'Margin %', 'Invoices'
        ]
        
        row = 5
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Data rows
        row = 6
        for product in products:
            ws.cell(row=row, column=1, value=product['product__name']).style = self.styles['data']
            ws.cell(row=row, column=2, value=product['product__sku']).style = self.styles['data']
            ws.cell(row=row, column=3, value=product['total_quantity']).style = self.styles['data']
            ws.cell(row=row, column=4, value=float(product['total_revenue'])).style = self.styles['currency']
            ws.cell(row=row, column=5, value=float(product['avg_price'])).style = self.styles['currency']
            ws.cell(row=row, column=6, value=float(product['product__base_price'])).style = self.styles['currency']
            
            # Calculate margin percentage
            margin_pct = 0
            if product['avg_price'] and product['product__base_price']:
                margin_pct = ((product['avg_price'] - product['product__base_price']) / product['product__base_price']) * 100
            ws.cell(row=row, column=7, value=margin_pct).style = self.styles['percentage']
            
            ws.cell(row=row, column=8, value=product['invoice_count']).style = self.styles['data']
            row += 1
    
    def _add_inventory_analysis(self, ws, date_from: datetime, date_to: datetime):
        """Add inventory analysis"""
        self._add_report_header(ws, "Inventory Analysis", date_from, date_to)
        
        # Current inventory status
        products = Product.objects.filter(is_active=True).annotate(
            current_stock=Sum('batches__current_quantity', filter=Q(batches__is_active=True))
        )
        
        # Headers
        headers = [
            'Product', 'SKU', 'Current Stock', 'Allocated', 'Available',
            'Min Level', 'Status', 'Reorder Needed'
        ]
        
        row = 5
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Data rows
        row = 6
        for product in products:
            ws.cell(row=row, column=1, value=product.name).style = self.styles['data']
            ws.cell(row=row, column=2, value=product.sku).style = self.styles['data']
            ws.cell(row=row, column=3, value=product.current_stock or 0).style = self.styles['data']
            ws.cell(row=row, column=4, value=0).style = self.styles['data']  # Simplified - no allocated stock calculation
            ws.cell(row=row, column=5, value=product.current_stock or 0).style = self.styles['data']  # Available = current for now
            ws.cell(row=row, column=6, value=product.min_stock_level).style = self.styles['data']
            
            # Status
            current_stock = product.current_stock or 0
            status = "Normal"
            status_style = self.styles['data']
            
            if current_stock <= product.min_stock_level:
                status = "Low Stock"
                status_style = self.styles['kpi_negative']
            elif current_stock <= product.min_stock_level * 1.5:
                status = "Warning"
                status_style = self.styles['percentage']  # Yellow-ish
            
            status_cell = ws.cell(row=row, column=7, value=status)
            status_cell.style = status_style
            
            # Reorder needed
            reorder_needed = "Yes" if current_stock <= product.min_stock_level else "No"
            reorder_cell = ws.cell(row=row, column=8, value=reorder_needed)
            reorder_cell.style = self.styles['kpi_negative'] if reorder_needed == "Yes" else self.styles['kpi_positive']
            
            row += 1
    
    def _add_sales_velocity_analysis(self, ws, date_from: datetime, date_to: datetime):
        """Add sales velocity analysis"""
        self._add_report_header(ws, "Sales Velocity Analysis", date_from, date_to)
        
        # Calculate sales velocity (units sold per day)
        period_days = (date_to - date_from).days + 1
        
        velocity_data = InvoiceItem.objects.filter(
            invoice__invoice_date__range=[date_from, date_to]
        ).values(
            'product__name', 'product__sku'
        ).annotate(
            total_sold=Sum('quantity'),
            days_with_sales=Count('invoice__invoice_date', distinct=True),
            velocity=Sum('quantity') / Value(period_days, output_field=models.DecimalField())
        ).order_by('-velocity')
        
        # Headers
        headers = [
            'Product', 'SKU', 'Total Sold', 'Days with Sales',
            'Velocity (units/day)', 'Turnover Rate', 'Category'
        ]
        
        row = 5
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Data rows
        row = 6
        for data in velocity_data:
            ws.cell(row=row, column=1, value=data['product__name']).style = self.styles['data']
            ws.cell(row=row, column=2, value=data['product__sku']).style = self.styles['data']
            ws.cell(row=row, column=3, value=data['total_sold']).style = self.styles['data']
            ws.cell(row=row, column=4, value=data['days_with_sales']).style = self.styles['data']
            ws.cell(row=row, column=5, value=float(data['velocity'])).style = self.styles['data']
            
            # Turnover rate (simplified calculation)
            turnover_rate = data['total_sold'] / period_days if period_days > 0 else 0
            ws.cell(row=row, column=6, value=float(turnover_rate)).style = self.styles['data']
            
            # Category based on velocity
            velocity_val = float(data['velocity'])
            if velocity_val >= 10:
                category = "Fast Moving"
                category_style = self.styles['kpi_positive']
            elif velocity_val >= 5:
                category = "Medium Moving"
                category_style = self.styles['data']
            else:
                category = "Slow Moving"
                category_style = self.styles['kpi_negative']
            
            category_cell = ws.cell(row=row, column=7, value=category)
            category_cell.style = category_style
            
            row += 1
    
    def _add_product_margin_analysis(self, ws, date_from: datetime, date_to: datetime):
        """Add product margin analysis"""
        self._add_report_header(ws, "Product Margin Analysis", date_from, date_to)
        
        # Margin analysis by product
        margin_data = InvoiceItem.objects.filter(
            invoice__invoice_date__range=[date_from, date_to]
        ).values(
            'product__name', 'product__base_price', 'product__cost_price'
        ).annotate(
            avg_selling_price=Avg('unit_price'),
            total_revenue=Sum(F('quantity') * F('unit_price')),
            total_cost=Sum(F('quantity') * F('product__cost_price')),
            total_quantity=Sum('quantity')
        ).order_by('-total_revenue')
        
        # Headers
        headers = [
            'Product', 'Avg Selling Price', 'Base Price', 'Cost Price',
            'Gross Margin %', 'Total Revenue', 'Total Cost', 'Profit'
        ]
        
        row = 5
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Data rows
        row = 6
        for data in margin_data:
            ws.cell(row=row, column=1, value=data['product__name']).style = self.styles['data']
            ws.cell(row=row, column=2, value=float(data['avg_selling_price'])).style = self.styles['currency']
            ws.cell(row=row, column=3, value=float(data['product__base_price'])).style = self.styles['currency']
            ws.cell(row=row, column=4, value=float(data['product__cost_price'])).style = self.styles['currency']
            
            # Gross margin percentage
            gross_margin = 0
            if data['avg_selling_price'] and data['product__cost_price']:
                gross_margin = ((data['avg_selling_price'] - data['product__cost_price']) / data['avg_selling_price']) * 100
            
            margin_cell = ws.cell(row=row, column=5, value=gross_margin)
            margin_cell.style = self.styles['kpi_positive'] if gross_margin > 20 else self.styles['kpi_negative']
            margin_cell.number_format = '0.0%'
            
            ws.cell(row=row, column=6, value=float(data['total_revenue'])).style = self.styles['currency']
            ws.cell(row=row, column=7, value=float(data['total_cost'])).style = self.styles['currency']
            
            # Profit
            profit = data['total_revenue'] - data['total_cost']
            profit_cell = ws.cell(row=row, column=8, value=float(profit))
            profit_cell.style = self.styles['kpi_positive'] if profit > 0 else self.styles['kpi_negative']
            profit_cell.number_format = 'LKR #,##0.00'
            
            row += 1    

    def _add_customer_overview(self, ws, date_from: datetime, date_to: datetime):
        """Add customer overview analysis"""
        self._add_report_header(ws, "Customer Overview", date_from, date_to)
        
        # Customer metrics
        invoices_in_period = Invoice.objects.filter(
            invoice_date__range=[date_from, date_to]
        )
        
        # Get unique customers (shops)
        customer_data = invoices_in_period.values(
            'shop__name', 'shop__location', 'shop__contact_person'
        ).annotate(
            total_orders=Count('id'),
            total_spent=Sum('net_total'),
            avg_order_value=Avg('net_total'),
            total_paid=Sum('paid_amount'),
            outstanding=Sum('balance_due'),
            last_order_date=models.Max('invoice_date')
        ).order_by('-total_spent')
        
        # Headers
        headers = [
            'Customer/Shop', 'Location', 'Contact Person', 'Orders',
            'Total Spent', 'Avg Order', 'Paid Amount', 'Outstanding', 'Last Order'
        ]
        
        row = 5
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Data rows
        row = 6
        for customer in customer_data:
            ws.cell(row=row, column=1, value=customer['shop__name']).style = self.styles['data']
            ws.cell(row=row, column=2, value=customer['shop__location'] or '').style = self.styles['data']
            ws.cell(row=row, column=3, value=customer['shop__contact_person'] or '').style = self.styles['data']
            ws.cell(row=row, column=4, value=customer['total_orders']).style = self.styles['data']
            ws.cell(row=row, column=5, value=float(customer['total_spent'])).style = self.styles['currency']
            ws.cell(row=row, column=6, value=float(customer['avg_order_value'])).style = self.styles['currency']
            ws.cell(row=row, column=7, value=float(customer['total_paid'])).style = self.styles['currency']
            ws.cell(row=row, column=8, value=float(customer['outstanding'])).style = self.styles['currency']
            ws.cell(row=row, column=9, value=customer['last_order_date'].date()).style = self.styles['data']
            row += 1
    
    def _add_shop_performance(self, ws, date_from: datetime, date_to: datetime):
        """Add shop performance analysis"""
        self._add_report_header(ws, "Shop Performance Analysis", date_from, date_to)
        
        # Shop performance with salesman info
        shop_performance = Invoice.objects.filter(
            invoice_date__range=[date_from, date_to]
        ).values(
            'shop__name', 'shop__location', 'salesman__name'
        ).annotate(
            revenue=Sum('net_total'),
            order_count=Count('id'),
            avg_order=Avg('net_total'),
            payment_rate=Sum('paid_amount') * 100 / Sum('net_total'),
            last_order=models.Max('invoice_date')
        ).order_by('-revenue')
        
        # Headers
        headers = [
            'Shop Name', 'Location', 'Salesman', 'Revenue',
            'Orders', 'Avg Order', 'Payment Rate %', 'Last Order', 'Performance'
        ]
        
        row = 5
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Data rows
        row = 6
        for shop in shop_performance:
            ws.cell(row=row, column=1, value=shop['shop__name']).style = self.styles['data']
            ws.cell(row=row, column=2, value=shop['shop__location'] or '').style = self.styles['data']
            ws.cell(row=row, column=3, value=shop['salesman__name']).style = self.styles['data']
            ws.cell(row=row, column=4, value=float(shop['revenue'])).style = self.styles['currency']
            ws.cell(row=row, column=5, value=shop['order_count']).style = self.styles['data']
            ws.cell(row=row, column=6, value=float(shop['avg_order'])).style = self.styles['currency']
            ws.cell(row=row, column=7, value=float(shop['payment_rate'] or 0)).style = self.styles['percentage']
            ws.cell(row=row, column=8, value=shop['last_order'].date()).style = self.styles['data']
            
            # Performance rating
            performance_score = self._calculate_shop_performance_score(shop)
            performance_cell = ws.cell(row=row, column=9, value=performance_score)
            performance_cell.style = self.styles['kpi_positive'] if performance_score in ['Excellent', 'Good'] else self.styles['kpi_negative']
            
            row += 1
    
    def _calculate_shop_performance_score(self, shop_data) -> str:
        """Calculate shop performance score"""
        revenue = shop_data['revenue']
        payment_rate = shop_data['payment_rate'] or 0
        order_count = shop_data['order_count']
        
        # Simple scoring logic
        score = 0
        if revenue > 50000:
            score += 3
        elif revenue > 20000:
            score += 2
        elif revenue > 10000:
            score += 1
        
        if payment_rate > 80:
            score += 2
        elif payment_rate > 60:
            score += 1
        
        if order_count > 10:
            score += 1
        
        if score >= 5:
            return "Excellent"
        elif score >= 3:
            return "Good"
        elif score >= 2:
            return "Average"
        else:
            return "Poor"
    
    def _add_geographic_analysis(self, ws, date_from: datetime, date_to: datetime):
        """Add geographic analysis"""
        self._add_report_header(ws, "Geographic Analysis", date_from, date_to)
        
        # Geographic performance by location
        geographic_data = Invoice.objects.filter(
            invoice_date__range=[date_from, date_to]
        ).values(
            'shop__location'
        ).annotate(
            total_revenue=Sum('net_total'),
            shop_count=Count('shop', distinct=True),
            order_count=Count('id'),
            avg_revenue_per_shop=Sum('net_total') / Count('shop', distinct=True)
        ).order_by('-total_revenue')
        
        # Headers
        headers = [
            'Location', 'Total Revenue', 'Shop Count', 'Orders',
            'Avg Revenue/Shop', 'Market Share %', 'Density'
        ]
        
        row = 5
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Calculate total for market share
        total_revenue = sum(float(data['total_revenue'] or 0) for data in geographic_data)
        
        # Data rows
        row = 6
        for data in geographic_data:
            location = data['shop__location'] or 'Unknown'
            ws.cell(row=row, column=1, value=location).style = self.styles['data']
            ws.cell(row=row, column=2, value=float(data['total_revenue'])).style = self.styles['currency']
            ws.cell(row=row, column=3, value=data['shop_count']).style = self.styles['data']
            ws.cell(row=row, column=4, value=data['order_count']).style = self.styles['data']
            ws.cell(row=row, column=5, value=float(data['avg_revenue_per_shop'])).style = self.styles['currency']
            
            # Market share
            market_share = (data['total_revenue'] / total_revenue * 100) if total_revenue > 0 else 0
            ws.cell(row=row, column=6, value=market_share).style = self.styles['percentage']
            
            # Density (orders per shop)
            density = data['order_count'] / data['shop_count'] if data['shop_count'] > 0 else 0
            ws.cell(row=row, column=7, value=float(density)).style = self.styles['data']
            
            row += 1
    
    def _add_payment_behavior_analysis(self, ws, date_from: datetime, date_to: datetime):
        """Add payment behavior analysis"""
        self._add_report_header(ws, "Payment Behavior Analysis", date_from, date_to)
        
        # Payment behavior by customer
        payment_behavior = Invoice.objects.filter(
            invoice_date__range=[date_from, date_to]
        ).values(
            'shop__name'
        ).annotate(
            total_invoiced=Sum('net_total'),
            total_paid=Sum('paid_amount'),
            payment_rate=Sum('paid_amount') * 100 / Sum('net_total'),
            avg_payment_delay=Avg(
                Case(
                    When(paid_amount__gt=0, then=F('updated_at') - F('invoice_date')),
                    default=Value(0),
                    output_field=models.DurationField()
                )
            ),
            overdue_count=Count(
                Case(
                    When(status='overdue', then=1),
                    output_field=models.IntegerField()
                )
            )
        ).order_by('-payment_rate')
        
        # Headers
        headers = [
            'Customer', 'Total Invoiced', 'Total Paid', 'Payment Rate %',
            'Avg Payment Delay (days)', 'Overdue Count', 'Risk Level'
        ]
        
        row = 5
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.style = self.styles['subheader']
        
        # Data rows
        row = 6
        for behavior in payment_behavior:
            ws.cell(row=row, column=1, value=behavior['shop__name']).style = self.styles['data']
            ws.cell(row=row, column=2, value=float(behavior['total_invoiced'])).style = self.styles['currency']
            ws.cell(row=row, column=3, value=float(behavior['total_paid'])).style = self.styles['currency']
            ws.cell(row=row, column=4, value=float(behavior['payment_rate'] or 0)).style = self.styles['percentage']
            
            # Payment delay in days
            delay_days = 0
            if behavior['avg_payment_delay']:
                delay_days = behavior['avg_payment_delay'].days
            ws.cell(row=row, column=5, value=delay_days).style = self.styles['data']
            
            ws.cell(row=row, column=6, value=behavior['overdue_count']).style = self.styles['data']
            
            # Risk level assessment
            risk_level = self._assess_payment_risk(behavior)
            risk_cell = ws.cell(row=row, column=7, value=risk_level)
            
            if risk_level == "Low":
                risk_cell.style = self.styles['kpi_positive']
            elif risk_level == "Medium":
                risk_cell.style = self.styles['percentage']  # Yellow-ish
            else:
                risk_cell.style = self.styles['kpi_negative']
            
            row += 1
    
    def _assess_payment_risk(self, behavior_data) -> str:
        """Assess payment risk level for a customer"""
        payment_rate = behavior_data['payment_rate'] or 0
        overdue_count = behavior_data['overdue_count']
        
        if payment_rate >= 90 and overdue_count == 0:
            return "Low"
        elif payment_rate >= 70 and overdue_count <= 2:
            return "Medium"
        else:
            return "High"
    
    def generate_custom_report(self, report_config: Dict[str, Any]) -> str:
        """
        Generate custom report based on configuration
        """
        logger.info(f"Generating custom report with config: {report_config}")
        
        report_type = report_config.get('type', 'custom')
        date_from = report_config.get('date_from')
        date_to = report_config.get('date_to')
        sections = report_config.get('sections', [])
        
        self.workbook = Workbook()
        ws = self.workbook.active
        ws.title = "Custom Report"
        
        self._add_report_header(ws, f"Custom {report_type.title()} Report", date_from, date_to)
        
        current_row = 5
        
        # Add requested sections
        for section in sections:
            if section == 'kpi_summary':
                current_row = self._add_kpi_summary(ws, date_from, date_to, current_row) + 2
            elif section == 'sales_performance':
                current_row = self._add_sales_performance(ws, date_from, date_to, current_row) + 2
            elif section == 'top_performers':
                current_row = self._add_top_performers(ws, date_from, date_to, current_row) + 2
            elif section == 'trend_analysis':
                current_row = self._add_trend_analysis(ws, date_from, date_to, current_row) + 2
        
        # Auto-adjust columns
        self._auto_adjust_columns(ws)
        
        # Save file
        filename = f"custom_report_{report_type}_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.xlsx"
        filepath = self._save_report(filename)
        
        logger.info(f"Custom Report generated: {filepath}")
        return filepath
    
    def schedule_automated_reports(self, schedule_config: Dict[str, Any]) -> bool:
        """
        Schedule automated report generation
        This would integrate with Django's task queue (Celery) in production
        """
        logger.info(f"Scheduling automated reports with config: {schedule_config}")
        
        # This is a placeholder for automated scheduling
        # In production, this would create Celery periodic tasks
        
        report_types = schedule_config.get('report_types', [])
        frequency = schedule_config.get('frequency', 'daily')  # daily, weekly, monthly
        recipients = schedule_config.get('recipients', [])
        
        # For now, just log the configuration
        logger.info(f"Would schedule {len(report_types)} report types with {frequency} frequency for {len(recipients)} recipients")
        
        return True
    
    def export_report_data(self, report_type: str, format: str = 'xlsx') -> str:
        """
        Export report data in specified format
        """
        logger.info(f"Exporting {report_type} report in {format} format")
        
        if format not in ['xlsx', 'csv', 'json']:
            raise ValueError(f"Unsupported format: {format}")
        
        # This would implement different export formats
        # For now, we only support Excel
        if format == 'xlsx':
            # Use existing Excel generation methods
            today = timezone.now().date()
            week_ago = today - timedelta(days=7)
            
            if report_type == 'master_dashboard':
                return self.generate_master_dashboard(week_ago, today)
            elif report_type == 'delivery_performance':
                return self.generate_delivery_performance(week_ago, today)
            # Add other report types as needed
        
        return ""
    
    def validate_report_data(self, report_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate report data for accuracy and completeness
        """
        errors = []
        
        # Basic validation checks
        if not report_data:
            errors.append("Report data is empty")
            return False, errors
        
        # Check for required fields
        required_fields = ['date_from', 'date_to']
        for field in required_fields:
            if field not in report_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate date range
        if 'date_from' in report_data and 'date_to' in report_data:
            if report_data['date_from'] > report_data['date_to']:
                errors.append("Start date cannot be after end date")
        
        # Additional validation logic would go here
        
        is_valid = len(errors) == 0
        return is_valid, errors


# Utility functions for report generation
def generate_all_reports(date_from: datetime, date_to: datetime) -> Dict[str, str]:
    """
    Generate all report types for a given date range
    Returns dictionary with report type as key and filepath as value
    """
    service = ExcelReportService()
    
    reports = {}
    
    try:
        reports['master_dashboard'] = service.generate_master_dashboard(date_from, date_to)
        reports['delivery_performance'] = service.generate_delivery_performance(date_from, date_to)
        reports['salesman_performance'] = service.generate_salesman_performance(date_from, date_to)
        reports['cash_flow_analysis'] = service.generate_cash_flow_analysis(date_from, date_to)
        reports['product_analytics'] = service.generate_product_analytics(date_from, date_to)
        reports['customer_analysis'] = service.generate_customer_analysis(date_from, date_to)
        
        logger.info(f"Generated {len(reports)} reports successfully")
        
    except Exception as e:
        logger.error(f"Error generating reports: {str(e)}")
        raise
    
    return reports


def generate_monthly_reports() -> Dict[str, str]:
    """
    Generate monthly reports for the current month
    """
    today = timezone.now().date()
    first_day = today.replace(day=1)
    
    return generate_all_reports(first_day, today)


def generate_weekly_reports() -> Dict[str, str]:
    """
    Generate weekly reports for the current week
    """
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    
    return generate_all_reports(week_start, today)