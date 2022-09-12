import copy
from typing import Optional, List, Dict
from abc import ABC, abstractmethod


DEFAULT_COUNTRY = 'RU'
# Тип забора посылки
# 1 - от двери, 2 - самостоятельная доставка до склада
DEFAULT_PICKUP_TYPE = 2


class AbstractData(ABC):
    """
    Абстрактный класс содержащий параметры запроса к апи
    """
    @abstractmethod
    def to_data(self) -> dict:
        raise NotImplementedError


class Calculator(AbstractData):
    """
    Набор параметров для расчета стоимости доставки
    """

    def __init__(self, city_from: dict, city_to: dict,
                 weight: int, width: int, height: int,
                 length: int,
                 assessedCost: float,
                 pickupTypes: Optional[List[int]] = [DEFAULT_PICKUP_TYPE],
                 deliveryTypes: Optional[List[int]] = None,
                 providerKeys: Optional[List[str]] = None,
                 codCost: Optional[float] = None,
                 includeFees: Optional[bool] = False,
                 timeout: Optional[int] = 2000):
        """
        :param city_from: адрес отправителя
        :param city_to: адрес получателя
        :param weight: вес
        :param width: ширина
        :param height: высота
        :param length: длина
        :param assessedCost: оценочная стоимость
        :param pickupTypes: типы забора [1 - от дверей, 2 - со склада]
        :param deliveryTypes: типы доставки [1 - до дверей, 2 - самовывоз]
        :param providerKeys: список ключей службы доставки
        :param codCost: сумма наложенного платежа
        :param includeFees: суммировать ли к итоговой стоимости сборы СД
        :param timeout: адрес
        """

        self.city_from = city_from
        self.city_to = city_to
        self.weight = weight
        self.width = width
        self.height = height
        self.length = length
        self.assessedCost = assessedCost
        self.pickupTypes = pickupTypes

        if deliveryTypes is not None:
            self.deliveryTypes = deliveryTypes
        if providerKeys is not None:
            self.providerKeys = providerKeys
        if codCost is not None:
            self.codCost = codCost
        if includeFees is not None:
            self.includeFees = includeFees
        if timeout is not None:
            self.timeout = timeout

    def to_data(self):
        data = copy.deepcopy(self.__dict__)
        # from зарезервированное слово и не может быть атритбутом класса
        # to добавлено для единообразия
        data['from'] = data.pop("city_from")
        data['to'] = data.pop("city_to")
        return data

    @staticmethod
    def add_address(
            cityGuid: Optional[str] = None,
            region: Optional[str] = None,
            city: Optional[str] = None,
            countryCode: Optional[str] = DEFAULT_COUNTRY,
            addressString: Optional[str] = None,
            lat: Optional[float] = None, lng: Optional[float] = None):
        """
        Добавление адреса доставки
        :param city_from: адрес отправителя
        :param city_to: адрес получателя
        :param weight: вес
        :param width: ширина
        :param height: высота
        :param length: длина
        :param assessedCost: оценочная стоимость
        :param pickupTypes: типы забора [1 - от дверей, 2 - со склада]
        :param deliveryTypes: типы доставки [1 - до дверей, 2 - самовывоз]
        :param providerKeys: список ключей службы доставки
        :param codCost: сумма наложенного платежа
        :param includeFees: суммировать ли к итоговой стоимости сборы СД
        :param timeout: адрес
        """

        if cityGuid is None and city is None:
            raise TypeError("Должен быть указан хотя бы"
                            " один из аргументов cityGuid либо city")
        address_data = {}
        if cityGuid is not None:
            address_data['cityGuid'] = cityGuid
        if region is not None:
            address_data['region'] = region
        if city is not None:
            address_data['city'] = city
        address_data['countryCode'] = countryCode
        if addressString is not None:
            address_data['addressString'] = addressString
        if (lat is not None) and (long is not None):
            address_data['lat'], address_data['lng'] = lat, lng

        return address_data


