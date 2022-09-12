from django.template.loader import render_to_string
from django.views.generic import ListView
from django.core.cache import cache
from django.contrib.auth.models import AnonymousUser

from apps.commons.mixins import JSONResponseMixin, AlertMixin
from apps.domains.middleware import get_request
from .filtering import (ProductFilter)
from .models import Product


class TypeViewMixin:
    def is_table_view(self):
        """
        Определяем выводить ли широкие карточки
        """
        return self.request.GET.get('view', 'table') == 'table'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_table'] = self.is_table_view()
        return context


class AjaxProductListView(AlertMixin, ListView, JSONResponseMixin, TypeViewMixin):
    paginate_by = 30
    template_name_filters = "catalog/includes/filters.html"
    template_name_pagin = "commons/pagination.html"
    template_name_products = "catalog/product_cards.html"

    # класс, осуществляющий фильтрацию
    filter_class = ProductFilter

    def get_queryset(self, search=None):
        if search:
            return Product.objects.search(search)
        return Product.objects.active()

    def get_paginate_by(self, queryset):
        return self.request.GET.get('paginate') or self.paginate_by

    def get_filter_instance(self, queryset):
        """
        Получение объекта фильтрующего класса
        """
        return self.filter_class(queryset, self.request)

    def get_context_filters(self):
        """
        Получение контекста для рендеринга фильтров
        """
        filters = self.filter_instance.get_filters()
        filters_actived = self.filter_instance.get_actived()
        context = {
            'filters': filters,
            'filters_actived': filters_actived
        }
        return context

    def get_context_products(self, default_context):
        """
        Получение контекста для рендеринга товаров
        """
        products = default_context["object_list"]
        if not products:
            q = self.request.GET.get('q')
            products = Product.objects.search(q)
        if sort := self.request.GET.get('sort'):
            if 'price' in sort:
                price_sort = {'price': False, '-price': True}
                reverse = price_sort[self.request.GET.get('sort')]
                products = sorted(list(products), key=lambda x: int(x.get_storage_info().get('discount_price')
                                                                    if x.get_storage_info().get('discount_price')
                                                                    else x.get_storage_info().get('price')),
                                  reverse=reverse)
        context = {'products': products, 'is_table': self.is_table_view(), 'request': self.request}
        return context

    def get_context_data(self, **kwargs):
        """
        Получение контекста для ajax-запроса
        """
        domain = self.request.domain.domain
        q = self.request.GET.get('q') or self.request.GET.get('sort')
        page = self.request.GET.get('page', 1)
        paginate_by = self.request.GET.get('paginate')
        view_by = self.request.GET.get('view')
        user_contractor = self.request.user.contractor if not isinstance(self.request.user, AnonymousUser) else None
        if not self.request.GET.get('not_filters', False) and not q:  # and cache_filters:
            print('=====CACHE TRUE')
            print("CACHE FILTERS GET", f'get-context-data-filters-for-{self.request.path}-on-{domain}-'
                                f'page={page}-contr={user_contractor}-paginate_by={paginate_by}-view_by={view_by}')
            context = cache.get(f'get-context-data-filters-for-{self.request.path}-on-{domain}-'
                                f'page={page}-contr={user_contractor}-paginate_by={paginate_by}-view_by={view_by}')
        else:
            context = None
        if not context:
            default_context = super().get_context_data(**kwargs)
            products = self.get_context_products(default_context)
            context = {
                'pagination': render_to_string(
                    template_name=self.template_name_pagin,
                    context=default_context),
                'products': render_to_string(
                    template_name=self.template_name_products,
                    context=products)
            }

            # context['template_filters'] = render_to_string(
            #         template_name=self.template_name_filters,
            #         context=self.get_context_filters())

            # Зачем рендерить каждый раз фильтры, если они не меняются
            if not self.request.GET.get('not_filters', False):
                context['template_filters'] = render_to_string(
                    template_name=self.template_name_filters,
                    context=self.get_context_filters())
            if not products['products']:
                context['empty'] = self.get_empty_catalog()

            cache.set(f'get-context-data-filters-for-{self.request.path}-on-{domain}-'
                      f'page={page}-contr={user_contractor}-paginate_by={paginate_by}-view_by={view_by}',
                      context, 7 * 3600)

        print("CONTEXT", self.get_context_filters())

        return context

    def get(self, request, *args, **kwargs):
        search_word = request.GET.get('q')
        if search_word:
            search_word = search_word.strip(' \n\t')
        self.queryset = self.get_queryset(search=search_word).filter(is_active=True)
        # инстанс фильтрующего класса
        self.filter_instance = self.filter_class(self.queryset, request)
        self.object_list = self.filter_instance.filter()
        context = self.get_context_data()
        return self.render_to_response(context)

    def render_to_response(self, context, **kwargs):
        return self.render_to_json_response(context, **kwargs)
