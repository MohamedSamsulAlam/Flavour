from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_customer, name='register'),
    path('register/restaurant/', views.register_restaurant, name='register_restaurant'),
    path('profile/', views.profile_view, name='profile'),
]
