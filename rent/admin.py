"""
Административная панель для управления моделями приложения rent.

Зарегистрированные модели:
- Product: товары (с фильтрами, поиском, массовыми действиями)
- Category: категории
- ContactInfo: контакты
- Order: заказы (с inline-редактированием позиций)
"""

from django.contrib import admin
from .models import Product, Category, ContactInfo, OrderItem, Order


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Управление товарами."""
    list_display = ('name', 'price', 'category', 'is_available', 'created_at', 'description_info')
    list_display_links = ('name', 'description_info')
    list_filter = ('category', 'is_available')
    search_fields = ('name', 'description')
    ordering = ('created_at', 'name')
    list_editable = ('is_available', 'category')
    list_per_page = 5
    prepopulated_fields = {'slug': ('name',)}
    actions = ['set_available', 'set_unavailable']

    @admin.display(description='Краткое описание')
    def description_info(self, prod: Product):
        return prod.description[:120]

    @admin.action(description='Есть в наличии')
    def set_available(self, request, queryset):
        queryset.update(is_available=True)

    @admin.action(description='Нет в наличии')
    def set_unavailable(self, request, queryset):
        queryset.update(is_available=False)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Управление категориями."""
    list_display = ('name', 'slug', 'is_available')
    list_filter = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)
    actions = ['set_available', 'set_unavailable']

    @admin.action(description='Есть в наличии')
    def set_available(self, request, queryset):
        queryset.update(is_available=True)

    @admin.action(description='Нет в наличии')
    def set_unavailable(self, request, queryset):
        queryset.update(is_available=False)


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    """Контактная информация."""
    list_display = ['phone', 'email']


class OrderItemInline(admin.TabularInline):
    """Позиции заказа внутри формы заказа."""
    model = OrderItem
    raw_id_fields = ['product']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Управление заказами."""
    list_display = ['id', 'user', 'created_at', 'status', 'total_price']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'id']
    inlines = [OrderItemInline]