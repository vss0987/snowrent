"""
Представления (views) для приложения rent.

Содержит контроллеры для обработки запросов:
- Главная страница и каталог
- Аутентификация (регистрация, вход, выход)
- Корзина покупок
- Оформление заказов
- Контакты и категории
"""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q, Prefetch
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, TemplateView

from rent.models import Product, Category, CartItem, Cart, Order, OrderItem
from .forms import RegistrationForm, LoginForm, OrderForm
from .models import ContactInfo


# ============================================================
# БАЗОВЫЕ КЛАССЫ
# ============================================================

class BaseView:
    """Базовый миксин для работы с редиректами."""

    redirect_url = 'rent:home'

    def get_redirect_url(self, request):
        return request.POST.get('next', request.GET.get('next', self.redirect_url))

    def redirect_authenticated_user(self, request):
        if request.user.is_authenticated:
            return redirect(self.get_redirect_url(request))
        return None


class CartView(View):
    """Базовый класс для всех представлений корзины (требует авторизации)."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('rent:login')
        return super().dispatch(request, *args, **kwargs)

    def get_cart(self, user):
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart


# ============================================================
# ОСНОВНЫЕ СТРАНИЦЫ
# ============================================================

class HomeView(View):
    """Главная страница с 3 случайными товарами."""

    def get(self, request):
        popular_products = Product.objects.filter(is_available=True).order_by('?')[:3]
        return render(request, 'rent/index.html', {'popular_products': popular_products})


class SportRentView(View):
    """Каталог товаров с группировкой по категориям."""

    def get(self, request):
        categories = Category.objects.prefetch_related(
            Prefetch('products',
                     queryset=Product.objects.filter(is_available=True).order_by('price'),
                     to_attr='cheapest_products')
        ).all()
        return render(request, 'rent/products.html', {'categories': categories})


class ProductDetailView(View):
    """Детальная страница товара."""

    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_available=True)
        related_products = Product.objects.filter(
            category=product.category, is_available=True
        ).exclude(id=product.id)
        return render(request, 'rent/show_product.html', {
            'product': product,
            'related_products': related_products
        })


# ============================================================
# КАТЕГОРИИ
# ============================================================

class SkiView(View):
    """Страница категории 'Лыжи'."""

    def get(self, request):
        products = Product.objects.filter(category__slug='skis')
        category = Category.objects.get(slug='skis')
        return render(request, 'rent/category.html', {'products': products, 'category': category})


class SnowboardView(View):
    """Страница категории 'Сноуборды'."""

    def get(self, request):
        products = Product.objects.filter(category__slug='snowboards')
        category = Category.objects.get(slug='snowboards')
        return render(request, 'rent/category.html', {'products': products, 'category': category})


class EquipmentView(View):
    """Страница категории 'Экипировка' (объединяет несколько подкатегорий)."""

    def get(self, request):
        equipment_slugs = ['equipment', 'snowboard-goggles', 'ski-goggles', 'ski-poles',
                           'snowboard-helmets', 'ski-helmets', 'snowboard-bindings',
                           'ski-bindings', 'ski-snowboard-backpacks']
        products = Product.objects.filter(category__slug__in=equipment_slugs, is_available=True)
        category = Category.objects.filter(slug='equipment').first()
        if not category:
            category = Category(name='Экипировка', slug='equipment')
        return render(request, 'rent/category.html', {'products': products, 'category': category})


# ============================================================
# АУТЕНТИФИКАЦИЯ
# ============================================================

class RegisterView(CreateView):
    """Регистрация нового пользователя."""

    form_class = RegistrationForm
    template_name = 'rent/register.html'
    success_url = reverse_lazy('rent:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = authenticate(self.request,
                           username=form.cleaned_data['username'],
                           password=form.cleaned_data['password1'])
        if user:
            login(self.request, user)
        return response


class LoginView(View, BaseView):
    """Вход пользователя в систему."""

    form_class = LoginForm
    template_name = 'rent/login.html'

    def get(self, request):
        redirect_response = self.redirect_authenticated_user(request)
        if redirect_response:
            return redirect_response
        return render(request, self.template_name, {
            'form': self.form_class(),
            'next': self.get_redirect_url(request)
        })

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = authenticate(request,
                               username=form.cleaned_data['username'],
                               password=form.cleaned_data['password'])
            if user:
                login(request, user)
                return redirect(self.get_redirect_url(request))
            form.add_error(None, "Неверное имя пользователя или пароль.")
        return render(request, self.template_name, {'form': form, 'next': self.get_redirect_url(request)})


class LogoutView(View, BaseView):
    """Выход пользователя из системы."""

    def get(self, request):
        logout(request)
        return redirect(self.redirect_url)


# ============================================================
# КОРЗИНА
# ============================================================

class ViewCart(CartView):
    """Просмотр корзины."""

    def get(self, request):
        cart = self.get_cart(request.user)
        return render(request, 'rent/view_cart.html', {'cart': cart})


class AddToCart(View):
    """Добавление товара в корзину."""

    def post(self, request, slug):
        if not request.user.is_authenticated:
            messages.warning(request, "Войдите в систему")
            return redirect('rent:login')

        product = get_object_or_404(Product, slug=slug, is_available=True)
        cart, _ = Cart.objects.get_or_create(user=request.user, defaults={'expires_at': timezone.now() + timedelta(minutes=15)})
        cart.expires_at = timezone.now() + timedelta(minutes=15)
        cart.save()

        if product.available_quantity <= 0:
            messages.error(request, f"Товар '{product.name}' отсутствует")
            return redirect('rent:products')

        cart_item, _ = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': 0})
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f"{product.name} добавлен в корзину")
        return redirect('cart:view_cart')


class RemoveFromCart(View):
    """Удаление товара из корзины."""

    def post(self, request, item_id):
        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            product_name = cart_item.product.name
            cart_item.delete()
            messages.success(request, f"{product_name} удален")
        except Exception as e:
            messages.error(request, f"Ошибка: {str(e)}")
        return redirect('cart:view_cart')


class UpdateCartItem(View):
    """Обновление количества товара в корзине."""

    def post(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        product = cart_item.product

        try:
            new_quantity = int(request.POST.get('quantity', 0))
            if new_quantity < 0:
                messages.error(request, "Количество не может быть отрицательным")
                return redirect('cart:view_cart')
        except ValueError:
            messages.error(request, "Некорректное значение")
            return redirect('cart:view_cart')

        with transaction.atomic():
            if new_quantity == 0:
                cart_item.delete()
                messages.success(request, f"{product.name} удален")
            else:
                available = product.total_quantity - product.reserved_quantity + cart_item.quantity
                if new_quantity <= available:
                    cart_item.quantity = new_quantity
                    cart_item.save()
                    messages.success(request, f"Количество обновлено до {new_quantity}")
                else:
                    messages.error(request, f"Доступно только {available} шт.")
        return redirect('cart:view_cart')


# ============================================================
# ЗАКАЗЫ
# ============================================================

class OrderCreateView(LoginRequiredMixin, CreateView):
    """Оформление заказа из товаров корзины."""

    model = Order
    form_class = OrderForm
    template_name = 'rent/order_create.html'
    success_url = reverse_lazy('rent:order_success')

    def dispatch(self, request, *args, **kwargs):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        if not cart.items.exists():
            messages.warning(request, "Корзина пуста")
            return redirect('cart:view_cart')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        with transaction.atomic():
            cart = Cart.objects.get(user=self.request.user)
            if not cart.items.exists():
                return redirect('cart:view_cart')

            form.instance.user = self.request.user
            form.instance.total_price = cart.total_price()
            response = super().form_valid(form)

            for item in cart.items.all():
                OrderItem.objects.create(
                    order=self.object,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
                item.product.total_quantity -= item.quantity
                item.product.reserved_quantity = max(0, item.product.reserved_quantity - item.quantity)
                item.product.save()

            cart.items.all().delete()
            messages.success(self.request, f"Заказ #{self.object.id} оформлен!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'], _ = Cart.objects.get_or_create(user=self.request.user)
        return context


class OrderSuccessView(TemplateView):
    """Страница успешного оформления заказа."""
    template_name = 'rent/order_success.html'


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ СТРАНИЦЫ
# ============================================================

class ContactsView(View):
    """Страница контактов."""

    def get(self, request):
        try:
            info = ContactInfo.objects.first()
            context = {
                'phone': info.phone,
                'email': info.email,
                'address': info.address,
                'work_hours': info.work_hours,
                'social_links': {'vk': info.vk_link, 'telegram': info.telegram_link, 'whatsapp': info.whatsapp_link},
                'map_embed': info.map_embed_code
            }
        except (AttributeError, ContactInfo.DoesNotExist):
            context = {
                'phone': '+7 (123) 456-78-90',
                'email': 'info@snowrent.ru',
                'address': 'г. Горнолыжск, ул. Снежная, 15',
                'work_hours': 'Пн-Пт: 9:00-21:00, Сб-Вс: 10:00-20:00',
                'social_links': {'vk': '#', 'telegram': '#', 'whatsapp': '#'},
                'map_embed': '<iframe src="https://yandex.ru/map-widget/"></iframe>'
            }
        return render(request, 'rent/contacts.html', context)


class TestView(View):
    """Тестовая страница для разработки."""

    def get(self, request):
        return render(request, 'rent/test-page.html')


class PageNotFound(View):
    """Страница 404."""

    def get(self, request):
        return render(request, 'rent/page_not_found.html')