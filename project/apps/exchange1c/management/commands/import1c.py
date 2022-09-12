import hashlib
import re
import traceback
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
import datetime

from apps.catalog.models import Product, ProductImage, Category, Brand, Prices, Alias, Catalog, SlugCategory
from apps.catalog.models import (
    ProductAttribute, AttributeValue, AttributeProducValue)
from apps.exchange1c.management.commands import in_stock_notification
from apps.domains.models import Domain
from apps.exchange1c.models import Settings
from apps.shop.models import Order
from apps.stores.models import Store, StoreProductQuantity
from django.conf import settings
from django.core.cache import cache
from django.core.files import File
from django.core.exceptions import MultipleObjectsReturned
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db.models import F, Q, Value
from slugify import slugify
import gc

from django.db.models import Q

from .parse import errors


class Command(BaseCommand):
    """
    Импорт из файла 1с

    FOLDER_NAME - имя каталог с файлами выгрузки
    FOLDER_PATH - путь до каталога

    CATEGORIES_CREATED - создано категорий
    CATEGORIES_UPDATED - обновлено категорий
    CATEGORY_EXCLUDE_LIST - список названий категорий,
    которые не должны попадать на сайт
    PRODUCTS_CREATED - создано товаров
    PRODUCTS_UPDATED - обновлено товаров
    FOLDER_IMAGES_NAME - название каталога с картинками
    FOLDER_IMAGES_PATH - путь до каталога с картинками
    DEFAULT_PRICE_NAME - часть названия цены в 1с, которая должна быть на сайте
    если конкретная цена не требуется, то остаить пустой строкой
    """
    FOLDER_NAME = '1c'
    FOLDER_PATH = Path(settings.BASE_DIR) / '../' / FOLDER_NAME

    CATEGORIES_CREATED = 0
    CATEGORIES_UPDATED = 0
    CATEGORY_EXCLUDE_LIST = ['Интернет-магазин']

    PRODUCTS_CREATED = 0
    PRODUCTS_UPDATED = 0

    FOLDER_IMAGES_NAME = 'products'
    FOLDER_IMAGES_PATH = Path(settings.MEDIA_ROOT) / FOLDER_IMAGES_NAME

    DEFAULT_PRICE_NAME = 'розница'

    IS_ACTIVE_ID = 'e2325d8a-84e5-11e8-b0fa-eac9f6b3f8f9'
    DESCRIPTION_ID = 'bd24486d-4900-11e6-bef4-aa13f697773b'
    SPECIAL_ATTRS = [IS_ACTIVE_ID, DESCRIPTION_ID]

    related_products_attrs = []
    related_products = {}
    brands = {}
    not_found = []
    not_quantity = []


    def add_arguments(self, parser):
        parser.add_argument('--filename', default="import1.xml")

    def set_ns(self):
        """
        Устанавливаем пространство имен для файла
        ищем его в корневом теге и сохраняем в словарь
        https://docs.python.org/2/library/xml.etree.elementtree.html#parsing-xml-with-namespaces
        """
        xmlns = re.match(r'\{(?P<ns>.+)\}', self.root.tag)
        if xmlns:
            self.NS = {'ns': xmlns.group('ns')}
        else:
            self.NS = {'ns': ''}

    def set_settings(self):
        """Получаем настройки выгрузки"""
        self.settings = Settings.load()

    @classmethod
    def clear_number(cls, value):
        return re.sub(r'[^\d\.]+', '', value.replace(',', '.'))

    def main(self, *args, **options):
        self.FILE_NAME = options['filename']
        self.FILE_PATH = self.FOLDER_PATH / self.FILE_NAME
        self.domains = Domain.objects.all()
        # проверка файла на существование
        if not self.FILE_PATH.is_file():
            raise errors.FileUndefined(self.FILE_PATH)

        self.root = ET.parse(self.FILE_PATH).getroot()

        self.set_ns()
        self.set_settings()

        if self.root.find('ns:ПакетПредложений', self.NS):
            self.offers()
            print(f'Не найдено товаров: {len(self.not_found)} - {self.not_found}')
            self.clear_cache()
            in_stock_notification.check_stock()
            return

        self.import_attributes()
        self.import_categories()
        self.import_products()
        self.set_variations()
        Category.objects.update(is_active=F('is_import_active'), is_import_active=False)
        Product.objects.update(is_active=F('is_import_active'), is_import_active=False)
        self.set_related()
        self.clear_cache()        

    def clear_cache(self):
        # Ф-я для чистки различного кэша, по мере нужды будет регулярно дополняться
        for item in SlugCategory.objects.all():
            for domain in Domain.objects.all():
                if cache.get(f'get-cache-index-page-for-{domain.domain}'):
                    cache.delete(f'get-cache-index-page-for-{domain.domain}')
                    print(f'Удален кэш для главной страницы на домене {domain.domain}')
                if cache.get(f'get-context-data-filters-for-{item.slug}-on-{domain}'):
                    cache.delete(f'get-context-data-filters-for-{item.slug}-on-{domain}')
                    print(f'Удален кэш фильтров для категории {item.category.title}')
                for user_contractor in range(1, 4):
                    if cache.get(f'render_to_string_{item.slug}-'
                                 f'{user_contractor}-{domain}'):
                        cache.delete(f'render_to_string_{item.slug}-'
                                     f'{user_contractor}-{domain}')
                        print(f'Удален кэш страницы категории {item.category.title} для домена {item.domain.domain}')

    def set_related(self):
        for id_1c, related in self.related_products.items():
            item = Product.objects.filter(id_1c=id_1c).first()
            if item:
                item.related_products.set(Product.objects.filter(id_1c__in=related))
        # gc.collect()
        return self

    def set_variations(self):
        # Если нужна скорость можно поменять логику выгрузки со стороны 1с
        remove_ids = []
        Product.objects.filter(Q(parent__isnull=False) & ~Q(title=F('category__title'))).update(parent=None)
        for product in Product.objects.filter(title=F('category__title')):
            category = product.category
            remove_ids += [category.id]
            category.products.exclude(id=product.id).update(parent_id=product.id, category=category.parent)
            product.category = category.parent
            product.save(update_fields=['category'])
            keys = []
            for domain in self.domains:
                keys += [product.get_key_slug(domain)]
                keys += [category.parent.get_key_slug(domain)]
            cache.delete_many(keys)
        Category.objects.filter(id__in=remove_ids).delete()
        gc.collect()

    def import_products(self):
        self.stdout.write("Импорт товаров")
        items = self.root.findall('ns:Каталог/ns:Товары/ns:Товар', self.NS)
        for item in items:
            try:
                self.import_product(item)
            except errors.Error as e:
                self.stderr.write(str(e))
        call_command('slug_fixer')

    def import_product(self, element):
        id_1c = element.find('ns:Ид', self.NS).text
        title = element.find('ns:Наименование', self.NS).text.replace('^', '').strip(' \n\t')
        try:
            cat_id_1c = element.find(
                'ns:Группы/ns:Ид', self.NS).text
        except AttributeError:
            raise errors.GroupUndefined(id_1c)

        category = Category.objects.get(id_1c=cat_id_1c)

        try:
            description = element.find(
                'ns:Описание', self.NS).text.strip(" \t\n")
        except AttributeError:
            description = ''

        try:
            code = element.find(
                'ns:Артикул', self.NS).text.strip(" \t\n")
        except AttributeError:
            code = None
        product_brand = None
        brand = element.find('ns:Изготовитель', self.NS)
        if brand:
            brand_title = brand.find('ns:Наименование', self.NS).text.strip(" \t\n")
            brand_id = brand.find('ns:Ид', self.NS).text.strip(" \t\n")
            brand = self.brands.get(brand_id, None)
            if not brand:
                brand, created = Brand.objects.get_or_create(id_1c=brand_id,
                                                             defaults={'title': brand_title,
                                                                       'slug': slugify(brand_title)})
                brand.domain.set(self.domains)
                self.brands[brand_id] = brand
            product_brand = brand
        images_elements = element.findall('ns:Картинка', self.NS)
        images_path_list = [image.text for image in images_elements]

        slug = str(title).replace(',', '-').replace('+', 'plus')
        try:
            slug = slugify(slug)
            Product.objects.get(slug=slug)
        except MultipleObjectsReturned:
            slug = slugify(slug + str(Product.objects.filter(slug=slug).count()))
        except Product.DoesNotExist:
            pass

        # !!Возможно придется гененрировать уникальный слаг

        defaults = {
            'title': title,
            'slug': slug,
            #'is_active': True,
            'category': category,
            'code': code,
            # 'old_price': 0,
            # 'description': description,
            'brand': product_brand,
            'is_import_active': True,
        }

        product, created = Product.objects.update_or_create(
            id_1c=id_1c, defaults=defaults)

        print("Спарсенный продукт", product)

        if created:
            product.slug = slug
            product.new = True
            product.description = description
            product.save(update_fields=['slug', 'new', 'description'])
        for domain in self.domains:
            key = product.get_key_slug(domain)
            cache.delete(key)
        product.domain.set(self.domains)

        if created:
            self.PRODUCTS_CREATED += 1
            self.stdout.write(f'{id_1c} {title} создан')
        else:
            self.PRODUCTS_UPDATED += 1
            self.stdout.write(f'{id_1c} {title} обновлен')

        self.set_product_attributes(element, product)

        if images_path_list:
            self.set_images(product, images_path_list)

    # gc.collect()

    def set_images(self, instance, items):
        # первую картинку делаем основной
        image, md5 = self.image_and_hash(items[0])
        # сравниваем хэш сумму
        if image and md5 != instance.image_md5:
            instance.image = image
            instance.image_md5 = md5
            instance.save()

        hash_list = []
        for counter, item in enumerate(items[1:]):
            image, md5 = self.image_and_hash(item)
            if image is None:
                continue
            hash_list.append(md5)
            # проверка картинки на существование в базе
            image_exist = instance.gallery.filter(image_md5=md5).exists()
            if not image_exist:
                ProductImage.objects.create(
                    product=instance, image=image, image_md5=md5
                )
                self.stdout.write(
                    f'Элемент галереи {counter} ({instance.title})')
        instance.gallery.exclude(image_md5__in=hash_list).delete()

    # gc.collect()

    def image_and_hash(self, relative_path):
        # находим путь до картинки
        path = self.FOLDER_IMAGES_PATH / relative_path
        try:
            # !!!! мы нигде не закрываем файл
            # !!!! так как он загружается только при создании товара
            # !!!! нужно придумать что-то другое
            file = open(path, 'rb')
            # создаем объект джанго-файла
            image_file = File(file, name=relative_path)
            # находим хэш
            hash_img = hashlib.md5(file.read()).hexdigest()
        except FileNotFoundError:
            image_file, hash_img = None, None
            self.stderr.write(f'Файл картинки {relative_path} отсутствует')
        # gc.collect()
        return image_file, hash_img

    def set_product_attributes(self, element, product):
        """
        Привязка атрибутов к товару
        """
        items = element.findall(
            'ns:ЗначенияСвойств/ns:ЗначенияСвойства', self.NS)
        ATTR_IDS = []
        for item in items:
            id_1c = item.find('ns:Ид', self.NS).text
            # находим значение атрибута
            # если значения нет => атрибут не выгружаем
            try:
                value = item.find(
                    'ns:Значение', self.NS).text.strip(' \n\t')
            except AttributeError:
                continue

            # проверка на спец атрибуты
            is_special = self.check_special_attributes(id_1c, value, product)
            if is_special:
                continue

            fields = {'product': product}
            print(id_1c)
            attribute = ProductAttribute.objects.get(id_1c=id_1c)
            fields['attribute'] = attribute
            # в зависимости от типа атрибута берем значение
            # если тип справочник, то значение - ид значения
            # если число, то значение - число
            if attribute.type == ProductAttribute.DICT:
                # проверка на ид
                # так как у нас нет строковых атрибутов, то их переводим в словарные
                try:
                    uuid.UUID(value)
                    fields['value_dict'] = AttributeValue.objects.get(
                        id_1c=value)
                except ValueError:
                    fields['value_dict'], _ = AttributeValue.objects.get_or_create(value=value, slug=slugify(value))
            elif attribute.type == ProductAttribute.NUMBER:
                fields['value_number'] = self.clear_number(value)
            else:
                raise errors.InvalidTypeAttribute(id_1c)
            attr, created = AttributeProducValue.objects.get_or_create(
                **fields)
            ATTR_IDS.append(attr.id)
        # удаляем старые атрибуты
        product.product_attributes.exclude(id__in=ATTR_IDS).delete()

    # gc.collect()

    def check_special_attributes(self, id_1c, value, product):
        """
        Проверка на специальный атрибуты.
        Описание товара, выгружать ли товар на сайт и т.д.
        """
        if id_1c == self.IS_ACTIVE_ID:
            # Выгружать на сайт
            if value.lower() == 'да':
                product.is_import_active = False
                product.save(update_fields=['is_import_active'])
            return True
        elif id_1c == self.DESCRIPTION_ID:
            # Описание товара
            product.description = value
            product.save(update_fields=['description'])
            return True
        elif id_1c in self.related_products_attrs:
            # Сопуствующие товары
            if product.id_1c not in self.related_products:
                self.related_products[product.id_1c] = []
            self.related_products[product.id_1c].append(value)
            return True
        return False

    def import_categories(self):
        self.stdout.write("Импорт категорий")
        self.CATEGORIES_IDS = []
        items = self.root.findall(
            'ns:Классификатор/ns:Группы/ns:Группа', self.NS)
        k = 0
        for item in items:
            self.import_category(item)
            k += 1
            if k >= 500:
                gc.collect()
                k = 0
        # деактивируем старые категории
        #Category.objects.exclude(
        #    Q(pk__in=self.CATEGORIES_IDS) | Q(type='alias')).update(is_active=False)

    def import_category(self, element, parent=None):
        # TODO: Добавление доменов m2m
        id_1c = element.find('ns:Ид', self.NS).text.strip(' \n\t')
        title = element.find('ns:Наименование', self.NS).text.strip(' \n\t')

        # проверяем на исключения
        if title not in self.CATEGORY_EXCLUDE_LIST:
            self.stdout.write(f'{id_1c} {title} {parent}')
            slug = slugify(title) if parent else slugify(title)
            # Создание или обновление категории товаров
            defaults = ({
                'title': title,
                # 'slug': slug,
                #'is_active': True,
                'parent': parent,
                'is_import_active': True,
                'old_product_description': ''
            })
            category, created = Category.objects.update_or_create(
                id_1c=id_1c, defaults=defaults)
            if created:
                category.title = title
                # Сделать неактивными для того, чтобы не видны были категории вариативных товаров
                #category.is_active = False
                category.saved_attrs_parent = True
                category.save(update_fields=['title', 'saved_attrs_parent', 'is_active'])
                for domain in self.domains:
                    category.slugs.create(domain=domain, slug=slug)
            category.domain.set(self.domains)
            for domain in self.domains:
                key = category.get_key_slug(domain)
                cache.delete(key)
            # добавление ид категории
            self.CATEGORIES_IDS.append(category.pk)
            # счетчик созданных/обновленных
            if created:
                self.CATEGORIES_CREATED += 1
            else:
                self.CATEGORIES_UPDATED += 1
            # gc.collect()
            # импорт дочерних категорий
            for item in element.findall('ns:Группы/ns:Группа', self.NS):
                self.import_category(item, category)

    def import_attributes(self):
        """Импорт свойств товаров"""
        k = 0
        for item in self.root.findall(
                'ns:Классификатор/ns:Свойства/ns:Свойство', self.NS):
            self.import_attribute(item)
            k += 1
            if k >= 500:
                gc.collect()
                k = 0

    def import_attribute(self, element):
        """Импорт атрибута"""

        def to_import():
            if id_1c in self.SPECIAL_ATTRS:
                return False
            elif 'Сопутствующий товар' in title:
                self.related_products_attrs.append(id_1c)
                return False
            else:
                return True

        id_1c = element.find("ns:Ид", self.NS).text
        title = element.find("ns:Наименование", self.NS).text
        if not to_import():
            self.stdout.write(f'Специальный атрибут: {title} ({id_1c})')
            return
        type_value = element.find("ns:ТипЗначений", self.NS).text
        if type_value == 'Справочник':
            # создаем атрибут
            ProductAttribute.objects.update_or_create(
                id_1c=id_1c, defaults={
                    'title': title,
                    'slug': slugify(title),
                    'type': ProductAttribute.DICT})
            # ищем справочник значений
            values = element.find("ns:ВариантыЗначений", self.NS)
            if values:
                for value_item in values.findall("ns:Справочник", self.NS):
                    value_id = value_item.find('ns:ИдЗначения', self.NS).text
                    value = value_item.find('ns:Значение', self.NS).text
                    AttributeValue.objects.update_or_create(
                        id_1c=value_id, defaults={
                            'value': value,
                            'slug': slugify(value)})

        elif type_value == 'Число':
            # создаем атрибут
            ProductAttribute.objects.get_or_create(
                id_1c=id_1c, defaults={
                    'title': title,
                    'type': ProductAttribute.NUMBER})

        elif type_value == 'Строка':
            # создаем атрибут
            ProductAttribute.objects.update_or_create(
                id_1c=id_1c, defaults={
                    'title': title,
                    'slug': slugify(title),
                    'type': ProductAttribute.DICT})

        self.stdout.write(f'Атрибут:{title} ({id_1c}) создан')

    def import_stores(self):
        """Импорт складов"""
        self.stores = {}
        for item in self.root.findall(
                'ns:ПакетПредложений/ns:Склады/ns:Склад', self.NS):
            self.import_store(item)
        print('=====STORES ', self.stores)

    def import_store(self, store):
        id_1c = store.find("ns:Ид", self.NS).text.strip()
        title = store.find("ns:Наименование", self.NS).text.strip()
        print('=====TITLE ', title)
        address = store.find("ns:Адрес/ns:Представление", self.NS)
        address = ','.join(address.text.split(' ,')) if address else ''
        phone = store.find("ns:Контакты/ns:Контакт[ns:Тип='Телефон рабочий']", self.NS)
        phone = phone.find("ns:Значение", self.NS).text if phone else ''

        street = store.find("ns:Адрес/ns:АдресноеПоле[ns:Тип='Улица']", self.NS)
        street = street.find("ns:Значение", self.NS).text if street else ''

        house = store.find("ns:Адрес/ns:АдресноеПоле[ns:Тип='Дом']", self.NS)
        house = house.find("ns:Значение", self.NS).text if house else ''

        city = store.find("ns:Адрес/ns:АдресноеПоле[ns:Тип='Город']", self.NS)
        city = city.find("ns:Значение", self.NS).text if city else ''
        address = ', '.join([street, house])
        try:
            if not city: raise Domain.DoesNotExist
            domain = Domain.objects.get(name=city)
        except Domain.DoesNotExist:
            return

        defaults = {
            'id_1c': id_1c,
            'title': title,
            'address': address,
            'domain': domain
        }

        defaults = {k: v for k, v in defaults.items() if v}
        print(store, defaults)
        store, created = Store.objects.update_or_create(id_1c=id_1c, defaults=defaults)
        # запоминаем склады, чтобы не получать их при обновлении количества товаров
        self.stores[id_1c] = store

        if created:
            self.stdout.write(f'Склад:{id_1c} создан')
        else:
            self.stdout.write(f'Склад:{id_1c} обновлен')

    def offers(self):
        """
        Обновление цен и количества
        !Актуально только для файла offers.xml
        """
        self.spb = Domain.objects.get(domain='spb.rupechi.ru')

        def set_prices():
            """
            Создание словаря типов цен
            Словарь PRICES:
                key - ид цены в 1с
                value - наименования типа цены в 1с
            В данный момент PRICES не используется,
            оставлен на случай если нужно несколько цен
            PRICE_PATTERN - шаблон поиска цены с помощью XPATH
            MAIN_PRICE_ID - определяем ид 1с для цены на сайте
            """
            self.PRICES = {}
            self.PRICE_PATTERN = None
            MAIN_PRICE_ID = None
            # находим все типы цен
            prices = self.root.findall(
                'ns:ПакетПредложений/ns:ТипыЦен/ns:ТипЦены', self.NS)
            for item in prices:
                price_id = item.find('ns:Ид', self.NS).text
                price_title = item.find(
                    'ns:Наименование', self.NS).text.lower()
                self.PRICES[price_id] = price_title
                if (len(self.DEFAULT_PRICE_NAME) > 0 and
                        self.DEFAULT_PRICE_NAME in price_title):
                    MAIN_PRICE_ID = price_id
            # оперделяем паттерн для нахождения цены
            # если ид основной стоимости найден, то ищем с помощью него
            # иначе берем первую(индексация в XPath начинается с одного)
            if MAIN_PRICE_ID is not None:
                self.PRICE_PATTERN = f"ns:Цены/ns:Цена[ns:ИдТипаЦены='{MAIN_PRICE_ID}']"
            else:
                self.PRICE_PATTERN = f"ns:Цены/ns:Цена[1]"

        set_prices()
        self.import_stores()
        offers = self.root.findall(
            'ns:ПакетПредложений/ns:Предложения/ns:Предложение', self.NS)
        self.line_prices = {}
        for domain in self.domains:
            if domain.id_price:
                self.line_prices[str(domain.id_price)] = {'domain': domain}
        for item in offers:
            c = 0
            try:
                self.offer(item)
            except AttributeError as error:
                self.stderr.write(f"Проблема с информацией в товаре: {error}")
                continue
            c += 1
            if c >= 500:
                gc.collect()
        print('Количество меньше 0: ', len(self.not_quantity))
        print(','.join([str(item.id_1c) for item in self.not_quantity]))

    def offer(self, offer):
        """Обновление цены/количества конкретной товарной позиции"""
        id_1c = offer.find("ns:Ид", self.NS).text.strip()
        for line in self.line_prices:
            self.line_prices[line].update({'price': 0, 'price_1': 0, 'price_2': 0})
        price_1 = offer.find("ns:Цены/ns:Цена[ns:ИдТипаЦены='d5932fd4-4f1a-11eb-93f4-aa4d1c088e1e']", self.NS) \
            .find('ns:ЦенаЗаЕдиницу', self.NS).text.strip(' \t\n')  # Сорокин
        price_2 = offer.find("ns:Цены/ns:Цена[ns:ИдТипаЦены='79ccbb2a-54a3-11eb-a30e-ca7ff23814de']", self.NS) \
            .find('ns:ЦенаЗаЕдиницу', self.NS).text.strip(' \t\n')  # Сорокин
        for price_block in offer.findall('ns:Цены/ns:Цена', self.NS):
            price_block_id = price_block.find('ns:ИдТипаЦены', self.NS).text.strip(' \t\n')
            price_block_price = price_block.find('ns:ЦенаЗаЕдиницу', self.NS).text.strip(' \t\n')
            if price_block_id in self.line_prices.keys():
                self.line_prices[price_block_id].update(
                    {'price': price_block_price, 'price_1': price_1, 'price_2': price_2}
                )
        updated = 0
        product = Product.objects.filter(id_1c=id_1c).first()
        if product:
            for line in self.line_prices.values():
                defaults = line.copy()
                del defaults['domain']
                price = Prices.objects.filter(product=product, domain=line['domain']).first()

                if price:
                    for k, v in defaults.items():
                        setattr(price, k, v)
                        price.save(update_fields=defaults.keys())
                        #price.update_prices()
                else:
                    price = Prices.objects.create(product=product, domain=line['domain'], **defaults)
                    #price.update_prices()

                if line['domain'].domain == 'ivanovo.rupechi.ru':
                    defaults = line.copy()
                    del defaults['domain']
                    price = Prices.objects.filter(product=product, domain=self.spb).first()
                    if price:
                        for k, v in defaults.items():
                            setattr(price, k, v)
                            price.save(update_fields=defaults.keys())
                        #price.update_prices()
                    else:
                        price = Prices.objects.create(product=product, domain=self.spb, **defaults)
                        #price.update_prices()

                updated += 1
                self.set_product_quantity_stores(offer, id_1c)
            if updated > 0:
                self.stdout.write(f'Товар:{id_1c} обновлен {updated}')
            else:
                self.stderr.write(f'Новых цен нет {id_1c}')
        else:
            self.stderr.write(f'Товар:{id_1c} не найден')
            self.not_found += [id_1c]

    def set_product_quantity_stores(self, offer, product_id_1c):
        """Импортируем количество товара на каждом складе"""
        product = Product.objects.get(id_1c=product_id_1c)
        for item in offer.findall('ns:Склад', self.NS):
            store_id_1c = item.attrib['ИдСклада']
            quantity = item.attrib['КоличествоНаСкладе']
            quantity = int(float(quantity))
            if quantity < 0:
                print(quantity, product)
                self.not_quantity.append(product)
                quantity = 10
            store = self.stores.get(store_id_1c)
            if store:
                StoreProductQuantity.objects.update_or_create(
                    product=product,
                    store=store,
                    defaults={'quantity': quantity})
        #         spb_quantity_list = []
        #         spb_quantity_value = 0
        #         if {'ivanovo.rupechi.ru', 'www.rupechi.ru'} & {store.domain.domain.lower()} and \
        #             store.domain.domain.lower() not in spb_quantity_list:
        #             spb_quantity_value += quantity
        #             spb_quantity_list.append(store.domain.domain.lower())
        # if spb_quantity_value:
        #     if StoreProductQuantity.objects.filter(product=product, store=self.SPB_STORE):
        #         spb_product = StoreProductQuantity.objects.get(product=product, store=self.SPB_STORE)
        #         spb_product.quantity = spb_quantity_value
        #         spb_product.save()
        #     else:
        #         StoreProductQuantity(product=product, store=self.SPB_STORE, quantity=spb_quantity_value).save()

    def export_order(self, element):
        """
        Самая сомнительная фукнция из всех
        загрузка заказов из 1с на сайт

        """
        order_id = element.find("ns:Номер", self.NS).text
        if self.settings.order_prefix:
            order_id = self.settings.order_prefix + order_id
        order = Order.objects.get(id=order_id)
        status_elem = element.find(
            "ns:ЗначенияРеквизитов/"
            "ns:ЗначениеРеквизита[ns:Наименование='Статус заказа']", self.NS)
        if status_elem:
            status = status_elem.find('ns:Значение').text
            order.status = self.ORDER_STATUSES[status]
            order.save(update_fields=['status'])

        order_items = order.get_items(True)

        product_elemets = element.findall('ns:Товары/ns:Товар', self.NS)
        products_info = {}
        for product_elem in product_elemets:
            product_id = product_elem.find("ns:Ид", self.NS).text
            quantity = product_elem.find("ns:Количество", self.NS).text
            price = product_elem.find("ns:ЦенаЗаЕдиницу", self.NS).text
            products_info[product_id] = {
                'price': price,
                'quantity': quantity
            }

        # удаляем товарные позиции которых нет в заказе 1с
        order_items.exclude(product__id_1c=products_info.keys()).delete()

        for id_1c, count in products_info:
            try:
                order_items.get_or_create(
                    product_id=Product.objects.filter(id_1c=id_1c).only('id'),
                    defaults={'price': price, 'quantity': quantity})
            except Product.DoesNotExist:
                pass

    def handle(self, *args, **options):
        try:
            self.main(*args, **options)
            with open(self.FOLDER_PATH / '1c_history.txt', 'a') as history_file:
                iso_time = str(datetime.datetime.now().astimezone().replace(microsecond=0).isoformat())
                history_file.writelines(f'\n{iso_time} - SUCCESS')
        except:
            traceback.print_exc()
            with open(self.FOLDER_PATH / '1c_history.txt', 'a') as history_file:
                iso_time = str(datetime.datetime.now().astimezone().replace(microsecond=0).isoformat())
                history_file.write(f'\n{iso_time} - ERROR')

        #for price in Prices.objects.all():
        #    price.update_prices()
