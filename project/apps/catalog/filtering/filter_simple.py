import re

from django.db.models import Q, CharField, Value as V, F
from django.db.models.functions import Concat

from .base import ProductFilterBase


class ProductFilter(ProductFilterBase):
    """
    Фильтрация товаров по атрибутам с использованием id атрибутов.

    В данной реализации ид атрибута хранится в ключе GET-параметра, 
    а значение в значении(как бы тупо не звучало).

    DICT_PATTERN - паттерн для поиска словарных фильтров в строке запроса
    NUM_PATTERN - паттерн для поиска числовых фильтров в строке запроса

    Строка запроса должна иметь тип: ?num_10=100-200&dict_15=26&price=0-300
    где:
     num_10=100-200 - числовой атрибут num_{ид_атрибута}={мин}-{макс}
     dict_15=26 - словарный атрибут dict_{ид_атрибута}={ид_значения}
     price=0-300 - числовые поля модели {имя}={мин}-{макс}или{значение}
     hit=on - статичные фильтры
    """

    DICT_PATTERN = re.compile('dict_(\d+)=(\d+)')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.NUM_PATTERN = re.compile(
            f'num_(\d+)={self.NUM_VALUE_STRING_PATTERN}')
        self.query_string = self.request.META['QUERY_STRING']

    def filter_dict(self):
        """ Фильтрация по словарным атрибутам """

        def add_to_actived(attr, value):
            """ Добавление в активные """
            if attr_id not in self.actived['dict']:
                self.actived['dict'][attr_id] = []
            self.actived['dict'][attr_id].append(value_id)

        parameters = self.DICT_PATTERN.findall(self.query_string)
        for attr_id, value_id in parameters:
            self.queryset_filtered = self.queryset_filtered.filter(
                Q(product_attributes__attribute_id=attr_id) &
                Q(product_attributes__value_dict_id=value_id))
            # set actived
            self.actived['dict'].append(f'{attr_id}_{value_id}')

    def filter_num(self):
        """ Фильтрация по числовым атрибутам """
        parameters = self.NUM_PATTERN.findall(self.query_string)
        for attr_id, min_value, max_value in parameters:
            query = Q()
            if min_value:
                min_value = self.clear_number(min_value)
                query = query & Q(
                    product_attributes__value_number__gte=min_value)
            if max_value:
                max_value = self.clear_number(max_value)
                query = query & Q(
                    product_attributes__value_number__lte=max_value)
            if query:
                query = query & Q(product_attributes__attribute_id=attr_id)
                self.queryset_filtered = self.queryset_filtered.filter(query)

                # set actived
                self.actived['num_attributes'][f"num_{attr_id}"] = f'{min_value or 0}-{max_value}'

    def serialize_dict_attr(self, attr):
        """
        Получение всех значений словарного атрибута

        concat_uid - поле для аннотации, объединяющее ид атрибута и значение
        values - список значений атрибута в формате:
            (ид_значения, значение, уникальный идентификатор)

        идентификатор нужен для однозначного определения пары атрибут-значение
        по нему определяем вхождение в список активных self.actived['dict']
        """
        concat_uid = Concat(V(attr.id), V('_'), F('value_dict_id'),
                            output_field=CharField())
        values = attr.attribute_values.annotate(uid=concat_uid).filter(
            product__in=self.queryset).order_by('value_dict_id').distinct(
            'value_dict_id').values_list('value_dict_id',
                                         'value_dict__value',
                                         'uid')
        return {'title': attr.title,
                'name': f'dict_{attr.id}',
                'active': not attr.is_collapsed,
                'type': attr.type,
                'id': attr.id,
                'values': list(values)}
