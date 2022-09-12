from apps.commons.mixins import JSONResponseMixin, ContextPageMixin
from apps.pages import views
from apps.pages.models import Heading, Page, Post, BasePage
from django.http import Http404
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.generic import ListView, DetailView
from django.views.generic.detail import SingleObjectMixin
from apps.catalog import views as catalog_views
from apps.catalog.models import Catalog, Product
from apps.domains.models import Domain
from django.http import HttpResponseNotFound
from django.shortcuts import redirect, reverse
from django.db.models import Q


class HeadingDetail(SingleObjectMixin, ListView, JSONResponseMixin):
    paginate_by = 2
    template_name = "pages/heading.html"
    _is_ajax = None

    template_name_pagin = "commons/pagination.html"
    template_name_pages = "pages/page_cards.html"

    @property
    def is_ajax(self):
        if self._is_ajax is None:
            self._is_ajax = True if self.request.GET.get('ajax') else False
        return self._is_ajax

    def get_queryset(self):
        return Post.objects.filter(
            is_active=True,
            pub_date__lte=timezone.now(),
            heading=self.object,
            domain=self.request.domain)

    def _get_context_data_ajax(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pages = render_to_string(
            self.template_name_pages,
            {'pages': context['page_obj']})
        pagination = render_to_string(
            template_name=self.template_name_pagin,
            context=context)

        context = {
            'pages': pages,
            'pagination': pagination
        }
        return context

    def _get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pages = render_to_string(
            self.template_name_pages,
            {'pages': context['page_obj']})
        pagination = render_to_string(
            template_name=self.template_name_pagin,
            context=context)
        context['heading'] = self.object
        context['pages'] = pages
        context['pagination'] = pagination
        return context

    def get_context_data(self, **kwargs):
        if not self.is_ajax:
            return self._get_context_data(**kwargs)
        else:
            return self._get_context_data_ajax(**kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(
            queryset=Heading.objects.all()
        )
        return super(HeadingDetail, self).get(request, *args, **kwargs)

    def render_to_response(self, context, **kwargs):
        if not self.is_ajax:
            return super().render_to_response(context)
        return self.render_to_json_response(context)


def get_new_catalog(request, **kwargs):
    """Статичные текстовые страницы, чисто для сохранения слага и хлебных крошек"""
    # slug = Page.decode_slug(kwargs.get('slug'))
    slug = kwargs.get('slug')
    if slug[-1] == '/':
        slug = slug[:-1]
    kwargs['slug'] = slug
    slugs = slug.split('/f/')[0].split('/')
    slug = slugs[-1]
    parent_slug = ''
    domain = request.domain

    if len(slugs) > 1:
        parent_slug = slugs[-2]

    if slug == 'search':
        return catalog_views.SearchPageView.as_view()(request, **kwargs)
        
    if parent_slug:
        parent_object = Page.objects.activated().filter(slug=slug).first() \
                        or Catalog.objects.prefetch_related('slugs')\
                            .filter(Q(slugs__domain=domain) & Q(slugs__slug=slug)).first()
        if parent_object.__class__ == Catalog:
            obj = parent_object.__class__.objects.prefetch_related('slugs')\
                .filter(Q(slugs__domain=domain) & Q(slugs__slug=slug)).first() if parent_object else None
        else:
            obj = parent_object.__class__.objects \
                .filter(Q(domain__exact=domain) & Q(slug=slug)).first() if parent_object else None
    else:
        obj = Catalog.objects.prefetch_related('slugs').filter(slugs__domain=domain, slugs__slug=slug).first() \
              or Page.objects.activated().filter(slug=slug).first() or Catalog.objects.filter(slugs__slug=slug).first()

    if not obj:
        if Product.objects.filter(slug=slug).exists():
            return redirect(reverse('product', kwargs={'slug': slug}))
        if not 'cache' in slugs:
            print('*** HTTP EXCEPT 404', 'apps/pages/views/pages.py 107', slugs, slug, domain)
        raise Http404

    if obj.__class__.__name__ == 'Catalog':
        return catalog_views.CategoryDetailView.as_view()(request, **kwargs)

    templates = {
        Page.TemplateChoice.ABOUT.value: views.AboutView,
        Page.TemplateChoice.CALCULATOR.value: views.CalcView,
        Page.TemplateChoice.MOUNTING.value: views.MountingView,
        Page.TemplateChoice.REVIEWS.value: views.ReviewsView,
        Page.TemplateChoice.COOPERATION.value: views.CooperationView,
        Page.TemplateChoice.SERVICES.value: views.ServicesView,
        Page.TemplateChoice.PAGES.value: views.UsefulView,
        Page.TemplateChoice.OFFERS.value: views.OffersView,
        Page.TemplateChoice.NEWS.value: views.NewsView,
        Page.TemplateChoice.SITEMAP.value: views.SiteMapView,
    }

    if view := templates.get(obj.template):
        return view.as_view()(request, **kwargs)

    return PageDetail.as_view()(request, **kwargs)


class BasePageDetail(DetailView):
    template_name = 'pages/page.html'
    context_object_name = 'page'
    model = Page

    def get_queryset(self):
        return super(BasePageDetail, self).get_queryset()

    def get_object(self, queryset=None):
        slug = Page.decode_slug(self.kwargs.get('slug'))
        obj = self.get_queryset().filter(slug=slug).first()
        if obj:
            return obj
        print('*** HTTP EXCEPT 404', 'apps/pages/views/pages.py 138')
        raise Http404

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hide_title'] = True
        return context


class PageDetail(BasePageDetail):
    """Вывод текстовой страницы независимо от типа"""
    model = Page


class PostDetail(BasePageDetail):
    """Вывод поста"""
    model = Post

    def get_queryset(self):
        return Post.objects.published().filter(domain__exact=self.request.domain)


class AddressView(ContextPageMixin):
    page = BasePage.TemplateChoice.ADDRESS
    template_name = 'pages/static/address.html'