class CouirierCall(AbstractData):
    """
    Набор параметров для вызова курьера
    """

    def __init__(self,
                 providerKey: str,
                 date: str,
                 timeStart: str, timeEnd: str,
                 weight: int, width: int, height: int,
                 length: int,
                 orderIds: List[int],
                 region: str,
                 area: str,
                 city: str,
                 street: str,
                 house: str,
                 contactName: str,
                 phone: str,
                 email: str,
                 providerConnectId: Optional[int] = None,
                 postIndex: Optional[str] = None,
                 countryCode: Optional[List[int]] = DEFAULT_COUNTRY,
                 cityGuid: Optional[str] = 2000,
                 block: Optional[str] = None,
                 office: Optional[str] = None,
                 companyName: Optional[str] = None,):
        """
            :param providerKey: код службы доставки
            :param date: дата доставки
            :param timeStart: начальное время доставки
            :param timeEnd: конечное время доставки
            :param weight: вес
            :param width: ширина
            :param height: высота
            :param length: длина
            :param orderIds: номера заказов которые планируются передать
            :param region: область или республика или край
            :param area: район
            :param city: город или населенный пункт
            :param street: улица
            :param house: дом
            :param contactName: ФИО контактного лица
            :param phone:
            :param email:
            :param providerConnectId: ID подключения вашей компании к СД
            :param postIndex: почтовый индекс
            :param countryCode: код страны в соответствии с ISO 3166-1 alpha-2
            :param cityGuid: ID города в базе ФИАС
            :param block: строение/корпус
            :param office: офис/квартира
            :param companyName: название компании
        """

        self.providerKey = providerKey
        self.date = date
        self.timeStart = timeStart
        self.timeEnd = timeEnd
        self.weight = weight
        self.width = width
        self.height = height
        self.length = length
        self.orderIds = orderIds
        self.region = region
        self.area = area
        self.city = city
        self.street = street
        self.house = house
        self.contactName = contactName
        self.phone = phone
        self.email = email
        if providerConnectId is not None:
            self.providerConnectId = providerConnectId
        if postIndex is not None:
            self.postIndex = postIndex
        if countryCode is not None:
            self.countryCode = countryCode
        if cityGuid is not None:
            self.cityGuid = cityGuid
        if block is not None:
            self.block = block
        if office is not None:
            self.office = office
        if companyName is not None:
            self.companyName = companyName

    def to_data(self):
        return self.__dict__


class OrderData(AbstractData):
    def __init__(self,
                 clientNumber: str,
                 weight: int,
                 providerKey: str,
                 deliveryType: int,
                 tariffId: int,
                 pickupType: Optional[int] = DEFAULT_PICKUP_TYPE,
                 **kwargs):
        """
        :param clientNumber: номер заказа в системе клиента
        :param weight: вес заказа
        :param providerKey: код службы доставки
        :param deliveryType: тип доставки
        :param tariffId: тариф службы доставки
        :param providerNumber: номер заказа в системе службы доставки
        :param barcode: штрих-код
        :param description: коментарий
        :param height: высота заказа в сантиметрaх
        :param length: длина заказа в сантиметрaх
        :param width: ширина заказа в сантиметрaх
        optional
        :param pickupType: тип забора груза
        :param providerConnectId: ID подключения вашей компании к СД
        :param pickupDate: предполагаемая дата передачи груза в службу доставки
        :param deliveryDate: дата доставки
        :param pointInId: ID точки приема заказа
        :param pointOutId: ID точки выдачи заказа
        :param pickupTimeStart: Начальное время забора груза
        :param pickupTimeEnd: Конечное время забора груза
        :param deliveryTimeStart: Начальное время доставки
        :param deliveryTimeEnd: Конечное время доставки
        """
        self.clientNumber = clientNumber
        self.weight = weight
        self.providerKey = providerKey
        self.deliveryType = deliveryType
        self.tariffId = tariffId
        self.pickupType = pickupType

        self.__dict__.update(kwargs)

    def to_data(self):
        return self.__dict__


