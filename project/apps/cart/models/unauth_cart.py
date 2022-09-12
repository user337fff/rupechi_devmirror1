from apps.catalog.models import Product
from django.utils.functional import cached_property

from .cart import check_quantity
from .interface import CartInterface, CartItemInterface
from ...domains.middleware import get_request
from ...configuration.models import Settings
from apps.catalog.models import Catalog

CART_SESSION_ID = 'cart'


class UnauthCart(CartInterface):
    """
    Корзина неавторизованного пользователя
    Предсталяет из себя словарь в сесии пользователя,
    где в качестве ключей используются ид товаров,
    либо составной из ид товара и ид опции

    !!! ВАЖНО !!!
    Не прописана логика для опций в методе items
    """

    ID_SEPARATOR = '|'

    _items = None

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)
        if cart is None:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart = cart

    def encode_id(self, product, domain=None):
        if domain:
            item_id = f"{product.id}{self.ID_SEPARATOR}{domain}"
        else:
            item_id = str(product.id)
        return item_id

    def decode_id(self, item_id):
        if self.ID_SEPARATOR in item_id:
            product_id, option_id = item_id.split(self.ID_SEPARATOR)
        else:
            product_id, option_id = item_id, None

        return product_id, option_id

    @property
    def count(self):
        """
        Подсчет всех товаров в корзине.
        """
        return sum(item['quantity'] for item in self.cart.values())

    # @property
    # def discount(self):
    #     category_discount = set(Catalog.objects.filter(discount_category__isnull=False))
    #     category_parent_discount = set(self.category.get_ancestors(include_self=True))
    #     domain_discount = Settings.objects.all().order_by('id').first().discount_domain.all()
    #     discount = Settings.get_discount() if get_request().domain in domain_discount and\
    #                                           not category_discount & category_parent_discount\
    #                                           else decimal.Decimal(0)
    #     return discount

    @property
    def discount(self):
        domain_discount = Settings.objects.all().order_by('id').first().discount_domain.all()
        discount = Settings.get_discount() if get_request().domain in domain_discount\
                                              else decimal.Decimal(0)
        return discount

    def items(self):
        """
        Получение элементов корзины
        """
        domain = get_request().domain
        if self._items is None:
            product_ids = [self.decode_id(item_id)[0] for item_id in self.cart.keys()]

            products = Product.objects.filter(id__in=product_ids, domain__exact=domain)
            self._items = []
            for product in products:
                item_id = self.encode_id(product, domain)
                item = self.cart.get(item_id)
                if item:
                    self._items.append(UnauthCartItem(product, self.cart[item_id]['quantity'], domain))
        return self._items

    @property
    def total(self):
        return sum(item.total for item in self.items())

    @cached_property
    def total_without_discount(self):
        return sum(item.total_without_discount for item in self.items())

    @cached_property
    def discount_sum(self):
        return self.total_without_discount - self.total

    @property
    def discount_total(self):
        return self.total_without_discount - self.total

    def add(self, product, option=None, quantity=1):
        """
        Добавить продукт в корзину .
        """

        item_id = self.encode_id(product, option)
        try:
            self.cart[item_id]['quantity'] += quantity
        except KeyError:
            self.cart[item_id] = {'quantity': quantity}
        # новое количество не должно превышать количество товара на складе
        quantity = check_quantity(quantity, product)
        self.cart[item_id]['quantity'] = quantity
        self.save()

    def update(self, product, option=None, quantity=1):
        """
        Обновить количество товара в корзине.
        """
        if quantity == 0:
            return self.remove(product)
        item_id = self.encode_id(product, option)
        # новое количество не должно превышать количество товара на складе
        quantity = check_quantity(quantity, product)
        self.cart[item_id]['quantity'] = quantity
        self.save()

    def remove(self, product, option=None):
        """
        Удаление товара из корзины.
        """
        item_id = self.encode_id(product, option)
        if item_id in self.cart:
            del self.cart[item_id]
            self.save()

    def clear(self):
        self.cart = {}
        self.save()

    def save(self):
        # Обновление сессии cart
        self.session[CART_SESSION_ID] = self.cart
        # Отметить сеанс как "измененный", чтобы убедиться, что он сохранен
        self.session.modified = True

    def exists(self):
        return bool(self.items())

    def get(self, product, option=None, **kwargs):
        items = list(filter(
            lambda item: item.product.id == int(product) and item.option == option,
            self.items()))
        if items:
            return items[0]
        return None


class UnauthCartItem(CartItemInterface):
    """Элемент корзины неавторизованного пользователя."""

    def __init__(self, product, quantity, option=None):
        self.product = product
        self.option = option
        self.quantity = quantity
