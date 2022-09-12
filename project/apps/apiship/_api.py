# https://wiki.apiship.ru/pages/viewpage.action?pageId=17465357
from typing import Optional, Dict
import requests
from django.conf import settings
from .entities import Calculator, CouirierCall, OrderCreate

API_URL_TEST = 'http://api.dev.apiship.ru/v1'
API_URL_PROD = 'https://api.apiship.ru/v1'

LOGIN_TEST = 'test'
PASSWORD_TEST = 'test'


API_RESOURCES = {
    # получение токена
    'login': ('post', '/login'),

    # создание заказа
    'order': ('post', '/orders'),
    # создание синхронного заказа
    'order_sync': ('post', '/orders/sync'),
    # валидация заказа
    'order_validate': ('post', '/orders/validate'),
    # получение информации по заказу
    'order_get': ('get', '/orders/{orderId}'),
    # удаление закза
    'order_delete': ('delete', '/orders/{orderId}'),
    # изменение заказа
    'order_change': ('put', '/orders/{orderId}'),
    # повторная отправка заказа в СД
    'order_resend': ('post', '/orders/{orderId}/resend'),
    # отмена заказа
    'order_delete': ('get', '/orders/{orderId}/cancel'),
    # получение статуса заказа
    'order_status': ('get', '/orders/{orderId}/status'),

    # расчет стоимости доставки
    'calculator': ('post', '/calculator'),
    # вызов курьера
    'courier': ('post', '/courierCall'),

    # получение списка поставщиков
    'list_providers': ('get', '/lists/providers'),
    # получение списка поставщиков
    'list_points': ('get', '/lists/points'),
    # список тарифов
    'list_tariffs': ('get', '/lists/tariffs')
}


class Client:
    """
    Класс для работы с ApiShip

    Переопределен метод __getattr__.
    Благодаря этому если атрибут есть в списке методов,
    то отправляется запрос к этому api-методу с переданными парметрами.
    Также запросы привязаны к http-методам, поэтому первый парметр содержит
    название http-метода, а второй уже сам ресурс.

    """
    DEFAULT_METHOD = 'post'

    def __init__(self, token: Optional[str] = None,
                 mode: Optional['str'] = 'prod'):
        # выбираем ссылку в зависимости от режима
        if mode == 'prod':
            self.base = API_URL_PROD
        else:
            self.base = API_URL_TEST
        self._init_session()
        # в боевом режиме токен обязателен
        if token is None and mode == 'prod':
            raise TypeError("Token required for production mode")
        elif token is None and mode == 'test':
            token = self.get_token()
        # добавляем в сессию токен
        self.session.headers['Authorization'] = token

    def _init_session(self):
        """ Сессия нужна для хранения токена авторизации в заголовках  """
        self.session = requests.Session()
        self.session.encoding = 'utf-8'

    def _exec_request(self,
                      _action: str,
                      _data: Optional[Dict] = None,
                      **kwargs) -> dict:
        """
        Отправка запроса к апи
        """
        # получаем http-метод и api-метод из списка методов
        method, resource = API_RESOURCES[_action]
        # получаем метод отправки http-метода
        send = getattr(self.session, method, self.DEFAULT_METHOD)
        data = kwargs if _data is None else _data

        if method == 'get':
            response = send(self.base + resource, params=data)
        else:
            response = send(self.base + resource, json=data)
        # выкидываем исключение в зависимости от статуса запроса
        # response.raise_for_status()
        return response  # .json()

    def _get_token(self):
        return self.login(
            login=LOGIN_TEST,
            password=PASSWORD_TEST)['accessToken']

    def login(self, login, password):
        return self._exec_request("login", login=login, password=password)

    def calculate(self, calculator: Calculator):
        """
        Расчет стоимости доставки
        """
        data = calculator.to_data()
        return self._exec_request("calculator", data)

    def get_points(self, limit: Optional[int] = None,
                   offset: Optional[int] = None,
                   filter: Optional[str] = None,
                   fields: Optional[str] = None):
        """
         Получение списка пунктов выдачи.

         :param limit: максимальное количество точек
         :param offset:
         :param filter: фильтры
         :param fields: возвращаемые поля

         Возможные поля в filter:
         id, providerKey, code, name, postIndex, lat, lng,
         countryCode, region,regionType, city, cityGuid,cityType,
         area, street, streetType, house, block, office, url, email,
         phone, type, cod, paymentCard, fittingRoom
         Например city=Москва;providerKey=cdek
         """

        data = {}

        if limit is not None:
            data['limit'] = limit
        if offset is not None:
            data['offset'] = offset
        if filter is not None:
            data['filter'] = filter
        if fields is not None:
            data['fields'] = fields

        return self._exec_request("list_points", data)

    def get_tariffs(self, limit: Optional[int] = None,
                    offset: Optional[int] = None,
                    filter: Optional[str] = None,
                    fields: Optional[str] = None):
        """
         Получение списка тарифов.

         :param limit: максимальное количество точек
         :param offset:
         :param filter: фильтры
         :param fields: возвращаемые поля

         Возможные поля в filter:
         id, providerKey, name
         """

        data = {}

        if limit is not None:
            data['limit'] = limit
        if offset is not None:
            data['offset'] = offset
        if filter is not None:
            data['filter'] = filter
        if fields is not None:
            data['fields'] = fields

        return self._exec_request("list_tariffs", data)

    def call_couirer(self, callCouirer: CouirierCall):
        data = callCouirer.to_data()
        return self._exec_request("courier", data)

    def create_order(self, orderCreate: OrderCreate):
        data = orderCreate.to_data()
        return self._exec_request("order", data)

    # def __getattr__(self, attr: str):
    #     if attr in API_RESOURCES:
    #         def wrapper(*args, **kwargs):
    #             kwargs.update({'_action': attr})
    #             return self.request(*args, **kwargs)
    #         return wrapper
    #     raise AttributeError