class OrderCost(AbstractData):

    def __init__(self,
                 assessedCost: float,
                 codCost: Optional[float] = 0,
                 deliveryCost: Optional[float] = None,
                 deliveryCostVat: Optional[float] = None,
                 isDeliveryPayedByRecipient: Optional[bool] = False,
                 ):
        """
        :param assessedCost: оценочная стоимость / сумма страховки (в рублях)
        :param codCost: сумма наложенного платежа с учетом НДС (в рублях)
        :param deliveryCost: стоимость доставки с учетом НДС (в рублях)
        :param deliveryCostVat: процентная ставка НДС
        :param isDeliveryPayedByRecipient: флаг для указания стороны,
        которая платит за услуги доставки (0-отправитель, 1-получатель)
        """
        self.assessedCost = assessedCost
        self.codCost = codCost
        self.isDeliveryPayedByRecipient = isDeliveryPayedByRecipient
        if deliveryCost is not None:
            self.deliveryCost = deliveryCost
        if deliveryCostVat is not None:
            self.deliveryCostVat = deliveryCostVat

    def to_data(self):
        return self.__dict__


class OrderAddress(AbstractData):
    def __init__(self,
                 region: str,
                 city: str,
                 street: str,
                 house: str,
                 contactName: str,
                 phone: str,
                 countryCode: Optional[str] = DEFAULT_COUNTRY,
                 **kwargs):
        """
        :param addressString: Полный адрес отправителя одной строкой
        :param lat: Широта отправителя
        :param lng: Долгота отправителя
        :param postIndex: Почтовый индекс
        :param countryCode: Код страны в соответствии с ISO 3166-1 alpha-2
        :param region: Область или республика или край
        :param area: Район
        :param city: Город или населенный пункт
        :param cityGuid: ID города в базе ФИАС
        :param street: Улица
        :param house: Дом
        :param block: Строение/Корпус
        :param office: Офис/Квартира
        :param companyName: Название компании
        :param companyInn: ИНН компании
        :param contactName: ФИО контактного лица
        :param phone: Контактный телефон
        :param email: Контактный email адрес
        :param comment: Коментарий
        """
        self.region = region
        self.city = city
        self.street = street
        self.house = house
        self.contactName = contactName
        self.phone = phone
        self.countryCode = countryCode

        self.__dict__.update(kwargs)

    def to_data(self):
        return self.__dict__


class OrderItems(AbstractData):
    def __init__(self, *args, **kwargs):
        self.items = list()

    def add_item(self,
                 description,
                 quantity,
                 **kwargs):
        """
        :param description: Наименование товара
        :param quantity: Кол-во товара.
                         Если указан markCode, то кол-во не может быть > 1
        :param articul: Артикул товара
        :param markCode: Код маркировки(UTF-8)
        :param quantityDelivered: Заполняется только при частичной доставке
                                  и показывает сколько вложимых выкуплено
        :param height: Высота единицы товара в сантиметрах
        :param length: Длина единицы товара в сантиметрах
        :param width: Ширина единицы товара в сантиметрах
        :param weight: Вес единицы товара в граммах
        :param assessedCost: Оценочная стоимость единицы товара в рублях
        :param cost: Стоимость единицы товара с учетом НДС в рублях
        :param costVat: Процентная ставка НДС
        :param barcode: Штрихкод на товаре
        """

        item = {
            "description": description,
            "quantity": quantity
        }
        if kwargs:
            item.update(kwargs)
        self.items.append(item)

    def to_data(self):
        return self.items


class OrderCreate(AbstractData):
    def __init__(self,
                 order: OrderData,
                 cost: OrderCost,
                 sender: OrderAddress,
                 recipient: OrderAddress,
                 returnAddress: OrderAddress = None,
                 items: Optional[Dict] = None,
                 places: Optional[Dict] = None):
        self.order = order
        self.cost = cost
        self.sender = sender
        self.recipient = recipient
        if returnAddress is not None:
            self.returnAddress = returnAddress
        if items is not None:
            self.items = items
        if places is not None:
            self.places = places

    def to_data(self):
        data = copy.deepcopy(self.__dict__)
        for key in data:
            if isinstance(data[key], AbstractData):
                data[key] = data[key].to_data()
        return data
