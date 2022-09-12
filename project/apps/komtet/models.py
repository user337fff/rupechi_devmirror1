from requests.exceptions import HTTPError
from komtet_kassa_sdk import (
    Check, CorrectionCheck, Client, Intent, TaxSystem, VatRate, CorrectionType,
    PaymentMethod, Agent, AgentType, CalculationSubject, CalculationMethod
)
from django.db import models
from django.contrib.postgres.fields import JSONField

from apps.shop.models import Order


class KomtetSettings(models.Model):
    TAX_SYSTEMS = (
        (TaxSystem.COMMON, 'Общая'),
        (TaxSystem.SIMPLIFIED_IN, 'Упрощённая, доход'),
        (TaxSystem.SIMPLIFIED_IN_OUT, 'Упрощённая, доход - расход'),
        (TaxSystem.UTOII, 'Единый налог на вменённый доход'),
        (TaxSystem.UST, 'Единый сельскохозяйственный налог'),
        (TaxSystem.PATENT, 'Патентная система налогообложения'),
    )

    VAT_RATES = (
        (VatRate.RATE_NO, 'Без НДС'),
        (VatRate.RATE_0, 'НДС по ставке 0%'),
        (VatRate.RATE_10, 'НДС по ставке 10%'),
        (VatRate.RATE_20, 'НДС по ставке 20%'),
        (VatRate.RATE_110, 'НДС по расчетной ставке 10/110'),
        (VatRate.RATE_120, 'НДС по расчётной ставке 20/120'),
    )

    shop_id = models.CharField(
        verbose_name='Идентификатор магазина', max_length=31)
    secret_key = models.CharField(verbose_name='Секретный ключ', max_length=31)
    queue_id = models.CharField(
        verbose_name='Идентификатор очереди', max_length=31)
    cashier = models.CharField(
        verbose_name='ФИО кассира', max_length=31, blank=True, null=True)
    cashier_inn = models.CharField(
        verbose_name='ИНН кассира', max_length=31, blank=True, null=True)

    tax_system = models.PositiveIntegerField(
        verbose_name='Система налогообложения',
        choices=TAX_SYSTEMS,
        default=TaxSystem.COMMON)
    vat_rate = models.CharField(
        verbose_name='Налоговая ставка',
        choices=VAT_RATES,
        default=VatRate.RATE_NO,
        max_length=7)

    print_check = models.BooleanField(
        verbose_name='Печатать чек', default=True)

    # способ расчет
    calc_method = CalculationMethod.FULL_PAYMENT
    # предмет продажи
    calc_subject = CalculationSubject.PRODUCT

    def __str__(self):
        return 'Настройки комтет-кассы'

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        super(KomtetSettings, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()

    class Meta:
        verbose_name = 'Настройки комтет-кассы'
        verbose_name_plural = 'Настройки комтет-кассы'


class KomtetRequest(models.Model):
    """Запрос к кассе для передачи данных чека"""
    NOT_PROCESSED = 0
    SUCCESS = 1
    ERROR = 2
    STATUSES = (
        (NOT_PROCESSED, "Не обработан"),
        (SUCCESS, "Успешно"),
        (ERROR, "Ошибка")
    )
    order = models.OneToOneField(
        Order, verbose_name="Заказ", related_name='komtet',
        on_delete=models.CASCADE)
    task_id = models.CharField(
        verbose_name='Ид задачи', max_length=63, blank=True, default='')
    response = JSONField(verbose_name='Ответ кассы', blank=True)
    status = models.PositiveIntegerField(
        verbose_name="Статус", choices=STATUSES, default=0)

    client = None
    settings = None

    def __init__(self):
        self.set_settings()
        self.set_client()

    def set_settings(self):
        if self.settings is None:
            self.settings = KomtetSettings.load()
        return self.settings

    @classmethod
    def register_order(cls, order):
        """Регистрируем операцию в системе комтета"""
        return cls.objects.create(order=order).send_request()

    def send_request(self):
        """Отправка запроса в комтет кассу"""
        self.generate_check()
        self.create_task()

    def set_client(self):
        """Создание клиента-апи для кассы"""
        self.client = Client(self.settings.shop_id, self.settings.secret_key)
        self.client.set_default_queue(self.settings.queue_id)

    def generate_check(self, intent=Intent.SELL):
        """Создание чека"""
        self.check = Check(self.order.id, self.order.email, intent,
                           self.settings.tax_system)
        # устанавливаем информацию о кассире, если заполнена
        if self.settings.cashier and self.settings.cashier_inn:
            self.check.set_cashier(self.settings.cashier,
                                   self.settings.cashier_inn)
        if self.settings.print_check:
            # печать чека в кассе
            self.check.set_print(True)
        for item in self.order.get_items(True).iterator():
            self.check.add_position(
                item.product.title,
                oid=item.product.id,
                price=item.price,
                quantity=item.quantity,
                total=item.total,
                vat=self.settings.vat_rate,
                calculation_method=self.settings.calc_method,
                calculation_subject=self.settings.calc_subject,
            )
        self.check.add_payment(self.order.total)

    def generate_check_fake(self):
        """
        Создание словаря, повторяющего параметры настоящего чека
        Требуется только для отладки
        """
        check = {}
        check['info'] = {"id": self.order.id,
                         "email": self.order.email,
                         "intent": Intent.SELL,
                         "tax_system": self.settings.tax_system}
        check['items'] = []
        for item in self.order.get_items(True).iterator():
            check['items'].append(
                {"title": item.product.title,
                 "oid": item.product.id,
                 "price": item.total,
                 "quantity": item.count,
                 "total": item.total,
                 "vat": self.settings.vat_rate,
                 "calculation_method": self.settings.calc_method,
                 "calculation_subject": self.settings.calc_subject,
                 })
        return check

    def create_task(self):
        """Создание операции платежа в комтет кассе"""
        try:
            task = self.client.create_task(self.check)
        except HTTPError as exc:
            print(exc.response.text)
        else:
            self.task_id = str(task.id)
            self.save(update_fields=['task_id'])
            print(task)

    def get_task_info(self):
        """Получение информации о операции"""
        try:
            task_info = self.client.get_task_info(self.task_id)
        except HTTPError as exc:
            print(exc.response.text)
        else:
            print(task_info)

    class Meta:
        verbose_name = "Запрос к кассе"
        verbose_name_plural = "Запрос к кассе"
