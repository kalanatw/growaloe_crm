# Generated by Django 5.0.7 on 2025-06-18 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_financialsummary_financialtransaction'),
    ]

    operations = [
        migrations.RenameField(
            model_name='financialsummary',
            old_name='net_profit',
            new_name='net_balance',
        ),
        migrations.RenameField(
            model_name='financialsummary',
            old_name='total_expenses',
            new_name='total_credits',
        ),
        migrations.RenameField(
            model_name='financialsummary',
            old_name='total_income',
            new_name='total_debits',
        ),
        migrations.AddField(
            model_name='financialtransaction',
            name='invoice_id',
            field=models.CharField(blank=True, help_text='Invoice ID if related to invoice', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='financialtransaction',
            name='category',
            field=models.CharField(choices=[('invoice_settlement', 'Invoice Settlement'), ('cash_sale', 'Cash Sale'), ('other_income', 'Other Income'), ('loan_received', 'Loan Received'), ('capital_injection', 'Capital Injection'), ('refund_received', 'Refund Received'), ('invoice_created', 'Invoice Created'), ('purchase', 'Purchase'), ('rent', 'Rent'), ('utilities', 'Utilities'), ('salaries', 'Salaries'), ('transport', 'Transport'), ('marketing', 'Marketing'), ('office_expenses', 'Office Expenses'), ('agency_payment', 'Agency Payment'), ('loan_payment', 'Loan Payment'), ('tax_payment', 'Tax Payment'), ('bank_charges', 'Bank Charges'), ('other_expense', 'Other Expense')], max_length=20),
        ),
        migrations.AlterField(
            model_name='financialtransaction',
            name='transaction_type',
            field=models.CharField(choices=[('debit', 'Debit'), ('credit', 'Credit')], max_length=10),
        ),
    ]
