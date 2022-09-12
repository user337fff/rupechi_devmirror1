from django.db import models


class SeoBase(models.Model):
    meta_title = models.CharField(verbose_name="SEO заголовок", default='',
                                  blank=True, max_length=255)
    meta_description = models.TextField(verbose_name="Meta Description",
                                        default='', blank=True,
                                        help_text="""
                                        ||object|| - Заголовок объекта
                                        ||site|| - Название сайта
                                        ||city|| - Название города текущего поддомена
                                        ||city1|| - Название города текущего поддомена в предложном падеже
                                        ||price|| - Цена товара
                                        """)
    meta_keywords = models.TextField(verbose_name="Meta Keywords",
                                     default='', blank=True)

    class Meta:
        abstract = True
