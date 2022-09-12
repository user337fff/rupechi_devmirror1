import decimal
import itertools
import os

from apps.commons.models import ImageModel, WithBreadcrumbs, FullSlugMixin
from apps.domains.models import Domain
from apps.domains.middleware import get_request
from apps.seo.models import SeoBase
from apps.seo.templatetags.seo import Seo

from ckeditor_uploader.fields import RichTextUploadingField
from django.apps import apps
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import When, Case, Sum, Count, Avg, F, Min, Q, QuerySet
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.core.cache import cache
from mptt.models import MPTTModel, TreeForeignKey

from . import get_contractor
from ..managers import ProductManager
from ...configuration.models import Settings
from .category import *

from django.db.models.signals import post_save
from django.dispatch import receiver
import math

def _get_field(number=None, required=True, old=''):
    data = {}
    name = old + 'Розничная цена'
    if number:
        name = old + 'Цена контрагента №' + str(number)
    if required:
        data['blank'] = True
        data['null'] = True
    return models.DecimalField(name, decimal_places=2, max_digits=10, **data)


def get_old_price_field(number=None, required=True):
    return _get_field(number, required, 'Старая ')


def get_price_field(number=None, required=True):
    return _get_field(number, required)


CONTRACTORS_COUNT = 3

# Миграции нормально не работают, связано это с неправильной миграцией некоторых моделей, где создавались/удалялись поля
# Можно попробовать удалить список миграций, тогда, по-идее, миграции должны заработать
class Product(MPTTModel, FullSlugMixin, ImageModel, WithBreadcrumbs, SeoBase):
    # managers
    objects = ProductManager()

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ('title',)
        indexes = [GinIndex(fields=['search_vector'])]

    ONLY = ('title', 'slug', 'code', 'price', 'old_price', 'stock')

    parent = TreeForeignKey('self', verbose_name='Родительский товар',
                            on_delete=models.CASCADE, blank=True, null=True,
                            related_name='variations')
    is_active = models.BooleanField(
        verbose_name='Активен', default=True, db_index=True)
    is_discount = models.ManyToManyField(Domain, verbose_name='Не применять скидку 5% на доменах',
                                         related_name='product_discount', blank=True, null=True)
    is_import_active = models.BooleanField('В выгрузке', default=True)
    category = models.ForeignKey(
        'catalog.Category', verbose_name='Категория', related_name='products',
        on_delete=models.CASCADE, blank=True, null=True)
    brand = models.ForeignKey(
        'catalog.Brand', related_name='brand_products', on_delete=models.SET_NULL,
        blank=True, null=True)
    # info
    title = models.CharField(
        verbose_name='Название', max_length=127, db_index=True)
    slug = models.SlugField(verbose_name='Слаг', max_length=255, db_index=True)
    code = models.CharField(
        verbose_name='Артикул', blank=True, null=True, max_length=63)
    description = RichTextUploadingField(
        verbose_name='Описание', blank=True, default='')

    last_description = models.TextField(
		verbose_name='Описание', blank=True, default='')

    stock = models.PositiveIntegerField(
        verbose_name='Остаток на складе', default=0)
    attributes = models.ManyToManyField(
        'ProductAttribute', verbose_name='Атрибуты',
        through='AttributeProducValue')
    related_products = models.ManyToManyField(
        'self', verbose_name='Сопутствующие товары', blank=True,
        symmetrical=False)
    views = models.PositiveIntegerField('Просмотры', default=0, editable=False)

    # shipping parameters
    weight = models.PositiveIntegerField(verbose_name="Масса", default=0)
    width = models.PositiveIntegerField(verbose_name="Ширина", default=0)
    height = models.PositiveIntegerField(verbose_name="Высота", default=0)
    length = models.PositiveIntegerField(verbose_name="Длина", default=0)
    # const
    hit = models.BooleanField('Хит', default=False)
    new = models.BooleanField('Новинка', default=False)
    offer = models.BooleanField('Акция', default=False)
    top_hit = models.BooleanField('Топ продаж', help_text='Блок на главной', default=False)
    # import
    id_1c = models.UUIDField(
        verbose_name='Идентификатор 1С', blank=True, null=True, unique=True,
        help_text='Заполняется автоматически')
    # search
    search_vector = SearchVectorField(null=True)
    # dates
    created_at = models.DateTimeField(
        verbose_name='Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField(
        verbose_name='Дата последнего обновления', auto_now=True)
    keywords = models.CharField('Ключевые слова', max_length=125, default="", blank=True)

    VIEWED_SESSION_ID = 'viewed_products'

    lastStockQuantityBoolean = models.BooleanField(default=False)

    def replace_selectionTags(self):
        desc = self.description
        print(desc)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        search_vector = (
                SearchVector('title', weight='A')
                + SearchVector('description', weight='B')
        )
        # поисковой вектор можно обновлять только у уже существующих записей бд
        if not self.is_active:
            print(f'=== DEACT DEBUG PRODUCT ID {self.id_1c}')
        if self.pk:
            self.search_vector = search_vector
            return super().save(*args, **kwargs)
        else:
            _ = super().save(*args, **kwargs)
            Product.objects.filter(pk=self.pk).update(
                search_vector=search_vector)
            return _

    def in_stock(self):
        domain = get_request().domain
        return bool(self.quantity_stores.filter(quantity__gt=0, store__domain=domain))

    @staticmethod
    def autocomplete_search_fields():
        """jet admin"""
        return 'title', 'slug'

    def get_absolute_url(self, **kwargs):
        return reverse('product', kwargs={'slug': self.encode_slug()})

    def get_breadcrumbs(self, **kwargs):
        if self.parent:
            breadcrumbs = self.parent.get_breadcrumbs()
            breadcrumbs.append((self.title, self.get_absolute_url()))
        elif self.category:
            breadcrumbs = self.category.get_breadcrumbs()
            breadcrumbs.append((self.title, self.get_absolute_url()))
        else:
            breadcrumbs = super().get_breadcrumbs()
        breadcrumbs[-1] = (breadcrumbs[-1][0], '#')
        return breadcrumbs

    def get_price_line(self, domain=None):
        domain = domain or get_request().domain
        return self.prices.filter(domain=domain).first()

    def clean_description(self, description):
        ReplaceAttr = apps.get_model('catalog.ReplaceAttr')
        for item in ReplaceAttr.objects.iterator():
            slug = item.slug
            if slug in description:
                attr = self.product_attributes.filter(attribute=item.attribute).first()
                if attr:
                    description = description.replace(slug, str(attr.value))
        if self.brand:
            description = description.replace('||brand||', self.brand.__str__())
        description = Seo(context={'object': self}).clean(description)
        description = description.replace('"', "'")
        return description

    def get_quantity_stores(self):
        domain = get_request().domain
        stores = self.quantity_stores.filter(store__domain=domain, store__is_active=True)
        quantity_stores = [{'store': store.store, 'quantity': store.quantity,
                           'price': store.product.get_storage_info()['price']} for store in stores]
        return quantity_stores

    def get_description(self):
        description = self.category.product_description
        if not description:
            description = self.description
        result_description = mark_safe(self.clean_description(description))
        return result_description

    def get_unlink_brand(self):
        return self.category.get_ancestors(include_self=True).filter(unlink_brand=True).exists()

    def get_preview_attrs(self):
        dict_attrs = self.product_attributes.filter(attribute__visible_on_attrs=True) \
                         .filter(attribute__type='dict').order_by('attribute')[:5]
        number_attrs = self.product_attributes.filter(attribute__visible_on_attrs=True) \
                           .filter(attribute__type='number').order_by('attribute')[:5]
        dict_attrs = list(dict_attrs)
        number_attrs = list(number_attrs)
        if self.brand:
            dict_attrs.insert(1, {'attribute': 'Производитель', 'value': self.brand})
        response = dict_attrs + list(number_attrs)
        cache.set(f'{self.id}-get-preview-attrs', response, 10 * 60)
        return response

    def get_storage_info(self, domain=None):
        request = get_request()
        contractor = get_contractor(request)
        is_contractor = False
        contractors = ['1', '2', '3']
        if set(contractor.replace('_', '').split()).intersection(set(contractors)):
            is_contractor = True

        domain = domain or request.domain

        response = {
            'price': 0,
            'quantity': 0,
            'old_price': 0,
        }

        if domain.domain == 'spb.rupechi.ru':
            quantity_vologda = self.quantity_stores.active(domain='www.rupechi.ru').aggregate(
                quantity=Sum('quantity')).get('quantity') or 0
            quantity_spb = self.quantity_stores.active().aggregate(quantity=Sum('quantity')).get('quantity') or 0
            quantity = quantity_vologda + quantity_spb

        else:
            quantity = self.quantity_stores.active().aggregate(quantity=Sum('quantity')).get('quantity') or 0

        try:
            price = self.price if not is_contractor else eval(f'self.price{contractor}')
            old_price = self.old_price
            percent = self.percent

        except AttributeError:
            cart_price = self.get_price_line()
            if is_contractor:
                price = eval(f'cart_price.price{contractor}')
                old_price = 0
                percent = 0
            else:
                price = cart_price.price
                old_price = cart_price.old_price
                percent = cart_price.percent

        category = self.category
        if price:

            price = math.ceil(price)

            response = {
                'price': price,
                'quantity': int(quantity) if int(quantity) else '',
                'old_price': 0
            }

            categories_tree_ancestors = category.get_ancestors(include_self=True)

            #brands = list(category.discount_brands.values_list('id', flat=True))

            brands = set()
            for cat in categories_tree_ancestors:
                brands_list = cat.discount_brands.values_list('id', flat=True)
                if(brands_list):
                    brands.update(brands_list)

            #category_parent_discount = set(
            #    category.get_ancestors(include_self=True).values_list('discount_category', flat=True))

            category_parent_discount = set(
                categories_tree_ancestors.values_list('discount_category', flat=True))

            discount_brands = []

            if self.brand:
                discount_brands = self.brand.not_discount.all()

            discount = Settings.get_discount() if not domain.domain in category_parent_discount \
                                                  and domain not in discount_brands \
                                                  and domain not in self.is_discount.all() \
                else decimal.Decimal(0)

            if self.brand_id not in brands and discount and not is_contractor:
                response['discount_price'] = math.ceil((price or decimal.Decimal(0)) * discount)
                
            if not is_contractor and (old_price or percent):
                if old_price and not is_contractor:
                    
                    response['price'] = old_price
                    response['old_price'] = price

                    if old_price <= price:
                        response['price'] = price
                        response['old_price'] = 0

                if percent:
                    response['old_price'] = math.ceil(decimal.Decimal(1 - int(percent) / 100) * price)

            if self.brand_id not in brands and discount and not is_contractor:
                response['discount_price'] = math.ceil((price or decimal.Decimal(0)) * discount)

        return response

    def get_aliases(self):
        domain = get_request().domain
        return self.aliases.filter(domain__exact=domain)

    def add_viewed_product(self):
        """
        Добавление товара в просмотренные
        """
        request = get_request()
        session = request.session
        if self.VIEWED_SESSION_ID not in session:
            session[self.VIEWED_SESSION_ID] = []
        # если ид уже существует, то удаляем и вставляем в начало новый элемент
        if self.id in session[self.VIEWED_SESSION_ID]:
            session[self.VIEWED_SESSION_ID].remove(self.id)
        session[self.VIEWED_SESSION_ID].insert(0, self.id)
        session[self.VIEWED_SESSION_ID] = session[self.VIEWED_SESSION_ID][:15]
        session.save()
        self.__class__.objects.filter(id=self.id).update(views=F('views') + 1)

    @classmethod
    def get_viewed_product_list(cls, exclude_id=None):
        """
        Получение просмотренных товаров
        """
        request = get_request()
        session = request.session
        if cls.VIEWED_SESSION_ID not in session:
            return []
        else:
            when_list = []
            # собираем список условий для сортировки по дате добавления
            for pos, pk in enumerate(session[cls.VIEWED_SESSION_ID]):
                when_list.append(When(pk=pk, then=pos))
            preserved_order = Case(*when_list)
            queryset = cls.objects.active() \
                .filter(parent__isnull=True) \
                .filter(id__in=session[cls.VIEWED_SESSION_ID]) \
                .order_by(preserved_order)
            if exclude_id is not None:
                queryset = queryset.exclude(id=exclude_id)
            return queryset

    def get_variations(self):
        request = get_request()
        return self.variations.filter(domain__exact=request.domain, is_active=True, parent__is_active=True)

    def get_rating(self):
        ratings = self.ratings.aggregate(count=Count('id'), rating=Avg('rating'))
        return ratings

    def is_hit(self):
        if self.category and self.category.get_ancestors(include_self=True).filter(hit_check_products=True).exists():
            return self.hit
        return self.views >= 500

    def get_card_attrs(self):
        return self.product_attributes.filter(attribute__visible_on_attrs=True).order_by('attribute')

    def get_card_attrs_header(self):
        return self.get_card_attrs()[:5]

    def get_card_attrs_description(self):
        return self.get_card_attrs()[5:]

    def get_similar_product(self, count):
        request = get_request()
        price_line = self.prices.filter(domain=request.domain).first()
        price = 0
        price_name = 'price'
        if price_line:
            price_name = 'price' + get_contractor(request)
            price = getattr(price_line, price_name) or 0

        if price >= 300000:
            price_limit = price + 100000
            price_down_limit = price - 100000
        elif price >= 200000:
            price_limit = price + 50000
            price_down_limit = price - 50000
        elif price >= 100000:
            price_limit = price + 50000
            price_down_limit = price - 30000
        elif price >= 20000:
            price_limit = price + 10000
            price_down_limit = price - 10000
        else:
            price_limit = price + 5000
            price_down_limit = price - 10000

        products = Product.objects \
                       .filter(parent__isnull=True) \
                       .active(category=self.category,
                               prices__domain=request.domain,
                               **{f'prices__{price_name}__lte': price_limit,
                                  f'prices__{price_name}__gte': price_down_limit}) \
                       .exclude(id=self.id)[:count]
        return products


