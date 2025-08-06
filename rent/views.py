from datetime import timedelta
from urllib import request

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q, Prefetch
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, TemplateView

from rent.models import Product, Category, CartItem, Cart, Order, OrderItem
from .forms import RegistrationForm, LoginForm, OrderForm
from .models import ContactInfo


class BaseView:
    """Базовый класс для представлений с общими методами"""
    template_name = None
    redirect_url = 'rent:home'

    def get_redirect_url(self, request):
        """Получает URL для перенаправления из параметра 'next'"""
        return request.POST.get('next', request.GET.get('next', self.redirect_url))

    def redirect_authenticated_user(self, request):
        """Перенаправляет авторизованного пользователя"""
        if request.user.is_authenticated:
            return redirect(self.get_redirect_url(request))
        return None


class HomeView(View):
    """Представление для домашней страницы"""

    def get(self, request):
        # Получаем 3 случайных доступных товара
        popular_products = Product.objects.filter(is_available=True).order_by('?')[:3]
        return render(request,
                      template_name='rent/index.html',
                      context={
                          'popular_products': popular_products
                      })


class RegisterView(CreateView):
    """Представление для регистрации пользователя"""
    form_class = RegistrationForm
    template_name = 'rent/register.html'
    success_url = reverse_lazy('rent:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password1")
        user = authenticate(
            self.request,
            username=username,
            password=password,
        )
        if user:
            login(self.request, user)
        return response


class ProductService:
    """Сервис для работы с продуктами"""

    @staticmethod
    def get_cheapest_product(name_part):
        """Возвращает самый дешевый товар по названию или списку названий"""
        if isinstance(name_part, list):
            name_variants = name_part
        else:
            name_variants = [name_part, name_part.lower(), name_part.capitalize()]

        query = Q()
        for variant in name_variants:
            query |= Q(name__icontains=variant)

        return (
            Product.objects
            .filter(query, is_available=True)
            .order_by('price')
            .first()
        )


class SportRentView(View):
    """Представление для аренды спортивного инвентаря"""

    def get(self, request):
        categories = Category.objects.prefetch_related(
            Prefetch('products',
                     queryset=Product.objects.filter(is_available=True).order_by('price'),
                     to_attr='cheapest_products')
        ).all()

        return render(request,
                      template_name='rent/products.html',
                      context={
                          'categories': categories,
                      })


class ProductDetailView(View):
    """Представление для детальной страницы продукта"""

    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_available=True)

        related_products = Product.objects.filter(
            category=product.category,
            is_available=True
        ).exclude(id=product.id)

        return render(request,
                      template_name='rent/show_product.html',
                      context={
                          'product': product,
                          'related_products': related_products
                      })


class LoginView(View, BaseView):
    """Представление для входа пользователя"""
    form_class = LoginForm
    template_name = 'rent/login.html'

    def get(self, request):
        redirect_response = self.redirect_authenticated_user(request)
        if redirect_response:
            return redirect_response

        form = self.form_class()
        return render(request, self.template_name,
                      context={
                          'form': form,
                          'next': self.get_redirect_url(request)
                      })

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect(self.get_redirect_url(request))
            else:
                form.add_error(field=None, error="Неверное имя пользователя или пароль.")

        return render(request, self.template_name, {
            'form': form,
            'next': self.get_redirect_url(request)
        })


class LogoutView(View, BaseView):
    """Представление для выхода пользователя"""

    def get(self, request):
        logout(request)
        return redirect(self.redirect_url)


class TestView(View):
    """Тестовое представление"""

    def get(self, request):
        return render(request, template_name='rent/test-page.html')


class CartView(View):
    """Класс для работы с корзиной"""

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_cart(self, user):
        """Получение или создание корзины пользователя"""
        cart, created = Cart.objects.get_or_create(user=user)
        return cart


class ViewCart(CartView):
    """Просмотр содержимого корзины"""

    def get(self, request):
        cart = self.get_cart(request.user)
        return render(request,
                      template_name='rent/view_cart.html',
                      context={
                          'cart': cart
                      })


class AddToCart(View):
    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        cart, created = Cart.objects.get_or_create(
            user=request.user,
            defaults={'expires_at': timezone.now() + timedelta(minutes=15)}
        )

        if not created:
            cart.expires_at = timezone.now() + timedelta(minutes=15)
            cart.save()

        if product.available_quantity == 0:
            messages.error(request, message="Товар временно отсутствует")
            return redirect('rent:products')

        cart, _ = Cart.objects.get_or_create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 0}
        )

        if product.available_quantity > 0:
            cart_item.quantity += 1
            product.reserved_quantity += 1
            cart_item.save()
            product.save()
            messages.success(request, message=f"{product.name} добавлен в корзину")
        else:
            messages.warning(request, message="Достигнуто максимальное количество")

        return redirect('cart:view_cart')


