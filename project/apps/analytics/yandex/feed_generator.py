import os
from datetime import datetime
from pathlib import Path

from apps.catalog import models as catalog_models
from apps.domains.models import Domain
from lxml import etree
from slugify import slugify
from system import settings


class YandexFeedGenerator:
    """
    Генератор фида для яндекс маркета(подходит для метрики)

    Спецификации https://yandex.ru/support/partnermarket/export/yml.html#about-yml
    
    """
    FOLDER_NAME = 'feed'
    FOLDER_PATH = Path(settings.MEDIA_ROOT) / FOLDER_NAME
    FILE_NAME = 'yafeed.xml'
    FILE_PREFIX = ''

    SITE_URL = "https://www.rupechi.ru/"
    SHORT_IMAGE_URL = "/photoproducts/"
    TRANSPORT_PROTOCOL = "https://"

    FEED_TITLE = 'ЖарДаПар'
    FEED_LINK = SITE_URL
    FEED_COMPANY = 'ЖарДаПар'
    domain = ''

    CURRENCY = 'RUB'

    queryset_products = catalog_models.Product.objects.active()
    queryset_categories = catalog_models.Category.objects.filter(is_active=True)

    @property
    def FILE_PATH(self):
        return self.FOLDER_PATH / f'{self.FILE_PREFIX}_{self.FILE_NAME}'

    def generate(self, domainTitle=""):
        """Генерация фида"""
        self.FOLDER_PATH.mkdir(parents=True, exist_ok=True)
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M")

        print(domainTitle)
        if(domainTitle):
            iterator = Domain.objects.filter(name__icontains=domainTitle)

        else:
            iterator = Domain.objects.iterator()

        for domain in iterator:
            print("Start xml generation")
            print(domain)
            self.domain = domain
            self.FILE_PREFIX = slugify(domain.name)
            self.FEED_LINK = self.TRANSPORT_PROTOCOL + self.domain.domain
            catalog_xml = etree.Element('yml_catalog', date=date_now)
            catalog_xml.append(self.generate_shop())

            doc = etree.ElementTree(catalog_xml)
            print("Finish xml generation")
            doc.write(str(self.FILE_PATH), pretty_print=True,
                      xml_declaration=True, encoding='UTF-8')


        self.domain = Domain.objects.get(domain="www.rupechi.ru")
        self.FILE_PREFIX = "checking_file_main"
        self.FEED_LINK = self.TRANSPORT_PROTOCOL + self.domain.domain
        catalog_xml = etree.Element('yml_catalog', date=date_now)
        catalog_xml.append(self.generate_shop(True))

        doc = etree.ElementTree(catalog_xml)
        print("Finish xml generation")
        doc.write(str(self.FILE_PATH), pretty_print=True,
                    xml_declaration=True, encoding='UTF-8')


    def generate_shop(self, shortLinks=False):
        xml = etree.Element('shop')
        etree.SubElement(xml, "name").text = self.FEED_TITLE

        etree.SubElement(xml, "company").text = self.FEED_COMPANY

        etree.SubElement(xml, "url").text = self.FEED_LINK

        currencies = etree.SubElement(xml, "currencies")
        etree.SubElement(currencies, "currency", id=self.CURRENCY, rate="1")

        # categories
        print("Generate categories")
        categories = etree.SubElement(xml, 'categories')
        for category in self.queryset_categories.filter(domain__exact=self.domain).iterator():
            print("*", category.title)
            categories.append(self.generate_category(category))
        print("Categories generated")

        etree.SubElement(xml, 'delivery').text = 'false'

        # offers
        print("Generate offers")
        offers = etree.SubElement(xml, 'offers')
        for product in self.queryset_products.filter(domain__exact=self.domain).iterator():
            print("**", product.title)
            offers.append(self.generate_product(product, shortLinks))
        print("Offers generated")

        return xml

    def generate_product(self, product, shortLinks=False):
        #available = 'true' if product.quantity_stores.filter(quantity__gt=0).exists() else 'false'
        available = 'true'
        xml = etree.Element('offer', id=str(product.id), available=available)

        etree.SubElement(xml, 'name').text = product.title
        if product.brand:
            etree.SubElement(xml, 'vendor').text = product.brand.title

        url = etree.SubElement(xml, 'url')
        url.text = self.FEED_LINK + product.get_absolute_url()
        prices = product.get_storage_info(domain=self.domain)
        price = prices.get('price')
        if price:
            etree.SubElement(xml, 'price').text = str(price)
        old_price = prices.get('discount_price') or prices.get('old_price')
        if old_price > 0 and old_price > price:
            etree.SubElement(xml, 'oldprice').text = str(old_price)

        etree.SubElement(xml, 'currencyId').text = self.CURRENCY

        etree.SubElement(xml, 'categoryId').text = str(product.category_id)

        print("--------------PRODUCT-------")
        print(product.pk)
        if product.image:
            picture_xml = etree.SubElement(xml, 'picture')

            image_link = self.FEED_LINK + product.image.url

            if(shortLinks):
                image_link = image_link.replace("/media/images/catalog/product/import_files/", self.SHORT_IMAGE_URL)

            picture_xml.text = image_link
            print("FEED PHOTO URL", image_link)

        for pic in product.gallery.all():
            picture_xml = etree.SubElement(xml, 'picture')

            image_link = self.FEED_LINK + pic.image.url

            if(shortLinks):
                image_link = image_link.replace("/media/images/catalog/product/import_files/", self.SHORT_IMAGE_URL)

            picture_xml.text = image_link
            print("FEED PHOTO URL", image_link)

        if product.description:
            description = etree.SubElement(xml, 'description')
            description.text = etree.CDATA(product.description)

        params = product.product_attributes \
            .select_related('attribute', 'value_dict').all()
        for param in params:
            param_xml = etree.SubElement(xml, 'param',
                                         name=param.attribute.title)
            param_xml.text = str(param.value)

        return xml

    def generate_category(self, category):
        kwargs = {"id": str(category.id)}
        if category.parent_id:
            kwargs['parentId'] = str(category.parent_id)
        xml = etree.Element("category", **kwargs)
        xml.text = category.title
        return xml
