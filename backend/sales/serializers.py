from rest_framework import serializers
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Invoice, InvoiceItem, Transaction, Return
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
        
        # For salesmen, check stock availability
        request = self.context.get('request')
        if request and request.user.role == 'SALESMAN':
            try:
                stock = SalesmanStock.objects.get(
                    salesman=request.user.salesman_profile,
                    product=product
                )
                if quantity > stock.available_quantity:
                    raise serializers.ValidationError(
                        f"Insufficient stock. Available: {stock.available_quantity}, Requested: {quantity}"
                    )
            except SalesmanStock.DoesNotExist:
                raise serializers.ValidationError(
                    f"Product {product.name} not allocated to this salesman"
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
            'net_total', 'paid_amount', 'balance_due', 'total_amount', 'status', 
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
            'shop', 'due_date', 'tax_amount',
            'discount_amount', 'notes', 'terms_conditions', 'items'
        ]
    
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
        
        # Create invoice items and update stock
        for item_data in items_data:
            # Create invoice item
            invoice_item = InvoiceItem.objects.create(invoice=invoice, **item_data)
            
            # Update salesman stock (reduce available quantity)
            if invoice.salesman:
                try:
                    stock = SalesmanStock.objects.get(
                        salesman=invoice.salesman,
                        product=invoice_item.product
                    )
                    if stock.available_quantity >= invoice_item.quantity:
                        stock.available_quantity -= invoice_item.quantity
                        stock.save()
                        
                        # Create stock movement record
                        StockMovement.objects.create(
                            product=invoice_item.product,
                            salesman=invoice.salesman,
                            movement_type='sale',
                            quantity=-invoice_item.quantity,  # Negative for outward movement
                            reference_id=invoice.invoice_number,
                            notes=f'Sale via invoice {invoice.invoice_number}',
                            created_by=request.user if request else None
                        )
                    else:
                        # This should be caught by validation, but just in case
                        raise serializers.ValidationError(
                            f'Insufficient stock for {invoice_item.product.name}. '
                            f'Available: {stock.available_quantity}, Requested: {invoice_item.quantity}'
                        )
                except SalesmanStock.DoesNotExist:
                    raise serializers.ValidationError(
                        f'Product {invoice_item.product.name} not allocated to salesman {invoice.salesman.name}'
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
