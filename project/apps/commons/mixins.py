from apps.pages.models import Page
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string, get_template
from django.urls import reverse_lazy
from django.views.generic import ListView, TemplateView
from django.views.generic.base import View
from django.http.response import Http404
from django.views.generic.detail import SingleObjectMixin
from django.http import HttpResponseNotFound


class ContextPageMixin(TemplateView):
    """Добавить шаблон в apps.pages.models.TemplateChoice и url в get_absolute_url"""
    page = ''
    full_width = False
    hide_title = False
    only_seo = False

    def get_context_data(self, *args, **kwargs):
        context = super(ContextPageMixin, self).get_context_data(**kwargs)
        if self.page:
            page = Page.objects.activated(template=self.page).first()
            self.page_obj = page
            context['page'] = page
        for k in ['full_width', 'hide_title', 'only_seo']:
            context[k] = getattr(self, k, '')
        return context


class StaticPageMixin(ContextPageMixin):

    def get_context_data(self, *args, **kwargs):
        context = super(StaticPageMixin, self).get_context_data(*args, **kwargs)
        if context.get('page'):
            return context
        print('*** HTTP EXCEPT 404', 'apps/commons/mixins.py 35', context, str(self.request.domain))
        return context


class AlertMixin(View):

    @staticmethod
    def _get_template(**kwargs):
        return get_template('commons/alert.html').render(kwargs)

    def get_empty_wishlist(self):
        return self._get_template(
            title='По вашему запросу ничего не найдено',
            subtitle='Попробуйте изменить формулировку или перейдите в каталог',
            icon='cart',
            buttons=[
                {'text': 'Перейти в каталог', 'type': 'btn-primary', 'href': reverse_lazy('catalog')},
            ],
        )

    def get_empty_cart(self):
        return self._get_template(
            title="Корзина пуста",
            subtitle='В вашей корзине нет товаров',
            icon='cart',
            buttons=[
                {'text': 'Перейти в каталог', 'type': 'btn-primary', 'href': reverse_lazy('catalog')},
            ]
        )

    def get_empty_catalog(self):
        return self._get_template(
            classes='small',
            title='По вашему запросу ничего не найдено',
            subtitle='Измените формулировку поиска или фильтры',
            icon='cart',
            buttons=[
                {'text': 'Перейти в каталог', 'type': 'btn-primary', 'href': reverse_lazy('catalog')},
            ]
        )

    def get_empty_compare(self):
        return self._get_template(
            title='Нет товаров для сравнения',
            subtitle='Добавьте товар для сравнения',
            icon='cart',
            buttons=[
                {'text': 'Перейти в каталог', 'type': 'btn-primary', 'href': reverse_lazy('catalog')},
            ]
        )


class CustomListMixin(AlertMixin, TemplateView):
    """Миксин для страниц с итемами и пагинацией"""
    paginate_by = 2
    template_card_name = ''
    page_view = 4  # Количество чисел слева и справа от ...
    empty = 'wishlist'

    def get_items(self):
        return []

    def render(self, item):
        return get_template(self.template_card_name).render({'item': item})

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(self.get_items() or [], self.paginate_by)
        context['paginator'] = paginator.get_page(self.request.GET.get('page', 1))
        return context

    def render_to_response(self, context, **response_kwargs):
        items = [self.render(item) for item in context['paginator'].object_list]
        if items:
            context['items'] = '\n'.join(items)
        else:
            context['empty'] = getattr(self, f'get_empty_{self.empty}')()
        context['pagination'] = get_template('commons/pagination.html').render({
            'page_obj': context['paginator'],
            'page_view': self.page_view
        })
        if self.request.is_ajax():
            for key in set(context) - {'items', 'empty', 'pagination'}:
                del context[key]
            return JsonResponse(context)
        return super().render_to_response(context, **response_kwargs)


class JSONResponseMixin:
    """
    A mixin that can be used to render a JSON response.
    """

    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return JsonResponse(
            self.get_data(context),
            **response_kwargs
        )

    def get_data(self, context):
        """
        Returns an object that will be serialized as JSON by json.dumps().
        """
        # Note: This is *EXTREMELY* naive; in reality, you'll need
        # to do much more complex handling to ensure that arbitrary
        # objects -- such as Django model instances or querysets
        # -- can be serialized as JSON.
        return context


class AjaxableResponseMixin:
    message_success = None
    success_url = '/'
    extra_response_data = None

    def form_invalid(self, form):
        return JsonResponse({'errors': form.errors, 'success': False})

    def form_valid(self, form):
        data = {
            'success': True,
        }
        if self.extra_response_data is not None:
            data.update(self.extra_response_data)
        if self.message_success is not None:
            data['message'] = self.message_success
        return JsonResponse(data)

    def extra_data(self):
        return None


class DetailListView(ListView, SingleObjectMixin, JSONResponseMixin):
    """
    Вывод объекта и списка его элементов

    Наследование классов обязательно в таком порядке,
    т.к. в методе get_context_data вызывается метод предка
    в зависимости от аякса, при изменении пордяка питон вызовет
    метод ListView и бытие станет тщетным.
    Подробнее о правилах обхода метода super():
    https://sorokin.engineer/posts/ru/python_super.html.


    """
    paginate_by = 30
    template_name = None
    template_name_pagin = "commons/pagination.html"
    template_name_items = None
    context_items_name = 'items'
    object_queryset = None
    object = None
    _is_ajax = None

    @property
    def is_ajax(self):
        if self._is_ajax is None:
            self._is_ajax = True if self.request.GET.get('ajax') else False
        return self._is_ajax

    def get_queryset(self, search=None):
        return super(ListView, self).get_queryset(search=search)

    def get_context_items(self, default_context):
        """Контекст для рендеринга шаблона со списком элементов"""
        context = {
            self.context_items_name: default_context['page_obj']
        }
        return context

    def _get_context_data(self, **kwargs):
        """
        Получение контекста для обычного запроса
        """
        context = super(SingleObjectMixin, self).get_context_data(**kwargs)
        return context

    def _get_context_data_ajax(self, **kwargs):
        """
        Получение контекста для ajax-запроса
        """
        default_context = super().get_context_data(**kwargs)
        context = {}
        context['pagination'] = render_to_string(
            template_name=self.template_name_pagin,
            context=default_context)
        context[self.context_items_name] = render_to_string(
            template_name=self.template_name_items,
            context=self.get_context_items(default_context))

        return context

    def get_context_data(self, **kwargs):
        if not self.is_ajax:
            return self._get_context_data(**kwargs)
        else:
            return self._get_context_data_ajax(**kwargs)

    def get_object(self):
        if self.object:
            return self.object
        return super().get_object(self.object_queryset)

    def get_object_queryset(self):
        return self.object_queryset

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object_list = self.get_queryset()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def render_to_response(self, context):
        if not self.is_ajax:
            return super().render_to_response(context)
        return self.render_to_json_response(context)
