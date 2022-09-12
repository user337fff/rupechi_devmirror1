from datetime import timedelta
from random import randint

from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.urls import reverse

from apps.shop.models import Order
from .sber import Client, TaxSystem as Tax, VatRate as Vat, OrderBundle

DEFAULT_LIFETIME = 1200  # in seconds


class SberSettings(models.Model):
    TEST = 'test'
    PROD = 'prod'

    MODES = (
        (TEST, 'Тестовый'),
        (PROD, 'Боевой')
    )

    TAX_SYSTEMS = (
        (Tax.COMMON, 'Общая'),
        (Tax.SIMPLIFIED_IN, 'Упрощённая, доход'),
        (Tax.SIMPLIFIED_IN_OUT, 'Упрощённая, доход - расход'),
        (Tax.UTOII, 'Единый налог на вменённый доход'),
        (Tax.UST, 'Единый сельскохозяйственный налог'),
        (Tax.PATENT, 'Патентная система налогообложения'),
    )

    VAT_RATES = (
        (Vat.RATE_NO, 'Без НДС'),
        (Vat.RATE_0, 'НДС по ставке 0%'),
        (Vat.RATE_10, 'НДС по ставке 10%'),
        (Vat.RATE_20, 'НДС по ставке 20%'),
        (Vat.RATE_110, 'НДС по расчетной ставке 10/110'),
        (Vat.RATE_120, 'НДС по расчётной ставке 20/120'),
    )

    mode = models.CharField(
        verbose_name='Режим', choices=MODES, default=TEST, max_length=7)
    session_lifetime = models.PositiveIntegerField(
        verbose_name='Время жизни заказа в секундах', default=DEFAULT_LIFETIME,
        validators=[MinValueValidator(300)])
    tax_system = models.PositiveIntegerField(
        verbose_name='Система налогообложения',
        choices=TAX_SYSTEMS,
        default=Tax.COMMON)
    vat_rate = models.PositiveIntegerField(
        verbose_name='Налоговая ставка',
        choices=VAT_RATES,
        default=Vat.RATE_NO)
    username = models.CharField(
        verbose_name='Имя пользователя', blank=True, null=True, max_length=63)
    password = models.CharField(
        verbose_name='Пароль', blank=True, null=True, max_length=63)
    token = models.CharField(
        verbose_name='Токен', blank=True, null=True, max_length=63)

    client = None

    def __str__(self):
        return 'Настройки эквайринга'

    def clean(self):
        if not ((self.username and self.password) or self.token):
            raise ValidationError("Введите пару имя-пароль, либо токен")

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(pk=self.pk).delete()
        super(SberSettings, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()

    class Meta:
        verbose_name = 'Настройки эквайринга'
        verbose_name_plural = 'Настройки эквайринга'


def calc_expiration_date(lifetime=DEFAULT_LIFETIME):
    return timezone.now() + timedelta(seconds=lifetime)


class BankOrder(models.Model):
    """
    Регистратор заказа в банке

    CONVERSION_RATIO - Коэффициент перевода в минимальные единицы валюты
    """
    class Meta:
        verbose_name = 'Заказ в банке'
        verbose_name_plural = 'Заказы в банке'

    CONVERSION_RATIO = 100

    order = models.OneToOneField(
        Order, verbose_name='Заказ', on_delete=models.SET_NULL, null=True, related_name="bank_data")
    success = models.BooleanField(
        verbose_name='Заказ создан успешно', default=False)

    bank_id = models.CharField(
        verbose_name='Ид заказа в системе банка', max_length=63, blank=True,
        default='')
    bank_url = models.CharField(
        verbose_name='Ссылка на оплату', max_length=255, blank=True,
        default='')
    card_number = models.IntegerField(verbose_name='Последние 4 цифры номера карты', max_length=4,
                                      blank=True, null=True)

    # dates
    expiration_date = models.DateTimeField(
        verbose_name='Окончание жизни заказа в банке',
        default=calc_expiration_date, editable=False)
    created_at = models.DateTimeField(
        verbose_name='Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField(
        verbose_name='Дата последнего обновления', auto_now=True)

    def __str__(self):
        if self.order:
            return str(self.order) + self.bank_id
        return self.bank_id

    @classmethod
    def to_min_currency(cls, value):
        """Перевод в минимальную единицу валюты"""
        return cls.CONVERSION_RATIO * value

    @classmethod
    def get_client(cls):
        settings = SberSettings.load()
        kwargs = {}
        if settings.mode == settings.TEST:
            kwargs['test'] = True
        else:
            kwargs['test'] = False

        if settings.username and settings.password:
            kwargs.update({
                'username': settings.username,
                'password': settings.password
            })
        elif settings.token:
            kwargs['token'] = token
        else:
            raise AttributeError("Имя пользователя и пароль не указаны")
        return Client(**kwargs)

    @classmethod
    def get_bundle(cls, order, tax):
        """
        Формирование товарной корзины заказа
        (Сбер требует передавать словарь с информацией о заказе и товарах)"""
        bundle = OrderBundle()
        for item in order.items.all():
            amount = cls.to_min_currency(item.price)
            bundle.add_item(
                item.product.title,
                item.id,
                amount,
                item.quantity,
                tax_type=tax)
        import json
        print(f'=====BUNDLE DATA {json.loads(bundle.to_data())}')
        return bundle.to_data()

    def get_card_number(self):
        client = self.get_client()
        status = client.get_order_status_extended(order_id=self.bank_id)
        card_number = status.data['cardAuthInfo']['pan'][-4:]
        return card_number

    @classmethod
    def get_random_number(cls):
        return randint(1, 10000)


    @classmethod
    def register_order(cls, order, domain):
        """Регистрируем заказа в системе сбербанка"""
        settings = SberSettings.load()
        client = cls.get_client()
        # формируем корзину товаров из заказа
        bundle = cls.get_bundle(order, settings.tax_system)

        amount = float(cls.to_min_currency(order.total))
        return_url = 'https://' + domain + reverse('sber:sber_payment')
        fail_url = 'https://' + domain + reverse('shop:unsuccessful_pay')
        resp = client.register(str(order.id),
                               amount,
                               return_url,
                               fail_url,
                               order.email,
                               bundle,
                               settings.tax_system,
                               sessionTimeoutSecs=settings.session_lifetime,
                               )
        if resp.data.get('errorCode') == '5':
            resp = client.register(str(order.id),
                                   amount,
                                   return_url,
                                   fail_url,
                                   bundle=bundle,
                                   tax_system=settings.tax_system,
                                   sessionTimeoutSecs=settings.session_lifetime,
                                   )
        if resp.data.get('errorCode') == '1':
            order_id = f'{order.id}-{cls.get_random_number()}'
            resp = client.register(order_id,
                                   amount,
                                   return_url,
                                   fail_url,
                                   bundle=bundle,
                                   tax_system=settings.tax_system,
                                   sessionTimeoutSecs=settings.session_lifetime,
                                   )
        if resp.success:
            cls.objects.update_or_create(
                order=order,
                defaults=dict(
                    success=True,
                    bank_id=resp.orderId,
                    bank_url=resp.formUrl,
                    expiration_date=calc_expiration_date(settings.session_lifetime)
                )
            )
            return resp
        return resp

    def payment_success(self):
        """Устанавливаем успешную оплату в заказе"""
        self.card_number = self.get_card_number()
        self.save(update_fields=['card_number'])
        self.order.pay()


class BankResponse(models.Model):
    """Ответ банка"""
    bank_order = models.OneToOneField(BankOrder, on_delete=models.PROTECT)
    response = JSONField(verbose_name='Ответ сервера')
