from apps.commons.models import WithBreadcrumbs
from django.urls import reverse
from django.core.cache import cache

from apps.configuration.models import Settings
from apps.domains.middleware import get_request
from apps.catalog.models.calc import get_contractor
import decimal


class CartInterface(WithBreadcrumbs):
    title = 'Корзина'
    MAX = 100

    def total(self):
        raise AttributeError("Метод отсутствует")

    def items(self):
        raise AttributeError("Метод отсутствует")

    def get_absolute_url(self):
        return reverse('cart:cart_detail')
    
    def total_without_discount(self):
        raise AttributeError("Метод отсутствует")

    def discount_sum(self):
        raise AttributeError("Метод отсутствует")


class CartItemInterface:

    @property
    def title(self):
        title = self.product.title
        return title

    @property
    def price(self):
        # request = get_request()
        # contractor = cache.get(f'{request.user}-contractor')
        # if not contractor:
        #     contractor = get_contractor(request)
        #     cache.set(f'{request.user}-contractor', contractor)
        # is_contractor = False
        # contractors = ['1', '2', '3']
        # if set(contractor.replace('_', '').split()).intersection(set(contractors)):
        #     is_contractor = True
        # if is_contractor:
        #     cont_price = eval(f'self.product.get_storage_info().get("price{contractor}")')
        #     if cont_price:
        #         return cont_price
        #     else:
        #         return self.product.get_storage_info().get('price')
        return self.product.get_storage_info().get('price')

    @property
    def discount_price(self):
        request = get_request()
        contractor = cache.get(f'{request.user}-contractor')
        if not contractor:
            contractor = get_contractor(request)
            cache.set(f'{request.user}-contractor', contractor)
        is_contractor = False
        contractors = ['1', '2', '3']
        if set(contractor.replace('_', '').split()).intersection(set(contractors)):
            is_contractor = True
        if not is_contractor:
            data = self.product.get_storage_info()
            return data.get('discount_price') or data.get('old_price')
        else:
            return 0

    @property
    def total(self):
        """
        с учетом скидки 5%
        """
        return (self.discount_price or self.price) * self.quantity

    @property
    def total_without_discount(self):
        """
        Сумма без учета скидок
        """
        return self.price * self.quantity
