from apps.commons.models import ImageModel, WithBreadcrumbs, FullSlugMixin
from apps.seo.models import SeoBase
from django.apps import apps
from django.db import models
from django.db.models import Q
from django.urls import reverse
from apps.domains.middleware import get_request
from django.apps import apps
from ckeditor_uploader.fields import RichTextUploadingField


class Brand(ImageModel, FullSlugMixin, WithBreadcrumbs, SeoBase):
    id_1c = models.UUIDField('id_1c', blank=True, null=True)
    is_active = models.BooleanField(verbose_name='Активен', default=True)
    is_index = models.BooleanField(verbose_name="На главной", default=False)
    title = models.CharField(
        verbose_name='Название', max_length=127, db_index=True)
    slug = models.SlugField(verbose_name='Слаг', db_index=True)
    description = models.TextField(
        verbose_name='Описание', blank=True, default='')
    # extra seo settings
    meta_message = RichTextUploadingField('Текст на странице', blank=True, default="")
    not_discount = models.ManyToManyField('domains.Domain', verbose_name='Не применять скидку для доменов',
                                          blank=True, null=True, related_name='brands_not_discount')
    # dates
    created_at = models.DateTimeField(
        verbose_name='Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField(
        verbose_name='Дата последнего обновления', auto_now=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'Производитель'
        verbose_name_plural = 'производители'

    def __str__(self):
        return self.title

    def get_absolute_url(self, *args, **kwargs):
        return reverse('brand', kwargs={'slug': self.encode_slug()})

    def get_products(self):
        Product = apps.get_model('catalog.Product')
        return Product.objects.active(brand=self)

    def get_related_categories(self):
        Catalog = apps.get_model('catalog.Catalog')
        request = get_request()
        return Catalog.objects\
            .filter(is_active=True, domain__exact=request.domain)\
            .filter(Q(products__brand=self) | Q(alias_products__brand=self))\
            .filter(Q(show_on_menu=True) & Q(show_on_categories__pk=self.pk) & Q(is_active=True))\
            .exclude(Q(show_on_menu=True) & Q(parent__pk=self.pk)).distinct()

    def get_breadcrumbs(self, middle=None, callback=None):
        filters = {}
        request = get_request()
        domain = request.domain
        if domain:
            filters['domain__exact'] = domain
        Page = apps.get_model('pages', 'Page')
        page = Page.objects.filter(template=Page.TemplateChoice.BRANDS, domain__exact=domain, is_active=True).first()
        parents = []
        if page:
            parents = [
                (page.title, reverse('brands')),
            ]
        return super().get_breadcrumbs(middle=parents, callback=callback)
