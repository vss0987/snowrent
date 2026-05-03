"""
Celery задачи для автоматизации рутинных операций.

Задачи:
- notify_cart_expiration: уведомление об истечении корзины (каждую минуту)
- clean_expired_carts: очистка просроченных корзин (каждые 5 минут)
"""

from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from .models import Cart


@shared_task
def notify_cart_expiration():
    """Уведомляет пользователей за 5 минут до истечения корзины."""
    soon_to_expire = Cart.objects.filter(
        expires_at__lte=timezone.now() + timedelta(minutes=5),
        expires_at__gt=timezone.now(),
        user__isnull=False
    ).select_related('user')

    for cart in soon_to_expire:
        cart.user.email_user(
            'Ваша корзина скоро будет очищена',
            'Товары в вашей корзине будут доступны другим покупателям через 15 минут',
            'noreply@yourstore.com'
        )


@shared_task
def clean_expired_carts():
    """Удаляет просроченные корзины и освобождает резервы."""
    expired_carts = Cart.objects.filter(expires_at__lte=timezone.now())
    count = expired_carts.count()
    expired_carts.delete()
    return f"Cleaned {count} expired carts"