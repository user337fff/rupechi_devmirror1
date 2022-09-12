from django.core.cache import *
from django.core.management import BaseCommand

from apps.catalog.models import *
from apps.domains.models import *


class Command(BaseCommand):


    # Немного перемудрил, пока потестим полный сброс кэша, а не выбороный
    # def clear_cache(self):
    #     # Ф-я для чистки различного кэша, по мере нужды будет регулярно дополняться
    #     for domain in Domain.objects.filter(domain='www.rupechi.ru'):
    #         if cache.get(f'{domain.domain}_grouped_nav'):
    #             cache.delete(f'{domain.domain}_grouped_nav')
    #             print(f'Удален кэш для навигации сайта на домене {domain.domain}')
    #         if cache.get(f'get-cache-index-page-for-{domain.domain}'):
    #             cache.delete(f'get-cache-index-page-for-{domain.domain}')
    #             print(f'Удален кэш для главной страницы на домене {domain.domain}')
    #         for slug in list(SlugCategory.objects.all().values_list('slug', flat=True)) + \
    #                     list(Brand.objects.all().values_list('slug', flat=True)):
    #             if cache.get(f'get-context-data-filters-for-{slug}-on-{domain}'):
    #                 cache.delete(f'get-context-data-filters-for-{slug}-on-{domain}')
    #                 print(f'Удален кэш фильтров для категории {slug}')
    #             for user_contractor in range(1, 4):
    #                 if cache.get(f'render_to_string_{slug}-'
    #                              f'{user_contractor}-{domain}'):
    #                     cache.delete(f'render_to_string_{slug}-'
    #                                  f'{user_contractor}-{domain}')
    #                     print(f'Удален кэш страницы категории {slug} на домене {item.domain.domain}')
    #             for page in range(1, 40):
    #                 for paginate in ([30, 60, 90]):
    #                     for view in (['', 'list']):
    #                         if cache.get(f'get-context-data-filters-for-{slug}-on-{domain}-'
    #                                      f'page={page}-paginate_by={paginate}-view_by={view}'):
    #                             cache.delete(f'get-context-data-filters-for-{slug}-on-{domain}-'
    #                                          f'page={page}-paginate_by={paginate}-view_by={view}')
    #                             print(f'Удален кэш для категории {slug} на домене {domain}')

    def clear_cache(self):
        cache.clear()
        self.stdout.write('Очищен кэш')

    def handle(self, *args, **options):
        self.clear_cache()
