from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from accounts.models import Salesman, Shop
from products.models import Product

User = get_user_model()


class Invoice(models.Model):
    """Invoice model for sales transactions"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    invoice_number = models.CharField(max_length=100, unique=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='invoices')
    salesman = models.ForeignKey(Salesman, on_delete=models.CASCADE, related_name='invoices')
    invoice_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Financial fields
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    shop_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Percentage
    net_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Additional fields
    notes = models.TextField(blank=True, null=True)
    terms_conditions = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.shop.name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate invoice number if not provided
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        
        # Calculate totals
        self.calculate_totals()
        
        super().save(*args, **kwargs)
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        from datetime import datetime
        today = datetime.now()
        prefix = f"INV{today.strftime('%Y%m')}"
        
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('-invoice_number').first()
        
        if last_invoice:
            last_number = int(last_invoice.invoice_number[-4:])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:04d}"
    
    def calculate_totals(self):
        """Calculate invoice totals based on unit price * quantity with shop margin applied at invoice level"""
        if not self.pk:  # If invoice hasn't been saved yet, skip calculation
            return
        
        items = self.items.all()
        
        # Calculate total product price (sum of unit_price * quantity for all items)
        total_product_price = sum(
            Decimal(str(item.unit_price)) * Decimal(str(item.quantity)) 
            for item in items
        ) or Decimal('0.00')
        
        # Use invoice-level shop margin
        shop_margin_percent = Decimal(str(self.shop_margin)) or Decimal('0.00')
        
        # Calculate margin amount: total_product_price * shop_margin_percent / 100
        margin_amount = total_product_price * (shop_margin_percent / Decimal('100'))
        
        # Invoice calculation: total_product_price - margin_amount + tax - discount
        self.subtotal = total_product_price - margin_amount
        self.net_total = self.subtotal + Decimal(str(self.tax_amount)) - Decimal(str(self.discount_amount))
        self.balance_due = self.net_total - Decimal(str(self.paid_amount))
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        from datetime import date
        return self.due_date and self.due_date < date.today() and self.balance_due > 0
    
    @property
    def total_amount(self):
        """Get the total amount of the invoice (alias for net_total)"""
        return self.net_total
    
    def get_total_amount(self):
        """Get the total amount of the invoice"""
        return self.net_total
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['shop', 'status']),
            models.Index(fields=['salesman', 'invoice_date']),
        ]


class InvoiceItem(models.Model):
    """Individual items in an invoice with batch tracking"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='invoice_items')
    batch = models.ForeignKey('products.Batch', on_delete=models.CASCADE, related_name='invoice_items', null=True, blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    calculated_price = models.DecimalField(max_digits=10, decimal_places=2)  # Price after margins
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Margin information for tracking
    salesman_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    shop_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        batch_info = f" (Batch: {self.batch.batch_number})" if self.batch else ""
        return f"{self.product.name}{batch_info} x {self.quantity} - {self.invoice.invoice_number}"
    
    def save(self, *args, **kwargs):
        # Set calculated_price to unit_price (no margins applied at item level)
        self.calculated_price = Decimal(str(self.unit_price))
        
        # Set total_price to unit_price * quantity (simple multiplication)
        self.total_price = Decimal(str(self.quantity)) * Decimal(str(self.unit_price))
        
        is_new = self.pk is None
        old_quantity = 0
        
        if not is_new:
            # Get old quantity for stock adjustment
            old_item = InvoiceItem.objects.get(pk=self.pk)
            old_quantity = old_item.quantity
        
        super().save(*args, **kwargs)
        
        # Update stock quantities when invoice item is saved
        self._update_stock_quantities(old_quantity, is_new)
        
        # Update invoice totals
        if self.invoice_id:  # Only if invoice exists
            self.invoice.calculate_totals()
            self.invoice.save()
    
    def delete(self, *args, **kwargs):
        # Restore stock when item is deleted
        self._restore_stock_quantities()
        super().delete(*args, **kwargs)
    
    def _update_stock_quantities(self, old_quantity=0, is_new=True):
        """Update batch stock system for invoice items"""
        from products.models import StockMovement, BatchTransaction, BatchAssignment
        
        try:
            # Only update stock if invoice is not in draft status
            if self.invoice.status == 'draft':
                return
            
            quantity_change = self.quantity - old_quantity
            
            if quantity_change == 0:
                return
            
            # If batch is specified, update batch stock
            if self.batch:
                # For sales, we need to track which salesman sold from which batch
                # Find salesman's batch assignments for this batch
                assignments = BatchAssignment.objects.filter(
                    batch=self.batch,
                    salesman=self.invoice.salesman,
                    status__in=['delivered', 'partial']
                ).order_by('created_at')
                
                if not assignments.exists():
                    raise ValueError(f"Salesman doesn't have access to batch {self.batch.batch_number}")
                
                # Calculate total available for sale
                total_available_qty = sum(assignment.outstanding_quantity for assignment in assignments)
                if quantity_change > 0 and total_available_qty < quantity_change:
                    raise ValueError(f"Insufficient batch stock. Available: {total_available_qty}, Required: {quantity_change}")
                
                # For sales (positive quantity_change), mark as "sold" by increasing returned_quantity
                # This represents the product leaving the salesman's possession through sale
                if quantity_change > 0:
                    remaining_to_sell = quantity_change
                    for assignment in assignments:
                        if remaining_to_sell <= 0:
                            break
                        
                        available_in_assignment = assignment.outstanding_quantity
                        if available_in_assignment > 0:
                            to_sell = min(remaining_to_sell, available_in_assignment)
                            
                            # Increase returned_quantity to represent sold products
                            assignment.returned_quantity += to_sell
                            
                            # Update assignment status
                            if assignment.returned_quantity >= assignment.delivered_quantity:
                                assignment.status = 'returned'
                            elif assignment.returned_quantity > 0:
                                assignment.status = 'partial'
                            
                            assignment.save()
                            remaining_to_sell -= to_sell
                
                # Create batch transaction record for the sale
                BatchTransaction.objects.create(
                    batch=self.batch,
                    transaction_type='sale',
                    quantity=-quantity_change if quantity_change > 0 else abs(quantity_change),
                    balance_after=self.batch.current_quantity,  # Batch quantity doesn't change for salesman sales
                    reference_type='invoice_item',
                    reference_id=self.id,
                    notes=f"Sale to {self.invoice.shop.name} by {self.invoice.salesman.user.get_full_name()}",
                    created_by=self.invoice.created_by
                )
            else:
                # If no batch specified, we need to allocate from available batches using FIFO
                if quantity_change > 0:
                    self._allocate_from_available_batches(quantity_change)
            
            # Create stock movement record for audit
            StockMovement.objects.create(
                product=self.product,
                salesman=self.invoice.salesman,
                movement_type='sale',
                quantity=-quantity_change if quantity_change > 0 else abs(quantity_change),
                notes=f"Invoice {self.invoice.invoice_number} - {self.invoice.shop.name}",
                reference_id=self.invoice.invoice_number,
                created_by=self.invoice.created_by
            )
                
        except Exception as e:
            raise ValueError(f"Stock update failed: {str(e)}")
    
    def _allocate_from_available_batches(self, quantity_needed):
        """Allocate stock from salesman's available batches using FIFO"""
        from products.models import BatchAssignment
        
        # Get salesman's available batch assignments ordered by FIFO
        assignments = BatchAssignment.objects.filter(
            batch__product=self.product,
            salesman=self.invoice.salesman,
            status__in=['delivered', 'partial']
        ).filter(
            delivered_quantity__gt=models.F('returned_quantity')
        ).order_by('batch__manufacturing_date', 'batch__expiry_date', 'created_at')
        
        total_available = sum(assignment.outstanding_quantity for assignment in assignments)
        if total_available < quantity_needed:
            raise ValueError(f"Insufficient stock for {self.product.name}. Available: {total_available}, Required: {quantity_needed}")
        
        remaining_to_allocate = quantity_needed
        
        for assignment in assignments:
            if remaining_to_allocate <= 0:
                break
            
            available_in_assignment = assignment.outstanding_quantity
            if available_in_assignment > 0:
                to_allocate = min(available_in_assignment, remaining_to_allocate)
                
                # Update assignment (increase returned_quantity to represent sale)
                assignment.returned_quantity += to_allocate
                
                # Update assignment status
                if assignment.returned_quantity >= assignment.delivered_quantity:
                    assignment.status = 'returned'
                elif assignment.returned_quantity > 0:
                    assignment.status = 'partial'
                
                assignment.save()
                
                # Set batch reference for this invoice item to the first allocated batch
                if not self.batch:
                    self.batch = assignment.batch
                    self.save()
                
                # Create batch transaction
                BatchTransaction.objects.create(
                    batch=assignment.batch,
                    transaction_type='sale',
                    quantity=-to_allocate,
                    balance_after=assignment.batch.current_quantity,
                    reference_type='invoice_item',
                    reference_id=self.id,
                    notes=f"Auto-allocated sale to {self.invoice.shop.name}",
                    created_by=self.invoice.created_by
                )
                
                remaining_to_allocate -= to_allocate
    
    def _restore_stock_quantities(self):
        """Restore stock quantities when invoice item is deleted"""
        from products.models import StockMovement, BatchTransaction, BatchAssignment
        
        try:
            # Only restore stock if invoice is not in draft status
            if self.invoice.status == 'draft':
                return
            
            if self.batch:
                # Find the assignment that was reduced for this sale and restore it
                assignments = BatchAssignment.objects.filter(
                    batch=self.batch,
                    salesman=self.invoice.salesman,
                    status__in=['partial', 'returned']
                ).order_by('created_at')
                
                # Restore the quantity by reducing returned_quantity
                remaining_to_restore = self.quantity
                for assignment in assignments:
                    if remaining_to_restore <= 0:
                        break
                    
                    # Check how much we can restore from this assignment
                    can_restore = min(assignment.returned_quantity, remaining_to_restore)
                    if can_restore > 0:
                        assignment.returned_quantity -= can_restore
                        
                        # Update assignment status
                        if assignment.returned_quantity == 0:
                            assignment.status = 'delivered'
                        elif assignment.returned_quantity < assignment.delivered_quantity:
                            assignment.status = 'partial'
                        
                        assignment.save()
                        remaining_to_restore -= can_restore
                
                # Create reversal batch transaction
                BatchTransaction.objects.create(
                    batch=self.batch,
                    transaction_type='return',
                    quantity=self.quantity,
                    balance_after=self.batch.current_quantity,
                    reference_type='invoice_cancellation',
                    reference_id=self.id,
                    notes=f"Invoice item cancelled: {self.invoice.invoice_number}",
                    created_by=self.invoice.created_by
                )
            
            # Create stock movement record for audit
            StockMovement.objects.create(
                product=self.product,
                movement_type='return',
                quantity=self.quantity,  # Positive for inward movement
                salesman=self.invoice.salesman,
                notes=f"Invoice item deleted: {self.invoice.invoice_number}",
                created_by=self.invoice.created_by
            )
            
        except Exception as e:
            print(f"Error restoring stock quantities: {e}")
    
    def get_line_total(self):
        """Get the line total for this invoice item"""
        return self.total_price
    
    class Meta:
        db_table = 'invoice_items'
        unique_together = ['invoice', 'product', 'batch']


class Transaction(models.Model):
    """Payment transactions for invoices"""
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('return', 'Return'),
        ('bill_to_bill', 'Bill to Bill'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit_note', 'Credit Note'),
    ]
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='transactions')
    transaction_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    
    # Additional payment details
    reference_number = models.CharField(max_length=100, blank=True, null=True)  # Cheque number, transfer ID, etc.
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    cheque_date = models.DateField(blank=True, null=True)
    
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_payment_method_display()} - {self.amount} - {self.invoice.invoice_number}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update invoice paid amount and status
        self.invoice.paid_amount = self.invoice.transactions.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        self.invoice.balance_due = self.invoice.net_total - self.invoice.paid_amount
        
        # Update invoice status
        if self.invoice.balance_due <= 0:
            self.invoice.status = 'paid'
        elif self.invoice.paid_amount > 0:
            self.invoice.status = 'partial'
        
        self.invoice.save()
    
    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']


