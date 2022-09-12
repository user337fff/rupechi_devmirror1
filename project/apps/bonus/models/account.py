from datetime import timedelta

from django.db import models, transaction
from django.db.models import Sum, F, DecimalField
from django.conf import settings
from django.utils import timezone

from apps.shop.models import Order

from .. import errors
from .action import Action
from .settings import BonusSettings
from .category import BonusCategory


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
        verbose_name='Дата создания')
    updated_at = models.DateTimeField(
        verbose_name='Дата последнего обновления')

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

    def deposit_first_order_bonuses(self, order):
        """Начисление бонусов за первый заказ"""
        bonus_settings = BonusSettings.load()

        prev_deposites_order = Action.objects.filter(
            type=Action.TYPE_DEPOSITED,
            account=self,
            order__isnull=False)

        if (bonus_settings.first_order_bonuses > 0 and
                not prev_deposites_order.exists()):
            asof = timezone.now()
            comment = 'Бонусы за первый заказ на сайте'
            self.deposit(self.pk,
                         bonus_settings.first_order_bonuses,
                         asof,
                         lifetime=bonus_settings.first_order_lifetime_bonuses,
                         comment=comment)

    def deposit_for_completed_order(self, order):
        """Начисление бонусов за заказ только в случае его выполнения"""
        # начислялись ли бонусы за заказ ранее
        action_exist = Action.objects.filter(
            order=order, type=Action.TYPE_DEPOSITED).exists()
        # проверяем статус заказа и предыдущие начисления
        if order.status == Order.COMPLETED and not action_exist:
            # бонусы за первый заказ
            self.deposit_first_order_bonuses(order)
            self.deposit_for_order(order)
            return True
        return False

    def deposit_for_order(self, order):
        """Начисление бонусов за заказ"""
        bonus_settings = BonusSettings.load()
        # расчет получаемых за заказ бонусов
        bonuses = BonusAccount.calc_bonuses_amount(order)
        # процент начисления в настройках сайта и количество бонусов > 0
        if (bonus_settings.order_deposit_percent > 0 and bonuses > 0):
            asof = timezone.now()
            comment = 'Бонусы за заказ на сайте'
            self.deposit(self.pk,
                         bonuses,
                         asof,
                         order=order,
                         lifetime=bonus_settings.lifetime_bonuses,
                         comment=comment)

    def withdraw_from_order(self, order):
        """Списание бонусов за заказ"""
        if order.user and order.bonuses_used > 0:
            self._withdraw_from_order(order)

    def _withdraw_from_order(self, order):
        """Списание бонусов за заказ"""
        comment = 'Бонусы за заказ на сайте'
        # максимальное количество бонусов к использованию
        print('keyword')
        max_use_bonuses = BonusAccount.calc_max_bonuses_use(order)
        print('max_use_bonuses', max_use_bonuses)
        if order.bonuses_used > max_use_bonuses:
            bonuses = max_use_bonuses
        else:
            bonuses = instance.bonuses_used
        self.withdraw(self.pk,
                      bonuses,
                      order.created_at,
                      order=order,
                      comment=comment)
        # скидка в бонусах
        upd = Order.objects.filter(pk=order.pk).update(
            total=order.total - bonuses, bonuses_used=bonuses)
        print(upd)
        print('///keyword')

    @classmethod
    def calc_bonuses_amount(cls, order=None, cart=None):
        """Сумма начисляемых за заказ бонусов"""
        bonus_settings = BonusSettings.load()
        bonuses = 0
        # процент начисления по умолчанию
        default_percent = bonus_settings.order_deposit_percent
        # вычисление суммы элемента заказы на стороне бд
        total = Sum(F('price') * F('quantity'), output_field=DecimalField())
        if cart:
            items = cart.positions.select_related(
                'product__category__bonus_category').all()
            for item in items:
                total = item.total
                try:
                    item_percent = item.product.category.bonus_category.deposit_percent
                except BonusCategory.DoesNotExist:
                    item_percent = None

                if item_percent is not None and item_percent > 0:
                    percent = item_percent
                elif default_percent > 0:
                    percent = default_percent
                else:
                    continue
                bonuses += round(total * default_percent/100)
        elif order:
            # список элеметов заказа
            # первый параметр сумма товарной позиции
            # второй - процент бонусов связанный с категорией товара
            # если к категории не привязан процент, то значение будет None
            items = order.items.annotate(total=total).values_list(
                'total',
                'product__category__bonus_category__deposit_percent')
            for item in items:
                total, item_percent = item
                if item_percent is not None and item_percent > 0:
                    percent = item_percent
                elif default_percent > 0:
                    percent = default_percent
                else:
                    continue
                bonuses += round(total * percent/100)
        return bonuses

    @classmethod
    def calc_max_bonuses_use(cls, order):
        """Максимальная сумма бонусов к списанию в заказе"""
        bonus_settings = BonusSettings.load()
        bonuses = 0
        # процент списания по умолчанию
        default_percent = bonus_settings.order_withdraw_percent
        # вычисление суммы элемента заказы на стороне бд
        total = Sum(F('price') * F('quantity'), output_field=DecimalField())
        # список элеметов заказа
        # первый параметр сумма товарной позиции
        # второй - процент бонусов связанный с категорией товара
        # если к категории не привязан процент, то значение будет None
        items = order.items.annotate(total=total).values_list(
            'total',
            'product__category__bonus_category__withdraw_percent')
        for item in items:
            total, item_percent = item
            if item_percent is not None:
                percent = item_percent
            else:
                percent = default_percent
            if percent > 0:
                bonuses += round(total * percent/100)
        return bonuses

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
                expires_at=None,
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
            if expires_at is None and lifetime and lifetime > 0:
                expires_at = asof + timedelta(days=lifetime)

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
