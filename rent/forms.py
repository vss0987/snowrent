from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from rent.models import Order


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=False)  # Установите required=False для поля e-mail

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )


class OrderForm(forms.ModelForm):
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
