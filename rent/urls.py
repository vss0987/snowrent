"""
URL-конфигурация приложения rent.

Содержит все маршруты для основного приложения:
- Публичные страницы (главная, каталог, контакты)
- Страницы категорий (лыжи, сноуборды, экипировка)
- Аутентификация (регистрация, вход, выход)
- Оформление заказов
- Вспомогательные страницы

Пространство имен: 'rent'
"""

from django.conf.urls.static import static
from django.urls import path

from forrent import settings
from .views import (
    HomeView,
    SportRentView,
    RegisterView,
    ProductDetailView,
    LoginView,
    LogoutView,
    TestView,
    SkiView,
    SnowboardView,
    EquipmentView,
    ContactsView,
    OrderCreateView,
    OrderSuccessView,
    PageNotFound,
)

app_name = 'rent'

urlpatterns = [
    # Главная страница (доступна по двум URL)
    path('', HomeView.as_view(), name='home'),
    path('home/', HomeView.as_view(), name='home'),

    # Каталог товаров
    path('products/', SportRentView.as_view(), name='products'),

    # Аутентификация
    path('registration/', RegisterView.as_view(), name='registration'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Детальная страница товара
    path('rent/<slug:slug>/', ProductDetailView.as_view(), name='show_product'),

    # Страницы категорий
    path('skis/', SkiView.as_view(), name='skis'),
    path('snowboards/', SnowboardView.as_view(), name='snowboards'),
    path('equipment/', EquipmentView.as_view(), name='equipment'),

    # Контакты
    path('contacts/', ContactsView.as_view(), name='contacts'),

    # Оформление заказов
    path('order/create/', OrderCreateView.as_view(), name='order_create'),
    path('order/success/', OrderSuccessView.as_view(), name='order_success'),

    # Вспомогательные страницы
    path('test-page/', TestView.as_view(), name='test_view'),
    path('pnf/', PageNotFound.as_view(), name='pnf'),
]

# Раздача медиа-файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)