import re

from apps.catalog import models as catalog_models
from django.db.models import Q, CharField, Value as V, F, Max
from django.db.models.functions import Concat

from .base import ProductFilterBase


class ProductFilterSEF(ProductFilterBase):
    """
    Фильтрация товаров с использованием ЧПУ.

    В данной реализации используются не GET-параметры, а url.
    Вместо числовых идентификаторов атрибута и значения используются слаги.

    SEF URL - Search Engines Friendly Url
    По хуевастой русификации это зовется ЧПУ – Человеко-Понятные Урлы

    Строка запроса должна иметь тип:
     /f/brand=microsoft,sony,samsung/dlina=0-300
    где:
     brand=microsoft,sony,samsung
     {слаг_атрибута}={слаг_значения_1},{слаг_значения_2}
     dlina=0-300 - числовой атрибут {слаг_атрибута}={мин}-{макс}

     price=0-300 - числовые поля модели {имя}={мин}-{макс}или{значение}
     hit=on - статичные фильтры
    """

    DICT_PATTERN = re.compile('([\w+\-]+)=((?:[A-z0-9-]+,?)+(?<=[A-z]))')
    VALUE_SEPARATOR = ','

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.NUM_PATTERN = re.compile(
            f'([\w+\-]+)={self.NUM_VALUE_STRING_PATTERN}')
        self.path = self.request.path

    def filter_brand(self, slug, values):
        if self.is_alias:
            self.queryset = self.queryset.filter(brand__slug__in=values)
        else:
            self.queryset_filtered = self.queryset_filtered.filter(brand__slug__in=values)
        for v in values:
            self.actived['dict'].append(f'{slug}_{v}')

    def filter_dict(self):
        """ Фильтрация по словарным атрибутам """
        # Фильтры с урла
        if self.is_alias:
            parameters = self.alias_filters.items()
        else:
            parameters = self.DICT_PATTERN.findall(self.path)
        for attr_slug, values in parameters:
            # не понять какие атрибуты за какой тип отвечают, встречаются словари с цифрами
            if isinstance(values, str):
                values = values.split(self.VALUE_SEPARATOR)
            if attr_slug == 'brand':
                self.filter_brand(attr_slug, values)
                continue
            elif attr_slug == 'stock':
                for value in values:
                    if value == 'inStock':
                        self.queryset_filtered = self.queryset_filtered \
                            .annotate(
                            max_q=Max(
                                'quantity_stores__quantity',
                                filter=Q(store__domain=self.request.domain)
                            )
                        ) \
                            .filter(max_q__gt=0)
                    elif value in 'akcii':
                        self.queryset_filtered = self.queryset_filtered \
                            .annotate(
                            max_old_price=Max('prices__old_price', filter=Q(domain=self.request.domain))
                        ) \
                            .filter(max_old_price__gt=0)
                    self.actived['dict'].append(f'{attr_slug}_{value}')
                continue
            if attr_slug not in ['price']:
                # Доп проверОчка для регулярок
                # attr = ProductAttribute.objects.get(slug=attr_slug)
                # if attr.type == attr.DICT:
                attr_query = Q(product_attributes__attribute__slug=attr_slug)
                value_query = Q()
                for value in values:
                    value_query |= Q(product_attributes__value_dict__slug=value)
                    # set actived
                    self.actived['dict'].append(f'{attr_slug}_{value}')
                if self.is_alias:
                    if isinstance(values, list):
                        self.queryset = self.queryset.filter(attr_query & value_query)
                else:
                    self.queryset_filtered = self.queryset_filtered.filter(attr_query & value_query)

    def filter_num(self):
        """ Фильтрация по числовым атрибутам """
        if self.is_alias:
            parameters = self.alias_filters.items()
        else:
            parameters = re.findall(r'([\w\-]+)=([\d\.]*-[\d\.]*)', self.path)

        

        for attr_slug, value, *args in parameters:

            if attr_slug not in ['brand']:

                #num_object = {}

                # Доп проверОчка для регулярок
                # attr = ProductAttribute.objects.filter(slug=attr_slug).first()
                # if value and (attr_slug == 'price' or attr.type == attr.NUMBER):
                if isinstance(value, dict):
                    min_value = str(value.get('min', 0))
                    max_value = str(value.get('max', ''))
                elif isinstance(value, list):
                    continue
                else:
                    values = value.split('-')
                    min_value = values[0]
                    max_value = None
                    if len(values) > 1:
                        max_value = values[-1]
                if attr_slug == catalog_models.SLUG_PRICE:
                    self.filter_price(f'{min_value or 0}-{max_value}')
                    continue
                query = Q()
                if min_value:
                    min_value = self.clear_number(min_value)

                    #num_object["min"] = min_value 

                    query = query & Q(
                        product_attributes__value_number__gte=min_value)
                if max_value:
                    max_value = self.clear_number(max_value)

                    #num_object["max"] = max_value 

                    query = query & Q(
                        product_attributes__value_number__lte=max_value)
                if query:
                    query = query & Q(
                        product_attributes__attribute__slug=attr_slug)
                    if self.is_alias:
                        if isinstance(value, dict):
                            self.queryset = self.queryset.filter(query)
                    else:
                        self.queryset_filtered = self.queryset_filtered.filter(query)

                self.actived["num_attributes"][attr_slug] = str(min_value) + "-" + str(max_value)

    def serialize_dict_attr(self, attr):
        """ Получение всех значений словарного атрибута  """
        if attr.slug == 'brand':
            values = self.queryset.filter(brand__isnull=False) \
                .annotate(uid=Concat(V(attr.slug), V('_'), F('brand__slug'), output_field=CharField())) \
                .order_by('brand__title').distinct('brand__title').values_list('brand__slug', 'brand__title', 'uid')
        elif attr.slug == 'stock':
            values = [
                ['inStock', 'В наличии', 'stock__in'],
                ['akcii', 'По акции', 'stock__akcii'],
            ]
        else:
            concat_value_id = Concat(V(attr.slug), V('_'), F('value_dict__slug'),
                                     output_field=CharField())
            values = attr.attribute_values \
                .annotate(value_id=concat_value_id) \
                .filter(product__in=self.queryset) \
                .order_by('value_dict_id').distinct('value_dict_id') \
                .values_list('value_dict__slug', 'value_dict__value', 'value_id')
            values = sorted(list(values), key=lambda x: x[1])
        if values:
            return {'title': attr.title,
                    'name': attr.slug,
                    'type': attr.type,
                    'active': not attr.is_collapsed,
                    'id': attr.id,
                    'values': list(values)}
        else:
            return {}

    def _serialize_number_attr(self, attr, min_v, max_v):
        if min_v == max_v:
            return {}
        return {'title': attr.title,
                'name': attr.slug,
                'type': attr.type,
                'slug': attr.slug,
                'active': not attr.is_collapsed,
                'id': attr.id,
                'min': '{0:g}'.format(float(min_v)),
                'max': '{0:g}'.format(float(max_v))}