def product_image_directory_path(instance, filename):
    app = instance._meta.app_label
    product = str(instance.product_id)
    return f'images/{app}/products_gallery/{product}/{filename}'


class ProductImage(ImageModel):
    product = models.ForeignKey(
        Product, verbose_name='Товар', related_name='gallery',
        on_delete=models.CASCADE)
    image = models.ImageField(verbose_name='Изображение',
                              upload_to=product_image_directory_path)
    image_md5 = models.CharField(verbose_name='Хэш изображения', blank=True,
                                 default='', max_length=63,
                                 help_text='Заполняется автоматически')
    position = models.PositiveIntegerField(
        verbose_name='Сортировка', default=0)

    def __str__(self):
        return str(self.product)

    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'
        ordering = ['position']


class ProductVideo(models.Model):
    product = models.ForeignKey(
        Product, verbose_name='Товар', related_name='videos',
        on_delete=models.CASCADE)
    link = models.URLField(
        verbose_name='Ссылка', max_length=127, blank=True, default='')
    file = models.FileField(
        verbose_name='Изображение',
        upload_to=product_image_directory_path, blank=True)
    position = models.PositiveIntegerField(
        verbose_name='Сортировка', default=0)

    def __str__(self):
        return str(self.product)

    def get_youtube_link(self):
        _, code_video = self.link.split('v=')
        return f'https://www.youtube.com/embed/{code_video}'

    def get_link(self):
        _, code_video = self.link.split('v=')
        return f'Video-{code_video}'

    class Meta:
        verbose_name = 'видео товара'
        verbose_name_plural = 'Видео товаров'
        ordering = ['position']


