import json
import time
from pathlib import Path

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from apps.restaurants.models import Restaurant, MenuItem
import json

DEBUG_LOG_PATH = Path(settings.BASE_DIR).parent / 'debug-2ac106.log'


def _debug_log(location, message, data, hypothesis_id):
    payload = {
        'sessionId': '2ac106',
        'runId': 'home-view',
        'hypothesisId': hypothesis_id,
        'location': location,
        'message': message,
        'data': data,
        'timestamp': int(time.time() * 1000),
    }
    # #region agent log
    try:
        with DEBUG_LOG_PATH.open('a', encoding='utf-8') as log_file:
            log_file.write(json.dumps(payload) + '\n')
    except OSError:
        pass
    # #endregion


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

    image_samples = []
    for item in featured[:3]:
        if item.image:
            image_samples.append({
                'item_id': item.pk,
                'db_path': item.image.name,
                'url': item.image.url,
            })
    # #region agent log
    _debug_log(
        'customers/views.py:home',
        'Home page image URL samples',
        {
            'storage_backend': settings.STORAGES['default']['BACKEND'],
            'media_url': settings.MEDIA_URL,
            'image_samples': image_samples,
        },
        'B',
    )
    # #endregion

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
