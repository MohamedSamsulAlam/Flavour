from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['item_name', 'item_price', 'quantity']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'restaurant', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'restaurant']
    search_fields = ['customer__username', 'restaurant__name']
    inlines = [OrderItemInline]
