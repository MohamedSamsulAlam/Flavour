from django import forms
from .models import Restaurant, MenuItem, Category


class RestaurantSetupForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'description', 'cuisine', 'address', 'phone', 'logo', 'cover_image',
                  'delivery_time', 'minimum_order', 'latitude', 'longitude']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'latitude': forms.NumberInput(attrs={'step': 'any', 'placeholder': 'e.g. 13.082680'}),
            'longitude': forms.NumberInput(attrs={'step': 'any', 'placeholder': 'e.g. 80.270721'}),
        }


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['name', 'category', 'description', 'price', 'image', 'quantity', 'low_stock_threshold', 'is_available', 'is_vegetarian', 'is_featured']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, restaurant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if restaurant:
            self.fields['category'].queryset = Category.objects.filter(restaurant=restaurant)
        self.fields['price'].widget.attrs['min'] = '0.01'
        self.fields['price'].widget.attrs['step'] = '0.01'

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price <= 0:
            raise forms.ValidationError('Price must be greater than zero.')
        return price


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'order']
