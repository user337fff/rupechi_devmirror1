import os

from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.template.loader import render_to_string, TemplateDoesNotExist
from django.urls import reverse
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey

from apps.commons.models import WithBreadcrumbs, ImageModel
from apps.domains.models import Domain
from apps.domains.models import Domain
from apps.seo.models import SeoBase
from apps.seo.models import SeoBase
from .managers import PageManager, PostManager
from ..catalog.models.category import FullSlugMixin
from ..domains.middleware import get_request
from ..nav.models import MenuItem
from ..seo.templatetags.seo import Seo


class Heading(WithBreadcrumbs, SeoBase):
    title = models.CharField(verbose_name='Название', max_length=127)
    slug = models.SlugField(verbose_name='Слаг', db_index=True)
    domain = models.ManyToManyField(Domain, verbose_name="Домены")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('pages:heading_detail', args=[self.slug])

    class Meta:
        verbose_name = 'Рубрика'
        verbose_name_plural = 'Рубрики'


class BasePage(MPTTModel, WithBreadcrumbs, SeoBase, FullSlugMixin, ImageModel):
    PAGE = 'page'
    POST = 'post'

    TYPES = (
        (PAGE, 'Страница'),
        (POST, 'Пост')
    )
    CATALOG = 'catalog'
    INDEX = 'index'
    TEMPLATES = (
        (INDEX, 'Главная'),
        (CATALOG, 'Каталог'),
    )

    class TemplateChoice(models.TextChoices):
        INDEX = 'index', 'Главная'
        CATALOG = 'catalog', 'Каталог'
        CALCULATOR = 'calculator', 'Калькулятор дымоходов'
        CART = 'cart', 'Корзина'
        ORDER = 'order', 'Оформление заказа'
        MOUNTING = 'mounting', 'Монтаж отопительных приборов'
        REVIEWS = 'reviews', 'Отзывы'
        WISHLIST = 'wishlist', 'Избранное'
        ABOUT = 'about', 'О компании'
        SERVICES = 'services', 'Услуги'
        PAGES = 'pages', 'Полезные статьи'
        OFFERS = 'offers', 'Акции'
        BRANDS = 'brands', 'Производители'
        COMPARE = 'compare', 'Сравнение'
        ADDRESS = 'address', 'Адреса магазинов'
        SEARCH = 'search', 'Страница поиска'
        COOPERATION = 'cooperation', 'Сотрудничество'
        SALE = 'sale', 'Распродажа'
        NEWS = 'news', 'Новости'
        SITEMAP = 'sitemap', 'Карта сайта'
        PRIVACY = 'privacy', 'Политика конфиденциальности'
        PERSONAL = 'personal', 'Обработка персональных данных'
        PUBLIC = 'public', 'Публичная оферта'
        RESET = 'reset', 'Сброс пароля'

        LK = 'lk', 'Личный кабинет'
        CHANGE_PASSWORD = 'change_pass', 'Смена пароля'
        ORDERS = 'orders', 'Мои заказы'

        __empty__ = 'Текстовая страница'

    parent = TreeForeignKey('self', verbose_name='Родительская категория',
                            on_delete=models.CASCADE, blank=True,
                            null=True, related_name='children')
    is_active = models.BooleanField(verbose_name='Активно', default=True)
    type = models.CharField(
        verbose_name='Тип страницы', max_length=7, choices=TYPES, default=PAGE)
    heading = models.ForeignKey(
        Heading, verbose_name='Рубрика', related_name='pages',
        on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(
        verbose_name='Название', max_length=127, db_index=True)
    full_title = models.CharField('Полное название', max_length=250, db_index=True, blank=True, default="")
    description = models.TextField('Описание', default="", blank=True)
    slug = models.SlugField(verbose_name='Слаг', db_index=True)

    template = models.CharField('Шаблон', blank=True, null=True, choices=TemplateChoice.choices, max_length=125)
    has_sidebar = models.BooleanField('Показывать сайдбар', default=True)
    hide_sitemap = models.BooleanField('Скрыть в карте сайта', default=False)
    # dates
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации', default=timezone.now)
    created_at = models.DateTimeField(
        verbose_name='Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField(
        verbose_name='Дата последнего обновления', auto_now=True)

    objects = models.Manager()

    def __str__(self):
        return Seo().clean(self.title)

    def get_absolute_url(self, domain=None, *args, **kwargs):
        templates = {
            self.TemplateChoice.INDEX.value: reverse('index'),
            self.TemplateChoice.CATALOG.value: reverse('catalog'),
            self.TemplateChoice.LK.value: reverse('user-update'),
            self.TemplateChoice.CHANGE_PASSWORD.value: reverse('password_change'),
            self.TemplateChoice.ORDERS.value: reverse('personal-orders'),
            self.TemplateChoice.ADDRESS.value: reverse('pages:address'),
            self.TemplateChoice.SEARCH.value: reverse('search-page'),
            self.TemplateChoice.SALE.value: reverse('sale'),
            self.TemplateChoice.WISHLIST.value: reverse('wishlist:list'),
            self.TemplateChoice.COMPARE.value: reverse('compare:list'),
            self.TemplateChoice.CART.value: reverse('cart:cart_detail'),
            self.TemplateChoice.ORDER.value: reverse('shop:order'),
            self.TemplateChoice.BRANDS.value: reverse('brands'),
        }
        return templates.get(self.template,
                             reverse('pages:page_detail', args=[self.encode_slug(domain)])
                             )

    def get_content_list(self):
        content = []
        content += list(self.texts.all())
        content += list(self.titles_underline.all())
        content += list(self.file_blocks.select_related('block').all())
        content += list(self.gallery_blocks.select_related('block').all())
        content += list(self.slider_blocks.select_related('block').all())
        content += list(self.products_blocks.select_related('block').all())
        content += list(self.reviews_blocks.select_related('block').all())
        content += list(self.spoilers.all())
        content += list(self.titles.all())
        content += list(self.forms.all())
        content += list(self.pages_blocks.select_related('block').all())
        content.sort(key=lambda v: v.sort)
        return content

    class Meta:
        verbose_name = 'Страница'
        verbose_name_plural = 'Страницы'

    def get_breadcrumbs(self, middle=None, callback=None):
        filters = {}
        parents = [
            (parent.__str__(), parent.get_absolute_url())
            for parent in self.get_ancestors().filter(**filters)
        ]
        return super().get_breadcrumbs(middle=parents, callback=callback)


class Page(BasePage):
    """
    Прокси-модель для страниц
    Требуется, чтобы разделить страницы и посты на отдельные составляющие
    Сохраняя при этом структура таблиц в бд
    """
    objects = PageManager()

    class Meta:
        verbose_name = 'Страница'
        verbose_name_plural = 'Страницы'
        proxy = True

    def save(self, *args, **kwargs):
        self.type = self.PAGE
        print(f'======PAGE SAVE {args} \n ---- {kwargs}')
        return super(Page, self).save(*args, **kwargs)

    def get_absolute_url(self, domain=None, *args, **kwargs):
        templates = {
            self.TemplateChoice.INDEX.value: reverse('index'),
            self.TemplateChoice.CATALOG.value: reverse('catalog'),
            self.TemplateChoice.LK.value: reverse('user-update'),
            self.TemplateChoice.CHANGE_PASSWORD.value: reverse('password_change'),
            self.TemplateChoice.ORDERS.value: reverse('personal-orders'),
            self.TemplateChoice.ADDRESS.value: reverse('pages:address'),
            self.TemplateChoice.SEARCH.value: reverse('search-page'),
            self.TemplateChoice.SALE.value: reverse('sale'),
            self.TemplateChoice.WISHLIST.value: reverse('wishlist:list'),
            self.TemplateChoice.COMPARE.value: reverse('compare:list'),
            self.TemplateChoice.CART.value: reverse('cart:cart_detail'),
            self.TemplateChoice.ORDER.value: reverse('shop:order'),
            self.TemplateChoice.BRANDS.value: reverse('brands'),
        }
        return templates.get(self.template,
                             reverse('pages:page_detail', args=[self.encode_slug(domain)])
                             )

    def get_pages(self):
        return MenuItem.get_sidebar()

    def get_subpages(self):
        domain = get_request().domain
        obj = self.parent if self.parent else self
        return obj.get_descendants(include_self=True).filter(is_active=True, domain=domain)


class Post(BasePage):
    """
    Прокси-модель для постов
    В админ-панели также создана отдельная страница
    с обязательным полем "рубрика"
    """

    objects = PostManager()

    def save(self, *args, **kwargs):
        self.type = self.POST
        return super(Post, self).save(*args, **kwargs)

    def get_absolute_url(self, domain=None, *args, **kwargs):
        return reverse('pages:post_detail', args=[self.heading.slug, self.slug])

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ('-pub_date',)
        proxy = True


class BaseContentElement(models.Model):
    """
    Абстрактный класс для элементов контента,
    которые требуется отображать в шаблоне
    """
    template_name = None
    extra_context = None
    sort = models.PositiveIntegerField(verbose_name='Сортировка', default=0)

    def get_context_data(self, **kwargs):
        kwargs.setdefault('object', self)
        if self.extra_context is not None:
            kwargs.update(self.extra_context)
        return kwargs

    def get_template_name(self):
        if self.template_name is None:
            raise TemplateDoesNotExist
        return self.template_name

    def render(self):
        context = self.get_context_data()
        template_name = self.get_template_name()
        return render_to_string(template_name=template_name, context=context)

    class Meta:
        abstract = True


class FormBlock(BaseContentElement):
    class TemplateChoice(models.TextChoices):
        COOP = 'pages/content/coop.html', 'Сотрудничество'
        MOUNTING = 'pages/content/form.html', 'Монтаж'

    template_name = models.CharField('Форма', max_length=125, blank=True, default=TemplateChoice.MOUNTING,
                                     choices=TemplateChoice.choices)
    page = models.ForeignKey('pages.BasePage', related_name='forms', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Форма'
        verbose_name_plural = 'Формы'
        ordering = ['sort']

    def __str__(self):
        return f'Форма'

    def get_template_name(self):
        return self.template_name


class SpoilerBlock(BaseContentElement):
    template_name = 'pages/content/spoiler.html'

    page = models.ForeignKey('pages.BasePage', related_name='spoilers', on_delete=models.CASCADE)
    header = models.CharField('Заголовок', max_length=125)
    text = RichTextUploadingField(verbose_name='Текст')

    class Meta:
        verbose_name = 'Спойлер'
        verbose_name_plural = 'Спойлеры'
        ordering = ['sort']

    def __str__(self):
        return f'Спойлер к {self.page}'


class TitleLinkBlock(BaseContentElement):
    template_name = 'pages/content/title.html'

    page = models.ForeignKey('BasePage', related_name='titles', on_delete=models.CASCADE)
    title = models.CharField('Название', max_length=125)
    btn_title = models.CharField('Название кнопки', max_length=125, default="", blank=True)
    btn_link = models.ForeignKey('BasePage', on_delete=models.CASCADE, verbose_name='Ссылка кнопки', blank=True,
                                 null=True, related_name='title_link')

    class Meta:
        verbose_name = 'Название с кнопкой'
        verbose_name_plural = 'Названия с кнопкой'
        ordering = ['sort']

    def __str__(self):
        return f'{self.title}'


class TextBlock(BaseContentElement):
    template_name = 'pages/content/text.html'

    page = models.ForeignKey(
        'BasePage', related_name='texts', on_delete=models.CASCADE)
    text = RichTextUploadingField(verbose_name='Текст')

    def __str__(self):
        return f'Текстовый контент к {self.page}'

    class Meta:
        verbose_name = 'Текстовый блок'
        verbose_name_plural = 'Текстовые блоки'
        ordering = ('sort',)


class ShortTextBlock(BaseContentElement):
    QUOTE = 'qoute'
    UNDERLINE = 'uline'

    QUOTE_TEMPLATE = 'pages/content/quote.html'
    UNDERLINE_TEMPLATE = 'pages/content/underline.html'

    TYPES = (
        (QUOTE, 'Цитата'),
        (UNDERLINE, 'Подзаголовок с линией')
    )
    page = models.ForeignKey(
        'BasePage', related_name='titles_underline', on_delete=models.CASCADE)
    type = models.CharField(
        verbose_name='Тип отображения',
        choices=TYPES,
        default=UNDERLINE,
        max_length=7)
    text = models.TextField(verbose_name='Текст')
    description = models.TextField(verbose_name='Описание', blank=True, default="")

    def __str__(self):
        return f'Короткий текст к {self.page}'

    def get_template_name(self):
        if self.type == self.QUOTE:
            return self.QUOTE_TEMPLATE
        elif self.type == self.UNDERLINE:
            return self.UNDERLINE_TEMPLATE
        else:
            raise TemplateDoesNotExist

    class Meta:
        verbose_name = 'Короткий текст'
        verbose_name_plural = 'Короткий текст'
        ordering = ('sort',)


class FilesBlock(models.Model):
    title = models.CharField(
        verbose_name='Заголовок блока файлов', max_length=63)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Блок с файлами'
        verbose_name_plural = 'Блоки с файлами'


class FilesBlockItem(models.Model):
    block = models.ForeignKey(
        'FilesBlock', related_name='files_items', on_delete=models.CASCADE)
    file = models.FileField(
        verbose_name='Файл', upload_to='files/pages/content/filesblock/')
    title = models.CharField(
        verbose_name='Подпись к файлу', max_length=63)

    def __str__(self):
        return self.title

    def extension(self):
        name, extension = os.path.splitext(self.file.name)
        return extension

    def get_size(self):
        size = os.path.getsize(self.file.path)
        sizes = [" Б", " Кб", " Мб"]
        if size < 512000:
            size = size / 1024.0
            ext = 'Кб'
        elif size < 4194304000:
            size = size / 1048576.0
            ext = 'Мб'
        else:
            size = size / 1073741824.0
            ext = 'Гб'
        return f'{size} {ext}'

    class Meta:
        verbose_name = 'Элемент блока файлов'
        verbose_name_plural = 'Элементы блока файлов'


class Files(BaseContentElement):
    template_name = 'pages/content/files.html'

    page = models.ForeignKey(
        'BasePage', related_name='file_blocks', on_delete=models.CASCADE)
    block = models.OneToOneField(
        'FilesBlock', verbose_name='Блок файлов', on_delete=models.CASCADE)

    def __str__(self):
        return ""

    class Meta:
        verbose_name = 'Файлы'
        verbose_name_plural = 'Файлы'
        ordering = ('sort',)


class PagesBlock(models.Model):
    title = models.CharField(
        verbose_name='Заголовок блока страниц', max_length=63)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Блок страниц'
        verbose_name_plural = 'Блоки страниц'

    def get_pages(self):
        domain = get_request().domain
        return self.pages_items.select_related('page').filter(page__domain__exact=domain)


class PagesBlockItem(models.Model):
    block = models.ForeignKey(
        'PagesBlock', related_name='pages_items', on_delete=models.CASCADE)
    page = models.ForeignKey('pages.BasePage', verbose_name="Страница", on_delete=models.CASCADE)
    sort = models.PositiveIntegerField(verbose_name='Сортировка', default=0)

    def __str__(self):
        return f'Элемент блока страниц {self.id}'

    class Meta:
        verbose_name = 'Элемент блока страниц'
        verbose_name_plural = 'Элементы блока страниц'
        ordering = ('sort',)


class Pages(BaseContentElement):
    template_name = 'pages/content/pages.html'

    page = models.ForeignKey(
        'BasePage', related_name='pages_blocks', on_delete=models.CASCADE)
    block = models.ForeignKey(
        'PagesBlock', verbose_name='Блок страниц', on_delete=models.CASCADE)

    def __str__(self):
        return f'Страницы'

    class Meta:
        verbose_name = 'Страницы'
        verbose_name_plural = 'Страницы'
        ordering = ('sort',)


class GalleryBlock(models.Model):
    title = models.CharField(
        verbose_name='Заголовок блока галлереи', max_length=63)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Блок галлереи'
        verbose_name_plural = 'Блоки галлереи'


class GalleryBlockItem(models.Model):
    block = models.ForeignKey(
        'GalleryBlock', related_name='gallery_items', on_delete=models.CASCADE)
    image = models.ImageField(
        verbose_name='Изображение', upload_to='images/pages/content/gallery/')
    title = models.CharField(
        verbose_name='Подпись к файлу', max_length=63, default="", blank=True)
    sort = models.PositiveIntegerField(verbose_name='Сортировка', default=0)

    def __str__(self):
        return f'Элемент галлереи {self.id}'

    class Meta:
        verbose_name = 'Элемент блока галлереи'
        verbose_name_plural = 'Элементы блока галлерии'
        ordering = ('sort',)


class Gallery(BaseContentElement):
    template_name = 'pages/content/gallery.html'

    page = models.ForeignKey(
        'BasePage', related_name='gallery_blocks', on_delete=models.CASCADE)
    block = models.ForeignKey(
        'GalleryBlock', verbose_name='Блок галлереи', on_delete=models.CASCADE)

    def __str__(self):
        return ""

    class Meta:
        verbose_name = 'Галлерея'
        verbose_name_plural = 'Галлерея'
        ordering = ('sort',)


class SliderBlock(models.Model):
    title = models.CharField(
        verbose_name='Заголовок блока со слайдером', max_length=63)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Блок со слайдером'
        verbose_name_plural = 'Блоки со слайдером'


class SliderBlockItem(models.Model):
    block = models.ForeignKey(
        'SliderBlock', related_name='slider_items', on_delete=models.CASCADE)
    image = models.ImageField(
        verbose_name='Изображение', upload_to='images/pages/content/slider/')
    title = models.CharField(
        verbose_name='Подпись', default='', blank=True, max_length=63)
    sort = models.PositiveIntegerField(verbose_name='Сортировка', default=0)

    def __str__(self):
        return f'Элемент слайдера {self.id}'

    class Meta:
        verbose_name = 'Элемент блока слайдера'
        verbose_name_plural = 'Элементы блока слайдера'
        ordering = ('sort',)


class Slider(BaseContentElement):
    template_name = 'pages/content/slider.html'

    page = models.ForeignKey(
        'BasePage', related_name='slider_blocks', on_delete=models.CASCADE)
    block = models.OneToOneField(
        'SliderBlock', verbose_name='Блок слайдера', on_delete=models.CASCADE)

    def __str__(self):
        return ""

    class Meta:
        verbose_name = 'Слайдер'
        verbose_name_plural = 'Слайдер'
        ordering = ('sort',)


class ProductsBlock(models.Model):
    title = models.CharField(
        verbose_name='Заголовок блока с товарами', max_length=63)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Блок товаров'
        verbose_name_plural = 'Блоки товаров'
        # ordering = ('sort',)


# проверка существования модуля каталога
# подробнее в README.txt
try:
    from apps.catalog.models import Product

    product_field = models.ForeignKey(Product, on_delete=models.CASCADE)
except ImportError:
    product_field = None


class ProductsBlockItem(models.Model):
    block = models.ForeignKey(
        'ProductsBlock', related_name='products_items', on_delete=models.CASCADE)
    product = product_field
    sort = models.PositiveIntegerField(verbose_name='Сортировка', default=0)

    def __str__(self):
        return f'Элемент слайдера {self.id}'

    class Meta:
        verbose_name = 'Элемент блока товаров'
        verbose_name_plural = 'Элементы блока товаров'
        ordering = ('sort',)


class Products(BaseContentElement):
    template_name = 'pages/content/products.html'

    page = models.ForeignKey(
        'BasePage', related_name='products_blocks', on_delete=models.CASCADE)
    block = models.OneToOneField(
        'ProductsBlock', verbose_name='Блок товаров', on_delete=models.CASCADE)

    def __str__(self):
        return ""

    class Meta:
        verbose_name = 'Товары'
        verbose_name_plural = 'Товары'
        ordering = ('sort',)


class ReviewsBlock(models.Model):
    title = models.CharField(
        verbose_name='Заголовок блока с отзывами', max_length=63)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Блок отзывов'
        verbose_name_plural = 'Блоки отзывов'


class ReviewsBlockItem(models.Model):
    block = models.ForeignKey(
        'ReviewsBlock', related_name='reviews_items', on_delete=models.CASCADE)
    name = models.CharField(verbose_name='Имя', max_length=127)
    avatar = models.ImageField(
        verbose_name='Аватар', upload_to='images/pages/content/reviews/')
    text = models.TextField(verbose_name='Текст отзыва')
    sort = models.PositiveIntegerField(verbose_name='Сортировка', default=0)

    def __str__(self):
        return f'Элемент отзывов {self.id}'

    class Meta:
        verbose_name = 'Элемент блока отзывов'
        verbose_name_plural = 'Элементы блока отзывов'
        ordering = ('sort',)


class Reviews(BaseContentElement):
    template_name = 'pages/content/reviews.html'

    page = models.ForeignKey(
        'BasePage', related_name='reviews_blocks', on_delete=models.CASCADE)
    block = models.OneToOneField(
        'ReviewsBlock', verbose_name='Блок отзывов', on_delete=models.CASCADE)

    def __str__(self):
        return ""

    class Meta:
        verbose_name = 'Отзывы'
        verbose_name_plural = 'Отзывы'
        ordering = ('sort',)
