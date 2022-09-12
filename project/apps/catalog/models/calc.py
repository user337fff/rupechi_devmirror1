from django.db import models

from apps.domains.middleware import get_request


def get_contractor(request=None):
    if request is None:
        request = get_request()
    contractor = getattr(request.user, 'contractor', '') or ''
    if contractor:
        contractor = f'_{contractor}'
    return contractor


class Calc(models.Model):
    WALL = 'wall'
    ROOF = 'roof'
    PIPE_CHOICE = (
        (WALL, 'Через стену'),
        (ROOF, 'Через крышу'),
    )
    MIN_HEIGHT = 4
    MAX_HEIGHT = 20
    title = models.CharField('Название', default="", max_length=125, blank=True)
    diameter = models.FloatField('Диаметр', default=0, blank=True)
    pipe = models.CharField('Выход стены', default=WALL, choices=PIPE_CHOICE, max_length=5)
    brand = models.ForeignKey('catalog.Brand', blank=True, null=True, on_delete=models.SET_NULL,
                              verbose_name="Производитель")
    insulation = models.BooleanField('Утплитель', default=False)
    life_tile = models.PositiveSmallIntegerField('Срок службы', default=0)
    sort = models.PositiveSmallIntegerField('Сортировка', default=0)

    class Meta:
        ordering = ['sort']
        verbose_name = 'Вариант вывода комплектующих'
        verbose_name_plural = 'Варианты вывода комплектующих'

    def __str__(self):
        return self.title or f'{self.brand} {self.diameter}'

    def calc(self, height):
        diff_height = height - self.MIN_HEIGHT
        if diff_height < 0:
            diff_height = 0
        total = 0
        items = self.items.select_related('product')
        for item in items:
            info = item.product.get_storage_info()
            item.quantity = item.coefficient * diff_height + item.quantity
            item.discount_price = info.get('old_price') or info.get('discount_price')
            item.old_price = info.get('old_price')
            item.price = info.get('price')
        return items, total


class CalcItem(models.Model):
    line = models.ForeignKey('catalog.Calc', verbose_name="Вариант комплектующих", on_delete=models.CASCADE,
                             related_name='items')
    product = models.ForeignKey('catalog.Product', verbose_name="Продукт", on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField('Количество', default=1)
    coefficient = models.PositiveSmallIntegerField('Коэффициент', default=0)
    sort = models.PositiveSmallIntegerField('Сортировка', default=0)

    class Meta:
        ordering = ['sort']
        verbose_name = 'Товар подборки'
        verbose_name_plural = 'Товары подборки'

    def __str__(self):
        return self.product.__str__()
