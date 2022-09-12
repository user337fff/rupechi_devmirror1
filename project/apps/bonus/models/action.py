from django.db import models

from apps.shop.models import Order


class Action(models.Model):
    class Meta:
        verbose_name = 'Действие бонусного счета'
        verbose_name_plural = 'Действия бонусного счета'

    TYPE_CREATED = 'CREATED'
    TYPE_DEPOSITED = 'DEPOSITED'
    TYPE_WITHDRAWN = 'WITHDRAWN'
    TYPE_CHOICES = (
        (TYPE_CREATED, 'Создание аккаунта'),
        (TYPE_DEPOSITED, 'Начисление'),
        (TYPE_WITHDRAWN, 'Списание'),
    )
    account = models.ForeignKey(
        'bonus.BonusAccount', verbose_name='Аккаунт', related_name='account_actions',
        on_delete=models.CASCADE)
    order = models.ForeignKey(
        Order, verbose_name='Заказ', blank=True, null=True,
        on_delete=models.PROTECT)
    delta = models.IntegerField(verbose_name='Изменение баланса')
    type = models.CharField(
        verbose_name='Тип операции', max_length=15, choices=TYPE_CHOICES)
    expires_at = models.DateTimeField(
        verbose_name='Доступны до', blank=True, null=True)
    created_at = models.DateTimeField(
        verbose_name='Дата создания')
    comment = models.TextField(
        verbose_name='Комментарий', blank=True, default='')
    debug_balance = models.IntegerField(verbose_name='Остаток на балансе')

    def __str__(self):
        if self.delta > 0:
            return f'Начисление {self.delta} бонусов'
        elif self.delta < 0:
            return f'Списание {abs(self.delta)} бонусов'
        return f'Уведомление'

    @classmethod
    def create(
            cls,
            account,
            type,
            delta,
            asof,
            order=None,
            expires_at=None,
            comment=None):
        """Создание действия бонусного счета"""

        if comment is None:
            comment = ''

        return cls.objects.create(
            account=account,
            type=type,
            delta=delta,
            order=order,
            expires_at=expires_at,
            created_at=asof,
            comment=comment,
            debug_balance=account.balance,
        )
