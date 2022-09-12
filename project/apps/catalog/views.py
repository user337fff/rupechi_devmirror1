import os
from apps.pages.models import BasePage
from apps.configuration.models import Settings
from apps.stores.models import Store, StoreProductQuantity
import system.settings as ProjectSettings

from django.contrib.postgres.search import SearchVector, SearchRank, SearchQuery
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.db.models import Prefetch, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string, get_template
from django.urls import reverse
from django.views.generic import DetailView, RedirectView, TemplateView
from django.views.generic.base import View
from django.views.generic.edit import ProcessFormView
from django.http import HttpResponseNotFound, HttpResponse

from .filtering import ProductFilterSEF
from .mixins import TypeViewMixin, AjaxProductListView
from .models import Product, Category, Brand, Catalog, AttributeProducValue, Rating, ProductAttribute
from ..commons.mixins import ContextPageMixin, StaticPageMixin
from ..configuration.models import Settings
from ..domains.middleware import get_request
from ..stores.models import StoreProductQuantity


def get_slider(products, **kwargs):
    return get_template('catalog/includes/slider.html').render({
        'products': products.prefetch_related(
            Prefetch('product_attributes',
                     queryset=AttributeProducValue.objects.select_related('attribute', 'value_dict')),
            Prefetch('quantity_stores', queryset=StoreProductQuantity.objects.all())
        ).all()[:9], **kwargs
    })


def RedirectEndSlash(request, **kwargs):
    return redirect(reverse('product', kwargs=kwargs))


class CatalogTemplateView(ContextPageMixin, TemplateView):
    template_name = 'catalog/catalog.html'
    page = BasePage.TemplateChoice.CATALOG

    def get_context_data(self, *args, **kwargs):
        context = super(CatalogTemplateView, self).get_context_data(*args, **kwargs)
        context['catalog'], _ = Category.get_catalog()
        return context


class SaleView(ContextPageMixin, DetailView):
    model = Product
    template_name = 'catalog/category.html'
    page = BasePage.TemplateChoice.SALE
    object = None

    def get_object(self, queryset=None):
        return None


