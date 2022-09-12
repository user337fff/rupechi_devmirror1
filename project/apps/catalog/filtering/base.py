import re
from abc import ABC, abstractmethod

from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Q, Count, F, Min, Max, Value as V, When, Case, Subquery, OuterRef
from django.db.models.functions import Concat
from django.db.models.query import Prefetch, QuerySet

from .. import models as catalog_models
from ..models import get_contractor


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

    NUM_VALUE_STRING_PATTERN - нескомпилированный паттерн для числового
                               значения вынесен отдельно в строку,
                               т.к использован в двух местах
    NUM_VALUE_PATTERN - скомпилированный паттерн для числового значения


    queryset - кверисет который надо отфильтровать
    queryset_filtered - отфильтрованный кверисет
    serialized_filters - сериализованные фильтры в виде словаря
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

    NUM_VALUE_STRING_PATTERN = '([\d\.]*)-([\d\.]*)'
    NUM_VALUE_PATTERN = re.compile(NUM_VALUE_STRING_PATTERN)

    queryset_filtered = None
    serialized_filters = None
    rank = False

    @abstractmethod
    def __init__(self, queryset: QuerySet, request, **kwargs):
        self.queryset = queryset
        ids = list(queryset.values_list('id', flat=True))
        self.queryset = catalog_models.Product.objects \
            .filter(Q(domain__exact=request.domain) | Q(variations__domain__exact=request.domain)) \
            .filter(Q(id__in=ids) | Q(parent_id__in=ids)) \
            .distinct()
        self.request = request
        self.GET = self.request.GET
        self.alias_filters = {}
        category = self.GET.get('category')
        self.alias_query = ''
        self.brand = None
        self.is_alias = False
        self.alias = kwargs.get('alias')
        if category or self.alias:
            # проверка на производителя
            if '/brands/' in self.request.path:
                self.brand = catalog_models.Brand.objects.filter(slug=category).first()
                self.category = None
            else:
                self.category = self.alias or catalog_models.Catalog.objects \
                    .filter(slugs__slug=category, slugs__domain=self.request.domain).first()
            if self.alias:
                self.alias_query = self.category.search
                self.is_alias = True
                # Сборка фильтров из алиаса, чтобы по нему сразу же отсеить продукты
                for attr in self.category.alias_attrs.select_related('attribute').iterator():
                    if values := attr.value.all():
                        self.alias_filters[attr.attribute.slug] = list(values.values_list('slug', flat=True))
                    else:
                        self.alias_filters[attr.attribute.slug] = {}
                        if attr.min_value:
                            self.alias_filters[attr.attribute.slug]['min'] = attr.min_value
                        if attr.max_value:
                            self.alias_filters[attr.attribute.slug]['max'] = attr.max_value
                if brands := self.category.brands.all():
                    self.alias_filters['brand'] = list(brands.values_list('slug', flat=True))

        else:
            self.category = None

        self.init_actived()

    def init_actived(self):
        """
        Создание словаря для хранения активных атрибутов

        dict хранит в себе список активных пар атрибут-значение в формате:
            ['{ид_атрибута}_{ид_значения}',]
        """
        self.actived = {
            "dict": list(),
            "num_attributes": dict(),
            self.SEARCH_NAME: None,
            self.PRICE_NAME: None,
            self.ORDERING_NAME: None,
        }
        self.actived.update({cf[0]: None for cf in self.CONST_FILTERS})

    @staticmethod
    def clear_number(value: str) -> int:
        """ Очистка числовых значений от лишних символов """
        try:
            value = float(value.replace(' ', ''))
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

    def filter(self) -> QuerySet:
        """
        Фильтрация кверисета по строке запроса
        """
        # если это алиас то сразу отфильтровать запрос
        if self.is_alias:
            self.filter_dict()
            self.filter_num()
            self.filter_const()
            self.set_search()
            self.is_alias = False
            ids = list(self.queryset.values_list('id', flat=True))
            self.queryset = catalog_models.Product.objects \
                .filter(Q(variations__id__in=ids) | Q(id__in=ids) | Q(parent__id__in=ids)) \
                .distinct()
        self.queryset_filtered = self.queryset
        self.filter_dict()
        self.filter_num()
        self.filter_const()
        self.set_search()
        order_by = self.set_sort()
        # Если сортировки нет, и есть ранг ( ранг строится из поиска ), то сортируем по нему иначе айдишник
        if order_by is None:
            order_by = '-rank' if self.rank else 'id'
        ids = list(self.queryset_filtered.values_list('id', flat=True))
        # Ну грубо говоря исключаем вариации заменяя родительским товаром
        response = catalog_models.Product.objects \
            .filter(Q(variations__id__in=ids) | Q(parent__isnull=True, id__in=ids))
        if self.rank:
            # так как строится новый запрос нужно передать ранг чтобы по нему отсортировать
            response = response.annotate(rank=Subquery(self.queryset_filtered.filter(id=OuterRef('id')).values('rank')))
        if order_by in '-price':
            # если сортировка по цене то добавляем поле price по которому будет сортировать
            response = response.annotate(
                price=Min('prices__price' + get_contractor(self.request),
                          filter=Q(prices__domain=self.request.domain))
            )
        return response.distinct().order_by(order_by)

    def filter_price(self, price=None):
        """ Фильтрация по цене """
        if price is not None:
            match = self.NUM_VALUE_PATTERN.match(price)
            if match:
                price_min, price_max = match.group(1, 2)
            else:
                price_min = price
                price_max = ''
            line = f'prices__{self.PRICE_NAME}{get_contractor(self.request)}'
            price_query = Q()
            if price_min:
                price_query = price_query & Q(
                    **{f'{line}__gte': float(price_min), 'prices__domain': self.request.domain})
            if price_max:
                price_query = price_query & Q(
                    **{f'{line}__lte': float(price_max), 'prices__domain': self.request.domain})
            if price_query:
                if self.is_alias:
                    self.queryset = self.queryset.filter(price_query)
                else:
                    self.queryset_filtered = self.queryset_filtered.filter(price_query)
            # set_actived
            if price_min or price_max:
                self.actived[self.PRICE_NAME] = {
                    'min': price_min or 0,
                    'max': price_max or ''
                }

    def filter_const(self):
        """ Фильтрация по статичным фильтрам """
        for title, query in self.CONST_FILTERS:
            if self.GET.get(title) == "on":
                if self.is_alias:
                    self.queryset = self.queryset.filter(**query)
                else:
                    self.queryset_filtered = self.queryset_filtered.filter(**query)
                # set actived
                self.actived[title] = True
        self.filter_price()

    def get_actived(self):
        return self.actived

    def get_price(self):
        contractor = get_contractor(self.request)
        line = f'prices__{self.PRICE_NAME}{contractor}'
        aggregate = self.queryset.aggregate(
            min_price=Min(line, filter=Q(prices__domain=self.request.domain)),
            max_price=Max(line, filter=Q(prices__domain=self.request.domain))
        )
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

        В случае если данный метод работает неэффективно
         можно разделить на несколько запросов следующего формата:
         self.queryset.filter(const_param=query).exists()
        """
        result = {}
        result.update(self.get_price())
        aggregate_query = {}
        # постфикс нужен на случай когда имя зарезервировано и выдаст ошибку
        postfix = "_agg"
        for title, query in self.CONST_FILTERS:
            # собираем параметры запроса на агрегацию
            aggregate_query[title + postfix] = Count("id", filter=Q(**query))
        # посылаем запрос на а
        aggregate = self.queryset.aggregate(**aggregate_query)
        for title, _ in self.CONST_FILTERS:
            result[title] = aggregate[title + postfix]
        return result

    def get_attr_filters(self):
        """ Получение фильтров динамических атрибутов

        Схема слегка ебнутая, но по запросам к бд должна быть оптимальной

        Получаем одним запросом атрибуты товаров всех типов
        и префетчим к ним значения словарных атрибутов.
        Если атрибут словарный, то его сразу же сериализуем.
        Если числовой, то его добавляем в список
        """
        # выражение для объединения ид атрибута и значения в строку на уровне бд
        concat_uid = Concat(F('id'), V('_'), F('value_dict_id'))
        # значения атрибутов для класса Prefetch
        prefetch_values_queryset = (
            catalog_models
                .AttributeProducValue
                .objects
                .annotate(uid=concat_uid)
                .filter(product__in=self.queryset)
                .select_related('value_dict')
                .order_by('value_dict')
        )

        prefetch_values = Prefetch('attribute_values',
                                   prefetch_values_queryset)
        # получаем атрибуты совместно с их значениями
        additional_filters = {}
        if self.category:
            additional_filters['category_attrs__category'] = self.category
            # Если это категория то берет атрибуты входящие в эту категорию
            order_by = ['category_attrs__sort']
        else:
            additional_filters['category_attrs__in'] = catalog_models.CategoryAttribute.objects \
                .filter(category=None)
            # Если же это не категория, то берем атрибуты без категорий
            order_by = ['category_attrs__sort']
        # Получаем атрибуты
        '''Если это страница производителя, то выбираем только те атрибуты, 
           у которых чекнуто "Отображать в производителях", если таковых нет,
           то достаем атрибуты как для стандартного каталога'''
        if catalog_models.ProductAttribute.objects.filter(visible_on_brand=True) and self.brand:
            attributes = (
                catalog_models
                    .ProductAttribute
                    .objects
                    .filter(visible_on_brand=True)
                    .order_by('brand_position')
            )
        else:
            attributes = (
                catalog_models
                    .ProductAttribute
                    .objects
                    .prefetch_related(prefetch_values)
                    .filter(**additional_filters)
                    .filter(
                    Q(attribute_values__product__in=self.queryset)
                    | Q(slug__in=[catalog_models.SLUG_PRICE, 'brand', 'stock'])
                )
                    .order_by(*order_by)
                    .distinct()
            )
        # список всех сериализованных атрибутов
        attrs_serialized = {}
        # список инстансов числовых атрибутов для последующей агрегации
        attrs_number = {}
        # attributes = sorted(set(list(attributes)), key=lambda x: x.category_attrs.all()[0].sort)
        # в зависимости от типа атрибута сериализуем его
        distinct_attr = []
        for index, attr in enumerate(attributes):
            if attr not in distinct_attr:
                if attr.type == attr.DICT:
                    attrs_serialized[index] = self.serialize_dict_attr(attr)
                elif attr.type == attr.NUMBER:
                    attrs_number[index] = attr
                distinct_attr.append(attr)

        if len(attrs_number) == 1:
            index, attr = tuple(attrs_number.items())[0]
            attrs_serialized[index] = self.serialize_number_attr(attr)
        # если количество числовых атрибутов больше 2, то идем в другую функцию в целях оптимизации
        elif len(attrs_number) > 1:
            attrs_serialized.update(self.serialize_number_attrs(attrs_number))
        # Проверка на пустоту
        # p.s: выглядит как говно кстати
        empty = True
        for attr, value in attrs_serialized.items():
            if value:
                empty = False
                break
        return {'attrs': [v for k, v in sorted(attrs_serialized.items(), key=lambda f: int(f[0]))], 'empty': empty}

    def get_filters(self):
        """ Получение фильтров в сериализованном формате """
        if self.serialized_filters is None:
            self.serialized_filters = {}
            self.serialized_filters.update(self.get_attr_filters())
        return self.serialized_filters

    def serialize_number_attrs(self, attrs):
        """
        Сериализация числовых атрибутов
        Нахождение мин. и макс. значений числовых с последующей сериализацией
        Применяем агрегатные функции с filter т.е. Min('value', filter=Q())

        !!! Так как внутри Min/Max присутствует filter,
         данный метод будет иметь практический смысл если атрибутов 2 и более.
         В случае одного использовать метод serialize_number_attr

        """
        # именованные аргументы агрегации
        query_kwargs = {}
        price_agg = {}
        for attr in attrs.values():
            # наполняем именованные агрументы агрегирующими функциями
            # с доп фильтрацией по ид атрибута
            if attr.slug == catalog_models.SLUG_PRICE:
                min_value, max_value = self.get_price().get('price').split('-')
                price_agg = {
                    f'min_value_{attr.id}': min_value,
                    f'max_value_{attr.id}': max_value,
                }
            else:
                query_kwargs[f'min_value_{attr.id}'] = Min(
                    'value_number',
                    filter=Q(attribute_id=attr.id))
                query_kwargs[f'max_value_{attr.id}'] = Max(
                    'value_number',
                    filter=Q(attribute_id=attr.id))
            attr_agg = catalog_models \
                .AttributeProducValue.objects \
                .filter(attribute_id__in=[a.id for a in attrs.values()], product__in=self.queryset) \
                .aggregate(**query_kwargs)

            attr_agg.update(price_agg)
        # сериализация
        return {index: self._serialize_number_attr(
            attr,
            attr_agg[f'min_value_{attr.id}'],
            attr_agg[f'max_value_{attr.id}']
        )
            for index, attr in attrs.items()}

    def serialize_number_attr(self, attr):
        """ Получение мин и макс значений числового атрибута """
        if attr.slug == catalog_models.SLUG_PRICE:
            price = self.get_price().get('price', '')
            min_value, max_value = price.split('-')
            aggregate = {
                'min_value': min_value,
                'max_value': max_value,
            }
        else:
            aggregate = attr.attribute_values.filter(
                product__in=self.queryset, value_number__isnull=False
            ).aggregate(min_value=Min("value_number"),
                        max_value=Max("value_number"))

        return self._serialize_number_attr(
            attr,
            aggregate['min_value'],
            aggregate['max_value'])

    def _serialize_number_attr(self, attr, min_v, max_v):
        # нет смысла от числового атрибута у которого значения мин и макса идентичны
        if min_v == max_v:
            return {}
        return {'title': attr.title,
                'name': f'num_{attr.id}',
                'type': attr.type,
                'slug': attr.slug,
                'active': not attr.is_collapsed,
                'id': attr.id,
                'min': '{0:g}'.format(float(min_v)),
                'max': '{0:g}'.format(float(max_v))}

    def set_sort(self):
        """ Применение сортировки к кверисету """
        ordering_param = self.GET.get(self.ORDERING_NAME)
        if ordering_param is not None and ordering_param in self.ORDERINGS:
            order_by = ordering_param
        elif self.ORDERING_DEFAULT is not None:
            order_by = self.ORDERING_DEFAULT
        else:
            return
        if self.PRICE_NAME in order_by:
            self.queryset_filtered = self.queryset_filtered \
                .annotate(
                    price=Min('prices__price' + get_contractor(self.request),
                              filter=Q(prices__domain=self.request.domain))
                )
            # self.queryset_filtered = sorted(list(self.queryset_filtered), key=lambda x: x.get_storage_info()['price'])
        # else:
        self.queryset_filtered = self.queryset_filtered.order_by(order_by)
        # set_actived
        self.actived[self.ORDERING_NAME] = order_by
        return order_by

    def filtered_search(self, qs, search=''):
        search_vector = SearchVector('title', 'keywords', 'brand__title')
        qs = qs.annotate(search=search_vector, rank=SearchRank(search_vector, SearchQuery(search))) \
            .filter(
            Q(title__icontains=search)
            | Q(search=search)
            | Q(parent__title__icontains=search)
            | Q(brand__title=search)
        ).order_by('-rank')
        return qs

    def set_search(self):
        """ Примение поиска """
        question = self.GET.get(self.SEARCH_NAME) or self.GET.get('q') or self.alias_query
        if question is not None:
            length = len(question)
            if self.SEARCH_LEN_MIN < length < self.SEARCH_LEN_MAX:
                if self.alias_query:
                    self.queryset = self.filtered_search(self.queryset, self.alias_query)
                else:
                    self.queryset_filtered = self.filtered_search(self.queryset_filtered, question)
                    self.rank = True
            # set actived
            self.actived[self.SEARCH_NAME] = question[:self.SEARCH_LEN_MAX]

    @abstractmethod
    def serialize_dict_attr(self, attr):
        pass

    @abstractmethod
    def filter_dict(self):
        pass

    @abstractmethod
    def filter_num(self):
        pass
