from django.urls import path

from .views import ViewCart, AddToCart, RemoveFromCart, UpdateCartItem

app_name = 'cart'

urlpatterns = [
    path('', ViewCart.as_view(), name='view_cart'),
    path('add/<slug:slug>/', AddToCart.as_view(), name='add_to_cart'),
    path('remove/<int:item_id>/', RemoveFromCart.as_view(), name='remove_from_cart'),
    path('update/<int:item_id>/', UpdateCartItem.as_view(), name='update_cart_item'),
]
