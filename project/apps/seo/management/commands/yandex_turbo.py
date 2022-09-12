from datetime import datetime
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

from apps.catalog.models import Category, Product
from apps.domains.models import Domain
from django.core.management import BaseCommand
from django.db.models import Sum
from slugify import slugify
from system import settings


class Command(BaseCommand):
    root, domain = None, None

    def handle(self, *args, **options):
        for domain in Domain.objects.iterator():
            self.domain = domain
            self.root = Element('yml_catalog')
            self.root.set('date', str(datetime.now().strftime("%y-%d-%m %H:%m")))
            self.set_shop()
            self.root = '<?xml version="1.0" encoding="UTF-8"?>\n' + self.prettify(self.root)
            self.root = self.root.replace('<?xml version="1.0" ?>\n', "")
            with open(settings.MEDIA_ROOT + '/feed/' + slugify(self.domain.name) + '_feed.xml', "w+") as f:
                f.write(self.root)
            print(domain, 'окончен', '*' * 80)

    @classmethod
    def prettify(cls, elem):
        rough_string = tostring(elem, 'utf-8')
        parsed = minidom.parseString(rough_string)
        return parsed.toprettyxml(indent='   ')

    @classmethod
    def create_block(cls, block, name, value=None, **kwargs):
        response = SubElement(block, name)
        if value:
            response.text = str(value)
        for k, v in kwargs.items():
            response.set(k, str(v))
        return response

    def set_shop(self):
        shop = SubElement(self.root, 'shop')
        for name, value in (
                ('name', 'RuPechi'),
                ('company', 'RuPechi'),
                ('url', self.get_full_url())
        ):
            self.create_block(shop, name, value)
        self.set_currencies(shop)
        self.set_categories(shop)
        self.set_offers(shop)

    def set_currencies(self, block):
        currencies = self.create_block(block, 'currencies')
        self.create_block(currencies, 'currency', id='RUB', rate="1")

    def set_categories(self, block):
        categories = self.create_block(block, 'categories')
        for category in Category.objects.filter(is_active=True, domain__exact=self.domain).iterator():
            extra = {}
            if category.parent:
                extra['parentId'] = category.parent_id
            self.create_block(categories, 'category', category.title, id=str(category.id), **extra)
            print('create', category)

    def get_full_url(self, absolute_link=''):
        return 'https://' + self.domain.domain + absolute_link

    def set_offers(self, block):
        offers = self.create_block(block, 'offers')
        for product in Product.objects.filter(
                is_active=True, category__is_active=True, domain__exact=self.domain,
        ).iterator():
            extra = {}
            info = product.get_storage_info()
            extra['available'] = str(bool(info.get('quantity'))).lower()
            offer = self.create_block(offers, 'offer', id=product.id, **extra)
            if product.image:
                self.create_block(offer, 'picture', self.get_full_url(product.image.url))
            self.create_block(offer, 'url', self.get_full_url(product.get_absolute_url()))
            self.create_block(offer, 'price', int(info.get('price')))
            self.create_block(offer, 'currencyId', 'RUB')
            self.create_block(offer, 'categoryId', str(product.category.id))
            self.create_block(offer, 'name', product.title)
            if product.description:
                self.create_block(offer, 'description', f'<![CDATA["{product.description}"]]>')
            print('create', product)
