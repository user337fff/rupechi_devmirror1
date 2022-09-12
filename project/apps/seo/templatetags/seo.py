from apps.configuration.models import Settings
from apps.domains.middleware import get_request
from django import template
from django.apps import apps
from django.utils.safestring import mark_safe
from apps.catalog.templatetags.catalog import convert_price

register = template.Library()

class Seo:
    def __init__(self, context=None):
        self.context = context or {}
        # Часто юзается, следуюет бы закэшировать
        self.settings = Settings.get_settings()
        page = self.context.get('page')
        obj = self.context.get('object')
        self.domain = get_request().domain
        self.domain_attrs = {}
        self.current = obj or page
        self.main = page or obj
        q = self.context.get('q') or ''
        if hasattr(self.current, 'seo'):
            self.current = self.current.seo.filter(domain=self.domain).first() or self.main
        self.replacing = []
        if self.current:
            self.replacing += [
                ('||object||', self.current.__str__()),
            ]
        if self.settings:
            self.replacing += [
                ('||site||', self.settings.name),
            ]
        if self.domain:
            self.replacing += [
                ('||city||', self.domain.name),
                ('||city1||', self.domain.name_loct),
            ]
        self.replacing += [
            ('||q||', q),
        ]
        if hasattr(self.current, 'get_storage_info'):
            product_info = self.current.get_storage_info()
            self.replacing += [
                ('||price||', convert_price(product_info.get('price'))),
            ]

    def clean(self, string: str) -> str:
        """Замена переменных"""
        for key, value in self.replacing:
            if key and value:
                string = str(string).replace(key, value)
        return string

    def check_null_seo(self):
        name = self.current.__class__.__name__.lower()
        if name in ['catalog', 'category', 'alias', 'seocategory']:
            return self.domain.seo_description_category
        elif name in ['product']:
            return self.domain.seo_description_product
        return ''

    def replace_alter_seo(self, text:str, price='', product=False):
        if product:
            title = self.current.title
        else:
            title = self.current.category.title
        text = text\
               .replace('||title||', title)\
               .replace('||domain_loct||', self.domain.name_loct)\
               .replace('||domain_dat||', self.domain.name_dat)\
               .replace('||price||', str(price))
        return text

    def get_alter_seo(self, alter_seo, price='', product=False):
        if product:
            return self.replace_alter_seo(alter_seo.alter_seo_title_product, price=price, product=product), \
                   self.replace_alter_seo(alter_seo.alter_seo_desc_product, price=price, product=product)
        else:
            return self.replace_alter_seo(alter_seo.alter_seo_title_category, price=price), \
                   self.replace_alter_seo(alter_seo.alter_seo_desc_category, price=price)

    def get_tag(self) -> dict:
        try:
            Product = apps.get_model('catalog', 'Product')
            AlterSeoCategory = apps.get_model('catalog', 'AlterSeoCategory')
            SeoCategory = apps.get_model('catalog', 'SeoCategory')
            request = get_request()
            alter_seo = AlterSeoCategory.objects.all().first()

            """Получение информации страницы
            :return: dict [title, meta_title, meta_description]"""
            response = {}
            if self.current:
                response['title'] = self.main.__str__()
                response['full_title'] = self.context.get('title_prefix', '') + self.clean(
                    getattr(self.main, 'full_title', '') or response['title'])
                response['breadcrumbs'] = getattr(self.main, 'get_breadcrumbs', [])(callback=self.clean)

            if (isinstance(self.current, SeoCategory) or isinstance(self.current, Product)) \
               and (set(self.current.category.get_ancestors(include_self=True)) & set(alter_seo.category.all())) \
               and (not set(self.current.category.get_ancestors(include_self=True)) & set(alter_seo.category_exclude.all())):
                if isinstance(self.current, Product):
                    price = self.current.get_storage_info().get('discount_price') \
                            or self.current.get_storage_info().get('price')
                    price = round(price)
                    product = True
                else:
                    price = None
                    product = False
                response['meta_title'], response['meta_description'] = self.get_alter_seo(alter_seo,
                                                                                          price=price, product=product)
            else:
                if isinstance(self.current, Product):
                    title = self.current.title
                    price = self.current.get_storage_info().get('discount_price') \
                            or self.current.get_storage_info().get('price')
                    price = round(price)
                    response['meta_title'] = f'Купить {title} в {self.domain.name_loct} по цене {price}'
                    response['meta_description'] = f'{title} купить по доступной цене в компании «Жарко» ✅ Доставка ' \
                                                   f'и монтаж по всей России ⭐ Подробные характеристики, гарантии, ' \
                                                   f'7 дней на возврат. Помощь консультантов. Заявка онлайн или ' \
                                                   f'по телефону ☎: 8 800 250-32-38'
                else:
                    response['meta_title'] = mark_safe(self.clean(
                        getattr(self.current, 'meta_title', '') or self.domain.meta_title or self.settings.meta_title))
                    response['meta_description'] = self.current.meta_description or self.domain.meta_description
                    response['meta_description'] = self.clean(getattr(self.main, 'meta_description', '')
                                                              or response['meta_description'])
                if request.GET.get('page'):
                    if int(request.GET.get('page')) > 1:
                        response['meta_title'] = f"{response['title']} - страница {request.GET.get('page')} 🔥 " \
                                                 f"Купить в {self.domain.name_loct} по выгодной цене"
                        response['meta_description'] = f"{response['title']}, страница {request.GET.get('page')}. " \
                                                       f"Наличие на складе! Гарантия до 5 лет от производителя! " \
                                                       f"Консультация специалиста. Возможна оплата картой. " \
                                                       f"Монтаж под ключ. Доставка по всей России"
                        response['title'] = f"{response['title']}, страница {request.GET.get('page')}"
                        # response['page_number'] = int(request.GET.get('page'))
                # else:
            #         response['page_number'] = 0
            # print(f'=========PAGE NUMBER {response["page_number"]}')
            noindex = False
            urls = set(get_request().environ['REQUEST_URI'].split('/'))
            robots_urls = {'admin', 'ajax_lookup', 'admin_tools', 'checkout', 'ajaximage', 'ckeditor', 'comparsion',
                           'favorites', 'lk', 'changepassword', 'orders', 'neworder', 'user', 'search', 'order',
                           'sbros-parolya', 'compare', 'wishlist', 'cart', 'users', 'sitemap_img.xml', 'admin'}
            if urls & robots_urls:
                noindex = True
            response['noindex'] = noindex
            response['meta_message'] = self.clean(getattr(self.current, 'meta_message', ''))
            print(f'====META MESSAGE {response["meta_message"]}')
        except Exception as ex:
            print(f'=====META EXCEPTION {ex}')
            return
        return response


@register.simple_tag(takes_context=True)
def get_page_info(context):
    """Получает информацию о странице"""
    return Seo(context).get_tag()
