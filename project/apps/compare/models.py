from abc import ABC, abstractmethod

from django.conf import settings
from django.db import models

from apps.catalog.models import Product


def get_compare(request):
    """ Получение товаров для сравнения в зависимости от авторизации """
    if request.user.is_authenticated:
        return Compare(request)
    return CompareUnauth(request)


class CompareBase(ABC):
    """ Базовый класс для сравнения """

    @abstractmethod
    def items(self):
        pass

    @abstractmethod
    def count(self):
        pass

    @abstractmethod
    def toggle(self, product):
        pass


class Compare(CompareBase):
    """ Товары для сравнения авторизованного пользователя """

    def __init__(self, request):
        self.user = request.user

    @property
    def count(self):
        return self.items().count()

    def items(self):
        items = CompareItem.objects.filter(user=self.user).select_related('product')
        self.ids = list(map(int, list(items.values_list('product_id', flat=True))))
        return items

    def toggle(self, product):
        if product.parent:
            CompareItem.objects.filter(
                user=self.user,
                product__in=product.parent.variations.exclude(id=product.id).all()
            ).delete()
        product = product.variations.first() or product

        items = CompareItem.objects.filter(user=self.user, product=product)
        if(items.exists()):
            items.delete()
        else:
            item, _ = CompareItem.objects.get_or_create(user=self.user, product=product)
            #item, created = CompareItem.objects.get_or_create(
            #    user=self.user, product=product)
            #if not created:
            #    item.delete()

    def clear(self):
        self.items().delete()


class CompareItem(models.Model):
    """Элемент к сравнению"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='compare_products',
        on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, related_name="compare_items", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "элемент товаров для сравнения"
        verbose_name_plural = "Элементы товаров для сравнения"


class CompareUnauth(CompareBase):
    """ Товары для сравнения неавторизованного пользователя """

    COMPARE_SESSION_ID = 'compare'

    def __init__(self, request):
        self.session = request.session
        ids = self.session.get(self.COMPARE_SESSION_ID)
        if ids is None:
            ids = self.session[self.COMPARE_SESSION_ID] = []
        self.ids = ids

    @property
    def count(self):
        return len(self.ids)

    def items(self):
        products = Product.objects.filter(id__in=self.ids)
        return [UnauthCompareItem(product) for product in products]

    def toggle(self, product):
        product = product.variations.first() or product
        if product.id in self.ids:
            self.ids.remove(product.id)
        else:
            self.ids.append(product.id)
        self.save()

    def clear(self):
        self.ids = []
        self.save()

    def save(self):
        self.session[self.COMPARE_SESSION_ID] = self.ids
        self.session.modified = True


class UnauthCompareItem:
    """Элемент к сравнению неавторизованного пользователя."""

    def __init__(self, product):
        self.product = product
