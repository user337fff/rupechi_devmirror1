import string

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_delete, pre_save
from django.http.request import split_domain_port
from django.utils.translation import gettext_lazy as _

from apps.seo.models import SeoBase

DOMAIN_CACHE = {}


def _simple_domain_name_validator(value):
    """
    Validate that the given value contains no whitespaces to prevent common
    typos.
    """
    checks = ((s in value) for s in string.whitespace)
    if any(checks):
        raise ValidationError(
            _("The domain name cannot contain any spaces or tabs."),
            code='invalid',
        )


class DomainManager(models.Manager):
    use_in_migrations = True

    def get_current(self, request):
        host = request.get_host()
        return self.get(domain__iexact=host) or self.first()
        # return self.filter(domain__iexact=host).first() or self.first()
        #     Почему-то бывало что домен был равен None, возможно это не из-за глобального словар,
        #     а из-за ошибки MultipleObjectsReturned т.к. после тача он кидал ошибки мол выбрал 20 доменов вместо 1
        # try:
        #     # Поиск домена по хосту с номером порта или без.
        #     if host not in DOMAIN_CACHE:
        #         DOMAIN_CACHE[host] = self.get(domain__iexact=host)
        #     return DOMAIN_CACHE[host]
        # except Domain.DoesNotExist:
        #     # Поиск домена после обрезки номера порта.
        #     domain, port = split_domain_port(host)
        #     if domain not in DOMAIN_CACHE:
        #         DOMAIN_CACHE[domain] = self.get(domain__iexact=domain)
        #     return DOMAIN_CACHE[domain]

    def clear_cache(self):
        """Очистка кеша доменов"""
        global DOMAIN_CACHE
        DOMAIN_CACHE = {}

class Domain(SeoBase):
    class Meta:
        verbose_name = 'домен'
        verbose_name_plural = 'домены'
        ordering = ['domain']

    domain = models.CharField(
        'Имя домена',
        max_length=100,
        validators=[_simple_domain_name_validator],
        primary_key=True,
        unique=True,
    )
    name = models.CharField('Отображаемое имя', max_length=50)
    name_loct = models.CharField(
        'Отображаемое имя в предложном падеже', max_length=50,
        help_text='Пример: "Москве"')
    name_dat = models.CharField(
        'Отображаемое имя в дательном падеже', max_length=50,
        help_text='Пример: Санкт-Петербургу'
    )
    # contacts
    address = models.CharField(
        verbose_name="Адрес", blank=True, default="", max_length=255)
    email = models.EmailField(verbose_name="Email", blank=True, default="")
    phone = models.CharField(
        verbose_name="Номер телефона", blank=True, default="", max_length=31)
    extra_phones = models.CharField(
        verbose_name="Дополнительные номера телефонов", blank=True, default="",
        max_length=255, help_text="Введите номера через запятую")

    lat = models.DecimalField(
        verbose_name="Координата X на карте", max_digits=9, decimal_places=6,
        blank=True, null=True)
    lon = models.DecimalField(
        verbose_name="Координата Y на карте", max_digits=9, decimal_places=6,
        blank=True, null=True)

    robots_txt = models.TextField(
        verbose_name="robots.txt", default="", blank=True)
    header_extra = models.TextField(
        verbose_name="Вывод в head", default="", blank=True)
    footer_extra = models.TextField(
        verbose_name="Скрипты под footer", default="", blank=True)
    id_price = models.UUIDField('id розничной цены', blank=True, null=True)

    seo_description_category = models.TextField('SEO Описание для категорий', blank=True, default="")
    seo_description_product = models.TextField('SEO Описание для продукта', blank=True, default="")

    objects = DomainManager()

    def __str__(self):
        return self.domain

    @property
    def phones(self):
        if self.extra_phones:
            return self.extra_phones.split(',')
        return ''


def clear_domain_cache(sender, **kwargs):
    """
    Очистка кеша доменов
    """
    instance = kwargs['instance']
    using = kwargs['using']
    try:
        del DOMAIN_CACHE[instance.pk]
    except KeyError:
        pass


pre_save.connect(clear_domain_cache, sender=Domain)
pre_delete.connect(clear_domain_cache, sender=Domain)


class SeoContentFromLinks(models.Model):
    domainSettings = models.ForeignKey(Domain, on_delete=models.CASCADE, verbose_name="Настройки домена")
    slugField = models.CharField(max_length=200, verbose_name="Путь до страницы", blank=True, default="")
    title = models.CharField(max_length=200, verbose_name="Заголовок", blank=True, default="")
    description = models.TextField(verbose_name="Описание", blank=True, default="")
    keywords = models.TextField(verbose_name="Клюечевые слова", blank=True, default="")

    class Meta:
        verbose_name = "СЕО контент для страниц"
        verbose_name_plural = "СЕО контент для страниц"