from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.shop.models import Order
from .api import Client, TypePickup, TypeDelivery


class Settings(models.Model):
    class Meta:
        verbose_name = 'Настройки'
        verbose_name_plural = 'Настройки'

    TEST = 'test'
    PROD = 'prod'

    MODES = (
        (TEST, 'Тестовый'),
        (PROD, 'Боевой')
    )

    PICKUP_CHOICES = (
        (TypePickup.FROM_DOOR, 'Забор груза от двери'),
        (TypePickup.FROM_POINT, 'Самостоятельная доставка до ПВ')
    )

    mode = models.CharField(
        verbose_name='Режим', choices=MODES, default=TEST, max_length=7)
    token = models.CharField(
        verbose_name='Токен', blank=True, null=True, max_length=63)

    pickup_type = models.PositiveIntegerField(
        verbose_name='Тип приема груза',
        choices=PICKUP_CHOICES,
        default=TypePickup.FROM_POINT)

    region = models.CharField(
        verbose_name='Область, республика или край', max_length=127,
        help_text='Например: "Московская область"', blank=True, null=True)
    city = models.CharField(
        verbose_name='Город или населенный пункт', max_length=100,
        help_text='Например: "Москва"', blank=True, null=True)
    city_guid = models.CharField(
        verbose_name='ID города в базе ФИАС', max_length=63,
        help_text='https://fias.nalog.ru/Search', blank=True, null=True)

    include_fee = models.BooleanField(
        verbose_name='Добавлять все сборы СД',
        default=False,
        help_text='Суммировать к итоговой стоимости все'
                  ' сборы СД(страховка и комиссия за НП)')

    timeout = models.PositiveIntegerField(
        verbose_name='Время ожидания ответа СД (секунд)',
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        default=2,
        help_text='Время ожидания ответа от провайдера, результаты по'
                  ' провайдерам которые не успели в указанное время выдаваться'
                  ' не будут.')

    def __str__(self):
        return 'Настройки APISHIP'

    def clean(self):
        if self.mode == self.PROD and not self.token:
            raise ValidationError("Введите токен")
        if not self.city and not self.city_guid:
            raise ValidationError("Заполните город, либо ID ФИАС")

    @classmethod
    def load(cls):
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(pk=self.pk).delete()
        super(Settings, self).save(*args, **kwargs)


class OrderShipping(models.Model):
    order = models.OneToOneField(
        Order, related_name='apiship', on_delete=models.CASCADE)
    comment = models.TextField(verbose_name="Комментарий")
    created_at = models.DateTimeField(
        verbose_name="Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = 'Доставка'
        verbose_name_plural = 'Доставка'


class ApiShipOrder:
    settings = None
    apiship = None

    def __init__(self):
        self.settings = Settings.load()
        self.apiship = Client(
            self.settings.token,
            self.settings.mode)
        # self.apiship = Client(
        #     "2f0b7cbf13c3619e73a3c339cfd9c6fa", "test")

    @property
    def city_from(self):
        city_from = {
            "countryCode": "RU",
        }
        if self.settings.region:
            city_from['region'] = self.settings.region
        if self.settings.city:
            city_from['city'] = self.settings.city
        if self.settings.city_guid:
            city_from['cityGuid'] = self.settings.city_guid
        return city_from

    def get_points(self, fields="", **filters):
        """
        Получение списка пунктов выдачи.

        Возможные поля фильтрации:
        id, providerKey, code, name, postIndex, lat, lng,
        countryCode, region,regionType, city, cityGuid,cityType,
        area, street, streetType, house, block, office, url, email,
        phone, type, cod, paymentCard, fittingRoom
        Например city=Москва;providerKey=cdek
        """
        if fields:
            fields = "lat,lng,name,paymentCard"
        filter = ";".join(f"{f[0]}={f[1]}" for f in filters.items())
        return self.apiship.list_points(fields=fields, filter=filter)

    def calclulate(self, city_from, city_to, sizes, total, to_point):
        """
        Расчет стоимости доставки.

        city_from - город отправления
        city_to - город доставки
        sizes - кортеж либо список габаритов товара (вес, ширина, высота, длина)
        total - оценочная стоимость
        to_point - до пункта выдачи
        """
        weight, width, height, length = sizes

        # адрес отправки (возможно потребуется добавить в будущем)
        # if addressString:
        #     city_from['addressString'] = self.settings.city_guid

        params = {
            "from": self.city_from,
            "to": {
                # "region": "Саратовская обл",
                "city": city_to,
                "countryCode": "RU",
                # "addressString": "Саратов, Вавилова 36",
            },
            "weight": weight,
            "width": width,
            "height": height,
            "length": length,
            "assessedCost": total,
            "pickupTypes": [self.settings.pickup_type],
            "deliveryTypes": [
                TypeDelivery.TO_POINT if to_point else TypeDelivery.TO_DOOR
            ],
            "timeout": (self.settings.timeout * 1000)  # в милисекундах
        }
        response = self.apiship.calculator(**params)

        if to_point:
            providers_tariff = {}
            point_ids = []
            providers = response['deliveryToPoint']
            for provider in providers:
                if provider['tariffs']:
                    point_ids = point_ids + provider['providerKey']['pointIds']
                    providers_tariff[provider['providerKey']] = min(
                        provider['tariffs'], key=lambda x: x['deliveryCost'])

            return self.list_points(id=str(point_ids))
