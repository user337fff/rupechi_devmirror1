import datetime
import pytz

from bs4 import BeautifulSoup as bs

from apps.catalog.models import Calc, Brand, Catalog, Product, AttributeProducValue, Prices
from apps.commons.mixins import CustomListMixin, ContextPageMixin, StaticPageMixin
from apps.configuration.models import IndexSlide
from apps.domains.middleware import get_request
from apps.pages.models import BasePage, Page
from apps.reviews.models import Review
from apps.stores.models import StoreProductQuantity
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.syndication.views import Feed, add_domain
from django.db.models import Prefetch, Q, Exists, OuterRef
from django.http import JsonResponse, Http404
from django.template.defaultfilters import truncatewords
from django.template.loader import get_template
from django.views.generic import TemplateView, ListView
from django.core.cache import cache
from django.utils.feedgenerator import DefaultFeed
from django.utils.xmlutils import SimplerXMLGenerator
from django.utils.translation import get_language
from django.utils.timezone import get_default_timezone, is_naive, make_aware


def get_slider(products, **kwargs):
    if products:
        return get_template('catalog/includes/slider.html').render({
            'products': products.prefetch_related(
                Prefetch('product_attributes',
                         queryset=AttributeProducValue.objects.select_related('attribute', 'value_dict')),
                Prefetch('quantity_stores', queryset=StoreProductQuantity.objects.all())
            ).all()[:9], **kwargs
        })
    return ''


class SiteMapView(StaticPageMixin):
    template_name = 'pages/static/sitemap.html'
    page = BasePage.TemplateChoice.SITEMAP

    def get_context_data(self, *args, **kwargs):
        context = super(SiteMapView, self).get_context_data(*args, **kwargs)
        context['pages'] = BasePage.objects.filter(domain__exact=self.request.domain, is_active=True,
                                                   hide_sitemap=False).all()
        context['categories'] = Catalog.objects.filter(domain__exact=self.request.domain, is_active=True).all()
        return context


class CooperationView(StaticPageMixin):
    template_name = 'pages/static/cooperation.html'
    page = BasePage.TemplateChoice.COOPERATION

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['brands'] = Brand.objects.filter(domain__exact=self.request.domain, is_active=True, is_index=True)
        context['categories'] = Catalog.objects.filter(domain__exact=self.request.domain, is_active=True).all()
        return context


class CalcView(StaticPageMixin):
    template_name = 'pages/static/calc.html'
    page = BasePage.TemplateChoice.CALCULATOR

    def get_context_data(self, *args, **kwargs):
        context = super(CalcView, self).get_context_data(*args, **kwargs)
        context['diameters'] = list(
            map(int, Calc.objects
                .order_by('diameter')
                .distinct('diameter')
                .values_list('diameter', flat=True))
        )
        context['heights'] = list(range(4, 20))
        if diameter := self.request.GET.get('diameter'):
            context['diameter'] = int(float(diameter))
        if height := self.request.GET.get('height'):
            context['height'] = int(float(height))
        context['pipe'] = self.request.GET.get('pipe', 'roof')
        return context

    def render_to_response(self, context, **response_kwargs):
        height = context.get('height')
        diameter = context.get('diameter')
        pipe = context.get('pipe')
        if not all([height, diameter, pipe]):
            context['errors'] = 'Заполните поля'
        else:
            line = Calc.objects.filter(pipe=pipe, diameter=diameter).first()
            if line:
                items, _ = line.calc(height)
                template = 'pages/includes/static/calc/table.html'
                # template = 'cart/cart_table.html'
                context['items'] = get_template(template) \
                    .render({'cart': {'items': items}, 'request': self.request, 'is_calc': True})
            else:
                context['errors'] = 'Нет такой конфигурации'

        if self.request.is_ajax():
            for key in set(context.keys()) - {'errors', 'lines', 'items'}:
                del context[key]
            return JsonResponse(context)
        return super(CalcView, self).render_to_response(context, **response_kwargs)


class IndexView(StaticPageMixin):
    template_name = 'index.html'
    page = BasePage.TemplateChoice.INDEX
    only_seo = True

    def get_context_data(self, *args, **kwargs):
        domain = self.request.domain
        context = dict(super(IndexView, self).get_context_data(**kwargs))
        cache_context = cache.get(f'get-cache-index-page-for-{domain.domain}')
        if not cache_context:
            cache_context = dict()
            cache_context['brands'] = Brand.objects.filter(domain__exact=self.request.domain, is_active=True,
                                                           is_index=True)
            cache_context['reviews_page'] = Page.objects.activated(template=Page.TemplateChoice.REVIEWS).first()
            cache_context['uslugi_page'] = Page.objects.activated(template=Page.TemplateChoice.MOUNTING).first()
            cache_context['reviews'] = Review.objects.filter(is_active=True, product=None)[:3]
            _, categories = Catalog.get_catalog(dicted=False)
            cache_context['categories'] = categories.filter(is_index=True)[:12]

            products = Product.objects.active().filter(parent__isnull=True)

            hit = products.filter(top_hit=True).order_by('?')
            hit_slider = get_slider(products=hit, slidesToShow=4,
                                    request=self.request)

            sales = products.annotate(has_old_price=Exists(
                Prices.objects.filter(domain=self.request.domain, old_price__gt=0,
                                      product=OuterRef('id')))).filter(has_old_price=True)
            sales_slider = get_slider(products=sales,
                                      slidesToShow=4, request=self.request)

            news = products.filter(new=True)
            news_slider = get_slider(products=news, slidesToShow=4, request=self.request)

            sliders = {
                'hit': hit_slider,
                'sales': sales_slider,
                'news': news_slider
            }

            cache_context['sliders'] = {key: value for key, value in sliders.items() if value}

            if not context.get('page'):
                context['page'] = Page.objects.activated(template=self.page).first()

            cache.set(f'get-cache-index-page-for-{domain.domain}', cache_context, 420 * 60)

        #Вынес за кэш, потому что контент не так много весит и меняется из админки
        cache_context['slider'] = IndexSlide.objects.filter(
            image__gt=0,
            domain__exact=self.request.domain).all().order_by('sort')

        context.update(cache_context)
        return context


