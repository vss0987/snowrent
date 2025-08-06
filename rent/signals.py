from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver

from rent.models import CartItem


@receiver(pre_save, sender=CartItem)
def validate_cart_item(sender, instance, **kwargs):
    """Проверяем корректность данных перед сохранением"""
    if instance.quantity < 0:
        raise ValueError("Количество не может быть отрицательным")
    if instance.quantity > instance.product.total_quantity:
        raise ValueError("Количество не может превышать общий запас")

@receiver(post_save, sender=CartItem)
def update_reserved_on_save(sender, instance, created, **kwargs):
    """Обновляем резерв после сохранения"""
    if created:
        instance.product.reserved_quantity += instance.quantity
        instance.product.save()

@receiver(pre_delete, sender=CartItem)
def release_reserved_on_delete(sender, instance, **kwargs):
    """Освобождаем резерв перед удалением"""
    instance.product.reserved_quantity -= instance.quantity
    instance.product.save()