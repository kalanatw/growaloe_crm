# Generated by Django 5.0.7 on 2025-06-01 15:39

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        ('products', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_number', models.CharField(max_length=100, unique=True)),
                ('invoice_date', models.DateTimeField(auto_now_add=True)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('pending', 'Pending'), ('paid', 'Paid'), ('partial', 'Partially Paid'), ('overdue', 'Overdue'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('subtotal', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('tax_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('net_total', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('paid_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('balance_due', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('notes', models.TextField(blank=True, null=True)),
                ('terms_conditions', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('salesman', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='accounts.salesman')),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='accounts.shop')),
            ],
            options={
                'db_table': 'invoices',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='InvoiceItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('calculated_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('salesman_margin', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('shop_margin', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='sales.invoice')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoice_items', to='products.product')),
            ],
            options={
                'db_table': 'invoice_items',
            },
        ),
        migrations.CreateModel(
            name='Return',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('return_number', models.CharField(max_length=100, unique=True)),
                ('quantity', models.PositiveIntegerField()),
                ('reason', models.CharField(choices=[('defective', 'Defective Product'), ('wrong_item', 'Wrong Item'), ('damaged', 'Damaged in Transit'), ('expired', 'Expired Product'), ('customer_request', 'Customer Request'), ('other', 'Other')], max_length=20)),
                ('return_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('approved', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_returns', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('original_invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='returns', to='sales.invoice')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
            ],
            options={
                'db_table': 'returns',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_date', models.DateTimeField(auto_now_add=True)),
                ('payment_method', models.CharField(choices=[('cash', 'Cash'), ('cheque', 'Cheque'), ('return', 'Return'), ('bill_to_bill', 'Bill to Bill'), ('bank_transfer', 'Bank Transfer'), ('credit_note', 'Credit Note')], max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('reference_number', models.CharField(blank=True, max_length=100, null=True)),
                ('bank_name', models.CharField(blank=True, max_length=100, null=True)),
                ('cheque_date', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='sales.invoice')),
            ],
            options={
                'db_table': 'transactions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['invoice_number'], name='invoices_invoice_7778bc_idx'),
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['shop', 'status'], name='invoices_shop_id_681e11_idx'),
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['salesman', 'invoice_date'], name='invoices_salesma_b70783_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='invoiceitem',
            unique_together={('invoice', 'product')},
        ),
    ]
