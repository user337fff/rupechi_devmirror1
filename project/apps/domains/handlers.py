"""
Создание дефолтного домена
"""

from django.apps import apps as global_apps
from django.conf import settings
from django.core.management.color import no_style
from django.db import DEFAULT_DB_ALIAS, connections, router


def create_default_domain(
        app_config,
        verbosity=2,
        interactive=True,
        using=DEFAULT_DB_ALIAS,
        apps=global_apps,
        **kwargs):
    try:
        Domain = apps.get_model('domains', 'Domain')
    except LookupError:
        return

    if not router.allow_migrate_model(using, Domain):
        return

    if not Domain.objects.using(using).exists():
        if verbosity >= 2:
            print("Создание домена по умолчанию")
        Domain(
            domain=getattr(
                settings,
                'DEFAULT_DOMAIN',
                'place-shop.ru'),
            name=getattr(
                settings,
                'DEFAULT_DOMAIN_DISPLAY',
                'Москва'),
            name_loct=getattr(
                settings,
                'DEFAULT_DOMAIN_DISPLAY',
                'Москве')
        ).save(using=using)
