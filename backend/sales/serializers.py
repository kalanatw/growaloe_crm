from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from decimal import Decimal
from .models import Invoice, InvoiceItem, Transaction, Return, InvoiceSettlement, SettlementPayment, Commission
from products.models import Product, Batch, BatchAssignment, StockMovement, BatchTransaction

User = get_user_model()


class InvoiceItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    batch_expiry_date = serializers.DateField(source='batch.expiry_date', read_only=True)
    line_total = serializers.SerializerMethodField()
    
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'batch', 'batch_number', 
            'batch_expiry_date', 'quantity', 'unit_price', 'calculated_price', 
            'total_price', 'salesman_margin', 'shop_margin', 'line_total'
        ]
        read_only_fields = ['id', 'product_name', 'product_sku', 'batch_number', 
                          'batch_expiry_date', 'line_total', 'calculated_price', 'total_price']
    
    def get_line_total(self, obj):
        return obj.get_line_total()
    
    def validate(self, data):
        product = data.get('product')
        batch = data.get('batch')
        quantity = data.get('quantity', 0)
        
        # Check if product is active
        if product and not product.is_active:
            raise serializers.ValidationError(
                f"Product {product.name} is not active"
            )
        
        # If batch is specified, validate batch availability
        if batch:
            # Ensure batch belongs to the product
            if batch.product != product:
                raise serializers.ValidationError(
                    f"Batch {batch.batch_number} does not belong to product {product.name}"
                )
            
            # Check if batch is expired
            if batch.is_expired:
                raise serializers.ValidationError(
                    f"Batch {batch.batch_number} is expired"
                )
            
            # For salesmen, check if they have access to this batch
            request = self.context.get('request')
            if request and request.user.role == 'salesman':
                salesman = request.user.salesman_profile
                
                # Get all assignments for this batch and salesman
                assignments = batch.assignments.filter(
                    salesman=salesman,
                    status__in=['delivered', 'partial']
                )
                
                if not assignments.exists():
                    raise serializers.ValidationError(
                        f"Salesman does not have access to batch {batch.batch_number}"
                    )
                
                # Calculate total available quantity across all assignments
                total_available = sum(assignment.outstanding_quantity for assignment in assignments)
                if quantity > total_available:
                    raise serializers.ValidationError(
                        f"Insufficient batch stock. Available: {total_available}, Requested: {quantity}"
                    )
            
            # For owners, check batch available quantity
            elif request and request.user.role in ['owner', 'developer']:
                if quantity > batch.available_quantity:
                    raise serializers.ValidationError(
                        f"Insufficient batch stock. Available: {batch.available_quantity}, Requested: {quantity}"
                    )
        
        # Fallback to original stock validation if no batch specified
        else:
            # For salesmen, check stock availability from deliveries
            request = self.context.get('request')
            if request and request.user.role == 'salesman':
                from products.models import DeliveryItem
                from sales.models import InvoiceItem
                from django.db.models import Sum
                
                salesman = request.user.salesman_profile
                
                # Get total delivered quantity for this product to this salesman
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
            
            # For owners/developers, check against available batches
            elif request and request.user.role in ['owner', 'developer']:
                # Check total available stock from all batches
                available_batches = Batch.objects.filter(
                    product=product,
                    is_active=True,
                    current_quantity__gt=0
                ).order_by('manufacturing_date', 'expiry_date')
                
                total_available = sum(batch.current_quantity for batch in available_batches)
                
                if quantity > total_available:
                    raise serializers.ValidationError(
                        f"Insufficient stock. Available: {total_available}, Requested: {quantity}"
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
        
        # Create invoice items and handle stock appropriately
        for item_data in items_data:
            # Create invoice item
            invoice_item = InvoiceItem.objects.create(invoice=invoice, **item_data)
            
            # Handle stock reduction based on user role
            if request and request.user.role in ['owner', 'developer']:
                # For owners, reduce stock using product's reduce_stock method (FIFO)
                product = invoice_item.product
                try:
                    product.reduce_stock(
                        quantity=invoice_item.quantity,
                        user=request.user if request else None,
                        notes=f'Sale via invoice {invoice.invoice_number}',
                        movement_type='sale'
                    )
                except ValueError as e:
                    raise serializers.ValidationError(str(e))
            
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
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = Return
        fields = [
            'id', 'return_number', 'original_invoice', 'invoice_number', 'product', 'product_name',
            'batch', 'batch_number', 'quantity', 'reason', 'return_amount', 'approved', 
            'approved_by', 'approved_by_name', 'created_by', 'created_by_name', 'notes', 
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'return_number', 'created_at', 'updated_at', 'invoice_number', 'product_name', 
            'batch_number', 'created_by_name', 'approved_by_name'
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
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
        
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


class BatchInvoiceItemSerializer(serializers.ModelSerializer):
    """Specialized invoice item serializer for batch-based invoicing"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    batch_expiry_date = serializers.DateField(source='batch.expiry_date', read_only=True)
    line_total = serializers.SerializerMethodField()
    
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'batch', 'batch_number', 
            'batch_expiry_date', 'quantity', 'unit_price', 'calculated_price', 
            'total_price', 'salesman_margin', 'shop_margin', 'line_total'
        ]
        read_only_fields = ['id', 'product_name', 'product_sku', 'batch_number', 
                          'batch_expiry_date', 'line_total', 'calculated_price', 'total_price']
    
    def get_line_total(self, obj):
        return obj.get_line_total()
    
    def validate(self, data):
        """Strict validation for batch-based invoicing"""
        product = data.get('product')
        batch = data.get('batch')
        quantity = data.get('quantity', 0)
        
        # Batch is required for salesmen
        if not batch:
            raise serializers.ValidationError(
                "Batch is required for invoice items"
            )
        
        # Check if product is active
        if product and not product.is_active:
            raise serializers.ValidationError(
                f"Product {product.name} is not active"
            )
        
        # Ensure batch belongs to the product
        if batch.product != product:
            raise serializers.ValidationError(
                f"Batch {batch.batch_number} does not belong to product {product.name}"
            )
        
        # Check if batch is expired
        if batch.is_expired:
            raise serializers.ValidationError(
                f"Batch {batch.batch_number} is expired"
            )
        
        # For salesmen, check if they have access to this batch
        request = self.context.get('request')
        if request and request.user.role == 'salesman':
            salesman = request.user.salesman_profile
            
            # Get all assignments for this batch and salesman
            assignments = batch.assignments.filter(
                salesman=salesman,
                status__in=['delivered', 'partial']
            )
            
            if not assignments.exists():
                raise serializers.ValidationError(
                    f"Salesman does not have access to batch {batch.batch_number}"
                )
            
            # Calculate total available quantity across all assignments
            total_available = sum(assignment.outstanding_quantity for assignment in assignments)
            if quantity > total_available:
                raise serializers.ValidationError(
                    f"Insufficient batch stock. Available: {total_available}, Requested: {quantity}"
                )
        
        return data


class BatchInvoiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating batch-based invoices (enforced for salesmen)"""
    items = BatchInvoiceItemSerializer(many=True, write_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'shop', 'due_date', 'tax_amount',
            'discount_amount', 'shop_margin', 'notes', 'terms_conditions', 'items',
            'subtotal', 'net_total', 'total_amount'
        ]
        read_only_fields = ['id', 'invoice_number', 'subtotal', 'net_total', 'total_amount']
    
    def validate(self, data):
        """Validate shop margin and enforce batch requirements"""
        from core.models import CompanySettings
        
        request = self.context.get('request')
        shop_margin = data.get('shop_margin', 0)
        items_data = data.get('items', [])
        
        # Ensure all items have batches
        for item_data in items_data:
            if not item_data.get('batch'):
                raise serializers.ValidationError(
                    "All invoice items must have an associated batch"
                )
        
        # Only validate margin for salesmen, owners have no restrictions
        if request and request.user.role == 'salesman':
            settings = CompanySettings.get_settings()
            max_margin = settings.max_shop_margin_for_salesmen
            
            if shop_margin > max_margin:
                raise serializers.ValidationError({
                    'shop_margin': f'Salesmen cannot set shop margin above {max_margin}%. Current: {shop_margin}%'
                })
        
        return data
    
    def create(self, validated_data):
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
        
        # Create invoice items - stock reduction is handled in the model's save method
        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)
        
        # Calculate totals
        invoice.calculate_totals()
        
        return invoice


class AutoBatchInvoiceItemSerializer(serializers.ModelSerializer):
    """Simplified invoice item serializer that auto-allocates from available batches"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    line_total = serializers.SerializerMethodField()
    
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'quantity', 
            'unit_price', 'line_total'
        ]
        read_only_fields = ['id', 'product_name', 'product_sku', 'line_total']
    
    def get_line_total(self, obj):
        return obj.get_line_total()
    
    def validate(self, data):
        """Validate against total available batch quantities"""
        product = data.get('product')
        quantity = data.get('quantity', 0)
        
        # Check if product is active
        if product and not product.is_active:
            raise serializers.ValidationError(
                f"Product {product.name} is not active"
            )
        
        # For salesmen, check total available quantity across all batches
        request = self.context.get('request')
        if request and request.user.role == 'salesman':
            from products.models import BatchAssignment
            
            salesman = request.user.salesman_profile
            
            # Get total available quantity across all batch assignments
            assignments = BatchAssignment.objects.filter(
                salesman=salesman,
                batch__product=product,
                status__in=['delivered', 'partial'],
                batch__is_active=True
            ).exclude(
                batch__expiry_date__lt=timezone.now().date()
            )
            
            total_available = sum(assignment.outstanding_quantity for assignment in assignments)
            
            if quantity > total_available:
                raise serializers.ValidationError(
                    f"Insufficient stock for {product.name}. Available: {total_available}, Requested: {quantity}"
                )
        
        return data


class AutoBatchInvoiceCreateSerializer(serializers.ModelSerializer):
    """Simplified invoice creation that auto-allocates from available batches"""
    items = AutoBatchInvoiceItemSerializer(many=True, write_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'shop', 'due_date', 'tax_amount',
            'discount_amount', 'shop_margin', 'notes', 'terms_conditions', 'items',
            'subtotal', 'net_total', 'total_amount'
        ]
        read_only_fields = ['id', 'invoice_number', 'subtotal', 'net_total', 'total_amount']
    
    def validate(self, data):
        """Validate shop margin for salesmen"""
        from core.models import CompanySettings
        
        request = self.context.get('request')
        shop_margin = data.get('shop_margin', 0)
        
        # Only validate margin for salesmen, owners have no restrictions
        if request and request.user.role == 'salesman':
            settings = CompanySettings.get_settings()
            max_margin = settings.max_shop_margin_for_salesmen
            
            if shop_margin > max_margin:
                raise serializers.ValidationError({
                    'shop_margin': f'Salesmen cannot set shop margin above {max_margin}%. Current: {shop_margin}%'
                })
        
        return data
    
    def create(self, validated_data):
        from products.models import BatchAssignment
        
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
        
        # Create invoice items with automatic batch allocation
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            unit_price = item_data['unit_price']
            
            # Auto-allocate from available batches using FIFO
            self._allocate_and_create_items(invoice, product, quantity, unit_price)
        
        # Calculate totals
        invoice.calculate_totals()
        
        return invoice
    
    def _allocate_and_create_items(self, invoice, product, total_quantity, unit_price):
        """Allocate quantity across available batches using FIFO and create invoice items"""
        from products.models import BatchAssignment
        
        # Get available batch assignments for this salesman and product (FIFO order)
        assignments = BatchAssignment.objects.filter(
            salesman=invoice.salesman,
            batch__product=product,
            status__in=['delivered', 'partial'],
            batch__is_active=True
        ).exclude(
            batch__expiry_date__lt=timezone.now().date()
        ).order_by('batch__expiry_date', 'batch__manufacturing_date')
        
        remaining_quantity = total_quantity
        
        for assignment in assignments:
            if remaining_quantity <= 0:
                break
            
            # For salesmen, use only the assignment availability since they already have the goods
            available_in_assignment = assignment.outstanding_quantity
            if available_in_assignment <= 0:
                continue
            
            # Allocate from this assignment
            quantity_from_batch = min(remaining_quantity, available_in_assignment)
            
            # Check if an invoice item already exists for this invoice-product-batch combination
            existing_item = InvoiceItem.objects.filter(
                invoice=invoice,
                product=product,
                batch=assignment.batch
            ).first()
            
            if existing_item:
                # Update the existing item's quantity
                existing_item.quantity += quantity_from_batch
                existing_item.save()
            else:
                # Create new invoice item for this batch allocation
                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=product,
                    batch=assignment.batch,
                    quantity=quantity_from_batch,
                    unit_price=unit_price
                )
            
            remaining_quantity -= quantity_from_batch
        
        # Check if we could allocate all requested quantity
        if remaining_quantity > 0:
            raise serializers.ValidationError(
                f"Could not allocate {remaining_quantity} units of {product.name}. Insufficient batch stock available: {total_quantity - remaining_quantity} allocated."
            )


class CommissionSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    salesman_name = serializers.CharField(source='salesman.name', read_only=True)
    shop_name = serializers.CharField(source='invoice.shop.name', read_only=True)
    commission_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Commission
        fields = [
            'id', 'invoice', 'invoice_number', 'salesman', 'salesman_name', 
            'shop_name', 'commission_rate', 'commission_percentage', 
            'invoice_amount', 'commission_amount', 'status', 'paid_date', 
            'paid_by', 'payment_reference', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'invoice_number', 'salesman_name', 'shop_name', 
                          'commission_percentage', 'invoice_amount', 'commission_amount', 'created_at']
    
    def get_commission_percentage(self, obj):
        return f"{obj.commission_rate}%"


class EnhancedReturnSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    batch_expiry_date = serializers.DateField(source='batch.expiry_date', read_only=True)
    invoice_number = serializers.CharField(source='original_invoice.invoice_number', read_only=True)
    
    class Meta:
        model = Return
        fields = [
            'id', 'return_number', 'original_invoice', 'invoice_number',
            'product', 'product_name', 'batch', 'batch_number', 'batch_expiry_date',
            'quantity', 'reason', 'return_amount', 'approved', 'approved_by',
            'notes', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'return_number', 'product_name', 'batch_number', 
                          'batch_expiry_date', 'invoice_number', 'created_at', 'updated_at']
    
    def validate(self, data):
        batch = data.get('batch')
        quantity = data.get('quantity', 0)
        
        if batch and quantity > 0:
            # Check if there are enough sold items from this batch to return
            # This would involve checking invoice items that used this batch
            sold_from_batch = InvoiceItem.objects.filter(
                batch=batch,
                invoice__status__in=['paid', 'partial']
            ).aggregate(total_sold=models.Sum('quantity'))['total_sold'] or 0
            
            already_returned = Return.objects.filter(
                batch=batch,
                approved=True
            ).aggregate(total_returned=models.Sum('quantity'))['total_returned'] or 0
            
            available_for_return = sold_from_batch - already_returned
            
            if quantity > available_for_return:
                raise serializers.ValidationError(
                    f"Cannot return {quantity} units. Only {available_for_return} units available for return from batch {batch.batch_number}"
                )
        
        return data


class BatchSearchSerializer(serializers.Serializer):
    """Serializer for batch search functionality"""
    batch_number = serializers.CharField(required=False)
    product_id = serializers.IntegerField(required=False)
    salesman_id = serializers.IntegerField(required=False)
    
    def validate(self, data):
        if not data.get('batch_number') and not data.get('product_id'):
            raise serializers.ValidationError("Either batch_number or product_id must be provided")
        return data


class BatchReturnSerializer(serializers.ModelSerializer):
    """Enhanced Return serializer with batch-centric functionality"""
    invoice_number = serializers.CharField(source='original_invoice.invoice_number', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    batch_expiry_date = serializers.DateField(source='batch.expiry_date', read_only=True)
    shop_name = serializers.CharField(source='original_invoice.shop.name', read_only=True)
    salesman_name = serializers.CharField(source='original_invoice.salesman.user.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = Return
        fields = [
            'id', 'return_number', 'original_invoice', 'invoice_number', 'product', 'product_name',
            'product_sku', 'batch', 'batch_number', 'batch_expiry_date', 'quantity', 'reason', 
            'return_amount', 'approved', 'approved_by', 'approved_by_name', 'shop_name', 
            'salesman_name', 'created_by', 'created_by_name', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'return_number', 'created_at', 'updated_at', 'invoice_number', 'product_name', 
            'product_sku', 'batch_number', 'batch_expiry_date', 'shop_name', 'salesman_name',
            'created_by_name', 'approved_by_name'
        ]
    
    def validate(self, data):
        invoice = data.get('original_invoice')
        product = data.get('product')
        batch = data.get('batch')
        quantity = data.get('quantity', 0)
        
        # Check if product was in the invoice
        try:
            invoice_item = InvoiceItem.objects.get(invoice=invoice, product=product)
        except InvoiceItem.DoesNotExist:
            raise serializers.ValidationError(
                f"Product {product.name} was not in invoice {invoice.invoice_number}"
            )
        
        # If batch is specified, validate batch was used in the invoice
        if batch:
            if invoice_item.batch != batch:
                raise serializers.ValidationError(
                    f"Batch {batch.batch_number} was not used in invoice {invoice.invoice_number} for product {product.name}"
                )
        
        # Check if return quantity doesn't exceed purchased quantity
        if quantity > invoice_item.quantity:
            raise serializers.ValidationError(
                f"Return quantity ({quantity}) exceeds purchased quantity ({invoice_item.quantity})"
            )
        
        # Check for existing returns for this specific batch and product
        existing_returns_filter = {
            'original_invoice': invoice,
            'product': product,
            'approved': True
        }
        if batch:
            existing_returns_filter['batch'] = batch
            
        existing_returns = Return.objects.filter(**existing_returns_filter).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
        
        if existing_returns + quantity > invoice_item.quantity:
            raise serializers.ValidationError(
                f"Total return quantity would exceed purchased quantity. "
                f"Already returned: {existing_returns}, Requesting: {quantity}, "
                f"Purchased: {invoice_item.quantity}"
            )
        
        return data


class BatchReturnCreateSerializer(serializers.Serializer):
    """Serializer for creating returns during settlement - accepts IDs instead of objects"""
    original_invoice = serializers.IntegerField()
    product = serializers.IntegerField()
    batch = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    reason = serializers.ChoiceField(choices=[
        'DEFECTIVE', 'EXPIRED', 'DAMAGED', 'WRONG_PRODUCT', 'CUSTOMER_REQUEST', 'OTHER'
    ])
    return_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        try:
            # Convert IDs to actual model instances
            invoice = Invoice.objects.get(id=data['original_invoice'])
            product = Product.objects.get(id=data['product'])
            batch = Batch.objects.get(id=data['batch'])
            
        except (Invoice.DoesNotExist, Product.DoesNotExist, Batch.DoesNotExist) as e:
            raise serializers.ValidationError(f"Referenced object not found: {str(e)}")
        
        # Check if this batch was used in the invoice
        try:
            invoice_item = InvoiceItem.objects.get(
                invoice=invoice,
                product=product,
                batch=batch
            )
        except InvoiceItem.DoesNotExist:
            raise serializers.ValidationError(
                f"This batch was not sold in the specified invoice"
            )
        
        # Check if return quantity doesn't exceed purchased quantity
        if data['quantity'] > invoice_item.quantity:
            raise serializers.ValidationError(
                f"Return quantity ({data['quantity']}) exceeds purchased quantity ({invoice_item.quantity})"
            )
        
        # Check for existing returns for this specific batch and product
        existing_returns = Return.objects.filter(
            original_invoice=invoice,
            product=product,
            batch=batch,
            approved=True
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
        
        if existing_returns + data['quantity'] > invoice_item.quantity:
            raise serializers.ValidationError(
                f"Total return quantity would exceed purchased quantity. "
                f"Already returned: {existing_returns}, Requesting: {data['quantity']}, "
                f"Purchased: {invoice_item.quantity}"
            )
        
        # Store the actual objects for creation
        data['_invoice'] = invoice
        data['_product'] = product
        data['_batch'] = batch
        
        return data
    
    def create(self, validated_data):
        # Get the actual objects
        invoice = validated_data.pop('_invoice')
        product = validated_data.pop('_product')
        batch = validated_data.pop('_batch')
        
        request = self.context.get('request')
        user = request.user if request else None
        
        # Create the return with actual objects
        return_obj = Return.objects.create(
            original_invoice=invoice,
            product=product,
            batch=batch,
            quantity=validated_data['quantity'],
            reason=validated_data['reason'],
            return_amount=validated_data['return_amount'],
            notes=validated_data.get('notes', ''),
            approved=True,  # Auto-approve for settlement
            approved_by=user,
            approved_at=timezone.now(),
            created_by=user
        )
        
        return return_obj
    """Serializer for creating returns during settlement - accepts IDs instead of objects"""
    original_invoice = serializers.IntegerField()
    product = serializers.IntegerField()
    batch = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    reason = serializers.ChoiceField(choices=[
        ('DEFECTIVE', 'Defective'),
        ('EXPIRED', 'Expired'),
        ('DAMAGED', 'Damaged'),
        ('WRONG_PRODUCT', 'Wrong Product'),
        ('CUSTOMER_REQUEST', 'Customer Request'),
        ('OTHER', 'Other')
    ])
    return_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        try:
            invoice = Invoice.objects.get(id=data['original_invoice'])
            product = Product.objects.get(id=data['product'])
            batch = Batch.objects.get(id=data['batch'])
        except (Invoice.DoesNotExist, Product.DoesNotExist, Batch.DoesNotExist) as e:
            raise serializers.ValidationError(f"Referenced object not found: {str(e)}")
        
        # Check if this exact batch was sold in the invoice
        try:
            invoice_item = InvoiceItem.objects.get(
                invoice=invoice,
                product=product,
                batch=batch
            )
        except InvoiceItem.DoesNotExist:
            raise serializers.ValidationError(
                f"Batch {batch.batch_number} of product {product.name} was not sold in invoice {invoice.invoice_number}"
            )
        
        # Check if return quantity doesn't exceed purchased quantity
        if data['quantity'] > invoice_item.quantity:
            raise serializers.ValidationError(
                f"Return quantity ({data['quantity']}) exceeds purchased quantity ({invoice_item.quantity})"
            )
        
        # Check for existing returns for this specific batch and product
        existing_returns = Return.objects.filter(
            original_invoice=invoice,
            product=product,
            batch=batch,
            approved=True
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
        
        if existing_returns + data['quantity'] > invoice_item.quantity:
            raise serializers.ValidationError(
                f"Total return quantity would exceed purchased quantity. "
                f"Already returned: {existing_returns}, Requesting: {data['quantity']}, "
                f"Purchased: {invoice_item.quantity}"
            )
        
        # Store the actual objects for creation
        data['_invoice'] = invoice
        data['_product'] = product
        data['_batch'] = batch
        data['_invoice_item'] = invoice_item
        
        return data

    def create(self, validated_data):
        # Remove the helper objects
        invoice = validated_data.pop('_invoice')
        product = validated_data.pop('_product')
        batch = validated_data.pop('_batch')
        invoice_item = validated_data.pop('_invoice_item')
        
        # Create the return with actual objects
        return Return.objects.create(
            original_invoice=invoice,
            product=product,
            batch=batch,
            quantity=validated_data['quantity'],
            reason=validated_data['reason'],
            return_amount=validated_data['return_amount'],
            notes=validated_data.get('notes', ''),
            approved=True,  # Auto-approve for settlement
            approved_by=self.context['request'].user,
            approved_at=timezone.now(),
            created_by=self.context['request'].user
        )


class InvoiceSettlementWithReturnsSerializer(serializers.Serializer):
    """Serializer for invoice settlement with returns support"""
    invoice_id = serializers.IntegerField()
    returns = BatchReturnCreateSerializer(many=True, required=False)
    payments = SettlementPaymentSerializer(many=True, required=False)
    settlement_notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        invoice_id = data.get('invoice_id')
        returns = data.get('returns', [])
        payments = data.get('payments', [])
        
        # Validate invoice exists
        try:
            invoice = Invoice.objects.get(id=invoice_id)
        except Invoice.DoesNotExist:
            raise serializers.ValidationError(f"Invoice with ID {invoice_id} not found")
        
        # Validate returns if provided
        if returns:
            for return_data in returns:
                return_serializer = BatchReturnCreateSerializer(data=return_data, context=self.context)
                if not return_serializer.is_valid():
                    raise serializers.ValidationError(f"Invalid return data: {return_serializer.errors}")
        
        # Validate payments if provided
        if payments:
            total_payment = sum(Decimal(str(payment.get('amount', 0))) for payment in payments)
            if total_payment > invoice.balance_due:
                raise serializers.ValidationError(
                    f"Total payment amount ({total_payment}) exceeds balance due ({invoice.balance_due})"
                )
        
        return data


class BatchTraceabilitySerializer(serializers.Serializer):
    """Serializer for batch traceability data"""
    batch_id = serializers.IntegerField()
    batch_number = serializers.CharField()
    product_name = serializers.CharField()
    product_sku = serializers.CharField()
    manufacturing_date = serializers.DateField()
    expiry_date = serializers.DateField()
    initial_quantity = serializers.IntegerField()
    current_quantity = serializers.IntegerField()
    
    # Sales data
    total_sold = serializers.IntegerField()
    total_returned = serializers.IntegerField()
    shops_sold_to = serializers.ListField(child=serializers.DictField())
    shops_returned_from = serializers.ListField(child=serializers.DictField())
    
    # Salesmen data
    salesmen_assigned = serializers.ListField(child=serializers.DictField())
    
    # Quality data
    quality_status = serializers.CharField()
    return_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


# Serializers for enhanced returns management with batch identification
class BatchReturnCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating returns with mandatory batch identification"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    
    class Meta:
        model = Return
        fields = [
            'id', 'original_invoice', 'product', 'product_name', 'batch', 'batch_number',
            'quantity', 'reason', 'return_amount', 'notes'
        ]
        read_only_fields = ['id', 'product_name', 'batch_number']
    
    def validate(self, data):
        """Enhanced validation for batch-specific returns"""
        batch = data.get('batch')
        product = data.get('product')
        quantity = data.get('quantity', 0)
        original_invoice = data.get('original_invoice')
        
        # Batch is mandatory for returns
        if not batch:
            raise serializers.ValidationError("Batch identification is required for returns")
        
        # Ensure batch belongs to the product
        if batch.product != product:
            raise serializers.ValidationError(
                f"Batch {batch.batch_number} does not belong to product {product.name}"
            )
        
        # Check if there are sold items from this specific batch in the invoice
        invoice_items_with_batch = InvoiceItem.objects.filter(
            invoice=original_invoice,
            product=product,
            batch=batch
        )
        
        if not invoice_items_with_batch.exists():
            raise serializers.ValidationError(
                f"No items from batch {batch.batch_number} were sold in invoice {original_invoice.invoice_number}"
            )
        
        # Calculate total sold from this specific batch in this invoice
        total_sold_from_batch = invoice_items_with_batch.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
        
        # Check existing returns from this batch for this invoice
        existing_returns = Return.objects.filter(
            original_invoice=original_invoice,
            product=product,
            batch=batch,
            approved=True
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
        
        available_for_return = total_sold_from_batch - existing_returns
        
        if quantity > available_for_return:
            raise serializers.ValidationError(
                f"Cannot return {quantity} units. Only {available_for_return} units from batch {batch.batch_number} available for return"
            )
        
        return data
    
    def create(self, validated_data):
        """Create return and update batch quality metrics"""
        request = self.context.get('request')
        if request:
            validated_data['created_by'] = request.user
        
        return_instance = super().create(validated_data)
        
        # Update batch return rate when return is created
        if return_instance.batch:
            return_instance.batch.update_return_rate()
        
        return return_instance


class CommissionDashboardSerializer(serializers.Serializer):
    """Serializer for commission dashboard data"""
    total_pending_commissions = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_paid_commissions = serializers.DecimalField(max_digits=12, decimal_places=2)
    salesman_commissions = serializers.ListField()
    recent_commissions = CommissionSerializer(many=True)


class EnhancedSettlementSerializer(serializers.ModelSerializer):
    """Enhanced settlement serializer with bill-to-bill support"""
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    shop_name = serializers.CharField(source='invoice.shop.name', read_only=True)
    payments = serializers.SerializerMethodField()
    unsettled_invoices_total = serializers.SerializerMethodField()
    
    class Meta:
        model = InvoiceSettlement
        fields = [
            'id', 'invoice', 'invoice_number', 'shop_name', 'settlement_date',
            'total_amount', 'unsettled_invoices_total', 'payments', 'notes', 'created_by'
        ]
        read_only_fields = ['id', 'invoice_number', 'shop_name', 'unsettled_invoices_total', 'payments']
    
    def get_payments(self, obj):
        payments = SettlementPayment.objects.filter(settlement=obj)
        return SettlementPaymentSerializer(payments, many=True).data
    
    def get_unsettled_invoices_total(self, obj):
        """Get total amount of unsettled invoices for the same shop"""
        unsettled_invoices = Invoice.objects.filter(
            shop=obj.invoice.shop,
            balance_due__gt=0
        ).exclude(id=obj.invoice.id)
        
        return sum(invoice.balance_due for invoice in unsettled_invoices)


class SettlementPaymentSerializer(serializers.ModelSerializer):
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = SettlementPayment
        fields = [
            'id', 'payment_method', 'payment_method_display', 'amount',
            'reference_number', 'bank_name', 'cheque_date', 'notes'
        ]


class BatchDefectSerializer(serializers.Serializer):
    """Serializer for batch defect reporting"""
    batch_id = serializers.IntegerField()
    defect_type = serializers.ChoiceField(choices=[
        ('quality_issue', 'Quality Issue'),
        ('contamination', 'Contamination'),
        ('packaging_defect', 'Packaging Defect'),
        ('expiry_issue', 'Expiry Issue'),
        ('other', 'Other')
    ])
    severity = serializers.ChoiceField(choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ])
    description = serializers.CharField(max_length=1000)
    reported_by_name = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class BatchRecallSerializer(serializers.Serializer):
    """Serializer for batch recall operations"""
    batch_id = serializers.IntegerField()
    recall_reason = serializers.CharField(max_length=500)
    severity = serializers.ChoiceField(choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ])
    recall_all_stock = serializers.BooleanField(default=True)
    notify_customers = serializers.BooleanField(default=True)
    
    def validate_batch_id(self, value):
        """Validate batch exists and is not already recalled"""
        try:
            from products.models import Batch
            batch = Batch.objects.get(id=value)
            if batch.recall_initiated_at:
                raise serializers.ValidationError("This batch has already been recalled")
            return value
        except Batch.DoesNotExist:
            raise serializers.ValidationError("Batch not found")

