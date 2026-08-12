from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from apps.restaurants.models import MenuItem, Restaurant
from .models import Order, OrderItem


def get_cart(request):
    return request.session.get('cart', {})


def save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


def add_to_cart(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id, is_available=True)
    cart = get_cart(request)
    key = str(item_id)

    if cart:
        first_item_id = next(iter(cart))
        first_item = MenuItem.objects.get(id=first_item_id)
        if first_item.restaurant_id != item.restaurant_id:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'clear_cart', 'message': 'Your cart has items from another restaurant. Clear it first?'})
            messages.warning(request, 'Your cart has items from another restaurant. Please clear your cart first.')
            return redirect('customers:restaurant_detail', pk=item.restaurant_id)

    if key in cart:
        cart[key]['quantity'] += 1
    else:
        cart[key] = {
            'name': item.name,
            'price': str(item.price),
            'quantity': 1,
            'restaurant_id': item.restaurant_id,
            'restaurant_name': item.restaurant.name,
        }
    save_cart(request, cart)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        count = sum(i['quantity'] for i in cart.values())
        return JsonResponse({'success': True, 'cart_count': count, 'item_name': item.name})

    messages.success(request, f'"{item.name}" added to cart.')
    return redirect('customers:restaurant_detail', pk=item.restaurant_id)


def remove_from_cart(request, item_id):
    cart = get_cart(request)
    key = str(item_id)
    if key in cart:
        del cart[key]
        save_cart(request, cart)
        messages.success(request, 'Item removed from cart.')
    return redirect('orders:cart')


def update_cart(request, item_id):
    cart = get_cart(request)
    key = str(item_id)
    qty = int(request.POST.get('quantity', 1))
    if key in cart:
        if qty <= 0:
            del cart[key]
        else:
            cart[key]['quantity'] = qty
        save_cart(request, cart)
    return redirect('orders:cart')


def cart_view(request):
    cart = get_cart(request)
    items = []
    total = 0
    restaurant_name = ''
    restaurant_id = None
    for item_id, data in cart.items():
        subtotal = float(data['price']) * data['quantity']
        total += subtotal
        items.append({
            'id': item_id,
            'name': data['name'],
            'price': float(data['price']),
            'quantity': data['quantity'],
            'subtotal': subtotal,
        })
        restaurant_name = data.get('restaurant_name', '')
        restaurant_id = data.get('restaurant_id')
    return render(request, 'orders/cart.html', {
        'cart_items': items,
        'total': total,
        'restaurant_name': restaurant_name,
        'restaurant_id': restaurant_id,
    })


def clear_cart(request):
    request.session['cart'] = {}
    request.session.modified = True
    messages.info(request, 'Cart cleared.')
    return redirect('orders:cart')


@login_required
def checkout(request):
    cart = get_cart(request)
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('customers:home')

    items = []
    total = 0
    restaurant_id = None
    for item_id, data in cart.items():
        subtotal = float(data['price']) * data['quantity']
        total += subtotal
        items.append({'id': item_id, 'name': data['name'], 'price': float(data['price']),
                      'quantity': data['quantity'], 'subtotal': subtotal})
        restaurant_id = data['restaurant_id']

    if request.method == 'POST':
        delivery_address = request.POST.get('delivery_address', '').strip()
        notes = request.POST.get('notes', '')
        if not delivery_address:
            messages.error(request, 'Please enter a delivery address.')
            return render(request, 'orders/checkout.html', {'cart_items': items, 'total': total})

        # Save pending order to session and redirect to payment
        request.session['pending_order'] = {
            'cart': dict(cart),
            'delivery_address': delivery_address,
            'notes': notes,
            'total': total,
            'restaurant_id': restaurant_id,
        }
        request.session.modified = True
        return redirect('orders:payment')

    return render(request, 'orders/checkout.html', {
        'cart_items': items,
        'total': total,
    })


@login_required
def payment_page(request):
    pending = request.session.get('pending_order')
    if not pending:
        messages.warning(request, 'No pending order found.')
        return redirect('orders:cart')

    cart = pending['cart']
    items = []
    for item_id, data in cart.items():
        subtotal = float(data['price']) * data['quantity']
        items.append({'id': item_id, 'name': data['name'], 'price': float(data['price']),
                      'quantity': data['quantity'], 'subtotal': subtotal})

    banks = [
        'SBI', 'HDFC', 'ICICI', 'Axis', 'Kotak', 'PNB', 'BOB',
        'Canara', 'IDBI', 'Yes Bank', 'Federal', 'IDFC'
    ]

    return render(request, 'orders/payment.html', {
        'cart_items': items,
        'total': pending['total'],
        'delivery_address': pending['delivery_address'],
        'banks': banks,
    })


