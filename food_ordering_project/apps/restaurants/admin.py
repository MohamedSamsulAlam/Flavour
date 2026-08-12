from django.contrib import admin
from .models import Restaurant, MenuItem, Category


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'cuisine', 'is_open', 'rating', 'created_at']
    list_filter = ['cuisine', 'is_open']
    search_fields = ['name', 'owner__username']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'category', 'price', 'quantity', 'is_available']
    list_filter = ['is_available', 'is_vegetarian', 'restaurant']
    search_fields = ['name', 'restaurant__name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'order']
