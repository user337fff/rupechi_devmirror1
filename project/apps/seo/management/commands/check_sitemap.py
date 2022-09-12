import requests
from apps.domains.models import Domain
from django.core.management import BaseCommand
from lxml import etree as ET


class Command(BaseCommand):
    ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'

    def handle(self, *args, **options):
        errors = []
        for domain in Domain.objects.all():
            url = f'http://{domain}/sitemap.xml/'
            response = requests.get(url, stream=True)
            response.raw.decode_content = True
            for event, item in ET.iterparse(response.raw, events=('start',), tag=f'{self.ns}loc'):
                link = item.text
                if link:
                    response = session.get(url=link)
                    print(link, 'status_code:', response.status_code)
                    if response.status_code != 200:
                        errors += [[link, response.status_code]]
        print('Ошибочные страницы: ', errors)
