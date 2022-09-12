from django.db import models

from apps.catalog.models import Category


class BonusCategory(models.Model):
    class Meta:
        verbose_name = 'Бонус категории'
        verbose_name_plural = 'Бонусы по категориям'

    category = models.OneToOneField(
        Category, on_delete=models.CASCADE, related_name='bonus_category')
    deposit_percent = models.PositiveIntegerField(
        verbose_name='Бонусов за заказ в %',
        blank=True,
        null=True,
        help_text='Процент бонусов начисляемый за товар данной категории')
    withdraw_percent = models.PositiveIntegerField(
        verbose_name='Максимальное списание бонусов от заказа в %',
        blank=True,
        null=True,
        help_text='Процент бонусов списываемый за товар данной категории')

    def __str__(self):
        return f'{self.category.title}'