class Return(models.Model):
    """Product return model"""
    
    RETURN_REASONS = [
        ('defective', 'Defective Product'),
        ('wrong_item', 'Wrong Item'),
        ('damaged', 'Damaged in Transit'),
        ('expired', 'Expired Product'),
        ('customer_request', 'Customer Request'),
        ('other', 'Other'),
    ]
    
    return_number = models.CharField(max_length=100, unique=True)
    original_invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='returns')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    batch = models.ForeignKey('products.Batch', on_delete=models.CASCADE, related_name='returns', null=True, blank=True)
    quantity = models.PositiveIntegerField()
    reason = models.CharField(max_length=20, choices=RETURN_REASONS)
    return_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_returns')
    
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Return {self.return_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        if not self.return_number:
            self.return_number = self.generate_return_number()
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update batch stock when return is approved
        if self.approved and is_new:
            self._update_batch_stock()
    
    def _update_batch_stock(self):
        """Update batch stock when return is processed"""
        if self.approved and self.batch:
            from products.models import BatchTransaction, BatchAssignment
            
            # For returns, we need to restore the stock to the salesman's batch assignment
            # Find the salesman's assignment for this batch
            try:
                assignment = BatchAssignment.objects.filter(
                    batch=self.batch,
                    salesman=self.original_invoice.salesman,
                    status__in=['partial', 'returned']
                ).first()
                
                if assignment:
                    # Restore the stock by reducing returned_quantity
                    assignment.returned_quantity = max(0, assignment.returned_quantity - self.quantity)
                    
                    # Update assignment status
                    if assignment.returned_quantity == 0:
                        assignment.status = 'delivered'
                    elif assignment.returned_quantity < assignment.delivered_quantity:
                        assignment.status = 'partial'
                    
                    assignment.save()
                else:
                    # If no assignment found, the stock returns to general batch inventory
                    self.batch.current_quantity += self.quantity
                    self.batch.save()
            except Exception:
                # Fallback: add back to batch inventory
                self.batch.current_quantity += self.quantity
                self.batch.save()
            
            # Create batch transaction record
            BatchTransaction.objects.create(
                batch=self.batch,
                transaction_type='return',
                quantity=self.quantity,
                balance_after=self.batch.current_quantity,
                reference_type='return',
                reference_id=self.id,
                notes=f"Customer return: {self.return_number} - {self.reason}",
                created_by=self.created_by
            )
    
    def generate_return_number(self):
        """Generate unique return number"""
        from datetime import datetime
        today = datetime.now()
        prefix = f"RET{today.strftime('%Y%m')}"
        
        last_return = Return.objects.filter(
            return_number__startswith=prefix
        ).order_by('-return_number').first()
        
        if last_return:
            last_number = int(last_return.return_number[-4:])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:04d}"
    
    class Meta:
        db_table = 'returns'
        ordering = ['-created_at']


