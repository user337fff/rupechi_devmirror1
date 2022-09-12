from django.core.management.base import BaseCommand
from django.core.exceptions import MultipleObjectsReturned
from django.core.cache import cache

from django.db.models import Count

from apps.catalog.models import Product, SlugCategory

from apps.domains.models import Domain

from slugify import slugify


class Command(BaseCommand):

    def handle(self, *args, **options):
        products = Product.objects.filter(
            slug__in=Product.objects.all()
                                    .values('slug')
                                    .annotate(sc=Count('slug'))
                                    .filter(sc__gt=1)
                                    .order_by()
                                    .values_list('slug', flat=True)
        )
        for product in products:
            slug = str(product.title).replace(',', '-').replace('+', 'plus')
            try:
                slug = slugify(slug)
                Product.objects.get(slug=slug)
            except MultipleObjectsReturned:
                slug = slugify(slug + str(Product.objects.filter(slug=slug).count()))
            except Product.DoesNotExist:
                pass
            product.slug = slug
            product.save(update_fields=['slug'])
        for item in SlugCategory.objects.all():
            for domain in Domain.objects.all():
                for user_contractor in range(1, 4):
                    if cache.get(f'render_to_string_{item.slug}-'
                                 f'{user_contractor}-{domain}'):
                        cache.delete(f'render_to_string_{item.slug}-'
                                     f'{user_contractor}-{domain}')
                        print(f'Удален кэш страницы категории {item.category.title} для домена {item.domain.domain}')