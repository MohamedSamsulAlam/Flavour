from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('restaurants/', include('apps.restaurants.urls', namespace='restaurants')),
    path('orders/', include('apps.orders.urls', namespace='orders')),
    path('analytics/', include('apps.analytics.urls', namespace='analytics')),
    path('', include('apps.customers.urls', namespace='customers')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
