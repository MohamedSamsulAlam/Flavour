from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/', views.payment_page, name='payment'),
    path('payment/process/', views.process_payment, name='process_payment'),
    path('bulk/<int:restaurant_id>/', views.bulk_order, name='bulk_order'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),
    path('track/<int:order_id>/', views.order_tracking, name='order_tracking'),
    path('my-orders/', views.my_orders, name='my_orders'),
]
