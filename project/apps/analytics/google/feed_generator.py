# import os
from datetime import datetime
from pathlib import Path

from apps.catalog import models as catalog_models
from apps.domains.models import Domain
from lxml import etree
from system import settings
from slugify import slugify


class GoogleFeedGenerator:
    """
    Генератор фида для гугл мерчант центра

    Спецификации https://support.google.com/merchants/answer/7052112
    
    """
    FOLDER_NAME = 'feed'
    FOLDER_PATH = Path(settings.MEDIA_ROOT) / FOLDER_NAME
    FILE_NAME = 'gfeed.xml'
    SITE_URL = "https://www.rupechi.ru"

    XHTML_NAMESPACE = "http://base.google.com/ns/1.0"
    XHTML = "{%s}" % XHTML_NAMESPACE
    NSMAP = {'g': XHTML_NAMESPACE}

    _FILE_PATH = None
    FILE_PREFIX = ''
    FEED_TITLE = 'ЖарДаПар'
    FEED_DESCRIPTION = 'ЖарДаПар'
    domain = None

    CURRENCY = 'RUB'

    queryset_products = catalog_models.Product.objects.active()

    def generate(self):
        """Генерация фида"""
        self.FOLDER_PATH.mkdir(parents=True, exist_ok=True)
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
        for domain in Domain.objects.iterator():
            print("Start xml generation", domain)
            self.domain = domain
            self.FEED_LINK = f'https://{self.domain.domain}'
            self.FILE_PREFIX = slugify(self.domain.name)
            self.queryset_products = self.queryset_products.filter(domain__exact=self.domain, image__gt=0)
            rss_xml = etree.Element('rss', nsmap=self.NSMAP)
            self.channel_xml = etree.SubElement(rss_xml, "channel")
            etree.SubElement(self.channel_xml, "title").text = self.FEED_TITLE
            etree.SubElement(self.channel_xml, "link").text = self.FEED_LINK
            etree.SubElement(self.channel_xml, "description").text = self.FEED_DESCRIPTION

            self.generate_products()

            doc = etree.ElementTree(rss_xml)
            print("Finish xml generation", domain)
            doc.write(str(self.FILE_PATH), pretty_print=True,
                      xml_declaration=True, encoding='UTF-8')

    @property
    def FILE_PATH(self):
        return self.FOLDER_PATH / f'{self.FILE_PREFIX}_{self.FILE_NAME}'

    def generate_products(self):
        """Генерация товаров"""
        for item in self.queryset_products:
            self.channel_xml.append(self.generate_product(item))

    def generate_product(self, product):
        """Генерация одного элемента товара"""
        xml = etree.Element('item')

        # Основные сведения о товарах
        etree.SubElement(xml, f'{self.XHTML}id').text = str(product.pk)
        etree.SubElement(xml, f'{self.XHTML}title').text = product.title
        description = etree.SubElement(xml, f'{self.XHTML}description')
        if product.description:
            description.text = product.description
        else:
            description.text = product.title
        link = etree.SubElement(xml, 'link')
        link.text = self.FEED_LINK + product.get_absolute_url()
        if product.image:
            image_link = self.FEED_LINK + product.image.url
            etree.SubElement(xml, f'{self.XHTML}image_link').text = image_link

        # Цена и наличие
        # Все товары должны быть доступными, несмотря на кол-во
        availability = etree.SubElement(xml, f'{self.XHTML}availability')
        #stock = product.quantity_stores \
        #    .select_related('store') \
        #    .filter(store__domain=self.domain, quantity__gt=0) \
        #    .exists()
        #if stock:
        #    availability.text = 'in_stock'
        #else:
        #    availability.text = 'out_of_stock'
        availability.text = 'in_stock'

        price = etree.SubElement(xml, f'{self.XHTML}price')
        prices = product.get_storage_info(domain=self.domain)
        old_price = prices.get('discount_price') or prices.get('old_price')
        if old_price:
            price.text = f'{prices.get("price")} {self.CURRENCY}'

            sale_price = etree.SubElement(xml, f'{self.XHTML}sale_price')
            sale_price.text = f'{old_price} {self.CURRENCY}'
        else:
            price.text = f'{prices.get("price")} {self.CURRENCY}'
        if prices.get('price') < 5000:
            etree.SubElement(xml, f'{self.XHTML}custom_label_0').text = 'true'

        # Категория товара
        product_type = etree.SubElement(xml, f'{self.XHTML}product_type')
        product_type_values = [title for title, slug in product.get_breadcrumbs()[1:-1]]
        product_type.text = ' > '.join(product_type_values)

        # Идентификаторы товара
        if product.brand:
            etree.SubElement(xml, f'{self.XHTML}brand').text = product.brand.title
        # обязательный атрибут для товаров у которых есть gtin
        # etree.SubElement(xml, f'{self.XHTML}gtin').text = product.gtin

        # Подробное описание товара
        etree.SubElement(xml, f'{self.XHTML}condition').text = 'new'

        # Торговые кампании и другие инструменты
        etree.SubElement(xml, f'{self.XHTML}ads_redirect').text = link.text
        print('generate product', product)

        return xml
