from django.db import models

from apps.catalog.models import Product


class Option(models.Model):
    """ Опции для товаров """
    title = models.CharField(verbose_name='Заголовок',
                             max_length=63, db_index=True, unique=True)

    created_at = models.DateTimeField(
        verbose_name='Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField(
        verbose_name='Дата последнего обновления', auto_now=True)

    position = models.PositiveIntegerField(verbose_name='Позиция', default=0)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Опция'
        verbose_name_plural = 'Опции'
        ordering = ('position',)


class OptionValue(models.Model):
    """ Значения опций """
    option = models.ForeignKey(
        Option, related_name='option_values', on_delete=models.CASCADE)
    value = models.CharField(verbose_name='Значение',
                             max_length=63, db_index=True)
    position = models.PositiveIntegerField(verbose_name='Позиция', default=0)

    def __str__(self):
        return self.value

    class Meta:
        verbose_name = 'Значение опции'
        verbose_name_plural = 'Значения Опций'
        ordering = ('position',)


class ProductOption(models.Model):
    """ Количественные параметры опции конкретного товара  """
    product = models.ForeignKey(
        Product, related_name='product_options', on_delete=models.CASCADE)
    value = models.OneToOneField(
        OptionValue, related_name='value_product_options',
        verbose_name='Значение', on_delete=models.CASCADE)
    price = models.DecimalField(
        verbose_name='Цена', max_digits=10, decimal_places=2, default=0)
    old_price = models.DecimalField(
        verbose_name='Старая цена', max_digits=10, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(
        verbose_name='Остаток на складе', default=0)
    # dates
    created_at = models.DateTimeField(
        verbose_name='Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField(
        verbose_name='Дата последнего обновления', auto_now=True)

    def __str__(self):
        return f'{self.value} {self.price} {self.stock}'

    class Meta:
        verbose_name = 'Опция товара'
        verbose_name_plural = 'Опции товаров'
