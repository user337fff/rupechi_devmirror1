from typing import Optional, Dict

import requests

from .response import BaseResponse, OrderRegisterResponse, OrderStatusResponse


API_URL_TEST = "https://3dsec.sberbank.ru/payment/rest/"
API_URL_PROD = "https://securepayments.sberbank.ru/payment/rest/"

API_RESOURCES = {
    'deposit': 'deposit.do',
    'get_order_status_extended': 'getOrderStatusExtended.do',
    'payment': 'payment.do',
    'payment_sber_pay': 'paymentSberPay.do',
    'refund': 'refund.do',
    'register': 'register.do',
    'register_pre_auth': 'registerPreAuth.do',
    'reverse': 'reverse.do',
    'verify_enrollment': 'verifyEnrollment.do'
}


class Client:
    """ Класс для работы со Sberbank Acquiring REST API  """

    auth_data = None

    def __init__(self, username=None, password=None, token=None, test=True):
        if test:
            self.base = API_URL_TEST
        else:
            self.base = API_URL_PROD

        # проверка на существование пары имя-пароль, либо токена авторизации
        if username is not None and password is not None:
            self.auth_data = {'userName': username, 'password': password}
        elif token is not None:
            self.auth_data = {'token': token}
        else:
            raise TypeError(
                "{} missing required positional arguments: {}".format(
                    type(self).__name__, 'username and password or token'
                ))

    # # Данный метод не актуален, так как сбер не позволяет
    # # передавать авторизационные данные в заголовках
    # def _init_session(self, headers=None, auth_data=None):
    #     """
    #     Сессия нужна для хранения авторизационных данных в заголовках.

    #     headers - авторизационные заголовки, хранимые в сессии
    #     auth_data - авторизационные данные, добавляемые к каждому запросу
    #     """
    #     self.session = requests.Session()
    #     if headers is not None:
    #         self.session.headers.update(headers)
    #     elif auth_data is not None:
    #         self.auth_data = auth_data

    def _exec_request(self, action: str, data: Optional[Dict] = None) -> dict:
        """
        Отправка запроса к апи
        """
        resource = API_RESOURCES[action]
        # если есть авторизационные данные, то добавляем их к запросу
        if self.auth_data is not None:
            data.update(self.auth_data)
        response = requests.post(self.base + resource, data=data)
        return response

    def register(self,
                 order_number,
                 amount,
                 return_url,
                 fail_url,
                 email=None,
                 bundle=None,
                 tax_system=None,
                 **kwargs):
        """
        Регистрация заказа в системе
        Обязательные параметры:
            order_number - ид заказа в системе магазина
            amount - сумма платежа в минимальных единицах
            return_url - адрес перенаправления  в случае успешной оплаты

        bundle - корзина товаров, необязательный параметр для апи,
        но обязательный параметр для фискализации,
        без него не будут приходить чеки, а это нарушение законодательства
        taxSystem - аналогично bundle


        !!! Важные параметры
        sessionTimeoutSecs - Продолжительность жизни заказа в секундах.
        expirationDate - Дата и время окончания жизни заказа
        если есть expirationDate, то sessionTimeoutSecs не учитывается
        """
        data = {
            'amount': int(amount),
            'orderNumber': order_number,
            'returnUrl': return_url,
            'failUrl': fail_url
        }
        if bundle is not None:
            data['orderBundle'] = bundle
        if tax_system is not None:
            data['taxSystem'] = tax_system
        # if email:
        #     data['customerDetails'] = {'email': email}
        if email:
            data['email'] = email
        data.update(kwargs)
        return OrderRegisterResponse(self._exec_request('register', data))

    def get_order_status_extended(self, order_id=None, order_number=None):
        """
        Проверка статуса заказа

        order_id - ид в системе банка
        order_number - ид в системе магазина
        """
        if order_id:
            data = {'orderId': order_id}
        elif order_number:
            data = {'orderNumber': order_number}
        else:
            raise TypeError(
                "{} missing required positional argument: {}".format(
                    type(self).__name__, 'order_id or order_number'
                ))
        return OrderStatusResponse(self._exec_request('get_order_status_extended', data))
