from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.home, name='home'),
    path('restaurant/<int:pk>/', views.restaurant_detail, name='restaurant_detail'),
    path('map/', views.map_view, name='map'),
]