@login_required
def process_payment(request):
    if request.method != 'POST':
        return redirect('orders:payment')

    pending = request.session.get('pending_order')
    if not pending:
        messages.error(request, 'Session expired. Please try again.')
        return redirect('orders:cart')

    cart = pending['cart']
    total = pending['total']
    restaurant_id = pending['restaurant_id']
    delivery_address = pending['delivery_address']
    notes = pending['notes']

    try:
        with transaction.atomic():
            restaurant = Restaurant.objects.get(id=restaurant_id)
            payment_method = request.POST.get('payment_method', 'cod')
            if payment_method not in dict(Order.PAYMENT_METHOD_CHOICES):
                payment_method = 'cod'

            order = Order.objects.create(
                customer=request.user,
                restaurant=restaurant,
                total_price=total,
                payment_method=payment_method,
                delivery_address=delivery_address,
                notes=notes,
            )
            for item_id, data in cart.items():
                menu_item = get_object_or_404(MenuItem, id=item_id)
                qty = data['quantity']
                if menu_item.quantity < qty:
                    raise ValueError(f'Not enough stock for "{menu_item.name}".')
                menu_item.quantity -= qty
                menu_item.save()
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    item_name=menu_item.name,
                    item_price=menu_item.price,
                    quantity=qty,
                )
        request.session['cart'] = {}
        del request.session['pending_order']
        request.session.modified = True

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'order_id': order.id})
        messages.success(request, f'Order #{order.id} placed successfully!')
        return redirect('orders:order_success', order_id=order.id)

    except ValueError as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=400)
        messages.error(request, str(e))
        return redirect('orders:cart')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Something went wrong. Please try again.'}, status=500)
        messages.error(request, 'Something went wrong. Please try again.')
        return redirect('orders:cart')


@login_required
def bulk_order(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, pk=restaurant_id, is_open=True)
    categories = restaurant.categories.prefetch_related('items').all()
    uncategorized = MenuItem.objects.filter(restaurant=restaurant, category=None, is_available=True)

    if request.method == 'POST':
        cart = get_cart(request)
        added_count = 0
        errors = []

        for key, value in request.POST.items():
            if key.startswith('qty_'):
                try:
                    item_id = int(key.replace('qty_', ''))
                    qty = int(value)
                    if qty <= 0:
                        continue
                    item = MenuItem.objects.get(id=item_id, restaurant=restaurant, is_available=True)

                    # Check cross-restaurant conflict
                    if cart:
                        first_item_id = next(iter(cart))
                        first_item = MenuItem.objects.get(id=first_item_id)
                        if first_item.restaurant_id != restaurant.id:
                            messages.warning(request, 'Your cart has items from another restaurant. Clear your cart first.')
                            return redirect('orders:bulk_order', restaurant_id=restaurant_id)

                    str_id = str(item_id)
                    if str_id in cart:
                        cart[str_id]['quantity'] += qty
                    else:
                        cart[str_id] = {
                            'name': item.name,
                            'price': str(item.price),
                            'quantity': qty,
                            'restaurant_id': item.restaurant_id,
                            'restaurant_name': item.restaurant.name,
                        }
                    added_count += 1
                except (ValueError, MenuItem.DoesNotExist):
                    continue

        if added_count > 0:
            save_cart(request, cart)
            messages.success(request, f'{added_count} item(s) added to your cart!')
            return redirect('orders:cart')
        else:
            messages.warning(request, 'Please select at least one item with quantity > 0.')

    return render(request, 'orders/bulk_order.html', {
        'restaurant': restaurant,
        'categories': categories,
        'uncategorized': uncategorized,
    })


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, 'orders/order_success.html', {'order': order})


@login_required
def order_tracking(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    steps = [
        ('pending',   'Order Received',   '📥', 'Your order has been placed and is awaiting confirmation.'),
        ('confirmed', 'Confirmed',         '✅', 'The restaurant has confirmed your order.'),
        ('preparing', 'Being Prepared',   '👨‍🍳', 'The kitchen is preparing your meal.'),
        ('ready',     'Ready for Pickup', '📦', 'Your order is packed and ready.'),
        ('delivered', 'Delivered',        '🎉', 'Enjoy your meal!'),
    ]
    status_order = ['pending', 'confirmed', 'preparing', 'ready', 'delivered']
    current_idx = status_order.index(order.status) if order.status in status_order else 0
    completed_steps = status_order[:current_idx]
    return render(request, 'orders/order_tracking.html', {
        'order': order,
        'steps': steps,
        'completed_steps': completed_steps,
    })


@login_required
def my_orders(request):
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'orders/my_orders.html', {'orders': orders})
