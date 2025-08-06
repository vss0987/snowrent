from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cart/', include('rent.urls_cart')),
    path('', include('rent.urls')),
]
