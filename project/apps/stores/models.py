from apps.domains.middleware import get_request
from apps.domains.models import Domain
from apps.feedback.models import RecipientMixin
from apps.cart.models.base import get_cart, get_gefest, get_cooking_on_fire
from django.db import models


class StoreProductQuerySet(models.QuerySet):

    def active(self, domain=None):
        domain = domain or get_request().domain
        return self.filter(store__domain=domain)


class StoreProductQuantity(models.Model):
    store = models.ForeignKey(
        'stores.Store', verbose_name='Склад',
        on_delete=models.CASCADE,
        related_name='quantity_products')
    product = models.ForeignKey(
        'catalog.Product',
        verbose_name='Товар',
        on_delete=models.CASCADE,
        related_name='quantity_stores')

    quantity = models.PositiveIntegerField(verbose_name='Количество')

    objects = StoreProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'Количество на складе'
        verbose_name_plural = 'Количество на складе'

    def __str__(self):
        return f'{self.product.__str__()} {self.store.__str__()}'


class StoreQuerySet(models.QuerySet):

    def get_current(self, domain=None):
        domain = domain or get_request().domain
        # current = self.filter(domain__exact=domain)
        current = self
        print("~~~Stores~~~")
        #if domain.domain == 'spb.rupechi.ru':
        is_gefest = get_gefest(get_cart(get_request()))
        is_cooking_on_fire = get_cooking_on_fire(get_cart(get_request()))
        if is_gefest:
            current = current.exclude(title='ул. Фучика, 9')
        else:
            current = current.exclude(title='ул.Фучика, 9 "Технолит"')

        #Если есть товар из категории Готовка на огне, то исключаем магазин Паргос
        if(is_cooking_on_fire):
            print("Это готовка на огне!")
            current = current.exclude(id_1c="99e56951-8a67-11ec-a863-00155d2cb601")
        else:
            print("Это не готовка на огне")

        return current

    def active(self):
        return self.filter(is_active=True)


class Store(RecipientMixin, models.Model):
    id_1c = models.UUIDField(
        verbose_name='Идентификатор 1С',
        unique=True, blank=True, null=True,
        help_text='Заполняется автоматически')
    is_footer = models.BooleanField('Показывать в футере', default=False)
    is_active = models.BooleanField('Активность', default=True)
    domain = models.ForeignKey(
        Domain, related_name='stores', on_delete=models.CASCADE)
    title = models.CharField(verbose_name='Название', max_length=127)
    address = models.CharField(verbose_name='Адрес', max_length=255)

    description = models.TextField(
        verbose_name='Описание', default='', blank=True)
    phone = models.TextField(
        verbose_name="Номер телефона", blank=True, default="")
    email = models.EmailField('Email', blank=True, default="")
    working_hours = models.TextField('Часы работы', default="", blank=True)
    
    lat = models.DecimalField(
        verbose_name="Координата X на карте", max_digits=9, decimal_places=6,
        blank=True, null=True)
    lon = models.DecimalField(
        verbose_name="Координата Y на карте", max_digits=9, decimal_places=6,
        blank=True, null=True)

    products = models.ManyToManyField(
        "catalog.Product",
        verbose_name='Товары',
        through=StoreProductQuantity)

    # dates
    created_at = models.DateTimeField(
        verbose_name='Дата создания', auto_now_add=True)

    sort = models.PositiveIntegerField('Сортировка', default=0)

    objects = StoreQuerySet.as_manager()

    class Meta:
        verbose_name = 'Магазин (склад)'
        verbose_name_plural = 'Магазины (склады)'
        ordering = ('sort',)

    def __str__(self):
        return f'{self.title or self.get_full_address()}'

    def get_full_address(self):
        return f'{self.domain.name}, {self.address}'

    def get_phones(self):
        return self.phone.split('\n')

    def get_works(self):
        return self.working_hours.split('\n')
