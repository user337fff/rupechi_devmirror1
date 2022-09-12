from apps.catalog.models import *
from apps.domains.models import *

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    meta_title = '||cat_title|| - купить в ||name_loct|| по доступным ценам с доставкой'
    meta_desc = '||cat_title|| по доступной цене в компании «Жарко» ✅ Доставка и монтаж по ||name_dat|| и по всей России ⭐ ' \
                'Широкий выбор. Гарантия качества. Помощь консультантов. Заявка онлайн или по телефону ☎: 8 800 250-32-38'
    meta_desc_ivanovo = '||cat_title|| по доступной цене в компании «Жарко» ✅ Доставка и монтаж по городу Иваново и по ' \
                        'всей России ⭐ Широкий выбор. Гарантия качества. Помощь консультантов. Заявка онлайн ' \
                        'или по телефону ☎: 8 800 250-32-38'

    def replace_attrs(self, text:str, domain, category) -> str:
        return text\
               .replace('||cat_title||', category.title)\
               .replace('||name_loct||', domain.name_loct)\
               .replace('||name_dat||', domain.name_dat)

    def delete_old_meta(self):
        categories = Category.objects.all()
        for category in categories:
            SeoCategory.objects.filter(category=category).delete()

    def set_new_meta(self):
        categories = Category.objects.all()
        domains = Domain.objects.all()

        for domain in domains:
            for category in categories:
                meta_cat = SeoCategory.objects.filter(category=category, domain=domain).first()
                if not meta_cat:
                    meta_cat = SeoCategory(category=category, domain=domain)
                if domain.name == 'Иваново':
                    description = self.meta_desc_ivanovo
                else:
                    description = self.meta_desc
                meta_cat.meta_title = self.replace_attrs(self.meta_title, domain, category)
                meta_cat.meta_description = self.replace_attrs(description, domain, category)
                meta_cat.save()
                # SeoCategory(
                #     domain=domain,
                #     category=category,
                #     meta_title=self.replace_attrs(self.meta_title, domain, category),
                #     meta_description=self.replace_attrs(description, domain, category),
                #     meta_message = meta_cat.meta_message
                # ).save()
                # meta_cat.delete()

    @transaction.atomic
    def main(self):
        # self.delete_old_meta()
        self.set_new_meta()

    def handle(self, *args, **options):
        self.main()

