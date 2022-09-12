from django.views.generic import FormView, TemplateView, RedirectView
from django.urls import reverse
from django.shortcuts import redirect
from django.http import JsonResponse, Http404

from apps.configuration.models import Settings
from apps.commons.mixins import AjaxableResponseMixin, ContextPageMixin, AlertMixin
from apps.pages.models import Page
from apps.cart.models import Cart, CartItem
from apps.shop.models import Order
from .forms import CartQuantityProductForm, CartDeleteProductForm
from .models import get_cart
from ..catalog.models import Product
from ..catalog.templatetags.catalog import convert_price
from ..catalog.views import get_slider
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render
import random

class CartTemplateView(ContextPageMixin, AlertMixin, TemplateView):
    template_name = 'cart/cart.html'
    page = Page.TemplateChoice.CART

    def get_context_data(self, *args, **kwargs):
        context = super(CartTemplateView, self).get_context_data(*args, **kwargs)
        
        random_val = random.randint(0, 10)

        products_slider = cache.get("products-slider-{0}".format(random_val), False)

        if(not products_slider):
            context['slider'] = get_slider(products=Product.objects.active().filter(parent=None, image__gt=0).order_by('?'),
            **{
                'title': 'Вам может понадобиться',
                'btn': {
                    'text': 'Смотреть все',
                    'href': reverse('catalog'),
                },
                'request': self.request,
                'slidesToShow': 4,
            })
            cache.set("products-slider-{0}".format(random_val), context['slider'])
        else:
            context['slider'] = products_slider

        empty_template = cache.get("empty_cart", False)

        if(not empty_template):
            context['empty'] = self.get_empty_cart()
            cache.set("empty_cart", context['empty'])
        else:
            context['empty'] = empty_template

        context['domain_discount'] = Settings.objects.all().order_by('id').first().discount_domain.all()
        return context


class CartActionMixin:
    action = "add"
    extra_response_data = {}

    def form_valid(self, form):
        # получаем объект корзины
        self.cart = get_cart(self.request)
        # выполняем нужное действие
        getattr(self.cart, self.action)(**form.cleaned_data)
        # добавляем данные, которые попадут в ответ
        self.extra_response_data = self.get_cart_data()
        return super().form_valid(form)

    def get_cart_data(self):
        cart_data = {
            'count': self.cart.count,
        }
        return cart_data

    def get(self, *args, **kwargs):
        raise Http404

class AddCartFormView(CartActionMixin, AjaxableResponseMixin, FormView):
    """
    Добавление товара в корзину
    """

    action = "add"
    form_class = CartQuantityProductForm
    message_success = "Товар успешно добавлен в корзину"


class UpdateCartFormView(CartActionMixin, AjaxableResponseMixin, FormView):
    """
    Изменение количества товара в корзине
    """

    action = "update"
    form_class = CartQuantityProductForm
    message_success = "Количество товара корзины успешно обновлено"

    def get_cart_data(self):
        context = super(UpdateCartFormView, self).get_cart_data()
        product = self.request.POST.get('product')
        item = self.cart.get(option=self.request.domain, product=product)
        context['item_total'] = convert_price(item.total)

        context['total'] = convert_price(self.cart.total)
        context['discount'] = convert_price(self.cart.discount_total)
        context['withoutDiscount'] = convert_price(self.cart.total_without_discount)
        return context


class DeleteCartFormView(CartActionMixin, AjaxableResponseMixin, FormView):
    """
    Удаление товара из корзины
    """

    action = "remove"
    form_class = CartDeleteProductForm
    message_success = "Элемент корзины успешно удален"

    def get_cart_data(self):
        context = super(DeleteCartFormView, self).get_cart_data()
        context['total'] = convert_price(self.cart.total)
        context['discount'] = convert_price(self.cart.discount_total)
        context['withoutDiscount'] = convert_price(self.cart.total_without_discount)
        return context


# def repeat_cart(request):
#     print(f'=====REQUEST {request.__dict__}')
#     return redirect(f"{request.domain.domain}/{reverse('cart_detail')}")


def repeat_cart(request, order_number):
    try:
        user_cart = Cart.objects.get(user=request.user)
        repeat_order = Order.objects.get(id=order_number)
        for order_item in repeat_order.items.iterator():
            existsCartItem = user_cart.items().filter(product=order_item.product, option=order_item.domain, cart=user_cart).first()

            if(existsCartItem):
                existsCartItem.quantity += order_item.quantity
                existsCartItem.save()
            else:
                CartItem(
                    cart=user_cart,
                    product=order_item.product,
                    quantity=order_item.quantity,
                    option=order_item.domain
                ).save()

        message = 'В корзине'
    except Exception as ex:
        print(f'=====CART REPEAT EXCEPTION {ex}')
        message = 'Ошибка'
    return JsonResponse({
        'message': message
    })
