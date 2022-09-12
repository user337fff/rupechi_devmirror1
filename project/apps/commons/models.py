import gc
import hashlib
import os
import urllib

from PIL import Image
from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_save
from django.template.defaultfilters import safe
from sorl.thumbnail import get_thumbnail

from apps.domains.middleware import get_request
from system.settings import BASE_DIR, MEDIA_ROOT


def image_directory_path(instance, filename):
    app = instance._meta.app_label
    model = instance._meta.model_name
    return f'images/{app}/{model}/{filename}'


class FullSlugMixin(models.Model):
    domain = models.ManyToManyField('domains.Domain', verbose_name="Домены", blank=True)
    slug = models.SlugField(verbose_name='Слаг', max_length=255, db_index=True)

    class Meta:
        abstract = True

    def get_key_slug(self, domain=None):
        class_name = self.__class__.__name__
        if class_name in ['Page', 'BasePage']:
            class_name = 'Page'
        return f"{domain.domain + '_' if domain else ''}{class_name}_{self.id}"

    def get_slug(self, domain=None, *args, **kwargs):
        # TODO: Меньше запросов, но нет проверки по поддоменам
        key = self.get_key_slug(domain)
        slug = cache.get(key)
        if not slug:
            if hasattr(self, 'get_ancestors'):
                slugs = self.get_ancestors(include_self=True) \
                    .filter(is_active=True, domain__exact=domain) \
                    .values_list('slug', flat=True)
                if not slugs:
                    slugs = [self.slug]
            else:
                slugs = [self.slug]
            slug = '/'.join([slug for slug in slugs if slug])
            cache.set(key, slug)
        return slug

    def encode_slug(self, domain=None, *args, **kwargs):
        domain = domain or get_request().domain
        slug = self.get_slug(domain=domain)
        return slug

    @staticmethod
    def decode_slug(slugs, *args, **kwargs):
        return slugs.split('/')[-1]


