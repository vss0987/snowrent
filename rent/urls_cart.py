"""
================================================================================
URL-КОНФИГУРАЦИЯ КОРЗИНЫ ПОКУПОК (CART)
================================================================================

Данный файл содержит все маршруты, связанные с корзиной покупок.
"""

from django.urls import path
from .views import ViewCart, AddToCart, RemoveFromCart, UpdateCartItem

app_name = 'cart'

urlpatterns = [
    # Просмотр корзины
    path('', ViewCart.as_view(), name='view_cart'),

    # Добавление товара в корзину
    path('add/<slug:slug>/', AddToCart.as_view(), name='add_to_cart'),

    # Удаление товара из корзины
    path('remove/<int:item_id>/', RemoveFromCart.as_view(), name='remove_from_cart'),

    # Обновление количества товара
    path('update/<int:item_id>/', UpdateCartItem.as_view(), name='update_cart_item'),
]