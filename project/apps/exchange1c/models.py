from django.db import models
from django.utils import timezone
from apps.shop.models import Order


NOT_DELIVERY = 'not'
PICKUP = 'pickup'
COURIER = 'corier'

DELIVERY_FOR_NEW_CHOICES = (
    (NOT_DELIVERY, 'Без доставки'),
    (PICKUP, 'Самовывоз'),
    (COURIER, 'Курьер')
)

NOT_GROUPING = 'not'
CODE = 'code'
CATEGORY = 'cat'
ID_1C = 'id1c'
# ????
GROUP_VARIATIVE_CHOICES = (
    (NOT_GROUPING, '-'),
    (CODE, 'По артикулу'),
    (CATEGORY, 'По категории'),
    (ID_1C, 'По ид 1с')
)


class Settings(models.Model):

    orders_from_1c = models.BooleanField(
        verbose_name='Создавать новые заказы и контрагенты из 1с',
        default=False)

    order_prefix = models.CharField(
        verbose_name='Префикс номера заказа при выгрузке',
        max_length=31,
        blank=True,
        default='')

    only_paid_orders = models.BooleanField(
        verbose_name='Выгружать только оплаченные заказ',
        default=False)
    # ???????????
    only_allowed_delivery_orders = models.BooleanField(
        verbose_name='Выгружать только заказы c разрешенной доставкой',
        default=False)

    change_statuses_from_1c = models.BooleanField(
        verbose_name='Менять статусы заказов по информации из 1С',
        default=False)

    orders_status_gte = models.CharField(
        verbose_name='Выгружать заказы начиная со статуса',
        max_length=15,
        default=Order.CREATED,
        choices=Order.STATUS_CHOICES)
    # ???????
    delivery_for_new = models.CharField(
        verbose_name='Служба доставки для новых отгрузок',
        max_length=15,
        default=NOT_DELIVERY,
        choices=DELIVERY_FOR_NEW_CHOICES)

    # физические лица
    full_name = models.BooleanField(
        verbose_name='Полное наименование', default=True)
    name = models.BooleanField(verbose_name='Имя', default=True)
    last_name = models.BooleanField(verbose_name='Фамилия', default=True)
    address = models.BooleanField(verbose_name='Адрес', default=True)
    postcode = models.BooleanField(
        verbose_name='Почтовый индекс', default=True)
    city = models.BooleanField(verbose_name='Город', default=True)
    street = models.BooleanField(verbose_name='Улица', default=True)
    email = models.BooleanField(verbose_name='Email', default=True)

    # юридические лица
    full_name_ur = models.BooleanField(
        verbose_name='Полное наименование', default=True)
    inn_ur = models.BooleanField(verbose_name='ИНН', default=True)
    kpp_ur = models.BooleanField(verbose_name='КПП', default=True)
    address_ur = models.BooleanField(verbose_name='Адрес', default=True)
    country_ur = models.BooleanField(verbose_name='Страна', default=True)
    city_ur = models.BooleanField(verbose_name='Город', default=True)
    street_ur = models.BooleanField(verbose_name='Улица', default=True)
    phone_ur = models.BooleanField(
        verbose_name='Контактный телефон', default=True)
    email_ur = models.BooleanField(verbose_name='Email', default=True)

    know_price_instead_add_cart_button = models.BooleanField(
        verbose_name='Менять кнопку добавления в корзину на "Узнать цену"',
        default=False,
        help_text='Если товар есть в наличии, но цена указана 0, то заменить кнопку "Добавить в корзину" на кнопку "Узнать цену"')
    notify_instead_add_cart_button = models.BooleanField(
        verbose_name='Менять кнопку добавления в корзину на "Уведомить о поступлении"',
        default=False,
        help_text='Если товара нет в наличии, то заменяем кнопку "Добавить в корзину" на кнопку "Уведомить о поступлении"')
    hide_not_in_stock = models.BooleanField(
        verbose_name='Скрывать в катлоге товар без наличия и цены',
        default=False)

    variation_grouping = models.CharField(
        verbose_name='Группировать вариативные товары по',
        max_length=15,
        default=NOT_GROUPING,
        choices=GROUP_VARIATIVE_CHOICES)

    last_export_date = models.DateTimeField(
        verbose_name="Дата последнего экспорта заказов", blank=True, null=True)

    def __str__(self):
        return 'Настройки обмена с 1с'

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    class Meta:
        verbose_name = 'Настройки обмена'
        verbose_name_plural = 'Настройки обмена'
