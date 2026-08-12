from django.db import models
from django.conf import settings


class Restaurant(models.Model):
    CUISINE_CHOICES = [
        ('indian', 'Indian'), ('chinese', 'Chinese'), ('italian', 'Italian'),
        ('mexican', 'Mexican'), ('american', 'American'), ('thai', 'Thai'),
        ('japanese', 'Japanese'), ('mediterranean', 'Mediterranean'), ('other', 'Other'),
    ]
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='restaurant')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    cuisine = models.CharField(max_length=50, choices=CUISINE_CHOICES, default='other')
    address = models.TextField()
    phone = models.CharField(max_length=15)
    logo = models.ImageField(upload_to='restaurant_logos/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='restaurant_covers/', blank=True, null=True)
    is_open = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    delivery_time = models.PositiveIntegerField(default=30, help_text='Estimated delivery in minutes')
    minimum_order = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return f"{self.name} — {self.restaurant.name}"


class MenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_vegetarian = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    quantity = models.PositiveIntegerField(default=100, help_text='Available stock')
    low_stock_threshold = models.PositiveIntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} — ₹{self.price}"

    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold
