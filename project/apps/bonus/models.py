from datetime import timedelta

from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from apps.shop.models import Order

from . import errors


class BonusSettings(models.Model):
    class Meta:
        verbose_name = 'Настройки бонусной системы'
        verbose_name_plural = 'Настройки бонусной системы'

    order_deposit_percent = models.PositiveIntegerField(
        verbose_name='Бонусов за заказ в %', default=0)
    order_withdrow_percent = models.PositiveIntegerField(
        verbose_name='Максимальное списание бонусов от заказа в %', default=0)
    lifetime_bonuses = models.PositiveIntegerField(
        verbose_name='Дней до сгорания бонусов', default=0,
        help_text='Если бонусы бессрочные, то оставить равным нулю')

    register_bonuses = models.PositiveIntegerField(
        verbose_name='Бонусов за регистрацию', default=0)
    register_lifetime_bonuses = models.PositiveIntegerField(
        verbose_name='Дней до сгорания регистрационных бонусов', default=0,
        help_text='Если бонусы бессрочные, то оставить равным нулю')

    first_order_bonuses = models.PositiveIntegerField(
        verbose_name='Бонусов за первый заказ', default=0)
    first_order_lifetime_bonuses = models.PositiveIntegerField(
        verbose_name='Дней до сгорания бонусов за первый заказ', default=0,
        help_text='Если бонусы бессрочные, то оставить равным нулю')

    def __str__(self):
        return 'Настройки бонусной системы'

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        super(BonusSettings, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()


class BonusAccount(models.Model):
    class Meta:
        verbose_name = 'Бонусный счет'
        verbose_name_plural = 'Бонусные счета'
        ordering = ('-created_at',)

    MIN_BALANCE = 0
    MAX_BALANCE = 99999

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name='Пользователь',
        related_name='bonus_account', on_delete=models.CASCADE)
    balance = models.PositiveIntegerField(verbose_name='Баланс', default=0)

    # dates
    created_at = models.DateTimeField(
        verbose_name='Дата создания', default=timezone.now)
    updated_at = models.DateTimeField(
        verbose_name='Дата последнего обновления', default=timezone.now)

    def __str__(self):
        return f'Бонусный счет: {self.user}'

    def deposit_register_bonuses(self):
        """Начисление бонусов за регистрацию"""
        bonus_settings = BonusSettings.load()
        if bonus_settings.register_bonuses > 0:
            asof = timezone.now()
            comment = 'Бонусы за регистрацию на сайте'
            self.deposit(self.pk,
                         bonus_settings.register_bonuses,
                         asof,
                         lifetime=bonus_settings.register_lifetime_bonuses,
                         comment=comment)

    @classmethod
    def create(cls, user, asof):
        """Создание бонусного счета.

        user (User):
            Владелец бонусного счета.
        asof (datatime):
            Время создания.
        """
        with transaction.atomic():
            account = cls.objects.create(
                user=user,
                created_at=asof,
                updated_at=asof)

            action = Action.create(
                account=account,
                type=Action.TYPE_CREATED,
                delta=0,
                asof=asof,
            )

        return account, action

    @classmethod
    def deposit(cls,
                pk,
                amount,
                asof,
                order=None,
                lifetime=None,
                comment=None):
        """Начисление бонусов.

        pk (positive int):
            Ид счета
        amount (positive int):
            Сумма к начислению.
        asof (datetime.datetime):
            Время начисления.
        order (Order):
        Optional инстанс заказа.
        comment (str or None):
        Optional комментарий.

        Returns (tuple):
            [0] (BonusAccount) Бонусный счет.
            [1] (Action) Действие начисления.
        """

        with transaction.atomic():
            account = cls.objects.select_for_update().get(pk=pk)

            # if account.balance + amount > cls.MAX_BALANCE:
            #     raise errors.ExceedsLimit()

            account.balance += amount
            account.updated_at = asof

            account.save(update_fields=[
                'balance',
                'updated_at',
            ])

            # устанавливаем дату когда бонусы сгорят
            if lifetime and lifetime > 0:
                expires_at = asof + timedelta(days=lifetime)
            else:
                expires_at = None

            action = Action.create(
                account=account,
                type=Action.TYPE_DEPOSITED,
                delta=amount,
                asof=asof,
                order=order,
                expires_at=expires_at,
            )

        return account, action

    @classmethod
    def withdraw(cls, pk, amount, asof, order=None, comment=None):
        """Списание со счета.

        pk (positive int):
            Ид счета.
        amount (positive int):
            Сумма списания.
        asof (datetime.datetime):
            Время списания.
        order (Order):
            Optional инстанс заказа.
        lifetime (positive int)
            Optional время жизни бонусов в днях
        comment (str or None):
            Optional комментарий.


        Returns (tuple):
            [0] (BonusAccount) Бонусный счет.
            [1] (Action) Действие начисления.
        """

        with transaction.atomic():
            account = cls.objects.select_for_update().get(pk=pk)

            if account.balance - amount < cls.MIN_BALANCE:
                raise InsufficientFunds(amount, account.balance)

            account.balance -= amount
            account.updated_at = asof

            account.save(update_fields=[
                'balance',
                'updated_at',
            ])

            action = Action.create(
                account=account,
                type=Action.TYPE_WITHDRAWN,
                delta=-amount,
                asof=asof,
                order=order
            )

        return account, action


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
        BonusAccount, related_name='account_actions', on_delete=models.CASCADE)
    order = models.ForeignKey(
        Order, verbose_name='Заказ', blank=True, null=True,
        on_delete=models.PROTECT)
    delta = models.IntegerField(verbose_name='Изменение баланса')
    type = models.CharField(
        'Тип операции', max_length=15, choices=TYPE_CHOICES)
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
