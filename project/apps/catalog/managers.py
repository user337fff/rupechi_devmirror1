# search
from django.contrib.postgres.search import (
    SearchQuery, SearchVector)
from django.db import models
from django.db.models import Q, OuterRef, Subquery
from django.db.models.query import QuerySet
from django.apps import apps

from .filtering import ProductFilter, ProductFilterSEF
from ..domains.middleware import get_request


class ProductQuerySet(QuerySet):
    """QuerySet, реализующий доп методы"""

    def active(self, *args, **kwargs) -> QuerySet:
        domain = get_request().domain
        return self.filter(is_active=True, domain__exact=domain, *args, **kwargs)

    def filtrate(self, request):
        """Стандартная фильтрация"""
        pf = ProductFilter(self, request)
        return pf.filter()

    def filtrateSEF(self, request):
        """Фильтрация с ЧПУ"""
        pf = ProductFilterSEF(self, request)
        return pf.filter()


class ProductManager(models.Manager):
    """Кастомный менеджер для товаров"""

    def get_queryset(self):
        Prices = apps.get_model('catalog', 'Prices')
        qs = ProductQuerySet(self.model).annotate(
            price=Subquery(Prices.objects.filter(Q(product=OuterRef('pk')) &
                                                 Q(domain=get_request().domain))[:1].values_list('price'),
                                                   output_field=models.DecimalField()),
            old_price=Subquery(Prices.objects.filter(Q(product=OuterRef('pk')) &
                                                     Q(domain=get_request().domain))[:1].values_list('old_price'),
                                                       output_field=models.DecimalField()),
            percent=Subquery(Prices.objects.filter(Q(product=OuterRef('pk')) &
                                                   Q(domain=get_request().domain))[:1].values_list('percent'),
                                                     output_field=models.FloatField()),
            price_1=Subquery(Prices.objects.filter(Q(product=OuterRef('pk')) &
                                                   Q(domain=get_request().domain))[:1].values_list('price_1'),
                                                     output_field=models.DecimalField()),
            price_2=Subquery(Prices.objects.filter(Q(product=OuterRef('pk')) &
                                                   Q(domain=get_request().domain))[:1].values_list('price_2'),
                                                     output_field=models.DecimalField()),
            price_3=Subquery(Prices.objects.filter(Q(product=OuterRef('pk')) &
                                                   Q(domain=get_request().domain))[:1].values_list('price_3'),
                                                     output_field=models.DecimalField()),
            search=SearchVector('title')
        )
        return qs

    def active(self, *args, **kwargs):
        """Активные товары"""
        return self.get_queryset().active(*args, **kwargs)

    def in_stock(self):
        """Товары в наличии"""
        return self.get_queryset().filter(stock__gt=0)

    def search(self, text, rank=False):
        """Поиск по товарам"""
        if text:
            text = text.strip(' \n\t').lower()
            if 'тепловъ' not in text.lower() and 'теплов' in text.lower():
                text = text.replace('теплов', 'тепловъ')
            if 'универсалъ' not in text.lower() and 'универсал' in text.lower():
                text = text.replace('универсал', 'универсалъ')
            queryset = self.get_queryset().active(Q(search=text)
                                                  | Q(title__icontains=text)
                                                  | Q(code=text)
                                                  | Q(title__startswith=text))
            # if queryset.count() < 1:
            #     text = text.split(' ')
            #     for item in text:
            #         item_query = self.get_queryset().filter(Q(title__icontains=item)
            #                                                 | Q(title__startswith=text)
            #                                                 | Q(code=item))
            #         if 500 > item_query.count() > 1:
            #             queryset = item_query
            #             break
            return queryset
        return self.model.objects.none()

    # def search(self, text, rank=False):
    #     """Поиск по товарам"""
    #     if text:
    #         text = text.strip(' \n\t')
    #         search_query = SearchQuery(text, config='russian')
    #         # полнотекстовый поиск
    #         query = Q(search_vector=search_query)
    #         # query = Q()
    #         # поиск по названию
    #         query |= Q(title__icontains=text)
    #         if ' ' not in text:
    #             # если запрос не содержит пробела, то ищем также по артикулу
    #             query |= Q(code=text)
    #         # итоговый кверисет
    #         queryset = self.get_queryset().filter(query)\
    #             .filter(search_vector=text)
    #         if rank:
    #             search_rank = SearchRank(F('search_vector'))
    #             queryset = queryset.annotate(rank=search_rank).order_by('-rank')
    #         return queryset
    #     return self.model.objects.none()

