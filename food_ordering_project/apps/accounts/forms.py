from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class CustomerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'customer'
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
        return user


class RestaurantRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'restaurant'
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
        return user


class CustomAuthForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username', 'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


class OTPForm(forms.Form):
    otp_token = forms.CharField(
        max_length=6,
        label='Enter 6-digit OTP',
        widget=forms.TextInput(attrs={'placeholder': '000000', 'maxlength': '6', 'autocomplete': 'one-time-code'})
    )
