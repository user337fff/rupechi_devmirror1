from django.db import models


class NavManager(models.Manager):
    location = None

    def get_queryset(self):
        return super(NavManager, self).get_queryset() \
            .filter(location=self.location)

    def create(self, **kwargs):
        kwargs.update({'location': self.location})
        return super(NavManager, self).create(**kwargs)


class HeaderManager(NavManager, models.Manager):
    location = 'head'


class FooterManager(NavManager, models.Manager):
    location = 'foot'


class SidebarManager(NavManager, models.Manager):
    location = 'side'


class CatalogManager(NavManager, models.Manager):
    location = 'catalog'
