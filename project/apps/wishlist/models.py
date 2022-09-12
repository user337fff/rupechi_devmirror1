from abc import ABC, abstractmethod

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property

from apps.catalog.models import Product
from apps.domains.middleware import get_request


def get_wishlist(request):
    """ Получение избранные товары в зависимости от авторизации """
    if request.user.is_authenticated:
        return Wishlist(request)
    return WishlistUnauth(request)


class WishlistBase(ABC):
    """ Базовый класс избранных товаров """

    @abstractmethod
    def items(self):
        pass

    @abstractmethod
    def count(self):
        pass

    @abstractmethod
    def toggle(self, product):
        pass


class Wishlist(WishlistBase):
    """ Избранные товары авторизованного пользователя """

    def __init__(self, request):
        self.user = request.user

    @cached_property
    def count(self):
        return self.items().count()

    def items(self):
        domain = get_request().domain
        items = WishlistItem.objects.select_related('product').filter(user=self.user, product__domain__exact=domain)
        self.ids = list(map(int, list(items.values_list('product_id', flat=True))))
        return items

    def toggle(self, product):
        item, created = WishlistItem.objects.get_or_create(
            user=self.user, product=product)
        if not created:
            item.delete()


class WishlistItem(models.Model):
    """Элемент избранного"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='wishlist_products',
        on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, related_name="wishlist_items", on_delete=models.CASCADE)

    class Meta:
        ordering = ['id']
        verbose_name = "Элемент избранных товаров"
        verbose_name_plural = "Элементы избранных товаров"

    def __str__(self):
        return f'{self.user.__str__()}: {self.product.__str__()}'


class WishlistUnauth(WishlistBase):
    """ Избранные товары неавторизованного пользователя """
    WISHLIST_SESSION_ID = 'wishlist'

    def __init__(self, request):
        self.session = request.session
        ids = self.session.get(self.WISHLIST_SESSION_ID)
        if ids is None:
            ids = self.session[self.WISHLIST_SESSION_ID] = []
        self.ids = ids

    @cached_property
    def count(self):
        return len(self.ids)

    def items(self):
        domain = get_request().domain
        products = Product.objects.filter(id__in=self.ids, domain__exact=domain)
        return [UnauthWishlistItem(product) for product in products]

    def toggle(self, product):
        if product.id in self.ids:
            self.ids.remove(product.id)
        else:
            self.ids.append(product.id)
        self.save()

    def save(self):
        self.session[self.WISHLIST_SESSION_ID] = self.ids
        self.session.modified = True


class UnauthWishlistItem:
    """Элемент к сравнению неавторизованного пользователя."""

    def __init__(self, product):
        self.product = product
