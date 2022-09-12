import decimal

from apps.domains.middleware import get_request
from apps.catalog.models import get_contractor
from apps.commons.models import SingletonModel, ImageModel
from apps.feedback.models import RecipientMixin
from apps.seo.models import SeoBase
from apps.domains.models import *
from colorfield.fields import ColorField
from django.contrib.postgres.fields import ArrayField
from django.core.cache import cache
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string

CONTRACTOR_CHOICES = (
    ('price', 'Розница'),
    ('price_1', 'Контрагент 1'),
    ('price_2', 'Контрагент 2'),
    ('price_3', 'Контрагент 3'),
)


class TypePrice(models.Model):
    title = models.CharField('Название', unique=True, choices=CONTRACTOR_CHOICES, default='price', max_length=125)

    def __str__(self):
        return self.get_title_display()

    class Meta:
        ordering = ['id']
        verbose_name = 'Тип цены'
        verbose_name_plural = 'Типы цен'


class Settings(RecipientMixin, SingletonModel, SeoBase):
    """Настройки сайта"""
    CONTRACTOR_CHOICES = CONTRACTOR_CHOICES
    name = models.CharField(verbose_name="Наименование сайта", max_length=127)

    # logos
    logo = models.ImageField(
        verbose_name='Лого', upload_to='images/configuration/logo/',
        null=True, blank=True, help_text="Размер 270x80")
    logo_email = models.ImageField(
        verbose_name="Лого для уведомлений", upload_to='images/logo/mail/',
        null=True, blank=True)
    favicon = models.ImageField(
        verbose_name='Фавикон', upload_to='images/configuration/logo/favicon/',
        null=True, blank=True)
    # seo
    meta_title = models.CharField('Название по умолчанию', default="", blank=True, max_length=125)
    meta_description = models.TextField('Описание по умолчанию', default="", blank=True)

    # colors
    color_scheme = ColorField(default='#006EFF',
                              verbose_name="Цветовая схема сайта", max_length=7,
                              help_text=_(u'HEX color, as #RRGGBB'))
    color_scheme_alpha = models.CharField(blank=True,
                                          verbose_name="Цветовая схема c alpha", max_length=50,
                                          default='rgba(0, 110, 255, 0.6)', )
    color_scheme_dark = models.CharField(blank=True, default='#000CD4',
                                         verbose_name="Цветовая схема затемнение", max_length=7)

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

    custom_field_title = models.CharField(
        verbose_name="Пользовательское поле", blank=True, default="",
        max_length=127)
    custom_field_value = models.CharField(
        verbose_name="Значение пользовательского поля", blank=True,
        default="", max_length=127)

    requisites = models.FileField(
        verbose_name='Реквизиты', upload_to='files/configuration/requisites/',
        null=True, blank=True)

    # privacy policy
    company_name = models.CharField(
        verbose_name="Название компании", blank=True, default="",
        max_length=127)
    legal_address = models.CharField(
        verbose_name="Юридический адрес", blank=True, default="",
        max_length=127)
    domain = models.CharField(
        verbose_name="Домен", blank=True, default="", max_length=63)

    # Социальные сети
    vkontakte = models.CharField(verbose_name="Ссылка на ВК группу",
                                 max_length=127, blank=True, default="")
    facebook = models.CharField(verbose_name="Ссылка на fb группу",
                                max_length=127, blank=True)
    instagram = models.CharField(verbose_name="Ссылка на instagram",
                                 max_length=127, blank=True)
    telegram = models.CharField(verbose_name="Ссылка на telegram",
                                max_length=127, blank=True)
    twitter = models.CharField(verbose_name="Ссылка на twitter",
                               max_length=127, blank=True)
    youtube = models.CharField(verbose_name="Ссылка на youtube",
                               max_length=127, blank=True)
    odnoklassniky = models.CharField(verbose_name="Ссылка на Одноклассники",
                                     max_length=127, blank=True)

    banner_text = models.CharField(verbose_name="Текст баннера в сайдбаре",
                                   blank=True, default="", max_length=255)
    banner_img = models.ImageField(
        verbose_name="Изображение на баннере в сайдбаре",
        upload_to='images/configuration/banner/', null=True, blank=True)
    card_payment = models.TextField(
        verbose_name="Текст 'доставка' в карточке товара", default="",
        blank=True)
    card_shipping = models.TextField(
        verbose_name="Текст 'доставка' в карточке товара", default="",
        blank=True)
    attr_chimney = models.ForeignKey('catalog.ProductAttribute', verbose_name="Атрибут", blank=True, null=True,
                                     on_delete=models.SET_NULL)
    attr_second = models.ForeignKey('catalog.ProductAttribute', verbose_name="Второй атрибут", blank=True, null=True,
                                     on_delete=models.SET_NULL, related_name='second_attr')

    discount = models.PositiveSmallIntegerField('Процент скидки онлайн заказа', default=0)
    discount_domain = models.ManyToManyField('domains.Domain', verbose_name='Домены для скидок', blank=True, null=True)
    type_price = models.ManyToManyField(TypePrice, verbose_name="Тип цен", blank=True)

    def save(self, *args, **kwargs):
        color_scheme_alpha = "rgba({}, {}, {}, 0.6)".format(
            self._convert_base(self.color_scheme[1:3]),
            self._convert_base(self.color_scheme[3:5]),
            self._convert_base(self.color_scheme[5:7])
        )
        color_scheme_dark = self._darken(self.color_scheme)
        self.color_scheme_alpha = color_scheme_alpha
        self.color_scheme_dark = color_scheme_dark
        cache.delete('settings')
        super(Settings, self).save(*args, **kwargs)

    def _convert_base(self, num, to_base=10, from_base=16):
        if isinstance(num, str):
            n = int(num, from_base)
        else:
            n = int(num)
        alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if n < to_base:
            return alphabet[n]
        else:
            return self._convert_base(n // to_base, to_base) + alphabet[n % to_base]

    def _darken(self, hex_color):
        o1 = self._convert_base(
            round(int(self._convert_base(hex_color[1:3])) * 0.83), 16, 10)
        if len(o1) == 1:
            o1 = f"0{o1}"
        o2 = self._convert_base(
            round(int(self._convert_base(hex_color[4:5])) * 0.83), 16, 10)
        if len(o2) == 1:
            o2 = f"0{o2}"
        o3 = self._convert_base(round(
            int(self._convert_base(hex_color[5:7])) * 0.83), 16, 10)
        if len(o3) == 1:
            o3 = f"0{o3}"

        return "#{}{}{}".format(o1, o2, o3)

    def phones(self):
        if self.extra_phones:
            return self.extra_phones.split(',')
        return ''

    def slider(self):
        return self.slider_items.all()

    @staticmethod
    def get_settings():
        obj = cache.get('settings')
        if not obj:
            obj = Settings.objects.first()
            cache.set('settings', obj)
        return obj

    @classmethod
    def get_discount(cls):
        settings = cls.get_settings()
        discount = settings.discount
        contractor = get_contractor()
        # domain_discount = Settings.objects.all().order_by('id').first().discount_domain.all()
        if discount and settings.type_price.filter(title=f'price{contractor}').exists(): #and get_request().domain in domain_discount:
            return decimal.Decimal(1 - discount / 100)
        return decimal.Decimal(1)

    def __str__(self):
        title = 'Настройки сайта'
        if self.name:
            title += f' "{self.name}"'
        return title

    class Meta:
        verbose_name = _('Настройки сайта')
        verbose_name_plural = _('Настройки сайта')

class HTMLGroup(models.Model):
    
    HEADER = 'header'
    FOOTER = 'footer'
    
    TypePosition = [
        (HEADER, 'Шапка'),
        (FOOTER, 'Подвал')    
    ]
    
    domain = models.ForeignKey('domains.Domain', on_delete=models.CASCADE, related_name="element_groups")
    nameGroup = models.CharField(verbose_name="Название группы", default="", max_length=200)
    position = models.CharField(choices=TypePosition, max_length=100, default=HEADER)

    @staticmethod
    def get_header():
        return HTMLGroup.objects.filter(
            domain=get_request().domain,
            position=HTMLGroup.HEADER
        ).first()

    @staticmethod
    def get_footer():
        return HTMLGroup.objects.filter(
            domain=get_request().domain,
            position=HTMLGroup.HEADER
        ).first()

    def collect_scope(self):
        tags_html = ""
        for tag in self.tags.all():

            content = cache.get(F"{self.domain}-{tag.pk}", False)
            if(not content):
                content = tag.renderElement()
                cache.get(F"{self.domain}-{tag.pk}", content)
            
            tags_html += content

        return tags_html

    def __str__(self):
        return str(self.domain) + " - " + self.nameGroup

class HTMLTag(models.Model):

    JS = "js"
    HTML = "html"

    TypeContent = [
        (JS, "JavaScript"),
        (HTML, "HTML элементы")
    ]

    type = models.CharField(
        verbose_name="Элемент", 
        choices=TypeContent, 
        max_length=200, 
        default=HTML
    )

    group = models.ForeignKey(HTMLGroup, related_name="tags", on_delete=models.CASCADE)
    tag = models.CharField(verbose_name="Тег элемента", max_length=200, default="", blank=True)
    attributes = models.CharField(verbose_name="Атрибуты элемента", max_length=200, default="", blank=True)
    innerHTML = models.TextField(
        max_length=2500, 
        default="", 
        blank=True, 
        verbose_name="Контент", 
    )
    timeoutTime = models.PositiveIntegerField(verbose_name="Время исполнения контента", default=0, help_text="Работает только для JS")

    @property
    def isJS(self):
        return self.type == self.JS

    @property
    def isElement(self):
        return self.type == self.HTML

    def renderElement(self):
        return render_to_string(
            "configuration/element.html",
            context={
                "object": self
            }
        )


class IndexSlide(ImageModel, models.Model):
    domain = models.ManyToManyField('domains.Domain', verbose_name="Домены")
    link = models.CharField(
        verbose_name="Ссылка", blank=True, default="", max_length=127)
    sort = models.PositiveSmallIntegerField('Сортировка', default=0)

    def __str__(self):
        return 'Элемент слайдера №' + str(self.id)

    class Meta:
        verbose_name = _('Элемент слайдера')
        verbose_name_plural = _('Слайдер')
        ordering = ['sort']

    def save(self, *args, **kwargs):
        for domain in Domain.objects.all():
            if cache.get(f'get-cache-index-page-for-{domain.domain}'):
                cache.delete(f'get-cache-index-page-for-{domain.domain}')
                print(f'Удален кэщ для главной страницы на домене {domain.domain}')
        return super(IndexSlide, self).save(*args, **kwargs)


class Delivery(RecipientMixin, models.Model):
    domain = models.ManyToManyField('domains.Domain', blank=True, verbose_name="Домены")
    title = models.CharField('Название', max_length=125)
    id_1c = models.CharField('id 1c', help_text="Для выгрузки заказов", default="", blank=True, max_length=125)
    subtitle = models.CharField('Описание', max_length=125, default="", blank=True)
    selection = models.BooleanField('Выделение описания', default=False)
    stores = models.ManyToManyField('stores.Store', verbose_name="Магазины", blank=True)
    type_price = models.ManyToManyField(TypePrice, verbose_name="Тип цен", blank=True)
    sort = models.PositiveSmallIntegerField('Сортировка', default=0)

    class Meta:
        ordering = ['sort']
        verbose_name = 'Способ доставки'
        verbose_name_plural = 'Способы доставки'

    def __str__(self):
        return self.title


class Payment(models.Model):
    domain = models.ManyToManyField('domains.Domain', blank=True, verbose_name="Домены")
    title = models.CharField('Название', max_length=125)
    sort = models.PositiveSmallIntegerField('Сортировка', default=0)
    type_price = models.ManyToManyField(TypePrice, verbose_name="Тип цен", blank=True)

    class Meta:
        ordering = ['sort']
        verbose_name = 'Способ оплаты'
        verbose_name_plural = 'Способы оплаты'

    def __str__(self):
        return self.title