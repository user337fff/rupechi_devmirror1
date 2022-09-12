# https://wiki.apiship.ru/pages/viewpage.action?pageId=17465357
import requests
from django.conf import settings

API_URL_TEST = 'http://api.dev.apiship.ru/v1'
API_URL_PROD = 'https://api.apiship.ru/v1'

LOGIN = getattr(settings, 'APISHIP_LOGIN', 'test')
PASSWORD = getattr(settings, 'APISHIP_PASSWORD', 'test')


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

    # получение списка поставщиков
    'list_providers': ('get', '/lists/providers'),
    # получение списка поставщиков
    'list_points': ('get', '/lists/points')
}


class ApiShip:
    """
    Класс для работы с ApiShip

    Переопределен метод __getattr__.
    Благодаря этому если атрибут есть в списке методов,
    то отправляется запрос к этому api-методу с переданными парметрами.
    Также запросы привязаны к http-методам, поэтому первый парметр содержит
    название http-метода, а второй уже сам ресурс.

    """
    DEFAULT_METHOD = 'post'

    def __init__(self, token=None, mode='prod'):
        # выбираем ссылку в зависимости от режима
        if mode == 'prod':
            self.base = API_URL_PROD
        else:
            self.base = API_URL_TEST
        self.init_session()
        # в боевом режиме токен обязателен
        if token is None and mode == 'prod':
            raise TypeError("Token required for production mode")
        elif token is None and mode == 'test':
            token = self.get_token()
        # добавляем в сессию токен
        self.session.headers['Authorization'] = token

    def init_session(self):
        """ Сессия нужна для хранения токена авторизации в заголовках  """
        self.session = requests.Session()
        self.session.encoding = 'utf-8'

    def get_token(self):
        return self.login(login=LOGIN, password=PASSWORD)['accessToken']

    def __getattr__(self, attr):
        if attr in API_RESOURCES:
            def wrapper(*args, **kwargs):
                kwargs.update({'_action': attr})
                return self.request(*args, **kwargs)
            return wrapper
        raise AttributeError

    def request(self, _action, *args, **kwargs):
        """
        Отправка запроса к апи
        """
        print(args, kwargs)
        # получаем http-метод и api-метод из списка методов
        method, resource = API_RESOURCES[_action]
        # получаем метод отправки http-метода
        send = getattr(self.session, method, self.DEFAULT_METHOD)
        if method == "post":
            return send(self.base + resource, json=kwargs).json()
        return send(self.base + resource, data=kwargs)
