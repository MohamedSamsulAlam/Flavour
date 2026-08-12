from django.db import models
from django.conf import settings
from apps.restaurants.models import Restaurant, MenuItem


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('netbanking', 'Net Banking'),
        ('wallet', 'Wallet'),
    ]
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cod')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} by {self.customer.username}"

    @property
    def status_badge_class(self):
        classes = {
            'pending': 'badge-warning',
            'confirmed': 'badge-info',
            'preparing': 'badge-primary',
            'ready': 'badge-success',
            'delivered': 'badge-delivered',
            'cancelled': 'badge-danger',
        }
        return classes.get(self.status, 'badge-secondary')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    item_name = models.CharField(max_length=200)
    item_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.item_name}"

    @property
    def subtotal(self):
        return self.item_price * self.quantity
