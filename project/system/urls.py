import debug_toolbar
from apps.domains.views import ChangeDomain
from apps.pages.views import IndexView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.views.generic import TemplateView
from apps.configuration.models import Settings
from apps.configuration.views import autotestHandler
from django.contrib.sitemaps.views import sitemap
from django.contrib.sitemaps import Sitemap
from apps.domains.middleware import get_request
from apps.catalog import models as catalog_models
from apps.pages import models as pages_models
from django.shortcuts import reverse

class ProductsSitemap(Sitemap):

    def items(self):
        return catalog_models.Product.objects.active()

class CategorySitemap(Sitemap):

    def items(self):
        domain = get_request().domain
        return catalog_models.Catalog.objects.filter(is_active=True, domain__exact=domain)

class PageSitemap(Sitemap):

    def items(self):
        return pages_models.Page.objects.activated()

sitemaps = {
    'products': ProductsSitemap,
    'categories': CategorySitemap,
    'pages': PageSitemap,
}

class Favicon(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        return Settings.get_settings().favicon.url


urlpatterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + [
    path("sitemap.xml", sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('__debug__/', include(debug_toolbar.urls)),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('jet/', include('jet.urls', 'jet')),
    path('jet/dashboard/', include('jet.dashboard.urls',
                                   'jet-dashboard')),
    path("autotest/start/", autotestHandler),
    path("admin/", admin.site.urls),
    path('favicon.ico', Favicon.as_view()),
    path("", include("apps.seo.urls", namespace='seo')),
    path("", include('social_django.urls', namespace='social')),
    path("", IndexView.as_view(), name='index'),
    path('change/', ChangeDomain.as_view(), name='change_domain'),
    path('feedback/api/', include('apps.feedback.urls')),
    path("", include('apps.reviews.urls')),
    path("", include("apps.catalog.urls")),
    path("", include("apps.shop.urls", namespace='shop')),
    path("", include("apps.exchange1c.urls")),
    path("apiship/", include("apps.apiship.urls", namespace='apiship')),
    path("cart/", include("apps.cart.urls", namespace='cart')),
    path("compare/", include("apps.compare.urls", namespace='compare')),
    path("komtet/", include("apps.komtet.urls", namespace='komtet')),
    path("sber/", include("apps.sber_acquiring.urls", namespace='sber')),
    path("users/", include("apps.users.urls")),
    path("wishlist/", include("apps.wishlist.urls", namespace='wishlist')),
    path("", include("apps.pages.urls", namespace='pages')),
]