class WithBreadcrumbs:
    """Интерфейс для хлебных крошек"""

    _BASE = [
        ('Главная', '/'),
    ]

    title = ""

    def get_absolute_url(self, *args, **kwargs):
        # для обязательного переопределения
        raise AttributeError('Override get_absolute_url method')

    def get_breadcrumbs(self, middle=None, callback=None):
        breadcrumbs = []
        breadcrumbs += self._BASE
        if middle is not None:
            breadcrumbs += middle
        breadcrumbs.append(self.get_last_crumb())

        if callable(callback):
            for index, breadcrumb in enumerate(breadcrumbs):
                value, url = breadcrumb
                breadcrumbs[index] = (callback(value), url)
        return breadcrumbs

    def get_last_crumb(self):
        return self.title, self.get_absolute_url()


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(pk=self.pk).delete()
        super(SingletonModel, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()


class WebpImages(models.Model):
    to_webp_fields = ('image', 'image_s', 'image_m', 'image_l')

    _media_dir = 'webp_cache'

    webp_image = models.TextField(verbose_name='Полный путь до webp', null=True, blank=True)
    webp_hash_image = models.TextField(verbose_name='Хэш для webp', null=True, blank=True)

    webp_image_s = models.TextField(verbose_name='Полный путь до webp_small', null=True, blank=True)
    webp_hash_image_s = models.TextField(verbose_name='Хэш для webp_small', null=True, blank=True)

    webp_image_m = models.TextField(verbose_name='Полный путь до webp_medium', null=True, blank=True)
    webp_hash_image_m = models.TextField(verbose_name='Хэш для webp_medium', null=True, blank=True)

    webp_image_l = models.TextField(verbose_name='Полный путь до webp_large', null=True, blank=True)
    webp_hash_image_l = models.TextField(verbose_name='Хэш для webp_large', null=True, blank=True)

    class Meta:
        abstract = True

    @staticmethod
    def _convert_and_save_webp(full_path, pil_image):
        pil_image = pil_image.convert("RGBA")
        pil_image.save(full_path, "webp")

    @staticmethod
    def _create_path(full_path):
        dirs_path = full_path[:full_path.rfind('/')]
        if not os.path.exists(dirs_path):
            os.makedirs(dirs_path)

    @staticmethod
    def _get_relative_path(relative_path):
        return os.path.join('/media', '{}.webp'.format(relative_path))

    def _create(self, full_path, relative_path, pil_image):
        self._create_path(full_path),
        self._convert_and_save_webp(full_path, pil_image)
        return self._get_relative_path(relative_path)

    def _get_or_create(self, full_path, relative_path, pil_image):
        self._create_path(full_path)
        #  Проверяем существование webp для данного объекта
        if not os.path.isfile(full_path):
            return self._create(full_path, relative_path, pil_image)
        return self._get_relative_path(relative_path)

    def webp(self):
        """Вернет словарь вида:
        название_поля: путь до webp от media
        """

        converted = {}
        if not self.to_webp_fields:
            return

        for field in self.to_webp_fields:
            #  Получаем хеш изображения для поиска
            image = getattr(self, field)
            if not image:
                continue

            try:
                pil_image = Image.open(BASE_DIR + '/..' + image.url)
            except:
                return
            # pil_image = Image.open(urllib.parse.unquote(BASE_DIR + '/..' + image.url))

            image_hash = hashlib.md5(pil_image.tobytes()).hexdigest()

            # сравниваем хеш открытой фотки и той, от которой сделано текущее webp
            if image_hash != getattr(self, 'webp_hash_' + field) or not os.path.exists(getattr(self, 'webp_' + field)):
                # проверяем наличие webp
                if getattr(self, 'webp_' + field):
                    try:
                        # удаляем текущее webp
                        os.remove(
                            BASE_DIR + '/..' + getattr(self, 'webp_' + field))
                        print('removed ' + BASE_DIR +
                              '/..' + getattr(self, 'webp_' + field))
                    except Exception as e:
                        print(e)
                        print('Старый файл не найден')

                #  Получаем путь от media
                class_name = self.__class__.__name__
                relative_path = os.path.join(self._media_dir, class_name, field, f'{image_hash}{self.id}')

                #  Получаем полный путь и ищем сохраненные webp изображения
                full_path = os.path.join(MEDIA_ROOT, '{}.webp'.format(relative_path))

                converted[field] = self._get_or_create(full_path, relative_path, pil_image)
                setattr(self, 'webp_' + field, converted[field])
                setattr(self, 'webp_hash_' + field, image_hash)
                print('created webp ' + converted[field])
            else:
                print('webp image already created', self)
            # gc.collect()

        return WebpFieldsObject(**converted)

    def _get_template_picture(self, size=''):
        """
            15.12
            Не отображались картинки пришлось временно убрать вебп
        """
        try:
            if size:
                size = '_' + size
            return safe(f"""
                    <picture itemscope itemtype="https://schema.org/ImageObject">
                        <div itemprop="name" hidden>{getattr(self, 'title')}</div>
                       <source srcset="{getattr(self, 'image' + size).url}" type="image/png">
                      <img src="{getattr(self, 'image'+ size)}" alt="{self.__str__()}" itemprop="url image">
                   </picture>
            """)
        except:
            return safe(f"""
                    <picture itemscope itemtype="https://schema.org/ImageObject">
                       <source srcset="{getattr(self, 'image' + size).url}" type="image/png">
                      <img src="{getattr(self, 'image'+ size)}" alt="{self.__str__()}" itemprop="url image">
                   </picture>
            """)
        # try:
        #     if size:
        #         size = '_' + size
        #     return safe(f"""
        #             <picture itemscope itemtype="https://schema.org/ImageObject">
        #                 <div itemprop="name" hidden>{getattr(self, 'title')}</div>
        #                 <source srcset="{getattr(self, 'webp_image'+ size)}" type="image/webp">
        #                <source srcset="{getattr(self, 'image' + size).url}" type="image/png">
        #               <img src="{getattr(self, 'webp_image'+ size)}" alt={self.__str__()} loading="lazy" itemprop="url image">
        #            </picture>
        #     """)
        # except:
        #     return safe(f"""
        #             <picture itemscope itemtype="https://schema.org/ImageObject">
        #                 <source srcset="{getattr(self, 'webp_image'+ size)}" type="image/webp">
        #                <source srcset="{getattr(self, 'image' + size).url}" type="image/png">
        #               <img src="{getattr(self, 'webp_image'+ size)}" alt={self.__str__()} loading="lazy" itemprop="url image">
        #            </picture>
        #     """)

    def get_template_picture(self):
        try:
            return self._get_template_picture()
        except:
            self.webp()
            self.save()

    def get_template_picture_small(self):
        try:
            return self._get_template_picture('s')
        except:
            self.webp()
            self.save()

    def get_template_picture_medium(self):
        try:
            return self._get_template_picture('m')
        except:
            self.webp()
            self.save()

    def get_template_picture_large(self):
        try:
            return self._get_template_picture('l')
        except:
            self.webp()
            self.save()


def create_webp(sender, instance, **kwargs):
    # Делаем дополнительный save на объекте для создания webp
    post_save.disconnect(create_webp)
    if issubclass(sender, WebpImages):
        instance.webp()
        try:
            instance.save()
        except:
            pass
    post_save.connect(create_webp)


post_save.connect(create_webp)


class WebpFieldsObject:
    def __init__(self, **kwargs):
        for field, value in kwargs.items():
            setattr(self, field, value)


class ImageModel(WebpImages, models.Model):
    """ Абстрактный класс, содержащий изображение и его хэш """

    THUMBNAIL_S = ('100x100', 70)
    THUMBNAIL_M = ('300x200', 80)
    THUMBNAIL_L = ('500x500', 95)

    image = models.ImageField(verbose_name='Изображение',
                              upload_to=image_directory_path,
                              blank=True, null=True)
    image_md5 = models.CharField(verbose_name='Хэш изображения', blank=True,
                                 default='', max_length=63,
                                 help_text='Заполняется автоматически')

    def image_hash(self):
        """ Получение хэша картинки """
        md5 = self.image_md5
        if not md5:
            md5 = self.calc_image_hash(save=False)
        return md5

    def calc_image_hash(self, save=True):
        """ Вычисление хэша картинки """
        self.image_md5 = ""
        if self.image:
            self.image_md5 = hashlib.md5(self.image.read()).hexdigest()
        if save:
            self.save(update_fields=['image_md5'])
        return self.image_md5

    def save_with_hash(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.calc_image_hash()

    def get_thumbnail(self, props):
        """
        Получение миниатюры

        props - кортеж из двух элементов (размер миниатюры, качество)
        """
        if self.image:
            size, quality = props
            return get_thumbnail(
                self.image,
                size,
                quality=quality)

    @property
    def image_s(self):
        return self.get_thumbnail(self.THUMBNAIL_S)

    @property
    def image_m(self):
        return self.get_thumbnail(self.THUMBNAIL_M)

    @property
    def image_l(self):
        return self.get_thumbnail(self.THUMBNAIL_L)

    class Meta:
        abstract = True