class CategoryDetailView(TypeViewMixin, DetailView):
    template_name = "catalog/category.html"
    template_name_products = "catalog/product_cards.html"
    context_object_name = 'category'
    model = Catalog
    queryset = model.objects.filter(is_active=True)
    object = None

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object:
            raise Http404
        parent = self.object
        while not parent.is_active:
            parent = parent.parent
            if parent is None:
                return redirect(reverse('catalog'))
        else:
            if self.object != parent:
                print('category redirect', self.object, parent, parent.get_absolute_url())
                return redirect(parent.get_absolute_url())
        return super(CategoryDetailView, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        slugs = []
        for slug in self.kwargs.get('slug').split('/'):
            if slug == 'f':
                break
            slugs += [slug]
        slug = slugs[-1].split('/')[-1]
        if not self.object:
            self.object = self.model.objects. \
                filter(slugs__slug=slug, slugs__domain=self.request.domain, domain__exact=self.request.domain).first()
        if self.object is None:
            print('*** HTTP EXCEPT 404', 'apps/catalog/views 84', slug, self.request.domain, slugs)
        return self.object

    def get_related_categories(self):
        """Получение связанных категорий"""
        show_aliases = Catalog.objects.filter(Q(domain=self.domain) & Q(show_on_menu=True) & \
                                              Q(show_on_categories__pk=self.pk) & Q(is_active=True) & \
                                              ~Q(parent__pk__in=self.pk))
        children = list(self.get_object().get_children().exclude(Q(show_on_menu=True) & \
                                                                 Q(parent__pk=self.pk)).filter(
            domain=self.domain)) + list(show_aliases)
        siblings = list(self.get_object().get_siblings(include_self=True).filter(domain=self.domain)) + list(
            show_aliases)
        return children if children else siblings

    def get_context_data(self, **kwargs):
        """
        Получение контекста для обычного запроса
        """
        context = super().get_context_data(**kwargs)
        # context['related_categories'] = self.get_related_categories()

        # если гет параметров нет или есть один с номером страницы
        # то отображаем кешированные товары первой страницы
        products = self.object.get_fpp()
        if (not self.request.GET or
                (len(self.request.GET) == 1 and
                 self.request.GET.get('page') == '1')):
            user_contractor = self.request.user.contractor if not isinstance(self.request.user, AnonymousUser) else None
            context['products'] = cache.get(f'render_to_string_{self.request.environ["REQUEST_URI"]}-'
                                            f'{user_contractor}-{self.request.domain.domain}')
            if not context.get('products'):
                context['products'] = render_to_string(
                    template_name=self.template_name_products,
                    context={'products': products,
                             'is_table': context['is_table'],
                             'request': self.request})
                cache.set(f'render_to_string_{self.request.environ["REQUEST_URI"]}-'
                          f'{user_contractor}-{self.request.domain.domain}',
                          context['products'], 420 * 60)
        context['popular_products'] = cache.get(
            f'popular_products_for_{self.object.title}_on_{self.request.domain.domain}')
        if not context['popular_products']:
            categories = self.object.get_descendants(include_self=True)
            if self.object.type != 'alias':
                products = Product.objects.active(Q(parent__isnull=True) & Q(category__in=categories)).order_by('?')
                if products.count() < 1:
                    categories = self.object.title
                    products = Product.objects.search(categories).order_by('?')[:8]
            else:
                if isinstance(products, list):
                    products = Product.objects.active(title__in=products[:8])
            context['popular_products'] = get_slider(
                products,
                **{
                    'request': self.request,
                    'slidesToShow': 3,
                    'title': f'Популярные товары в разделе {self.object}',
                    'section': False,
                })
            cache.set(f'popular_products_for_{self.object.title}_on_{self.request.domain.domain}',
                      context['popular_products'], 420 * 60)
        context['brands'] = Brand.objects.filter(domain__exact=self.request.domain, is_active=True,
                                                 is_index=True, image__gt=0)
        context['template_filters'] = ''  # cache.get(f'template_filters_{self.object.id}') or ''
        context['content_text'] = True

        if self.request.GET.get('page'):
            try:
                if int(self.request.GET.get('page')) > 1:
                    print(f'=====PAGEEEEE {self.request.GET.get("page")}')
                    context['content_text'] = False
            except:
                context['content_text'] = False

        return context


class CategoryProductsListView(AjaxProductListView):
    """Получение товаров категории"""
    paginate_by = 15

    def get_category(self):
        category_pk = self.request.GET.get('category')
        if category_pk is not None:
            self.category = get_object_or_404(Category, pk=category_pk)
        else:
            print('*** HTTP EXCEPT 404', 'apps/catalog/models/category 136')
            return HttpResponseNotFound()
        return self.category

    def get_queryset(self):
        category = self.get_category()
        return Product.objects.active(
            category__in=category.get_descendants(include_self=True))


class SearchProductsListView(AjaxProductListView):
    paginate_by = 6
    filter_class = ProductFilterSEF

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.q = None

    """Получение товаров при поиске"""

    def get_search_query(self):
        if self.q is None:
            self.q = self.request.GET.get('q', '')
        return self.q

    def get_queryset(self, search=None):
        return super(SearchProductsListView, self).get_queryset(search=search)

    def get_filter_instance(self, queryset):
        """
        Получение объекта фильтрующего класса
        """
        self.request.path += '?q=' + self.get_search_query()
        return self.filter_class(queryset, self.request)[:self.paginate_by]

    def get_context_data(self, *args, **kwargs):
        context = super(AjaxProductListView, self).get_context_data(*args, **kwargs)
        products = context['page_obj'].object_list[:6]
        categories = Catalog.objects.filter(is_active=True, domain__exact=self.request.domain)
        search = self.get_search_query()
        search_vector = SearchVector('title', 'keywords')
        categories = categories.annotate(vector_search=search_vector) \
                         .filter(
            Q(title__icontains=search)
            | Q(vector_search=search)
            | Q(parent__title__icontains=search)
        )[:10]
        brands = Brand.objects.filter(is_active=True) \
            .filter(title__icontains=search)
        if products or categories or brands:
            return {'template': get_template('catalog/includes/search.html').render({
                'products': products, 'q': search, 'categories': categories, 'brands': brands,
            })}
        return {'template': ''}


class SearchPageView(StaticPageMixin, DetailView):
    model = Product
    template_name = 'catalog/search_page.html'
    page = BasePage.TemplateChoice.SEARCH
    object = None

    def get_object(self, queryset=None):
        return None

    def get_queryset(self):
        q = self.request.GET.get('q')
        sq = self.model.objects.search(q)
        return sq


class CategoryDetailSEF(DetailView, AjaxProductListView):
    filter_class = ProductFilterSEF
    model = Catalog
    object = None

    def get_object(self, queryset=None):
        slugs = []
        for slug in self.kwargs.get('slug').split('/'):
            if slug == 'f':
                break
            slugs += [slug]
        slug = slugs[-1].split('/')[-1]
        model = self.kwargs.get('type')
        if model == 'brands':
            self.model = Brand
            obj = self.model.objects.filter(domain__exact=self.request.domain, slug=slug).first()
        else:
            self.model = Catalog
            obj = self.model.objects.filter(domain__exact=self.request.domain,
                                            slugs__slug=slug, slugs__domain=self.request.domain).first()
        self.object = obj
        if not obj:
            return None
            # raise Http404
        return obj

    def get_queryset(self, search=None):
        domain = get_request().domain
        model = self.kwargs.get('type')
        if model == 'search':
            if search:
                text = search
                sq = Product.objects.search(text)
                return sq
            return Product.objects.active()
        elif model == 'sale':
            return Product.objects.active(prices__domain=domain) \
                .filter(Q(prices__old_price__gt=0) | Q(prices__percent__gt=0))
        else:
            obj = self.get_object()
            if not obj:
                return Product.objects.none()
            return obj.get_products()


class ProductDetail(DetailView):
    template_name = 'catalog/product.html'
    model = Product

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object:
            raise Http404
        return super(ProductDetail, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        slug = self.model.decode_slug(self.kwargs.get('slug'))
        try:
            self.object = self.get_queryset().get(slug=slug)
        except:
            print('*** HTTP EXCEPT 404', 'apps/catalog/views 265', slug, self.kwargs.get('slug'))
            raise Http404
        return self.object

    def get_queryset(self):
        self.queryset = self.model.objects.filter(domain__exact=self.request.domain)
        return self.queryset

    def get_context_data(self, **kwargs):
        context = super(ProductDetail, self).get_context_data(**kwargs)
        if not self.object:
            self.object = self.get_object()
        products = self.object.related_products.filter(parent__isnull=True, is_active=True).all()
        self.object.add_viewed_product()
        if products:
            context['product_slider'] = get_slider(products=products, **{
                'request': self.request,
                'slidesToShow': 4,
                'title': 'Вам может понадобиться',
                'btn': {
                    'href': reverse("catalog"), 'text': 'Смотреть все'
                }
            })
        products = self.object.get_similar_product(4)
        if products:
            context['related_slider'] = get_slider(products=products, **{
                'request': self.request,
                'slidesToShow': 4,
                'title': 'Похожие товары',
                'btn': {
                    'href': self.object.category.get_absolute_url(), 'text': 'Смотреть все'
                    # 'href': reverse("catalog"), 'text': 'Смотреть все'
                }
            })
        settings = Settings.get_settings()
        guarantee_attrib = ProductAttribute.objects.filter(title='Гарантия производителя').first()
        if guarantee_attrib in self.object.attributes.all():
            context['guarantee'] = AttributeProducValue.objects.filter(attribute=guarantee_attrib,
                                                                       product=self.object).first().value_dict.value\
                                                                       .replace('мес', 'месяцев')
        shops = StoreProductQuantity.objects.filter(product=self.object, store__is_active=True,
                                                    store__domain__exact=self.request.domain)
        context['quantity_stores'] = shops
        if settings and settings.attr_chimney:
            attr_first = AttributeProducValue.objects.filter(product=self.object,
                                                             attribute=settings.attr_chimney).first()
            if attr_first:
                context['diameter'] = attr_first.value
        referer = self.request.META.get('HTTP_REFERER')
        if referer:
            context['referer'] = self.request.META.get('HTTP_REFERER')
        context['brands'] = Brand.objects.filter(domain__exact=self.request.domain, is_active=True,
                                                 is_index=True, image__gt=0)
        context['address_page'] = BasePage.objects \
            .filter(domain__exact=self.request.domain, is_active=True, template=BasePage.TemplateChoice.ADDRESS) \
            .first()
        if self.object.category.get_ancestors(include_self=True).filter(visible_mounting=True):
            context['mounting_page'] = BasePage.objects \
                .filter(domain__exact=self.request.domain, is_active=True, template=BasePage.TemplateChoice.MOUNTING) \
                .first()
        if viewed := self.object.get_viewed_product_list():
            context['viewed_slider'] = get_slider(viewed, title='Вы смотрели', slidesToShow=4)
        context['domain_discount'] = Settings.objects.all().order_by('id').first().discount_domain.all()
        return context


class BrandsView(StaticPageMixin):
    page = BasePage.TemplateChoice.BRANDS
    template_name = 'pages/static/brands.html'

    def get_context_data(self, *args, **kwargs):
        context = super(BrandsView, self).get_context_data(*args, **kwargs)
        context['items'] = Brand.objects.filter(is_active=True, domain__exact=self.request.domain)
        return context


class BrandDetail(DetailView):
    model = Brand
    template_name = 'catalog/category.html'

    def get_queryset(self):
        return self.model.objects.filter(domain__exact=self.request.domain, is_active=True)

    def get_object(self, queryset=None):
        slug = self.model.decode_slug(self.kwargs.get('slug').split('/f')[0])
        self.object = self.model.objects.filter(domain__exact=self.request.domain, is_active=True, slug=slug).first()
        if self.object:
            return self.object

        print('*** HTTP EXCEPT 404', 'apps/catalog/views.py 333')
        raise Http404

    def get_context_data(self, **kwargs):
        context = super(BrandDetail, self).get_context_data(**kwargs)
        context['title_prefix'] = 'Производитель '
        context['brand_get'] = '?brand=' + self.object.slug
        return context


class SetRating(ProcessFormView, View):

    def post(self, request, *args, **kwargs):
        response = {}
        product = Product.objects.filter(id=request.POST.get('product')).first()
        user = request.user
        if product and user.is_authenticated:
            star = int(request.POST.get('star', 0))
            if star:
                Rating.objects.update_or_create(product=product, user=user, defaults={'rating': star})
            else:
                Rating.objects.filter(product=product, user=user).delete()
            response = product.get_rating()
        else:
            response['errors'] = 'Авторизуйтесь'
        return JsonResponse(response)


class UnloadingPhotoView(View):

    PRODUCT_SLUG = "/images/catalog/product/import_files/"

    def get(self, request, slug):

        file_path = ProjectSettings.MEDIA_ROOT + self.PRODUCT_SLUG + slug

        print('File path', file_path)

        if(os.path.exists(file_path) and os.path.isfile(file_path)):
            mime_type = ""
            content = b""
            with open(file_path, "rb") as f:
                content = f.read()

                filename, file_extension = os.path.splitext(file_path)

                print("File extension", file_extension)

                if(file_extension in [".jpg", ".jpeg"]):
                    mime_type = "image/jpeg"
                elif(file_extension == ".png"):
                    mime_type = "image/png"

            return HttpResponse(content=content, content_type=mime_type)
        else:
            raise Http404
