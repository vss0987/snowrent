"""
Сигналы для автоматического управления резервами товаров.

Обрабатывают события с CartItem:
- pre_save: валидация количества и доступности
- post_save: обновление reserved_quantity
- pre_delete: освобождение reserved_quantity
"""

from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from rent.models import CartItem


@receiver(pre_save, sender=CartItem)
def validate_cart_item(sender, instance, **kwargs):
    """Проверяет количество и наличие товара перед сохранением."""
    if instance.quantity < 0:
        raise ValueError("Количество не может быть отрицательным")

    if instance.pk:
        old_item = CartItem.objects.get(pk=instance.pk)
        additional = instance.quantity - old_item.quantity
    else:
        additional = instance.quantity

    available = instance.product.total_quantity - instance.product.reserved_quantity
    if additional > available:
        raise ValueError(f"Недостаточно товара. Доступно: {available}")


@receiver(post_save, sender=CartItem)
def update_reserved_on_save(sender, instance, created, **kwargs):
    """Обновляет резерв товара после сохранения позиции."""
    if created:
        instance.product.reserved_quantity += instance.quantity
    else:
        old_item = CartItem.objects.get(pk=instance.pk)
        diff = instance.quantity - old_item.quantity
        instance.product.reserved_quantity += diff

    instance.product.reserved_quantity = max(0, instance.product.reserved_quantity)
    instance.product.save()


@receiver(pre_delete, sender=CartItem)
def release_reserved_on_delete(sender, instance, **kwargs):
    """Освобождает резерв при удалении позиции."""
    instance.product.reserved_quantity = max(0, instance.product.reserved_quantity - instance.quantity)
    instance.product.save()