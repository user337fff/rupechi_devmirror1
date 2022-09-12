from django.db import models
from django.urls import reverse

from apps.commons.models import ImageModel, WithBreadcrumbs
from apps.seo.models import SeoBase


class Collection(ImageModel, WithBreadcrumbs, SeoBase):
    is_active = models.BooleanField(verbose_name='Активна', default=True)
    title = models.CharField(
        verbose_name='Название', max_length=127, db_index=True)
    slug = models.SlugField(verbose_name='Слаг', db_index=True)
    description = models.TextField(
        verbose_name='Описание', blank=True, default='')
    products = models.ManyToManyField(
        'Product', verbose_name='Товары', related_name="collections",
        blank=True)
    # dates
    created_at = models.DateTimeField(
        verbose_name='Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField(
        verbose_name='Дата последнего обновления', auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Коллекция'
        verbose_name_plural = 'Коллекции'
