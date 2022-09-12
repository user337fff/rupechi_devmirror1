from django.contrib.sitemaps import Sitemap
from django.http import HttpResponse
from django.shortcuts import reverse

from apps.catalog import models as catalog_models
from apps.domains.middleware import get_request
from apps.pages import models as pages_models


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


class StaticViewSitemap(Sitemap):

    def items(self):

        catalog_urls = ['catalog', 'sale', 'brands', 'search-page']
        compare_urls = ['compare:list']
        pages_urls = ['pages:address']

        return [] + catalog_urls + pages_urls + compare_urls

    def location(self, item):
        return reverse(item)


class ImageSitemap(Sitemap):

    def items(self):
        catalog_images = list(catalog_models.Catalog.objects.exclude(image_md5='').values_list('image', flat=True))
        product_images = list(catalog_models.ProductImage.objects.all().values_list('image', flat=True))
        return catalog_images + product_images

    def get_image(self, protocol, domain, item):
        return self.items()

    def __get(self, name, obj, default=None):
        try:
            attr = getattr(self, name)
        except AttributeError:
            return default
        if callable(attr):
            return attr.__dict__
        return attr

    def get_urls(self, page=1, site=None, protocol=None):
        if self.protocol is not None:
            protocol = self.protocol
        if protocol is None:
            protocol = 'http'

        if site is None:
            if Site.__meta.installed:
                try:
                    site = Site.objects.get_current()
                except Site.DoesNotExist:
                    pass
            if site is None:
                raise ImproperlyConfigured(
                    "To use sitemaps, either enable the sites framework or pass a Site/RequestSite object in your view.")
        domain = site.domain

        urls = []
        for item in self.paginator.page(page).object_list:
            loc = "%s://%s%s" % (protocol, domain, self.__get('location', item))
            priority = self.__get('priority', item, None)
            url_info = {
                'item': item,
                'location': loc,
                'lastmod': self.__get('lastmod', item, None),
                'changefreq': self.__get('changefreq', item, None),
                'priority': str(priority is not None and priority or ''),
            }
            urls.append(url_info)
        return urls


sitemaps = {
    'products': ProductsSitemap,
    'categories': CategorySitemap,
    'pages': PageSitemap,
    #'static': StaticViewSitemap
}

image_sitemap = {
    'images': ImageSitemap,
}


def robots(request):
    #return HttpResponse(request.domain.robots_txt, content_type='text/plain')
    return HttpResponse("")