class RemoveFromCart(View):
    def post(self, request, item_id):
        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            product = cart_item.product
            product.reserved_quantity -= cart_item.quantity  # Освобождаем резерв
            product.save()
            cart_item.delete()
            messages.success(request, message=f"{product.name} удален из корзины")
        except Exception as e:
            messages.error(request, message=f"Ошибка при удалении: {str(e)}")
        return redirect('cart:view_cart')


class UpdateCartItem(View):
    def post(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        product = cart_item.product  # Получаем продукт сразу
        new_quantity = int(request.POST.get('quantity', 0))

        with transaction.atomic():
            if new_quantity <= 0:
                # Удаляем товар
                product.reserved_quantity -= cart_item.quantity
                product.reserved_quantity = max(0, product.reserved_quantity)
                product.save()
                cart_item.delete()
                messages.success(request, message=f"{product.name} удален из корзины")
            else:
                # Проверяем доступное количество
                available = product.total_quantity - product.reserved_quantity + cart_item.quantity
                if new_quantity <= available:
                    diff = new_quantity - cart_item.quantity
                    product.reserved_quantity += diff
                    product.reserved_quantity = max(0, product.reserved_quantity)
                    cart_item.quantity = new_quantity
                    product.save()
                    cart_item.save()
                    messages.success(request, message="Количество обновлено")
                else:
                    messages.error(request, message=f"Недостаточно товара в наличии. Доступно: {available}")

        return redirect('cart:view_cart')


class SkiView(View):
    def get(self, request):
        ski_products = Product.objects.filter(category__slug='skis')
        cat = Category.objects.get(slug='skis')
        return render(request,
                      template_name='rent/category.html',
                      context={
                          'products': ski_products,
                          'category': cat
                      })


class SnowboardView(View):
    def get(self, request):
        snowboards_products = Product.objects.filter(category__slug='snowboards')
        cat = Category.objects.get(slug='snowboards')
        return render(request,
                      template_name='rent/category.html',
                      context={
                          'products': snowboards_products,
                          'category': cat
                      })


class EquipmentView(View):
    def get(self, request):
        cat = Category.objects.get(slug='equipment')
        equipment_products = Product.objects.filter(
            Q(category__slug='equipment') |
            Q(category__slug='snowboard-goggles') |
            Q(category__slug='ski-goggles') |
            Q(category__slug='ski-poles') |
            Q(category__slug='snowboard-helmets') |
            Q(category__slug='ski-helmets') |
            Q(category__slug='snowboard-bindings') |
            Q(category__slug='ski-bindings') |
            Q(category__slug='ski-snowboard-backpacks'),
        )

        return render(request,
                      template_name='rent/category.html',
                      context={
                          'products': equipment_products,
                          'category': cat
                      })


class ContactsView(View):
    def get(self, request):
        try:
            contact_info = ContactInfo.objects.first()
            context = {
                'phone': contact_info.phone,
                'email': contact_info.email,
                'address': contact_info.address,
                'work_hours': contact_info.work_hours,
                'social_links': {
                    'vk': contact_info.vk_link,
                    'telegram': contact_info.telegram_link,
                    'whatsapp': contact_info.whatsapp_link
                },
                'map_embed': contact_info.map_embed_code
            }
        except:
            # Запасные значения, если модель не настроена
            context = {
                'phone': '+7 (123) 456-78-90',
                'email': 'info@snowrent.ru',
                'address': 'г. Горнолыжск, ул. Снежная, 15',
                'work_hours': 'Пн-Пт: 9:00-21:00, Сб-Вс: 10:00-20:00',
                'social_links': {
                    'vk': 'https://vk.com/snowrent',
                    'telegram': 'https://t.me/snowrent',
                    'whatsapp': 'https://wa.me/snowrent'
                },
                'map_embed': '<iframe src="https://yandex.ru/map-widget/v1/?um=constructor%3A1a2b3c4d5e6f7g8h9i0j&amp;source=constructor" frameborder="0"></iframe>'
            }

        return render(request,
                      template_name='rent/contacts.html',
                      context=context
                      )


class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'rent/order_create.html'
    success_url = reverse_lazy('rent:order_success')

    def form_valid(self, form):
        cart = Cart.objects.get(user=self.request.user)
        form.instance.user = self.request.user
        form.instance.total_price = cart.total_price()
        response = super().form_valid(form)

        # Переносим товары из корзины в заказ
        for item in cart.items.all():
            OrderItem.objects.create(
                order=self.object,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            # Уменьшаем количество товара
            item.product.total_quantity -= item.quantity
            item.product.save()

        # Очищаем корзину
        cart.items.all().delete()

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = Cart.objects.get(user=self.request.user)
        return context

    def dispatch(self, request, *args, **kwargs):
        cart = Cart.objects.get(user=request.user)
        if not cart.items.exists():
            return redirect('cart:view_cart')
        return super().dispatch(request, *args, **kwargs)


class OrderSuccessView(TemplateView):
    template_name = 'rent/order_success.html'


class PageNotFound(View):
    def get(self, request):
        return render(request, 'rent/page_not_found.html')