class InvoiceSettlement(models.Model):
    """Settlement session for an invoice with multiple payment methods"""
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='settlements')
    settlement_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Settlement for {self.invoice.invoice_number} - {self.total_amount}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update invoice paid amount and status
        total_paid = sum(
            settlement.total_amount 
            for settlement in self.invoice.settlements.all()
        )
        
        self.invoice.paid_amount = total_paid
        self.invoice.balance_due = self.invoice.net_total - self.invoice.paid_amount
        
        # Update invoice status
        if self.invoice.balance_due <= 0:
            self.invoice.status = 'paid'
        elif self.invoice.paid_amount > 0:
            self.invoice.status = 'partial'
        
        self.invoice.save()
    
    class Meta:
        db_table = 'invoice_settlements'
        ordering = ['-created_at']


class SettlementPayment(models.Model):
    """Individual payment within a settlement"""
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('return', 'Return'),
        ('bill_to_bill', 'Bill to Bill'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit_note', 'Credit Note'),
    ]
    
    settlement = models.ForeignKey(InvoiceSettlement, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    
    # Additional payment details
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    cheque_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_payment_method_display()} - {self.amount}"
    
    class Meta:
        db_table = 'settlement_payments'
        ordering = ['created_at']


class Commission(models.Model):
    """Commission tracking for salesmen"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name='commission')
    salesman = models.ForeignKey(Salesman, on_delete=models.CASCADE, related_name='commissions')
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)  # 10% default
    invoice_amount = models.DecimalField(max_digits=12, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment tracking
    paid_date = models.DateTimeField(null=True, blank=True)
    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='paid_commissions')
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Commission for {self.salesman.name} - {self.invoice.invoice_number} ({self.commission_amount})"
    
    def save(self, *args, **kwargs):
        # Calculate commission amount
        self.invoice_amount = self.invoice.net_total
        self.commission_amount = (self.invoice_amount * self.commission_rate) / Decimal('100')
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'commissions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['salesman', 'status']),
            models.Index(fields=['invoice', 'status']),
        ]
