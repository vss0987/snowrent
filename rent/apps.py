"""
Конфигурация приложения rent.

Определяет мета-информацию и настройки приложения.
"""

from django.apps import AppConfig


class RentConfig(AppConfig):
    """Конфигурация приложения rent."""
    verbose_name = 'Категории и товары'  # Исправлено с "Категрии"
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rent'