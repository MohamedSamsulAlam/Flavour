from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from .models import Restaurant, MenuItem, Category
from .forms import RestaurantSetupForm, MenuItemForm, CategoryForm
from apps.orders.models import Order


def restaurant_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'restaurant':
            messages.error(request, 'Access denied. Restaurant accounts only.')
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@restaurant_required
def setup_restaurant(request):
    try:
        restaurant = request.user.restaurant
        return redirect('restaurants:dashboard')
    except Restaurant.DoesNotExist:
        pass

    form = RestaurantSetupForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        restaurant = form.save(commit=False)
        restaurant.owner = request.user
        restaurant.save()
        messages.success(request, 'Restaurant profile created successfully!')
        return redirect('restaurants:dashboard')
    return render(request, 'restaurants/setup.html', {'form': form})


@login_required
@restaurant_required
def dashboard(request):
    try:
        restaurant = request.user.restaurant
    except Restaurant.DoesNotExist:
        return redirect('restaurants:setup')

    orders = Order.objects.filter(restaurant=restaurant).order_by('-created_at')[:10]
    menu_items = MenuItem.objects.filter(restaurant=restaurant)
    low_stock_items = menu_items.filter(quantity__lte=10)

    stats = {
        'total_orders': Order.objects.filter(restaurant=restaurant).count(),
        'pending_orders': Order.objects.filter(restaurant=restaurant, status='pending').count(),
        'total_revenue': Order.objects.filter(restaurant=restaurant, status='delivered').aggregate(
            total=Sum('total_price'))['total'] or 0,
        'menu_items': menu_items.count(),
    }

    return render(request, 'restaurants/dashboard.html', {
        'restaurant': restaurant,
        'orders': orders,
        'low_stock_items': low_stock_items,
        'stats': stats,
    })


@login_required
@restaurant_required
def menu_list(request):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    categories = Category.objects.filter(restaurant=restaurant).prefetch_related('items')
    uncategorized = MenuItem.objects.filter(restaurant=restaurant, category=None)
    return render(request, 'restaurants/menu_list.html', {
        'restaurant': restaurant,
        'categories': categories,
        'uncategorized': uncategorized,
    })


@login_required
@restaurant_required
def menu_add(request):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    form = MenuItemForm(request.POST or None, request.FILES or None, restaurant=restaurant)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.restaurant = restaurant
        item.save()
        messages.success(request, f'"{item.name}" added to your menu!')
        return redirect('restaurants:menu')
    return render(request, 'restaurants/menu_form.html', {'form': form, 'action': 'Add'})


@login_required
@restaurant_required
def menu_edit(request, pk):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    item = get_object_or_404(MenuItem, pk=pk, restaurant=restaurant)
    form = MenuItemForm(request.POST or None, request.FILES or None, instance=item, restaurant=restaurant)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'"{item.name}" updated successfully!')
        return redirect('restaurants:menu')
    return render(request, 'restaurants/menu_form.html', {'form': form, 'action': 'Edit', 'item': item})


@login_required
@restaurant_required
def menu_delete(request, pk):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    item = get_object_or_404(MenuItem, pk=pk, restaurant=restaurant)
    if request.method == 'POST':
        name = item.name
        item.delete()
        messages.success(request, f'"{name}" removed from your menu.')
        return redirect('restaurants:menu')
    return render(request, 'restaurants/menu_confirm_delete.html', {'item': item})


@login_required
@restaurant_required
def orders_list(request):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    status_filter = request.GET.get('status', '')
    orders = Order.objects.filter(restaurant=restaurant).order_by('-created_at')
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, 'restaurants/orders.html', {
        'restaurant': restaurant,
        'orders': orders,
        'status_filter': status_filter,
    })


@login_required
@restaurant_required
def update_order_status(request, order_id):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid = ['pending', 'confirmed', 'preparing', 'ready', 'delivered', 'cancelled']
        if new_status in valid:
            order.status = new_status
            order.save()
            messages.success(request, f'Order #{order.id} status updated to {new_status}.')
    return redirect('restaurants:orders')


@login_required
@restaurant_required
def profile_edit(request):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    form = RestaurantSetupForm(request.POST or None, request.FILES or None, instance=restaurant)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Restaurant profile updated!')
        return redirect('restaurants:dashboard')
    return render(request, 'restaurants/setup.html', {'form': form, 'edit': True})
