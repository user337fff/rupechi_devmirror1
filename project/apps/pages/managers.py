from django.db import models
from django.utils import timezone

from apps.domains.middleware import get_request


class PageManager(models.Manager):
    """Менеджер для прокси-модели Page"""

    def get_queryset(self):
        return super(PageManager, self).get_queryset().filter(type='page')

    def create(self, **kwargs):
        """Создание только страниц"""
        kwargs.update({'type': 'page'})
        return super(PageManager, self).create(**kwargs)

    def activated(self, **kwargs):
        """Только активные"""
        domain = get_request().domain
        return self.get_queryset().filter(is_active=True, domain__exact=domain, **kwargs)


class PostManager(models.Manager):
    """Менеджер для прокси-модели Post"""

    def get_queryset(self):
        return super(PostManager, self).get_queryset().filter(type='post')

    def create(self, **kwargs):
        """Создание только постов"""
        kwargs.update({'type': 'post'})
        return super(PostManager, self).create(**kwargs)

    def activated(self, **kwargs):
        """Только активные"""
        domain = get_request().domain
        return self.get_queryset().filter(is_active=True, domain__exact=domain, **kwargs)

    def published(self):
        """Только опубликованные"""
        return self.activated().filter(pub_date__lte=timezone.now())
