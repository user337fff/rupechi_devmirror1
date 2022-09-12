from django.core.management import BaseCommand
from apps.catalog.models import SeoCategory, Catalog
from apps.domains.models import Domain
from apps.pages.models import BasePage
from django.db.models import Count, Q, F


class Command(BaseCommand):

    def handle(self, *args, **options):
        duplicates = SeoCategory.objects.values('meta_title', 'meta_description', 'id')\
            .annotate(title_count=Count('meta_title'), description_count=Count('meta_description'))\
            .filter(Q(title_count__gt=1) | Q(description_count__gt=1))
        print(f'{len(duplicates)}')