class ProductDocument(models.Model):
    product = models.ForeignKey(
        Product, verbose_name='Товар', related_name='docs',
        on_delete=models.CASCADE)
    title = models.CharField(
        verbose_name='Заголовок', max_length=127, blank=False, default='')
    file = models.FileField(
        verbose_name='Изображение', upload_to=product_image_directory_path)
    position = models.PositiveIntegerField(
        verbose_name='Сортировка', default=0)

    def __str__(self):
        return str(self.product)

    def extension(self):
        name, extension = os.path.splitext(self.file.name)
        return extension

    def get_size(self):
        size = os.path.getsize(self.file.path)
        sizes = [" Б", " Кб", " Мб"]
        if size < 512000:
            size = size / 1024.0
            ext = 'Кб'
        elif size < 4194304000:
            size = size / 1048576.0
            ext = 'Мб'
        else:
            size = size / 1073741824.0
            ext = 'Гб'
        return f'{size} {ext}'

    class Meta:
        verbose_name = 'документация товара'
        verbose_name_plural = 'Документации товаров'
        ordering = ['position']


class Rating(models.Model):
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, verbose_name="Продукт",
                                related_name='ratings')
    user = models.ForeignKey('users.Account', on_delete=models.CASCADE, verbose_name="Пользователь")
    rating = models.PositiveSmallIntegerField('Оценка', validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        ordering = ['id']
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки'
        unique_together = ['product', 'user']

    def __str__(self):
        return f'{self.product.__str__()}: {self.rating}'


class Prices(models.Model):
    product = models.ForeignKey('catalog.Product', verbose_name="Продукт", on_delete=models.CASCADE,
                                related_name='prices')
    domain = models.ForeignKey('domains.Domain', verbose_name="Домен", on_delete=models.CASCADE)
    # на самом деле ужасно, но иного выхода не нашел
    price = get_price_field(required=True)
    old_price = get_old_price_field()

    price_1 = get_price_field(1)
    price_2 = get_price_field(2)
    price_3 = get_price_field(3)
    percent = models.FloatField('Процент скидки', default=0, blank=True,
                                validators=[MinValueValidator(0), MaxValueValidator(100)])

    def update_prices(self):

        print("--------------")
        print("Прошлые цены")
        print(self.price)
        print(self.price_1)
        print(self.price_2)
        print(self.price_3)

        if(self.price):
            self.price = math.ceil(float(self.price))

        if(self.price_1):
            self.price_1 = math.ceil(float(self.price_1))
            
        if(self.price_2):
            self.price_2 = math.ceil(float(self.price_2))

        if(self.price_3):
            self.price_3 = math.ceil(float(self.price_3))

        print("Современные цены")
        print(self.price)
        print(self.price_1)
        print(self.price_2)
        print(self.price_3)

        self.save()

    class Meta:
        ordering = ['id']
        verbose_name = 'Цена'
        verbose_name_plural = 'Цены'
        unique_together = ['product', 'domain']

    def __str__(self):
        return f'Цена для {self.domain}'

    def get_price(self):
        request = get_request()
        contractor = get_contractor(request)
        return getattr(self, 'price' + contractor) or 0


class InStockNotification(models.Model):

    domain = models.ForeignKey('domains.Domain', verbose_name='Домен', on_delete=models.CASCADE)
    user_email = models.CharField(max_length=255, verbose_name='Email пользователя')
    product = models.ForeignKey('catalog.Product', verbose_name='Продукт', on_delete=models.CASCADE)

    def __str__(self):
        return f'Уведомление для {self.user_email}'

    def in_stock(self):
        return self.product.in_stock()


@receiver(post_save, sender=Product)
def signal_product_save(sender, instance, **kwargs):
    for price in instance.prices.all():
        price.update_prices()