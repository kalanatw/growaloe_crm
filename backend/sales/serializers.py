from rest_framework import serializers
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Invoice, InvoiceItem, Transaction, Return, InvoiceSettlement, SettlementPayment
from products.models import Product, SalesmanStock

User = get_user_model()


class InvoiceItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    line_total = serializers.SerializerMethodField()
    
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'quantity', 
            'unit_price', 'calculated_price', 'total_price', 'salesman_margin', 
            'shop_margin', 'line_total'
        ]
        read_only_fields = ['id', 'product_name', 'product_sku', 'line_total', 'calculated_price', 'total_price']
    
    def get_line_total(self, obj):
        return obj.get_line_total()
    
    def validate(self, data):
        product = data.get('product')
        quantity = data.get('quantity', 0)
        
        # Check if product is active
        if product and not product.is_active:
            raise serializers.ValidationError(
                f"Product {product.name} is not active"
            )
        
        # For salesmen, check stock availability from deliveries
        request = self.context.get('request')
        if request and request.user.role == 'salesman':
            from products.models import DeliveryItem
            from sales.models import InvoiceItem
            from django.db.models import Sum
            
            salesman = request.user.salesman_profile
            
            # Get total delivered quantity for this product to this salesman
            # Include both pending and delivered status since owners can allocate products
            delivered_qty = DeliveryItem.objects.filter(
                delivery__salesman=salesman,
                delivery__status__in=['pending', 'delivered'],
                product=product
            ).aggregate(total_delivered=Sum('quantity'))['total_delivered'] or 0
            
            # Get total sold quantity for this product by this salesman
            sold_qty = InvoiceItem.objects.filter(
                invoice__salesman=salesman,
                product=product
            ).aggregate(total_sold=Sum('quantity'))['total_sold'] or 0
            
            # Calculate available quantity
            available_qty = delivered_qty - sold_qty
            
            if delivered_qty == 0:
                raise serializers.ValidationError(
                    f"Product {product.name} not allocated to this salesman"
                )
            
            if quantity > available_qty:
                raise serializers.ValidationError(
                    f"Insufficient stock. Available: {available_qty}, Requested: {quantity}"
                )
        
        return data


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    salesman_name = serializers.CharField(source='salesman.user.get_full_name', read_only=True)
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    total_amount = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'salesman', 'salesman_name', 'shop', 'shop_name',
            'invoice_date', 'due_date', 'subtotal', 'tax_amount', 'discount_amount',
            'shop_margin', 'net_total', 'paid_amount', 'balance_due', 'total_amount', 'status', 
            'notes', 'terms_conditions', 'created_by', 'created_at', 'updated_at',
            'items', 'items_count'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'created_at', 'updated_at', 'items', 
            'salesman_name', 'shop_name', 'total_amount', 'items_count'
        ]
    
    def get_total_amount(self, obj):
        return obj.get_total_amount()
    
    def get_items_count(self, obj):
        return obj.items.count()
    
    def validate(self, data):
        # Validate due date is after invoice date
        invoice_date = data.get('invoice_date')
        due_date = data.get('due_date')
        
        if due_date and invoice_date and due_date < invoice_date:
            raise serializers.ValidationError(
                "Due date cannot be earlier than invoice date"
            )
        
        return data


class InvoiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating invoices with items"""
    items = InvoiceItemSerializer(many=True, write_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'shop', 'due_date', 'tax_amount',
            'discount_amount', 'shop_margin', 'notes', 'terms_conditions', 'items',
            'subtotal', 'net_total', 'total_amount'
        ]
        read_only_fields = ['id', 'invoice_number', 'subtotal', 'net_total', 'total_amount']
    
    def validate(self, data):
        """Validate shop margin based on user permissions"""
        from core.models import CompanySettings
        
        request = self.context.get('request')
        shop_margin = data.get('shop_margin', 0)
        
        # Only validate for salesmen, owners have no restrictions
        if request and request.user.role == 'salesman':
            settings = CompanySettings.get_settings()
            max_margin = settings.max_shop_margin_for_salesmen
            
            if shop_margin > max_margin:
                raise serializers.ValidationError({
                    'shop_margin': f'Salesmen cannot set shop margin above {max_margin}%. Current: {shop_margin}%'
                })
        
        return data
    
    def create(self, validated_data):
        from products.models import StockMovement
        
        items_data = validated_data.pop('items')
        request = self.context.get('request')
        
        # Set salesman based on user role
        if request and request.user.role == 'salesman':
            validated_data['salesman'] = request.user.salesman_profile
        elif not validated_data.get('salesman'):
            # For owner/developer, get the first available salesman or raise error
            from accounts.models import Salesman
            first_salesman = Salesman.objects.first()
            if first_salesman:
                validated_data['salesman'] = first_salesman
            else:
                raise serializers.ValidationError("No salesman available to assign to this invoice")
        
        invoice = Invoice.objects.create(**validated_data)
        
        # Create invoice items and create stock movement records
        for item_data in items_data:
            # Create invoice item
            invoice_item = InvoiceItem.objects.create(invoice=invoice, **item_data)
            
            # Create stock movement record for the sale
            if invoice.salesman:
                StockMovement.objects.create(
                    product=invoice_item.product,
                    salesman=invoice.salesman,
                    movement_type='sale',
                    quantity=-invoice_item.quantity,  # Negative for outward movement
                    reference_id=invoice.invoice_number,
                    notes=f'Sale via invoice {invoice.invoice_number}',
                    created_by=request.user if request else None
                )
        
        # Calculate totals
        invoice.calculate_totals()
        
        return invoice


class TransactionSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    processed_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'invoice', 'invoice_number', 'payment_method', 'amount',
            'reference_number', 'bank_name', 'cheque_date', 'transaction_date',
            'created_by', 'processed_by_name', 'notes', 'created_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'transaction_date', 'invoice_number', 'processed_by_name'
        ]
    
    def validate(self, data):
        invoice = data.get('invoice')
        amount = data.get('amount', 0)
        
        # Check if payment amount doesn't exceed outstanding balance
        if amount > invoice.balance_due:
            raise serializers.ValidationError(
                f"Payment amount ({amount}) exceeds outstanding balance ({invoice.balance_due})"
            )
        
        return data


class ReturnSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='original_invoice.invoice_number', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = Return
        fields = [
            'id', 'return_number', 'original_invoice', 'invoice_number', 'product', 'product_name',
            'quantity', 'reason', 'return_amount', 'approved', 'approved_by', 'approved_by_name',
            'created_by', 'created_by_name', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'return_number', 'created_at', 'updated_at', 'invoice_number', 'product_name', 
            'created_by_name', 'approved_by_name'
        ]
    
    def validate(self, data):
        invoice = data.get('original_invoice')
        product = data.get('product')
        quantity = data.get('quantity', 0)
        
        # Check if product was in the invoice
        try:
            invoice_item = InvoiceItem.objects.get(invoice=invoice, product=product)
        except InvoiceItem.DoesNotExist:
            raise serializers.ValidationError(
                f"Product {product.name} was not in invoice {invoice.invoice_number}"
            )
        
        # Check if return quantity doesn't exceed purchased quantity
        if quantity > invoice_item.quantity:
            raise serializers.ValidationError(
                f"Return quantity ({quantity}) exceeds purchased quantity ({invoice_item.quantity})"
            )
        
        # Check for existing returns
        existing_returns = Return.objects.filter(
            original_invoice=invoice, 
            product=product,
            approved=True
        ).aggregate(total=serializers.models.Sum('quantity'))['total'] or 0
        
        if existing_returns + quantity > invoice_item.quantity:
            raise serializers.ValidationError(
                f"Total return quantity would exceed purchased quantity. "
                f"Already returned: {existing_returns}, Requesting: {quantity}, "
                f"Purchased: {invoice_item.quantity}"
            )
        
        return data


class InvoiceSummarySerializer(serializers.Serializer):
    """Serializer for invoice summary statistics"""
    total_invoices = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    paid_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    outstanding_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    overdue_invoices = serializers.IntegerField()
    draft_invoices = serializers.IntegerField()


class SalesPerformanceSerializer(serializers.Serializer):
    """Serializer for sales performance data"""
    salesman_id = serializers.IntegerField()
    salesman_name = serializers.CharField()
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_invoices = serializers.IntegerField()
    average_sale = serializers.DecimalField(max_digits=15, decimal_places=2)
    commission_earned = serializers.DecimalField(max_digits=15, decimal_places=2)


class SettlementPaymentSerializer(serializers.ModelSerializer):
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = SettlementPayment
        fields = [
            'id', 'payment_method', 'payment_method_display', 'amount', 
            'reference_number', 'bank_name', 'cheque_date', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'payment_method_display']


class InvoiceSettlementSerializer(serializers.ModelSerializer):
    payments = SettlementPaymentSerializer(many=True, read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = InvoiceSettlement
        fields = [
            'id', 'invoice', 'invoice_number', 'settlement_date', 'total_amount',
            'notes', 'created_by', 'created_by_name', 'payments', 'created_at'
        ]
        read_only_fields = ['id', 'settlement_date', 'created_at', 'invoice_number', 'created_by_name']


class MultiPaymentSettlementSerializer(serializers.Serializer):
    """Serializer for creating a settlement with multiple payment methods"""
    invoice_id = serializers.IntegerField()
    payments = serializers.ListField(child=serializers.DictField(), min_length=1)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_invoice_id(self, value):
        try:
            invoice = Invoice.objects.get(id=value)
            if invoice.balance_due <= 0:
                raise serializers.ValidationError("Invoice is already fully paid")
            return value
        except Invoice.DoesNotExist:
            raise serializers.ValidationError("Invoice not found")
    
    def validate_payments(self, value):
        total_amount = Decimal('0')
        valid_payment_methods = [choice[0] for choice in SettlementPayment.PAYMENT_METHODS]
        
        for payment in value:
            # Validate required fields
            if 'payment_method' not in payment or 'amount' not in payment:
                raise serializers.ValidationError("Each payment must have payment_method and amount")
            
            # Validate payment method
            if payment['payment_method'] not in valid_payment_methods:
                raise serializers.ValidationError(f"Invalid payment method: {payment['payment_method']}")
            
            # Validate amount
            try:
                amount = Decimal(str(payment['amount']))
                if amount <= 0:
                    raise serializers.ValidationError("Payment amount must be greater than zero")
                total_amount += amount
            except (ValueError, TypeError):
                raise serializers.ValidationError("Invalid payment amount")
        
        return value
    
    def validate(self, data):
        invoice_id = data['invoice_id']
        payments = data['payments']
        
        try:
            invoice = Invoice.objects.get(id=invoice_id)
            total_payment_amount = sum(Decimal(str(p['amount'])) for p in payments)
            
            if total_payment_amount > invoice.balance_due:
                raise serializers.ValidationError(
                    f"Total payment amount ({total_payment_amount}) exceeds outstanding balance ({invoice.balance_due})"
                )
        except Invoice.DoesNotExist:
            raise serializers.ValidationError("Invoice not found")
        
        return data