class MountingView(StaticPageMixin):
    template_name = 'pages/static/mounting.html'
    page = BasePage.TemplateChoice.MOUNTING


class ReviewsView(StaticPageMixin, CustomListMixin):
    template_name = 'pages/static/reviews.html'
    page = BasePage.TemplateChoice.REVIEWS
    template_card_name = 'reviews/review_card.html'
    paginate_by = 10

    def get_items(self):
        return Review.objects.active().without_product()


class AboutView(StaticPageMixin):
    template_name = 'pages/static/about.html'
    page = BasePage.TemplateChoice.ABOUT

    def get_context_data(self, *args, **kwargs):
        context = super(AboutView, self).get_context_data(*args, **kwargs)
        context['information_title'] = 'Преимущества для клиентов'
        context['information'] = [
            {
                'icon': 'big_cart',
                'title': 'Опытные консультанты',
                'subtitle': 'Вы можете подобрать оптимальную модель и марку печного оборудования и комплектующих через '
                            'наш онлайн-чат, по телефону или в магазине.'
            },
            {
                'icon': 'big_box',
                'title': 'Можно увидеть товар',
                'subtitle': 'Большинство товаров из каталога можно увидеть и потрогать в наших розничных магазинах в'
                            ' Вологде, Череповце, Ярославле и Иваново.'
            },
            {
                'icon': 'big_outsourcing',
                'title': 'Напрямую от производителей',
                'subtitle': 'Прямые поставки от заводов-изготовителей позволяют нам предлагать самые '
                            'выгодные условия для наших покупателей.'
            },
        ]
        return context


class ServicesView(StaticPageMixin):
    page = BasePage.TemplateChoice.SERVICES
    template_name = 'pages/static/services.html'


class UsefulView(CustomListMixin, StaticPageMixin):
    page = BasePage.TemplateChoice.PAGES
    template_name = 'pages/static/useful.html'
    template_card_name = 'pages/includes/static/useful_items.html'
    paginate_by = 10

    def get_items(self):
        return self.page_obj.get_subpages().exclude(template=self.page)


class NewsView(CustomListMixin, StaticPageMixin):
    page = BasePage.TemplateChoice.NEWS
    template_name = 'pages/static/useful.html'
    template_card_name = 'pages/includes/static/useful_items.html'
    paginate_by = 10

    def get_items(self):
        return self.page_obj.get_subpages().exclude(template=self.page).order_by('-updated_at')


class OffersView(CustomListMixin, StaticPageMixin):
    page = BasePage.TemplateChoice.OFFERS
    template_name = 'pages/static/offers.html'
    template_card_name = 'pages/includes/static/offer.html'
    paginate_by = 3

    def get_items(self):
        return self.page_obj.get_subpages().exclude(template=self.page)


class RssPageFeed(ListView):
    template_name = 'pages/static/rss_feed.xml'
    request = get_request()

    def get_queryset(self):
        return Page.objects.filter(
            parent__template=Page.TemplateChoice.PAGES, is_active=True)

    def get_context_data_ajax(self, **kwargs):
        week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        date_now = datetime.datetime.now(pytz.timezone('Etc/Greenwich'))
        str_date = f'{week[date_now.weekday()]}, {date_now.day} {month[date_now.month - 1]} {date_now.year} {date_now.strftime("%H:%M:%S")} +0000'
        context = super().get_context_data(**kwargs)
        pages = Page.objects.filter(
            parent__template=Page.TemplateChoice.PAGES, is_active=True, domain__exact=request.domain)
        context['items'] = pages
        context['date_now'] = str_date


class UsefulPagesManager(DefaultFeed):
    def item_attributes(self, item):
        return {'turbo': 'true'}


class UsefulPagesFeed(Feed):
    feed_type = UsefulPagesManager
    title = 'Полезные статьи'
    link = '/pages/'
    description = 'Полезные статьи'

    def items(self):
        request = get_request()
        return Page.objects.filter(
            parent__template=Page.TemplateChoice.PAGES, is_active=True, domain__exact=request.domain)

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        description = ''
        for i in list(item.texts.all()):
            # description += bs(i.render()).get_text()
            description += i.render()
        return '<![CDATA[\n' + description + '\n]]>'


class TestPage(TemplateView):
    template_name = 'pages/success_pay.html'

    def get_context_data(self, **kwargs):
        context = super(TestPage, self).get_context_data(**kwargs)
        return context
