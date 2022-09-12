import decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils.functional import cached_property

from apps.catalog.models import Product, Catalog
from .interface import CartInterface, CartItemInterface
from ...configuration.models import Settings
from ...domains.middleware import get_request


def check_quantity(quantity, product):
    return quantity
    domain = get_request().domain
    product_quantity = product.quantity_stores \
                           .select_related('store') \
                           .filter(store__domain=domain) \
                           .aggregate(count=Sum('quantity')).get('count') \
                       or 0
    return quantity if quantity < product_quantity or not product_quantity else product_quantity


class Cart(models.Model, CartInterface):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    promocode = None

    def __str__(self):
        return f"Корзина пользователя {self.user}"

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

    @cached_property
    def count(self):
        # вычисляем сумму количества добавленных товаров
        quantity_sum = self.items().aggregate(Sum('quantity'))['quantity__sum']
        if isinstance(quantity_sum, int):
            return quantity_sum
        return 0

    @property
    def total(self):
        total = 0
        for item in self.items():
            total += item.total
        return total

    @cached_property
    def total_without_discount(self):
        total = 0
        for item in self.items():
            total += item.total_without_discount
        return total

    @property
    def discount_total(self):
        return self.total_without_discount - self.total

    @cached_property
    def discount_sum(self):
        return self.total_without_discount - self.total

    def items(self):
        domain = get_request().domain
        return self.positions.filter(option=domain).all()

    def add(self, product, option=None, quantity=1):
        """
        Добавить продукт в корзину.
        """
        try:
            item = CartItem.objects.get(
                cart=self, option=option, product=product)
            quantity += item.quantity
        except CartItem.DoesNotExist:
            item = None

        # новое количество не должно превышать количество товара на складе
        quantity = check_quantity(quantity, product)
        if item is None:
            CartItem.objects.create(
                cart=self, product=product, option=option, quantity=quantity)
        else:
            item.quantity = quantity
            item.save(update_fields=['quantity'])

    def update(self, product, option=None, quantity=1):
        if quantity == 0:
            return self.remove(product=product, option=option)
        # новое количество не должно превышать количество товара на складе
        quantity = check_quantity(quantity, product)
        CartItem.objects.update_or_create(
            cart=self, product=product, option=option, defaults={"quantity": quantity})

    def remove(self, **kwargs):
        """
        Удаление товара из корзины.
        """
        CartItem.objects.filter(**kwargs).delete()

    def clear(self):
        """Очистка корзины"""
        self.items().delete()

    def get(self, **kwargs):
        return self.items().filter(**kwargs).first()

    def exists(self):
        return self.items().exists()

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины пользователей"


class CartItem(CartItemInterface, models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name='positions')
    product = models.ForeignKey(
        Product, verbose_name='Товар', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(
        verbose_name='Количество', default=1)
    option = models.ForeignKey('domains.Domain', verbose_name="Домен", on_delete=models.CASCADE,
                               blank=True, null=True)

    def __str__(self):
        return f"Элемент корзины {self.id} {self.product.title}"

    class Meta:
        verbose_name = "Элемент корзины"
        verbose_name_plural = "Элементы корзины"
