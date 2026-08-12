from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('restaurant', 'Restaurant Owner'),
        ('customer', 'Customer'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def is_admin_user(self):
        return self.role == 'admin' or self.is_superuser

    def is_restaurant_user(self):
        return self.role == 'restaurant'

    def is_customer_user(self):
        return self.role == 'customer'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
