from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.catalog.models import Brand, Category, Catalog, Alias, Product
from apps.domains.middleware import get_request


@receiver(post_save, sender=Category)
@receiver(post_save, sender=Product)
@receiver(post_save, sender=Catalog)
@receiver(post_save, sender=Alias)
@receiver(post_save, sender=Brand)
def clear_cache(instance, sender, *args, **kwargs):
    domain = get_request().domain
    key = instance.get_key_slug(domain)
    cache.delete(key)
