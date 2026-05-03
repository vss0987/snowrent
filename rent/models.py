"""
Модели данных для приложения rent.

Содержит модели для:
- Товаров и категорий (Product, Category)
- Корзины покупок (Cart, CartItem)
- Заказов (Order, OrderItem)
- Контактной информации (ContactInfo)
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone


class Category(models.Model):
    """Категория товаров (Лыжи, Сноуборды, Экипировка)."""

    name = models.CharField(max_length=255, db_index=True, verbose_name="Название")
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="Slug")
    is_available = models.BooleanField(default=True, db_index=True, verbose_name="Наличие категории")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'cat_slug': self.slug})

    def available_products_count(self):
        return self.products.filter(is_available=True).count()

    def get_models_count_text(self):
        """Возвращает строку с правильным склонением слова 'модель'."""
        count = self.products.filter(is_available=True).count()
        if count % 10 == 1 and count % 100 != 11:
            return f"{count} модель"
        elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
            return f"{count} модели"
        return f"{count} моделей"

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Product(models.Model):
    """Товар для аренды (лыжи, сноуборды, экипировка)."""

    name = models.CharField(max_length=255, verbose_name="Товар")
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT,
        related_name='products', verbose_name="Категория"
    )
    total_quantity = models.PositiveIntegerField(default=0, verbose_name="Общее количество")
    reserved_quantity = models.PositiveIntegerField(default=0, verbose_name="Зарезервировано")
    main_image = models.ImageField(
        upload_to="products/%Y/%m/%d/",
        blank=True, null=True,
        verbose_name="Главное изображение"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Добавлено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Редактировано")
    is_available = models.BooleanField(default=True, db_index=True, verbose_name="Наличие товара")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Защита от некорректных значений reserved_quantity
        self.reserved_quantity = min(self.reserved_quantity, self.total_quantity)
        self.reserved_quantity = max(0, self.reserved_quantity)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('rent:product_detail', kwargs={'slug': self.slug})

    def release_reserved(self, amount):
        """Освободить указанное количество из резерва."""
        self.reserved_quantity = max(0, self.reserved_quantity - amount)
        self.save()

    def reserve(self, amount):
        """Зарезервировать указанное количество."""
        self.reserved_quantity += amount
        self.save()

    @property
    def available_quantity(self):
        """Доступное количество (общее - зарезервированное)."""
        return max(0, self.total_quantity - self.reserved_quantity)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['-created_at']


class Cart(models.Model):
    """Корзина покупок пользователя (живет 15 минут)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    expires_at = models.DateTimeField(db_index=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Корзина {self.user.username} (до {self.expires_at})"

    def total_price(self):
        return sum(item.total_price() for item in self.items.all())

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"


class CartItem(models.Model):
    """Позиция в корзине (связь Cart и Product)."""

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name="Корзина")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveIntegerField(default=0, verbose_name="Количество")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Добавлено")

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def total_price(self):
        return self.product.price * self.quantity

    def save(self, *args, **kwargs):
        # Обновляем резерв товара
        if not self.pk:  # Новая позиция
            self.product.reserved_quantity += self.quantity
        else:  # Изменение количества
            old_item = CartItem.objects.get(pk=self.pk)
            diff = self.quantity - old_item.quantity
            self.product.reserved_quantity += diff

        self.product.reserved_quantity = max(0, self.product.reserved_quantity)
        self.product.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Освобождаем резерв при удалении
        self.product.reserved_quantity = max(0, self.product.reserved_quantity - self.quantity)
        self.product.save()
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "Элемент корзины"
        verbose_name_plural = "Элементы корзины"
        unique_together = ('cart', 'product')


@receiver(pre_delete, sender=Cart)
def release_reserved(sender, instance, **kwargs):
    """При удалении корзины освобождаем все резервы товаров."""
    for item in instance.items.all():
        item.product.reserved_quantity = max(0, item.product.reserved_quantity - item.quantity)
        item.product.save()


class ContactInfo(models.Model):
    """Контактная информация компании (одна запись)."""

    phone = models.CharField('Телефон', max_length=20)
    email = models.EmailField('Email')
    address = models.TextField('Адрес')
    work_hours = models.TextField('Часы работы')
    vk_link = models.URLField('VK', blank=True)
    telegram_link = models.URLField('Telegram', blank=True)
    whatsapp_link = models.URLField('WhatsApp', blank=True)
    map_embed_code = models.TextField('Код карты', help_text='HTML-код для вставки карты')

    class Meta:
        verbose_name = 'Контактная информация'
        verbose_name_plural = 'Контактная информация'

    def __str__(self):
        return 'Контактная информация'


class Order(models.Model):
    """Заказ пользователя."""

    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    comment = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.id}"


class OrderItem(models.Model):
    """Позиция в заказе (сохраняет цену на момент покупки)."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"