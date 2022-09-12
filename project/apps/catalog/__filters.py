import re
from abc import ABC, abstractmethod
from django.db.models import Q, Count, Min, Max
from django.db.models.query import QuerySet

from . import models as catalog_models


class ProductFilterBase(ABC):
    """
    Базовый классФильтрация товаров по атрибутам

    CONST_FILTERS - список фильтров, параметры которых известны заранее
    ORDERINGS - список ключей доступных для сортировки
    ORDERING_NAME - название GET-параметра сортировки
    SEARCH_NAME - название GET-параметра поиска
    SEARCH_LEN_MIN - минимальное количество символов поискового запроса
    SEARCH_LEN_MAX - максимальное количество символов поискового запроса
    PRICE_NAME - название GET-параметра цены

    queryset - кверисет который надо отфильтровать
    queryset_filtered - отфильтрованный кверисет
    request - объект запроса
    actived - словарь активных фильтров


    Примечание:
     В большинстве методов фильтрации происходит добавление их в активные.
     (self.actived[name] = value)
     Это можно вынести в отдельный метод, дабы код был чище,
     но так возникнет дублирование некоторого функционала
     и уже лень с этим заморачиваться
    """
    CONST_FILTERS = (
        # ('hit', {"hit": True}),
        # ('new', {}),
        ('stock', {"stock__gt": 0}),
        ('sale', {"old_price__gt": 0}),
        ('image', {"image__gt": 0}),
    )

    ORDERINGS = ('title', '-title', 'price', '-price')
    ORDERING_NAME = 'sort'
    ORDERING_DEFAULT = None

    SEARCH_NAME = 'search'
    SEARCH_LEN_MIN = 0
    SEARCH_LEN_MAX = 80

    PRICE_NAME = 'price'

    queryset_filtered = None

    @abstractmethod
    def __init__(self, queryset: QuerySet, request):
        self.queryset = queryset
        self.request = request
        self.query_string = self.request.META['QUERY_STRING']
        self.GET = self.request.GET
        self.init_actived()

    def init_active_filters(self):
        self.actived = {
            "dict": dict(),
            "num_attributes": set(),
            self.SEARCH_NAME: None,
            self.PRICE_NAME: None,
            self.ORDERING_NAME: None,
        }
        self.actived.update({cf: None for cf in self.CONST_FILTERS})

    @staticmethod
    def clear_number(value: str) -> int:
        """ Очистка числовых значений от лишних символов """
        try:
            value = int(value.replace(' ', ''))
        except ValueError:
            value = 0
        return value

    @staticmethod
    def clear_number_regex(value: str):
        """
        Очистка числовых значений от лишних символов
        c использованием регулярного выражения
        """
        try:
            value = int(re.sub(r'[^0-9.]+', r'', value))
        except ValueError:
            value = 0
        return value

    def filter_price(self):
        """ Фильтрация по цене """
        price = self.GET.get(self.PRICE_NAME)
        if price is not None:
            price_min, price_max = self.NUM_VALUE_PATTERN.match(
                price).group(1, 2)
            price_query = Q()
            if price_min:
                price_min = self.clear_number(price_min)
                price_query = price_query & Q(
                    price__gte=price_min)
            if price_max:
                price_max = self.clear_number(price_max)
                price_query = price_query & Q(
                    price__lte=price_max)
            if price_query:
                self.queryset_filtered = self.queryset_filtered.filter(
                    price_query)
            # set_actived
            if price_min and price_max:
                self.actived[self.PRICE_NAME] = f"{price_min}-{price_max}"

    def get_price(self):
        aggregate = self.queryset.aggregate(
            min_price=Min(self.PRICE_NAME),
            max_price=Max(self.PRICE_NAME))

        price = f"{aggregate['min_price']}-{aggregate['max_price']}"
        return {
            self.PRICE_NAME: price
        }

    def get_const(self):
        """
        Получаем значения статичных фильтров

        Для проверки нескольких значений одним запросом используется
        агрегация в виде:
            queryset.aggregate(hit=Count("id",filter=Q(hit=True)))
            где hit - название статичного фильтра
            hit=True условие этого фильтра
        """
        result = {}
        result.update(self.get_price())
        aggregate_query = {}
        # постфикс нужен на случай когда имя зарезервировано и выдаст ошибку
        postfix = "_agg"
        for title, query in self.CONST_FILTERS:
            aggregate_query[title + postfix] = Count("id", filter=Q(**query))
        aggregate = self.queryset.aggregate(**aggregate_query)
        for title, _ in self.CONST_FILTERS:
            result[title] = aggregate[title + postfix]
        return result

    def set_sort(self):
        """ Применение сортировки к кверисету """

        ordering_param = self.GET.get(self.ORDERING_NAME)
        if ordering_param is not None and ordering_param in self.ORDERINGS:
            order_by = ordering_param
        elif self.ORDERING_DEFAULT is not None:
            order_by = self.ORDERING_DEFAULT
        else:
            return
        self.queryset_filtered.order_by(order_by)
        # set_actived
        self.actived[self.ORDERING_NAME] = order_by

    def set_search(self):
        """ Примение поиска """
        question = self.GET.get(self.SEARCH_NAME)
        if question is not None:
            length = len(question)
            if length > self.SEARCH_LEN_MIN and length < self.SEARCH_LEN_MAX:
                self.queryset_filtered = self.queryset_filtered.filter(
                    Q(title__icontains=question) | Q(slug__icontains=question)
                )
            # set actived
            self.actived[self.SEARCH_NAME] = question[:self.SEARCH_LEN_MAX]

    @abstractmethod
    def filter(self):
        pass

    @abstractmethod
    def get_filters(self):
        pass


