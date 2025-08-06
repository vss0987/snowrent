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
    path('', HomeView.as_view(), name='home'),
    path('home/', HomeView.as_view(), name='home'),
    path('products/', SportRentView.as_view(), name='products'),
    path('registration/', RegisterView.as_view(), name='registration'),
    path('rent/<slug:slug>/', ProductDetailView.as_view(), name='show_product'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('test-page/', TestView.as_view(), name='test_view'),
    path('skis/', SkiView.as_view(), name='skis'),
    path('snowboards/', SnowboardView.as_view(), name='snowboards'),
    path('equipment/', EquipmentView.as_view(), name='equipment'),
    path('contacts/', ContactsView.as_view(), name='contacts'),
    path('order/create/', OrderCreateView.as_view(), name='order_create'),
    path('order/success/', OrderSuccessView.as_view(), name='order_success'),
    path('pnf/', PageNotFound.as_view(), name='pnf'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
