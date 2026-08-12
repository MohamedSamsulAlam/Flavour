from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.restaurants.models import Restaurant, Category, MenuItem


class Command(BaseCommand):
    help = 'Seeds the database with demo data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('🌱 Seeding demo data...')

        # Admin
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@flavour.com', 'admin123', role='admin')
            self.stdout.write('  ✓ Admin: admin / admin123')

        # Restaurant owner
        r_user, created = User.objects.get_or_create(
            username='spicehouse',
            defaults={'email': 'spice@flavour.com', 'role': 'restaurant'}
        )
        r_user.set_password('demo1234')
        r_user.save()

        # Restaurant
        restaurant, _ = Restaurant.objects.get_or_create(
            owner=r_user,
            defaults={
                'name': 'The Spice House',
                'description': 'Authentic Indian cuisine with bold flavours and fresh ingredients.',
                'cuisine': 'indian',
                'address': '12 MG Road, Chennai, Tamil Nadu 600001',
                'phone': '+91 98765 43210',
                'delivery_time': 35,
                'minimum_order': 150,
                'is_open': True,
                'rating': 4.5,
                'latitude': 13.082680,
                'longitude': 80.270721,
            }
        )

        # Categories
        starters, _ = Category.objects.get_or_create(restaurant=restaurant, name='Starters',    defaults={'order': 1})
        mains, _    = Category.objects.get_or_create(restaurant=restaurant, name='Main Course', defaults={'order': 2})
        drinks, _   = Category.objects.get_or_create(restaurant=restaurant, name='Beverages',   defaults={'order': 3})

        # Menu items
        items = [
            dict(category=starters, name='Paneer Tikka',   description='Char-grilled cottage cheese with spices and peppers', price=199, is_vegetarian=True,  is_featured=True,  quantity=50),
            dict(category=starters, name='Chicken 65',     description='Deep-fried spicy chicken, South Indian style',        price=249, is_vegetarian=False, is_featured=True,  quantity=40),
            dict(category=starters, name='Onion Bhaji',    description='Crispy golden onion fritters with mint chutney',      price=129, is_vegetarian=True,  is_featured=False, quantity=60),
            dict(category=mains,    name='Butter Chicken', description='Creamy tomato-based curry with tender chicken pieces', price=329, is_vegetarian=False, is_featured=True,  quantity=30),
            dict(category=mains,    name='Dal Makhani',    description='Rich black lentils cooked overnight with cream',       price=229, is_vegetarian=True,  is_featured=False, quantity=45),
            dict(category=mains,    name='Chicken Biryani',description='Fragrant basmati rice with slow-cooked spiced chicken',price=349, is_vegetarian=False, is_featured=True,  quantity=25),
            dict(category=mains,    name='Palak Paneer',   description='Fresh spinach and cottage cheese curry',               price=249, is_vegetarian=True,  is_featured=False, quantity=35),
            dict(category=drinks,   name='Mango Lassi',    description='Sweet chilled yoghurt and mango drink',               price=99,  is_vegetarian=True,  is_featured=False, quantity=80),
            dict(category=drinks,   name='Masala Chai',    description='Spiced Indian milk tea with ginger and cardamom',     price=49,  is_vegetarian=True,  is_featured=False, quantity=100),
        ]

        for item_data in items:
            MenuItem.objects.get_or_create(
                restaurant=restaurant,
                name=item_data['name'],
                defaults=item_data
            )

        # Customer
        c_user, _ = User.objects.get_or_create(
            username='customer',
            defaults={'email': 'customer@flavour.com', 'role': 'customer'}
        )
        c_user.set_password('demo1234')
        c_user.save()

        self.stdout.write(self.style.SUCCESS('''
╔══════════════════════════════════════════════════╗
║         ✅  Demo Data Seeded Successfully!       ║
╠══════════════════════════════════════════════════╣
║  Admin:       admin / admin123                   ║
║               → http://127.0.0.1:8000/admin/    ║
║                                                  ║
║  Restaurant:  spicehouse / demo1234              ║
║               → /restaurants/dashboard/          ║
║                                                  ║
║  Customer:    customer / demo1234                ║
║               → http://127.0.0.1:8000/          ║
╚══════════════════════════════════════════════════╝
'''))
