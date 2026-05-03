"""
Формы для валидации пользовательского ввода.

Формы:
- RegistrationForm: регистрация пользователя
- LoginForm: авторизация
- OrderForm: оформление заказа (только комментарий)
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from rent.models import Order


class RegistrationForm(UserCreationForm):
    """Регистрация нового пользователя. Email не обязателен."""
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class LoginForm(forms.Form):
    """Авторизация пользователя."""
    username = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )


class OrderForm(forms.ModelForm):
    """Оформление заказа (только комментарий)."""
    class Meta:
        model = Order
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Комментарий к заказу (необязательно)'
            }),
        }