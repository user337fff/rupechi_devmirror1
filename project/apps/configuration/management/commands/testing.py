from datetime import datetime
from email.mime import image
import traceback
from django.core.management.base import BaseCommand
from lxml import etree as et
import requests
from bs4 import BeautifulSoup

class Command(BaseCommand):

    SHOW_PRODUCTS = True

    def decorator_time(func):
        def wrapper(*args, **kwargs):
            print("Начало выгрузки", datetime.now().strftime("%c"))
            func(*args, **kwargs)
            print("Конец выгрузки", datetime.now().strftime("%c"))
        return wrapper

    BASE_URL = "https://www.devmirror1.srv-rupechi-test1.place-start.ru/"

    @decorator_time
    def handle(self, *args, **options):
        response = requests.get(self.BASE_URL + "sitemap.xml")
        root = et.fromstring(response.text.encode("utf-8"))
        urls = root.iter()

        title_list, title_description = ({}, {})

        robots_urls = {'admin', 'ajax_lookup', 'admin_tools', 'checkout', 'ajaximage', 'ckeditor', 'comparsion',
                        'favorites', 'lk', 'changepassword', 'orders', 'neworder', 'user', 'search', 'order',
                        'sbros-parolya', 'compare', 'wishlist', 'cart', 'users', 'sitemap_img.xml', 'admin'}

        for url in urls:
            if(url.tag == "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
                print("-------------------------")
                _url = str(url.text).replace("www.rupechi.ru", "www.devmirror1.srv-rupechi-test1.place-start.ru")
                print(_url)

                if(not self.SHOW_PRODUCTS and "product" in _url.split("/")):
                    print("Страница не парсится")
                    continue

                if set(_url.split('/')) & robots_urls:
                    print("Страница не индексируется")
                    continue

                _response = requests.get(_url)

                try:
                    self.testing_xml(_response)
                except:
                    traceback.print_exc()

                try:
                    self.testing_spam_friendly_url(_response)
                except:
                    traceback.print_exc()

                try:
                    self.testing_unique_header(_response)
                except:
                    traceback.print_exc()

                try:
                    _, title_list, title_description = self.testing_unique_title_description(_response, title_list, title_description)
                except:
                    traceback.print_exc()

                try:
                    self.testing_alt_img(_response)
                except:
                    traceback.print_exc()

                try:
                    self.testing_selection_tags(_response)
                except:
                    traceback.print_exc()
    

    @classmethod
    def testing_xml(cls, _response) -> bool:
        """
        Ссылка: sitemap.xml
        Проверка:
            Карта сайта XML соответствует стандартам: отклик каждого из элементов равен 200
        return value: True
        """

        if(_response.status_code != 200):
            raise Exception("Страница отдаёт отклик не 200: " + _response.url + ", а " + str(_response.status_code))

        return True

    @classmethod
    def testing_unique_header(cls, _response) -> bool:
        """
        Проверка:
            Заголовок h1 корректен на каждой странице и размещен в одном формате
        return value: True
        """

        htmlParser = BeautifulSoup(_response.text, 'html.parser')
        countElements = len(htmlParser.select("h1"))
        if(countElements != 1):
            raise Exception(F"Число элементов h1 на странице не равно 1: " + _response.url)

        print(htmlParser.select("h1")[0])

        return True

    @classmethod
    def testing_unique_title_description(cls, _response, title_dict, description_dict) -> bool:
        """
        Проверка:
            Title и description уникальны для всех страниц сайта
        return value: True, List<Title>, List<Description>
        """

        htmlParser = BeautifulSoup(_response.text, 'html.parser')
        page_title = str(htmlParser.select_one("title"))
        page_description = str(htmlParser.select_one("meta[name='description']"))

        if(page_title in title_dict and title_dict[page_title] != _response.url):
            raise Exception("Заголовок страницы " + page_title + " уже существует:" + _response.url + ". Урл страницы с одинаковым заголовком: " + title_dict[page_title])
        else:
            title_dict.update({page_title: _response.url})
        
        if(page_description in description_dict and description_dict[page_description] != _response.url):
            raise Exception("Описание страницы " + page_description + " уже существует: " + _response.url + ". Урл страницы с одинаковым описанием: " + description_dict[page_description])
        else:
            description_dict.update({page_description: _response.url})

        return True, title_dict, description_dict

    @classmethod
    def testing_alt_img(cls, _response) -> bool:
        """
        Проверка:
            Наличие alt-тегов у изображений с ключевыми словами
        return value: True
        """

        htmlParser = BeautifulSoup(_response.text, 'html.parser')
        img_list = htmlParser.select("img")

        errors_list = []

        for img in img_list:
            #Отсеиватель Яндекс метрики и других изображений, для которых alt не требуется
            imgSrc = img.get("src")

            usingImg = True

            for key in ["yandex", "vk.com/rtrg", "googleusercontent"]:
                if(key in imgSrc):
                    usingImg = False
                    continue

            if usingImg and not img.get("alt", ""):
                errors_list.append(str(img))
                

        if(errors_list):
            raise Exception("У изображений " + ", ".join(errors_list) + " отсутствует alt на странице: " + _response.url)

        return True

    @classmethod
    def testing_selection_tags(cls, _response) -> bool:
        """
        Проверка:
            Отсутствие тегов выделения <b>, <u>, <i>, <em> и <strong>
        return value: True
        """

        htmlParser = BeautifulSoup(_response.text, 'html.parser')

        for tag in ["b", "u", "i", "em", "strong"]:
            if(len(htmlParser.select(tag)) != 0):
                raise Exception(F"Число элементов {tag} не равны 0: " + _response.url)

        return True

    @classmethod
    def testing_spam_friendly_url(cls, _response) -> bool:
        """
        Проверка:
            Нет спама в звеньях ЧПУ. Не должно быть ЧПУ следующего вида site.ru/razdel/razdel-podrazdel/
        return value: True
        """

        url = _response.url

        if("https:" in url):
            url = url[8:]
        elif("http:" in url):
            url = url[7:]

        splitting_url = url.split("/")
        formatted_splitting_url = []
        for index in range(len(splitting_url)):
            if(splitting_url[index] == ''):
                continue
            else:
                formatted_splitting_url.append(splitting_url[index])

        formatted_splitting_url = formatted_splitting_url[1:]

        for index in range(len(formatted_splitting_url)):
            url = formatted_splitting_url[index]
            for _url in formatted_splitting_url[:index:]:
                if(url in _url or _url in url):
                    raise Exception("У страницы скорее всего присуствует спам в звеньях ЧПУ: " + _response.url)

        return True        