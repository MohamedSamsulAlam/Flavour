from django.shortcuts import render, get_object_or_404
from apps.restaurants.models import Restaurant, MenuItem
import json


def home(request):
    cuisine_filter = request.GET.get('cuisine', '')
    search = request.GET.get('q', '')
    restaurants = Restaurant.objects.filter(is_open=True).select_related('owner')
    if cuisine_filter:
        restaurants = restaurants.filter(cuisine=cuisine_filter)
    if search:
        restaurants = restaurants.filter(name__icontains=search)

    cuisine_choices = Restaurant.CUISINE_CHOICES
    featured = MenuItem.objects.filter(is_featured=True, is_available=True).select_related('restaurant')[:6]

    return render(request, 'customers/home.html', {
        'restaurants': restaurants,
        'cuisine_choices': cuisine_choices,
        'cuisine_filter': cuisine_filter,
        'search': search,
        'featured_items': featured,
    })


def restaurant_detail(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    categories = restaurant.categories.prefetch_related('items').all()
    uncategorized = MenuItem.objects.filter(restaurant=restaurant, category=None, is_available=True)
    return render(request, 'customers/restaurant_detail.html', {
        'restaurant': restaurant,
        'categories': categories,
        'uncategorized': uncategorized,
    })


def map_view(request):
    restaurants = Restaurant.objects.filter(is_open=True)
    map_data = []
    for r in restaurants:
        if r.latitude and r.longitude:
            map_data.append({
                'id': r.id,
                'name': r.name,
                'cuisine': r.get_cuisine_display(),
                'rating': float(r.rating),
                'delivery_time': r.delivery_time,
                'address': r.address,
                'lat': float(r.latitude),
                'lng': float(r.longitude),
                'url': f'/restaurant/{r.id}/',
            })
    return render(request, 'customers/map.html', {
        'restaurants': restaurants,
        'map_data_json': json.dumps(map_data),
    })
