from django.http import Http404
from django.db.models import Count, Q
from django.http import JsonResponse
from django.template.loader import get_template
from django.views.generic import FormView, TemplateView

from apps.commons.mixins import AjaxableResponseMixin, ContextPageMixin, AlertMixin
from .forms import CompareProductForm
from .models import get_compare
from ..catalog.models import Product, ProductAttribute, Category
from ..pages.models import Page


class CompareTemplateView(ContextPageMixin, AlertMixin, TemplateView):
    template_name = 'compare/compare.html'
    compare = None
    ids = []
    page = Page.TemplateChoice.COMPARE

    def dispatch(self, request, *args, **kwargs):
        self.compare = get_compare(self.request)
        self.ids = [item.product.id for item in self.compare.items()]
        return super(CompareTemplateView, self).dispatch(request, *args, **kwargs)

    def get_items(self, category=None):
        items = Product.objects.filter(id__in=self.ids)
        if category:
            items = items.filter(category=category)
        return items

    @staticmethod
    def get_attrs(items):
        """Получение атрибутов по продуктам"""
        # Генерируем словарь с атрибутами
        attrs = dict((item, []) for item in ProductAttribute.objects
                     .filter(attribute_values__product__in=items)
                     .distinct()
                     .values_list('title', flat=True))
        for item in items:
            groups = item.product_attributes.values_list(
                'attribute__title',
                'value_dict__value',
                'value_number'
            )

            groups = {item[0]: {'value': item[1] or item[2]} for item in groups}
            for attr, values in attrs.items():
                group_line = groups.get(attr)
                if group_line:
                    attrs[attr] += [group_line.get('value')]
                else:
                    # Дефолтное значение, если у товара нет атрибута
                    attrs[attr] += ['-']
        return attrs

    def get_category(self):
        category_id = self.request.GET.get('category') or 'all'
        if category_id == 'all':
            return None
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            category = None
        return category

    def get_context_data(self, **kwargs):
        context = super(CompareTemplateView, self).get_context_data(**kwargs)
        if self.request.GET.get('clear') == 'on':
            self.compare.clear()
            context['body'] = self.get_empty_compare()
            context['categories'] = ''
        else:
            category = self.get_category()
            items = self.get_items(category)
            context['category'] = category
            context['items'] = items
            context['quantity'] = len(self.ids)
            context['compare_categories'] = Category.objects \
                .filter(products__id__in=self.ids) \
                .annotate(
                counter=Count(
                    'products',
                    filter=Q(products__id__in=self.ids)
                )
            ) \
                .distinct()
            context['attrs'] = self.get_attrs(items)
            context['categories'] = get_template('compare/includes/categories.html').render({
                'categories': context['compare_categories'],
                'quantity': context['quantity'],
                'current_category': context['category'],
            })
            if items:
                context['body'] = get_template('compare/includes/body.html').render({
                    'items': '\n'.join(
                        [get_template('catalog/product_card.html').render({
                            'product': product,
                            'actions': 'trash',
                            # не представляю как сделать выбор вариации, если все обновляется аяксом,
                            # а на мобильной версии еще и два слайдера
                            # 'option': product.parent if product.parent else '',
                        })
                            for product in context['items']]
                    ),
                    'attrs': context['attrs'],
                })
            else:
                context['body'] = self.get_empty_compare()
                context['categories'] = ''
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.is_ajax():
            return JsonResponse({
                'categories': context.get('categories'),
                'body': context.get('body'),
            })
        return super(CompareTemplateView, self).render_to_response(context, **response_kwargs)


class ToggleCompareFormView(AjaxableResponseMixin, FormView):
    """
    Добавление товара в корзину 
    """
    form_class = CompareProductForm
    message_success = "Элемент сравнения успешно изменен"

    def form_valid(self, form):
        self.compare = get_compare(self.request)
        self.compare.toggle(**form.cleaned_data)
        self.extra_response_data = {'count': self.compare.count}
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        raise Http404