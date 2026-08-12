from django.urls import path
from . import views

app_name = 'restaurants'

urlpatterns = [
    path('setup/', views.setup_restaurant, name='setup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('menu/', views.menu_list, name='menu'),
    path('menu/add/', views.menu_add, name='menu_add'),
    path('menu/<int:pk>/edit/', views.menu_edit, name='menu_edit'),
    path('menu/<int:pk>/delete/', views.menu_delete, name='menu_delete'),
    path('orders/', views.orders_list, name='orders'),
    path('orders/<int:order_id>/status/', views.update_order_status, name='update_order_status'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
]
