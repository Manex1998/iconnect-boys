from django.db import models

# Create your models here.

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=255, default=generate_order_number, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Added for tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_method = models.CharField(max_length=50, blank=True)
    fastway_label = models.CharField(max_length=50, blank=True, null=True)
    completed_at = models.DateTimeField(null=True, blank=True)  # Added for analytics

    # Add to Order model
    billing_name = models.CharField(max_length=255, blank=True)
    billing_email = models.EmailField(blank=True)
    billing_address = models.TextField(blank=True)
    billing_phone = models.CharField(max_length=50, blank=True)

    shipping_name = models.CharField(max_length=255, blank=True)
    shipping_email = models.EmailField(blank=True)
    shipping_address = models.TextField(blank=True)
    shipping_phone = models.CharField(max_length=50, blank=True)

    notes = models.TextField(blank=True)


    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

    def update_total(self):
        self.total_price = sum(item.total_price() for item in self.items.all())  # ← add ()
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price_at_order = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def total_price(self):
        price = self.discount_price_at_order if self.discount_price_at_order else self.price_at_order
        return price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    updated_at = models.DateTimeField(auto_now=True)  # Added for tracking

    def __str__(self):
        return f"{self.user.username}'s Cart"
    
    @property
    def total(self):
        return sum(
            item.quantity * (item.product.discount_price if item.product.is_discounted else item.product.price)
            for item in self.items.select_related('product')
        )
    
    @property
    def total_quantity(self):
        """
        Returns the total number of items in the cart, 
        summing the quantity of each CartItem.
        """
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    


