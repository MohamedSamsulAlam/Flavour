from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomerRegistrationForm, RestaurantRegistrationForm, CustomAuthForm


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)
    
    form = CustomAuthForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f'Welcome back, {user.username}!')
        return _redirect_by_role(user)
    
    return render(request, 'accounts/login.html', {'form': form})


def register_customer(request):
    form = CustomerRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Account created successfully! Welcome aboard.')
        return redirect('customers:home')
    return render(request, 'accounts/register.html', {'form': form, 'role': 'Customer'})


def register_restaurant(request):
    form = RestaurantRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Restaurant account created! Please complete your profile.')
        return redirect('restaurants:setup')
    return render(request, 'accounts/register.html', {'form': form, 'role': 'Restaurant'})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


def _redirect_by_role(user):
    if user.is_superuser or user.role == 'admin':
        return redirect('/admin/')
    elif user.role == 'restaurant':
        return redirect('restaurants:dashboard')
    else:
        return redirect('customers:home')
