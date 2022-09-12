from django.apps import AppConfig
from django.db.models.signals import post_migrate

from .handlers import create_default_domain


class DomainsConfig(AppConfig):
    name = 'apps.domains'
    verbose_name = 'Домены'

    def ready(self):
        post_migrate.connect(create_default_domain, sender=self)
