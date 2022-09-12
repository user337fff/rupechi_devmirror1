from django.core.cache import cache
from django.db import models
from django.db.models import Q

from .managers import HeaderManager, FooterManager, SidebarManager, CatalogManager
from ..domains.middleware import get_request
from ..domains.models import Domain


class AbstractMenuItem(models.Model):
    domain = models.ManyToManyField('domains.Domain', verbose_name="Домен")
    title = models.CharField("Заголовок", max_length=63)
    page = models.ForeignKey('pages.BasePage', verbose_name="Страница", blank=True, null=True, on_delete=models.CASCADE)
    category = models.ForeignKey('catalog.Catalog', verbose_name="Категория", blank=True, null=True,
                                 on_delete=models.CASCADE)
    url = models.CharField("Ссылка", max_length=127, blank=True, default="")
    sort = models.PositiveIntegerField(verbose_name='Сортировка', default=0)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        if self.category:
            return self.category.get_absolute_url()
        if self.page:
            return self.page.get_absolute_url()
        return self.url

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        cache.delete_many([f'{domain}_grouped_nav' for domain in Domain.objects.iterator()])
        return super(AbstractMenuItem, self).save(force_insert, force_update, using, update_fields)

    def delete(self, using=None, keep_parents=False):
        cache.delete_many([f'{domain}_grouped_nav' for domain in Domain.objects.iterator()])
        return super(AbstractMenuItem, self).delete(using, keep_parents)

    class Meta:
        verbose_name = 'Элемент меню'
        verbose_name_plural = 'Меню сайта'
        ordering = ('sort',)
        abstract = True


class MenuItem(AbstractMenuItem):
    HEADER = "head"
    FOOTER = "foot"
    SIDEBAR = "side"
    CATALOG = 'catalog'

    LOC_CHOICES = (
        (HEADER, "Шапка"),
        (FOOTER, "Подвал"),
        (SIDEBAR, "Сайдбар"),
        (CATALOG, 'Каталог'),
    )

    location = models.CharField(
        "Расположение", choices=LOC_CHOICES, max_length=10)

    @classmethod
    def _get_grouped_menu(cls):
        """
        Получение меню и группировка по хедеру и футеру
        """
        domain = get_request().domain
        grouped = cache.get(f'{domain}_grouped_nav')
        if not grouped:
            grouped = {}
            for location, _ in cls.LOC_CHOICES:
                grouped.setdefault(location, [])
            queryset = cls.objects.prefetch_related('subitems') \
                .filter(location__in=dict(cls.LOC_CHOICES).keys(), domain__exact=domain) \
                .filter(Q(page__domain__exact=domain, page__is_active=True) | Q(page=None)) \
                .filter(Q(category__domain__exact=domain, category__is_active=True) | Q(category=None))
            for item in queryset:
                grouped[item.location].append(item)
            cache.set(f'{domain}_grouped_nav', grouped)
        return grouped

    @classmethod
    def get_header(cls):
        return cls._get_grouped_menu()[cls.HEADER]

    @classmethod
    def get_footer(cls):
        return cls._get_grouped_menu()[cls.FOOTER]

    @classmethod
    def get_sidebar(cls):
        return cls._get_grouped_menu()[cls.SIDEBAR]

    @classmethod
    def get_catalog(cls):
        return cls._get_grouped_menu()[cls.CATALOG]

    def get_subitems(self):
        domain = get_request().domain
        return self.subitems \
            .filter(domain__exact=domain)\
            .filter(
                Q(page__domain__exact=domain, page__is_active=True)
                | Q(category__is_active=True)
                # | Q(category__domain__exact=domain, category__is_active=True)
            )


class HeaderMenuItem(MenuItem):
    """
    Прокси-модель для отдельного заполнения пунктов хедера
    """
    objects = HeaderManager()

    def save(self, *args, **kwargs):
        self.location = self.HEADER
        return super(HeaderMenuItem, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Элемент шапки'
        verbose_name_plural = 'Шапка сайта'
        ordering = ('sort',)
        proxy = True


class FooterMenuItem(MenuItem):
    """
    Прокси-модель для отдельного заполнения пунктов футера
    """
    objects = FooterManager()

    def save(self, *args, **kwargs):
        self.location = self.FOOTER
        return super(FooterMenuItem, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Элемент подвала'
        verbose_name_plural = 'Подвал сайта'
        ordering = ('sort',)
        proxy = True


class SidebarMenuItem(MenuItem):
    """
    Прокси-модель для отдельного заполнения пунктов сайдбара
    Также используется для получения сайдбара
    """
    objects = SidebarManager()

    def save(self, *args, **kwargs):
        self.location = self.SIDEBAR
        return super(SidebarMenuItem, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Элемент сайдбара'
        verbose_name_plural = 'Сайдбар'
        ordering = ('sort',)
        proxy = True


class CatalogMenuItem(MenuItem):
    """
    Прокси-модель для отдельного заполнения пунктов сайдбара
    Также используется для получения сайдбара
    """
    objects = CatalogManager()

    def save(self, *args, **kwargs):
        self.location = self.CATALOG
        return super(CatalogMenuItem, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Элемент каталог'
        verbose_name_plural = 'Каталог'
        ordering = ('sort',)
        proxy = True


class MenuSubItem(AbstractMenuItem):
    parent = models.ForeignKey(
        MenuItem, verbose_name='Родительский пункт', related_name='subitems',
        on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Подпункт меню'
        verbose_name_plural = 'Подпункты меню'
        ordering = ['sort']
