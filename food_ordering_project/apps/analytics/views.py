from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDate, TruncMonth
from apps.restaurants.models import Restaurant, MenuItem
from apps.orders.models import Order
import json
from datetime import datetime, timedelta
from django.utils import timezone


def restaurant_required(view_func):
    from django.contrib import messages
    from django.shortcuts import redirect
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'restaurant':
            messages.error(request, 'Access denied.')
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@restaurant_required
def restaurant_analytics(request):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    
    # Date range
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    orders_qs = Order.objects.filter(
        restaurant=restaurant,
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    # Daily revenue
    daily_revenue = list(
        orders_qs.filter(status='delivered')
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(total=Sum('total_price'), count=Count('id'))
        .order_by('date')
    )
    
    # Order status distribution
    status_data = list(
        orders_qs.values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )
    
    # Top selling items
    from apps.orders.models import OrderItem
    top_items = list(
        OrderItem.objects.filter(order__restaurant=restaurant, order__created_at__gte=start_date)
        .values('item_name')
        .annotate(total_qty=Sum('quantity'), total_revenue=Sum('item_price'))
        .order_by('-total_qty')[:8]
    )
    
    # Monthly summary
    monthly = list(
        orders_qs.filter(status='delivered')
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total_price'), count=Count('id'))
        .order_by('month')
    )
    
    # Summary stats
    stats = {
        'total_orders': orders_qs.count(),
        'delivered_orders': orders_qs.filter(status='delivered').count(),
        'cancelled_orders': orders_qs.filter(status='cancelled').count(),
        'total_revenue': orders_qs.filter(status='delivered').aggregate(t=Sum('total_price'))['t'] or 0,
        'avg_order_value': orders_qs.filter(status='delivered').aggregate(a=Avg('total_price'))['a'] or 0,
    }
    
    # Serialize for JSON
    chart_data = {
        'daily_revenue': [
            {'date': str(d['date']), 'total': float(d['total']), 'count': d['count']}
            for d in daily_revenue
        ],
        'status_data': [
            {'status': s['status'], 'count': s['count']}
            for s in status_data
        ],
        'top_items': [
            {'name': i['item_name'], 'qty': i['total_qty'], 'revenue': float(i['total_revenue'] or 0)}
            for i in top_items
        ],
        'monthly': [
            {'month': str(m['month'])[:7], 'total': float(m['total']), 'count': m['count']}
            for m in monthly
        ],
    }

    return render(request, 'analytics/dashboard.html', {
        'restaurant': restaurant,
        'stats': stats,
        'chart_data': json.dumps(chart_data),
        'days': days,
    })
