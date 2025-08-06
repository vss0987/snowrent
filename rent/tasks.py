from datetime import timedelta

from celery import shared_task
from django.utils import timezone
from .models import Cart


@shared_task
def notify_cart_expiration():
    """Уведомляет пользователей об истечении срока корзины"""
    soon_to_expire = Cart.objects.filter(
        expires_at__lte=timezone.now() + timedelta(minutes=5),
        expires_at__gt=timezone.now(),
        user__isnull=False
    ).select_related('user')

    for cart in soon_to_expire:
        cart.user.email_user(
            'Ваша корзина скоро будет очищена',
            f'Товары в вашей корзине будут доступны другим покупателям через 30 минут',
            'noreply@yourstore.com'
        )