class ProductFilter(ProductFilterBase):
    """
    Фильтрация товаров по атрибутам с использованием id атрибутов.

    DICT_PATTERN - паттерн для поиска словарных фильтров в строке запроса
    NUM_VALUE_STRING_PATTERN - нескомпилированный паттерн для числового
                               значения вынесен отдельно в строку,
                               т.к использован в двух местах
    NUM_VALUE_PATTERN - скомпилированный паттерн для числового значения
    NUM_PATTERN - паттерн для поиска числовых фильтров в строке запроса

    queryset - кверисет который надо отфильтровать
    queryset_filtered - отфильтрованный кверисет
    request - объект запроса

    Строка запроса должна иметь тип: ?num_10=100-200&dict_15=26&price=0-300
    где:
     num_10=100-200 - числовой атрибут num_{ид_атрибута}={мин}-{макс}
     dict_15=26 - словарный атрибут dict_{ид_атрибута}={ид_значения}
     price=0-300 - числовые поля модели {имя}={мин}-{макс}или{значение}
     hit=on - статичные фильтры
    """

    DICT_PATTERN = re.compile('dict_(\d+)=(\d+)')
    NUM_VALUE_STRING_PATTERN = '(\d*)-(\d*)'
    NUM_VALUE_PATTERN = re.compile(NUM_VALUE_STRING_PATTERN)
    NUM_PATTERN = re.compile(f'num_(\d+)={NUM_VALUE_STRING_PATTERN}')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def filter_dict(self):
        """ Фильтрация по словарным атрибутам """
        def add_to_actived(attr, value):
            """ Добавление в активные """
            if not attr_id in self.actived['dict']:
                self.actived['dict'][attr_id] = []
            self.actived['dict'][attr_id].append(value_id)

        parameters = self.DICT_PATTERN.findall(self.query_string)
        for attr_id, value_id in parameters:
            self.queryset_filtered = self.queryset_filtered.filter(
                Q(product_attributes__attribute_id=attr_id) &
                Q(product_attributes__value_dict_id=value_id))
            # set actived
            add_to_actived(attr_id, value_id)

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

    def filter_const(self):
        """ Фильтрация по статичным фильтрам """
        for title, query in self.CONST_FILTERS:
            if self.GET.get(title) == "on":
                self.queryset_filtered = self.queryset_filtered.filter(**query)
                # set actived
                # self.actived[title] = True
        self.filter_price()

    def filter(self) -> QuerySet:
        self.queryset_filtered = self.queryset
        self.filter_dict()
        self.filter_num()
        self.filter_const()
        self.set_search()
        self.set_sort()
        return self.queryset_filtered

    def get_attr_filters(self):
        """ Получение фильтров динамических атрибутов """
        def serialize_dict_attr(attr):
            """ Получение всех значений словарного атрибута  """
            values = attr.attribute_values.filter(
                product__in=self.queryset).order_by('value_dict_id').distinct(
                    'value_dict_id').values('value_dict_id',
                                            'value_dict__value')
            return {'title': attr.title,
                    'type': attr.type,
                    'id': attr.id,
                    'values': list(values)}

        def serialize_number_attr(attr):
            """ Получение мин и макс значений числового атрибута """
            aggregate = attr.attribute_values.filter(
                product__in=self.queryset, value_number__isnull=False
            ).aggregate(min_value=Min("value_number"),
                        max_value=Max("value_number"))

            return {'title': attr.title,
                    'type': attr.type,
                    'id': attr.id,
                    'min': aggregate['min_value'],
                    'max': aggregate['max_value']}

        # получаем все атрибуты
        attributes = catalog_models.ProductAttribute.objects.filter(
            attribute_values__product__in=self.queryset).distinct()
        dict_attrs = []
        number_attrs = []
        # в зависимости от типа атрибута сериализуем его
        for attr in attributes:
            if attr.type == attr.DICT:
                dict_attrs.append(serialize_dict_attr(attr))
            elif attr.type == attr.NUMBER:
                number_attrs.append(serialize_number_attr(attr))

        attrs_serialized = {
            'dict_attrs': dict_attrs,
            'number_attrs': number_attrs,
        }
        return attrs_serialized

    def get_filters(self):
        """ Получение фильтров в сериализованном формате """

        data = {}
        data.update(self.get_const())
        data.update(self.get_attr_filters())
        print(data)

        return data
